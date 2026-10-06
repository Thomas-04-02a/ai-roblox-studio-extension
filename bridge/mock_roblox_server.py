import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockRobloxMCPServer:
    def __init__(self, host="127.0.0.1", port=8767):
        self.host = host
        self.port = port
        self.tools = {
            "inspect_tree": {"description": "Return mock instance tree"},
            "read_script": {"description": "Return mock script source"},
            "write_script": {"description": "Write script source"},
            "create_instance": {"description": "Create a mock instance"},
            "set_property": {"description": "Set a property"},
            "run_luau": {"description": "Execute a mock Luau expression"},
        }

    def build_response(self, tool_name, arguments):
        if tool_name == "inspect_tree":
            return {"ok": True, "children": [{"Name": "Workspace", "ClassName": "Folder"}], "path": arguments.get("path", "Workspace")}
        if tool_name == "read_script":
            return {"ok": True, "source": "print('mock script loaded')\n"}
        if tool_name == "write_script":
            return {"ok": True, "path": arguments.get("path"), "written": True}
        if tool_name == "create_instance":
            return {"ok": True, "instance": arguments.get("className", "Part"), "name": arguments.get("name", "NewPart")}
        if tool_name == "set_property":
            return {"ok": True, "target": arguments.get("target"), "property": arguments.get("property"), "value": arguments.get("value")}
        if tool_name == "run_luau":
            return {"ok": True, "result": "mock luau executed"}
        return {"ok": False, "error": "Unknown tool"}

    def run(self):
        handler = self._make_handler()
        server = ThreadingHTTPServer((self.host, self.port), handler)
        print(f"Mock Roblox MCP server listening on http://{self.host}:{self.port}")
        server.serve_forever()

    def _make_handler(self):
        tools = self.tools
        server_self = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/tools":
                    payload = json.dumps({"ok": True, "tools": list(tools.keys())}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    payload = json.dumps({"ok": True, "status": "ready"}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                tool_name = body.get("tool")
                arguments = body.get("arguments", {})
                response = server_self.build_response(tool_name, arguments)
                payload = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                _ = (fmt, args)
                return

        return Handler


if __name__ == "__main__":
    MockRobloxMCPServer().run()
