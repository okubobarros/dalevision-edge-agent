from __future__ import annotations

import os
import re
import time
import json
import logging
import socket
import importlib.metadata
import platform
import subprocess
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

from .activation import ConfigManager
from .installation_check import build_installation_check_payload
from .onboarding_readiness import build_onboarding_readiness
from .scan import build_onboarding_blueprint
from .streaming import stream_manager
from .diagnostics import _run_cmd


DiscoveryProvider = Callable[[], list[dict[str, Any]]]
DiscoveryTelemetryHook = Callable[[list[dict[str, Any]], dict[str, Any]], None]


def _redact_sensitive_text(value: str) -> str:
    text = str(value or "")
    # Avoid leaking camera credentials when lower-level libraries include RTSP URLs in errors.
    return re.sub(r"(rtsp://[^:/\s]+:)[^@\s]+@", r"\1***@", text)


def _looks_like_version(value: str) -> bool:
    return bool(re.fullmatch(r"v?\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9._-]+)?", str(value or "").strip()))


def _version_from_path(path: Path) -> str:
    for candidate in (path, Path.cwd()):
        name = candidate.name.strip()
        if _looks_like_version(name):
            return name.lstrip("v")
    return ""


def _resolve_agent_version() -> str:
    app_dir = str(os.getenv("DALE_APP_DIR") or "").strip()
    if app_dir:
        app_dir_path = Path(app_dir)
        path_version = _version_from_path(app_dir_path)
        if path_version:
            return path_version
        try:
            version_file = app_dir_path / "VERSION"
            version_value = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
            if version_value:
                return version_value
        except Exception:
            pass

    env_version = str(
        os.getenv("DALEVISION_EDGE_AGENT_VERSION")
        or os.getenv("EDGE_AGENT_VERSION")
        or ""
    ).strip()
    if env_version:
        return env_version

    installed_version = str(ConfigManager.from_default().load().get("installed_version") or "").strip()
    if installed_version:
        return installed_version

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

    def _runtime_marker_dir() -> Path:
        config_dir = str(os.getenv("DALE_CONFIG_DIR") or "").strip()
        if config_dir:
            base = Path(config_dir)
        elif os.getenv("APPDATA"):
            base = Path(str(os.getenv("APPDATA"))) / "DaleVision"
        else:
            base = Path.cwd() / "config"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _paused_marker() -> Path:
        return _runtime_marker_dir() / "runtime.paused"

    def _decommissioned_marker() -> Path:
        return _runtime_marker_dir() / "runtime.decommissioned"

    def _runtime_state_snapshot() -> dict[str, Any]:
        paused = _paused_marker()
        decommissioned = _decommissioned_marker()
        return {
            "paused": paused.exists(),
            "decommissioned": decommissioned.exists(),
            "paused_marker_path": str(paused),
            "decommissioned_marker_path": str(decommissioned),
        }

    def _resolve_scripts_root() -> Path:
        app_dir = str(os.getenv("DALE_APP_DIR") or "").strip()
        if app_dir:
            candidate = Path(app_dir) / "scripts"
            if candidate.exists():
                return candidate
        cwd_scripts = Path.cwd() / "scripts"
        if cwd_scripts.exists():
            return cwd_scripts
        return Path.cwd()

    def _run_ps1_detached(script_name: str, extra_args: list[str] | None = None) -> dict[str, Any]:
        script_path = _resolve_scripts_root() / script_name
        if not script_path.exists():
            return {"ok": False, "error": f"script_not_found:{script_path}"}
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ] + (extra_args or [])
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "script": str(script_path)}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "script": str(script_path)}

    def _request_graceful_exit(delay_seconds: float = 0.8) -> None:
        def _exit_later() -> None:
            time.sleep(max(0.1, delay_seconds))
            os._exit(0)

        threading.Thread(target=_exit_later, daemon=True).start()

    def build_local_runtime_diagnostics() -> dict[str, Any]:
        is_windows = platform.system().lower().startswith("win")
        netstat_output = _run_cmd("netstat -ano | findstr :8787")
        tasklist_output = _run_cmd('tasklist /FI "IMAGENAME eq python.exe"')
        scheduler_output = _run_cmd('schtasks /Query /FO LIST /V | findstr /I "DaleVision Edge Agent"')
        service_output = _run_cmd('sc query type= service state= all | findstr /I "DaleVision"')

        return {
            "ok": True,
            "runtime_local_reachable": True,
            "host_os": platform.system(),
            "is_windows": is_windows,
            "checks": {
                "port_8787_listening": bool(netstat_output and "LISTENING" in netstat_output.upper()),
                "python_process_detected": bool(tasklist_output and "python.exe" in tasklist_output.lower()),
                "scheduled_task_detected": bool(
                    scheduler_output
                    and "INFO:" not in scheduler_output.upper()
                    and "[command_error]" not in scheduler_output
                ),
                "service_detected": bool(
                    service_output
                    and "SERVICE_NAME" in service_output.upper()
                    and "[command_error]" not in service_output
                ),
            },
            "raw": {
                "netstat_8787": netstat_output[:2000],
                "tasklist_python": tasklist_output[:2000],
                "schtasks_dalevision": scheduler_output[:2000],
                "services_dalevision": service_output[:2000],
            },
        }

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

    if route == "/onboarding/local-runtime-diagnostics":
        payload = build_local_runtime_diagnostics()
        return 200, payload

    if route == "/onboarding/runtime-control":
        action = str((query.get("action") or ["status"])[0] or "status").strip().lower()
        state = _runtime_state_snapshot()

        if action == "status":
            return 200, {"ok": True, "action": "status", "state": state}

        if action == "pause":
            marker = _paused_marker()
            marker.write_text(
                json.dumps({"ts": time.time(), "reason": "paused_via_setup_api"}, ensure_ascii=True),
                encoding="utf-8",
            )
            state = _runtime_state_snapshot()
            return 200, {"ok": True, "action": "pause", "state": state}

        if action == "resume":
            _paused_marker().unlink(missing_ok=True)
            state = _runtime_state_snapshot()
            return 200, {"ok": True, "action": "resume", "state": state}

        if action == "stop":
            marker = _paused_marker()
            marker.write_text(
                json.dumps({"ts": time.time(), "reason": "stop_via_setup_api"}, ensure_ascii=True),
                encoding="utf-8",
            )
            stop_result = _run_ps1_detached("stop-agent.ps1")
            _request_graceful_exit()
            state = _runtime_state_snapshot()
            return 200, {
                "ok": True,
                "action": "stop",
                "state": state,
                "stop_result": stop_result,
            }

        if action == "decommission":
            _paused_marker().write_text(
                json.dumps({"ts": time.time(), "reason": "decommission_via_setup_api"}, ensure_ascii=True),
                encoding="utf-8",
            )
            _decommissioned_marker().write_text(
                json.dumps({"ts": time.time(), "reason": "decommission_via_setup_api"}, ensure_ascii=True),
                encoding="utf-8",
            )
            uninstall_result = _run_ps1_detached("uninstall-service.ps1")
            stop_result = _run_ps1_detached("stop-agent.ps1")
            _request_graceful_exit()
            state = _runtime_state_snapshot()
            return 200, {
                "ok": True,
                "action": "decommission",
                "state": state,
                "uninstall_result": uninstall_result,
                "stop_result": stop_result,
            }

        return 400, {"ok": False, "error": "invalid_action", "action": action}

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
