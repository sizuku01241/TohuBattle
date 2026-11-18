export class MinecraftPlayerAdapter {
  showActionBar(player, text) { return player?.onScreenDisplay?.setActionBar?.(text); }
  showTitle(player, title, subtitle = "") { return player?.onScreenDisplay?.setTitle?.(title, { subtitle }); }
  sendMessage(player, message) { return player?.sendMessage?.(message); }
  setSpectator(player) { try { player.setGameMode?.("spectator"); return true; } catch (_) { return false; } }
}
