from __future__ import annotations

import os
import re
import time
import json
import logging
import socket
import importlib.metadata
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

from .activation import ConfigManager
from .installation_check import build_installation_check_payload
from .onboarding_readiness import build_onboarding_readiness
from .scan import build_onboarding_blueprint
from .streaming import stream_manager


DiscoveryProvider = Callable[[], list[dict[str, Any]]]
DiscoveryTelemetryHook = Callable[[list[dict[str, Any]], dict[str, Any]], None]


def _redact_sensitive_text(value: str) -> str:
    text = str(value or "")
    # Avoid leaking camera credentials when lower-level libraries include RTSP URLs in errors.
    return re.sub(r"(rtsp://[^:/\s]+:)[^@\s]+@", r"\1***@", text)


def _resolve_agent_version() -> str:
    installed_version = str(ConfigManager.from_default().load().get("installed_version") or "").strip()
    if installed_version:
        return installed_version

    env_version = str(
        os.getenv("DALEVISION_EDGE_AGENT_VERSION")
        or os.getenv("EDGE_AGENT_VERSION")
        or ""
    ).strip()
    if env_version:
        return env_version

    app_dir = str(os.getenv("DALE_APP_DIR") or "").strip()
    if app_dir:
        try:
            version_file = Path(app_dir) / "VERSION"
            version_value = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
            if version_value:
                return version_value
        except Exception:
            pass

    try:
        return importlib.metadata.version("dalevision-edge-agent")
    except Exception:
        return "unknown"


def build_setup_api_response(
    *,
    path: str,
    discovery_provider: DiscoveryProvider,
    on_discovery_result: Optional[DiscoveryTelemetryHook] = None,
) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    route = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    def get_local_ips() -> list[str]:
        ips = []
        try:
            hostname = socket.gethostname()
            info = socket.getaddrinfo(hostname, None)
            for addr in info:
                ip = addr[4][0]
                if ":" not in ip and ip != "127.0.0.1": # IPv4 only, skip localhost
                    ips.append(ip)
        except:
            pass
        return list(set(ips))

    if route == "/health":
        return 200, {
            "ok": True,
            "service": "edge_setup_api",
            "status": "online",
            "version": _resolve_agent_version(),
            "ips": get_local_ips(),
            "capabilities": {
                "onboarding_blueprint": True,
                "onboarding_readiness": True,
                "onboarding_installation_check": True,
                "streaming_hls": True,
            },
        }

    if route == "/onboarding/blueprint":
        plan_code = (query.get("plan") or ["trial"])[0]
        scan_results = discovery_provider()
        payload = build_onboarding_blueprint(scan_results, plan_code=plan_code)
        if callable(on_discovery_result):
            try:
                on_discovery_result(scan_results, payload)
            except Exception:
                # Discovery telemetry must never break onboarding API.
                pass
        return 200, {
            "ok": True,
            **payload,
        }

    if route == "/onboarding/ping":
        # Ultra-lightweight endpoint for frontend polling
        return 200, {
            "ok": True,
            "status": "online",
            "timestamp": time.time()
        }

    if route == "/onboarding/readiness":
        plan_code = (query.get("plan") or ["trial"])[0]
        include_scan = (query.get("scan") or ["0"])[0].strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        payload = build_onboarding_readiness(
            plan_code=plan_code,
            include_scan=include_scan,
            discovery_provider=discovery_provider,
        )
        return 200, payload

    if route == "/onboarding/installation-check":
        payload = build_installation_check_payload()
        return 200, payload

    if route == "/onboarding/test-camera":
        ip = (query.get("ip") or [""])[0]
        user = (query.get("user") or ["admin"])[0]
        password = (query.get("password") or ["admin"])[0]
        channel = int((query.get("channel") or ["1"])[0])
        
        from .rtsp_test import test_rtsp
        import logging
        logger = logging.getLogger("setup_api")
        
        result = test_rtsp(
            ip=ip,
            user=user,
            password=password,
            channel=channel,
            subtype=0,
            timeout_seconds=5,
            logger=logger
        )
        return 200, result

    if route == "/onboarding/snapshot":
        ip = (query.get("ip") or [""])[0]
        user = (query.get("user") or ["admin"])[0]
        password = (query.get("password") or ["admin"])[0]
        channel = int((query.get("channel") or ["1"])[0])
        cam_id = f"{ip.replace('.', '_')}_ch{channel}"
        
        rtsp_urls = [
            f"rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=1",
            f"rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0",
        ]
        
        print(f"[SETUP_API] Tentando snapshot: {ip} (CH {channel})")
        try:
            snap_path = stream_manager.get_snapshot_with_fallbacks(cam_id, rtsp_urls)
            if snap_path and os.path.exists(snap_path):
                print(f"[SETUP_API] Snapshot OK: {snap_path}")
                return 200, {"ok": True, "serving_file": True, "file_path": snap_path}
            
            print(f"[SETUP_API] Aviso: capture_failed para {ip}")
            return 200, {"ok": False, "error": "capture_failed", "detail": "stream_manager_empty"}
        except Exception as e:
            detail = _redact_sensitive_text(str(e))
            print(f"[SETUP_API] Exceção no snapshot: {detail}")
            return 200, {"ok": False, "error": "exception", "detail": detail}

    # --- Streaming (Phase 1) ---
    if route.startswith("/stream/"):
        # Serve static stream files from a temp folder or the worker's shared state
        content_type = "image/jpeg"
        if route.endswith(".m3u8"):
            content_type = "application/vnd.apple.mpegurl"
        elif route.endswith(".ts"):
            content_type = "video/MP2T"
        elif route.endswith(".jpg"):
            content_type = "image/jpeg"
        
        # This will be handled by the Handler if we allow file access
        return 200, {"ok": True, "serving_file": True}

    return 404, {
        "ok": False,
        "error": "not_found",
    }


def serve_setup_api(
    *,
    host: str,
    port: int,
    discovery_provider: DiscoveryProvider,
    on_discovery_result: Optional[DiscoveryTelemetryHook] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    # O host padrão de escuta deve ser 0.0.0.0 para garantir acessibilidade loopback no Windows.
    host = host or "0.0.0.0"
    logger = logger or logging.getLogger(__name__)

    class Handler(BaseHTTPRequestHandler):
        def _set_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _write_json(self, code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):  # noqa: N802
            self.send_response(204)
            self._set_cors_headers()
            self.end_headers()

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            route = parsed.path.rstrip("/") or "/"
            
            # Simple static file server for HLS segments in a 'tmp_streams' dir
            if "/stream/" in route:
                filename = os.path.basename(route)
                cam_id = filename.split(".")[0]
                
                # If requesting the playlist, ensure ffmpeg is running
                if filename.endswith(".m3u8"):
                    cameras = discovery_provider()
                    target_cam = next((c for c in cameras if (c.get("camera_id") or c.get("id")) == cam_id), None)
                    if target_cam and target_cam.get("rtsp_url"):
                        stream_manager.start_hls(cam_id, target_cam["rtsp_url"])
                
                # Keep active
                stream_manager.touch(cam_id)
                
                stream_dir = os.path.join(os.getcwd(), "tmp_streams")
                file_path = os.path.join(stream_dir, filename)
                
                # Wait a bit for the first segment if needed
                max_retries = 5
                while not os.path.exists(file_path) and max_retries > 0:
                    time.sleep(1)
                    max_retries -= 1

                if os.path.exists(file_path):
                    content_type = "application/octet-stream"
                    if filename.endswith(".m3u8"): content_type = "application/vnd.apple.mpegurl"
                    elif filename.endswith(".ts"): content_type = "video/MP2T"
                    elif filename.endswith(".jpg"): content_type = "image/jpeg"
                    
                    with open(file_path, "rb") as f:
                        data = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Length", str(len(data)))
                        self._set_cors_headers()
                        self.end_headers()
                        self.wfile.write(data)
                        return

            code, payload = build_setup_api_response(
                path=self.path,
                discovery_provider=discovery_provider,
                on_discovery_result=on_discovery_result,
            )
            
            if payload.get("serving_file") and payload.get("file_path") and os.path.exists(payload["file_path"]):
                with open(payload["file_path"], "rb") as f:
                    data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(data)))
                    self._set_cors_headers()
                    self.end_headers()
                    self.wfile.write(data)
                    return
            
            self._write_json(code, payload)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    logger.info("[SETUP_API] listening on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("[SETUP_API] shutdown requested")
    finally:
        server.server_close()
