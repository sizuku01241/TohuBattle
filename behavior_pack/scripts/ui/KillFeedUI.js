export class KillFeedUI { format({ attacker = "Environment", victim, distance = "—" }) { return `[KILL] ${attacker} »» ${victim} (${distance})`; } }
