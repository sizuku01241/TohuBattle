export class EventBus {
  constructor({ maxDepth = 20, onError = () => {} } = {}) { this._listeners = new Map(); this._owners = new Map(); this._depth = 0; this._maxDepth = maxDepth; this._onError = onError; }
  on(event, listener, owner = undefined) {
    if (typeof listener !== "function") throw new TypeError("listener must be a function");
    const set = this._listeners.get(event) ?? new Set(); set.add(listener); this._listeners.set(event, set);
    if (owner) { const owned = this._owners.get(owner) ?? new Set(); owned.add(() => this.off(event, listener)); this._owners.set(owner, owned); }
    return () => this.off(event, listener);
  }
  off(event, listener) { const set = this._listeners.get(event); if (!set) return false; const removed = set.delete(listener); if (!set.size) this._listeners.delete(event); return removed; }
  clear(event) { this._listeners.delete(event); }
  unsubscribeAll(owner) { for (const unsubscribe of this._owners.get(owner) ?? []) unsubscribe(); this._owners.delete(owner); }
  emit(event, payload = {}) {
    if (this._depth >= this._maxDepth) { this._onError(new Error(`Event depth exceeded: ${event}`), event, payload); return; }
    const snapshot = [...(this._listeners.get(event) ?? [])]; this._depth++;
    try { for (const listener of snapshot) { try { listener(Object.freeze(payload)); } catch (error) { this._onError(error, event, payload); } } }
    finally { this._depth--; }
  }
}
