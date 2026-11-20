import tempfile
import unittest
from pathlib import Path

from tools.item_editor.generators.loot_js import generate_loot_files
from tools.item_editor.generators.ability_js import generate_ability_files
from tools.item_editor.importer import import_loot
from tools.item_editor.models import Item, LootEntry, item_to_dict
from tools.item_editor.validators import validate
from tools.item_editor.writer import apply, plan
from tools.item_editor.ui_logic import loot_matrix, suggest_key, template_item
from tools.item_editor.store import load_settings, save_items, save_settings
from tools.item_editor.state import EditorState


class ItemEditorTests(unittest.TestCase):
    def test_editor_state_delete_does_not_change_other_items(self):
        items = [
            Item("one", True, "vanilla", "minecraft:bread", "one"),
            Item("two", True, "vanilla", "minecraft:arrow", "two", loot=[LootEntry("common", 1, 8, 0.5)]),
            Item("three", True, "vanilla", "minecraft:bow", "three"),
        ]
        state = EditorState(items)
        before = [item_to_dict(item) for item in items]
        state.select(1)
        state.remove_selected()
        self.assertEqual([item_to_dict(item) for item in items], [before[0], before[2]])

    def test_editor_state_undo_redo_round_trip(self):
        items = [Item("one", True, "vanilla", "minecraft:bread", "one"), Item("two", True, "vanilla", "minecraft:arrow", "two")]
        state = EditorState(items)
        original = state.snapshot()
        items[1].display_name = "changed"
        state.record_change(original)
        changed = state.snapshot()
        state.undo()
        self.assertEqual(state.snapshot(), original)
        state.redo()
        self.assertEqual(state.snapshot(), changed)
        state.undo(); state.redo(); state.undo()
        self.assertEqual(state.snapshot(), original)

    def test_editor_state_repeated_selection_does_not_mutate_items(self):
        items = [Item("one", True, "vanilla", "minecraft:bread", "one"), Item("two", True, "vanilla", "minecraft:arrow", "two")]
        state = EditorState(items)
        original = state.snapshot()
        for index in (1, 0, 1, 0, 1, 0):
            state.select(index)
        self.assertEqual(state.snapshot(), original)

    def test_editor_logic_key_templates_and_matrix(self):
        existing = [Item("bread", True, "vanilla", "minecraft:bread", "パン")]
        self.assertEqual(suggest_key("minecraft:bread", existing), "bread_copy2")
        healing = template_item("healing", existing)
        self.assertEqual(healing.custom.food["nutrition"], 0)
        self.assertTrue(healing.custom.on_use)
        cells = loot_matrix([healing])
        common_one = next(cell for cell in cells if cell.pool == "common" and cell.rarity == 1)
        self.assertEqual(common_one.count, 1)

    def test_import_existing_loot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            loot = root / "behavior_pack/scripts/item/loot/common"
            loot.mkdir(parents=True)
            (loot / "rarity1.js").write_text('export const X = Object.freeze([{ id: "minecraft:bread", amount: 4, weight: 0.75, rarity: 1 }]);\n', encoding="utf-8")
            items = import_loot(root)
            self.assertEqual(items[0].id, "minecraft:bread")
            self.assertEqual(items[0].loot[0].amount, 4)

    def test_validation_rejects_invalid_custom(self):
        items = [Item("same", True, "custom", "minecraft:bad", "", [], [], None), Item("same", True, "vanilla", "minecraft:bread", "", [], [], None)]
        self.assertTrue(any(level == "error" for _, level, _ in validate(items)))

    def test_writer_creates_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = generate_loot_files([Item("bread", True, "vanilla", "minecraft:bread", "", [], [LootEntry("common", 1, 4, 0.75)], None)])
            history = apply(root, plan(root, files))
            self.assertTrue((root / "behavior_pack/scripts/item/loot/common/rarity1.js").exists())
            self.assertTrue((history / "manifest.json").exists())

    def test_item_history_is_unique_and_limited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            items_path = root / "tools/items/items.json"
            items_path.parent.mkdir(parents=True)
            items_path.write_text('{"schema_version": 1, "items": []}\n', encoding="utf-8")
            for _ in range(55):
                save_items(root, [])
            generations = [entry for entry in (root / "tools/items/history").iterdir() if entry.is_dir()]
            self.assertEqual(len(generations), 50)
            self.assertEqual(len({entry.name for entry in generations}), 50)

    def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_settings(root, {"window_geometry": "1200x700", "last_key": "bread", "filters": {"kind": "vanilla"}})
            self.assertEqual(load_settings(root)["window_geometry"], "1200x700")
            self.assertEqual(load_settings(root)["filters"]["kind"], "vanilla")

    def test_multiple_loot_rows_and_ability_generation(self):
        item = Item("ability", True, "custom", "tbr:ability", "Ability", [], [LootEntry("common", 1, 1, 0.2), LootEntry("supply", 2, 1, 0.4)], None)
        from tools.item_editor.models import CustomSpec
        item.custom = CustomSpec(on_use={"trigger": "tap", "target": {"type": "cone"}, "effects": [{"kind": "heal", "amount": 2, "duration_sec": 1, "level": 1}]})
        files = generate_loot_files([item])
        self.assertIn("common: Object.freeze([", files["behavior_pack/scripts/item/loot/index.js"])
        self.assertIn("supply: Object.freeze([", files["behavior_pack/scripts/item/loot/index.js"])
        ability_files = generate_ability_files([item])
        self.assertIn("abilityData.js", "\n".join(ability_files))
        self.assertIn('"tbr:ability"', __import__("tools.item_editor.generators.bp_item", fromlist=["generate_bp_item"]).generate_bp_item(item))


if __name__ == "__main__":
    unittest.main()
