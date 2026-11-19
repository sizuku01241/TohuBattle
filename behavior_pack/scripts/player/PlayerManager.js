import { ERROR_CODES, PLAYER_STATES, fail, ok } from "../core/Constants.js";
import { EVENTS } from "../core/Events.js";

export class PlayerManager {
  constructor({ eventBus } = {}) { this.eventBus = eventBus; this.players = new Map(); this.eliminationSequence = 0; }
  registerPlayer(player) { const id = player?.id; if (!id) return fail(ERROR_CODES.INVALID_ARGUMENT, "player.id is required"); if (this.players.has(id)) return fail(ERROR_CODES.PLAYER_ALREADY_REGISTERED, "player already registered"); const record = { id, name: player.name ?? id, entity: player, state: PLAYER_STATES.WAITING, kills: 0, assists: 0, damage: 0, survivalSeconds: 0, joinedAt: Date.now() }; this.players.set(id, record); this.eventBus?.emit(EVENTS.PLAYER_JOINED, { playerId: id, name: record.name }); return ok({ ...record, entity: undefined }); }
  activatePlayer(id) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); if (p.state !== PLAYER_STATES.WAITING) return fail(ERROR_CODES.INVALID_ARGUMENT, "player is not waiting"); p.state = PLAYER_STATES.ALIVE; return ok({ ...p, entity: undefined }); }
  eliminatePlayer(id, details = {}) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); if (p.state !== PLAYER_STATES.ALIVE) return fail(ERROR_CODES.PLAYER_NOT_ALIVE, "player is not alive"); p.state = PLAYER_STATES.ELIMINATED; p.eliminatedAt = Date.now(); p.eliminationOrder = ++this.eliminationSequence; Object.assign(p, details); this.eventBus?.emit(EVENTS.PLAYER_ELIMINATED, { playerId: id, eliminationOrder: p.eliminationOrder, ...details }); return ok({ ...p, entity: undefined }); }
  revivePlayer(id, details = {}) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); if (![PLAYER_STATES.ELIMINATED, PLAYER_STATES.SPECTATOR].includes(p.state)) return fail(ERROR_CODES.INVALID_ARGUMENT, "player is not eliminated"); p.state = PLAYER_STATES.ALIVE; p.revivedAt = Date.now(); Object.assign(p, details); return ok({ ...p, entity: undefined }); }
  disconnectPlayer(id) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); const previousState = p.state; if (p.state === PLAYER_STATES.ALIVE || p.state === PLAYER_STATES.WAITING) p.state = PLAYER_STATES.DISCONNECTED; p.entity = null; this.eventBus?.emit(EVENTS.PLAYER_DISCONNECTED, { playerId: id, previousState }); return ok({ ...p, previousState, entity: undefined }); }
  setSpectator(id) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); p.state = PLAYER_STATES.SPECTATOR; return ok({ ...p, entity: undefined }); }
  recordKill(id) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); p.kills = (p.kills ?? 0) + 1; return ok({ playerId: id, kills: p.kills }); }
  recordAssist(id) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); p.assists = (p.assists ?? 0) + 1; return ok({ playerId: id, assists: p.assists }); }
  recordDamage(id, amount) { const p = this.players.get(id); if (!p) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); p.damage = (p.damage ?? 0) + Math.max(0, Number(amount) || 0); return ok({ playerId: id, damage: p.damage }); }
  isAlive(id) { return this.players.get(id)?.state === PLAYER_STATES.ALIVE; }
  getPlayer(id) { const p = this.players.get(id); return p ? { ...p, entity: undefined } : null; }
  attachEntity(id, entity) { const player = this.players.get(id); if (!player) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); player.entity = entity; return ok(); }
  returnToLobby(id) { const player = this.players.get(id); if (!player) return fail(ERROR_CODES.PLAYER_NOT_FOUND, "player not found"); if (player.state === PLAYER_STATES.DISCONNECTED || player.state === PLAYER_STATES.SPECTATOR || player.state === PLAYER_STATES.ELIMINATED) player.state = PLAYER_STATES.WAITING; return ok(); }
  getEntity(id) { return this.players.get(id)?.entity ?? null; }
  getAlivePlayers() { return [...this.players.values()].filter(p => p.state === PLAYER_STATES.ALIVE).map(p => ({ ...p, entity: undefined })); }
  getStatus() { return [...this.players.values()].map(p => ({ ...p, entity: undefined })); }
  resetForLobby() { for (const player of this.players.values()) { if (player.state !== PLAYER_STATES.DISCONNECTED) player.state = PLAYER_STATES.WAITING; player.kills = 0; player.assists = 0; player.damage = 0; player.survivalSeconds = 0; delete player.eliminatedAt; delete player.eliminationOrder; delete player.cause; delete player.lastAttacker; } this.eliminationSequence = 0; return ok(); }
  clear() { this.players.clear(); }
}
