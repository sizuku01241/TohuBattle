import json
from ..models import Item


def generate_bp_item(item: Item) -> str:
    custom = item.custom
    if item.kind != "custom" or not custom:
        return ""
    components = {
        "minecraft:icon": f"tbr_{item.key}",
        "minecraft:max_stack_size": custom.max_stack_size,
    }
    if custom.use:
        components["minecraft:use_modifiers"] = {"use_duration": custom.use.get("duration_sec", 1.6), "movement_modifier": custom.use.get("movement_modifier", 0.35)}
        components["minecraft:use_animation"] = custom.use.get("animation", "eat")
    if custom.food:
        components["minecraft:food"] = custom.food
    if custom.cooldown:
        components["minecraft:cooldown"] = custom.cooldown
    if custom.on_use:
        components["tbr:ability"] = {}
        if custom.on_use.get("trigger") == "hold" and custom.use is None:
            components["minecraft:use_modifiers"] = {"use_duration": 1.0, "movement_modifier": 0.35}
    payload = {"format_version": "1.21.90", "minecraft:item": {"description": {"identifier": item.id, "menu_category": {"category": "items"}}, "components": components}}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
