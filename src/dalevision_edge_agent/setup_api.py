from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

from .installation_check import build_installation_check_payload
from .onboarding_readiness import build_onboarding_readiness
from .scan import build_onboarding_blueprint


DiscoveryProvider = Callable[[], list[dict[str, Any]]]


def build_setup_api_response(
    *,
    path: str,
    discovery_provider: DiscoveryProvider,
) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(path)
    route = parsed.path.rstrip("/") or "/"
    query = parse_qs(parsed.query)

    if route == "/health":
        return 200, {
            "ok": True,
            "service": "edge_setup_api",
            "status": "online",
            "capabilities": {
                "onboarding_blueprint": True,
                "onboarding_readiness": True,
                "onboarding_installation_check": True,
            },
        }

    if route == "/onboarding/blueprint":
        plan_code = (query.get("plan") or ["trial"])[0]
        scan_results = discovery_provider()
        payload = build_onboarding_blueprint(scan_results, plan_code=plan_code)
        return 200, {
            "ok": True,
            **payload,
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

    return 404, {
        "ok": False,
        "error": "not_found",
    }


def serve_setup_api(
    *,
    host: str,
    port: int,
    discovery_provider: DiscoveryProvider,
    logger: Optional[logging.Logger] = None,
) -> None:
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
            code, payload = build_setup_api_response(
                path=self.path,
                discovery_provider=discovery_provider,
            )
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
