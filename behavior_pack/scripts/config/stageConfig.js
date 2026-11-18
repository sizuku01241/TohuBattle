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
  airplane: Object.freeze({
    seats: Object.freeze([{ x: 0, y: -58, z: 0 }, { x: 1, y: -58, z: 0 }, { x: -1, y: -58, z: 0 }, { x: 0, y: -58, z: 1 }]),
    floorCenter: Object.freeze({ x: 0, y: -59, z: 0 }),
    countdownSeconds: 10,
    maxDropSeconds: 90,
  }),
  map: Object.freeze({
    name: "default",
    bounds: Object.freeze({ minX: -128, maxX: 128, minY: -64, maxY: 320, minZ: -128, maxZ: 128, spawnY: -60 }),
  }),
  zone: Object.freeze({
    warningSeconds: 150,
    shrinkSeconds: 60,
    damageIntervalTicks: 20,
    damageAmount: 1,
    minimumRadius: 6,
    stages: Object.freeze([
      Object.freeze({ targetRadius: 64, warningSeconds: 150, shrinkSeconds: 60, damageAmount: 1.0 }),
      Object.freeze({ targetRadius: 46, warningSeconds: 90, shrinkSeconds: 50, damageAmount: 1.4 }),
      Object.freeze({ targetRadius: 32, warningSeconds: 75, shrinkSeconds: 45, damageAmount: 2.0 }),
      Object.freeze({ targetRadius: 22, warningSeconds: 60, shrinkSeconds: 40, damageAmount: 2.7 }),
      Object.freeze({ targetRadius: 14, warningSeconds: 45, shrinkSeconds: 30, damageAmount: 3.8 }),
      Object.freeze({ targetRadius: 9, warningSeconds: 30, shrinkSeconds: 25, damageAmount: 5.3 }),
      Object.freeze({ targetRadius: 6, warningSeconds: 20, shrinkSeconds: 20, damageAmount: 7.4 }),
    ]),
  }),
  supplies: Object.freeze([
    Object.freeze({ x: 0, y: -59, z: 40 }),
  ]),
  tickingAreas: Object.freeze([
    Object.freeze({ name: "tbr_stage_1", dimensionId: "overworld", from: Object.freeze({ x: -128, y: -64, z: -128 }), to: Object.freeze({ x: 0, y: 320, z: 0 }) }),
    Object.freeze({ name: "tbr_stage_2", dimensionId: "overworld", from: Object.freeze({ x: 1, y: -64, z: -128 }), to: Object.freeze({ x: 128, y: 320, z: 0 }) }),
    Object.freeze({ name: "tbr_stage_3", dimensionId: "overworld", from: Object.freeze({ x: -128, y: -64, z: 1 }), to: Object.freeze({ x: 0, y: 320, z: 128 }) }),
    Object.freeze({ name: "tbr_stage_4", dimensionId: "overworld", from: Object.freeze({ x: 1, y: -64, z: 1 }), to: Object.freeze({ x: 128, y: 320, z: 128 }) }),
  ]),
});
