export class MinecraftWorldAdapter {
  constructor({ world } = {}) { this.world = world; }
  getPlayers() { return this.world?.getPlayers?.() ?? []; }
  broadcast(message) { return this.world?.sendMessage?.(message); }
  getDimension(id = "overworld") { return this.world?.getDimension?.(id); }
}
