import unittest

from bridge.websocket_server import BridgeWebSocketServer


class WebSocketServerTests(unittest.TestCase):
    def test_status_snapshot_includes_bridge_and_mcp(self):
        server = BridgeWebSocketServer()
        snapshot = server.status_snapshot()
        self.assertIn("bridge", snapshot)
        self.assertIn("mcp", snapshot)


if __name__ == "__main__":
    unittest.main()
