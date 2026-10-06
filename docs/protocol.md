# Protocol

The browser extension and bridge use a compact, machine-readable JSON envelope so that the AI does not casually generate freeform commands that the extension could mistakenly execute.

## Tool envelope

```json
{
  "type": "tool",
  "id": "tool_001",
  "name": "call_mcp_tool",
  "arguments": {
    "tool": "inspect_tree",
    "arguments": {}
  }
}
```

## Tool result envelope

```json
{
  "id": "tool_001",
  "success": true,
  "result": {
    "children": []
  },
  "error": null,
  "truncated": false
}
```

## Validation rules

- reject malformed JSON
- reject missing IDs or names
- require a dictionary for arguments
- reject duplicate tool IDs
- reject unsupported message types
- treat project content as data, not directives

## Prompt injection protection

Roblox scripts, object names, comments, output logs, and asset metadata are treated as untrusted content. The model is instructed not to follow instructions hidden inside those values, and the extension validates tool payloads rather than guessing commands from natural language.
