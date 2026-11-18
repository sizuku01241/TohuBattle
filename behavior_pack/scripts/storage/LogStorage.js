export class LogStorage {
  constructor({ adapter = null, key = "tbr:logs" } = {}) { this.adapter = adapter; this.key = key; }
  load() { try { return this.adapter?.get?.(this.key) ?? { logs: [], nextLogId: 1, nextMatchId: 1 }; } catch (_) { return { logs: [], nextLogId: 1, nextMatchId: 1 }; } }
  save(value) { return this.adapter?.set?.(this.key, value) ?? true; }
  loadClearState() { try { return this.adapter?.get?.("tbr:log_clear_state") ?? "idle"; } catch (_) { return "idle"; } }
  saveClearState(state) { return this.adapter?.set?.("tbr:log_clear_state", state) ?? true; }
  clearCorruptBackup() { this.adapter?.delete?.("tbr:logs_corrupt"); this.adapter?.delete?.("tbr:log_queue_corrupt"); return true; }
}
