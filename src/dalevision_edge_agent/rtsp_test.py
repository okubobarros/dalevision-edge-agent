from __future__ import annotations

import ipaddress
import logging
from typing import Any, Optional

from .cameras import (
    capture_snapshot_if_possible,
    check_camera_health,
    mask_rtsp_url,
)
from .diagnostics import _parse_ipconfig, _run_cmd


def _build_intelbras_rtsp(ip: str, user: str, password: str, channel: int, subtype: int) -> str:
    host = ip
    port = "554"
    if ":" in ip:
        host, port = ip.rsplit(":", 1)
    return (
        f"rtsp://{user}:{password}@{host}:{port}/"
        f"cam/realmonitor?channel={channel}&subtype={subtype}"
    )


def _is_segmented(target_ip: str) -> bool:
    ipconfig_text = _run_cmd("ipconfig /all")
    parsed = _parse_ipconfig(ipconfig_text)
    ipv4 = parsed.get("ipv4")
    mask = parsed.get("mask")
    if not ipv4 or not mask:
        return False
    try:
        network = ipaddress.ip_network(f"{ipv4}/{mask}", strict=False)
        return ipaddress.ip_address(target_ip) not in network
    except Exception:
        return False


def test_rtsp(
    *,
    ip: str,
    user: str,
    password: str,
    channel: int,
    subtype: int,
    timeout_seconds: int,
    logger: logging.Logger,
) -> dict[str, Any]:
    rtsp_url = _build_intelbras_rtsp(ip, user, password, channel, subtype)
    safe_url = mask_rtsp_url(rtsp_url)
    logger.info("RTSPTEST tentando %s", safe_url)

    health = check_camera_health(
        {"ip": ip},
        perform_describe=True,
        rtsp_url_override=rtsp_url,
        timeout_seconds=timeout_seconds,
    )
    error = str(health.get("error") or "unknown")
    if health.get("status") not in {"online", "degraded"} and "unauthorized" in error:
        # Many NVRs answer 401 on the first DESCRIBE and require Digest challenge/retry.
        # Fallback to plain RTSP socket connectivity to avoid false negatives.
        fallback_health = check_camera_health(
            {"ip": ip},
            perform_describe=False,
            rtsp_url_override=rtsp_url,
            timeout_seconds=timeout_seconds,
        )
        if fallback_health.get("status") in {"online", "degraded"}:
            logger.info("RTSPTEST digest challenge detected; connectivity fallback succeeded")
            health = fallback_health

    if health.get("status") not in {"online", "degraded"}:
        error = str(health.get("error") or "unknown")
        if "unauthorized" in error:
            message = "RTSP401 credencial invalida"
        elif "timeout" in error:
            if _is_segmented(ip):
                message = "NET002 NVR fora do subnet local (VLAN diferente)"
            else:
                message = "RTSPTO timeout. Possivel VLAN/porta bloqueada"
        else:
            message = f"RTSPERR {error}"
        logger.info("RTSPTEST falhou: %s", message)
        return {
            "ok": False,
            "message": message,
            "health": health,
        }

    safe_ip_for_path = ip.replace(":", "_")
    snapshot = capture_snapshot_if_possible(
        camera_id=f"nvr-{safe_ip_for_path}-ch{channel}",
        rtsp_url=rtsp_url,
        logger=logger,
        timeout_seconds=timeout_seconds,
    )
    fps_estimate = None
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(rtsp_url)
        fps_value = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        if fps_value and fps_value > 0:
            fps_estimate = float(fps_value)
    except Exception:
        fps_estimate = None
    result = {
        "ok": True,
        "health": health,
        "snapshot": snapshot,
        "fps": fps_estimate,
    }
    logger.info("RTSPTEST ok: canal %s", channel)
    return result


def test_rtsp_channels(
    *,
    ip: str,
    user: str,
    password: str,
    channels: list[int],
    subtype: int,
    timeout_seconds: int,
    logger: logging.Logger,
) -> dict[str, Any]:
    results = []
    for channel in channels:
        result = test_rtsp(
            ip=ip,
            user=user,
            password=password,
            channel=channel,
            subtype=subtype,
            timeout_seconds=timeout_seconds,
            logger=logger,
        )
        results.append({"channel": channel, "ok": result.get("ok"), "message": result.get("message")})
        if result.get("ok"):
            break
        if result.get("message") == "RTSP401 credencial invalida":
            break
    return {"results": results}
