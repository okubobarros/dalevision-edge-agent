from dalevision_edge_agent.scan import build_discovery_candidates


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


def test_build_discovery_candidates_fail_when_no_supported_ports():
    rows = [{"ip": "192.168.0.12", "ports": [], "confidence": "low"}]
    out = build_discovery_candidates(rows)
    assert out[0]["status"] == "fail"
    assert out[0]["reason_code"] == "no_supported_ports"
