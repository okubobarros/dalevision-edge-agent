from unittest.mock import Mock, patch

from dalevision_edge_agent.update import (
    acquire_update_lock,
    apply_update_if_possible,
    check_for_update,
    release_update_lock,
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
            "rollout_window": {"start_local": "00:00", "end_local": "23:59", "timezone": "UTC"},
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


@patch("dalevision_edge_agent.update.requests.get")
def test_check_for_update_blocks_when_min_supported_not_met(mock_get: Mock):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "channel": "stable",
            "target_version": "1.4.2",
            "current_min_supported": "1.4.0",
            "rollout_window": {"start_local": "00:00", "end_local": "23:59", "timezone": "UTC"},
            "package": {
                "url": "https://cdn.example.com/edge-1.4.2.zip",
                "sha256": "abc123",
            },
        },
    )
    logger = Mock()
    result = check_for_update(
        logger=logger,
        current_version="1.3.9",
        update_check_url="",
        auto_update_enabled=True,
        cloud_base_url="https://api.example.com",
        edge_token="tok_123",
        store_id="store-1",
        agent_id="edge-1",
    )
    assert result is not None
    assert result["auto_apply"] is False
    assert result["blocked_reason_code"] == "UNSUPPORTED_VERSION"


@patch("dalevision_edge_agent.update._is_within_rollout_window", return_value=False)
@patch("dalevision_edge_agent.update.requests.get")
def test_check_for_update_blocks_outside_rollout_window(mock_get: Mock, _mock_window: Mock):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "channel": "stable",
            "target_version": "1.4.2",
            "rollout_window": {"start_local": "02:00", "end_local": "05:00", "timezone": "America/Sao_Paulo"},
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
    assert result["auto_apply"] is False
    assert result["blocked_reason_code"] == "ROLLOUT_WINDOW_CLOSED"


def test_update_lock_acquire_release(tmp_path):
    logger = Mock()
    with patch("dalevision_edge_agent.update.Path.cwd", return_value=tmp_path):
        ok1, lock_path, reason1 = acquire_update_lock(logger=logger, version="1.5.0")
        assert ok1 is True
        assert reason1 is None
        assert lock_path is not None and lock_path.exists()

        ok2, _, reason2 = acquire_update_lock(logger=logger, version="1.5.0")
        assert ok2 is False
        assert reason2 == "UPDATE_LOCKED"

        release_update_lock(logger=logger, lock_path=lock_path)
        assert not lock_path.exists()

        ok3, lock_path2, reason3 = acquire_update_lock(logger=logger, version="1.5.0")
        assert ok3 is True
        assert reason3 is None
        release_update_lock(logger=logger, lock_path=lock_path2)


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


@patch("dalevision_edge_agent.update.subprocess.Popen")
def test_apply_update_persists_attempt_in_pending_payload(mock_popen: Mock, tmp_path, monkeypatch):
    monkeypatch.setattr("dalevision_edge_agent.update.Path.cwd", lambda: tmp_path)
    monkeypatch.setattr("dalevision_edge_agent.update.subprocess.CREATE_NEW_CONSOLE", 0, raising=False)

    executable = tmp_path / "agent.exe"
    executable.write_bytes(b"old-binary")
    downloaded = tmp_path / "downloaded.exe"
    downloaded.write_bytes(b"new-binary")
    (tmp_path / "updates").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("dalevision_edge_agent.update.sys.argv", [str(executable)])

    logger = Mock()
    ok = apply_update_if_possible(
        logger=logger,
        current_version="1.4.1",
        update={
            "version": "1.4.2",
            "channel": "canary",
            "attempt": 7,
            "health_gate": {"max_boot_seconds": 120},
        },
        downloaded_path=downloaded,
    )

    assert ok is True
    assert mock_popen.called is True

    pending_path = tmp_path / "updates" / "pending.json"
    assert pending_path.exists()
    pending = __import__("json").loads(pending_path.read_text(encoding="utf-8"))
    assert pending["attempt"] == 7
    assert pending["to"] == "1.4.2"
