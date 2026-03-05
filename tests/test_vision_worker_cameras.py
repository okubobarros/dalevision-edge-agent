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


@patch("dalevision_edge_agent.vision.worker.fetch_roi")
def test_fetch_cameras_enriches_local_cameras_with_remote_roi(mock_fetch_roi, monkeypatch, tmp_path) -> None:
    cameras_payload = [
        {"id": "cam-1", "name": "Cam Caixa", "rtsp_url": "rtsp://10.0.0.10:554/stream"},
    ]
    mock_fetch_roi.return_value = (
        {
            "config_json": {
                "roi_version": 7,
                "zones": [
                    {
                        "name": "Salao",
                        "type": "poly",
                        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.2}, {"x": 0.3, "y": 0.3}],
                    }
                ],
            }
        },
        "7",
        False,
        None,
    )
    monkeypatch.setenv("CAMERAS_JSON", json.dumps(cameras_payload))
    monkeypatch.setenv("CAMERA_SYNC_ENABLED", "0")
    monkeypatch.setenv("VISION_LOCAL_CAMERAS_ONLY", "1")
    monkeypatch.setenv("VISION_CAMERAS_CACHE_PATH", str(tmp_path / "cameras_cache.json"))

    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )

    cameras = worker._fetch_cameras()

    assert cameras[0]["roi"]["zones"][0]["name"] == "area_consumo"
    assert cameras[0]["roi"]["roi_version"] == 7
    mock_fetch_roi.assert_called_once_with(
        "cam-1",
        cloud_base_url="https://api.example.com",
        edge_token="token",
        logger=worker.logger,
    )


def test_resolve_role_maps_caixa_name_to_balcao() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )

    role = worker._resolve_role(
        {"id": "cam-1", "camera_id": "cam-1", "name": "Cam1 Caixa", "external_id": "Cam1 Caixa"}
    )

    assert role == "balcao"
