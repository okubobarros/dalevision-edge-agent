from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from dalevision_edge_agent.vision.worker import VisionWorker


@patch("dalevision_edge_agent.vision.worker.requests.post", side_effect=Exception("network_down"))
def test_vision_event_failed_send_is_enqueued(mock_post, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VISION_OUTBOX_ENABLED", "1")
    monkeypatch.setenv("VISION_OUTBOX_PATH", str(tmp_path / "vision_outbox.sqlite"))
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    payload = {
        "store_id": "store-1",
        "camera_id": "cam-1",
        "camera_role": "entrada",
        "roi_version": 1,
        "bucket": {
            "seconds": 30,
            "start": "2026-01-01T00:00:00+00:00",
            "end": "2026-01-01T00:00:30+00:00",
        },
        "traffic": {"footfall": 1, "entries": 1, "exits": 0, "engaged": 0, "dwell_seconds_avg": 0},
        "conversion": {"queue_avg_seconds": 0, "staff_active_est": 0, "checkout_events": 0},
        "debug": {"frame_source": "rtsp_or_snapshot", "snapshot_url_present": False, "line_crossings_count": 1},
    }

    worker._send_event(payload)

    assert mock_post.called
    assert worker._outbox is not None
    assert worker._outbox.size() == 1


def test_outbox_flush_marks_event_sent(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VISION_OUTBOX_ENABLED", "1")
    monkeypatch.setenv("VISION_OUTBOX_PATH", str(tmp_path / "vision_outbox.sqlite"))
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    envelope = {
        "event_name": "vision.queue_state.v1",
        "source": "edge",
        "receipt_id": "abc123",
        "idempotency_key": "abc123",
        "ts": "2026-01-01T00:00:00+00:00",
        "data": {"store_id": "store-1", "camera_id": "cam-1"},
    }
    assert worker._outbox is not None
    assert worker._outbox.enqueue(envelope) is True

    with patch.object(worker, "_send_now", return_value=(True, 201, None)) as mock_send:
        worker._flush_outbox(limit=10)

    assert mock_send.called
    assert worker._outbox.size() == 0


def test_outbox_oldest_pending_seconds(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VISION_OUTBOX_ENABLED", "1")
    monkeypatch.setenv("VISION_OUTBOX_PATH", str(tmp_path / "vision_outbox.sqlite"))
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    envelope = {
        "event_name": "vision.queue_state.v1",
        "source": "edge",
        "receipt_id": "abc-oldest-1",
        "idempotency_key": "abc-oldest-1",
        "ts": "2026-01-01T00:00:00+00:00",
        "data": {"store_id": "store-1", "camera_id": "cam-1"},
    }
    assert worker._outbox is not None
    worker._outbox.enqueue(envelope)

    with patch("dalevision_edge_agent.vision.outbox.time.time", return_value=10_000.0):
        age = worker._outbox.oldest_pending_seconds()
    assert age >= 0


def test_outbox_chaos_network_recovery_flushes_all(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VISION_OUTBOX_ENABLED", "1")
    monkeypatch.setenv("VISION_OUTBOX_PATH", str(tmp_path / "vision_outbox.sqlite"))
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    assert worker._outbox is not None

    # Simula 3 eventos acumulados durante indisponibilidade de rede
    for idx in range(3):
        envelope = {
            "event_name": "vision.queue_state.v1",
            "source": "edge",
            "receipt_id": f"chaos-{idx}",
            "idempotency_key": f"chaos-{idx}",
            "ts": "2026-01-01T00:00:00+00:00",
            "data": {"store_id": "store-1", "camera_id": f"cam-{idx}"},
        }
        assert worker._outbox.enqueue(envelope)

    # Primeiro flush: rede fora, nada deve ser removido
    with patch.object(worker, "_send_now", return_value=(False, None, "network_down")) as mock_down:
        worker._flush_outbox(limit=10)
    assert mock_down.called
    assert worker._outbox.size() == 3

    # Segundo flush: rede voltou, tudo deve ser enviado e limpo
    with patch("dalevision_edge_agent.vision.outbox.time.time", return_value=9_999_999_999.0):
        with patch.object(worker, "_send_now", return_value=(True, 201, None)) as mock_up:
            worker._flush_outbox(limit=10)
    assert mock_up.called
    assert worker._outbox.size() == 0


def test_runtime_entrypoint_is_canonical() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert 'dalevision-edge-agent = "dalevision_edge_agent.main:main"' in content
