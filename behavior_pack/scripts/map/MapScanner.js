import { ok, fail } from "../core/Constants.js";

// Incremental, cached candidate scanner. It deliberately samples the registered
// map volume in small batches so a large map never monopolizes one tick.
export class MapScanner {
  constructor({ world, scheduler, storage, mapManager, batchSize = 256 } = {}) {
    this.world = world; this.scheduler = scheduler; this.storage = storage; this.mapManager = mapManager; this.batchSize = batchSize;
    this.status = { state: "WAITING", scanned: 0, total: 0, candidates: 0, valid: 0, failedRegions: [] }; this.candidates = [];
    this.task = null;
  }
  cacheKey() { return `tbr:map_candidates:${this.mapManager.getMap()?.name ?? "default"}`; }
  getStatus() { return { ...this.status, candidates: this.candidates.length, valid: this.candidates.filter(c => c.valid).length }; }
  getCandidates() { return this.candidates.filter(c => c.valid).map(c => ({ ...c })); }
  isReady() { return this.status.state === "COMPLETE"; }
  loadCache() { const saved = this.storage?.get?.(this.cacheKey()); if (!saved?.schemaVersion || !Array.isArray(saved.candidates)) return false; this.candidates = saved.candidates; this.status = { ...this.status, state: "COMPLETE", scanned: saved.scanned ?? 0, total: saved.total ?? 0 }; return true; }
  start(force = false) {
    if (!force && this.loadCache()) return ok(this.getStatus());
    const b = this.mapManager.getMapBounds(); if (!b) return fail("INVALID_MAP", "map bounds are required");
    this.stop(); this.candidates = []; this.status = { state: "SCANNING", scanned: 0, total: Math.max(0, (b.maxX - b.minX + 1) * (b.maxZ - b.minZ + 1)), candidates: 0, valid: 0, failedRegions: [] };
    this.cursor = { x: b.minX, z: b.minZ }; this.bounds = b;
    if (this.scheduler?.runInterval) this.task = this.scheduler.runInterval(() => this.tick(), 1); else this.tick();
    return ok(this.getStatus());
  }
  stop() { if (this.task !== null) this.scheduler?.clearRun?.(this.task); this.task = null; }
  tick() {
    if (this.status.state !== "SCANNING") return;
    const dimension = this.world?.getDimension?.(this.mapManager.getMap()?.dimensionId ?? "overworld"); let processed = 0;
    while (processed++ < this.batchSize && this.cursor.z <= this.bounds.maxZ) {
      const x = this.cursor.x; const z = this.cursor.z; this.cursor.x += 1; if (this.cursor.x > this.bounds.maxX) { this.cursor.x = this.bounds.minX; this.cursor.z += 1; }
      try {
        const y = this.findSurfaceY(dimension, x, z); if (y !== null) { const candidate = this.inspect(dimension, x, y, z); if (candidate) this.candidates.push(candidate); }
      } catch (_) { this.status.failedRegions.push({ x, z }); }
      this.status.scanned += 1;
    }
    if (this.cursor.z > this.bounds.maxZ) { this.status.state = "COMPLETE"; this.stop(); this.storage?.set?.(this.cacheKey(), { schemaVersion: 1, scanned: this.status.scanned, total: this.status.total, candidates: this.candidates }); }
  }
  findSurfaceY(dimension, x, z) {
    const minY = this.bounds.minY ?? this.bounds.spawnY ?? -64; const maxY = this.bounds.maxY ?? (this.bounds.spawnY ?? 320); for (let y = maxY; y >= minY; y--) { const floor = dimension?.getBlock?.({ x, y, z }); const above = dimension?.getBlock?.({ x, y: y + 1, z }); if (floor && above && this.isSolid(floor) && this.isAir(above)) return y; } return null;
  }
  isAir(block) { return !block || ["minecraft:air", "minecraft:cave_air", "minecraft:void_air"].includes(block.typeId); }
  isSolid(block) { return !!block && !this.isAir(block) && !["minecraft:water", "minecraft:flowing_water", "minecraft:lava", "minecraft:flowing_lava", "minecraft:fire", "minecraft:soul_fire"].includes(block.typeId); }
  inspect(dimension, x, y, z) { const first = dimension?.getBlock?.({ x, y: y + 1, z }); const second = dimension?.getBlock?.({ x, y: y + 2, z }); if (!this.isAir(first) || !this.isAir(second)) return null; return { x, y: y + 1, z, floorBlock: dimension?.getBlock?.({ x, y, z })?.typeId ?? "unknown", valid: true, failedCount: 0 }; }
  rescan() { return this.start(true); }
}
