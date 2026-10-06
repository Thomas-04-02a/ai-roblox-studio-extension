class DeepSeekProvider extends window.RbxBaseProvider {
  constructor() {
    super('DeepSeek', /^https:\/\/chat\.deepseek\.com\//i);
    this.lastRateLimitWarning = 0;
  }

  findComposer() {
    const selectors = [
      'textarea[placeholder*="Message" i]',
      'textarea[aria-label*="Message" i]',
      'textarea[rows]',
      'div[contenteditable="true"][role="textbox"]',
      'textarea'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) return element;
    }

    return null;
  }

  findSendButton() {
    const selectors = [
      'button[aria-label*="Send" i]',
      'button[type="submit"]',
      '[data-testid*="send" i]',
      'button'
    ];

    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (!button) continue;
      const text = (button.textContent || '').toLowerCase();
      if (text.includes('stop') || text.includes('cancel')) continue;
      return button;
    }

    return null;
  }

  isGenerating() {
    const stopButton = document.querySelector(
      'button[aria-label*="Stop" i], [data-testid*="stop" i], [data-testid*="stop-generating" i], [aria-label*="Stop generating" i]'
    );
    const waitingIndicator = document.querySelector('[role="status"], [aria-live="polite"], [data-state="loading"]');
    const rateLimited = this.detectRateLimit();
    return !!(stopButton || waitingIndicator || rateLimited);
  }

  detectRateLimit() {
    const text = document.body ? document.body.innerText || '' : '';
    const lowered = text.toLowerCase();
    return lowered.includes('429') || lowered.includes('rate limit') || lowered.includes('too many requests') || lowered.includes('please wait');
  }

  waitForGenerationComplete() {
    return new Promise((resolve) => {
      const poll = () => {
        const rateLimited = this.detectRateLimit();
        if (!this.isGenerating() && !rateLimited) {
          resolve();
          return;
        }
        setTimeout(poll, 400);
      };
      poll();
    });
  }

  getLatestAssistantMessage() {
    const nodes = [...document.querySelectorAll('div[data-message-role="assistant"], .assistant-message, [data-testid*="assistant" i]')];
    const text = nodes
      .map((node) => node.textContent || '')
      .filter(Boolean)
      .pop();

    return (text || '').trim();
  }

  insertExtensionUI() {
    const existing = document.getElementById('rbx-agent-bar');
    if (existing) return existing;

    const composer = this.findComposer();
    if (!composer) return null;

    const bar = document.createElement('div');
    bar.id = 'rbx-agent-bar';
    bar.className = 'rbx-agent-bar';

    bar.innerHTML = `
      <div class="rbx-agent-status">
        <span class="rbx-agent-dot rbx-agent-dot--idle"></span>
        <span class="rbx-agent-label">Roblox agent</span>
      </div>
      <button class="rbx-agent-button" data-rbx-action="toggle-agent">Start Roblox Agent</button>
      <button class="rbx-agent-button secondary" data-rbx-action="pause-agent">Pause</button>
      <button class="rbx-agent-button secondary" data-rbx-action="clear-session">Clear</button>
      <button class="rbx-agent-button secondary" data-rbx-action="settings">Settings</button>
    `;

    const container = composer.closest('div, form, section') || composer.parentElement;
    if (container && container.parentElement) {
      container.parentElement.appendChild(bar);
    } else {
      document.body.appendChild(bar);
    }

    return bar;
  }

  getConversationId() {
    const path = window.location.pathname;
    const match = path.match(/\/chat\/(.+?)(?:\?|$)/);
    return match ? match[1] : null;
  }
}

window.RbxDeepSeekProvider = DeepSeekProvider;
