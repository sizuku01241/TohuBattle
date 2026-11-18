export class MinecraftStorageAdapter {
  constructor({ world } = {}) { this.world = world; }
  get(key) {
    try {
      const value = this.world?.getDynamicProperty?.(key);
      if (typeof value !== "string") return value ?? null;
      try { return JSON.parse(value); } catch (_) { return value; }
    } catch (_) { return null; }
  }
  set(key, value) {
    try { this.world?.setDynamicProperty?.(key, typeof value === "string" ? value : JSON.stringify(value)); return true; }
    catch (_) { return false; }
  }
  delete(key) { try { this.world?.setDynamicProperty?.(key, undefined); return true; } catch (_) { return false; } }
}
