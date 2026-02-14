from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dalevision_edge_agent.cameras import (  # noqa: E402
    build_camera_heartbeat_fields,
    capture_snapshot_if_possible,
    fetch_cameras,
    fetch_roi,
)


class CamerasTests(unittest.TestCase):
    @patch("dalevision_edge_agent.cameras.requests.request")
    def test_fetch_cameras_from_edge_endpoint(self, mock_request: Mock) -> None:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "cam-1", "rtsp_url": "rtsp://10.0.0.10:554/stream"},
                {"id": "cam-2", "rtsp_url": "rtsp://10.0.0.11:554/stream"},
            ]
        }
        mock_request.return_value = mock_response

        cameras, error = fetch_cameras(
            cloud_base_url="https://api.example.com",
            edge_token="token",
            store_id="store-1",
        )

        self.assertIsNone(error)
        self.assertEqual(2, len(cameras))
        self.assertEqual("cam-1", cameras[0]["id"])

    @patch("dalevision_edge_agent.cameras.requests.request")
    def test_fetch_roi_skips_download_when_cached_version_matches(
        self,
        mock_request: Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            cached_path = cache_dir / "cam-1.json"
            cached_path.write_text(
                '{"version":"v5","data":{"roi":[{"x":1,"y":1}]}}',
                encoding="utf-8",
            )

            payload, version, from_cache, error = fetch_roi(
                "cam-1",
                cloud_base_url="https://api.example.com",
                edge_token="token",
                expected_version="v5",
                cache_dir=cache_dir,
            )

            self.assertIsNone(error)
            self.assertTrue(from_cache)
            self.assertEqual("v5", version)
            self.assertIsNotNone(payload)
            mock_request.assert_not_called()

    def test_camera_aggregation_for_heartbeat(self) -> None:
        fields = build_camera_heartbeat_fields(
            {
                "cam-1": {"status": "online", "roi_version": "v1"},
                "cam-2": {"status": "offline", "roi_version": "v2"},
                "cam-3": {"status": "degraded", "roi_version": "v3"},
                "cam-4": {"status": "mystery", "roi_version": "v4"},
            }
        )

        self.assertEqual(4, fields["cameras_total"])
        self.assertEqual(1, fields["cameras_online"])
        self.assertEqual(1, fields["cameras_degraded"])
        self.assertEqual(1, fields["cameras_offline"])
        self.assertEqual(1, fields["cameras_unknown"])
        self.assertEqual(4, len(fields["cameras"]))

    @patch("dalevision_edge_agent.cameras._try_import_cv2")
    @patch("dalevision_edge_agent.cameras._ffmpeg_path")
    def test_snapshot_skips_when_opencv_and_ffmpeg_absent(
        self,
        mock_ffmpeg_path: Mock,
        mock_try_import: Mock,
    ) -> None:
        mock_try_import.return_value = None
        mock_ffmpeg_path.return_value = None
        logger = Mock()

        result = capture_snapshot_if_possible(
            camera_id="cam-1",
            rtsp_url="rtsp://user:pass@10.0.0.10:554/stream1",
            logger=logger,
        )

        self.assertIsNone(result)

    @patch("dalevision_edge_agent.cameras.subprocess.run")
    @patch("dalevision_edge_agent.cameras._try_import_cv2")
    @patch("dalevision_edge_agent.cameras._ffmpeg_path")
    def test_snapshot_ffmpeg_failure_does_not_crash(
        self,
        mock_ffmpeg_path: Mock,
        mock_try_import: Mock,
        mock_run: Mock,
    ) -> None:
        mock_try_import.return_value = None
        mock_ffmpeg_path.return_value = "ffmpeg"
        mock_run.return_value = Mock(returncode=1, stderr="boom")
        logger = Mock()

        result = capture_snapshot_if_possible(
            camera_id="cam-2",
            rtsp_url="rtsp://user:pass@10.0.0.11:554/stream1",
            logger=logger,
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
