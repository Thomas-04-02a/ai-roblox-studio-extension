import json

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None


class BridgeWebSocketServer:
    def __init__(self, host="127.0.0.1", port=8766):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.server = None

    def status_snapshot(self, mcp_status="discovering"):
        return {
            "ok": True,
            "type": "status",
            "bridge": "ready",
            "mcp": mcp_status,
            "host": self.host,
            "port": self.port,
        }

    async def _handler(self, websocket):
        self.connected_clients.add(websocket)
        try:
            async for raw in websocket:
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"ok": False, "error": "Invalid JSON."}))
                    continue

                if payload.get("type") == "ping":
                    await websocket.send(json.dumps({"ok": True, "type": "pong"}))
                elif payload.get("type") == "status":
                    await websocket.send(json.dumps(self.status_snapshot()))
                else:
                    await websocket.send(json.dumps({"ok": False, "error": "Unsupported message type."}))
        finally:
            self.connected_clients.discard(websocket)

    async def start(self):
        if websockets is None:
            raise RuntimeError("websockets package is not installed.")
        self.server = await websockets.serve(self._handler, self.host, self.port)
        return self.server

    async def close(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
