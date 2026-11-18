import { ok } from "../core/Constants.js";
export class PresetManager {
  constructor({ configManager, storage = null } = {}) { this.configManager = configManager; this.storage = storage; this.presets = new Map(); }
  listPresets() { return ok([...new Set([...this.presets.keys(), ...(this.storage?.list?.() ?? [])])]); }
  savePreset(name, config = this.configManager.getConfig()) { if (!name) return { ok: false, error: { code: "INVALID_ARGUMENT", message: "preset name is required" } }; this.presets.set(name, { ...config }); const saved = this.storage?.save?.(name, config); return saved === false ? { ok: false, error: { code: "STORAGE_FAILED", message: "preset could not be saved" } } : ok({ name }); }
  loadPreset(name) { const config = this.presets.get(name) ?? this.storage?.load?.(name); if (!config) return { ok: false, error: { code: "PRESET_NOT_FOUND", message: "preset not found" } }; const result = this.configManager.applyConfigTransaction(config); if (result.ok) this.presets.set(name, { ...config }); return result; }
  deletePreset(name) { this.presets.delete(name); const deleted = this.storage?.delete?.(name); return deleted === false ? { ok: false, error: { code: "STORAGE_FAILED", message: "preset could not be deleted" } } : ok({ name }); }
  editPreset(name, changes) { const current = this.presets.get(name) ?? {}; return this.savePreset(name, { ...current, ...changes }); }
}
