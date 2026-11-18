export class CommandValidator {
  validate(parsed) {
    if (!parsed?.command) return { ok: false, error: { code: "INVALID_COMMAND", message: "command is required" } };
    return { ok: true, data: parsed };
  }
}
