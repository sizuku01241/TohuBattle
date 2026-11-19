import test from "node:test";
import assert from "node:assert/strict";
import { EventBus } from "../behavior_pack/scripts/core/EventBus.js";
import { TeamManager } from "../behavior_pack/scripts/team/TeamManager.js";
import { PlayerManager } from "../behavior_pack/scripts/player/PlayerManager.js";
import { CombatManager } from "../behavior_pack/scripts/combat/CombatManager.js";
import { ZoneManager } from "../behavior_pack/scripts/zone/ZoneManager.js";
import { MinecraftStorageAdapter } from "../behavior_pack/scripts/platform/MinecraftStorageAdapter.js";
import { MapManager } from "../behavior_pack/scripts/map/MapManager.js";
import { MatchManager } from "../behavior_pack/scripts/match/MatchManager.js";
import { ConfigManager } from "../behavior_pack/scripts/config/ConfigManager.js";
import { LogManager } from "../behavior_pack/scripts/log/LogManager.js";
import { MapScanner } from "../behavior_pack/scripts/map/MapScanner.js";
import { MatchStatisticsManager } from "../behavior_pack/scripts/match/MatchStatisticsManager.js";

const setupPlayers = (names) => { const bus = new EventBus(); const pm = new PlayerManager({ eventBus: bus }); for (const id of names) pm.registerPlayer({ id, name: id }); return { bus, pm }; };

test("teams are balanced and cannot be changed after locking", () => {
  const teams = new TeamManager(); teams.createTeams(2); assert.equal(teams.randomAssign(["a", "b", "c", "d"]).ok, true); assert.equal(teams.validateTeams(["a", "b", "c", "d"]).ok, true); teams.lockTeams(); assert.equal(teams.assignPlayer("a", "team_02").ok, false);
});

test("automatic team assignment allows a size difference of one but fixed teams require exact capacity", () => {
  const teams = new TeamManager(); teams.createTeams(2);
  assert.equal(teams.randomAssign(["a", "b", "c", "d", "e"]).ok, true);
  assert.equal(teams.validateTeams(["a", "b", "c", "d", "e"]).ok, true);
  const fixed = new TeamManager(); fixed.createTeams(2);
  assert.equal(fixed.randomAssign(["a", "b", "c", "d", "e"], Math.random, { fixedTeamSize: 3 }).ok, false);
});

test("friendly fire is cancelled and enemy damage becomes an assistable attack", () => {
  const { pm } = setupPlayers(["a", "b", "c"]); pm.activatePlayer("a"); pm.activatePlayer("b"); pm.activatePlayer("c"); const teams = new TeamManager(); teams.createTeams(2); teams.assignPlayer("a", "team_01"); teams.assignPlayer("b", "team_01"); teams.assignPlayer("c", "team_02"); const config = { getConfigValue: key => ({ friendlyFire: false }[key]), getConfig: () => ({ assistWindowSeconds: 10, assistDamage: 5, environmentKillWindowSeconds: 10 }) }; const combat = new CombatManager({ eventBus: new EventBus(), playerManager: pm, teamManager: teams, configManager: config, clock: () => 1000 }); assert.equal(combat.handleDamage({ attackerId: "a", victimId: "b", amount: 5 }).data.cancelled, true); assert.equal(combat.handleDamage({ attackerId: "c", victimId: "b", amount: 5 }).data.cancelled, false); assert.equal(pm.getPlayer("c").damage, 5);
  combat.reset(); assert.equal(combat.getLastAttacker("b"), null);
});

test("zone interpolation uses the original start snapshot and configured target radius", () => {
  const zones = new ZoneManager({ mapManager: { getMapBounds: () => ({ minX: 0, maxX: 100, minZ: 0, maxZ: 100 }) }, random: () => 0.5 }); zones.initialize(); const before = zones.getZoneStatus().current; zones.generateNextZone(10); assert.equal(zones.getZoneStatus().next.radius, 10); zones.startShrink(); zones.update(0.5); const middle = zones.getZoneStatus().current; zones.update(1); const end = zones.getZoneStatus().current; assert.equal(middle.radius, (before.radius + end.radius) / 2); assert.equal(zones.getZoneStatus().stage, 1);
});

test("dynamic property storage transparently chunks large values", () => {
  const values = new Map(); const world = { getDynamicProperty: key => values.get(key), setDynamicProperty: (key, value) => value === undefined ? values.delete(key) : values.set(key, value) }; const storage = new MinecraftStorageAdapter({ world }); const payload = { text: "x".repeat(50000) }; assert.equal(storage.set("large", payload), true); assert.deepEqual(storage.get("large"), payload); assert.equal(storage.delete("large"), true); assert.equal(storage.get("large"), null);
});

test("map manager registers and selects maps", () => {
  const maps = new MapManager(); maps.registerMap({ mapId: "a", bounds: { minX: 0, maxX: 10, minZ: 0, maxZ: 10 } }); maps.registerMap({ mapId: "b", bounds: { minX: -10, maxX: 0, minZ: -10, maxZ: 0 } }); assert.equal(maps.selectMap("b").ok, true); assert.equal(maps.getMap().mapId, "b"); assert.equal(maps.selectMap("missing").ok, false);
});

test("admin stop requires confirmation", () => {
  const manager = new MatchManager({ configManager: { getConfigValue: () => null, getConfig: () => ({ mode: "solo", minPlayers: 1, maxPlayers: 32 }) }, playerManager: { getStatus: () => [] }, teamManager: { unlockTeams() {} } }); manager.state = "IN_PROGRESS"; assert.equal(manager.stopByAdmin().error.code, "CONFIRMATION_REQUIRED"); assert.equal(manager.stopByAdmin().ok, true); assert.equal(manager.getState(), "LOBBY");
});

test("match manager starts a solo match and ends after the last player is eliminated", () => {
  const bus = new EventBus(); const { pm } = setupPlayers(["a", "b"]); const teams = new TeamManager(); const config = { getConfigValue: key => ({ mapName: "default", victoryConfirmationTicks: 1 }[key]), getConfig: () => ({ mode: "solo", minPlayers: 1, maxPlayers: 32, countdownSeconds: 1, mapName: "default", victoryConfirmationTicks: 1 }) }; const manager = new MatchManager({ eventBus: bus, configManager: config, playerManager: pm, teamManager: teams }); let ended = null; bus.on("match:ended", data => { ended = data; }); assert.equal(manager.start().ok, true); assert.equal(manager.getState(), "PREPARING"); assert.equal(manager.setPhase("IN_PROGRESS").ok, false); assert.equal(manager.setPhase("DROPPING").ok, true); assert.equal(manager.setPhase("IN_PROGRESS").ok, true); pm.eliminatePlayer("b", { cause: "player_attack" }); assert.equal(manager.checkVictory().ok, true); assert.equal(ended?.winnerId, "a"); assert.equal(manager.getState(), "LOBBY");
});

test("disconnecting an alive player marks them disconnected and removes them from alive players", () => {
  const { pm } = setupPlayers(["a"]); pm.activatePlayer("a"); assert.equal(pm.disconnectPlayer("a").ok, true); assert.equal(pm.getPlayer("a").state, "DISCONNECTED"); assert.equal(pm.getAlivePlayers().length, 0);
});

test("config validation rejects unsafe player and zone values", () => {
  const config = new ConfigManager(); assert.equal(config.validateConfig({ ...config.getConfig(), maxPlayers: 33 }).ok, false); assert.equal(config.validateConfig({ ...config.getConfig(), zone: { ...config.getConfig().zone, damageMultiplier: 0 } }).ok, false); assert.equal(config.validateConfig({ ...config.getConfig(), countdownSeconds: 301 }).ok, false);
});

test("environment damage can be disabled independently from PvP", () => {
  const { pm } = setupPlayers(["a"]); pm.activatePlayer("a"); const teams = new TeamManager(); const config = { getConfigValue: () => false, getConfig: () => ({ environmentDamage: { lava: false }, assistWindowSeconds: 10, assistDamage: 5, environmentKillWindowSeconds: 10 }) }; const combat = new CombatManager({ eventBus: new EventBus(), playerManager: pm, teamManager: teams, configManager: config }); const result = combat.handleDamage({ victimId: "a", cause: "lava", amount: 2 }); assert.equal(result.ok, true); assert.equal(result.data.cancelled, true);
});

test("log persistence failure keeps the pending entry for a later retry", () => {
  let shouldFail = true; const saved = []; const storage = { load: () => ({ logs: [], queue: [], nextLogId: 1, nextMatchId: 1 }), save: value => { if (shouldFail) return false; saved.push(value); return true; }, loadClearState: () => "idle" }; const logs = new LogManager({ storage, clock: () => new Date("2026-01-01T00:00:00Z") }); assert.equal(logs.record("TEST").ok, false); shouldFail = false; assert.equal(logs.record("RETRY").ok, true); assert.equal(logs.getLogs().map(entry => entry.type).join(","), "TEST,RETRY"); assert.equal(saved.length, 1);
});

test("map scanner invalidates candidate cache when map bounds change", () => {
  const values = new Map(); const storage = { get: key => values.get(key), set: (key, value) => { values.set(key, value); return true; } }; const maps = new MapManager(); maps.registerMap({ mapId: "arena", bounds: { minX: 0, maxX: 1, minY: 0, maxY: 10, minZ: 0, maxZ: 1 } }); const scanner = new MapScanner({ storage, mapManager: maps, world: {} }); values.set(scanner.cacheKey(), { scannerVersion: 5, boundsFingerprint: "0,1,0,10,0,1", candidates: [{ x: 0, y: 1, z: 0 }] }); assert.equal(scanner.loadCache(), true); maps.loadMap({ mapId: "arena", bounds: { minX: 0, maxX: 2, minY: 0, maxY: 10, minZ: 0, maxZ: 2 } }); assert.equal(scanner.loadCache(), false);
});

test("victory confirmation rechecks the planned winner is still alive", () => {
  const { pm } = setupPlayers(["a", "b"]); pm.activatePlayer("a"); pm.activatePlayer("b"); let confirmation = null; const manager = new MatchManager({ configManager: { getConfigValue: key => key === "victoryConfirmationTicks" ? 1 : null, getConfig: () => ({ mode: "solo", victoryConfirmationTicks: 1 }) }, playerManager: pm, teamManager: new TeamManager(), scheduler: { runTimeout: callback => { confirmation = callback; return 1; }, clearRun() {} } }); manager.state = "IN_PROGRESS"; pm.eliminatePlayer("b"); manager.checkVictory(); pm.eliminatePlayer("a"); confirmation(); assert.equal(manager.getState(), "IN_PROGRESS");
});

test("match statistics keep team kills separate from individual kills", () => {
  const stats = new MatchStatisticsManager();
  stats.start({ matchId: "m1", config: { mapName: "arena", mode: "team" }, players: [{ id: "a", name: "A" }, { id: "b", name: "B" }], teams: [{ id: "team_01", members: ["a", "b"] }] });
  stats.onKill("a");
  assert.equal(stats.current.participants.find(player => player.id === "a").kills, 1);
  assert.deepEqual(stats.current.teamStats, [{ teamId: "team_01", kills: 1 }]);
});

test("ticking area preparation can be awaited and propagates command failure", async () => {
  let resolveCommand;
  const command = new Promise(resolve => { resolveCommand = resolve; });
  const maps = new MapManager({ world: { getDimension: () => ({ runCommandAsync: () => command }) } });
  maps.initializeTickingAreas([{ name: "stage", from: { x: 0, y: 0, z: 0 }, to: { x: 1, y: 1, z: 1 } }]);
  let completed = false;
  const waiting = maps.waitForTickingAreas().then(() => { completed = true; });
  await Promise.resolve();
  assert.equal(completed, false);
  resolveCommand();
  await waiting;
  assert.equal(completed, true);

  const failing = new MapManager({ world: { getDimension: () => ({ runCommandAsync: () => Promise.reject(new Error("command failed")) }) } });
  failing.initializeTickingAreas([{ name: "stage" }]);
  await assert.rejects(failing.waitForTickingAreas(), /command failed/);
});

test("changing the selected map invalidates the scan before match start", () => {
  const maps = new MapManager();
  maps.registerMap({ mapId: "default", bounds: { minX: 0, maxX: 10, minY: 0, maxY: 20, minZ: 0, maxZ: 10 } });
  maps.registerMap({ mapId: "arena", bounds: { minX: 100, maxX: 110, minY: 0, maxY: 20, minZ: 100, maxZ: 110 } });
  maps.selectMap("default");
  let rescans = 0;
  const manager = new MatchManager({ mapManager: maps, mapScanner: { rescan: () => { rescans += 1; }, isReady: () => false }, configManager: { getConfigValue: key => key === "mapName" ? "arena" : null, getConfig: () => ({ mode: "solo", minPlayers: 1, maxPlayers: 32, mapName: "arena" }) }, playerManager: { getStatus: () => [] }, teamManager: new TeamManager() });
  assert.equal(manager.validateStart().error.code, "MAP_SCAN_INCOMPLETE");
  assert.equal(rescans, 1);
});
