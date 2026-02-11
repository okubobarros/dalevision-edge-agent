import unittest

from src.transport.api_client import build_edge_headers


class BuildEdgeHeadersTests(unittest.TestCase):
    def test_build_edge_headers(self):
        token = "token-123"
        headers = build_edge_headers(token)
        self.assertEqual(headers["X-EDGE-TOKEN"], token)
        self.assertEqual(headers["Content-Type"], "application/json")


if __name__ == "__main__":
    unittest.main()
