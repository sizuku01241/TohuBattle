export class DebugManager {
  constructor({ mapManager, zoneManager, playerManager } = {}) { this.mapManager = mapManager; this.zoneManager = zoneManager; this.playerManager = playerManager; }
  getZoneStatus() { return this.zoneManager?.getZoneStatus?.() ?? null; }
  getPlayerStatus() { return this.playerManager?.getStatus?.() ?? []; }
  getSystemStatus() { return { map: this.mapManager?.getMap?.() ?? null, zone: this.getZoneStatus(), players: this.getPlayerStatus() }; }
}
