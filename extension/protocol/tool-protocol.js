class ToolProtocol {
  static validateToolEnvelope(payload) {
    if (!payload || typeof payload !== 'object') {
      throw new Error('Tool payload must be an object.');
    }

    if (typeof payload.id !== 'string' || !payload.id.trim()) {
      throw new Error('Tool payload requires a non-empty string id.');
    }

    if (typeof payload.name !== 'string' || !payload.name.trim()) {
      throw new Error('Tool payload requires a non-empty string name.');
    }

    if (!payload.arguments || typeof payload.arguments !== 'object') {
      throw new Error('Tool payload requires an object arguments field.');
    }

    return true;
  }

  static validateToolResult(payload) {
    if (!payload || typeof payload !== 'object') {
      throw new Error('Tool result must be an object.');
    }

    if (typeof payload.id !== 'string' || !payload.id.trim()) {
      throw new Error('Tool result requires a valid id.');
    }

    return true;
  }

  static serializeToolResult(id, success, result, error = null) {
    return {
      id,
      success,
      result: result && typeof result === 'object' ? result : { value: result },
      error,
      timestamp: new Date().toISOString()
    };
  }
}

window.RbxToolProtocol = ToolProtocol;
