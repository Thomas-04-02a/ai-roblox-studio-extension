# Local bridge

This is the initial Stage 1 bridge scaffold. It is intentionally minimal and bound to localhost only.

## What is included

- Local-only HTTP health endpoint
- Token-based session validation layer
- Lightweight protocol helpers for tool calls and results
- Minimal Roblox MCP discovery stub

## Run it

```bash
cd bridge
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The bridge listens on `127.0.0.1:8765` by default and does not bind to the public network.
