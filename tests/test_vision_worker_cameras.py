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
    monkeypatch.setenv("ProgramData", str(tmp_path))

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


@patch("dalevision_edge_agent.vision.worker.requests.get")
def test_fetch_cameras_uses_env_file_fallback_when_process_env_is_empty(mock_get, monkeypatch, tmp_path) -> None:
    cameras_payload = [
        {"id": "cam-1", "name": "Cam 1", "rtsp_url": "rtsp://10.0.0.10:554/stream"},
    ]
    env_path = tmp_path / ".env"
    env_path.write_text(
        "CAMERA_SYNC_ENABLED=0\n"
        f"CAMERAS_JSON={json.dumps(cameras_payload)}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CAMERAS_JSON", raising=False)
    monkeypatch.setenv("CAMERA_SYNC_ENABLED", "0")
    monkeypatch.setenv("VISION_CAMERAS_CACHE_PATH", str(tmp_path / "cameras_cache.json"))
    monkeypatch.setenv("ProgramData", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )

    cameras = worker._fetch_cameras()

    assert len(cameras) == 1
    assert cameras[0]["id"] == "cam-1"
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
    monkeypatch.setenv("ProgramData", str(tmp_path))

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


def test_extract_roi_uses_remote_roi_when_local_roi_is_empty() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    cam = {
        "id": "cam-1",
        "camera_id": "cam-1",
        "zone_id": "zone-front",
        "roi_local": {"zones": {}, "lines": {}},
        "roi": {
            "lines": [
                {
                    "id": "entry-line",
                    "name": "Linha Entrada",
                    "type": "line",
                    "metric_type": "entry_exit",
                    "ownership": "primary",
                    "zone_id": "zone-front",
                    "roi_entity_id": "entry-line",
                    "points": [{"x": 0.5, "y": 0.0}, {"x": 0.5, "y": 1.0}],
                }
            ]
        },
    }

    class Frame:
        shape = (100, 100, 3)

    roi = worker._extract_roi(cam, Frame())

    assert roi is not None
    assert "Linha Entrada" in roi["lines"]
    assert roi["line_meta"]["Linha Entrada"]["metric_type"] == "entry_exit"
