class AgentLoop {
  constructor() {
    this.state = 'IDLE';
    this.sessionId = crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`;
    this.toolCalls = 0;
    this.errors = 0;
    this.maxToolCalls = 30;
    this.maxConsecutiveErrors = 5;
    this.startedAt = Date.now();
  }

  start() {
    if (this.state === 'WAITING_FOR_MODEL' || this.state === 'EXECUTING_TOOL') {
      return { ok: false, error: 'Agent loop already active.' };
    }

    this.state = 'STARTING_SESSION';
    this.startedAt = Date.now();
    return { ok: true, sessionId: this.sessionId };
  }

  pause() {
    this.state = 'PAUSED';
    return { ok: true };
  }

  stop() {
    this.state = 'COMPLETED';
    return { ok: true };
  }

  recordToolCall() {
    this.toolCalls += 1;
    if (this.toolCalls > this.maxToolCalls) {
      this.state = 'ERROR';
      return { ok: false, error: 'Maximum tool-call limit reached.' };
    }
    return { ok: true };
  }

  recordError() {
    this.errors += 1;
    if (this.errors >= this.maxConsecutiveErrors) {
      this.state = 'ERROR';
      return { ok: false, error: 'Too many consecutive errors. Pausing agent.' };
    }
    return { ok: true };
  }

  setState(next) {
    this.state = next;
    return this.state;
  }
}

window.RbxAgentLoop = AgentLoop;
