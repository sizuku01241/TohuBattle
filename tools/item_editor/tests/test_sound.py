import unittest

from tools.item_editor.form_logic import apply_form_to_item
from tools.item_editor.generators.ability_js import generate_ability_files
from tools.item_editor.models import CustomSpec, Item, LootEntry
from tools.item_editor.validators import validate


class SoundTests(unittest.TestCase):
    def item(self, sound=None):
        return Item("test", True, "custom", "tbr:test", "Test", [], [LootEntry("common", 1, 1, 0.5)], CustomSpec(icon="x.png", on_use={"target": {"type": "self"}, "effects": [], **({"sound": sound} if sound else {})}))

    def test_sound_round_trip_and_generated_runner(self):
        sound = {"id": "random.levelup", "volume": 0.8, "pitch": 1.2, "scope": "nearby"}
        item = self.item(sound)
        files = generate_ability_files([item])
        self.assertIn('"sound": {', files["behavior_pack/scripts/item/custom/abilityData.js"])
        self.assertIn("game.playSound?.(source, sound.id", files["behavior_pack/scripts/item/custom/abilityRunner.js"])
        self.assertEqual(item.custom.on_use["sound"], sound)

    def test_form_keeps_sound_and_empty_sound_is_omitted(self):
        item = self.item({"id": "random.levelup", "volume": 1, "pitch": 1, "scope": "source"})
        values = {"kind": "custom", "ability_enabled": True, "target_type": "self", "sound_id": "random.orb", "sound_volume": "0.5", "sound_pitch": "1.1", "sound_scope": "source"}
        result = apply_form_to_item(item, values, item.loot, [])
        self.assertEqual(result.custom.on_use["sound"]["id"], "random.orb")
        result = apply_form_to_item(item, {"kind": "custom", "ability_enabled": True, "target_type": "self", "sound_id": ""}, item.loot, [])
        self.assertNotIn("sound", result.custom.on_use)

    def test_sound_validation(self):
        errors = validate([self.item({"id": "BAD ID", "volume": 0, "pitch": 3, "scope": "all"})])
        self.assertGreaterEqual(sum(level == "error" for _, level, _ in errors), 3)


if __name__ == "__main__":
    unittest.main()
