"""GUIフォーム値をItemへ変換する副作用の少ないロジック。"""

from __future__ import annotations

import copy

from .models import CustomSpec, Item, LootEntry


def parse_float(value, label, default):
    """空欄だけ既定値にし、それ以外は厳密に数値化する。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label}には数値を入力してください: {value}") from error


def parse_int(value, label, default):
    """空欄だけ既定値にし、それ以外は整数として数値化する。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return int(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label}には整数を入力してください: {value}") from error
    if not parsed.is_integer():
        raise ValueError(f"{label}には整数を入力してください: {value}")
    return int(parsed)


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
    custom.use = {"duration_sec": parse_float(values.get("duration"), "使用時間", 1.6), "movement_modifier": parse_float(values.get("movement"), "移動速度係数", 0.35), "animation": str(values.get("animation", "eat"))} if food_enabled else None
    custom.food = {"nutrition": parse_int(values.get("nutrition"), "空腹回復", 0), "saturation_modifier": parse_float(values.get("saturation"), "満腹度", 0), "can_always_eat": bool(values.get("always_eat", False))} if food_enabled else None
    if bool(values.get("ability_enabled", False)):
        custom.on_use = {"trigger": str(values.get("trigger", "tap")), "target": {"type": str(values.get("target_type", "self")), "radius": parse_float(values.get("radius"), "半径", 0), "angle": parse_float(values.get("angle"), "角度", 90), "width": parse_float(values.get("width"), "幅", 1)}, "effects": [{"kind": str(values.get("effect_kind", "heal") or "heal"), "id": str(values.get("effect_id", "")), "duration_sec": parse_float(values.get("effect_duration"), "効果時間", 1), "level": parse_int(values.get("effect_level"), "効果レベル", 1), "amount": parse_float(values.get("heal"), "回復量", 0)}]}
    else:
        custom.on_use = None
    result.custom = custom
    return result
