import { fail, ok } from "../core/Constants.js";
export class MapManager {
  constructor({ worldAdapter = null, world = null } = {}) { this.worldAdapter = worldAdapter; this.world = world; this.map = null; this.maps = new Map(); this.tickingAreas = []; this.tickingAreaTasks = []; this.tickingAreaFingerprint = null; this.tickingAreaPromise = null; }
  loadMap(map) { if (!map?.name && !map?.mapId) return fail("INVALID_MAP", "map id is required"); if (!map?.bounds) return fail("INVALID_MAP", "map bounds are required"); const id = map.mapId ?? map.name; const normalized = { ...map, mapId: id, name: map.name ?? id, bounds: { ...map.bounds } }; this.maps.set(id, normalized); this.map = normalized; return ok(this.getMap()); }
  registerMap(map) { return this.loadMap(map); }
  selectMap(mapId) { const selected = this.maps.get(mapId); if (!selected) return fail("INVALID_MAP", `map not found: ${mapId}`); this.map = selected; return ok(this.getMap()); }
  listMaps() { return [...this.maps.values()].map(map => ({ mapId: map.mapId, name: map.name, bounds: { ...map.bounds } })); }
  unloadMap() { this.map = null; this.tickingAreas = []; this.tickingAreaTasks = []; this.tickingAreaFingerprint = null; this.tickingAreaPromise = null; return ok(); }
  getMap() { return this.map ? { ...this.map, bounds: { ...this.map.bounds } } : null; }
  getMapBounds() { return this.map?.bounds ? { ...this.map.bounds } : null; }
  isInside({ x, z }) { const b = this.map?.bounds; return !!b && x >= b.minX && x <= b.maxX && z >= b.minZ && z <= b.maxZ; }
  getRandomPosition(random = Math.random) { const b = this.map?.bounds; if (!b) return null; return { x: Math.floor(b.minX + random() * (b.maxX - b.minX + 1)), y: b.spawnY ?? -60, z: Math.floor(b.minZ + random() * (b.maxZ - b.minZ + 1)) }; }
  isSafePosition(position) { return this.isInside(position); }
  initializeTickingAreas(areas = []) {
    const normalized = areas.map((area, index) => ({ name: area.name ?? `tbr_stage_${index + 1}`, dimensionId: area.dimensionId ?? "overworld", ...area }));
    const fingerprint = JSON.stringify(normalized);
    if (this.tickingAreaFingerprint === fingerprint && this.tickingAreaPromise) return ok({ areas: this.tickingAreas, pending: this.tickingAreaTasks.length, reused: true });
    this.tickingAreas = normalized;
    this.tickingAreaFingerprint = fingerprint;
    this.tickingAreaTasks = [];
    let chain = this.tickingAreaPromise ?? Promise.resolve();
    chain = chain.catch(() => undefined);
    for (const area of this.tickingAreas) {
      chain = chain.then(() => {
        let dimension = null;
        try { dimension = this.world?.getDimension?.(area.dimensionId); } catch (error) { throw error; }
        if (!dimension?.runCommandAsync) return null;
        const a = area.from ?? area; const b = area.to ?? area;
        const command = `tickingarea add ${Math.floor(a.x)} ${Math.floor(a.y ?? -64)} ${Math.floor(a.z)} ${Math.floor(b.x)} ${Math.floor(b.y ?? 320)} ${Math.floor(b.z)} ${area.name}`;
        const task = dimension.runCommandAsync(command);
        if (task?.then) this.tickingAreaTasks.push(task);
        return task;
      });
    }
    this.tickingAreaPromise = chain.catch(error => { this.tickingAreaPromise = null; throw error; });
    return ok({ areas: this.tickingAreas, pending: this.tickingAreas.length });
  }
  waitForTickingAreas() { return this.tickingAreaPromise ?? Promise.resolve([]); }
  removeTickingAreas(areas = this.tickingAreas) {
    const targets = areas.map((area, index) => ({ name: area.name ?? `tbr_stage_${index + 1}`, dimensionId: area.dimensionId ?? "overworld" }));
    const tasks = targets.map(area => {
      let dimension = null;
      try { dimension = this.world?.getDimension?.(area.dimensionId); } catch (_) { return null; }
      if (!dimension?.runCommandAsync) return null;
      return dimension.runCommandAsync(`tickingarea remove ${area.name}`).catch(() => null);
    }).filter(Boolean);
    this.tickingAreaTasks = [];
    this.tickingAreaFingerprint = null;
    this.tickingAreaPromise = Promise.all(tasks).then(() => []);
    return ok({ removed: targets.length, pending: tasks.length });
  }
}
