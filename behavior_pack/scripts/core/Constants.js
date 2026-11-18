export const MATCH_STATES = Object.freeze({ LOBBY: "LOBBY", COUNTDOWN: "COUNTDOWN", IN_PROGRESS: "IN_PROGRESS", ENDING: "ENDING" });
export const PLAYER_STATES = Object.freeze({ WAITING: "WAITING", ALIVE: "ALIVE", ELIMINATED: "ELIMINATED", DISCONNECTED: "DISCONNECTED", SPECTATOR: "SPECTATOR" });
export const GAME_MODES = Object.freeze({ SOLO: "solo", TEAM: "team" });
export const ERROR_CODES = Object.freeze({
  INVALID_ARGUMENT: "INVALID_ARGUMENT", MATCH_ALREADY_RUNNING: "MATCH_ALREADY_RUNNING", MATCH_NOT_RUNNING: "MATCH_NOT_RUNNING",
  PLAYER_NOT_FOUND: "PLAYER_NOT_FOUND", PLAYER_NOT_ALIVE: "PLAYER_NOT_ALIVE", PLAYER_ALREADY_REGISTERED: "PLAYER_ALREADY_REGISTERED",
  TEAM_NOT_FOUND: "TEAM_NOT_FOUND", INVALID_TEAM_COUNT: "INVALID_TEAM_COUNT", CONFIG_VALIDATION_FAILED: "CONFIG_VALIDATION_FAILED"
});
export const DEFAULT_CONFIG = Object.freeze({
  mode: GAME_MODES.SOLO, teamCount: null, mapName: "default", countdownSeconds: 10,
  friendlyFire: false, minPlayers: 1, maxPlayers: 32,
  zone: { warningSeconds: 150, shrinkSeconds: 60, minimumRadius: 6, damageAmount: 1 },
  assistWindowSeconds: 10, assistDamage: 5
});

export const ok = (data = {}) => ({ ok: true, data });
export const fail = (code, message, details = undefined) => ({ ok: false, error: { code, message, ...(details === undefined ? {} : { details }) } });
