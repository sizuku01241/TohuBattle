import { CommandParser } from "./CommandParser.js";
import { CommandValidator } from "./CommandValidator.js";

export class AdminManager {
  constructor({ matchManager, configManager, teamManager, logManager, permission = () => true } = {}) {
    this.matchManager = matchManager; this.configManager = configManager; this.teamManager = teamManager; this.logManager = logManager;
    this.permission = permission; this.parser = new CommandParser(); this.validator = new CommandValidator();
  }
  executeCommand(source, input) {
    if (!this.permission(source)) { this.logManager?.record("ADMIN_COMMAND", { result: "permission_denied" }); return { ok: false, error: { code: "PERMISSION_DENIED", message: "operator permission required" } }; }
    const parsed = this.parser.parse(input); const valid = this.validator.validate(parsed); if (!valid.ok) return valid;
    let result;
    switch (parsed.command) {
      case "start": result = this.matchManager.start(); break;
      case "stop": result = this.matchManager.stopByAdmin(); break;
      case "config": result = { ok: true, data: this.configManager.getConfig() }; break;
      case "team": if (parsed.args[0] === "random") result = { ok: true, data: this.teamManager.getTeams() }; else result = { ok: false, error: { code: "INVALID_ARGUMENT", message: "use /tbr team random" } }; break;
      case "help": result = { ok: true, data: { usage: "/tbr <start|stop|team random|config|help>" } }; break;
      default: result = { ok: false, error: { code: "INVALID_COMMAND", message: `unknown command: ${parsed.command}` } };
    }
    this.logManager?.record("ADMIN_COMMAND", { command: input, result: result.ok ? "success" : "failed" }); return result;
  }
}
