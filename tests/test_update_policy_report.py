from unittest.mock import Mock, patch

from dalevision_edge_agent.update import (
    check_for_update,
    send_update_report,
    _build_update_report_idempotency_key,
)


@patch("dalevision_edge_agent.update.requests.get")
def test_check_for_update_uses_policy_endpoint(mock_get: Mock):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "channel": "canary",
            "target_version": "1.4.2",
            "package": {
                "url": "https://cdn.example.com/edge-1.4.2.zip",
                "sha256": "abc123",
            },
        },
    )
    logger = Mock()
    result = check_for_update(
        logger=logger,
        current_version="1.4.1",
        update_check_url="",
        auto_update_enabled=True,
        cloud_base_url="https://api.example.com",
        edge_token="tok_123",
        store_id="store-1",
        agent_id="edge-1",
    )
    assert result is not None
    assert result["version"] == "1.4.2"
    assert result["channel"] == "canary"
    assert result["auto_apply"] is True


@patch("dalevision_edge_agent.update.requests.get")
def test_check_for_update_falls_back_to_legacy_url(mock_get: Mock):
    responses = [
        Mock(status_code=500, json=lambda: {}),
        Mock(
            status_code=200,
            json=lambda: {
                "version": "1.4.3",
                "url": "https://cdn.example.com/edge-1.4.3.zip",
                "sha256": "abc123",
            },
        ),
    ]
    mock_get.side_effect = responses
    logger = Mock()
    result = check_for_update(
        logger=logger,
        current_version="1.4.2",
        update_check_url="https://updates.example.com/check",
        auto_update_enabled=False,
        cloud_base_url="https://api.example.com",
        edge_token="tok_123",
        store_id="store-1",
        agent_id="edge-1",
    )
    assert result is not None
    assert result["version"] == "1.4.3"
    assert result["auto_apply"] is False


@patch("dalevision_edge_agent.update.requests.post")
def test_send_update_report_success(mock_post: Mock):
    mock_post.return_value = Mock(status_code=201, json=lambda: {"ok": True})
    logger = Mock()
    ok, status, error = send_update_report(
        logger=logger,
        cloud_base_url="https://api.example.com",
        edge_token="tok_123",
        payload={
            "store_id": "store-1",
            "event": "edge_update_started",
            "status": "started",
        },
    )
    assert ok is True
    assert status == 201
    assert error is None
    _, kwargs = mock_post.call_args
    assert "idempotency_key" in kwargs["json"]
    assert kwargs["json"]["idempotency_key"]


@patch("dalevision_edge_agent.update.requests.post")
def test_send_update_report_preserves_custom_idempotency_key(mock_post: Mock):
    mock_post.return_value = Mock(status_code=201, json=lambda: {"ok": True})
    logger = Mock()
    ok, status, error = send_update_report(
        logger=logger,
        cloud_base_url="https://api.example.com",
        edge_token="tok_123",
        payload={
            "store_id": "store-1",
            "agent_id": "edge-1",
            "event": "edge_update_started",
            "status": "started",
            "idempotency_key": "custom-key-001",
        },
    )
    assert ok is True
    assert status == 201
    assert error is None
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["idempotency_key"] == "custom-key-001"


def test_build_update_report_idempotency_key_is_stable_without_timestamp():
    payload_a = {
        "store_id": "store-1",
        "agent_id": "edge-1",
        "from_version": "1.4.1",
        "to_version": "1.4.2",
        "channel": "stable",
        "event": "edge_update_healthy",
        "status": "healthy",
        "phase": "health_check",
        "attempt": 1,
        "timestamp": "2026-03-16T12:00:00Z",
    }
    payload_b = dict(payload_a)
    payload_b["timestamp"] = "2026-03-16T12:00:03Z"
    key_a = _build_update_report_idempotency_key(payload_a)
    key_b = _build_update_report_idempotency_key(payload_b)
    assert key_a == key_b


def test_send_update_report_missing_config():
    logger = Mock()
    ok, status, error = send_update_report(
        logger=logger,
        cloud_base_url="",
        edge_token="",
        payload={"event": "edge_update_started", "status": "started"},
    )
    assert ok is False
    assert status is None
    assert "missing_cloud_base_url_or_edge_token" in str(error)
