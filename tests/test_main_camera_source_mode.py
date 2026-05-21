from __future__ import annotations

import logging
import os

import dalevision_edge_agent.main as agent_main
from dalevision_edge_agent.main import (
    _normalize_vision_model_path,
    _parse_cameras_json,
    _resolve_camera_source_mode,
    _start_setup_api_background,
)


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


def test_normalize_vision_model_path_from_markdown_link(monkeypatch) -> None:
    logger = logging.getLogger("test")
    monkeypatch.setenv("VISION_MODEL_PATH", "[yolov8n.pt](http://yolov8n.pt/)")
    _normalize_vision_model_path(logger)
    assert os.getenv("VISION_MODEL_PATH") == "yolov8n.pt"


def test_normalize_vision_model_path_from_http_url(monkeypatch) -> None:
    logger = logging.getLogger("test")
    monkeypatch.setenv("VISION_MODEL_PATH", "https://example.com/models/yolov8n.pt?x=1")
    _normalize_vision_model_path(logger)
    assert os.getenv("VISION_MODEL_PATH") == "yolov8n.pt"


def test_start_setup_api_background_is_idempotent(monkeypatch) -> None:
    logger = logging.getLogger("test")
    monkeypatch.setenv("EDGE_SETUP_API_ENABLED", "1")
    monkeypatch.setattr(agent_main, "_SETUP_API_BOOTSTRAPPED", False)
    monkeypatch.setattr(agent_main, "_SETUP_API_DISCOVERY_HOOK", None)

    captured = {"thread_starts": 0}

    def fake_serve_setup_api(**_kwargs):
        return None

    class FakeThread:
        def __init__(self, target, name=None, daemon=None):
            self._target = target
            self.name = name
            self.daemon = daemon

        def start(self):
            captured["thread_starts"] += 1
            self._target()

    monkeypatch.setattr(agent_main, "serve_setup_api", fake_serve_setup_api)
    monkeypatch.setattr(agent_main.threading, "Thread", FakeThread)

    _start_setup_api_background(logger=logger)
    _start_setup_api_background(logger=logger)

    assert captured["thread_starts"] == 1


def test_start_setup_api_background_updates_discovery_hook_after_bootstrap(monkeypatch) -> None:
    logger = logging.getLogger("test")
    monkeypatch.setenv("EDGE_SETUP_API_ENABLED", "1")
    monkeypatch.setattr(agent_main, "_SETUP_API_BOOTSTRAPPED", False)
    monkeypatch.setattr(agent_main, "_SETUP_API_DISCOVERY_HOOK", None)

    captured: dict = {}

    def fake_serve_setup_api(**kwargs):
        captured["on_discovery_result"] = kwargs.get("on_discovery_result")
        return None

    class FakeThread:
        def __init__(self, target, name=None, daemon=None):
            self._target = target

        def start(self):
            self._target()

    monkeypatch.setattr(agent_main, "serve_setup_api", fake_serve_setup_api)
    monkeypatch.setattr(agent_main.threading, "Thread", FakeThread)

    _start_setup_api_background(logger=logger)

    hook_calls: list[dict] = []

    def hook(scan_results, payload):
        hook_calls.append({"scan_results": scan_results, "payload": payload})

    _start_setup_api_background(logger=logger, on_discovery_result=hook)
    callback = captured.get("on_discovery_result")
    assert callable(callback)

    callback([{"ip": "192.168.0.10"}], {"plan_code": "trial"})
    assert len(hook_calls) == 1
