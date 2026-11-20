"""基本タブで使う選択肢と表示ルール。"""

KIND_VALUES = ("custom", "vanilla")


def filter_vanilla_candidates(candidates, query):
    """入力文字列でVanilla ID候補を絞り込む。手入力自体はUI側で許可する。"""
    normalized = str(query or "").strip().lower()
    values = tuple(sorted(candidates))
    if not normalized:
        return values
    return tuple(value for value in values if normalized in value.lower())


def build_basic_tab(frame, ttk, entry, fields, kind, enabled, tag_vars, tags, stack_limits, icon_label, choose_icon):
    """基本タブのウィジェットを構築して参照を返す。"""
    entry(frame, 0, "内部ID", fields["key"])
    ttk.Label(frame, text="種別").grid(row=1, column=0, sticky="w", padx=5, pady=4)
    kind_box = ttk.Combobox(frame, textvariable=kind, values=KIND_VALUES, state="readonly", width=22)
    kind_box.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
    ttk.Label(frame, text="アイテムID").grid(row=2, column=0, sticky="w", padx=5, pady=4)
    id_box = ttk.Combobox(frame, textvariable=fields["id"], values=tuple(sorted(stack_limits)), state="normal", width=25)
    id_box.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
    ttk.Label(frame, text="候補から選択できます。未知のVanilla IDは手入力できますが検証警告になります。", foreground="#666").grid(row=2, column=2, sticky="w", padx=5)
    entry(frame, 3, "表示名", fields["name"])
    ttk.Checkbutton(frame, text="有効", variable=enabled).grid(row=4, column=1, sticky="w", padx=5, pady=4)
    ttk.Label(frame, text="タグ").grid(row=5, column=0, sticky="nw", padx=5, pady=4)
    tag_frame = ttk.Frame(frame)
    tag_frame.grid(row=5, column=1, sticky="w")
    for index, tag in enumerate(tags):
        ttk.Checkbutton(tag_frame, text=tag, variable=tag_vars[tag]).grid(row=index // 4, column=index % 4, sticky="w", padx=4)
    icon_preview = ttk.Label(frame, text="プレビューなし")
    ttk.Button(frame, text="PNGファイルを選択", command=choose_icon).grid(row=6, column=0, padx=5, pady=8)
    ttk.Label(frame, textvariable=icon_label).grid(row=6, column=1, sticky="w", padx=5)
    icon_preview.grid(row=6, column=2, padx=8)
    ttk.Label(frame, text="音声ファイル: 未対応（Bedrock定義確認待ち）", foreground="#996600").grid(row=7, column=0, columnspan=3, sticky="w", padx=5, pady=8)
    return {"id_box": id_box, "icon_label": icon_label, "icon_preview": icon_preview}
