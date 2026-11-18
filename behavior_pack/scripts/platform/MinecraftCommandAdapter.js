export class MinecraftCommandAdapter {
  constructor({ registry = null } = {}) { this.registry = registry; }
  register(definition, handler) { return this.registry?.register?.(definition, handler); }
}
