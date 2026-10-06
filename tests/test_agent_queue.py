import unittest

from bridge.protocol import serialize_tool_result


class QueueSafetyTests(unittest.TestCase):
    def test_result_payload_is_valid(self):
        payload = serialize_tool_result("queue_1", True, {"message": "ok"}, None)
        self.assertEqual(payload["id"], "queue_1")
        self.assertTrue(payload["success"])

    def test_init_prompt_contains_rbxtool_hint(self):
        prompt = "You are now connected to Roblox Studio through a local tool bridge. Use RBX_TOOL exactly once."
        self.assertIn("RBX_TOOL", prompt)


if __name__ == "__main__":
    unittest.main()
