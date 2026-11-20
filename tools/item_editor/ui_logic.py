"""副作用を持たない、GUIからもテストできる編集ロジック。"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .models import CustomSpec, Item, LootEntry


@dataclass(frozen=True)
class SelectionChangeResult:
    """UI非依存の一覧選択切替結果。"""
    selected_index: int | None
    changed: bool
    write_attempted: bool
    error: ValueError | None = None


def change_selection(current_index: int | None, target_index: int, write_back) -> SelectionChangeResult:
    """同じ選択は無視し、異なる選択だけ書き戻し後に切り替える。"""
    if current_index == target_index:
        return SelectionChangeResult(current_index, False, False)
    try:
        write_back()
    except ValueError as error:
        return SelectionChangeResult(current_index, False, True, error)
    return SelectionChangeResult(target_index, True, True)


def suggest_key(item_id: str, existing: list[Item] | None = None) -> str:
    """アイテムIDからkeyを提案し、既存keyと衝突しない名前を返す。"""
    base = item_id.split(":", 1)[-1].lower()
    base = re.sub(r"[^a-z0-9_]+", "_", base).strip("_") or "new_item"
    used = {item.key for item in (existing or [])}
    if base not in used:
        return base
    number = 2
    while f"{base}_copy{number}" in used:
        number += 1
    return f"{base}_copy{number}"


def template_item(template: str, existing: list[Item] | None = None) -> Item:
    """安全な初期値を持つCustomアイテムを生成する。"""
    key = suggest_key("tbr:new_item", existing)
    loot = [LootEntry("common", 1, 1, 0.5)]
    custom = CustomSpec()
    tags: list[str] = []
    if template == "food":
        tags = ["food"]
        custom.food = {"nutrition": 4, "saturation_modifier": 0.6, "can_always_eat": False}
        custom.use = {"duration_sec": 1.6, "movement_modifier": 0.35, "animation": "eat"}
    elif template == "healing":
        tags = ["healing"]
        custom.food = {"nutrition": 0, "saturation_modifier": 0, "can_always_eat": True}
        custom.use = {"duration_sec": 2.0, "movement_modifier": 0.35, "animation": "eat"}
        custom.on_use = {"trigger": "tap", "target": {"type": "self"}, "effects": [{"kind": "heal", "amount": 4, "duration_sec": 1, "level": 1}]}
    elif template == "ability":
        tags = ["special"]
        custom.on_use = {"trigger": "tap", "target": {"type": "cone", "radius": 4, "angle": 90, "width": 1}, "effects": [{"kind": "potion_effect", "id": "speed", "duration_sec": 5, "level": 1}]}
    return Item(key, True, "custom", f"tbr:{key}", "", tags, loot, custom)


@dataclass(frozen=True)
class LootMatrixCell:
    pool: str
    rarity: int
    count: int
    weight_total: float


def loot_matrix(items: list[Item]) -> list[LootMatrixCell]:
    """pool×レア度の件数と出現確率合計を決定的に集計する。"""
    result = []
    for pool in ("common", "supply", "ground"):
        for rarity in range(1, 8):
            rows = [entry for item in items for entry in item.loot if entry.pool == pool and entry.rarity == rarity]
            result.append(LootMatrixCell(pool, rarity, len(rows), sum(entry.weight for entry in rows)))
    return result


def history_entries(root: Path) -> list[dict[str, object]]:
    base = root / "tools" / "items" / "history"
    result = []
    for path in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True) if base.exists() else []:
        files = len([p for p in path.rglob("*") if p.is_file() and p.name != "manifest.json"])
        snapshot = path / "tools" / "items" / "items.json"
        if not snapshot.exists():
            snapshot = path / "items.json"
        item_keys = []
        if snapshot.exists():
            try:
                item_keys = [str(item.get("key", "")) for item in json.loads(snapshot.read_text(encoding="utf-8")).get("items", [])]
            except (OSError, json.JSONDecodeError, AttributeError):
                item_keys = []
        current_path = root / "tools" / "items" / "items.json"
        current_keys = []
        if current_path.exists():
            try:
                current_keys = [str(item.get("key", "")) for item in json.loads(current_path.read_text(encoding="utf-8")).get("items", [])]
            except (OSError, json.JSONDecodeError, AttributeError):
                current_keys = []
        result.append({
            "name": path.name,
            "path": path,
            "files": files,
            "items": len(item_keys),
            "added": [key for key in item_keys if key not in current_keys][:5],
            "removed": [key for key in current_keys if key not in item_keys][:5],
        })
    return result


def restore_history(root: Path, history_path: Path) -> list[str]:
    """履歴にある変更前ファイルをプロジェクトへ戻す。呼び出し側で現在状態を先に保存する。"""
    history_path = history_path.resolve()
    history_root = (root / "tools" / "items" / "history").resolve()
    history_path.relative_to(history_root)
    restored = []
    for source in history_path.rglob("*"):
        if not source.is_file() or source.name == "manifest.json":
            continue
        relative = source.relative_to(history_path)
        if relative == Path("items.json"):
            target = root / "tools" / "items" / "items.json"
        else:
            target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        restored.append(target.relative_to(root).as_posix())
    return restored
