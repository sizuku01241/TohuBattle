import { ok } from "../core/Constants.js";
import { ItemStack } from "@minecraft/server";
export class ItemManager {
  constructor({ random = Math.random, storage = null, storageKey = "tbr:spawned_blocks" } = {}) {
    this.random = random;
    this.storage = storage;
    this.storageKey = storageKey;
    this.loot = [];
    this.spawnedEntities = [];
    const persisted = this.storage?.get?.(this.storageKey);
    this.spawnedBlocks = Array.isArray(persisted) ? persisted.map(entry => ({ ...entry, dimension: null })) : [];
  }
  generateLoot(table = []) { return ok(table.filter(item => !item.weight || this.random() <= item.weight).map(item => ({ ...item }))); }
  placeGroundItems(items = []) { this.loot.push(...items.map(item => ({ ...item }))); return ok({ count: items.length }); }
  refillChests() { return ok({ count: 0 }); }
  spawnSupply(position, contents = [], entities = []) { this.spawnedEntities.push(...entities.filter(Boolean)); return ok({ position: { ...position }, contents: [...contents], entityCount: entities.length }); }
  spawnChest(dimension, location, contents = []) {
    try {
      const block = dimension?.getBlock?.(location);
      if (!block) return { ok: false, error: { code: "BLOCK_UNAVAILABLE", message: "supply chest location is unavailable" } };
      const originalTypeId = block.typeId;
      block.setType("minecraft:chest");
      const container = block.getComponent("inventory")?.container;
      if (!container) {
        try { block.setType(originalTypeId); } catch (_) { /* best effort rollback */ }
        return { ok: false, error: { code: "CHEST_INVENTORY_UNAVAILABLE", message: "supply chest inventory is unavailable" } };
      }
      contents.forEach((item, index) => container.setItem(index, new ItemStack(item.id, item.amount ?? 1)));
      this.registerBlock(dimension, location, originalTypeId);
      return ok({ location: { ...location }, itemCount: contents.length });
    } catch (error) {
      return { ok: false, error: { code: "CHEST_SPAWN_FAILED", message: String(error) } };
    }
  }
  registerBlock(dimension, location, originalTypeId = "minecraft:air") {
    if (!dimension || !location) return ok({ registered: false });
    const entry = { dimension, dimensionId: dimension.id ?? "overworld", location: { ...location }, originalTypeId };
    this.spawnedBlocks.push(entry);
    this.storage?.set?.(this.storageKey, this.spawnedBlocks.map(item => ({ dimensionId: item.dimensionId, location: item.location, originalTypeId: item.originalTypeId })));
    return ok({ registered: true });
  }
  recover(dimensionResolver) {
    let restored = 0;
    for (const entry of this.spawnedBlocks) {
      try {
        const dimension = entry.dimension ?? dimensionResolver?.(entry.dimensionId);
        const block = dimension?.getBlock?.(entry.location);
        if (block) { block.setType(entry.originalTypeId || "minecraft:air"); restored += 1; }
      } catch (_) { /* interrupted match block may be unloaded */ }
    }
    this.spawnedBlocks = [];
    this.storage?.set?.(this.storageKey, []);
    return ok({ restored });
  }
  clearSpawned() {
    let entityCount = 0;
    let blockCount = 0;
    for (const entity of this.spawnedEntities) {
      try { entity.remove?.(); entityCount += 1; } catch (_) { /* entity may be invalid */ }
    }
    for (const entry of this.spawnedBlocks) {
      try {
        const block = entry.dimension.getBlock(entry.location);
        if (block) {
          block.setType(entry.originalTypeId || "minecraft:air");
          blockCount += 1;
        }
      } catch (_) { /* block may be unloaded or already removed */ }
    }
    this.spawnedEntities = [];
    this.spawnedBlocks = [];
    this.storage?.set?.(this.storageKey, []);
    this.loot = [];
    return ok({ entityCount, blockCount, count: entityCount + blockCount });
  }
  getItemInfo(itemId) { return this.loot.find(item => item.id === itemId) ?? null; }
  handleItemObtained(itemId) { this.loot = this.loot.filter(item => item.id !== itemId); return ok(); }
}
