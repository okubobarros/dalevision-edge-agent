from __future__ import annotations

from datetime import datetime, timezone
import json
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


def render_onboarding_readiness_markdown(
    payload: dict[str, Any],
    *,
    generated_at: Optional[str] = None,
) -> str:
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    summary = payload.get("summary") or {}
    plan = payload.get("plan") or {}
    discovery = payload.get("discovery") or {}
    checks = payload.get("checks") or []
    missing_env = summary.get("missing_required_env") or []

    lines: list[str] = [
        "# DaleVision Edge Onboarding Readiness Report",
        "",
        f"- generated_at_utc: {generated}",
        f"- status: {payload.get('status')}",
        f"- checks_ok: {summary.get('checks_ok', 0)}",
        f"- checks_warning: {summary.get('checks_warning', 0)}",
        f"- checks_fail: {summary.get('checks_fail', 0)}",
        f"- plan_code: {plan.get('plan_code')}",
        f"- camera_limit: {plan.get('camera_limit')}",
        "",
        "## Discovery",
        "",
        f"- executed: {discovery.get('executed')}",
        f"- detected_count: {discovery.get('detected_count', 0)}",
        f"- recommended_count: {discovery.get('recommended_count', 0)}",
    ]
    recommended_ips = discovery.get("recommended_camera_ips") or []
    if recommended_ips:
        lines.append(f"- recommended_camera_ips: {', '.join(str(ip) for ip in recommended_ips)}")
    else:
        lines.append("- recommended_camera_ips: none")

    lines.extend(["", "## Missing Env", ""])
    if missing_env:
        for key in missing_env:
            lines.append(f"- {key}")
    else:
        lines.append("- none")

    lines.extend(["", "## Checks", ""])
    for item in checks:
        lines.append(
            f"- {item.get('key')}: status={item.get('status')} reason={item.get('reason_code')} message={item.get('message')}"
        )
    if not checks:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def export_onboarding_readiness_report(
    payload: dict[str, Any],
    *,
    export_json_path: str = "",
    export_markdown_path: str = "",
    generated_at: Optional[str] = None,
) -> dict[str, str]:
    output_paths: dict[str, str] = {}

    if export_json_path:
        json_target = Path(export_json_path).expanduser().resolve()
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        output_paths["json"] = str(json_target)

    if export_markdown_path:
        markdown_target = Path(export_markdown_path).expanduser().resolve()
        markdown_target.parent.mkdir(parents=True, exist_ok=True)
        markdown_target.write_text(
            render_onboarding_readiness_markdown(payload, generated_at=generated_at),
            encoding="utf-8",
        )
        output_paths["markdown"] = str(markdown_target)

    return output_paths
