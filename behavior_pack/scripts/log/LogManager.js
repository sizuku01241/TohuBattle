// Persistent log lifecycle is intentionally kept behind this manager.
export class LogManager {
  constructor({ storage = null, exporter = null, maxLogs = 100, clock = () => new Date() } = {}) {
    this.storage = storage;
    this.exporter = exporter;
    this.maxLogs = maxLogs;
    this.clock = clock;
    const saved = storage?.load?.() ?? {};
    this.logs = Array.isArray(saved.logs) ? saved.logs.slice(-maxLogs) : [];
    this.queue = Array.isArray(saved.queue) ? saved.queue : [];
    this.nextLogId = Number.isInteger(saved.nextLogId) && saved.nextLogId > 0 ? saved.nextLogId : 1;
    this.nextMatchId = Number.isInteger(saved.nextMatchId) && saved.nextMatchId > 0 ? saved.nextMatchId : 1;
    this.clearState = this.storage?.loadClearState?.() ?? "idle";
    if (this.clearState === "clearing" || this.clearState === "logging") this.recoverClear();
  }

  formatTimestamp(date) {
    const value = new Date(date);
    const offset = 9 * 60 * 60 * 1000;
    const jst = new Date(value.getTime() + offset);
    return `${jst.toISOString().replace("Z", "") }+09:00`;
  }

  record(type, data = {}) {
    const entry = { logId: this.nextLogId++, type, timestamp: this.formatTimestamp(this.clock()), ...data };
    this.queue.push(entry);
    const flushed = this.flush();
    if (!flushed) return { ok: false, error: { code: "STORAGE_FAILED", message: "log could not be persisted" }, data: entry };
    return { ok: true, data: entry };
  }

  flush() {
    if (!this.queue.length) return true;
    const nextLogs = [...this.logs, ...this.queue].slice(-this.maxLogs);
    const value = { logs: nextLogs, queue: [], nextLogId: this.nextLogId, nextMatchId: this.nextMatchId };
    const saved = this.storage?.save?.(value) ?? true;
    if (saved === false) return false;
    this.logs = nextLogs; this.queue = [];
    return true;
  }

  getLogs() { return this.logs.map(log => ({ ...log })); }

  clear() {
    this.storage?.saveClearState?.("clearing");
    const saved = this.storage?.save?.({ logs: [], queue: [], nextLogId: this.nextLogId, nextMatchId: this.nextMatchId }) ?? true;
    if (saved === false) { this.storage?.saveClearState?.("clearing"); return { ok: false, error: { code: "STORAGE_FAILED", message: "logs could not be cleared" } }; }
    this.logs = [];
    this.queue = [];
    this.storage?.saveClearState?.("logging");
    this.record("ADMIN_COMMAND", { command: "/tbr log clear", result: "success" });
    this.storage?.saveClearState?.("idle"); this.clearState = "idle";
    return { ok: true, data: {} };
  }

  recoverClear() {
    this.logs = []; this.queue = [];
    this.storage?.save?.({ logs: [], queue: [], nextLogId: this.nextLogId, nextMatchId: this.nextMatchId });
    this.storage?.saveClearState?.("idle"); this.clearState = "idle";
    return { ok: true, data: { recovered: true } };
  }

  repair() { this.storage?.clearCorruptBackup?.(); return this.recoverClear(); }

  export() { return this.exporter?.export(this.getLogs()) ?? { ok: true, data: this.getLogs() }; }
}
