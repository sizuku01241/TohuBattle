from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class LootEntry:
    pool: str
    rarity: int
    amount: int
    weight: float
    source_file: str = field(default="", repr=False, compare=False)
    source_index: int = field(default=-1, repr=False, compare=False)


@dataclass
class CustomSpec:
    icon: str = ""
    max_stack_size: int = 64
    use: dict[str, Any] | None = None
    food: dict[str, Any] | None = None
    cooldown: dict[str, Any] | None = None
    on_use: dict[str, Any] | None = None
    equipment: dict[str, Any] | None = None


@dataclass
class Item:
    key: str
    enabled: bool
    kind: str
    id: str
    display_name: str
    tags: list[str] = field(default_factory=list)
    loot: list[LootEntry] = field(default_factory=list)
    custom: CustomSpec | None = None


def item_from_dict(raw: dict[str, Any]) -> Item:
    custom = raw.get("custom")
    custom_spec = None
    if custom:
        custom_spec = CustomSpec(
            icon=str(custom.get("icon", "")), max_stack_size=int(custom.get("max_stack_size", 64)),
            use=custom.get("use"), food=custom.get("food"), cooldown=custom.get("cooldown"),
            on_use=custom.get("on_use"), equipment=custom.get("equipment"),
        )
    return Item(
        key=str(raw.get("key", "")), enabled=bool(raw.get("enabled", True)),
        kind=str(raw.get("kind", "vanilla")), id=str(raw.get("id", "")),
        display_name=str(raw.get("display_name", "")), tags=list(raw.get("tags", [])),
        loot=[LootEntry(pool=str(x["pool"]), rarity=int(x["rarity"]), amount=int(x["amount"]), weight=float(x["weight"])) for x in raw.get("loot", [])],
        custom=custom_spec,
    )


def item_to_dict(item: Item) -> dict[str, Any]:
    raw = asdict(item)
    raw["loot"] = [{"pool": entry.pool, "rarity": entry.rarity, "amount": entry.amount, "weight": entry.weight} for entry in item.loot]
    return raw
