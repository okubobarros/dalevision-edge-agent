from dalevision_edge_agent.scan import build_discovery_candidates, build_onboarding_blueprint


def test_build_discovery_candidates_rtsp_ok():
    rows = [{"ip": "192.168.0.10", "ports": [554, 80], "confidence": "high"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "ok"
    assert out[0]["reason_code"] == "rtsp_port_open"


def test_build_discovery_candidates_nvr_warning():
    rows = [{"ip": "192.168.0.11", "ports": [37777], "confidence": "medium"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "warning"
    assert out[0]["reason_code"] == "nvr_port_open_rtsp_unknown"


def test_build_discovery_candidates_hikvision_warning():
    rows = [{"ip": "192.168.0.15", "ports": [8000], "confidence": "medium"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "warning"
    assert out[0]["reason_code"] == "hikvision_control_port_open_rtsp_unknown"


def test_build_discovery_candidates_onvif_warning():
    rows = [{"ip": "192.168.0.16", "ports": [8999], "confidence": "medium"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "warning"
    assert out[0]["reason_code"] == "onvif_port_open_rtsp_unknown"


def test_build_discovery_candidates_fail_when_no_supported_ports():
    rows = [{"ip": "192.168.0.12", "ports": [], "confidence": "low"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "fail"
    assert out[0]["reason_code"] == "no_supported_ports"


def test_onboarding_blueprint_trial_limit_and_recommendation():
    rows = [
        {"ip": "192.168.0.20", "ports": [554], "confidence": "high"},
        {"ip": "192.168.0.21", "ports": [554], "confidence": "medium"},
        {"ip": "192.168.0.22", "ports": [37777], "confidence": "high"},
        {"ip": "192.168.0.23", "ports": [80], "confidence": "low"},
    ]
    payload = build_onboarding_blueprint(rows, plan_code="trial")
    assert payload["plan_code"] == "trial"
    assert payload["camera_limit"] == 3
    assert payload["selection_guidance"]["recommended_camera_ips"] == [
        "192.168.0.20",
        "192.168.0.21",
        "192.168.0.22",
    ]
    assert len(payload["indicators"]) >= 1


def test_onboarding_blueprint_marks_non_selectable_when_fail():
    rows = [{"ip": "192.168.0.30", "ports": [], "confidence": "low"}]
    payload = build_onboarding_blueprint(rows, plan_code="trial")
    assert payload["candidates"][0]["selectable"] is False
    assert payload["candidates"][0]["recommended"] is False
