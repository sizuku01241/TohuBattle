import test from "node:test";
import assert from "node:assert/strict";
import { inCircle, inCone, inLine } from "../ability_geometry.mjs";

test("ability geometry detects circle, cone, and line", () => {
  assert.equal(inCircle({ x: 0, z: 0 }, { x: 2, z: 0 }, 3), true);
  assert.equal(inCone({ x: 0, z: 0 }, { x: 1, z: 0 }, { x: 2, z: 0 }, 3, 60), true);
  assert.equal(inLine({ x: 0, z: 0 }, { x: 1, z: 0 }, { x: 2, z: 0.5 }, 3, 1), true);
  assert.equal(inCircle({ x: 0, z: 0 }, { x: 4, z: 0 }, 3), false);
});
