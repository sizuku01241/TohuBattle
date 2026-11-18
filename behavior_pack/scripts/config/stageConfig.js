// TBR stage setup. Edit these coordinates for your world.
// Coordinates are block coordinates in the selected dimension.
export const STAGE_CONFIG = Object.freeze({
  dimensionId: "overworld",
  lobby: Object.freeze({ x: 0, y: -60, z: 0 }),
  spawns: Object.freeze([
    Object.freeze({ x: 20, y: -60, z: 20 }),
    Object.freeze({ x: -20, y: -60, z: 20 }),
    Object.freeze({ x: 20, y: -60, z: -20 }),
    Object.freeze({ x: -20, y: -60, z: -20 }),
  ]),
  map: Object.freeze({
    name: "default",
    bounds: Object.freeze({ minX: -128, maxX: 128, minZ: -128, maxZ: 128, spawnY: -60 }),
  }),
  zone: Object.freeze({
    warningSeconds: 10,
    shrinkSeconds: 30,
    damageIntervalTicks: 20,
    damageAmount: 1,
    minimumRadius: 8,
  }),
  supplies: Object.freeze([
    Object.freeze({ x: 0, y: -60, z: 40 }),
  ]),
  tickingAreas: Object.freeze([
    Object.freeze({ name: "tbr_stage_1", dimensionId: "overworld", from: Object.freeze({ x: -128, y: -64, z: -128 }), to: Object.freeze({ x: 0, y: 320, z: 0 }) }),
    Object.freeze({ name: "tbr_stage_2", dimensionId: "overworld", from: Object.freeze({ x: 1, y: -64, z: -128 }), to: Object.freeze({ x: 128, y: 320, z: 0 }) }),
    Object.freeze({ name: "tbr_stage_3", dimensionId: "overworld", from: Object.freeze({ x: -128, y: -64, z: 1 }), to: Object.freeze({ x: 0, y: 320, z: 128 }) }),
    Object.freeze({ name: "tbr_stage_4", dimensionId: "overworld", from: Object.freeze({ x: 1, y: -64, z: 1 }), to: Object.freeze({ x: 128, y: 320, z: 128 }) }),
  ]),
});
