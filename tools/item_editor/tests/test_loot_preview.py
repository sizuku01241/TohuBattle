import unittest
from tools.item_editor.generators.loot_js import simulate_loot
from tools.item_editor.models import Item, LootEntry

class LootPreviewTests(unittest.TestCase):
    def items(self):
        return [Item(str(i), True, "vanilla", f"minecraft:item{i}", f"Item {i}", [], [LootEntry("common", 1, 1, weight)]) for i, weight in enumerate((1, 0.5, 0))]
    def test_seed_slots_unique_and_zero_weight(self):
        data = simulate_loot(self.items(), slots=1, trials=100, seed=4)
        self.assertEqual(data["rows"][2]["probability"], 0)
        self.assertTrue(all(row["probability"] <= 1 for row in data["rows"]))
        self.assertTrue(data["approximate"])
    def test_fixed_seed(self):
        self.assertEqual(simulate_loot(self.items(), trials=20, seed=9), simulate_loot(self.items(), trials=20, seed=9))
