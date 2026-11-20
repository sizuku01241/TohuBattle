# TBR-001 Item Editor

Python 3.10以上、標準ライブラリのみで動作するオリジナルアイテム管理GUIです。

プロジェクトルートで実行します。

```powershell
python tools/item_editor/main.py
python tools/item_editor/main.py --preview
python tools/item_editor/main.py --generate
```

初回起動時は既存の `behavior_pack/scripts/item/loot/` を読み込み、`tools/items/items.json` を作成します。

GUIでは `Vanilla / Custom`、pool、レア度、使用アニメーションを選択式で指定できます。Customアイテムの画像は入力欄へパスを貼り付けず、ファイル選択ボタンから選びます。音声ファイル選択は未対応として無効化しています。

- PNG画像: `tools/items/icons/<key>.png` と `resource_pack/textures/items/tbr_<key>.png`
ファイルは「確認して生成」を確定した後にコピーされます。保存だけを行った場合も、選択済みアイコンはコピーされます。

右クリック能力は `on_use` として管理し、生成物は `abilityData.js`、`abilityRunner.js`、`abilityGeometry.js`、`abilityContext.js`、`tbrAbility.js` です。生成後に表示される `main.js` へのimportと `setAbilityContext` 接続例は手動で追加します。ツールは既存の `main.js` を変更しません。

使用時の音は `on_use.sound`（id / volume / pitch / scope）で管理します。生成ランナーは実際に発動条件を通過した後、`abilityContext.playSound(source, id, options)` を呼びます。接続例は `setAbilityContext({ playSound(source, id, options) { source.playSound?.(id); } })` です。音量・ピッチ・nearby の厳密なBedrock挙動は実機確認待ちです。音声ファイルは未対応です。

右クリック範囲プレビューは自動縮尺のグリッド上にプレイヤー、向き、判定内（緑）/外（赤）のサンプル対象を表示します。ルートプレビューは common/supply の3スロット上限で表示し、地面プールは現在のゲーム生成対象外として表示しません。`ItemManager.generateLoot` のJSランダム比較ソートはPythonで完全再現できないため、試行結果は概算です。

実機確認が必要な項目は、ItemCustomComponentの `onUse` イベント形、`tbr:ability` の登録タイミング、`event.itemStack` の取得、`minecraft:use_modifiers` のhold挙動、potion effectの引数単位、Bedrockのサウンド定義形式です。確認前の推測実装は行いません。

生成前に必ず検証とプレビューを行い、書き込み時は `tools/items/history/` に変更前ファイルを退避します。`main.js`、`ItemManager.js`、manifest、UUIDは変更しません。
# 操作手順

1. `python tools/item_editor/main.py` で起動する。
2. 「新規Custom」から空・食べ物・回復・右クリック能力のテンプレートを選ぶ。Vanillaは一覧から既存IDを編集する。
3. 基本情報、複数行の出現設定、食べ物/使用、右クリック能力を編集する。出現設定の下部にはpool×★の件数/確率合計が表示され、セルをクリックすると行を追加できる。
4. 保存はエラーが残っていても可能。下部の検証結果を確認し、「確認して生成」はエラー0件のときだけ実行する。
5. 生成前に「生成プレビュー」で差分を確認する。生成時は自動バックアップされる。
6. 「履歴」から世代を選択して復元できる。復元前には現在の`items.json`を保存する。

編集内容はタイトルバーの`*`で未保存状態を示す。`Ctrl+S`で保存、`Ctrl+Z`/`Ctrl+Y`でアイテム単位のUndo/Redoができる。検索・種別・タグ・pool・状態フィルターは一覧上部にある。

ウィンドウサイズ、最後に選択した項目、フィルターは`tools/items/settings.json`に保存される。終了時に未保存変更がある場合は、保存・破棄・キャンセルを選択できる。

## 実機確認待ち

Bedrockの仕様確認が完了していない項目（能力イベントの形、`tbr:ability`登録タイミング、hold/use_modifiers、Potion効果の単位、装備コンポーネント、サウンド）は生成対象にせず、GUIでも未対応として表示する。`main.js`へのimportと`setAbilityContext`接続はプレビューに手動追加行として表示し、自動変更しない。
