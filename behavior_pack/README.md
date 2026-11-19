# Tohu Battle Royale - 初期設定と動作確認

## 初期設定

座標は `scripts/config/stageConfig.js` にあります。最初はサンプル値です。自分のワールドの座標に変更してください。

- `dimensionId`: 使用するディメンション
- `lobby`: Lobby の待機地点
- `spawns`: 試合開始時のスポーン地点
- `map.bounds`: マップの X/Z 範囲
- `map.spawnY`: ランダム地点の Y 座標

Solo のサンプル設定はそのまま利用できます。Team を使う場合は `scripts/core/Constants.js` の `DEFAULT_CONFIG` で、次のように設定します。

```js
mode: GAME_MODES.TEAM,
teamCount: 2,
```

## ワールド側の準備

1. Behavior Pack と Resource Pack をワールドに追加する。
2. Beta APIs を有効にする。
3. OP 権限を持つプレイヤーで入る。
4. `stageConfig.js` の座標へ移動し、Lobby・スポーン地点・マップ範囲を確認する。
5. ワールドを完全再起動する。Custom Command は起動時に登録される。

## コマンド

Custom Command API の仕様により namespace が必要です。`/tbr start` ではなく、次の形式を使います。

| コマンド | 用途 |
|---|---|
| `/tbr:help` | コマンド一覧 |
| `/tbr:test` | 初期設定・登録人数の診断 |
| `/tbr:status` | 試合状態 |
| `/tbr:config` | 現在の設定 |
| `/tbr:team_setup` | 設定したチーム数で作成・ランダム編成 |
| `/tbr:team_random` | 待機中プレイヤーを再編成 |
| `/tbr:start` | Countdown と試合開始 |
| `/tbr:stop` | 管理者停止 |
| `/tbr:log_export` | 保存済みログをコンソール出力 |

## 推奨動作確認

### Solo

1. 3人以上でワールドに入る。
2. `/tbr:test` で `players` が3以上であることを確認する。
3. `/tbr:start` を実行する。
4. `10秒前`、`3`、`2`、`1`、`GAME START` を確認する。
5. 試合開始後、プレイヤーが `spawns` の地点へ移動することを確認する。
6. プレイヤーが死亡したとき観戦者になることを確認する。
7. 最後の1人が残ったとき Lobby に戻ることを確認する。
8. `/tbr:log_export` で `MATCH_START` / `MATCH_END` が出力されることを確認する。

### Team

1. `DEFAULT_CONFIG` を Team、`teamCount: 2` にする。
2. 4人以上でワールドに入る。
3. `/tbr:team_setup` を実行する。
4. `/tbr:start` を実行する。
5. 最後の1チームが残ったとき Team 勝利になることを確認する。

### 異常系

- 2人以下で `/tbr:start`: 参加人数不足で拒否。
- Team の人数が割り切れない場合: 編成拒否。
- 試合中に `/tbr:start`: 二重開始を拒否。
- Lobby で `/tbr:stop`: 試合なしとして失敗。
- OP 以外が管理コマンドを実行: 権限で拒否。

## 実装・検証状況

実装済みの主要機能は、試合管理、チーム編成、戦闘判定、Zone縮小、通常物資、段階サプライ、Scoreboard/Actionbar、ログ、Dynamic Properties分割保存、切断時インベントリ譲渡、MapManagerの複数マップ管理です。

リポジトリ内では `npm test` で純粋ロジックの自動テストを実行できます。Minecraft実機でのみ確認できる以下は、まだ実機確認待ちです。

- Script API 2.12.0-beta上の全イベント購読
- 実ワールドでの地形スキャンと物資配置
- サプライ開封・Zone外削除・再起動復旧
- Ticking Area、エリトラ降下、Locator Bar
- 3〜32人のSolo/Team統合試験

`stageConfig.js` の座標とマップ範囲は、実際のワールドに合わせて変更してください。
