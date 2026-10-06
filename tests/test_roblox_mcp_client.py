import unittest

from bridge.roblox_mcp import RobloxMCPClient


class RobloxMCPClientTests(unittest.TestCase):
    def test_launcher_path_uses_local_app_data(self):
        client = RobloxMCPClient()
        self.assertTrue(client.launcher_path.lower().endswith("roblox\\mcp.bat") or client.launcher_path.lower().endswith("roblox/mcp.bat"))

    def test_status_snapshot_reports_stdio_backend(self):
        client = RobloxMCPClient()
        snapshot = client.get_status_snapshot()
        self.assertEqual("stdio", snapshot["backend"])
        self.assertIn(snapshot["status"], {"connected", "launcher_missing", "not_connected", "process_crashed", "mock_active"})

    def test_status_snapshot_auto_starts_launcher_when_needed(self):
        client = RobloxMCPClient()
        client._last_error = None
        snapshot = client.get_status_snapshot()
        self.assertTrue(snapshot["mcp_bat_found"])
        self.assertIn(snapshot["status"], {"connected", "not_connected", "launcher_missing"})
        self.assertTrue(snapshot["process_running"] or snapshot["status"] == "connected")

    def test_ensure_stdio_connection_fails_cleanly_when_launcher_missing(self):
        client = RobloxMCPClient()
        client.launcher_path = "C:/definitely/missing/mcp.bat"
        result = client.ensure_stdio_connection()
        self.assertFalse(result)
        self.assertFalse(client.connected)
        self.assertIn("launcher", str(client._last_error).lower())

    def test_normalize_tool_list_handles_tool_metadata(self):
        client = RobloxMCPClient()
        discovered = client._normalize_tool_list([
            {"name": "custom_tool", "description": "Custom tool"},
            {"tool": "another_tool", "description": "Another tool"},
        ])
        self.assertIn("custom_tool", discovered)
        self.assertIn("another_tool", discovered)


if __name__ == "__main__":
    unittest.main()
