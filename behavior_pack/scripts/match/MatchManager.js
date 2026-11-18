import { ERROR_CODES, GAME_MODES, MATCH_STATES, fail, ok } from "../core/Constants.js";
import { EVENTS } from "../core/Events.js";

export class MatchManager {
  constructor({ eventBus, configManager, playerManager, teamManager, scheduler = null, notifier = () => {}, storage = null, mapScanner = null } = {}) {
    this.eventBus = eventBus; this.configManager = configManager; this.playerManager = playerManager; this.teamManager = teamManager;
    this.scheduler = scheduler; this.notifier = notifier; this.storage = storage; this.mapScanner = mapScanner; this.state = MATCH_STATES.LOBBY; this.countdownTask = null; this.victoryTask = null; this.countdownRemaining = 0; this.startedAt = null; this.interruptedState = this.storage?.get?.("tbr:match_state") ?? null;
    if (this.interruptedState?.state === MATCH_STATES.LOBBY) this.interruptedState = null;
  }
  persistState() { this.storage?.set?.("tbr:match_state", { state: this.state, matchId: this.matchId ?? null, startedAt: this.startedAt ?? null }); }
  consumeInterruptedState() { const result = this.interruptedState; this.interruptedState = null; this.storage?.set?.("tbr:match_state", { state: MATCH_STATES.LOBBY }); return result; }
  getState() { return this.state; }
  validateStart() {
    if (this.mapScanner && !this.mapScanner.isReady()) return fail("MAP_SCAN_INCOMPLETE", "map scan is not complete");
    const config = this.configManager.getConfig(); const players = this.playerManager.getStatus().filter(p => p.state === "WAITING");
    if (players.length < config.minPlayers || players.length > config.maxPlayers) return fail(ERROR_CODES.INVALID_ARGUMENT, `players must be ${config.minPlayers}-${config.maxPlayers}`);
    if (config.mode === GAME_MODES.TEAM) {
      if (!config.teamCount) return fail(ERROR_CODES.INVALID_TEAM_COUNT, "teamCount is required");
      const ids = players.map(p => p.id);
      if (this.teamManager.getTeams().length !== config.teamCount || !this.teamManager.hasValidAssignment(ids)) {
        const created = this.teamManager.createTeams(config.teamCount); if (!created.ok) return created;
        const assigned = this.teamManager.randomAssign(ids); if (!assigned.ok) return assigned;
      }
      const result = this.teamManager.validateTeams(ids); if (!result.ok) return result;
    }
    return ok({ players, config });
  }
  start() {
    if (this.state !== MATCH_STATES.LOBBY) return fail(ERROR_CODES.MATCH_ALREADY_RUNNING, "match is already running");
    const validation = this.validateStart(); if (!validation.ok) return validation;
    const countdownSeconds = validation.data.config.countdownSeconds ?? 10;
    this.state = MATCH_STATES.COUNTDOWN; this.persistState(); this.eventBus?.emit(EVENTS.MATCH_COUNTDOWN_STARTED, { seconds: countdownSeconds });
    this.notifier(`${countdownSeconds}秒前`); this.countdownRemaining = countdownSeconds;
    if (this.scheduler?.runInterval) this.countdownTask = this.scheduler.runInterval(() => {
      this.countdownRemaining--;
      if ([3, 2, 1].includes(this.countdownRemaining)) this.notifier(String(this.countdownRemaining));
      if (this.countdownRemaining <= 0) { this.scheduler.clearRun?.(this.countdownTask); this.countdownTask = null; this.beginMatch(); }
    }, 20);
    else if (this.scheduler?.runTimeout) this.countdownTask = this.scheduler.runTimeout(() => this.beginMatch(), 200);
    else this.beginMatch();
    return ok({ state: this.state });
  }
  cancelCountdown() { if (this.state !== MATCH_STATES.COUNTDOWN) return fail(ERROR_CODES.INVALID_ARGUMENT, "countdown is not active"); this.scheduler?.clearRun?.(this.countdownTask); this.countdownTask = null; this.state = MATCH_STATES.LOBBY; this.persistState(); return ok(); }
  beginMatch() {
    if (this.state !== MATCH_STATES.COUNTDOWN) return fail(ERROR_CODES.INVALID_ARGUMENT, "countdown is not active");
    const validation = this.validateStart(); if (!validation.ok) { this.state = MATCH_STATES.LOBBY; return validation; }
    for (const player of validation.data.players) this.playerManager.activatePlayer(player.id);
    if (validation.data.config.mode === GAME_MODES.TEAM) this.teamManager.lockTeams();
    this.matchId = `match_${String(Date.now()).slice(-6)}`; this.startedAt = Date.now(); this.state = MATCH_STATES.IN_PROGRESS; this.persistState();
    this.eventBus?.emit(EVENTS.MATCH_STARTED, { matchId: this.matchId, mode: validation.data.config.mode, teamCount: validation.data.config.mode === GAME_MODES.TEAM ? validation.data.config.teamCount : null });
    this.notifier("GAME START"); return ok({ matchId: this.matchId });
  }
  checkVictory() {
    if (this.state !== MATCH_STATES.IN_PROGRESS) return ok({ winnerType: null, winnerId: null });
    if (this.victoryTask !== null) return ok({ winnerType: null, winnerId: null, pending: true });
    const alive = this.playerManager.getAlivePlayers();
    const config = this.configManager.getConfig();
    if (config.mode === GAME_MODES.TEAM) {
      const aliveTeams = new Set(alive.map(player => this.teamManager.getTeamId(player.id)).filter(Boolean));
      if (aliveTeams.size > 1) return ok({ winnerType: null, winnerId: null });
      return this.deferVictory(aliveTeams.size === 1 ? { winnerType: "team", winnerId: [...aliveTeams][0], reason: "last_team" } : { winnerType: null, winnerId: null, reason: "all_eliminated" });
    }
    if (alive.length > 1) return ok({ winnerType: null, winnerId: null });
    if (alive.length <= 1) return this.deferVictory(alive.length === 1 ? { winnerType: "player", winnerId: alive[0].id, reason: "last_player" } : { winnerType: null, winnerId: null, reason: "all_eliminated" });
  }
  deferVictory(result) { if (!this.scheduler?.runTimeout) return this.endMatch(result); this.victoryTask = this.scheduler.runTimeout(() => { this.victoryTask = null; if (this.state === MATCH_STATES.IN_PROGRESS) this.endMatch(result); }, 60); return ok({ ...result, pending: true }); }
  endMatch({ winnerType = null, winnerId = null, reason = "admin_stop" } = {}) {
    if (this.state === MATCH_STATES.ENDING || this.state === MATCH_STATES.LOBBY) return fail(ERROR_CODES.MATCH_NOT_RUNNING, "match is not active");
    if (this.victoryTask !== null) { this.scheduler?.clearRun?.(this.victoryTask); this.victoryTask = null; }
    this.state = MATCH_STATES.ENDING; const duration = this.startedAt ? Math.floor((Date.now() - this.startedAt) / 1000) : 0;
    this.eventBus?.emit(EVENTS.MATCH_ENDED, { matchId: this.matchId, winnerType, winnerId, reason, duration }); this.notifier("GAME OVER");
    this.teamManager.unlockTeams(); this.state = MATCH_STATES.LOBBY; this.persistState(); return ok({ matchId: this.matchId, winnerType, winnerId, reason, duration });
  }
  stopByAdmin() { return this.endMatch({ reason: "admin_stop" }); }
  eliminateByAdmin(id, reason = "admin") { if (this.state !== MATCH_STATES.IN_PROGRESS) return fail(ERROR_CODES.MATCH_NOT_RUNNING, "match is not active"); const result = this.playerManager.eliminatePlayer(id, { cause: reason, adminElimination: true }); if (result.ok) this.checkVictory(); return result; }
  reviveByAdmin(id) { if (this.state !== MATCH_STATES.IN_PROGRESS) return fail(ERROR_CODES.MATCH_NOT_RUNNING, "match is not active"); const result = this.playerManager.revivePlayer(id, { adminRevival: true }); if (!result.ok) return result; const entity = this.playerManager.getEntity(id); try { entity?.setGameMode?.("adventure"); entity?.teleport?.(entity.location); } catch (_) {} return result; }
}
