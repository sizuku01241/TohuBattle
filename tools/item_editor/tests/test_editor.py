import json
import tempfile
import unittest
from pathlib import Path

from tools.item_editor.generators.loot_js import generate_loot_files
from tools.item_editor.generators.ability_js import generate_ability_files
from tools.item_editor.importer import import_loot
from tools.item_editor.models import Item, LootEntry, item_to_dict
from tools.item_editor.validators import validate
from tools.item_editor.writer import apply, plan
from tools.item_editor.ui_logic import change_selection, history_entries, loot_matrix, restore_history, suggest_key, template_item
from tools.item_editor.store import load_items, load_settings, save_items, save_settings
from tools.item_editor.state import EditorState
from tools.item_editor.form_logic import apply_form_to_item, parse_float, parse_int
from tools.item_editor.ui.tab_basic import filter_vanilla_candidates


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

    def test_form_writeback_undo_redo_preserves_every_item(self):
        items = [
            Item("one", True, "vanilla", "minecraft:bread", "one"),
            Item("two", True, "vanilla", "minecraft:arrow", "two"),
        ]
        state = EditorState(items)
        original = state.snapshot()
        before = state.snapshot()
        changed = apply_form_to_item(
            state.selected,
            {"key": "one", "id": "minecraft:bread", "name": "変更", "kind": "vanilla", "enabled": True},
            state.selected.loot,
            state.selected.tags,
        )
        state.items[state.selected_index] = changed
        state.record_change(before)
        changed_snapshot = state.snapshot()
        state.undo()
        self.assertEqual(state.snapshot(), original)
        state.redo()
        self.assertEqual(state.snapshot(), changed_snapshot)
        self.assertEqual(state.items[1].id, "minecraft:arrow")

    def test_editor_state_delete_keeps_valid_selection(self):
        state = EditorState([
            Item("one", True, "vanilla", "minecraft:bread", "one"),
            Item("two", True, "vanilla", "minecraft:arrow", "two"),
            Item("three", True, "vanilla", "minecraft:bow", "three"),
        ])
        state.select(1)
        state.remove_selected()
        self.assertEqual(state.selected.key, "three")
        state.remove_selected()
        self.assertEqual(state.selected.key, "one")

    def test_editor_state_history_restore_replaces_state(self):
        state = EditorState([Item("one", True, "vanilla", "minecraft:bread", "one")])
        restored = [Item("restored", True, "vanilla", "minecraft:arrow", "restored")]
        state.replace_items(restored, dirty=False)
        self.assertEqual(state.selected.key, "restored")
        self.assertFalse(state.dirty)

    def test_vanilla_id_candidates_are_searchable(self):
        self.assertEqual(filter_vanilla_candidates(("minecraft:arrow", "minecraft:bread"), "bread"), ("minecraft:bread",))
        self.assertEqual(filter_vanilla_candidates(("minecraft:arrow",), "unknown"), ())

    def test_invalid_numeric_form_names_the_field_and_does_not_mutate(self):
        item = Item("one", True, "custom", "tbr:one", "one")
        before = item_to_dict(item)
        with self.assertRaisesRegex(ValueError, "使用時間"):
            apply_form_to_item(item, {"kind": "custom", "food_enabled": True, "duration": "abc"}, [], [])
        self.assertEqual(item_to_dict(item), before)

    def test_zero_is_not_replaced_by_default(self):
        self.assertEqual(parse_float("0", "半径", 3), 0)
        self.assertEqual(parse_int("0", "効果レベル", 1), 0)
        self.assertEqual(parse_float("", "半径", 3), 3)

    def test_selection_same_index_does_not_write_back(self):
        calls = []
        result = change_selection(1, 1, lambda: calls.append("write"))
        self.assertFalse(result.changed)
        self.assertFalse(result.write_attempted)
        self.assertEqual(calls, [])

    def test_selection_write_failure_keeps_selection_and_retries_once_only(self):
        calls = []
        def fail_write():
            calls.append("write")
            raise ValueError("使用時間には数値を入力してください")
        failed = change_selection(0, 1, fail_write)
        repeated_event = change_selection(failed.selected_index, 0, fail_write)
        self.assertFalse(failed.changed)
        self.assertEqual(failed.selected_index, 0)
        self.assertIsNotNone(failed.error)
        self.assertFalse(repeated_event.write_attempted)
        self.assertEqual(calls, ["write"])

    def test_selection_write_success_changes_selection(self):
        result = change_selection(0, 1, lambda: None)
        self.assertTrue(result.changed)
        self.assertEqual(result.selected_index, 1)

    def test_restore_history_old_format_targets_tools_items(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history = root / "tools/items/history/old"
            history.mkdir(parents=True)
            payload = {"schema_version": 1, "items": [{"key": "arrow", "enabled": True, "kind": "vanilla", "id": "minecraft:arrow", "display_name": "矢"}]}
            expected = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            (history / "items.json").write_text(expected, encoding="utf-8")
            restored = restore_history(root, history)
            self.assertIn("tools/items/items.json", restored)
            self.assertEqual((root / "tools/items/items.json").read_text(encoding="utf-8"), expected)
            self.assertFalse((root / "items.json").exists())

    def test_restore_history_new_format_and_save_delete_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = [Item("bread", True, "vanilla", "minecraft:bread", "パン"), Item("arrow", True, "vanilla", "minecraft:arrow", "矢")]
            save_items(root, original)
            save_items(root, [original[0]])
            history = next((root / "tools/items/history").iterdir())
            restore_history(root, history)
            self.assertEqual([item.key for item in load_items(root)], ["bread", "arrow"])
            self.assertFalse((root / "items.json").exists())
            new_history = root / "tools/items/history/new"
            (new_history / "tools/items").mkdir(parents=True)
            (new_history / "tools/items/items.json").write_text((root / "tools/items/items.json").read_text(encoding="utf-8"), encoding="utf-8")
            (root / "tools/items/items.json").write_text('{"schema_version": 1, "items": []}\n', encoding="utf-8")
            restore_history(root, new_history)
            self.assertEqual([item.key for item in load_items(root)], ["bread", "arrow"])

    def test_history_entries_reports_item_count_and_key_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_items(root, [Item("bread", True, "vanilla", "minecraft:bread", "パン")])
            history = root / "tools/items/history/diff"
            history.mkdir(parents=True)
            payload = {"schema_version": 1, "items": [item_to_dict(Item("arrow", True, "vanilla", "minecraft:arrow", "矢"))]}
            (history / "items.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            entry = next(item for item in history_entries(root) if item["name"] == "diff")
            self.assertEqual(entry["items"], 1)
            self.assertIn("arrow", entry["added"])
            self.assertIn("bread", entry["removed"])

    def test_ten_item_history_restores_arrow_after_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = [Item("minecraft_bread", True, "vanilla", "minecraft:bread", "パン"), Item("minecraft_arrow", True, "vanilla", "minecraft:arrow", "矢")]
            original.extend(Item(f"item_{index}", True, "vanilla", "minecraft:stone", "") for index in range(8))
            save_items(root, original)
            save_items(root, [item for item in original if item.key != "minecraft_arrow"])
            history = next((root / "tools/items/history").iterdir())
            restore_history(root, history)
            restored = load_items(root)
            self.assertEqual(len(restored), 10)
            self.assertIn("minecraft_arrow", [item.key for item in restored])

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
