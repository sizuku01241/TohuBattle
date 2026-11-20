import copy
from pathlib import Path

from ..generators.loot_js import simulate_item_probability
from ..models import CustomSpec, Item, LootEntry, item_from_dict, item_to_dict
from ..store import load_items, load_settings, save_items, save_settings
from ..state import EditorState
from ..validators import STACK_LIMITS, TAGS, validate
from ..writer import apply, plan
from ..ui_logic import history_entries, loot_matrix, restore_history, suggest_key, template_item
from .preview import unified_diff
from .tab_ability import EFFECT_VALUES, TARGET_VALUES
from .tab_basic import KIND_VALUES
from .tab_loot import POOL_VALUES, RARITY_VALUES
from .tab_use import UNSUPPORTED_USE_MESSAGE


def launch_gui(root: Path) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from ..main import ensure_items, generate_files, source_texts, guarded_files

    settings = load_settings(root)
    window = tk.Tk(); window.title("TBR-001 アイテム管理GUI"); window.geometry(settings.get("window_geometry", "1350x850")); window.minsize(1100, 700)
    items = ensure_items(root); editor_state = EditorState(items); sources = source_texts(root); selected = {"item": editor_state.selected}; asset_sources = {}; search = tk.StringVar(master=window); filter_kind = tk.StringVar(master=window, value="すべて"); filter_tag = tk.StringVar(master=window, value="すべて"); filter_pool = tk.StringVar(master=window, value="すべて"); filter_state = tk.StringVar(master=window, value="すべて"); status = tk.StringVar(master=window, value="自動取り込み済み。項目を切り替えると編集内容を反映します")
    edit_state = {"dirty": False, "restoring": False, "undo": [], "redo": [], "allow_count_reduction": False}
    saved_filters = settings.get("filters", {})
    filter_kind.set(saved_filters.get("kind", "すべて")); filter_tag.set(saved_filters.get("tag", "すべて")); filter_pool.set(saved_filters.get("pool", "すべて")); filter_state.set(saved_filters.get("state", "すべて"))
    window.columnconfigure(1, weight=1); window.rowconfigure(1, weight=1)
    fields = {key: tk.StringVar() for key in ("key", "id", "name", "pool", "rarity", "amount", "weight", "nutrition", "saturation", "duration", "movement", "animation", "target", "radius", "angle", "width", "effect_id", "effect_duration", "effect_level", "heal")}
    kind = tk.StringVar(); enabled = tk.BooleanVar(); food_enabled = tk.BooleanVar(); always_eat = tk.BooleanVar(); ability_enabled = tk.BooleanVar(); trigger = tk.StringVar(value="tap"); target_type = tk.StringVar(value="self"); tag_vars = {tag: tk.BooleanVar() for tag in TAGS}; icon_label = tk.StringVar(value="未対応"); preview_text = None
    loot_rows = []; loot_selected = {"index": None}

    def entry(frame, row, label, var, column=0):
        ttk.Label(frame, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=4); widget = ttk.Entry(frame, textvariable=var, width=25); widget.grid(row=row, column=column + 1, sticky="ew", padx=5, pady=4); return widget

    header = ttk.Frame(window); header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=8); ttk.Label(header, text="検索").pack(side="left"); ttk.Entry(header, textvariable=search, width=24).pack(side="left", padx=6)
    ttk.Label(header, text="種別").pack(side="left"); ttk.Combobox(header, textvariable=filter_kind, values=("すべて", "custom", "vanilla"), state="readonly", width=9).pack(side="left", padx=3)
    ttk.Label(header, text="タグ").pack(side="left"); ttk.Combobox(header, textvariable=filter_tag, values=("すべて", *sorted(TAGS)), state="readonly", width=11).pack(side="left", padx=3)
    ttk.Label(header, text="pool").pack(side="left"); ttk.Combobox(header, textvariable=filter_pool, values=("すべて", "common", "supply", "ground"), state="readonly", width=9).pack(side="left", padx=3)
    ttk.Label(header, text="状態").pack(side="left"); ttk.Combobox(header, textvariable=filter_state, values=("すべて", "有効", "無効", "エラーあり"), state="readonly", width=11).pack(side="left", padx=3)
    tree_frame = ttk.LabelFrame(window, text="登録アイテム"); tree_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5); tree_frame.rowconfigure(0, weight=1); tree_frame.columnconfigure(0, weight=1)
    tree = ttk.Treeview(tree_frame, columns=("kind", "id", "name", "loot", "state"), show="headings", selectmode="browse")
    for col, title, width in (("kind", "種別", 70), ("id", "ID", 190), ("name", "名前", 120), ("loot", "出現設定", 100), ("state", "状態", 60)): tree.heading(col, text=title); tree.column(col, width=width)
    tree.grid(row=0, column=0, sticky="nsew"); tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview); tree_scroll.grid(row=0, column=1, sticky="ns"); tree.configure(yscrollcommand=tree_scroll.set)
    editor = ttk.Frame(window); editor.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5); editor.rowconfigure(0, weight=1); editor.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(editor); notebook.grid(row=0, column=0, sticky="nsew")
    basic = ttk.Frame(notebook, padding=12); loot = ttk.Frame(notebook, padding=12); food = ttk.Frame(notebook, padding=12); ability = ttk.Frame(notebook, padding=12); equip = ttk.Frame(notebook, padding=12); preview = ttk.Frame(notebook, padding=8)
    for frame, title in ((basic, "基本"), (loot, "出現設定"), (food, "食べ物/使用"), (ability, "右クリック"), (equip, "装備(未対応)"), (preview, "プレビュー")): notebook.add(frame, text=title)
    for frame in (basic, loot, food, ability, equip): frame.columnconfigure(1, weight=1)

    entry(basic, 0, "内部ID", fields["key"]); ttk.Label(basic, text="種別").grid(row=1, column=0, sticky="w", padx=5, pady=4); kind_box = ttk.Combobox(basic, textvariable=kind, values=KIND_VALUES, state="readonly", width=22); kind_box.grid(row=1, column=1, sticky="ew", padx=5, pady=4); ttk.Label(basic, text="アイテムID").grid(row=2, column=0, sticky="w", padx=5, pady=4); id_box = ttk.Combobox(basic, textvariable=fields["id"], values=tuple(sorted(STACK_LIMITS)), state="normal", width=25); id_box.grid(row=2, column=1, sticky="ew", padx=5, pady=4); ttk.Label(basic, text="候補から選択できます。未知のVanilla IDは検証警告になります。", foreground="#666").grid(row=2, column=2, sticky="w", padx=5); entry(basic, 3, "表示名", fields["name"]); ttk.Checkbutton(basic, text="有効", variable=enabled).grid(row=4, column=1, sticky="w", padx=5, pady=4)
    ttk.Label(basic, text="タグ").grid(row=5, column=0, sticky="nw", padx=5, pady=4); tag_frame = ttk.Frame(basic); tag_frame.grid(row=5, column=1, sticky="w")
    for index, tag in enumerate(TAGS): ttk.Checkbutton(tag_frame, text=tag, variable=tag_vars[tag]).grid(row=index // 4, column=index % 4, sticky="w", padx=4)
    ttk.Button(basic, text="PNGファイルを選択", command=lambda: choose_icon()).grid(row=6, column=0, padx=5, pady=8); ttk.Label(basic, textvariable=icon_label).grid(row=6, column=1, sticky="w", padx=5); icon_preview = ttk.Label(basic, text="プレビューなし"); icon_preview.grid(row=6, column=2, padx=8); ttk.Label(basic, text="音声ファイル: 未対応（Bedrock定義確認待ち）", foreground="#996600").grid(row=7, column=0, columnspan=3, sticky="w", padx=5, pady=8)

    ttk.Label(loot, text="複数行を保持します。行を切り替えても自動反映されます。", foreground="#555").grid(row=0, column=0, columnspan=4, sticky="w", pady=4)
    loot_table = ttk.Treeview(loot, columns=("pool", "rarity", "amount", "weight", "prob"), show="headings", height=8)
    for col, title, width in (("pool", "pool", 100), ("rarity", "★", 50), ("amount", "個数", 70), ("weight", "出現確率(0〜1)", 130), ("prob", "1チェスト確率", 130)): loot_table.heading(col, text=title); loot_table.column(col, width=width)
    loot_table.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=6); loot.rowconfigure(1, weight=1)
    matrix = ttk.Treeview(loot, columns=("pool", "r1", "r2", "r3", "r4", "r5", "r6", "r7"), show="headings", height=4)
    for col, title in (("pool", "pool"), *( (f"r{i}", f"★{i}") for i in range(1, 8) )): matrix.heading(col, text=title); matrix.column(col, width=80, anchor="center")
    matrix.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(10, 4)); ttk.Label(loot, text="マトリクス: 件数 / 出現確率合計。セルをクリックすると、そのpool・レア度の行を追加します。", foreground="#555").grid(row=5, column=0, columnspan=4, sticky="w")
    ttk.Button(loot, text="行を追加", command=lambda: add_loot_row()).grid(row=2, column=0, padx=3, pady=5, sticky="w"); ttk.Button(loot, text="選択行を削除", command=lambda: remove_loot_row()).grid(row=2, column=1, padx=3, pady=5, sticky="w")
    loot_form = ttk.Frame(loot); loot_form.grid(row=3, column=0, columnspan=4, sticky="ew"); loot_form.columnconfigure(1, weight=1); ttk.Label(loot_form, text="選択行を編集").grid(row=0, column=0, columnspan=4, sticky="w"); ttk.Label(loot_form, text="pool").grid(row=1, column=0); pool_box = ttk.Combobox(loot_form, textvariable=fields["pool"], values=POOL_VALUES, state="readonly", width=12); pool_box.grid(row=1, column=1); ttk.Label(loot_form, text="★").grid(row=1, column=2); ttk.Combobox(loot_form, textvariable=fields["rarity"], values=RARITY_VALUES, state="readonly", width=8).grid(row=1, column=3); entry(loot_form, 2, "個数", fields["amount"]); entry(loot_form, 3, "出現確率(0〜1)", fields["weight"])

    ttk.Checkbutton(food, text="食べ物を有効化", variable=food_enabled).grid(row=0, column=0, columnspan=2, sticky="w", pady=5); entry(food, 1, "空腹回復", fields["nutrition"]); entry(food, 2, "満腹度", fields["saturation"]); ttk.Checkbutton(food, text="常に食べられる", variable=always_eat).grid(row=3, column=1, sticky="w"); entry(food, 4, "使用時間(秒)", fields["duration"]); entry(food, 5, "移動速度係数", fields["movement"]); ttk.Label(food, text="アニメーション").grid(row=6, column=0, sticky="w", padx=5); ttk.Combobox(food, textvariable=fields["animation"], values=("eat", "drink", "bow", "block", "none"), state="readonly", width=22).grid(row=6, column=1, sticky="ew", padx=5); ttk.Label(food, text=UNSUPPORTED_USE_MESSAGE, foreground="#996600").grid(row=7, column=0, columnspan=2, sticky="w", pady=10)

    ttk.Checkbutton(ability, text="右クリック能力を有効化", variable=ability_enabled).grid(row=0, column=0, columnspan=2, sticky="w"); ttk.Label(ability, text="発動").grid(row=1, column=0, sticky="w", padx=5, pady=4); ttk.Combobox(ability, textvariable=trigger, values=("tap", "hold"), state="readonly", width=22).grid(row=1, column=1, sticky="ew", padx=5); ttk.Label(ability, text="対象形状").grid(row=2, column=0, sticky="w", padx=5, pady=4); ttk.Combobox(ability, textvariable=target_type, values=TARGET_VALUES, state="readonly", width=22).grid(row=2, column=1, sticky="ew", padx=5); entry(ability, 3, "半径", fields["radius"]); entry(ability, 4, "角度", fields["angle"]); entry(ability, 5, "幅", fields["width"]); ttk.Label(ability, text="効果kind").grid(row=6, column=0, sticky="w", padx=5); ttk.Combobox(ability, textvariable=fields["target"], values=EFFECT_VALUES, state="readonly", width=22).grid(row=6, column=1, sticky="ew", padx=5); entry(ability, 7, "効果ID", fields["effect_id"]); entry(ability, 8, "効果時間(秒)", fields["effect_duration"]); entry(ability, 9, "効果レベル", fields["effect_level"]); entry(ability, 10, "回復量", fields["heal"]); ttk.Label(ability, text="対象判定はabilityContext経由。ダメージ/ノックバック/発火は未対応。", foreground="#996600").grid(row=11, column=0, columnspan=2, sticky="w", pady=10)
    ability_canvas = tk.Canvas(ability, width=360, height=220, background="#20242b", highlightthickness=0); ability_canvas.grid(row=0, column=2, rowspan=12, padx=18, pady=8, sticky="nsew")

    def draw_ability_preview(*_args):
        ability_canvas.delete("all"); cx, cy = 180, 110; ability_canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#ffffff", outline="")
        try: radius = max(10, min(95, float(fields["radius"].get() or 3) * 20))
        except ValueError: radius = 60
        shape = target_type.get()
        if shape == "circle": ability_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#55ccff", width=3)
        elif shape == "line": ability_canvas.create_rectangle(cx, cy - max(5, float(fields["width"].get() or 1) * 10), cx + radius, cy + max(5, float(fields["width"].get() or 1) * 10), outline="#55ccff", width=3)
        elif shape == "cone": ability_canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=-45, extent=90, outline="#55ccff", width=3, style="arc")
        elif shape == "look": ability_canvas.create_line(cx, cy, cx + radius, cy, fill="#55ccff", width=4)
        else: ability_canvas.create_text(cx, cy - radius - 15, text="self", fill="#ffffff")
    for variable in (target_type, fields["radius"], fields["angle"], fields["width"]): variable.trace_add("write", draw_ability_preview)

    ttk.Label(equip, text="装備タブは設計書により未対応です", foreground="#996600").grid(row=0, column=0, columnspan=2, sticky="w"); ttk.Label(equip, text="Minecraftの装備コンポーネント確認後に有効化します。", foreground="#666").grid(row=1, column=0, columnspan=2, sticky="w")
    preview.columnconfigure(0, weight=0); preview.columnconfigure(1, weight=1); preview.rowconfigure(0, weight=1)
    preview_files = tk.Listbox(preview, width=42); preview_files.grid(row=0, column=0, sticky="nsew", padx=(0, 8)); preview_text = tk.Text(preview, wrap="none", state="disabled"); preview_text.grid(row=0, column=1, sticky="nsew")
    preview_diffs = {}

    def show_preview_diff(_event=None):
        selection = preview_files.curselection()
        if not selection:
            return
        path = preview_files.get(selection[0])
        preview_text.configure(state="normal"); preview_text.delete("1.0", "end"); preview_text.insert("1.0", preview_diffs.get(path, "差分なし")); preview_text.configure(state="disabled")
    preview_files.bind("<<ListboxSelect>>", show_preview_diff)

    def update_icon_preview(path):
        try:
            image = tk.PhotoImage(file=str(path))
            scale = max(1, min(8, 64 // max(image.width(), image.height(), 1)))
            if scale > 1:
                image = image.zoom(scale, scale)
            icon_preview.configure(image=image, text=f"{image.width()}x{image.height()}px")
            icon_preview.image = image
        except Exception:
            icon_preview.configure(image="", text="PNGを読み込めません")
            icon_preview.image = None

    def choose_icon():
        path = filedialog.askopenfilename(title="アイコンPNGを選択", filetypes=(("PNG画像", "*.png"),))
        if path: asset_sources[id(selected["item"])] = path; icon_label.set(Path(path).name); update_icon_preview(path); refresh()

    validation_label = ttk.Label(window, text="", anchor="w")
    validation_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

    def update_title():
        window.title(("*" if edit_state["dirty"] else "") + "TBR-001 アイテム管理GUI")

    def mark_dirty(*_args):
        if not edit_state["restoring"]:
            edit_state["dirty"] = True
            update_title()

    def snapshot():
        return copy.deepcopy([item_to_dict(item) for item in items])

    def restore_snapshot(data):
        edit_state["restoring"] = True
        editor_state.replace(data)
        selected["item"] = editor_state.selected
        refresh()
        if selected["item"]:
            load_item(selected["item"], flush=False)
        edit_state["restoring"] = False

    def undo():
        if not edit_state["undo"]:
            return
        edit_state["redo"].append(snapshot()); restore_snapshot(edit_state["undo"].pop()); edit_state["dirty"] = True; update_title()

    def redo():
        if not edit_state["redo"]:
            return
        edit_state["undo"].append(snapshot()); restore_snapshot(edit_state["redo"].pop()); edit_state["dirty"] = True; update_title()

    def refresh():
        tree.delete(*tree.get_children()); needle = search.get().lower(); issues = validate(items); errors = sum(level == "error" for _, level, _ in issues); warnings = sum(level == "warning" for _, level, _ in issues)
        validation_label.configure(text=f"検証結果: エラー {errors}件 / 警告 {warnings}件", foreground="#b00020" if errors else ("#996600" if warnings else "#287a2b"))
        for index, item in enumerate(items):
            if needle and needle not in (item.key + item.id + item.display_name).lower(): continue
            item_issues = [level for key, level, _ in issues if key == item.key]
            if filter_kind.get() != "すべて" and item.kind != filter_kind.get(): continue
            if filter_tag.get() != "すべて" and filter_tag.get() not in item.tags: continue
            if filter_pool.get() != "すべて" and not any(entry.pool == filter_pool.get() for entry in item.loot): continue
            if filter_state.get() == "有効" and not item.enabled: continue
            if filter_state.get() == "無効" and item.enabled: continue
            if filter_state.get() == "エラーあり" and "error" not in item_issues: continue
            state = "✖" if "error" in item_issues else ("⚠" if "warning" in item_issues else "✔")
            tree.insert("", "end", iid=str(index), values=(item.kind, item.id, item.display_name or "(未設定)", len(item.loot), state))
        refresh_matrix()

    def refresh_matrix():
        matrix.delete(*matrix.get_children())
        cells = {(cell.pool, cell.rarity): cell for cell in loot_matrix(items)}
        for pool in ("common", "supply", "ground"):
            values = [pool]
            for rarity in range(1, 8):
                cell = cells[(pool, rarity)]
                values.append(f"{cell.count} / {cell.weight_total:.2f}")
            matrix.insert("", "end", iid=pool, values=values)

    def show_validation():
        issues = validate(items)
        dialog = tk.Toplevel(window)
        dialog.title("検証結果")
        dialog.geometry("760x360")
        issue_list = tk.Listbox(dialog)
        issue_list.pack(fill="both", expand=True, padx=10, pady=10)
        for key, level, message in issues:
            issue_list.insert("end", f"{'✖' if level == 'error' else '⚠'} [{key}] {message}")

        def select_issue(_event=None):
            selection = issue_list.curselection()
            if not selection:
                return
            key = issues[selection[0]][0]
            for index, item in enumerate(items):
                if item.key == key:
                    selected["item"] = item
                    load_item(item)
                    refresh()
                    tree.selection_set(str(index))
                    notebook.select(basic)
                    dialog.destroy()
                    return

        issue_list.bind("<Double-Button-1>", select_issue)
        ttk.Label(dialog, text="項目をダブルクリックすると対象アイテムを開きます。", foreground="#666").pack(pady=(0, 8))

    def add_matrix_row(event):
        row = matrix.identify_row(event.y); column = matrix.identify_column(event.x)
        if not row or column in ("", "#1"):
            return
        rarity = int(column[1:])
        loot_rows.append(LootEntry(row, rarity, 1, 0.5)); refresh_loot_table(); loot_table.selection_set(str(len(loot_rows) - 1)); load_loot_row(loot_rows[-1]); write_form_to_item()
    matrix.bind("<Button-1>", add_matrix_row)
    validation_label.bind("<Button-1>", lambda _event: show_validation())

    def write_form_to_item():
        item = selected["item"]
        if not item or item not in items: return
        before = snapshot()
        commit_selected_loot()
        item.key = fields["key"].get().strip(); item.id = fields["id"].get().strip(); item.display_name = fields["name"].get(); item.kind = kind.get(); item.enabled = enabled.get(); item.tags = [tag for tag, var in tag_vars.items() if var.get()]
        item.loot = copy.deepcopy(loot_rows)
        if item.kind == "custom":
            custom = item.custom or CustomSpec(); custom.icon = custom.icon or ""
            if asset_sources.get(id(item)): custom.icon = f"tools/items/icons/{item.key}.png"
            custom.use = {"duration_sec": float(fields["duration"].get() or 1.6), "movement_modifier": float(fields["movement"].get() or 0.35), "animation": fields["animation"].get()} if food_enabled.get() else None
            custom.food = {"nutrition": int(fields["nutrition"].get() or 0), "saturation_modifier": float(fields["saturation"].get() or 0), "can_always_eat": always_eat.get()} if food_enabled.get() else None
            if ability_enabled.get():
                custom.on_use = {"trigger": trigger.get(), "target": {"type": target_type.get(), "radius": float(fields["radius"].get() or 0), "angle": float(fields["angle"].get() or 90), "width": float(fields["width"].get() or 1)}, "effects": [{"kind": fields["target"].get() or "heal", "id": fields["effect_id"].get(), "duration_sec": float(fields["effect_duration"].get() or 1), "level": int(fields["effect_level"].get() or 1), "amount": float(fields["heal"].get() or 0)}]}
            else:
                custom.on_use = None
            item.custom = custom
        else: item.custom = None
        after = snapshot()
        if before != after and not edit_state["restoring"]:
            edit_state["undo"].append(before)
            edit_state["redo"].clear()
            edit_state["dirty"] = True
            update_title()
        refresh()

    def load_item(item, flush=False):
        previous_restoring = edit_state["restoring"]
        edit_state["restoring"] = True
        if flush:
            edit_state["restoring"] = previous_restoring
            write_form_to_item()
            edit_state["restoring"] = True
        if item not in items:
            edit_state["restoring"] = previous_restoring
            return
        editor_state.select_item(item)
        selected["item"] = editor_state.selected
        fields["key"].set(item.key); fields["id"].set(item.id); fields["name"].set(item.display_name); kind.set(item.kind); enabled.set(item.enabled)
        for tag, var in tag_vars.items(): var.set(tag in item.tags)
        loot_rows.clear(); loot_rows.extend(copy.deepcopy(item.loot)); refresh_loot_table()
        entry = loot_rows[0] if loot_rows else LootEntry("common", 1, 1, 0.5); load_loot_row(entry)
        custom = item.custom or CustomSpec(); icon_label.set(Path(custom.icon).name if custom.icon else "未選択"); icon_source = asset_sources.get(id(item)); update_icon_preview(icon_source) if icon_source else icon_preview.configure(image="", text="プレビューなし"); food_enabled.set(bool(custom.food)); fields["nutrition"].set(str((custom.food or {}).get("nutrition", ""))); fields["saturation"].set(str((custom.food or {}).get("saturation_modifier", ""))); fields["duration"].set(str((custom.use or {}).get("duration_sec", "1.6"))); fields["movement"].set(str((custom.use or {}).get("movement_modifier", "0.35"))); fields["animation"].set((custom.use or {}).get("animation", "eat")); ability_enabled.set(bool(custom.on_use));
        if custom.on_use: target = custom.on_use.get("target", {}); target_type.set(target.get("type", "self")); fields["radius"].set(str(target.get("radius", ""))); fields["angle"].set(str(target.get("angle", ""))); fields["width"].set(str(target.get("width", ""))); effect = (custom.on_use.get("effects") or [{}])[0]; fields["target"].set(effect.get("kind", "heal")); fields["effect_id"].set(effect.get("id", "")); fields["effect_duration"].set(str(effect.get("duration_sec", ""))); fields["effect_level"].set(str(effect.get("level", ""))); fields["heal"].set(str(effect.get("amount", "")))
        edit_state["restoring"] = previous_restoring

    def load_loot_row(row):
        loot_selected["index"] = loot_rows.index(row) if row in loot_rows else None
        fields["pool"].set(row.pool); fields["rarity"].set(str(row.rarity)); fields["amount"].set(str(row.amount)); fields["weight"].set(str(row.weight))

    def refresh_loot_table():
        loot_table.delete(*loot_table.get_children())
        for index, row in enumerate(loot_rows):
            probability = simulate_item_probability(items, selected["item"].id if selected["item"] else "", row.pool)
            loot_table.insert("", "end", iid=str(index), values=(row.pool, row.rarity, row.amount, f"{row.weight:g}", f"{probability:.1%}"))

    def commit_selected_loot():
        index = loot_selected["index"]
        if index is None or index >= len(loot_rows): return
        row = loot_rows[index]; row.pool = fields["pool"].get(); row.rarity = int(fields["rarity"].get() or 1); row.amount = int(fields["amount"].get() or 1); row.weight = float(fields["weight"].get() or 0); refresh_loot_table()

    def add_loot_row():
        commit_selected_loot(); loot_rows.append(LootEntry("common", 1, 1, 0.5)); refresh_loot_table(); loot_table.selection_set(str(len(loot_rows) - 1)); load_loot_row(loot_rows[-1])
    def remove_loot_row():
        selection = loot_table.selection()
        if selection: loot_rows.pop(int(selection[0])); refresh_loot_table()
    loot_table.bind("<<TreeviewSelect>>", lambda _event: (commit_selected_loot(), load_loot_row(loot_rows[int(loot_table.selection()[0])])) if loot_table.selection() else None)

    def asset_files():
        files = {}
        for item in items:
            source = asset_sources.get(id(item));
            if source and item.kind == "custom": files[f"tools/items/icons/{item.key}.png"] = Path(source).read_bytes(); files[f"resource_pack/textures/items/tbr_{item.key}.png"] = Path(source).read_bytes()
        return files

    def preview():
        commit_selected_loot(); write_form_to_item(); files, conflicts = guarded_files(root, items, sources); entries = plan(root, {**files, **asset_files()}); preview_files.delete(0, "end"); preview_diffs.clear()
        for entry in entries:
            relative = entry.path.relative_to(root).as_posix(); preview_files.insert("end", f"{entry.kind}: {relative}")
            preview_diffs[f"{entry.kind}: {relative}"] = unified_diff(relative, entry.old_content, entry.new_content)
        body = [f"CONFLICT: {path}" for path in conflicts]
        if any(item.custom and item.custom.on_use for item in items):
            body.extend(["", "main.jsへ手動追加する行:", 'import "./item/custom/tbrAbility.js";', 'import { setAbilityContext } from "./item/custom/abilityContext.js";', "setAbilityContext({ /* TBRの既存Player/Combat/Zone判定を接続 */ });"])
        if body:
            preview_files.insert("end", "-- conflicts --")
        if preview_files.size():
            preview_files.selection_set(0); show_preview_diff()
        preview_text.configure(state="normal"); preview_text.insert("end", "\n".join(body)); preview_text.configure(state="disabled"); notebook.select(preview)

    def check_save_safety():
        invalid = [item.key or "(空)" for item in items if not item.key.strip() or not item.id.strip()]
        if invalid:
            raise ValueError("空のkeyまたはIDを持つアイテムがあるため保存できません: " + ", ".join(invalid))
        previous = load_items(root)
        if len(items) < len(previous) and not edit_state["allow_count_reduction"]:
            if not messagebox.askyesno("件数減少の確認", f"保存前よりアイテム数が{len(previous)}件から{len(items)}件に減ります。続行しますか？"):
                return False
        return True

    def save():
        try:
            commit_selected_loot(); write_form_to_item()
            if not check_save_safety():
                return
            save_items(root, items); edit_state["allow_count_reduction"] = False
            assets = asset_files()
            if assets: apply(root, plan(root, assets))
            status.set("入力データと選択済みアイコンを保存しました"); edit_state["dirty"] = False; update_title()
        except Exception as exc: messagebox.showerror("保存エラー", str(exc))

    def generate():
        try:
            preview(); issues = validate(items)
            if any(level == "error" for _, level, _ in issues): raise ValueError("検証エラーがあります")
            if not check_save_safety():
                return
            files, conflicts = guarded_files(root, items, sources); entries = plan(root, {**files, **asset_files()})
            if messagebox.askyesno("生成確認", "プレビューの内容をバックアップ後に書き込みますか？"): apply(root, entries); save_items(root, items); edit_state["allow_count_reduction"] = False; status.set("生成しました"); edit_state["dirty"] = False; update_title()
        except Exception as exc: messagebox.showerror("生成エラー", str(exc))

    def new_item(item_kind, template="empty"):
        if item_kind == "custom":
            item = template_item(template, items)
        else:
            key = suggest_key("minecraft:bread", items); item = Item(key, True, "vanilla", "minecraft:bread", "", ["food"], [LootEntry("common", 1, 1, 0.5)], None)
        write_form_to_item(); items.append(item); editor_state.select_item(item); load_item(item, flush=False); refresh()

    def new_custom():
        dialog = tk.Toplevel(window); dialog.title("Customテンプレート"); dialog.transient(window); dialog.grab_set(); choice = tk.StringVar(dialog, value="empty")
        ttk.Label(dialog, text="テンプレートを選択").pack(padx=16, pady=(16, 4)); box = ttk.Combobox(dialog, textvariable=choice, state="readonly", values=("empty", "food", "healing", "ability")); box.pack(padx=16, pady=4)
        ttk.Button(dialog, text="作成", command=lambda: (dialog.destroy(), new_item("custom", choice.get()))).pack(pady=12)
    def duplicate_item():
        if selected["item"]:
            write_form_to_item(); item = copy.deepcopy(selected["item"]); item.key = suggest_key(item.key, items); item.id = f"{item.id}_copy"; items.append(item); editor_state.select_item(item); load_item(item, flush=False); refresh()

    def show_history():
        dialog = tk.Toplevel(window); dialog.title("履歴"); dialog.geometry("600x400"); listbox = tk.Listbox(dialog); listbox.pack(fill="both", expand=True, padx=10, pady=10); entries = history_entries(root)
        for entry in entries: listbox.insert("end", f"{entry['name']} ({entry['files']} files)")
        def restore_selected():
            selected_index = listbox.curselection()
            if not selected_index or not messagebox.askyesno("履歴復元", "現在のitems.jsonを保存してから復元しますか？"):
                return
            save(); restore_history(root, entries[selected_index[0]]["path"]); items[:] = load_items(root); editor_state.items = items; editor_state.select(0 if items else None); selected["item"] = editor_state.selected; load_item(selected["item"], flush=False) if selected["item"] else None; refresh(); status.set("履歴を復元して画面を更新しました"); dialog.destroy()
        ttk.Button(dialog, text="選択した履歴を復元", command=restore_selected).pack(pady=(0, 10))
    def delete_item():
        if not selected["item"] or not messagebox.askyesno("削除確認", "items.jsonから削除しますか？"):
            return
        write_form_to_item()
        editor_state.select_item(selected["item"])
        editor_state.remove_selected()
        selected["item"] = editor_state.selected
        edit_state["allow_count_reduction"] = True
        refresh()
        if selected["item"]:
            load_item(selected["item"], flush=False)

    tree.bind("<<TreeviewSelect>>", lambda _event: load_item(items[int(tree.selection()[0])], flush=True) if tree.selection() else None); search.trace_add("write", lambda *_: refresh()); filter_kind.trace_add("write", lambda *_: refresh()); filter_tag.trace_add("write", lambda *_: refresh()); filter_pool.trace_add("write", lambda *_: refresh()); filter_state.trace_add("write", lambda *_: refresh())
    footer = ttk.Frame(window); footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=8); ttk.Button(footer, text="新規Custom", command=new_custom).pack(side="left", padx=3); ttk.Button(footer, text="新規Vanilla", command=lambda: new_item("vanilla")).pack(side="left", padx=3); ttk.Button(footer, text="複製", command=duplicate_item).pack(side="left", padx=3); ttk.Button(footer, text="削除", command=delete_item).pack(side="left", padx=3); ttk.Button(footer, text="履歴", command=show_history).pack(side="left", padx=3); ttk.Button(footer, text="元に戻す", command=undo).pack(side="left", padx=3); ttk.Button(footer, text="やり直す", command=redo).pack(side="left", padx=3); ttk.Button(footer, text="保存", command=save).pack(side="left", padx=3); ttk.Button(footer, text="生成プレビュー", command=preview).pack(side="left", padx=3); ttk.Button(footer, text="確認して生成", command=generate).pack(side="left", padx=3); ttk.Label(footer, textvariable=status).pack(side="left", padx=12)
    for variable in fields.values(): variable.trace_add("write", mark_dirty)
    kind.trace_add("write", mark_dirty); enabled.trace_add("write", mark_dirty); food_enabled.trace_add("write", mark_dirty); always_eat.trace_add("write", mark_dirty); ability_enabled.trace_add("write", mark_dirty); trigger.trace_add("write", mark_dirty); target_type.trace_add("write", mark_dirty)
    window.bind("<Control-s>", lambda _event: (save(), "break")[-1]); window.bind("<Control-z>", lambda _event: (undo(), "break")[-1]); window.bind("<Control-y>", lambda _event: (redo(), "break")[-1])
    refresh()
    if items: tree.selection_set("0"); load_item(items[0], flush=False)
    draw_ability_preview()
    def on_close():
        if edit_state["dirty"]:
            decision = messagebox.askyesnocancel("未保存の変更", "未保存の変更を保存して終了しますか？")
            if decision is None:
                return
            if decision:
                save()
        save_settings(root, {"window_geometry": window.geometry(), "last_key": selected["item"].key if selected["item"] else "", "filters": {"kind": filter_kind.get(), "tag": filter_tag.get(), "pool": filter_pool.get(), "state": filter_state.get()}})
        window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
