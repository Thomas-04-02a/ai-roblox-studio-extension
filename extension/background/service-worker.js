chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) {
    sendResponse({ ok: false, error: 'Missing message type.' });
    return false;
  }

  if (message.type === 'bridge:ping') {
    fetch('http://127.0.0.1:8765/health', { method: 'GET' })
      .then(async (response) => {
        let body = null;
        try {
          body = await response.json();
        } catch {
          body = await response.text();
        }
        sendResponse({ ok: response.ok, status: response.status, body });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message });
      });
    return true;
  }

  if (message.type === 'bridge:status') {
    fetch('http://127.0.0.1:8765/status', { method: 'GET' })
      .then(async (response) => {
        const body = await response.json().catch(() => ({ ok: false }));
        sendResponse({ ok: response.ok && body.ok, status: response.ok ? 'ready' : 'offline', details: body });
      })
      .catch((error) => {
        sendResponse({ ok: false, status: 'offline', error: error.message });
      });
    return true;
  }

  if (message.type === 'bridge:session.create') {
    fetch('http://127.0.0.1:8765/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'session.create', provider: message.provider || 'unknown', sessionId: message.sessionId || null })
    })
      .then(async (response) => {
        const body = await response.json().catch(() => ({ ok: false }));
        sendResponse({ ok: response.ok && body.ok, ...body });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message });
      });
    return true;
  }

  if (message.type === 'bridge:session') {
    const headers = new Headers();
    if (message.sessionId) headers.set('X-Session-Id', message.sessionId);
    if (message.token) headers.set('X-Session-Token', message.token);

    fetch('http://127.0.0.1:8765/status', { method: 'POST', headers, body: JSON.stringify({ type: 'session' }) })
      .then(async (response) => {
        const body = await response.json().catch(() => ({ ok: false }));
        sendResponse({ ok: response.ok, response: body });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message });
      });
    return true;
  }

  if (message.type === 'bridge:tool') {
    const headers = new Headers({ 'Content-Type': 'application/json' });
    if (message.sessionId) headers.set('X-Session-Id', message.sessionId);
    if (message.token) headers.set('X-Session-Token', message.token);

    fetch('http://127.0.0.1:8765/', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        type: 'tool',
        id: message.id,
        name: message.name,
        arguments: message.arguments || {}
      })
    })
      .then(async (response) => {
        const body = await response.json().catch(() => ({ ok: false }));
        sendResponse({ ok: response.ok, response: body });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message });
      });
    return true;
  }

  sendResponse({ ok: false, error: 'Unsupported message type.' });
  return false;
});
