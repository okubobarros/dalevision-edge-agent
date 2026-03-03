from __future__ import annotations

import logging
from unittest.mock import Mock, patch

from dalevision_edge_agent import main as agent_main
from dalevision_edge_agent.cameras import send_camera_health_event


@patch("dalevision_edge_agent.cameras.requests.request")
def test_send_camera_health_event_posts_edge_events(mock_request: Mock) -> None:
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"ok": True}
    mock_request.return_value = mock_response

    ok, status, error = send_camera_health_event(
        cloud_base_url="https://api.example.com",
        edge_token="token",
        store_id="store-1",
        agent_id="agent-1",
        camera_health={
            "camera_id": "cam-1",
            "status": "online",
            "latency_ms": 123,
            "error": None,
            "checked_at": "2026-03-03T00:00:00Z",
        },
    )

    assert ok is True
    assert status == 201
    assert error is None
    kwargs = mock_request.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/api/edge/events/"
    assert kwargs["json"]["event_name"] == "camera_health"
    assert kwargs["json"]["data"]["camera_id"] == "cam-1"
    assert kwargs["json"]["data"]["store_id"] == "store-1"
    assert kwargs["json"]["data"]["agent_id"] == "agent-1"


def test_run_camera_health_once_posts_one_event_per_camera(monkeypatch) -> None:
    logger = logging.getLogger("test-camera-health-local")
    logger.addHandler(logging.NullHandler())
    posted_payloads = []

    def fake_check_camera_health(*_args, **_kwargs):
        return {
            "camera_id": "cam-1",
            "status": "online",
            "latency_ms": 80,
            "error": None,
            "checked_at": "2026-03-03T00:00:00Z",
        }

    def fake_send_camera_health_event(**kwargs):
        posted_payloads.append(kwargs["camera_health"])
        return True, 201, None

    monkeypatch.setattr(agent_main, "check_camera_health", fake_check_camera_health)
    monkeypatch.setattr(agent_main, "send_camera_health_event", fake_send_camera_health_event)

    count = agent_main._run_camera_health_once(
        cloud_base_url="https://api.example.com",
        edge_token="token",
        store_id="store-1",
        agent_id="agent-1",
        cameras=[
            {"id": "cam-1", "rtsp_url": "rtsp://10.0.0.10:554/stream"},
            {"id": "cam-2", "rtsp_url": "rtsp://10.0.0.11:554/stream"},
        ],
        logger=logger,
        state_store={},
    )

    assert count == 2
    assert len(posted_payloads) == 2
    assert all(payload["status"] == "online" for payload in posted_payloads)
