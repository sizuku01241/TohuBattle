import { ERROR_CODES, fail, ok } from "../core/Constants.js";
import { EVENTS } from "../core/Events.js";

export class TeamManager {
  constructor({ eventBus } = {}) { this.eventBus = eventBus; this.teams = new Map(); this.playerToTeam = new Map(); this.locked = false; }
  createTeams(count) { if (!Number.isInteger(count) || count < 2) return fail(ERROR_CODES.INVALID_TEAM_COUNT, "team count must be at least 2"); this.teams.clear(); this.playerToTeam.clear(); for (let i = 1; i <= count; i++) { const id = `team_${String(i).padStart(2, "0")}`; this.teams.set(id, { id, members: [] }); } return ok(this.getTeams()); }
  assignPlayer(playerId, teamId) { if (this.locked) return fail("TEAM_ALREADY_LOCKED", "teams are locked"); const team = this.teams.get(teamId); if (!team) return fail(ERROR_CODES.TEAM_NOT_FOUND, "team not found"); this.removePlayer(playerId); team.members.push(playerId); this.playerToTeam.set(playerId, teamId); this.eventBus?.emit(EVENTS.TEAM_CHANGED, { playerId, teamId }); return ok({ playerId, teamId }); }
  removePlayer(playerId) { const old = this.playerToTeam.get(playerId); if (!old) return ok(); const team = this.teams.get(old); if (team) team.members = team.members.filter(id => id !== playerId); this.playerToTeam.delete(playerId); return ok(); }
  getTeamId(playerId) { return this.playerToTeam.get(playerId) ?? null; }
  getTeam(teamId) { const t = this.teams.get(teamId); return t ? { id: t.id, members: [...t.members] } : null; }
  getMembers(teamId) { return this.teams.get(teamId)?.members.slice() ?? []; }
  getTeams() { return [...this.teams.values()].map(t => ({ id: t.id, members: [...t.members] })); }
  validateTeams(playerIds) {
    if (!this.teams.size || playerIds.length % this.teams.size !== 0) return fail(ERROR_CODES.INVALID_TEAM_COUNT, "players cannot be divided evenly");
    const size = playerIds.length / this.teams.size; if (size < 2) return fail(ERROR_CODES.INVALID_TEAM_COUNT, "each team needs at least 2 players");
    const expected = new Set(playerIds); const assigned = playerIds.filter(id => expected.has(id) && this.playerToTeam.has(id));
    if (assigned.length !== playerIds.length || new Set(assigned).size !== playerIds.length) return fail("TEAM_ASSIGNMENT_INCOMPLETE", "all players must be assigned to exactly one team");
    if ([...this.teams.values()].some(team => team.members.filter(id => expected.has(id)).length !== size)) return fail("TEAM_SIZE_MISMATCH", "team sizes are not equal");
    return ok({ teamSize: size });
  }
  hasValidAssignment(playerIds) { return this.validateTeams(playerIds).ok; }
  randomAssign(playerIds, random = Math.random) {
    if (this.locked) return fail("TEAM_ALREADY_LOCKED", "チームはロックされています");
    if (!this.teams.size || playerIds.length % this.teams.size !== 0 || playerIds.length / this.teams.size < 2) return fail(ERROR_CODES.INVALID_TEAM_COUNT, "players cannot be divided into equal teams of at least 2");
    const shuffled = [...playerIds];
    for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]; }
    const teams = [...this.teams.keys()];
    shuffled.forEach((playerId, index) => this.assignPlayer(playerId, teams[index % teams.length]));
    return ok(this.getTeams());
  }
  lockTeams() { this.locked = true; return ok(); }
  unlockTeams() { this.locked = false; return ok(); }
}
