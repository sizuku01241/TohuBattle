export class UIManager {
  constructor({ playerAdapter = null, scoreboardAdapter = null } = {}) { this.playerAdapter = playerAdapter; this.scoreboardAdapter = scoreboardAdapter; }
  initialize() { return { ok: true, data: {} }; }
  refreshPlayer(playerId, view = {}) { return this.playerAdapter?.show?.(playerId, view) ?? { ok: true, data: {} }; }
  refreshAll(players = [], view = {}) { players.forEach(player => this.refreshPlayer(player.id, view)); this.scoreboardAdapter?.update?.(players, view); return { ok: true, data: { count: players.length } }; }
  handleEvent(event) { return this.refreshAll(event?.players ?? [], event); }
  dispose() { return { ok: true, data: {} }; }
}
