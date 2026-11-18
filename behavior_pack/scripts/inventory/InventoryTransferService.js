import { ok } from "../core/Constants.js";
export class InventoryTransferService {
  constructor({ inventoryAdapter } = {}) { this.inventoryAdapter = inventoryAdapter; }
  transferOnDisconnect(player, recipients = []) { if (!this.inventoryAdapter?.transfer) return ok({ status: "not_applicable", transferred: 0 }); return this.inventoryAdapter.transfer(player, recipients); }
}
