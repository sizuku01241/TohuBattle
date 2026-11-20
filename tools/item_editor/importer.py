import re
from pathlib import Path
from .models import Item, LootEntry

ENTRY = re.compile(r"\{\s*id:\s*\"([^\"]+)\"\s*,\s*amount:\s*(\d+)\s*,\s*weight:\s*([0-9.eE+-]+)\s*,\s*rarity:\s*(\d+)\s*\}")


def import_loot(root: Path) -> list[Item]:
    by_id: dict[str, Item] = {}
    loot_root = root / "behavior_pack" / "scripts" / "item" / "loot"
    for pool_dir in ("common", "supply", "ground"):
        directory = loot_root / pool_dir
        if not directory.exists():
            continue
        for path in sorted(directory.glob("rarity*.js")):
            relative = path.relative_to(root).as_posix()
            for index, match in enumerate(ENTRY.finditer(path.read_text(encoding="utf-8"))):
                item_id, amount, weight, rarity = match.groups()
                item = by_id.setdefault(item_id, Item(key=item_id.replace(":", "_"), enabled=True, kind="vanilla", id=item_id, display_name="", tags=[], loot=[]))
                item.loot.append(LootEntry(pool_dir, int(rarity), int(amount), float(weight), relative, index))
    return list(by_id.values())
