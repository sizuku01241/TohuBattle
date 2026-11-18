export class CommandParser {
  parse(input = "") {
    const tokens = String(input).trim().split(/\s+/).filter(Boolean);
    if (tokens[0]?.toLowerCase() === "tbr") tokens.shift();
    return { command: (tokens.shift() ?? "help").toLowerCase(), args: tokens };
  }
}
