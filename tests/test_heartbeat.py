from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dalevision_edge_agent.heartbeat import send_heartbeat  # noqa: E402


class HeartbeatTests(unittest.TestCase):
    @patch("dalevision_edge_agent.heartbeat.requests.post")
    def test_send_heartbeat_includes_camera_fields(self, mock_post: Mock) -> None:
        response = Mock()
        response.status_code = 201
        mock_post.return_value = response

        ok, status, error = send_heartbeat(
            url="https://api.example.com/api/edge/events/",
            edge_token="token",
            store_id="store-1",
            agent_id="agent-1",
            version="0.1.0",
            extra_data={
                "cameras_total": 2,
                "cameras_online": 1,
                "cameras_degraded": 0,
                "cameras_offline": 1,
                "cameras": [
                    {"camera_id": "cam-1", "status": "online", "roi_version": "v1"},
                    {"camera_id": "cam-2", "status": "offline", "roi_version": "v2"},
                ],
            },
        )

        self.assertTrue(ok)
        self.assertEqual(201, status)
        self.assertIsNone(error)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(2, payload["data"]["cameras_total"])
        self.assertEqual("cam-1", payload["data"]["cameras"][0]["camera_id"])


if __name__ == "__main__":
    unittest.main()
