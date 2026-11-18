export class ErrorHandler {
  constructor({ logger = console } = {}) { this.logger = logger; }
  handle(error, context = {}) {
    try { this.logger.error(`[TBR] ${context.scope ?? "error"}: ${error?.stack ?? error}`); } catch (_) {}
    return { error, context };
  }
}
