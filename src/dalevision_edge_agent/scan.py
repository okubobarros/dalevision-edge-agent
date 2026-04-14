from __future__ import annotations

import logging
from typing import Any

from .scanner import scan_network
PLAN_CAMERA_LIMITS = {
    "trial": 3,
    "start": 6,
    "essentials": 12,
    "scale": 24,
}
ONBOARDING_INDICATORS = [
    {
        "key": "entry_flow",
        "label": "Fluxo de entrada/saida",
        "roi_shape": "line",
        "required": True,
    },
    {
        "key": "queue_monitoring",
        "label": "Fila no caixa",
        "roi_shape": "polygon",
        "required": False,
    },
    {
        "key": "staff_presence",
        "label": "Presenca de equipe",
        "roi_shape": "polygon",
        "required": False,
    },
    {
        "key": "occupancy_monitoring",
        "label": "Ocupacao da area",
        "roi_shape": "polygon",
        "required": False,
    },
]
def run_scan(*, logger: logging.Logger) -> list[dict[str, Any]]:
    results = []

    # 1. WS-Discovery Automático (Frictionless ONVIF)
    try:
        from .discovery import discover_onvif_cameras
        logger.info("Executando ONVIF Auto-Discovery...")
        onvif_results = discover_onvif_cameras(timeout=2)
        if onvif_results:
            results.extend(onvif_results)
    except Exception as exc:
        logger.warning(f"ONVIF Auto-Discovery skipado/falhou: {exc}")

    # 2. Fallback Scan TCP assíncrono por sub-rede local
    fallback_results = scan_network()
    if fallback_results:
        found_ips = {str(r.get("ip") or "") for r in results}
        for row in fallback_results:
            if str(row.get("ip") or "") not in found_ips:
                results.append(row)
    else:
        logger.warning("NET001 sem candidatos no scan TCP local")

    if not results:
        logger.info("NETSCAN nenhum candidato encontrado")
    return results


def build_discovery_candidates(scan_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Normalize raw scan results for onboarding consumption.
    Output contract:
      - status: ok|warning|fail
      - reason_code: deterministic reason for UX guidance
    """
    normalized: list[dict[str, Any]] = []
    for item in scan_results or []:
        ip = str(item.get("ip") or "").strip()
        ports_raw = item.get("ports") or []
        ports = [int(p) for p in ports_raw if isinstance(p, int) or str(p).isdigit()]
        confidence = str(item.get("confidence") or "low")
        status = "warning"
        reason_code = "camera_discovered_limited_signal"

        has_rtsp = 554 in ports
        has_nvr = 37777 in ports
        has_http = 80 in ports
        has_hik = 8000 in ports
        has_onvif = 8999 in ports

        if has_rtsp:
            status = "ok"
            reason_code = "rtsp_port_open"
        elif has_nvr:
            status = "warning"
            reason_code = "nvr_port_open_rtsp_unknown"
        elif has_hik:
            status = "warning"
            reason_code = "hikvision_control_port_open_rtsp_unknown"
        elif has_onvif:
            status = "warning"
            reason_code = "onvif_port_open_rtsp_unknown"
        elif has_http:
            status = "warning"
            reason_code = "http_only_device"
        else:
            status = "fail"
            reason_code = "no_supported_ports"

        normalized.append(
            {
                "ip": ip,
                "brand_hint": item.get("brand_hint") or "Generic",
                "rtsp_suggestions": item.get("rtsp_suggestions") or [],
                "ports": sorted(ports),
                "confidence": confidence,
                "status": status,
                "reason_code": reason_code,
            }
        )

    return normalized


def run_discovery(*, logger: logging.Logger) -> list[dict[str, Any]]:
    return build_discovery_candidates(run_scan(logger=logger))


def _camera_limit_for_plan(plan_code: str) -> int:
    normalized = str(plan_code or "trial").strip().lower()
    return PLAN_CAMERA_LIMITS.get(normalized, PLAN_CAMERA_LIMITS["trial"])


def _candidate_priority(item: dict[str, Any]) -> tuple[int, int, str]:
    status = str(item.get("status") or "")
    confidence = str(item.get("confidence") or "low")
    status_rank = 0 if status == "ok" else 1 if status == "warning" else 2
    confidence_rank = {"high": 0, "medium": 1, "low": 2}.get(confidence, 3)
    ip = str(item.get("ip") or "")
    return status_rank, confidence_rank, ip


def build_onboarding_blueprint(
    scan_results: list[dict[str, Any]],
    *,
    plan_code: str = "trial",
) -> dict[str, Any]:
    candidates = build_discovery_candidates(scan_results)
    sorted_candidates = sorted(candidates, key=_candidate_priority)
    camera_limit = _camera_limit_for_plan(plan_code)
    selectable_statuses = {"ok", "warning"}

    recommended_ips = [
        str(item.get("ip") or "")
        for item in sorted_candidates
        if item.get("status") in selectable_statuses
    ][:camera_limit]

    output_candidates: list[dict[str, Any]] = []
    for item in sorted_candidates:
        ip = str(item.get("ip") or "")
        is_selectable = item.get("status") in selectable_statuses
        output_candidates.append(
            {
                **item,
                "selectable": is_selectable,
                "recommended": ip in recommended_ips,
            }
        )

    return {
        "method": {"id": "edge_onboarding_blueprint", "version": "v1"},
        "plan_code": str(plan_code or "trial").strip().lower(),
        "camera_limit": camera_limit,
        "candidates": output_candidates,
        "selection_guidance": {
            "max_selectable": camera_limit,
            "recommended_camera_ips": recommended_ips,
        },
        "indicators": ONBOARDING_INDICATORS,
    }
