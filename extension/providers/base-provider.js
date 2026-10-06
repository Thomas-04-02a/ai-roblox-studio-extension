class BaseProvider {
  constructor(name, pageMatcher) {
    this.name = name;
    this.pageMatcher = pageMatcher;
    this.debug = [];
  }

  isSupportedPage() {
    return !!this.pageMatcher && this.pageMatcher.test(window.location.href);
  }

  log(message) {
    const timestamp = new Date().toLocaleTimeString();
    this.debug.push(`[${timestamp}] ${message}`);
  }

  findComposer() {
    return null;
  }

  findSendButton() {
    return null;
  }

  setComposerText(text) {
    const composer = this.findComposer();
    if (!composer) return false;

    if (composer.tagName === 'TEXTAREA') {
      composer.value = text;
      composer.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    }

    if (composer.isContentEditable) {
      composer.textContent = text;
      composer.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }));
      return true;
    }

    return false;
  }

  sendMessage(text) {
    const composer = this.findComposer();
    const button = this.findSendButton();
    if (!composer || !button) return false;

    this.setComposerText(text);
    button.click();
    return true;
  }

  isGenerating() {
    return false;
  }

  getLatestAssistantMessage() {
    return '';
  }

  waitForGenerationComplete() {
    return new Promise((resolve) => {
      const poll = () => {
        if (!this.isGenerating()) {
          resolve();
          return;
        }
        setTimeout(poll, 250);
      };
      poll();
    });
  }

  insertExtensionUI() {
    return null;
  }

  getConversationId() {
    return null;
  }

  diagnostics() {
    return {
      name: this.name,
      supported: this.isSupportedPage(),
      composer: !!this.findComposer(),
      sendButton: !!this.findSendButton(),
      generating: this.isGenerating(),
      conversationId: this.getConversationId()
    };
  }
}

window.RbxBaseProvider = BaseProvider;
