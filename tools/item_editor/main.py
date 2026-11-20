import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.item_editor.generators.ability_js import generate_ability_files
from tools.item_editor.generators.bp_item import generate_bp_item
from tools.item_editor.generators.loot_js import entry_signature, generate_loot_files
from tools.item_editor.generators.rp_assets import generate_lang, generate_texture_data
from tools.item_editor.importer import import_loot
from tools.item_editor.models import Item
from tools.item_editor.paths import project_root
from tools.item_editor.store import load_items
from tools.item_editor.validators import validate
from tools.item_editor.writer import apply, plan


def source_texts(root: Path) -> dict[str, str]:
    result = {}
    base = root / "behavior_pack/scripts/item/loot"
    for path in base.glob("**/rarity*.js"):
        result[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    return result


def ensure_items(root: Path) -> list[Item]:
    items = load_items(root)
    return items if items else import_loot(root)


def generate_files(root: Path, items: list[Item], sources: dict[str, str] | None = None) -> dict[str, str]:
    files = generate_loot_files(items, sources)
    custom_items = [item for item in items if item.enabled and item.kind == "custom"]
    for item in custom_items:
        files[f"behavior_pack/items/{item.key}.json"] = generate_bp_item(item)
    files.update(generate_ability_files(items))
    if custom_items:
        texture_path = root / "resource_pack/textures/item_texture.json"
        lang_path = root / "resource_pack/texts/ja_JP.lang"
        files["resource_pack/textures/item_texture.json"] = generate_texture_data(items, texture_path.read_text(encoding="utf-8") if texture_path.exists() else None)
        files["resource_pack/texts/ja_JP.lang"] = generate_lang(items, lang_path.read_text(encoding="utf-8") if lang_path.exists() else None)
    return files


def guarded_files(root: Path, items: list[Item], original_sources: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    files = generate_files(root, items, original_sources); conflicts = []
    current_sources = source_texts(root)
    for path, original in original_sources.items():
        if entry_signature(current_sources.get(path, "")) != entry_signature(original) and path in files:
            conflicts.append(path); files.pop(path, None)
    return files, conflicts


def cli(root: Path, write: bool) -> int:
    items = ensure_items(root); sources = source_texts(root); issues = validate(items)
    for key, level, message in issues: print(f"{level.upper()}: {key}: {message}")
    if any(level == "error" for _, level, _ in issues): return 1
    files, conflicts = guarded_files(root, items, sources)
    for path in conflicts: print(f"CONFLICT: 手動変更を検出したため上書きしません: {path}")
    entries = plan(root, files)
    for entry in entries: print(f"{entry.kind:9} {entry.path.relative_to(root)}")
    if write:
        history = apply(root, entries); print(f"written: {history.relative_to(root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TBR-001 item editor")
    parser.add_argument("--preview", action="store_true", help="GUIを開かず生成計画を表示")
    parser.add_argument("--generate", action="store_true", help="GUIを開かず生成して書き込む")
    args = parser.parse_args(); root = project_root()
    if args.preview or args.generate: return cli(root, args.generate)
    from tools.item_editor.ui import launch_gui
    launch_gui(root); return 0


if __name__ == "__main__":
    raise SystemExit(main())
