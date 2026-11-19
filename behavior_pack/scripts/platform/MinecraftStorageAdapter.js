export class MinecraftStorageAdapter {
  constructor({ world } = {}) { this.world = world; }
  readRaw(key) { try { const value = this.world?.getDynamicProperty?.(key); return typeof value === "string" ? value : null; } catch (_) { return null; } }
  get(key) {
    try {
      const value = this.readRaw(key);
      if (value?.startsWith("__TBR_CHUNKED__:")) { const count = Number(value.slice("__TBR_CHUNKED__:".length)); let combined = ""; for (let index = 0; index < count; index++) combined += this.readRaw(`${key}:chunk:${index}`) ?? ""; return JSON.parse(combined); }
      if (typeof value !== "string") return value ?? null;
      try { return JSON.parse(value); } catch (_) { return value; }
    } catch (_) { return null; }
  }
  set(key, value) {
    try { const serialized = typeof value === "string" ? value : JSON.stringify(value); const chunkSize = 24000; const previous = Number(this.readRaw(key)?.replace("__TBR_CHUNKED__:", "")); for (let index = 0; index < (Number.isFinite(previous) ? previous : 0); index++) this.world?.setDynamicProperty?.(`${key}:chunk:${index}`, undefined); if (serialized.length <= chunkSize) { this.world?.setDynamicProperty?.(key, serialized); return true; } const count = Math.ceil(serialized.length / chunkSize); for (let index = 0; index < count; index++) this.world?.setDynamicProperty?.(`${key}:chunk:${index}`, serialized.slice(index * chunkSize, (index + 1) * chunkSize)); this.world?.setDynamicProperty?.(key, `__TBR_CHUNKED__:${count}`); return true; }
    catch (_) { return false; }
  }
  delete(key) { try { const previous = Number(this.readRaw(key)?.replace("__TBR_CHUNKED__:", "")); for (let index = 0; index < (Number.isFinite(previous) ? previous : 0); index++) this.world?.setDynamicProperty?.(`${key}:chunk:${index}`, undefined); this.world?.setDynamicProperty?.(key, undefined); return true; } catch (_) { return false; } }
}
