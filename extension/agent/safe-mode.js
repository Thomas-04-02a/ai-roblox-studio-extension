class SafeMode {
  constructor() {
    this.enabled = false;
    this.confirmations = new Set();
  }

  setEnabled(value) {
    this.enabled = !!value;
    return this.enabled;
  }

  requiresConfirmation(actionName) {
    if (!this.enabled) return false;
    const dangerous = new Set(['delete_hierarchy', 'mass_delete', 'overwrite_large_script', 'asset_insertion']);
    return dangerous.has(actionName);
  }

  confirm(actionName) {
    if (!this.requiresConfirmation(actionName)) return true;
    this.confirmations.add(actionName);
    return true;
  }
}

window.RbxSafeMode = SafeMode;
