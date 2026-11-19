import { LOOT_COMMON_RARITY_1 } from "./common/rarity1.js";
import { LOOT_SUPPLY_RARITY_1 } from "./supply/rarity1.js";

// レア度ファイルを追加したら、ここで種類ごとに連結する。
export const lootTables = Object.freeze({
  common: Object.freeze([...LOOT_COMMON_RARITY_1]),
  supply: Object.freeze([...LOOT_SUPPLY_RARITY_1]),
});
