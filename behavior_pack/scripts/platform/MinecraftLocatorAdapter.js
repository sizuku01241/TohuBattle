import { PlayerWaypoint, WaypointTexture } from "@minecraft/server";

export class MinecraftLocatorAdapter {
  constructor() { this.waypoints = new Map(); }
  clear() { for (const waypoint of this.waypoints.values()) { try { waypoint.remove(); } catch (_) {} } this.waypoints.clear(); return { ok: true }; }
  update(players = [], teamManager = null) {
    this.clear();
    const textureSelector = { textureBoundsList: [{ lowerBound: 0, texture: WaypointTexture.Circle }] };
    let added = 0;
    for (const viewer of players) {
      const viewerTeam = teamManager?.getTeamId?.(viewer.id); if (!viewerTeam || viewer.state !== "ALIVE") continue;
      for (const target of players) {
        if (target.id === viewer.id || target.state !== "ALIVE" || teamManager.getTeamId(target.id) !== viewerTeam || !target.entity) continue;
        try {
          const waypoint = new PlayerWaypoint(target.entity, textureSelector, { showHidden: false, showSpectator: false, showSpectatorToSpectator: false }, { red: 0.2, green: 0.8, blue: 0.2 });
          viewer.entity?.locatorBar?.addWaypoint?.(waypoint); this.waypoints.set(`${viewer.id}:${target.id}`, waypoint); added += 1;
          if (this.waypoints.size >= (viewer.entity?.locatorBar?.maxCount ?? 128)) break;
        } catch (_) { /* unsupported or full locator bar */ }
      }
    }
    return { ok: true, data: { added, max: players[0]?.entity?.locatorBar?.maxCount ?? null } };
  }
}
