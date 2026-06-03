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
    assert payload["capabilities"]["test_stream"] is True
    assert payload["capabilities"]["dvrip_icsee"] is True


def test_setup_api_test_rtsp_requires_rtsp_url():
    code, payload = build_setup_api_response(
        path="/onboarding/test-rtsp",
        discovery_provider=lambda: [],
    )
    assert code == 400
    assert payload["ok"] is False
    assert payload["error"] == "rtsp_url_required"


def test_setup_api_test_stream_auto_falls_back_to_dvrip(monkeypatch):
    monkeypatch.setattr(
        "dalevision_edge_agent.rtsp_test.test_rtsp",
        lambda **_kwargs: {"ok": False, "error": "rtsp_timeout"},
    )
    monkeypatch.setattr(
        "dalevision_edge_agent.dvrip_icsee.probe_dvrip_icsee",
        lambda **_kwargs: {
            "ok": True,
            "protocol": "dvrip",
            "working_channel": 0,
            "working_stream": "main",
            "latency_ms": 123,
        },
    )

    code, payload = build_setup_api_response(
        path="/onboarding/test-stream?connection_type=auto&ip=192.168.15.74&user=admin&password=pass",
        discovery_provider=lambda: [],
    )
    assert code == 200
    assert payload["ok"] is True
    assert payload["validated_protocol"] == "dvrip"
    assert payload["attempts"][0]["protocol"] == "rtsp"
    assert payload["attempts"][1]["protocol"] == "dvrip"


def test_setup_api_snapshot_prefers_explicit_rtsp_url(monkeypatch):
    captured: dict = {}

    def fake_snapshot(camera_id: str, rtsp_urls: list[str]):
        captured["camera_id"] = camera_id
        captured["rtsp_urls"] = list(rtsp_urls)
        return None

    monkeypatch.setattr(
        "dalevision_edge_agent.setup_api.stream_manager.get_snapshot_with_fallbacks",
        fake_snapshot,
    )

    code, payload = build_setup_api_response(
        path=(
            "/onboarding/snapshot?"
            "ip=192.168.15.4&user=admin&password=pass&channel=2&"
            "rtsp_url=rtsp://admin:pass@192.168.15.4:554/cam/realmonitor?channel=2%26subtype=1%26unicast=true%26proto=Onvif"
        ),
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["ok"] is False
    assert captured["camera_id"] == "192_168_15_4_ch2"
    assert captured["rtsp_urls"][0] == (
        "rtsp://admin:pass@192.168.15.4:554/cam/realmonitor?channel=2&subtype=1&unicast=true&proto=Onvif"
    )


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
    monkeypatch.delenv("DALE_APP_DIR", raising=False)
    monkeypatch.setenv("DALEVISION_EDGE_AGENT_VERSION", expected_version)
    monkeypatch.delenv("EDGE_AGENT_VERSION", raising=False)

    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["version"] == expected_version


def test_setup_api_health_prefers_versioned_app_dir_over_stale_config(monkeypatch, tmp_path):
    app_dir = tmp_path / "DaleVision" / "app" / "1.0.43"
    app_dir.mkdir(parents=True)
    config_path = tmp_path / "agent_config.json"
    config_path.write_text(json.dumps({"installed_version": "1.0.30"}), encoding="utf-8")

    monkeypatch.setenv("DALE_APP_DIR", str(app_dir))
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DALEVISION_EDGE_AGENT_VERSION", "1.0.30")

    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["version"] == "1.0.43"


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


def test_setup_api_local_runtime_diagnostics_response(monkeypatch):
    def fake_run_cmd(command: str, timeout_seconds: int = 8):
        if "netstat" in command:
            return "TCP    127.0.0.1:8787     0.0.0.0:0      LISTENING      1234"
        if "tasklist" in command:
            return "python.exe                   1234 Console                    1     50,000 K"
        if "schtasks" in command:
            return "TaskName: \\DaleVision Edge Agent"
        if "sc query" in command:
            return "SERVICE_NAME: DaleVisionEdgeAgent"
        return ""

    monkeypatch.setattr("dalevision_edge_agent.setup_api._run_cmd", fake_run_cmd)

    code, payload = build_setup_api_response(
        path="/onboarding/local-runtime-diagnostics",
        discovery_provider=lambda: [],
    )

    assert code == 200
    assert payload["ok"] is True
    assert payload["runtime_local_reachable"] is True
    assert payload["checks"]["port_8787_listening"] is True
    assert payload["checks"]["python_process_detected"] is True


def test_setup_api_runtime_control_pause_and_resume(monkeypatch, tmp_path):
    monkeypatch.setenv("DALE_CONFIG_DIR", str(tmp_path))

    code_pause, payload_pause = build_setup_api_response(
        path="/onboarding/runtime-control?action=pause",
        discovery_provider=lambda: [],
    )
    assert code_pause == 200
    assert payload_pause["ok"] is True
    assert payload_pause["action"] == "pause"
    assert payload_pause["state"]["paused"] is True

    code_status, payload_status = build_setup_api_response(
        path="/onboarding/runtime-control?action=status",
        discovery_provider=lambda: [],
    )
    assert code_status == 200
    assert payload_status["state"]["paused"] is True

    code_resume, payload_resume = build_setup_api_response(
        path="/onboarding/runtime-control?action=resume",
        discovery_provider=lambda: [],
    )
    assert code_resume == 200
    assert payload_resume["ok"] is True
    assert payload_resume["action"] == "resume"
    assert payload_resume["state"]["paused"] is False
