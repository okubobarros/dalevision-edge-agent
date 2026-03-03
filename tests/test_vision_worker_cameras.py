from __future__ import annotations

import json
from unittest.mock import Mock, patch

from dalevision_edge_agent.vision.worker import VisionWorker


@patch("dalevision_edge_agent.vision.worker.requests.get")
def test_fetch_cameras_uses_cameras_json_without_v1_calls(mock_get, monkeypatch, tmp_path) -> None:
    cameras_payload = [
        {"id": "cam-1", "name": "Cam 1", "rtsp_url": "rtsp://10.0.0.10:554/stream"},
        {"id": "cam-2", "name": "Cam 2", "rtsp_url": "rtsp://10.0.0.11:554/stream"},
        {"id": "cam-3", "name": "Cam 3", "rtsp_url": "rtsp://10.0.0.12:554/stream"},
    ]
    monkeypatch.setenv("CAMERAS_JSON", json.dumps(cameras_payload))
    monkeypatch.setenv("CAMERA_SYNC_ENABLED", "0")
    monkeypatch.setenv("VISION_CAMERAS_CACHE_PATH", str(tmp_path / "cameras_cache.json"))

    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    cameras = worker._fetch_cameras()

    assert len(cameras) == 3
    assert [cam["id"] for cam in cameras] == ["cam-1", "cam-2", "cam-3"]
    mock_get.assert_not_called()
