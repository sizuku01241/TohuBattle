export class MinecraftScoreboardAdapter {
  constructor({ world } = {}) { this.world = world; }
  update() { return { ok: true, data: {} }; }
}
