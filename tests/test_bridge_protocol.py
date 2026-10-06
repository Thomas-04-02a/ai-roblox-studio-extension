import unittest

from bridge.protocol import ProtocolError, parse_tool_message, serialize_tool_result


class ProtocolTests(unittest.TestCase):
    def test_parse_tool(self):
        payload = {"id": "tool_1", "name": "read_script", "arguments": {"path": "ServerScriptService"}}
        self.assertEqual(parse_tool_message(payload)["name"], "read_script")

    def test_invalid_tool_missing_id(self):
        with self.assertRaises(ProtocolError):
            parse_tool_message({"name": "read_script", "arguments": {}})

    def test_duplicate_id_not_validated_here(self):
        first = serialize_tool_result("tool_1", True, {"status": "ok"})
        second = serialize_tool_result("tool_1", True, {"status": "ok"})
        self.assertEqual(first["id"], second["id"])

    def test_serialize_result(self):
        payload = serialize_tool_result("tool_2", True, {"ok": True}, None)
        self.assertTrue(payload["success"])
        self.assertIsNone(payload["error"])

    def test_parse_rbx_tool_wrapper(self):
        wrapped = "<RBX_TOOL>\n{\"id\": \"tool_9\", \"name\": \"read_script\", \"arguments\": {\"path\": \"ServerScriptService\"}}\n</RBX_TOOL>"
        payload = parse_tool_message(wrapped)
        self.assertEqual(payload["id"], "tool_9")
        self.assertEqual(payload["name"], "read_script")


if __name__ == "__main__":
    unittest.main()
