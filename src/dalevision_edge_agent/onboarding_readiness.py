from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Callable, Optional

from .env import describe_env_file, load_env_from_cwd, load_settings
from .scan import build_onboarding_blueprint


DiscoveryProvider = Callable[[], list[dict[str, Any]]]

REQUIRED_ENV_KEYS = (
    ("CLOUD_BASE_URL", ("DALE_CLOUD_BASE_URL",)),
    ("STORE_ID", ("DALE_STORE_ID",)),
    ("EDGE_TOKEN", ("DALE_EDGE_TOKEN",)),
)


def _get_env_with_legacy(name: str, legacy_names: tuple[str, ...]) -> str:
    primary = str(os.getenv(name) or "").strip()
    if primary:
        return primary
    for legacy in legacy_names:
        value = str(os.getenv(legacy) or "").strip()
        if value:
            return value
    return ""


def _summarize_status(checks: list[dict[str, Any]]) -> str:
    has_failed = any(item.get("status") == "fail" for item in checks)
    if has_failed:
        return "blocked"
    has_warning = any(item.get("status") == "warning" for item in checks)
    if has_warning:
        return "needs_attention"
    return "ready"


def build_onboarding_readiness(
    *,
    plan_code: str = "trial",
    include_scan: bool = False,
    discovery_provider: Optional[DiscoveryProvider] = None,
) -> dict[str, Any]:
    env_path = load_env_from_cwd()
    env_info = describe_env_file(Path(env_path))

    checks: list[dict[str, Any]] = []
    missing_env_keys: list[str] = []
    for name, legacy in REQUIRED_ENV_KEYS:
        value = _get_env_with_legacy(name, legacy)
        status = "ok" if value else "fail"
        if not value:
            missing_env_keys.append(name)
        checks.append(
            {
                "key": f"env_{name.lower()}",
                "status": status,
                "reason_code": "env_present" if value else "env_missing",
                "message": f"{name} {'presente' if value else 'ausente'}",
            }
        )

    settings_payload: dict[str, Any] = {}
    try:
        settings = load_settings()
        settings_payload = {
            "cloud_base_url": settings.cloud_base_url,
            "store_id": settings.store_id,
            "agent_id": settings.agent_id,
            "max_active_cameras": settings.max_active_cameras,
            "auto_update_enabled": settings.auto_update_enabled,
        }
        checks.append(
            {
                "key": "settings_contract",
                "status": "ok",
                "reason_code": "settings_loaded",
                "message": "Configuração validada com sucesso",
            }
        )
    except Exception as exc:
        checks.append(
            {
                "key": "settings_contract",
                "status": "fail",
                "reason_code": "settings_invalid",
                "message": str(exc),
            }
        )

    ffmpeg_path = shutil.which("ffmpeg")
    checks.append(
        {
            "key": "ffmpeg_runtime",
            "status": "ok" if ffmpeg_path else "warning",
            "reason_code": "ffmpeg_available" if ffmpeg_path else "ffmpeg_missing",
            "message": "ffmpeg disponível" if ffmpeg_path else "ffmpeg não encontrado no PATH",
            "details": {"path": ffmpeg_path},
        }
    )

    discovery_summary = {
        "executed": False,
        "detected_count": 0,
        "recommended_count": 0,
        "recommended_camera_ips": [],
    }
    plan_payload = {
        "plan_code": str(plan_code or "trial").strip().lower(),
        "camera_limit": 3,
    }
    if include_scan and callable(discovery_provider):
        scan_results = discovery_provider()
        blueprint = build_onboarding_blueprint(scan_results, plan_code=plan_payload["plan_code"])
        plan_payload["camera_limit"] = int(blueprint.get("camera_limit") or 3)
        recommended_ips = list(blueprint.get("selection_guidance", {}).get("recommended_camera_ips") or [])
        discovery_summary = {
            "executed": True,
            "detected_count": len(blueprint.get("candidates") or []),
            "recommended_count": len(recommended_ips),
            "recommended_camera_ips": recommended_ips,
        }
        checks.append(
            {
                "key": "local_discovery_scan",
                "status": "ok" if discovery_summary["detected_count"] > 0 else "warning",
                "reason_code": "scan_candidates_found"
                if discovery_summary["detected_count"] > 0
                else "scan_no_candidates",
                "message": f"{discovery_summary['detected_count']} candidatas detectadas no scan local",
            }
        )
    else:
        plan_payload["camera_limit"] = int(
            build_onboarding_blueprint([], plan_code=plan_payload["plan_code"]).get("camera_limit") or 3
        )

    status = _summarize_status(checks)
    return {
        "ok": True,
        "method": {"id": "edge_onboarding_readiness", "version": "v1"},
        "status": status,
        "summary": {
            "checks_total": len(checks),
            "checks_ok": len([item for item in checks if item.get("status") == "ok"]),
            "checks_warning": len([item for item in checks if item.get("status") == "warning"]),
            "checks_fail": len([item for item in checks if item.get("status") == "fail"]),
            "missing_required_env": missing_env_keys,
        },
        "env_file": env_info,
        "settings": settings_payload,
        "plan": plan_payload,
        "discovery": discovery_summary,
        "checks": checks,
    }

