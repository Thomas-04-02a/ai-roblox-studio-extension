function createSessionId() {
  if (crypto && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `rbx-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

window.RbxCreateSessionId = createSessionId;
