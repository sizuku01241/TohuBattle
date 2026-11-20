import json
from ..models import Item


def generate_texture_data(items: list[Item], existing: str | None = None) -> str:
    payload = json.loads(existing) if existing else {"resource_pack_name": "Tohu Battle Royale", "texture_name": "atlas.items", "texture_data": {}}
    texture_data = payload.setdefault("texture_data", {})
    for item in items:
        if item.enabled and item.kind == "custom" and item.custom:
            texture_data[f"tbr_{item.key}"] = {"textures": f"textures/items/tbr_{item.key}"}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def generate_lang(items: list[Item], existing: str | None = None) -> str:
    lines = (existing or "").splitlines(); positions = {line.split("=", 1)[0]: index for index, line in enumerate(lines) if "=" in line}
    for item in items:
        if item.enabled and item.kind == "custom" and item.display_name:
            key = f"item.{item.id}.name"
            line = f"{key}={item.display_name}"
            if key in positions: lines[positions[key]] = line
            else:
                lines.append(f"{key}={item.display_name}")
    return "\n".join(lines) + ("\n" if lines else "")
