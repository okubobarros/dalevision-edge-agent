from unittest.mock import Mock, patch

from dalevision_edge_agent.update import check_for_update, send_update_report


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
