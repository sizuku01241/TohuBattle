export class PresetStorage {
  constructor({ adapter = null, prefix = "tbr:preset:", indexKey = "tbr:preset:index" } = {}) { this.adapter = adapter; this.prefix = prefix; this.indexKey = indexKey; this.memory = new Map(); }
  list() { return this.adapter?.get?.(this.indexKey) ?? [...this.memory.keys()]; }
  save(name, value) {
    this.memory.set(name, { ...value });
    const names = [...new Set([...this.list(), name])];
    const saved = this.adapter?.set?.(`${this.prefix}${name}`, value) ?? true;
    if (saved && this.adapter) this.adapter.set(this.indexKey, names);
    return saved;
  }
  load(name) { return this.adapter?.get?.(`${this.prefix}${name}`) ?? this.memory.get(name) ?? null; }
  delete(name) {
    this.memory.delete(name);
    const names = this.list().filter(item => item !== name);
    const deleted = this.adapter?.delete?.(`${this.prefix}${name}`) ?? true;
    if (deleted && this.adapter) this.adapter.set(this.indexKey, names);
    return deleted;
  }
}
