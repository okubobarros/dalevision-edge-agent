from dalevision_edge_agent.heartbeat_client import HeartbeatClient, HeartbeatPayload


def test_heartbeat_client_sends_identity_payload(monkeypatch) -> None:
    captured = {}

    def fake_send_heartbeat(**kwargs):
        captured.update(kwargs)
        return True, 201, None

    monkeypatch.setattr("dalevision_edge_agent.heartbeat_client.send_heartbeat", fake_send_heartbeat)
    client = HeartbeatClient()
    payload = HeartbeatPayload(
        device_key="edge-abc",
        installed_version="1.2.3",
        update_channel="stable",
        status="active",
        uptime_seconds=15,
        cameras_connected=2,
        inference_fps=0.0,
    )

    ok, status, error = client.send(
        url="https://api.example.com/api/edge/events/",
        edge_token="token",
        store_id="store-1",
        agent_id="agent-1",
        version="1.2.3",
        payload=payload,
        extra_data={"cameras_total": 2},
    )

    assert ok is True
    assert status == 201
    assert error is None
    extra = captured["extra_data"]
    assert extra["device_key"] == "edge-abc"
    assert extra["installed_version"] == "1.2.3"
    assert extra["update_channel"] == "stable"
    assert extra["status"] == "active"
    assert extra["cameras_total"] == 2

