"""GUIフォーム値をItemへ変換する副作用の少ないロジック。"""

from __future__ import annotations

import copy

from .models import CustomSpec, Item, LootEntry


def apply_form_to_item(
    item: Item,
    values: dict[str, str | bool],
    loot_rows: list[LootEntry],
    tags: list[str],
    icon: str | None = None,
) -> Item:
    """フォーム値から新しいItemを作る。入力Itemとloot行は変更しない。"""
    result = copy.deepcopy(item)
    result.key = str(values.get("key", "")).strip()
    result.id = str(values.get("id", "")).strip()
    result.display_name = str(values.get("name", ""))
    result.kind = str(values.get("kind", result.kind))
    result.enabled = bool(values.get("enabled", result.enabled))
    result.tags = list(tags)
    result.loot = copy.deepcopy(loot_rows)
    if result.kind != "custom":
        result.custom = None
        return result

    custom = result.custom or CustomSpec()
    if icon:
        custom.icon = icon
    food_enabled = bool(values.get("food_enabled", False))
    custom.use = {"duration_sec": float(values.get("duration", 1.6) or 1.6), "movement_modifier": float(values.get("movement", 0.35) or 0.35), "animation": str(values.get("animation", "eat"))} if food_enabled else None
    custom.food = {"nutrition": int(values.get("nutrition", 0) or 0), "saturation_modifier": float(values.get("saturation", 0) or 0), "can_always_eat": bool(values.get("always_eat", False))} if food_enabled else None
    if bool(values.get("ability_enabled", False)):
        custom.on_use = {"trigger": str(values.get("trigger", "tap")), "target": {"type": str(values.get("target_type", "self")), "radius": float(values.get("radius", 0) or 0), "angle": float(values.get("angle", 90) or 90), "width": float(values.get("width", 1) or 1)}, "effects": [{"kind": str(values.get("effect_kind", "heal") or "heal"), "id": str(values.get("effect_id", "")), "duration_sec": float(values.get("effect_duration", 1) or 1), "level": int(values.get("effect_level", 1) or 1), "amount": float(values.get("heal", 0) or 0)}]}
    else:
        custom.on_use = None
    result.custom = custom
    return result
