import { EVENTS } from "../core/Events.js";
import { fail, ok } from "../core/Constants.js";

export class CombatManager {
  constructor({ eventBus, playerManager, teamManager, configManager, clock = () => Date.now() } = {}) { this.eventBus = eventBus; this.playerManager = playerManager; this.teamManager = teamManager; this.configManager = configManager; this.clock = clock; this.attacks = new Map(); }
  recordAttack(victimId, attackerId, details = {}) { this.attacks.set(victimId, { attackerId, at: this.clock(), ...details }); return ok(); }
  getLastAttacker(victimId, maxAgeMs = 10000) { const attack = this.attacks.get(victimId); return attack && this.clock() - attack.at <= maxAgeMs ? { ...attack } : null; }
  checkFriendlyFire(attackerId, victimId) { if (this.configManager.getConfigValue("friendlyFire")) return ok({ allowed: true }); const a = this.teamManager.getTeamId(attackerId); const v = this.teamManager.getTeamId(victimId); return ok({ allowed: !a || !v || a !== v }); }
  handleDamage({ attackerId = null, victimId, cause = "unknown", amount = 0 } = {}) { if (!victimId || !this.playerManager.isAlive(victimId)) return fail("PLAYER_NOT_ALIVE", "victim is not alive"); if (attackerId && attackerId !== victimId) { const ff = this.checkFriendlyFire(attackerId, victimId); if (!ff.data.allowed) return ok({ cancelled: true }); this.recordAttack(victimId, attackerId); } return ok({ cancelled: false, victimId, cause, amount }); }
  resolveKill(victimId, { cause = "unknown", attackerId = null } = {}) { const last = attackerId ? { attackerId } : this.getLastAttacker(victimId); const resolvedAttackerId = last?.attackerId ?? null; const result = this.playerManager.eliminatePlayer(victimId, { cause, lastAttacker: resolvedAttackerId }); if (!result.ok) return result; if (resolvedAttackerId && resolvedAttackerId !== victimId) this.playerManager.recordKill(resolvedAttackerId); this.eventBus?.emit(EVENTS.COMBAT_KILL, { victimId, attackerId: resolvedAttackerId, cause }); return ok(result.data); }
  getKillCount(playerId) { return this.playerManager.getPlayer(playerId)?.kills ?? 0; }
}
