import copy
from pathlib import Path

from ..generators.loot_js import simulate_item_probability
from ..models import CustomSpec, Item, LootEntry
from ..form_logic import apply_form_to_item, parse_float, parse_int
from ..store import load_items, load_settings, save_items, save_settings
from ..state import EditorState
from ..validators import STACK_LIMITS, TAGS, validate
from ..writer import apply, plan
from ..ui_logic import history_entries, loot_matrix, restore_history, suggest_key, template_item
from .preview import build_preview_tab, unified_diff
from .item_list import build_filter_header, build_item_tree
from .history_dialog import open_history_dialog
from .tab_ability import build_ability_tab, draw_ability_preview
from .tab_basic import build_basic_tab
from .tab_loot import build_loot_tab
from .tab_use import build_use_tab


def launch_gui(root: Path) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from ..main import ensure_items, generate_files, source_texts, guarded_files

    settings = load_settings(root)
    window = tk.Tk(); window.title("TBR-001 アイテム管理GUI"); window.geometry(settings.get("window_geometry", "1350x850")); window.minsize(1100, 700)
    items = ensure_items(root); editor_state = EditorState(items); sources = source_texts(root); asset_sources = {}; search = tk.StringVar(master=window); filter_kind = tk.StringVar(master=window, value="すべて"); filter_tag = tk.StringVar(master=window, value="すべて"); filter_pool = tk.StringVar(master=window, value="すべて"); filter_state = tk.StringVar(master=window, value="すべて"); status = tk.StringVar(master=window, value="自動取り込み済み。項目を切り替えると編集内容を反映します")
    ui_guard = {"restoring": False, "allow_count_reduction": False}
    saved_filters = settings.get("filters", {})
    filter_kind.set(saved_filters.get("kind", "すべて")); filter_tag.set(saved_filters.get("tag", "すべて")); filter_pool.set(saved_filters.get("pool", "すべて")); filter_state.set(saved_filters.get("state", "すべて"))
    window.columnconfigure(1, weight=1); window.rowconfigure(1, weight=1)
    fields = {key: tk.StringVar() for key in ("key", "id", "name", "pool", "rarity", "amount", "weight", "nutrition", "saturation", "duration", "movement", "animation", "target", "radius", "angle", "width", "effect_id", "effect_duration", "effect_level", "heal")}
    kind = tk.StringVar(); enabled = tk.BooleanVar(); food_enabled = tk.BooleanVar(); always_eat = tk.BooleanVar(); ability_enabled = tk.BooleanVar(); trigger = tk.StringVar(value="tap"); target_type = tk.StringVar(value="self"); tag_vars = {tag: tk.BooleanVar() for tag in TAGS}; icon_label = tk.StringVar(value="未対応"); preview_text = None
    loot_rows = []; loot_selected = {"index": None}

    def entry(frame, row, label, var, column=0):
        ttk.Label(frame, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=4); widget = ttk.Entry(frame, textvariable=var, width=25); widget.grid(row=row, column=column + 1, sticky="ew", padx=5, pady=4); return widget

    filter_variables = {"search": search, "kind": filter_kind, "tag": filter_tag, "pool": filter_pool, "state": filter_state}
    build_filter_header(window, tk, ttk, filter_variables, TAGS)
    tree = build_item_tree(window, ttk)
    editor = ttk.Frame(window); editor.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5); editor.rowconfigure(0, weight=1); editor.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(editor); notebook.grid(row=0, column=0, sticky="nsew")
    basic = ttk.Frame(notebook, padding=12); loot = ttk.Frame(notebook, padding=12); food = ttk.Frame(notebook, padding=12); ability = ttk.Frame(notebook, padding=12); equip = ttk.Frame(notebook, padding=12); preview = ttk.Frame(notebook, padding=8)
    for frame, title in ((basic, "基本"), (loot, "出現設定"), (food, "食べ物/使用"), (ability, "右クリック"), (equip, "装備(未対応)"), (preview, "プレビュー")): notebook.add(frame, text=title)
    for frame in (basic, loot, food, ability, equip): frame.columnconfigure(1, weight=1)

    basic_widgets = build_basic_tab(basic, ttk, entry, fields, kind, enabled, tag_vars, TAGS, STACK_LIMITS, icon_label, lambda: choose_icon())
    id_box = basic_widgets["id_box"]
    icon_preview = basic_widgets["icon_preview"]

    loot_table, matrix = build_loot_tab(loot, ttk, entry, fields, lambda: add_loot_row(), lambda: remove_loot_row())

    build_use_tab(food, ttk, entry, fields, food_enabled, always_eat)

    ability_canvas = build_ability_tab(ability, tk, ttk, entry, fields, ability_enabled, trigger, target_type)

    def refresh_ability_preview(*_args):
        draw_ability_preview(ability_canvas, target_type.get(), fields["radius"].get(), fields["width"].get())
    for variable in (target_type, fields["radius"], fields["angle"], fields["width"]): variable.trace_add("write", refresh_ability_preview)

    ttk.Label(equip, text="装備タブは設計書により未対応です", foreground="#996600").grid(row=0, column=0, columnspan=2, sticky="w"); ttk.Label(equip, text="Minecraftの装備コンポーネント確認後に有効化します。", foreground="#666").grid(row=1, column=0, columnspan=2, sticky="w")
    preview_files, preview_text = build_preview_tab(preview, tk)
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
        if editor_state.selected: asset_sources[id(editor_state.selected)] = path; icon_label.set(Path(path).name); update_icon_preview(path); refresh()

    validation_label = ttk.Label(window, text="", anchor="w")
    validation_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

    def update_title():
        window.title(("*" if editor_state.dirty else "") + "TBR-001 アイテム管理GUI")

    def mark_dirty(*_args):
        if not ui_guard["restoring"]:
            editor_state.mark_dirty()
            update_title()

    def undo():
        editor_state.undo()
        if editor_state.selected:
            load_item(editor_state.selected, flush=False)
        refresh()
        update_title()

    def redo():
        editor_state.redo()
        if editor_state.selected:
            load_item(editor_state.selected, flush=False)
        refresh()
        update_title()

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
        loot_rows.append(LootEntry(row, rarity, 1, 0.5)); refresh_loot_table(); loot_table.selection_set(str(len(loot_rows) - 1)); load_loot_row(loot_rows[-1]); try_write_form_to_item()
    matrix.bind("<Button-1>", add_matrix_row)
    validation_label.bind("<Button-1>", lambda _event: show_validation())

    def write_form_to_item():
        item = editor_state.selected
        if not item or item not in items: return
        commit_selected_loot()
        before = editor_state.snapshot()
        values = {"key": fields["key"].get(), "id": fields["id"].get(), "name": fields["name"].get(), "kind": kind.get(), "enabled": enabled.get(), "food_enabled": food_enabled.get(), "nutrition": fields["nutrition"].get(), "saturation": fields["saturation"].get(), "duration": fields["duration"].get(), "movement": fields["movement"].get(), "animation": fields["animation"].get(), "always_eat": always_eat.get(), "ability_enabled": ability_enabled.get(), "trigger": trigger.get(), "target_type": target_type.get(), "radius": fields["radius"].get(), "angle": fields["angle"].get(), "width": fields["width"].get(), "effect_kind": fields["target"].get(), "effect_id": fields["effect_id"].get(), "effect_duration": fields["effect_duration"].get(), "effect_level": fields["effect_level"].get(), "heal": fields["heal"].get()}
        icon = f"tools/items/icons/{values['key']}.png" if asset_sources.get(id(item)) else None
        changed = apply_form_to_item(item, values, loot_rows, [tag for tag, var in tag_vars.items() if var.get()], icon)
        items[editor_state.selected_index] = changed
        editor_state.record_change(before)
        refresh()

    def try_write_form_to_item():
        try:
            write_form_to_item()
        except ValueError as error:
            messagebox.showerror("入力値エラー", str(error))
            return False
        return True

    def load_item(item, flush=False):
        previous_restoring = ui_guard["restoring"]
        ui_guard["restoring"] = True
        if flush:
            ui_guard["restoring"] = previous_restoring
            if not try_write_form_to_item():
                ui_guard["restoring"] = previous_restoring
                if editor_state.selected_index is not None:
                    tree.selection_set(str(editor_state.selected_index))
                return
            ui_guard["restoring"] = True
        if item not in items:
            ui_guard["restoring"] = previous_restoring
            return
        editor_state.select_item(item)
        fields["key"].set(item.key); fields["id"].set(item.id); fields["name"].set(item.display_name); kind.set(item.kind); enabled.set(item.enabled)
        for tag, var in tag_vars.items(): var.set(tag in item.tags)
        loot_rows.clear(); loot_rows.extend(copy.deepcopy(item.loot)); refresh_loot_table()
        entry = loot_rows[0] if loot_rows else LootEntry("common", 1, 1, 0.5); load_loot_row(entry)
        custom = item.custom or CustomSpec(); icon_label.set(Path(custom.icon).name if custom.icon else "未選択"); icon_source = asset_sources.get(id(item)); update_icon_preview(icon_source) if icon_source else icon_preview.configure(image="", text="プレビューなし"); food_enabled.set(bool(custom.food)); fields["nutrition"].set(str((custom.food or {}).get("nutrition", ""))); fields["saturation"].set(str((custom.food or {}).get("saturation_modifier", ""))); fields["duration"].set(str((custom.use or {}).get("duration_sec", "1.6"))); fields["movement"].set(str((custom.use or {}).get("movement_modifier", "0.35"))); fields["animation"].set((custom.use or {}).get("animation", "eat")); ability_enabled.set(bool(custom.on_use));
        if custom.on_use: target = custom.on_use.get("target", {}); target_type.set(target.get("type", "self")); fields["radius"].set(str(target.get("radius", ""))); fields["angle"].set(str(target.get("angle", ""))); fields["width"].set(str(target.get("width", ""))); effect = (custom.on_use.get("effects") or [{}])[0]; fields["target"].set(effect.get("kind", "heal")); fields["effect_id"].set(effect.get("id", "")); fields["effect_duration"].set(str(effect.get("duration_sec", ""))); fields["effect_level"].set(str(effect.get("level", ""))); fields["heal"].set(str(effect.get("amount", "")))
        ui_guard["restoring"] = previous_restoring

    def load_loot_row(row):
        loot_selected["index"] = loot_rows.index(row) if row in loot_rows else None
        fields["pool"].set(row.pool); fields["rarity"].set(str(row.rarity)); fields["amount"].set(str(row.amount)); fields["weight"].set(str(row.weight))

    def refresh_loot_table():
        loot_table.delete(*loot_table.get_children())
        for index, row in enumerate(loot_rows):
            probability = simulate_item_probability(items, editor_state.selected.id if editor_state.selected else "", row.pool)
            loot_table.insert("", "end", iid=str(index), values=(row.pool, row.rarity, row.amount, f"{row.weight:g}", f"{probability:.1%}"))

    def commit_selected_loot():
        index = loot_selected["index"]
        if index is None or index >= len(loot_rows): return
        row = loot_rows[index]
        row.pool = fields["pool"].get()
        row.rarity = parse_int(fields["rarity"].get(), "レア度", 1)
        row.amount = parse_int(fields["amount"].get(), "個数", 1)
        row.weight = parse_float(fields["weight"].get(), "出現確率", 0)
        refresh_loot_table()

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
        try:
            commit_selected_loot()
        except ValueError as error:
            messagebox.showerror("入力値エラー", str(error))
            return
        if not try_write_form_to_item():
            return
        files, conflicts = guarded_files(root, items, sources); entries = plan(root, {**files, **asset_files()}); preview_files.delete(0, "end"); preview_diffs.clear()
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
        if len(items) < len(previous) and not ui_guard["allow_count_reduction"]:
            if not messagebox.askyesno("件数減少の確認", f"保存前よりアイテム数が{len(previous)}件から{len(items)}件に減ります。続行しますか？"):
                return False
        return True

    def save():
        try:
            commit_selected_loot(); write_form_to_item()
            if not check_save_safety():
                return
            save_items(root, items); ui_guard["allow_count_reduction"] = False
            assets = asset_files()
            if assets: apply(root, plan(root, assets))
            status.set("入力データと選択済みアイコンを保存しました"); editor_state.clear_dirty(); update_title()
        except Exception as exc: messagebox.showerror("保存エラー", str(exc))

    def generate():
        try:
            preview(); issues = validate(items)
            if any(level == "error" for _, level, _ in issues): raise ValueError("検証エラーがあります")
            if not check_save_safety():
                return
            files, conflicts = guarded_files(root, items, sources); entries = plan(root, {**files, **asset_files()})
            if messagebox.askyesno("生成確認", "プレビューの内容をバックアップ後に書き込みますか？"): apply(root, entries); save_items(root, items); ui_guard["allow_count_reduction"] = False; status.set("生成しました"); editor_state.clear_dirty(); update_title()
        except Exception as exc: messagebox.showerror("生成エラー", str(exc))

    def new_item(item_kind, template="empty"):
        if item_kind == "custom":
            item = template_item(template, items)
        else:
            key = suggest_key("minecraft:bread", items); item = Item(key, True, "vanilla", "minecraft:bread", "", ["food"], [LootEntry("common", 1, 1, 0.5)], None)
        if try_write_form_to_item():
            editor_state.add(item); load_item(item, flush=False); refresh()

    def new_custom():
        dialog = tk.Toplevel(window); dialog.title("Customテンプレート"); dialog.transient(window); dialog.grab_set(); choice = tk.StringVar(dialog, value="empty")
        ttk.Label(dialog, text="テンプレートを選択").pack(padx=16, pady=(16, 4)); box = ttk.Combobox(dialog, textvariable=choice, state="readonly", values=("empty", "food", "healing", "ability")); box.pack(padx=16, pady=4)
        ttk.Button(dialog, text="作成", command=lambda: (dialog.destroy(), new_item("custom", choice.get()))).pack(pady=12)
    def duplicate_item():
        if editor_state.selected:
            if try_write_form_to_item():
                item = copy.deepcopy(editor_state.selected); item.key = suggest_key(item.key, items); item.id = f"{item.id}_copy"; editor_state.add(item); load_item(item, flush=False); refresh()

    def show_history():
        entries = history_entries(root)
        def restore_selected(dialog, listbox):
            selected_index = listbox.curselection()
            if not selected_index or not messagebox.askyesno("履歴復元", "現在のitems.jsonを保存してから復元しますか？"):
                return
            save(); restore_history(root, entries[selected_index[0]]["path"]); editor_state.replace_items(load_items(root), dirty=False); load_item(editor_state.selected, flush=False) if editor_state.selected else None; refresh(); status.set("履歴を復元して画面を更新しました"); dialog.destroy()
        open_history_dialog(window, tk, ttk, entries, restore_selected)
    def delete_item():
        if not editor_state.selected or not messagebox.askyesno("削除確認", "items.jsonから削除しますか？"):
            return
        if not try_write_form_to_item():
            return
        editor_state.remove_selected()
        ui_guard["allow_count_reduction"] = True
        refresh()
        if editor_state.selected:
            load_item(editor_state.selected, flush=False)

    tree.bind("<<TreeviewSelect>>", lambda _event: load_item(items[int(tree.selection()[0])], flush=True) if tree.selection() else None); search.trace_add("write", lambda *_: refresh()); filter_kind.trace_add("write", lambda *_: refresh()); filter_tag.trace_add("write", lambda *_: refresh()); filter_pool.trace_add("write", lambda *_: refresh()); filter_state.trace_add("write", lambda *_: refresh())
    footer = ttk.Frame(window); footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=8); ttk.Button(footer, text="新規Custom", command=new_custom).pack(side="left", padx=3); ttk.Button(footer, text="新規Vanilla", command=lambda: new_item("vanilla")).pack(side="left", padx=3); ttk.Button(footer, text="複製", command=duplicate_item).pack(side="left", padx=3); ttk.Button(footer, text="削除", command=delete_item).pack(side="left", padx=3); ttk.Button(footer, text="履歴", command=show_history).pack(side="left", padx=3); ttk.Button(footer, text="元に戻す", command=undo).pack(side="left", padx=3); ttk.Button(footer, text="やり直す", command=redo).pack(side="left", padx=3); ttk.Button(footer, text="保存", command=save).pack(side="left", padx=3); ttk.Button(footer, text="生成プレビュー", command=preview).pack(side="left", padx=3); ttk.Button(footer, text="確認して生成", command=generate).pack(side="left", padx=3); ttk.Label(footer, textvariable=status).pack(side="left", padx=12)
    for variable in fields.values(): variable.trace_add("write", mark_dirty)
    kind.trace_add("write", mark_dirty); enabled.trace_add("write", mark_dirty); food_enabled.trace_add("write", mark_dirty); always_eat.trace_add("write", mark_dirty); ability_enabled.trace_add("write", mark_dirty); trigger.trace_add("write", mark_dirty); target_type.trace_add("write", mark_dirty)
    window.bind("<Control-s>", lambda _event: (save(), "break")[-1]); window.bind("<Control-z>", lambda _event: (undo(), "break")[-1]); window.bind("<Control-y>", lambda _event: (redo(), "break")[-1])
    refresh()
    if items: tree.selection_set("0"); load_item(items[0], flush=False)
    refresh_ability_preview()
    def on_close():
        if editor_state.dirty:
            decision = messagebox.askyesnocancel("未保存の変更", "未保存の変更を保存して終了しますか？")
            if decision is None:
                return
            if decision:
                save()
        save_settings(root, {"window_geometry": window.geometry(), "last_key": editor_state.selected.key if editor_state.selected else "", "filters": {"kind": filter_kind.get(), "tag": filter_tag.get(), "pool": filter_pool.get(), "state": filter_state.get()}})
        window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
