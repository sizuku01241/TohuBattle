export class MinecraftEventAdapter {
  constructor({ world, system } = {}) { this.world = world; this.system = system; }
  subscribe(signal, handler) { return signal?.subscribe?.(handler) ?? (() => {}); }
  unsubscribe(signal, handler) { return signal?.unsubscribe?.(handler); }
}
