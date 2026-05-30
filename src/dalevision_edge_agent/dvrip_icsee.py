from __future__ import annotations

import socket
import time
from typing import Any


def probe_dvrip_icsee(
    *,
    ip: str,
    port: int,
    username: str,
    password: str,
    timeout_seconds: int,
    channel_candidates: list[int] | None = None,
    stream_candidates: list[str] | None = None,
) -> dict[str, Any]:
    start = time.time()
    host = str(ip or "").strip()
    if not host:
        return {
            "ok": False,
            "protocol": "dvrip",
            "error": "DVRIP_IP_REQUIRED",
            "latency_ms": int((time.time() - start) * 1000),
            "attempts": [],
        }

    dvrip_port = int(port or 34567)
    channels = channel_candidates or [0, 1]
    streams = stream_candidates or ["main", "extra"]
    attempts: list[dict[str, Any]] = []

    # Step 1: TCP liveness probe (works even when DVRIP libs are unavailable).
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(max(1, timeout_seconds))
    try:
        sock.connect((host, dvrip_port))
    except OSError as exc:
        return {
            "ok": False,
            "protocol": "dvrip",
            "error": "DVRIP_TCP_UNREACHABLE",
            "detail": str(exc),
            "latency_ms": int((time.time() - start) * 1000),
            "attempts": attempts,
        }
    finally:
        sock.close()

    # Step 2: Optional full DVRIP login/monitor if dependency is present.
    # Keep graceful degradation so onboarding can still return a deterministic status.
    try:
        from dvrip.io import DVRIPClient  # type: ignore
        from dvrip.monitor import Stream  # type: ignore
    except Exception:
        return {
            "ok": False,
            "protocol": "dvrip",
            "error": "DVRIP_LIBRARY_MISSING",
            "detail": "python package 'dvrip' not installed in this edge runtime",
            "latency_ms": int((time.time() - start) * 1000),
            "attempts": attempts,
        }

    for channel in channels:
        for stream_name in streams:
            stream = Stream.HD if str(stream_name).lower() == "main" else Stream.SD
            attempt = {"channel": channel, "stream": stream_name, "ok": False}
            conn = DVRIPClient(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((host, dvrip_port), username, password)
                data_sock.connect((host, dvrip_port))
                reader = conn.monitor(data_sock, channel=channel, stream=stream)
                chunk = reader.read(4096)
                if chunk:
                    attempt["ok"] = True
                    attempts.append(attempt)
                    return {
                        "ok": True,
                        "protocol": "dvrip",
                        "working_channel": channel,
                        "working_stream": stream_name,
                        "latency_ms": int((time.time() - start) * 1000),
                        "attempts": attempts,
                    }
                attempt["error"] = "empty_stream"
            except Exception as exc:
                attempt["error"] = str(exc)
            finally:
                attempts.append(attempt)
                try:
                    conn.logout()
                except Exception:
                    pass
                try:
                    conn.socket.close()
                except Exception:
                    pass
                try:
                    data_sock.close()
                except Exception:
                    pass

    return {
        "ok": False,
        "protocol": "dvrip",
        "error": "DVRIP_FRAME_CAPTURE_FAIL",
        "latency_ms": int((time.time() - start) * 1000),
        "attempts": attempts,
    }

