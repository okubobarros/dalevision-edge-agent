from __future__ import annotations

from unittest.mock import Mock, patch

from dalevision_edge_agent.onboarding_events import sanitize_event_data, send_onboarding_event


def test_sanitize_event_data_removes_sensitive_keys_recursively() -> None:
    payload = {
        "store_id": "store-1",
        "edge_token": "secret",
        "camera": {
            "camera_id": "cam-1",
            "password": "123",
            "meta": {"authorization": "Bearer x"},
        },
        "items": [
            {"rtsp_url": "rtsp://admin:pass@camera"},
            {"camera_id": "cam-2"},
        ],
    }
    out = sanitize_event_data(payload)
    assert out["store_id"] == "store-1"
    assert "edge_token" not in out
    assert "password" not in out["camera"]
    assert "authorization" not in out["camera"]["meta"]
    assert "rtsp_url" not in out["items"][0]


@patch("dalevision_edge_agent.onboarding_events.requests.post")
def test_send_onboarding_event_posts_edge_event_envelope(mock_post: Mock) -> None:
    response = Mock()
    response.status_code = 201
    mock_post.return_value = response

    ok, status, error = send_onboarding_event(
        cloud_base_url="https://api.example.com",
        edge_token="edge-token",
        event_name="onboarding_started",
        data={"store_id": "store-1", "agent_id": "agent-1"},
    )

    assert ok is True
    assert status == 201
    assert error is None
    kwargs = mock_post.call_args.kwargs
    args = mock_post.call_args.args
    assert args[0] == "https://api.example.com/api/edge/events/"
    assert kwargs["json"]["event_name"] == "onboarding_started"
    assert kwargs["json"]["idempotency_key"] == kwargs["json"]["receipt_id"]
    assert kwargs["json"]["data"]["store_id"] == "store-1"
    assert "ts" in kwargs["json"]["data"]
