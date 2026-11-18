import { system, world, ItemStack, EquipmentSlot, DisplaySlotId, ObjectiveSortOrder, CommandPermissionLevel, CustomCommandParamType, CustomCommandStatus } from "@minecraft/server";
import { createApplication } from "./core/bootstrap.js";
import { STAGE_CONFIG } from "./config/stageConfig.js";
import { EVENTS } from "./core/Events.js";

export const app = createApplication({ scheduler: system, notifier: message => console.warn(`[TBR] ${message}`) });

const registerCommand = (registry, name, description, callback) => registry.registerCommand({
  name,
  description,
  permissionLevel: CommandPermissionLevel.GameDirectors,
  cheatsRequired: false,
}, callback);
const applyConfig = changes => {
  const result = app.configManager.applyConfigTransaction(changes);
  return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: 設定を変更しました" : `TBR: ${result.error.message}` };
};
const configMessage = () => `設定: mode=${app.configManager.getConfigValue("mode")}, teamCount=${app.configManager.getConfigValue("teamCount") ?? "なし"}, friendlyFire=${app.configManager.getConfigValue("friendlyFire") ? "on" : "off"}, countdown=${app.configManager.getConfigValue("countdownSeconds")}秒, map=${app.configManager.getConfigValue("mapName")}`;
const resolvePlayerId = value => app.playerManager.getStatus().find(p => p.id === String(value) || p.name === String(value))?.id ?? String(value);
const playerStateLabel = state => ({ WAITING: "待機", ALIVE: "生存", ELIMINATED: "脱落", DISCONNECTED: "切断", SPECTATOR: "観戦" }[state] ?? state);
const titleStyle = Object.freeze({
  start: "§r§aGAME START",
  eliminated: "§r§cELIMINATED",
  victory: "§r§6VICTORY",
  defeat: "§r§7DEFEAT",
  gameOver: "§r§eGAME OVER",
});

// Custom commands must be registered during early startup. The API requires
// namespace:command names, so these are /tbr:start etc.
system.beforeEvents.startup.subscribe(({ customCommandRegistry }) => {
  customCommandRegistry.registerEnum("tbr:config_key", ["mode", "ff", "teams", "countdown"]);
  customCommandRegistry.registerEnum("tbr:config_value", ["on", "off", "solo", "team", ...Array.from({ length: 60 }, (_, index) => String(index + 1))]);
  registerCommand(customCommandRegistry, "tbr:start", "試合を開始する", () => {
    system.run(() => {
      const result = app.matchManager.start();
      if (!result.ok) world.sendMessage(`TBR: 試合開始失敗 - ${result.error.message}`);
    });
    return { status: CustomCommandStatus.Success, message: "TBR: 試合開始を要求しました" };
  });
  registerCommand(customCommandRegistry, "tbr:stop", "試合を管理者停止する", () => {
    system.run(() => {
      const result = app.matchManager.stopByAdmin();
      if (!result.ok) world.sendMessage(`TBR: 試合停止失敗 - ${result.error.message}`);
    });
    return { status: CustomCommandStatus.Success, message: "TBR: 試合停止を要求しました" };
  });
  customCommandRegistry.registerCommand({ name: "tbr:eliminate", description: "プレイヤーを強制脱落させる", permissionLevel: CommandPermissionLevel.GameDirectors, cheatsRequired: false, mandatoryParameters: [{ type: CustomCommandParamType.String, name: "player" }], optionalParameters: [{ type: CustomCommandParamType.String, name: "reason" }] }, (_origin, playerId, reason) => {
    const targetId = resolvePlayerId(playerId); const result = app.matchManager.eliminateByAdmin(targetId, String(reason ?? "admin"));
    if (result.ok) app.logManager.record("ADMIN_COMMAND", { command: "eliminate", playerId: targetId, reason: String(reason ?? "admin") });
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: プレイヤーを強制脱落させました" : `TBR: ${result.error.message}` };
  });
  customCommandRegistry.registerCommand({ name: "tbr:revive", description: "脱落プレイヤーを復活させる", permissionLevel: CommandPermissionLevel.GameDirectors, cheatsRequired: false, mandatoryParameters: [{ type: CustomCommandParamType.String, name: "player" }] }, (_origin, playerId) => {
    const targetId = resolvePlayerId(playerId); const result = app.matchManager.reviveByAdmin(targetId);
    if (result.ok) app.logManager.record("ADMIN_COMMAND", { command: "revive", playerId: targetId });
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: プレイヤーを復活させました" : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:status", "試合状態を表示する", () => ({
    status: CustomCommandStatus.Success,
    message: `TBR状態: ${app.matchManager.getState()}`,
  }));
  customCommandRegistry.registerCommand({
    name: "tbr:preset_save",
    description: "現在の設定をプリセット保存する。例: /tbr:preset_save arena1",
    permissionLevel: CommandPermissionLevel.GameDirectors,
    cheatsRequired: false,
    mandatoryParameters: [{ type: CustomCommandParamType.String, name: "name" }],
  }, (_origin, name) => {
    const result = app.presetManager.savePreset(String(name));
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? `TBR: プリセット${name}を保存しました` : `TBR: ${result.error.message}` };
  });
  customCommandRegistry.registerCommand({
    name: "tbr:preset_load",
    description: "プリセットを読み込む。例: /tbr:preset_load arena1",
    permissionLevel: CommandPermissionLevel.GameDirectors,
    cheatsRequired: false,
    mandatoryParameters: [{ type: CustomCommandParamType.String, name: "name" }],
  }, (_origin, name) => {
    if (app.matchManager.getState() !== "LOBBY") return { status: CustomCommandStatus.Failure, message: "TBR: プリセット読込はLobby中のみ実行できます" };
    const result = app.presetManager.loadPreset(String(name));
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? `TBR: プリセット${name}を読み込みました` : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:preset_list", "保存済みプリセットを表示する", () => {
    const result = app.presetManager.listPresets();
    return { status: CustomCommandStatus.Success, message: `プリセット: ${result.data.length ? result.data.join(", ") : "なし"}` };
  });
  customCommandRegistry.registerCommand({
    name: "tbr:preset_delete",
    description: "保存済みプリセットを削除する。例: /tbr:preset_delete arena1",
    permissionLevel: CommandPermissionLevel.GameDirectors,
    cheatsRequired: false,
    mandatoryParameters: [{ type: CustomCommandParamType.String, name: "name" }],
  }, (_origin, name) => {
    const result = app.presetManager.deletePreset(String(name));
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? `TBR: プリセット${name}を削除しました` : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:help", "TBRコマンドの使い方を日本語で表示する", () => ({
    status: CustomCommandStatus.Success,
    message: "TBRヘルプ: /tbr:start 開始 /tbr:stop 停止 /tbr:status 状態 /tbr:config 設定表示・変更(例: /tbr:config ff on /tbr:config mode team /tbr:config teams 2 /tbr:config countdown 10) /tbr:preset_save 名前 保存 /tbr:preset_load 名前 読込 /tbr:preset_list 一覧 /tbr:preset_delete 名前 削除 /tbr:players プレイヤー /tbr:teams チーム /tbr:zone 安全地帯 /tbr:team_setup 編成 /tbr:team_random 再編成 /tbr:log_export ログ出力 /tbr:log_clear 消去 /tbr:log_repair 修復",
  }));
  customCommandRegistry.registerCommand({
    name: "tbr:config",
    description: "設定を表示・変更する。例: /tbr:config ff on",
    permissionLevel: CommandPermissionLevel.GameDirectors,
    cheatsRequired: false,
    optionalParameters: [
      { type: CustomCommandParamType.Enum, name: "tbr:config_key" },
      { type: CustomCommandParamType.Enum, name: "tbr:config_value" },
    ],
  }, (_origin, key, rawValue) => {
    if (key === undefined) return { status: CustomCommandStatus.Success, message: configMessage() };
    if (rawValue === undefined) return { status: CustomCommandStatus.Failure, message: "使用方法: /tbr:config <mode|ff|teams|countdown> <値>" };
    let changes;
    const value = String(rawValue).toLowerCase();
    if (key === "mode" && ["solo", "team"].includes(value)) changes = { mode: value, teamCount: value === "solo" ? null : 2, minPlayers: value === "solo" ? 1 : 4 };
    else if (key === "ff" && ["on", "off"].includes(value)) changes = { friendlyFire: value === "on" };
    else if (key === "teams") { const teamCount = Number.parseInt(value, 10); if (Number.isInteger(teamCount) && teamCount >= 2 && teamCount <= 16) changes = { mode: "team", teamCount, minPlayers: Math.max(4, teamCount * 2) }; }
    else if (key === "countdown") { const countdownSeconds = Number.parseInt(value, 10); if (Number.isInteger(countdownSeconds) && countdownSeconds >= 1 && countdownSeconds <= 60) changes = { countdownSeconds }; }
    if (!changes) return { status: CustomCommandStatus.Failure, message: "値が不正です。modeはsolo/team、ffはon/off、teamsは2-16、countdownは1-60です" };
    system.run(() => { const result = app.configManager.applyConfigTransaction(changes); world.sendMessage(result.ok ? `TBR: 設定を変更しました。${configMessage()}` : `TBR: 設定変更失敗 - ${result.error.message}`); });
    return { status: CustomCommandStatus.Success, message: "TBR: 設定変更を要求しました" };
  });
  registerCommand(customCommandRegistry, "tbr:test", "初期設定と登録プレイヤーを確認する", () => ({
    status: CustomCommandStatus.Success,
    message: `診断: state=${app.matchManager.getState()} players=${app.playerManager.getStatus().length} lobby=(${STAGE_CONFIG.lobby.x},${STAGE_CONFIG.lobby.y},${STAGE_CONFIG.lobby.z}) map=${STAGE_CONFIG.map.name}`,
  }));
  registerCommand(customCommandRegistry, "tbr:players", "登録プレイヤーの状態を表示する", () => {
    const players = app.playerManager.getStatus();
    const body = players.length === 0
      ? "登録プレイヤーなし"
      : players.map(p => `${p.name}:${playerStateLabel(p.state)}(kill:${p.kills ?? 0})`).join(" / ");
    return { status: CustomCommandStatus.Success, message: `プレイヤー: ${body}` };
  });
  registerCommand(customCommandRegistry, "tbr:teams", "チーム編成を表示する", () => {
    const teams = app.teamManager.getTeams();
    const body = teams.length === 0
      ? "チーム未作成"
      : teams.map(team => `${team.id}[${team.members.length}人]`).join(" / ");
    return { status: CustomCommandStatus.Success, message: `チーム: ${body}` };
  });
  registerCommand(customCommandRegistry, "tbr:zone", "安全地帯の状態を表示する", () => {
    const status = app.zoneManager.getZoneStatus();
    const current = status.current ? `現在(${status.current.centerX.toFixed(1)},${status.current.centerZ.toFixed(1)}) 半径${status.current.radius.toFixed(1)}` : "現在なし";
    const next = status.next ? `次(${status.next.centerX.toFixed(1)},${status.next.centerZ.toFixed(1)}) 半径${status.next.radius.toFixed(1)}` : "次なし";
    return { status: CustomCommandStatus.Success, message: `安全地帯: phase=${status.phase} ${current} ${next}` };
  });
  registerCommand(customCommandRegistry, "tbr:debug", "TBR内部状態をまとめて表示する", () => ({
    status: CustomCommandStatus.Success,
    message: `診断: match=${app.matchManager.getState()} players=${app.playerManager.getStatus().length} teams=${app.teamManager.getTeams().length} zone=${app.zoneManager.getZoneStatus().phase} map=${STAGE_CONFIG.map.name} height=${STAGE_CONFIG.map.bounds.spawnY} scan=${app.mapScanner.getStatus().state} ${app.mapScanner.getStatus().scanned}/${app.mapScanner.getStatus().total} candidates=${app.mapScanner.getStatus().valid}`,
  }));
  registerCommand(customCommandRegistry, "tbr:scan", "物資配置候補を再スキャンする", () => {
    const result = app.mapScanner.rescan();
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: マップスキャンを開始しました" : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:history", "試合履歴を表示する", () => ({ status: CustomCommandStatus.Success, message: `TBR履歴: ${app.statisticsManager.list().slice(-10).map(x => `${x.matchId}:${x.result?.winnerId ?? "draw"}`).join(" / ") || "なし"}` }));
  registerCommand(customCommandRegistry, "tbr:team_random", "待機中のプレイヤーをランダム編成する", () => {
    const ids = app.playerManager.getStatus().filter(p => p.state === "WAITING").map(p => p.id);
    const result = app.teamManager.randomAssign(ids);
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: チームをランダム編成しました" : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:team_setup", "設定したチーム数でチームを作成する", () => {
    const count = app.configManager.getConfigValue("teamCount");
    const created = app.teamManager.createTeams(count);
    if (!created.ok) return { status: CustomCommandStatus.Failure, message: `TBR: ${created.error.message}` };
    const ids = app.playerManager.getStatus().filter(p => p.state === "WAITING").map(p => p.id);
    const assigned = app.teamManager.randomAssign(ids);
    return { status: assigned.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: assigned.ok ? "TBR: チームを作成してランダム編成しました" : `TBR: ${assigned.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:log_export", "保存済みログをエクスポートする", () => {
    const result = app.logManager.export();
    return { status: result.ok === false ? CustomCommandStatus.Failure : CustomCommandStatus.Success, message: result.ok === false ? `TBR: ${result.error.message}` : "TBR: ログをエクスポートしました" };
  });
  registerCommand(customCommandRegistry, "tbr:log_clear", "保存済みログを消去する", () => {
    const result = app.logManager.clear();
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: ログを消去しました" : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:log_repair", "ログ保存状態を修復する", () => {
    const result = app.logManager.repair();
    return { status: result.ok ? CustomCommandStatus.Success : CustomCommandStatus.Failure, message: result.ok ? "TBR: ログ保存状態を修復しました" : `TBR: ${result.error.message}` };
  });
  registerCommand(customCommandRegistry, "tbr:commands", "TBRコマンド一覧を表示する", () => ({
    status: CustomCommandStatus.Success,
    message: "/tbr:help ヘルプ /tbr:start 開始 /tbr:stop 停止 /tbr:status 状態 /tbr:config 設定表示・変更 /tbr:preset_save 保存 /tbr:preset_load 読込 /tbr:preset_list 一覧 /tbr:preset_delete 削除 /tbr:players プレイヤー /tbr:teams チーム /tbr:zone 安全地帯 /tbr:debug 診断 /tbr:team_setup チーム作成 /tbr:team_random 再編成 /tbr:log_export ログ出力 /tbr:log_clear 消去 /tbr:log_repair 修復",
  }));
});

const getDimension = () => world.getDimension(STAGE_CONFIG.dimensionId);
let zoneTimer = null;
let actionbarTimer = null;
let scoreboardTimer = null;
let pillarTimer = null;
let dropTimer = null;
let dropMonitor = null;
let dropping = false;
let dropStartedAt = 0;
let airplaneFloorBackup = [];
let zoneElapsed = 0;
let actionbarTicks = 0;
const pendingLeaveTransfers = new Map();
const VALID_CAUSES = new Set(["player_attack", "fall", "fire", "lava", "drowning", "explosion", "void", "environment", "unknown"]);
const normalizeCause = (cause, attackerId = null) => attackerId ? "player_attack" : (VALID_CAUSES.has(cause) ? cause : "unknown");
const spawnZonePillar = () => { const current = app.zoneManager.getZoneStatus().current; if (!current) return; try { const dimension = getDimension(); const minY = STAGE_CONFIG.map.bounds.minY ?? -64; const maxY = Math.min(STAGE_CONFIG.map.bounds.maxY ?? 320, minY + 96); for (let y = minY; y <= maxY; y += 4) { const location = { x: current.centerX + 0.5, y, z: current.centerZ + 0.5 }; try { dimension.spawnParticle("minecraft:endrod", location); } catch (_) { dimension.spawnParticle("minecraft:basic_flame_particle", location); } } } catch (error) { console.warn(`[TBR] zone pillar failed: ${error}`); } };
const equipDropWings = player => { try { const equipment = player.getComponent("minecraft:equippable") ?? player.getComponent("equippable"); equipment?.setEquipment?.(EquipmentSlot.Chest, new ItemStack("minecraft:elytra", 1)); return !!equipment; } catch (_) { return false; } };
const createDropPlatform = () => { const center = STAGE_CONFIG.airplane.floorCenter; airplaneFloorBackup = []; try { for (let x = center.x - 3; x <= center.x + 3; x++) for (let z = center.z - 2; z <= center.z + 2; z++) { const block = getDimension().getBlock({ x, y: center.y, z }); if (!block) return false; airplaneFloorBackup.push({ x, y: center.y, z, typeId: block.typeId }); block.setType("minecraft:glass"); } return true; } catch (error) { console.warn(`[TBR] drop platform creation failed: ${error}`); return false; } };
const removeDropWings = player => { try { const equipment = player.getComponent("minecraft:equippable") ?? player.getComponent("equippable"); const item = equipment?.getEquipment?.(EquipmentSlot.Chest); if (item?.typeId === "minecraft:elytra") equipment.setEquipment(EquipmentSlot.Chest, undefined); } catch (_) {} };
const startDrop = players => { dropping = true; dropStartedAt = Date.now(); for (const record of players) { const entity = app.playerManager.getEntity(record.id); if (entity) equipDropWings(entity); } dropTimer = system.runTimeout(() => { const center = STAGE_CONFIG.airplane.floorCenter; try { for (let x = center.x - 3; x <= center.x + 3; x++) for (let z = center.z - 2; z <= center.z + 2; z++) { const block = getDimension().getBlock({ x, y: center.y, z }); if (block?.typeId === "minecraft:glass") block.setType("minecraft:air"); } } catch (error) { console.warn(`[TBR] drop platform opening failed: ${error}`); } }, STAGE_CONFIG.airplane.countdownSeconds * 20); dropMonitor = system.runInterval(() => { const active = players.map(p => app.playerManager.getEntity(p.id)).filter(Boolean).filter(e => app.playerManager.isAlive(e.id)); const landed = active.filter(e => !e.isGliding && e.location.y < STAGE_CONFIG.airplane.floorCenter.y - 2); if (!active.length || landed.length === active.length || Date.now() - dropStartedAt > STAGE_CONFIG.airplane.maxDropSeconds * 1000) { for (const entity of landed) removeDropWings(entity); dropping = false; if (dropMonitor !== null) system.clearRun(dropMonitor); dropMonitor = null; } }, 5); };
const spawnSupplies = () => { const cached = app.mapScanner.getCandidates(); const configured = STAGE_CONFIG.supplies; const fallback = []; const b = STAGE_CONFIG.map.bounds; if (!cached.length) for (let x = b.minX + 8; x <= b.maxX - 8 && fallback.length < 48; x += 32) for (let z = b.minZ + 8; z <= b.maxZ - 8 && fallback.length < 48; z += 32) fallback.push({ x, y: b.spawnY + 1, z }); const positions = [...configured, ...(cached.length ? cached : fallback)].filter((position, index, list) => list.findIndex(other => Math.hypot(other.x - position.x, other.z - position.z) < 2) === index).slice(0, 48); let placed = 0; for (const position of positions) { const result = app.itemManager.spawnChest(getDimension(), position, [{ id: "minecraft:bread", amount: 4 }]); if (result.ok) placed += 1; else console.warn(`[TBR] supply chest failed: ${result.error.message}`); } if (!placed) throw new Error("no supply could be placed"); };
const clearScoreboard = objective => {
  for (const participant of objective.getParticipants?.() ?? []) {
    try { objective.removeParticipant(participant); } catch (_) { /* stale scoreboard entry */ }
  }
};
const updateScoreboard = () => {
  try {
    const scoreboard = world.scoreboard;
    let objective = scoreboard.getObjective("tbr_alive");
    if (objective && objective.displayName !== "TOHU BATTLE ROYALE") {
      scoreboard.removeObjective(objective);
      objective = undefined;
    }
    if (!objective) objective = scoreboard.addObjective("tbr_alive", "TOHU BATTLE ROYALE");
    clearScoreboard(objective);
    const records = app.playerManager.getStatus();
    const alive = records.filter(record => record.state === "ALIVE").length;
    const config = app.configManager.getConfig();
    const lines = [
      "§r§aTOHU BATTLE ROYALE",
      `§r§aモード: §e${config.mode === "team" ? "TEAM" : "SOLO"}`,
      `§r§a生存者数: §f${alive}/${records.length}`,
      "§r§8----------------",
    ];
    lines.push(`§r§aチーム数: §f${config.mode === "team" ? app.teamManager.getTeams().length : 0}`);
    lines.push(`§r§aZone: §f${app.zoneManager.getZoneStatus().stage ?? 0}/7`);
    lines.forEach((line, index) => objective.setScore(`${line}§${index}`, lines.length - index));
    scoreboard.setObjectiveAtDisplaySlot(DisplaySlotId.Sidebar, { objective, sortOrder: ObjectiveSortOrder.Descending });
  } catch (error) { console.warn(`[TBR] scoreboard update failed: ${error}`); }
};
const teleportTo = (player, location) => {
  try { player.teleport(location, { dimension: getDimension() }); }
  catch (error) { console.warn(`[TBR] teleport failed: ${error}`); }
};
const formatClock = seconds => `${Math.floor(seconds / 60)}:${String(Math.max(0, seconds % 60)).padStart(2, "0")}`;
const truncateName = (name, maxLength) => [...String(name ?? "")].slice(0, maxLength).join("");
const healthInfo = entity => {
  try {
    const health = entity?.getComponent?.("minecraft:health");
    const current = Math.max(0, health?.currentValue ?? 0);
    const max = Math.max(1, health?.effectiveMax ?? health?.defaultValue ?? 20);
    return { current, max, ratio: current / max };
  } catch (_) { return { current: 0, max: 20, ratio: 0 }; }
};
const healthColor = (ratio, blink) => ratio >= 0.6 ? "§a" : ratio >= 0.3 ? "§e" : blink ? "§c" : "§7";
const buildTeammateText = (playerId, config) => {
  if (config.mode !== "team") return "";
  const teamId = app.teamManager.getTeamId(playerId);
  if (!teamId) return "";
  const members = app.teamManager.getMembers(teamId).filter(id => id !== playerId);
  if (!members.length) return "";
  const maxLength = members.length <= 2 ? 6 : members.length === 3 ? 4 : 3;
  const records = members.map(id => {
    const record = app.playerManager.getPlayer(id);
    const entity = app.playerManager.getEntity(id);
    const health = healthInfo(entity);
    return { record, entity, health };
  }).filter(item => item.record);
  records.sort((a, b) => {
    const aAlive = a.record.state === "ALIVE";
    const bAlive = b.record.state === "ALIVE";
    if (aAlive !== bAlive) return aAlive ? -1 : 1;
    return aAlive ? a.health.ratio - b.health.ratio : 0;
  });
  const blink = Math.floor(actionbarTicks / 10) % 2 === 0;
  return records.map(({ record, health }) => {
    const name = truncateName(record.name, maxLength);
    if (record.state === "ELIMINATED") return `§8§m${name}§r §cX`;
    if (record.state === "DISCONNECTED" || record.state === "SPECTATOR") return `§7${name} OFF`;
    return `§f${name} ${healthColor(health.ratio, blink)}${Math.floor(health.current)}`;
  }).join(" §8| ");
};
const buildActionbar = (player, status, config) => {
  const current = status.current;
  const distance = current ? Math.hypot(player.location.x - current.centerX, player.location.z - current.centerZ) : 0;
  const radius = current ? Math.ceil(current.radius) : 0;
  const inside = !current || distance <= current.radius;
  const nearBoundary = current && distance >= current.radius * 0.9 && inside;
  const blink = Math.floor(actionbarTicks / 10) % 2 === 0;
  const zoneState = inside ? "§aIN" : (blink ? "§c§lOUT" : "§r§cOUT");
  const distanceColor = inside ? (nearBoundary ? "§e" : "§f") : "§c";
  const stage = STAGE_CONFIG.zone.stages?.[status.stage ?? 0] ?? STAGE_CONFIG.zone;
  let timerText = "§7ZONE --";
  if (status.phase === "shrinking") timerText = "§bSHRINKING";
  else if (status.phase === "warning") {
    const remaining = Math.max(0, stage.warningSeconds - zoneElapsed);
    const timerColor = remaining <= 5 ? (blink ? "§c" : "§r§c") : remaining <= 10 ? "§e" : "§f";
    timerText = `${timerColor}ZONE ${formatClock(remaining)}`;
  }
  const teamText = buildTeammateText(player.id, config);
  let result = `${zoneState} ${distanceColor}${Math.floor(distance)}m§7/${radius}m ${timerText}${teamText ? ` §8| ${teamText}` : ""}`;
  if (result.replace(/§./g, "").length > 90) result = result.replace("ZONE ", "Z ");
  return result;
};
const showTitle = (player, title, subtitle = "") => {
  try { player.onScreenDisplay?.setTitle?.(title, { subtitle, fadeInDuration: 0, stayDuration: 40, fadeOutDuration: 10 }); }
  catch (_) { /* player may be invalid or title API may be unavailable */ }
};

world.afterEvents.playerSpawn.subscribe(({ player }) => {
  if (!app.playerManager.getPlayer(player.id)) app.playerManager.registerPlayer(player);
  else app.playerManager.attachEntity(player.id, player);
  if (app.matchManager.getState() === "LOBBY") {
    app.playerManager.returnToLobby(player.id);
    try { player.setGameMode?.("adventure"); } catch (_) { /* game mode may be unavailable during early spawn */ }
    teleportTo(player, STAGE_CONFIG.lobby);
  } else if (app.playerManager.getPlayer(player.id)?.state !== "ALIVE") {
    app.playerManager.setSpectator(player.id);
    try { player.setGameMode?.("spectator"); } catch (_) { /* entity may be invalid */ }
  }
});

world.beforeEvents.entityHurt.subscribe(event => {
  if (event.hurtEntity?.typeId !== "minecraft:player") return;
  const attacker = event.damageSource?.damagingEntity;
  if (dropping && attacker?.typeId === "minecraft:player") { event.cancel = true; return; }
  const result = app.combatManager.handleDamage({
    attackerId: attacker?.typeId === "minecraft:player" ? attacker.id : null,
    victimId: event.hurtEntity.id,
    cause: event.damageSource?.cause ?? "unknown",
    amount: event.damage,
  });
  if (result.ok && result.data?.cancelled) event.cancel = true;
});

world.beforeEvents.playerLeave.subscribe(({ player }) => {
  const record = app.playerManager.getPlayer(player.id);
  if (!record || (record.state !== "ALIVE" && record.state !== "WAITING")) return;
  const teamId = app.teamManager.getTeamId(player.id);
  const recipients = teamId
    ? app.teamManager.getMembers(teamId).filter(id => id !== player.id && app.playerManager.isAlive(id)).map(id => app.playerManager.getEntity(id)).filter(Boolean)
    : [];
  const result = app.inventoryTransferService.transferOnDisconnect(player, recipients);
  pendingLeaveTransfers.set(player.id, result.ok ? result.data.status : "failed");
});

world.afterEvents.playerLeave.subscribe(({ playerId }) => {
  const result = app.playerManager.disconnectPlayer(playerId);
  const itemTransfer = pendingLeaveTransfers.get(playerId) ?? "not_applicable";
  pendingLeaveTransfers.delete(playerId);
  if (result.ok) {
    app.logManager.record("PLAYER_DISCONNECTED", { playerId, previousState: result.data.previousState, spectatorOnReconnect: true, itemTransfer });
    if (result.data.previousState === "ALIVE") app.matchManager.checkVictory();
  }
});

world.afterEvents.entityDie.subscribe(event => {
  const victim = event.deadEntity;
  if (!victim || victim.typeId !== "minecraft:player") return;
  const attacker = event.damageSource?.damagingEntity;
  const attackerId = attacker?.typeId === "minecraft:player" ? attacker.id : null;
  const cause = normalizeCause(event.damageSource?.cause ?? "unknown", attackerId);
  const result = app.combatManager.resolveKill(victim.id, {
    cause,
    attackerId,
  });
  if (result.ok) {
    app.logManager.record("PLAYER_ELIMINATED", { playerId: victim.id, cause, lastAttacker: attackerId });
    app.matchManager.checkVictory();
  }
});

app.eventBus.on(EVENTS.MATCH_STARTED, ({ matchId }) => {
  app.mapManager.initializeTickingAreas(STAGE_CONFIG.tickingAreas);
  const players = app.playerManager.getStatus().filter(p => p.state === "ALIVE");
  if (!createDropPlatform()) { world.sendMessage("TBR: 降下用ガラス床を作成できませんでした"); app.matchManager.stopByAdmin(); return; }
  players.forEach((record, index) => {
    const entity = app.playerManager.getEntity(record.id);
    if (entity) teleportTo(entity, STAGE_CONFIG.airplane.seats[index % STAGE_CONFIG.airplane.seats.length] ?? STAGE_CONFIG.spawns[index % STAGE_CONFIG.spawns.length]);
  });
  app.logManager.record("MATCH_START", { matchId, mode: app.configManager.getConfigValue("mode"), teamCount: app.configManager.getConfigValue("teamCount") });
  app.statisticsManager.start({ matchId, config: app.configManager.getConfig(), players, teams: app.teamManager.getTeams() });
  for (const record of players) {
    const entity = app.playerManager.getEntity(record.id);
    if (entity) showTitle(entity, titleStyle.start);
  }
  startDrop(players);
  spawnSupplies();
  app.zoneManager.initialize();
  app.zoneManager.generateNextZone(STAGE_CONFIG.zone.stages?.[0]?.targetRadius ?? STAGE_CONFIG.zone.minimumRadius);
  app.zoneManager.startWarning();
  pillarTimer = system.runInterval(spawnZonePillar, 10);
  spawnZonePillar();
  zoneElapsed = 0;
  actionbarTicks = 0;
  zoneTimer = system.runInterval(() => {
    if (app.matchManager.getState() !== "IN_PROGRESS") return;
    zoneElapsed++;
    const status = app.zoneManager.getZoneStatus();
    const zoneStage = STAGE_CONFIG.zone.stages?.[status.stage ?? 0] ?? STAGE_CONFIG.zone;
    if (status.phase === "warning" && zoneElapsed >= zoneStage.warningSeconds) { zoneElapsed = 0; app.zoneManager.startShrink(); }
    else if (status.phase === "shrinking") {
      app.zoneManager.update(zoneElapsed / zoneStage.shrinkSeconds);
      if (app.zoneManager.getZoneStatus().phase === "stable") {
        zoneElapsed = 0;
        const current = app.zoneManager.getZoneStatus().current;
        if (!current || current.radius > STAGE_CONFIG.zone.minimumRadius) {
          const nextStage = STAGE_CONFIG.zone.stages?.[app.zoneManager.getZoneStatus().stage] ?? STAGE_CONFIG.zone;
          if (current && current.radius > STAGE_CONFIG.zone.minimumRadius && nextStage) { app.zoneManager.generateNextZone(nextStage.targetRadius ?? STAGE_CONFIG.zone.minimumRadius); app.zoneManager.startWarning(); }
        }
      }
    }
    const alive = app.playerManager.getAlivePlayers().map(player => app.playerManager.getEntity(player.id)).filter(Boolean);
    app.zoneManager.applyOutsideDamage(alive, zoneStage.damageAmount ?? STAGE_CONFIG.zone.damageAmount);
  }, 20);
  actionbarTimer = system.runInterval(() => {
    if (app.matchManager.getState() !== "IN_PROGRESS") return;
    actionbarTicks++;
    const status = app.zoneManager.getZoneStatus();
    const config = app.configManager.getConfig();
    for (const player of world.getPlayers()) {
      try { player.onScreenDisplay?.setActionBar?.(buildActionbar(player, status, config)); } catch (_) { /* player may be invalid */ }
    }
    if (actionbarTicks === 1 || actionbarTicks % 20 === 0) app.locatorAdapter.update(app.playerManager.getStatus(), app.teamManager);
  }, 1);
  scoreboardTimer = system.runInterval(updateScoreboard, 20);
  updateScoreboard();
});

app.eventBus.on(EVENTS.PLAYER_ELIMINATED, ({ playerId }) => {
  app.statisticsManager.onElimination(playerId, app.playerManager.getPlayer(playerId)?.cause ?? "unknown");
  const entity = app.playerManager.getEntity(playerId);
  if (entity) showTitle(entity, titleStyle.eliminated);
  const player = app.playerManager.getPlayer(playerId);
  world.sendMessage(`§r§7[TBR] ${player?.name ?? playerId} が脱落しました`);
  try { entity?.setGameMode?.("spectator"); } catch (_) { /* entity can be invalid */ }
  app.playerManager.setSpectator(playerId);
});

app.eventBus.on(EVENTS.COMBAT_KILL, ({ victimId, attackerId, cause }) => {
  const victim = app.playerManager.getPlayer(victimId);
  const attacker = attackerId ? app.playerManager.getPlayer(attackerId) : null;
  const victimEntity = app.playerManager.getEntity(victimId);
  const attackerEntity = attackerId ? app.playerManager.getEntity(attackerId) : null;
  let distance = "—";
  if (victimEntity?.location && attackerEntity?.location) {
    const dx = attackerEntity.location.x - victimEntity.location.x;
    const dy = attackerEntity.location.y - victimEntity.location.y;
    const dz = attackerEntity.location.z - victimEntity.location.z;
    distance = Math.sqrt(dx * dx + dy * dy + dz * dz).toFixed(2) + "m";
  }
  const source = attacker?.name ?? (cause === "unknown" ? "Environment" : cause);
  world.sendMessage(`§r§c[KILL] §b${source} §e»» §c${victim?.name ?? victimId} §7(${distance})`);
  if (attackerId) app.statisticsManager.onKill(attackerId);
});
app.eventBus.on("combat:assist", ({ attackerId }) => app.statisticsManager.onAssist(attackerId));

app.eventBus.on(EVENTS.MATCH_ENDED, data => {
  app.statisticsManager.finish(data);
  if (zoneTimer !== null) { system.clearRun(zoneTimer); zoneTimer = null; }
  if (actionbarTimer !== null) { system.clearRun(actionbarTimer); actionbarTimer = null; }
  if (scoreboardTimer !== null) { system.clearRun(scoreboardTimer); scoreboardTimer = null; }
  if (pillarTimer !== null) { system.clearRun(pillarTimer); pillarTimer = null; }
  if (dropTimer !== null) { system.clearRun(dropTimer); dropTimer = null; }
  if (dropMonitor !== null) { system.clearRun(dropMonitor); dropMonitor = null; }
  dropping = false;
  for (const block of airplaneFloorBackup) { try { getDimension().getBlock(block)?.setType(block.typeId); } catch (_) {} }
  airplaneFloorBackup = [];
  const endObjective = world.scoreboard.getObjective("tbr_alive");
  if (endObjective) clearScoreboard(endObjective);
  try { world.scoreboard.clearObjectiveAtDisplaySlot(DisplaySlotId.Sidebar); } catch (_) { /* scoreboard may already be cleared */ }
  app.zoneManager.initialize(null);
  app.locatorAdapter.clear();
  app.itemManager.clearSpawned();
  app.mapManager.removeTickingAreas(STAGE_CONFIG.tickingAreas);
  app.logManager.record("MATCH_END", data);
  for (const record of app.playerManager.getStatus()) {
    const entity = app.playerManager.getEntity(record.id);
    if (entity) {
      const isWinner = data.winnerType === "player"
        ? data.winnerId === record.id
        : data.winnerType === "team" && app.teamManager.getTeamId(record.id) === data.winnerId;
      showTitle(entity, data.winnerType ? (isWinner ? titleStyle.victory : titleStyle.defeat) : titleStyle.gameOver);
      try { entity.setGameMode?.("adventure"); } catch (_) { /* entity may be invalid */ }
      teleportTo(entity, STAGE_CONFIG.lobby);
    }
  }
  app.playerManager.resetForLobby();
});

system.run(() => console.warn("[TBR] application initialized"));
system.run(() => {
  const scan = app.mapScanner.start();
  if (!scan.ok) console.warn(`[TBR] map scan failed: ${scan.error.message}`);
});
system.run(() => {
  const ticking = app.mapManager.removeTickingAreas(STAGE_CONFIG.tickingAreas);
  if (ticking.ok) console.warn(`[TBR] stale ticking areas removed: ${ticking.data.removed}`);
});
system.run(() => {
  const recovery = app.itemManager.recover(id => world.getDimension(id ?? STAGE_CONFIG.dimensionId));
  if (recovery.ok && recovery.data.restored > 0) console.warn(`[TBR] recovered ${recovery.data.restored} interrupted supply blocks`);
  const interrupted = app.matchManager.consumeInterruptedState?.();
  if (interrupted) {
    app.playerManager.resetForLobby();
    app.teamManager.unlockTeams();
    app.logManager.record("ADMIN_COMMAND", { command: "world_restart", result: "cancelled", error: "match interrupted and returned to lobby" });
    console.warn(`[TBR] interrupted match ${interrupted.matchId ?? "unknown"} was returned to Lobby`);
  }
});
