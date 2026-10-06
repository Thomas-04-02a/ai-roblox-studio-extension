import unittest

from bridge.mock_roblox_server import MockRobloxMCPServer


class MockMCPServerTests(unittest.TestCase):
    def test_tools_include_expected_names(self):
        server = MockRobloxMCPServer()
        self.assertIn("inspect_tree", server.tools)
        self.assertIn("read_script", server.tools)

    def test_build_response_handles_write_script(self):
        server = MockRobloxMCPServer()
        result = server.build_response("write_script", {"path": "ServerScriptService.Test", "source": "print('ok')"})
        self.assertTrue(result["ok"])
        self.assertTrue(result["written"])


if __name__ == "__main__":
    unittest.main()
