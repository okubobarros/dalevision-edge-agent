import json

from dalevision_edge_agent.setup_api import build_setup_api_response
from dalevision_edge_agent.setup_api import _redact_sensitive_text


def test_setup_api_health_response():
    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )
    assert code == 200
    assert payload["ok"] is True
    assert payload["service"] == "edge_setup_api"
    assert payload["capabilities"]["onboarding_installation_check"] is True


def test_setup_api_health_uses_installed_version_from_config(monkeypatch, tmp_path):
    config_path = tmp_path / "agent_config.json"
    expected_version = "latest-test-version"
    config_path.write_text(
        json.dumps({"installed_version": expected_version}),
        encoding="utf-8",
    )
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("DALEVISION_EDGE_AGENT_VERSION", raising=False)
    monkeypatch.delenv("EDGE_AGENT_VERSION", raising=False)

    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["version"] == expected_version


def test_setup_api_health_falls_back_to_launcher_version(monkeypatch, tmp_path):
    config_path = tmp_path / "missing_agent_config.json"
    expected_version = "launcher-dynamic-version"
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DALEVISION_EDGE_AGENT_VERSION", expected_version)
    monkeypatch.delenv("EDGE_AGENT_VERSION", raising=False)

    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["version"] == expected_version


def test_setup_api_blueprint_response_uses_plan_and_scan_results():
    def fake_discovery():
        return [
            {"ip": "192.168.0.10", "ports": [554], "confidence": "high"},
            {"ip": "192.168.0.11", "ports": [37777], "confidence": "medium"},
        ]

    code, payload = build_setup_api_response(
        path="/onboarding/blueprint?plan=trial",
        discovery_provider=fake_discovery,
    )
    assert code == 200
    assert payload["ok"] is True
    assert payload["plan_code"] == "trial"
    assert payload["camera_limit"] == 3
    assert len(payload["candidates"]) == 2
    assert payload["selection_guidance"]["recommended_camera_ips"] == [
        "192.168.0.10",
        "192.168.0.11",
    ]


def test_setup_api_blueprint_invokes_discovery_hook_once():
    captured: dict = {}

    def fake_discovery():
        return [{"ip": "192.168.0.10", "ports": [554], "confidence": "high"}]

    def hook(scan_results, payload):
        captured["count"] = len(scan_results)
        captured["plan"] = payload.get("plan_code")
        captured["candidates"] = len(payload.get("candidates") or [])

    code, payload = build_setup_api_response(
        path="/onboarding/blueprint?plan=trial",
        discovery_provider=fake_discovery,
        on_discovery_result=hook,
    )

    assert code == 200
    assert payload["ok"] is True
    assert captured == {"count": 1, "plan": "trial", "candidates": 1}


def test_setup_api_not_found_response():
    code, payload = build_setup_api_response(
        path="/unknown",
        discovery_provider=lambda: [],
    )
    assert code == 404
    assert payload["ok"] is False
    assert payload["error"] == "not_found"


def test_setup_api_redacts_rtsp_passwords_from_errors():
    text = "failed opening rtsp://admin:secret@192.168.1.10:554/live"
    redacted = _redact_sensitive_text(text)

    assert "secret" not in redacted
    assert "rtsp://admin:***@192.168.1.10:554/live" in redacted


def test_setup_api_readiness_response_uses_readiness_builder(monkeypatch):
    captured: dict = {}

    def fake_builder(*, plan_code: str, include_scan: bool, discovery_provider):
        captured["plan_code"] = plan_code
        captured["include_scan"] = include_scan
        captured["provider"] = callable(discovery_provider)
        return {"ok": True, "status": "ready", "checks": []}

    monkeypatch.setattr(
        "dalevision_edge_agent.setup_api.build_onboarding_readiness",
        fake_builder,
    )

    code, payload = build_setup_api_response(
        path="/onboarding/readiness?plan=trial&scan=1",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert captured == {
        "plan_code": "trial",
        "include_scan": True,
        "provider": True,
    }


def test_setup_api_installation_check_response_uses_builder(monkeypatch):
    captured: dict = {}

    def fake_builder():
        captured["called"] = True
        return {"ok": True, "status": "ready", "checks": []}

    monkeypatch.setattr(
        "dalevision_edge_agent.setup_api.build_installation_check_payload",
        fake_builder,
    )

    code, payload = build_setup_api_response(
        path="/onboarding/installation-check",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert captured == {"called": True}
