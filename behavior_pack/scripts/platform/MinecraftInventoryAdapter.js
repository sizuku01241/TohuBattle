import { EquipmentSlot } from "@minecraft/server";
import { ok } from "../core/Constants.js";

export class MinecraftInventoryAdapter {
  getContainer(player) { try { return player?.getComponent?.("inventory")?.container ?? null; } catch (_) { return null; } }
  getEquippable(player) { try { return player?.getComponent?.("minecraft:equippable") ?? player?.getComponent?.("equippable") ?? null; } catch (_) { return null; } }
  // Mainhand is already represented by the hotbar inventory slot. Reading it
  // from equippable as well would transfer the same stack twice.
  getEquipmentSlots() { return [EquipmentSlot.Head, EquipmentSlot.Chest, EquipmentSlot.Legs, EquipmentSlot.Feet, EquipmentSlot.Offhand].filter(Boolean); }
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
      if (!item) return { remainder: undefined, moved: 0, dropped: 0, success: true };
      if (!containers.length) { try { player.dimension.spawnItem(item, player.location); dropped += item.amount; return { remainder: undefined, moved: 0, dropped: item.amount, success: true }; } catch (_) { return { remainder: item, moved: 0, dropped: 0, success: false }; } }
      let remainder = item; for (const target of containers) { if (!remainder) break; try { remainder = target.addItem(remainder); } catch (_) {} }
      const moved = item.amount - (remainder?.amount ?? 0); transferred += moved;
      if (!remainder) return { remainder: undefined, moved, dropped: 0, success: true };
      try { player.dimension.spawnItem(remainder, player.location); dropped += remainder.amount; return { remainder: undefined, moved, dropped: remainder.amount, success: true }; } catch (_) { return { remainder, moved, dropped: 0, success: false }; }
    };
    for (let slot = 0; slot < source.size; slot++) {
      let item; try { item = source.getItem(slot); } catch (_) { item = undefined; }
      if (!item) continue; const moved = move(item);
      try { source.setItem(slot, moved.success ? moved.remainder : item); } catch (_) {}
    }
    for (const slot of this.getEquipmentSlots()) {
      let item; try { item = equipment?.getEquipment(slot); } catch (_) { item = undefined; }
      if (!item) continue; const moved = move(item); try { equipment.setEquipment(slot, moved.success ? moved.remainder : item); } catch (_) {}
    }
    return ok({ status: !containers.length ? "no_recipient" : (dropped > 0 ? "partial" : "success"), transferred, dropped });
  }
}
