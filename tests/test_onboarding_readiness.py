from pathlib import Path

from dalevision_edge_agent.onboarding_readiness import (
    build_onboarding_readiness,
    export_onboarding_readiness_report,
    render_onboarding_readiness_markdown,
)


class _SettingsStub:
    cloud_base_url = "https://api.example.com"
    store_id = "550e8400-e29b-41d4-a716-446655440000"
    agent_id = "edge-store-001"
    max_active_cameras = 3
    auto_update_enabled = True


def test_readiness_ready_when_settings_valid(monkeypatch):
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.load_env_from_cwd",
        lambda: "C:/tmp/.env",
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.describe_env_file",
        lambda _path: {"path": "C:/tmp/.env", "exists": True},
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.load_settings",
        lambda: _SettingsStub(),
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness._get_env_with_legacy",
        lambda _name, _legacy: "value",
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.shutil.which",
        lambda _cmd: "C:/ffmpeg/bin/ffmpeg.exe",
    )

    payload = build_onboarding_readiness(plan_code="trial", include_scan=False)

    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert payload["summary"]["checks_fail"] == 0
    assert payload["plan"]["camera_limit"] == 3
    assert payload["discovery"]["executed"] is False


def test_readiness_scan_summary_included_when_scan_enabled(monkeypatch):
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.load_env_from_cwd",
        lambda: "C:/tmp/.env",
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.describe_env_file",
        lambda _path: {"path": "C:/tmp/.env", "exists": True},
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.load_settings",
        lambda: _SettingsStub(),
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness._get_env_with_legacy",
        lambda _name, _legacy: "value",
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.onboarding_readiness.shutil.which",
        lambda _cmd: "C:/ffmpeg/bin/ffmpeg.exe",
    )

    payload = build_onboarding_readiness(
        plan_code="trial",
        include_scan=True,
        discovery_provider=lambda: [
            {"ip": "192.168.0.10", "ports": [554], "confidence": "high"},
        ],
    )

    assert payload["status"] == "ready"
    assert payload["discovery"]["executed"] is True
    assert payload["discovery"]["detected_count"] == 1
    assert payload["discovery"]["recommended_count"] == 1


def test_render_markdown_contains_summary_fields():
    payload = {
        "status": "needs_attention",
        "summary": {
            "checks_ok": 2,
            "checks_warning": 1,
            "checks_fail": 0,
            "missing_required_env": [],
        },
        "plan": {"plan_code": "trial", "camera_limit": 3},
        "discovery": {
            "executed": True,
            "detected_count": 2,
            "recommended_count": 1,
            "recommended_camera_ips": ["192.168.0.10"],
        },
        "checks": [
            {
                "key": "ffmpeg_runtime",
                "status": "warning",
                "reason_code": "ffmpeg_missing",
                "message": "ffmpeg não encontrado no PATH",
            }
        ],
    }

    markdown = render_onboarding_readiness_markdown(
        payload,
        generated_at="2026-03-29T12:00:00+00:00",
    )
    assert "DaleVision Edge Onboarding Readiness Report" in markdown
    assert "status: needs_attention" in markdown
    assert "plan_code: trial" in markdown
    assert "recommended_camera_ips: 192.168.0.10" in markdown
    assert "ffmpeg_runtime: status=warning" in markdown


def test_export_reports_writes_json_and_markdown(tmp_path: Path):
    payload = {
        "status": "ready",
        "summary": {"checks_ok": 3, "checks_warning": 0, "checks_fail": 0, "missing_required_env": []},
        "plan": {"plan_code": "trial", "camera_limit": 3},
        "discovery": {"executed": False, "detected_count": 0, "recommended_count": 0, "recommended_camera_ips": []},
        "checks": [],
    }
    json_path = tmp_path / "reports" / "readiness.json"
    md_path = tmp_path / "reports" / "readiness.md"

    output = export_onboarding_readiness_report(
        payload,
        export_json_path=str(json_path),
        export_markdown_path=str(md_path),
        generated_at="2026-03-29T12:00:00+00:00",
    )

    assert output["json"] == str(json_path.resolve())
    assert output["markdown"] == str(md_path.resolve())
    assert json_path.exists() is True
    assert md_path.exists() is True
    assert '"status": "ready"' in json_path.read_text(encoding="utf-8")
    assert "status: ready" in md_path.read_text(encoding="utf-8")
