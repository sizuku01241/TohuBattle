export class ChatUI {
  constructor({ adapter } = {}) { this.adapter = adapter; }
  render(player, message) { return this.adapter?.sendMessage?.(player, message); }
}
