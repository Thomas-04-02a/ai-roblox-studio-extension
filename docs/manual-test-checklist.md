# Manual test checklist

## Session lifecycle

- Start a session
- Stop the session
- Pause and resume the session
- Clear the session
- Double-click Start to ensure no duplicate agent loop begins

## Roblox connectivity

- Disconnect Roblox Studio and confirm the connection status changes
- Reconnect Roblox Studio and confirm the bridge reports a healthy state
- Refresh the AI webpage and ensure the extension reinitializes without crashing

## Generation interruptions

- Interrupt AI generation mid-response
- Confirm the provider waits for generation completion before next tool or follow-up
- Confirm a malformed tool response does not execute anything

## Safe operations

- Trigger a small script edit and confirm the result is validated
- Attempt a destructive action in Safe Mode and confirm confirmation is required
- Confirm large tool results are truncated or flagged as truncated

## Rate limit and challenge handling

- Simulate a provider 429 or rate-limit response
- Confirm the extension stops new sends and backs off according to retry policy
- Detect CAPTCHA verification or anti-abuse warnings and stop the agent

## Loop detection

- Repeatedly call the same tool several times and verify the loop detector fires
- Confirm the agent enters an error or pause state instead of continuing indefinitely

## DOM stability

- Trigger rapid DOM mutations and confirm the extension does not continually rewrite the page
- Confirm mutation observers do not crash the provider adapter
- Confirm provider UI still remains usable after refresh
