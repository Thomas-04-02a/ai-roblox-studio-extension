# Roblox AI Agent Extension

This project contains a Chrome/Edge extension and a local Python bridge for connecting ChatGPT or DeepSeek to a Roblox Studio session through a controlled, localhost-only tool channel.

## What it does

The extension inserts a small control bar into supported AI pages and creates a structured agent loop that can:

- detect the active provider page
- keep a single asynchronous generation queue
- validate tool payloads before execution
- communicate with a local bridge bound to localhost only
- prepare for Roblox Studio MCP tool execution and state feedback

## Architecture overview

```text
AI website
  -> Browser Extension
  -> Local Bridge
  -> Roblox Studio MCP
  -> Local Bridge
  -> Browser Extension
  -> AI provider
```

The system intentionally separates:

- provider adapters for ChatGPT and DeepSeek
- bridge protocol handling and session checks
- Roblox MCP discovery and tool calls
- agent lifecycle and queue protection

## Repository layout

```text
roblox-ai-agent/
  bridge/
    __init__.py
    __pycache__/
    main.py
    protocol.py
    security.py
    session_manager.py
    roblox_mcp.py
    websocket_server.py
    requirements.txt
    README.md
  docs/
    architecture.md
    protocol.md
    troubleshooting.md
  extension/
    manifest.json
    agent/
      agent-loop.js
      queue.js
    background/
      service-worker.js
    content/
      content.js
    protocol/
      tool-protocol.js
    providers/
      base-provider.js
      chatgpt-provider.js
      deepseek-provider.js
    ui/
      agent-panel.css
    utils/
      session.js
  scripts/
    start_bridge.py
  tests/
    test_agent_queue.py
    test_bridge_protocol.py
  README.md
```

## Supported providers

- ChatGPT (`https://chatgpt.com/`)
- DeepSeek (`https://chat.deepseek.com/`)

## Installation

### 1. Install the browser extension

1. Open Chrome or Edge.
2. Navigate to `chrome://extensions`.
3. Enable Developer mode.
4. Click Load unpacked.
5. Select the `extension/` folder in this workspace.

### 2. Install the local bridge

Quick start on Windows:

```bat
cd "c:\thomas\persoonlijk\roblox_extension\ai-roblox-studio-extension"
Scripts\start_bridge.bat
```

Manual setup:

```bash
cd "c:\thomas\persoonlijk\roblox extension\ai-roblox-studio-extension"
python -m venv .venv
.venv\Scripts\activate
pip install -r bridge\requirements.txt
python scripts\start_bridge.py
```

The bridge is intentionally bound to `127.0.0.1` and does not expose itself publicly.

### 3. Optional mock Roblox MCP server

If you want to validate the local tool channel without a real Roblox Studio MCP endpoint, run:

```bat
cd "c:\thomas\persoonlijk\roblox extension\ai-roblox-studio-extension"
Scripts\start_mock_mcp_server.bat
```

## Roblox Studio MCP

The bridge discovers the tools exposed by the active Roblox Studio MCP server and passes their descriptions and input schemas to the AI agent. The tools available for reading or editing your project depend on the MCP server and Roblox Studio integration you have enabled.

The agent calls those tools through the local bridge and sends each tool result back to the chat before continuing. It does not advertise placeholder tools that the Studio MCP server does not provide.

## How to start an agent session

1. Start the local bridge.
2. Open ChatGPT or DeepSeek in the supported website.
3. Load the unpacked extension.
4. Click the inserted Roblox Agent control bar.
5. Press Start Roblox Agent.
6. Send your task in the chat UI.

The extension sends a structured startup prompt and keeps the active generation queue to a single outstanding message.

## Safety model

This project is built around reliability and local-only execution:

- bridge binds to localhost only
- session token validation is used for local requests
- malformed tool payloads are rejected
- duplicate tool IDs are tracked
- tool calls are queued to avoid uncontrolled rapid follow-ups
- the agent loop has hard limits for tool count and repeated error states

## Testing

Run the included Python validation checks:

```bash
cd "c:\thomas\persoonlijk\roblox extension\ai-roblox-studio-extension"
python -m unittest discover -s tests -v
```

This covers protocol parsing and queue safety checks and is the current verification baseline for the project foundation.

## Known limitations

This is not a production-grade Roblox Studio automation package. Tool execution depends on the MCP tools exposed by the installed Studio integration, and the browser provider adapters may need updates if the live chat websites change their page layouts.

## Troubleshooting

- Bridge unavailable: ensure the Python bridge is running on `127.0.0.1:8765`
- Provider not detected: confirm the page is a supported URL
- Tool validation issues: inspect the console and ensure the payload matches the strict RBX_TOOL schema
- DeepSeek rate limits: respect generation completion and cooldown windows rather than sending rapid follow-ups

## Development notes

The codebase favors plain JavaScript and Python, minimal dependencies, and explicit validation. The goal is to keep provider-specific DOM behavior isolated in adapter classes rather than embedding it in one giant content script.
