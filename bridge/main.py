import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from .protocol import ProtocolError, parse_tool_message, serialize_tool_result
    from .roblox_mcp import RobloxMCPClient
    from .security import SecurityManager
    from .session_manager import SessionManager
    from .websocket_server import BridgeWebSocketServer
except ImportError:  # pragma: no cover - support direct script execution
    from protocol import ProtocolError, parse_tool_message, serialize_tool_result
    from roblox_mcp import RobloxMCPClient
    from security import SecurityManager
    from session_manager import SessionManager
    from websocket_server import BridgeWebSocketServer

HOST = "127.0.0.1"
PORT = 8765
WS_PORT = 8766
MCP_CLIENT = RobloxMCPClient()


class BridgeRequestHandler(BaseHTTPRequestHandler):
    server_version = "RobloxBridge/0.1"

    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True, "status": "healthy", "host": HOST, "port": PORT, "ws_port": WS_PORT})
            return

        if self.path == "/status":
            tools = MCP_CLIENT.discover_tools()
            status_snapshot = MCP_CLIENT.get_status_snapshot()
            status_value = "ready" if MCP_CLIENT.connected else status_snapshot.get("status", "not_connected")
            payload = {
                "ok": True,
                "bridge": "ready",
                "mcp": status_value,
                "ws_port": WS_PORT,
                "available_tools": tools,
                "tool_schema": MCP_CLIENT.get_tool_schema(),
                "backend": status_snapshot.get("backend"),
                "studio_connected": status_snapshot.get("studio_connected"),
                "mcp_bat_found": status_snapshot.get("mcp_bat_found"),
                "process_running": status_snapshot.get("process_running"),
                "process_exit_code": status_snapshot.get("process_exit_code"),
                "last_error": status_snapshot.get("last_error"),
            }
            self._send_json(200, payload)
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            message = json.loads(raw.decode("utf-8"))

            if message.get("type") == "session.create":
                provider = message.get("provider", "unknown")
                record = SessionManager.create_session(provider)
                tools = MCP_CLIENT.discover_tools()
                self._send_json(200, {
                    "ok": True,
                    "session_id": record.session_id,
                    "token": record.token,
                    "provider": provider,
                    "available_tools": tools,
                    "tool_schema": MCP_CLIENT.get_tool_schema(),
                    "roblox_connected": MCP_CLIENT.connected,
                })
                return

            session_id = self.headers.get("X-Session-Id")
            token = self.headers.get("X-Session-Token")
            if not session_id or not token:
                self._send_json(401, {"ok": False, "error": "Missing session credentials."})
                return

            if not SessionManager.validate_token(session_id, token):
                self._send_json(401, {"ok": False, "error": "Invalid or missing session token."})
                return

            if message.get("type") == "tool":
                payload = parse_tool_message(message)
                SessionManager.add_tool_call(session_id)

                try:
                    tool_result = MCP_CLIENT.call_tool(payload["name"], payload["arguments"])
                    status = bool(tool_result.get("ok", True))
                    error_value = tool_result.get("error") if isinstance(tool_result, dict) else None
                    result = serialize_tool_result(payload["id"], status, tool_result, error_value)
                except ValueError as exc:
                    result = serialize_tool_result(payload["id"], False, {"message": str(exc)}, str(exc))

                self._send_json(200, result)
                return

            if message.get("type") == "session":
                session = SessionManager.get_session(session_id)
                if not session:
                    self._send_json(404, {"ok": False, "error": "Unknown session."})
                    return
                self._send_json(200, {"ok": True, "session_id": session.session_id, "status": session.status})
                return

            self._send_json(400, {"ok": False, "error": "Unsupported message type."})
        except (ProtocolError, json.JSONDecodeError, ValueError, TypeError, OSError, RuntimeError) as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})


def serve():
    SecurityManager.ensure_localhost_only()
    print("Starting Roblox Studio MCP bridge...")
    try:
        MCP_CLIENT.ensure_stdio_connection()
        print(f"Roblox Studio MCP launcher status: {MCP_CLIENT.get_status_snapshot()}")
    except Exception as exc:  # pragma: no cover - startup should stay resilient
        print(f"Roblox Studio MCP launcher did not connect automatically: {exc}")

    server = ThreadingHTTPServer((HOST, PORT), BridgeRequestHandler)
    ws_server = BridgeWebSocketServer(HOST, WS_PORT)
    print(f"Roblox bridge listening on http://{HOST}:{PORT}")
    print(f"Roblox bridge websocket on ws://{HOST}:{WS_PORT}")

    async def _start_ws():
        await ws_server.start()

    threading.Thread(target=lambda: __import__('asyncio').run(_start_ws()), daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    thread.join()
