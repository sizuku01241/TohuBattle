import { EquipmentSlot } from "@minecraft/server";
import { ok } from "../core/Constants.js";

export class MinecraftInventoryAdapter {
  getContainer(player) { try { return player?.getComponent?.("inventory")?.container ?? null; } catch (_) { return null; } }
  getEquippable(player) { try { return player?.getComponent?.("minecraft:equippable") ?? player?.getComponent?.("equippable") ?? null; } catch (_) { return null; } }
  getEquipmentSlots() { return [EquipmentSlot.Head, EquipmentSlot.Chest, EquipmentSlot.Legs, EquipmentSlot.Feet, EquipmentSlot.Offhand, EquipmentSlot.Mainhand].filter(Boolean); }
  snapshot(player) {
    const container = this.getContainer(player); if (!container) return { ok: false, error: { code: "INVENTORY_UNAVAILABLE", message: "inventory is unavailable" } };
    const items = [];
    for (let slot = 0; slot < container.size; slot++) { try { const item = container.getItem(slot); if (item) items.push({ slot, typeId: item.typeId, amount: item.amount }); } catch (_) {} }
    const equipment = this.getEquippable(player); for (const slot of this.getEquipmentSlots()) { try { const item = equipment?.getEquipment(slot); if (item) items.push({ slot: String(slot), typeId: item.typeId, amount: item.amount }); } catch (_) {} }
    return ok({ items });
  }
  transfer(player, recipients = []) {
    const source = this.getContainer(player); if (!source) return { ok: false, error: { code: "INVENTORY_UNAVAILABLE", message: "source inventory is unavailable" } };
    const containers = recipients.map(recipient => this.getContainer(recipient)).filter(Boolean); const equipment = this.getEquippable(player); let transferred = 0; let dropped = 0;
    const move = item => {
      if (!item) return true;
      if (!containers.length) { try { player.dimension.spawnItem(item, player.location); dropped += item.amount; return true; } catch (_) { return false; } }
      let remainder = item; for (const target of containers) { if (!remainder) break; try { remainder = target.addItem(remainder); } catch (_) {} }
      if (!remainder) { transferred += item.amount; return true; }
      const moved = item.amount - remainder.amount; transferred += moved;
      if (moved > 0) { try { player.dimension.spawnItem(remainder, player.location); dropped += remainder.amount; return true; } catch (_) { return false; } }
      try { player.dimension.spawnItem(remainder, player.location); dropped += remainder.amount; return true; } catch (_) { return false; }
    };
    for (let slot = 0; slot < source.size; slot++) {
      let item; try { item = source.getItem(slot); } catch (_) { item = undefined; }
      if (!item) continue; const before = item.amount; const moved = move(item);
      try { if (moved) source.setItem(slot, undefined); else if (transferred > 0 && item.amount < before) source.setItem(slot, item); } catch (_) {}
    }
    for (const slot of this.getEquipmentSlots()) {
      let item; try { item = equipment?.getEquipment(slot); } catch (_) { item = undefined; }
      if (!item) continue; if (move(item)) { try { equipment.setEquipment(slot, undefined); } catch (_) {} }
    }
    return ok({ status: !containers.length ? "no_recipient" : (dropped > 0 ? "partial" : "success"), transferred, dropped });
  }
}
