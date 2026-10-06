# Troubleshooting

## Extension not appearing

- Confirm the page is a supported URL.
- Check that the extension is loaded in Developer Mode.
- Ensure the content script is active and the DOM includes the chat composer.

## Bridge unavailable

- Confirm the Python process is running on `127.0.0.1:8765`.
- Ensure no firewall is blocking localhost traffic.
- Verify the health endpoint responds.

## Provider layout changed

- The provider abstraction should be adjusted with safer selectors.
- The content script should degrade gracefully and show the warning state instead of crashing.

## DeepSeek rate limiting

- Respect the generation completion state and cooldown timer.
- Stop the agent automatically when a verification or challenge screen appears.
