import re
import struct
from pathlib import Path
from .models import Item

KEY = re.compile(r"^[a-z0-9_]+$")
IDENTIFIER = re.compile(r"^[a-z0-9_]+:[a-z0-9_]+$")
SOUND_IDENTIFIER = re.compile(r"^[a-z0-9_.:]+$")
TAGS = {"food", "weapon", "armor", "healing", "potion", "utility", "material", "special"}
POOLS = {"common", "supply", "ground"}
STACK_LIMITS = {
    # 主要なTBR物資。表にないIDは警告を出し、勝手に上限を推測しない。
    **{f"minecraft:{name}": 64 for name in (
        "apple", "bread", "carrot", "potato", "baked_potato", "beetroot", "beetroot_soup",
        "melon_slice", "pumpkin_pie", "cookie", "cooked_beef", "cooked_chicken", "cooked_porkchop",
        "cooked_mutton", "cooked_rabbit", "cooked_salmon", "cooked_cod", "golden_apple", "arrow",
        "spectral_arrow", "snowball", "egg", "stick", "string", "leather", "paper", "flint",
        "iron_ingot", "gold_ingot", "diamond", "coal", "torch", "glass", "stone", "cobblestone",
    )},
    **{f"minecraft:{name}": 16 for name in ("potion", "splash_potion", "lingering_potion", "sign", "bucket")},
    **{f"minecraft:{name}": 1 for name in (
        "bow", "crossbow", "shield", "fishing_rod", "flint_and_steel", "trident", "elytra",
        "stone_sword", "iron_sword", "golden_sword", "diamond_sword", "netherite_sword",
        "stone_axe", "iron_axe", "diamond_axe", "leather_chestplate", "iron_chestplate",
        "diamond_chestplate", "netherite_chestplate", "leather_helmet", "iron_helmet",
        "diamond_helmet", "leather_leggings", "iron_leggings", "diamond_leggings",
        "leather_boots", "iron_boots", "diamond_boots", "water_bucket", "lava_bucket",
    )},
}


def png_info(path: Path) -> tuple[bool, int, int]:
    try:
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR": return False, 0, 0
        width, height = struct.unpack(">II", data[16:24])
        return True, width, height
    except (OSError, struct.error):
        return False, 0, 0


def validate(items: list[Item]) -> list[tuple[str, str, str]]:
    errors: list[tuple[str, str, str]] = []
    seen_keys: set[str] = set()
    seen_ids: set[str] = set()
    for item in items:
        if not item.key or not KEY.fullmatch(item.key) or item.key in seen_keys:
            errors.append((item.key, "error", "keyが空・重複、または[a-z0-9_]以外を含みます"))
        seen_keys.add(item.key)
        if not IDENTIFIER.fullmatch(item.id) or (item.kind == "custom" and item.id.startswith("minecraft:")):
            errors.append((item.key, "error", "IDはnamespace:name形式で、customはminecraft名前空間を使えません"))
        if item.id in seen_ids:
            errors.append((item.key, "error", "IDが重複しています"))
        seen_ids.add(item.id)
        if item.kind == "custom" and (not item.display_name or not item.custom or not item.custom.icon):
            errors.append((item.key, "error", "customには表示名・アイコン・custom設定が必要です"))
        if not item.tags:
            errors.append((item.key, "warning", "タグがありません"))
        for entry in item.loot:
            if entry.pool not in POOLS or not 1 <= entry.rarity <= 7 or entry.amount < 1 or entry.weight <= 0:
                errors.append((item.key, "error", "lootのpool、レア度、個数、weightが不正です"))
            if entry.weight > 1: errors.append((item.key, "warning", "出現確率が1を超えています"))
            limit = item.custom.max_stack_size if item.custom else STACK_LIMITS.get(item.id, 64)
            if item.kind == "vanilla" and item.id not in STACK_LIMITS: errors.append((item.key, "warning", "Vanillaのスタック上限表に未登録です"))
            if entry.amount > limit:
                errors.append((item.key, "error", "個数が最大スタック数を超えています"))
        duplicates = {(entry.pool, entry.rarity) for entry in item.loot}
        if len(duplicates) != len(item.loot): errors.append((item.key, "warning", "同じpool・同じレア度のlootが重複しています"))
        if item.custom:
            if item.custom.food and not item.custom.use: errors.append((item.key, "error", "foodには使用時間(use)が必要です"))
            icon = Path(item.custom.icon) if item.custom.icon else None
            if icon and icon.exists():
                valid, width, height = png_info(icon)
                if not valid: errors.append((item.key, "error", "アイコンがPNGではありません"))
                elif width > 64 or height > 64: errors.append((item.key, "warning", "アイコンは16〜64px推奨です"))
            if item.custom.on_use:
                sound = item.custom.on_use.get("sound")
                if sound:
                    if not SOUND_IDENTIFIER.fullmatch(str(sound.get("id", ""))): errors.append((item.key, "error", "サウンドIDはnamespace.name形式で入力してください"))
                    try:
                        if not 0 < float(sound.get("volume", 1)) <= 10: errors.append((item.key, "error", "音量は0より大きく10以下にしてください"))
                        if not 0.1 <= float(sound.get("pitch", 1)) <= 2: errors.append((item.key, "error", "ピッチは0.1〜2の範囲にしてください"))
                    except (TypeError, ValueError): errors.append((item.key, "error", "音量とピッチは数値で入力してください"))
                    if sound.get("scope") not in {"source", "nearby"}: errors.append((item.key, "error", "音の範囲が不正です"))
                for effect in item.custom.on_use.get("effects", []):
                    if effect.get("kind") not in {"potion_effect", "heal"}: errors.append((item.key, "error", "右クリック効果kindはpotion_effect/healのみです"))
                    if float(effect.get("duration_sec", 0)) <= 0 or int(effect.get("level", 0)) <= 0: errors.append((item.key, "error", "効果時間とレベルは1以上が必要です"))
        if not item.loot:
            errors.append((item.key, "warning", "lootがありません"))
    return errors
