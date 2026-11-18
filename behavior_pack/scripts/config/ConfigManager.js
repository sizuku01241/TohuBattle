import { DEFAULT_CONFIG, ERROR_CODES, fail, ok } from "../core/Constants.js";

export class ConfigManager {
  constructor({ eventBus, defaults = DEFAULT_CONFIG, storage = null, storageKey = "tbr:config" } = {}) {
    this.eventBus = eventBus;
    this.defaults = { ...defaults };
    this.storage = storage;
    this.storageKey = storageKey;
    const saved = this.storage?.get?.(this.storageKey);
    const candidate = saved && this.validateConfig(saved).ok ? saved : this.defaults;
    this.config = { ...candidate };
  }
  getConfig() { return { ...this.config }; }
  getConfigValue(key) { return this.config[key]; }
  validateConfig(candidate) {
    if (!candidate || !["solo", "team"].includes(candidate.mode)) return fail(ERROR_CODES.CONFIG_VALIDATION_FAILED, "mode must be solo or team");
    if (candidate.teamCount !== null && (!Number.isInteger(candidate.teamCount) || candidate.teamCount < 2)) return fail(ERROR_CODES.CONFIG_VALIDATION_FAILED, "teamCount must be at least 2 or null");
    // The sample world keeps Solo at one player for local demonstrations.
    // Team mode switches minPlayers back to the approved production minimum.
    if (candidate.minPlayers < 1 || candidate.maxPlayers > 32 || candidate.minPlayers > candidate.maxPlayers) return fail(ERROR_CODES.CONFIG_VALIDATION_FAILED, "player limits are invalid");
    return ok();
  }
  setConfigValue(key, value) { return this.applyConfigTransaction({ [key]: value }); }
  applyConfigTransaction(changes) {
    const next = { ...this.config, ...changes };
    const result = this.validateConfig(next);
    if (!result.ok) return result;
    if (this.storage && this.storage.set?.(this.storageKey, next) === false) return fail("STORAGE_FAILED", "config could not be saved");
    const before = this.config;
    this.config = next;
    this.eventBus?.emit("config:changed", { before: { ...before }, after: { ...next }, changes: { ...changes } });
    return ok(this.getConfig());
  }
  resetConfig() {
    const next = { ...this.defaults };
    if (this.storage && this.storage.set?.(this.storageKey, next) === false) return fail("STORAGE_FAILED", "config could not be saved");
    this.config = next;
    return ok(this.getConfig());
  }
}
