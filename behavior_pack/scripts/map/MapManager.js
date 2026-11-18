import { fail, ok } from "../core/Constants.js";
export class MapManager {
  constructor({ worldAdapter = null, world = null } = {}) { this.worldAdapter = worldAdapter; this.world = world; this.map = null; this.tickingAreas = []; this.tickingAreaTasks = []; }
  loadMap(map) { if (!map?.bounds) return fail("INVALID_MAP", "map bounds are required"); this.map = { ...map, bounds: { ...map.bounds } }; return ok(this.getMap()); }
  unloadMap() { this.map = null; this.tickingAreas = []; this.tickingAreaTasks = []; return ok(); }
  getMap() { return this.map ? { ...this.map, bounds: { ...this.map.bounds } } : null; }
  getMapBounds() { return this.map?.bounds ? { ...this.map.bounds } : null; }
  isInside({ x, z }) { const b = this.map?.bounds; return !!b && x >= b.minX && x <= b.maxX && z >= b.minZ && z <= b.maxZ; }
  getRandomPosition(random = Math.random) { const b = this.map?.bounds; if (!b) return null; return { x: Math.floor(b.minX + random() * (b.maxX - b.minX + 1)), y: b.spawnY ?? -60, z: Math.floor(b.minZ + random() * (b.maxZ - b.minZ + 1)) }; }
  isSafePosition(position) { return this.isInside(position); }
  initializeTickingAreas(areas = []) {
    this.tickingAreas = areas.map((area, index) => ({ name: area.name ?? `tbr_stage_${index + 1}`, dimensionId: area.dimensionId ?? "overworld", ...area }));
    this.tickingAreaTasks = this.tickingAreas.map(area => {
      let dimension = null;
      try { dimension = this.world?.getDimension?.(area.dimensionId); } catch (_) { return null; }
      if (!dimension?.runCommandAsync) return null;
      const a = area.from ?? area; const b = area.to ?? area;
      const command = `tickingarea add ${Math.floor(a.x)} ${Math.floor(a.y ?? -64)} ${Math.floor(a.z)} ${Math.floor(b.x)} ${Math.floor(b.y ?? 320)} ${Math.floor(b.z)} ${area.name}`;
      return dimension.runCommandAsync(command).catch(() => null);
    }).filter(Boolean);
    return ok({ areas: this.tickingAreas, pending: this.tickingAreaTasks.length });
  }
  removeTickingAreas(areas = this.tickingAreas) {
    const targets = areas.map((area, index) => ({ name: area.name ?? `tbr_stage_${index + 1}`, dimensionId: area.dimensionId ?? "overworld" }));
    const tasks = targets.map(area => {
      let dimension = null;
      try { dimension = this.world?.getDimension?.(area.dimensionId); } catch (_) { return null; }
      if (!dimension?.runCommandAsync) return null;
      return dimension.runCommandAsync(`tickingarea remove ${area.name}`).catch(() => null);
    }).filter(Boolean);
    this.tickingAreaTasks = [];
    return ok({ removed: targets.length, pending: tasks.length });
  }
}
