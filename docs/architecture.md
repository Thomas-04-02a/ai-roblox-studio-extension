# Architecture

The project intentionally separates the browser-side automation from the local bridge and the Roblox-side tool layer.

## Browser extension layer

- Detects whether the active page is ChatGPT or DeepSeek.
- Inserts a minimal status bar without interfering with the main conversation UI.
- Uses provider adapters to isolate page-specific DOM logic.
- Maintains a single active message queue and prevents uncontrolled follow-up prompting.

## Agent controller layer

- Keeps a structured state machine such as IDLE, STARTING_SESSION, WAITING_FOR_MODEL, EXECUTING_TOOL, and PAUSED.
- Tracks tool calls and consecutive errors.
- Validates tool payloads before they are sent.
- Debounces repeated assistant-message changes to avoid duplicate processing.

## Local bridge layer

- Runs on localhost only.
- Accepts authenticated extension requests.
- Keeps a session registry and active token checks.
- Exposes health and status endpoints.
- Prepares for Roblox Studio MCP requests through a compatibility layer.

## Roblox MCP layer

- Discovers what tools are actually available instead of assuming fixed names.
- Maps the discovered tool names into a stable internal interface.
- Returns structured tool results that the agent loop can parse and forward back to the AI without treating Roblox text as instructions.

## Safety principles

- never expose the bridge publicly
- never send rapid automated bursts to the model provider
- never let arbitrary webpage text override agent instructions
- never execute unsupported tools without validation
- never run more than one model submission at a time
