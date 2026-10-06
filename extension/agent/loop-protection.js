class LoopProtection {
  constructor({ maxRepeatedToolCalls = 3, maxSessionMinutes = 20 } = {}) {
    this.maxRepeatedToolCalls = maxRepeatedToolCalls;
    this.maxSessionMinutes = maxSessionMinutes;
    this.history = [];
    this.startedAt = Date.now();
  }

  record(toolName) {
    this.history.push({ toolName, timestamp: Date.now() });
    const recent = this.history.filter((entry) => Date.now() - entry.timestamp < 60000);
    const counts = {};
    for (const entry of recent) {
      counts[entry.toolName] = (counts[entry.toolName] || 0) + 1;
    }

    if (Object.values(counts).some((count) => count >= this.maxRepeatedToolCalls)) {
      return { ok: false, error: 'Potential agent loop detected.' };
    }

    if ((Date.now() - this.startedAt) > this.maxSessionMinutes * 60 * 1000) {
      return { ok: false, error: 'Maximum session duration reached.' };
    }

    return { ok: true };
  }
}

window.RbxLoopProtection = LoopProtection;
