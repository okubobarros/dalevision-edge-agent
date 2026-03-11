from __future__ import annotations

import logging

from dalevision_edge_agent.main import _parse_cameras_json, _resolve_camera_source_mode


def test_parse_cameras_json_accepts_ip_without_rtsp() -> None:
    logger = logging.getLogger("test")
    payload, error = _parse_cameras_json(
        '[{"id":"cam-1","ip":"192.168.0.10","username":"admin","password":"x"}]',
        logger,
    )
    assert error is None
    assert len(payload) == 1
    assert payload[0]["camera_id"] == "cam-1"
    assert payload[0]["ip"] == "192.168.0.10"


def test_resolve_camera_source_mode_defaults_to_api_first(monkeypatch) -> None:
    monkeypatch.delenv("CAMERA_SOURCE_MODE", raising=False)
    assert _resolve_camera_source_mode() == "api_first"


def test_resolve_camera_source_mode_local_only(monkeypatch) -> None:
    monkeypatch.setenv("CAMERA_SOURCE_MODE", "local_only")
    assert _resolve_camera_source_mode() == "local_only"
