from dalevision_edge_agent.events import compute_idempotency_key


def test_compute_idempotency_key_accepts_bucket_minutes() -> None:
    key = compute_idempotency_key(
        event_name="edge_heartbeat",
        data={"store_id": "store-1"},
        ts="2026-04-02T19:45:21Z",
        bucket_minutes=1,
    )
    assert isinstance(key, str)
    assert len(key) == 64


def test_compute_idempotency_key_accepts_bucket_seconds() -> None:
    key = compute_idempotency_key(
        event_name="edge_heartbeat",
        data={"store_id": "store-1"},
        ts="2026-04-02T19:45:21Z",
        bucket_seconds=5,
    )
    assert isinstance(key, str)
    assert len(key) == 64

