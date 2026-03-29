from dalevision_edge_agent.onboarding_readiness import build_onboarding_readiness


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
