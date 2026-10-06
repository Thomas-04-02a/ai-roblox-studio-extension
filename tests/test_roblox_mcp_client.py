import threading
import time
import unittest

from bridge.mock_roblox_server import MockRobloxMCPServer
from bridge.roblox_mcp import RobloxMCPClient


class RobloxMCPClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = MockRobloxMCPServer()
        cls.server_thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.server_thread.start()
        time.sleep(0.25)

    def test_discover_tools_from_local_server(self):
        client = RobloxMCPClient(base_url="http://127.0.0.1:8767")
        tools = client.discover_tools()
        self.assertIn("inspect_tree", tools)
        self.assertTrue(client.connected)

    def test_discover_tools_handles_structured_tool_metadata(self):
        client = RobloxMCPClient(base_url="http://127.0.0.1:8767")
        discovered = client._normalize_tool_list([
            {"name": "custom_tool", "description": "Custom tool"},
            {"tool": "another_tool", "description": "Another tool"},
        ])
        self.assertIn("custom_tool", discovered)
        self.assertIn("another_tool", discovered)

    def test_call_tool_returns_server_payload(self):
        client = RobloxMCPClient(base_url="http://127.0.0.1:8767")
        response = client.call_tool("read_script", {"path": "ServerScriptService.Test"})
        self.assertTrue(response["ok"])
        self.assertIn("source", response)

    def test_call_tool_allows_dynamic_tool_names(self):
        client = RobloxMCPClient(base_url="http://127.0.0.1:8767")
        response = client.call_tool("custom_tool", {"query": "Workspace"})
        self.assertIn("ok", response)
        self.assertIn("error", response)

    def test_discover_tools_marks_offline_when_server_missing(self):
        client = RobloxMCPClient(base_url="http://127.0.0.1:1")
        client.base_urls = ["http://127.0.0.1:1"]
        client.base_url = "http://127.0.0.1:1"

        tools = client.discover_tools()
        self.assertEqual([], tools)
        self.assertFalse(client.connected)


if __name__ == "__main__":
    unittest.main()
