from dalevision_edge_agent.setup_api import build_setup_api_response


def test_setup_api_health_response():
    code, payload = build_setup_api_response(
        path="/health",
        discovery_provider=lambda: [],
    )
    assert code == 200
    assert payload["ok"] is True
    assert payload["service"] == "edge_setup_api"


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


def test_setup_api_not_found_response():
    code, payload = build_setup_api_response(
        path="/unknown",
        discovery_provider=lambda: [],
    )
    assert code == 404
    assert payload["ok"] is False
    assert payload["error"] == "not_found"
