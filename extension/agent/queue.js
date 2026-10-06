class AgentQueue {
  constructor({ maxConcurrentMessages = 1, cooldownMs = 2000, maxQueueLength = 20 } = {}) {
    this.maxConcurrentMessages = maxConcurrentMessages;
    this.cooldownMs = cooldownMs;
    this.maxQueueLength = maxQueueLength;
    this.pending = [];
    this.active = false;
    this.lastSentAt = 0;
    this.backoffMs = 0;
  }

  enqueue(task) {
    if (!task || typeof task !== 'object') {
      return { ok: false, error: 'Task must be an object.' };
    }
    if (this.pending.length >= this.maxQueueLength) {
      return { ok: false, error: 'Message queue is full.' };
    }
    this.pending.push(task);
    return { ok: true, queueLength: this.pending.length };
  }

  async waitForTurn() {
    if (this.active) {
      await new Promise((resolve) => {
        const check = () => {
          if (!this.active) resolve();
          else setTimeout(check, 100);
        };
        check();
      });
    }

    this.active = true;
    const next = this.pending.shift();
    return next;
  }

  async applyCooldown(forceMs) {
    const waitMs = typeof forceMs === 'number' ? forceMs : Math.max(this.cooldownMs, this.backoffMs);
    const now = Date.now();
    const delta = this.lastSentAt ? now - this.lastSentAt : waitMs;
    const remaining = waitMs - delta;
    if (remaining > 0) {
      await new Promise((resolve) => setTimeout(resolve, remaining));
    }
    this.lastSentAt = Date.now();
  }

  setBackoff(multiplier = 1) {
    this.backoffMs = Math.min(Math.max(this.cooldownMs * multiplier, 0), 120000);
  }

  release() {
    this.active = false;
  }
}

window.RbxAgentQueue = AgentQueue;
