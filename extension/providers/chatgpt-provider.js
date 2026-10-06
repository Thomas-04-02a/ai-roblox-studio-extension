class ChatGPTProvider extends window.RbxBaseProvider {
  constructor() {
    super('ChatGPT', /^https:\/\/chatgpt\.com\//i);
  }

  findComposer() {
    const selectors = [
      'textarea[placeholder*="Message" i]',
      'textarea[aria-label*="Message" i]',
      '[data-testid*="composer" i]',
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
      'button[data-testid*="send" i]',
      'button[type="submit"]',
      'button:has(svg)',
      'button'
    ];

    for (const selector of selectors) {
      const button = document.querySelector(selector);
      if (button && button.textContent && button.textContent.toLowerCase().includes('send')) continue;
      if (button) return button;
    }

    return null;
  }

  isGenerating() {
    return !!document.querySelector(
      '[aria-label*="Stop generating" i], [data-testid*="stop" i], button[aria-label*="Stop" i], [role="button"][aria-label*="Stop" i]'
    );
  }

  getLatestAssistantMessage() {
    const candidates = [
      '[data-message-author-role="assistant"]',
      '.markdown',
      '[data-testid*="assistant" i]',
      '.group.w-full'
    ];

    let latest = '';
    for (const selector of candidates) {
      const nodes = [...document.querySelectorAll(selector)];
      const text = nodes
        .map((node) => node.textContent || '')
        .filter((value) => value.trim())
        .pop();

      if (text) {
        latest = text;
        break;
      }
    }

    return latest.trim();
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
    const match = window.location.pathname.match(/\/c\/(.+?)(?:\?|$)/);
    return match ? match[1] : null;
  }
}

window.RbxChatGPTProvider = ChatGPTProvider;
