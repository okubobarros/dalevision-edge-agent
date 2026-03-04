from __future__ import annotations

import logging

from dalevision_edge_agent import rtsp_test


def test_rtsp_digest_challenge_fallback_to_connectivity(monkeypatch) -> None:
    calls = []

    def fake_check_camera_health(*_args, **kwargs):
        calls.append(kwargs.get("perform_describe"))
        if kwargs.get("perform_describe"):
            return {
                "status": "error",
                "error": "unauthorized",
                "latency_ms": None,
                "checked_at": "2026-03-04T00:00:00Z",
            }
        return {
            "status": "online",
            "error": None,
            "latency_ms": 90,
            "checked_at": "2026-03-04T00:00:01Z",
        }

    monkeypatch.setattr(rtsp_test, "check_camera_health", fake_check_camera_health)
    monkeypatch.setattr(
        rtsp_test,
        "capture_snapshot_if_possible",
        lambda **_kwargs: {"snapshot_status": "skip", "snapshot_local_path": None},
    )
    logger = logging.getLogger("test-rtsp-fallback")
    logger.addHandler(logging.NullHandler())

    result = rtsp_test.test_rtsp(
        ip="192.168.15.4",
        user="admin",
        password="secret",
        channel=1,
        subtype=0,
        timeout_seconds=6,
        logger=logger,
    )

    assert result["ok"] is True
    assert calls[:2] == [True, False]
