"""アイテム一覧と検索・フィルター部品。"""


def build_filter_header(parent, tk, ttk, variables, tags):
    """一覧上部の検索・フィルターを構築する。"""
    header = ttk.Frame(parent)
    header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
    ttk.Label(header, text="検索").pack(side="left")
    ttk.Entry(header, textvariable=variables["search"], width=24).pack(side="left", padx=6)
    choices = (
        ("種別", variables["kind"], ("すべて", "custom", "vanilla"), 9),
        ("タグ", variables["tag"], ("すべて", *sorted(tags)), 11),
        ("pool", variables["pool"], ("すべて", "common", "supply", "ground"), 9),
        ("状態", variables["state"], ("すべて", "有効", "無効", "エラーあり"), 11),
    )
    for label, variable, values, width in choices:
        ttk.Label(header, text=label).pack(side="left")
        ttk.Combobox(header, textvariable=variable, values=values, state="readonly", width=width).pack(side="left", padx=3)
    return header


def build_item_tree(parent, ttk):
    """一覧Treeviewとスクロールバーを構築する。"""
    frame = ttk.LabelFrame(parent, text="登録アイテム")
    frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=("kind", "id", "name", "loot", "state"), show="headings", selectmode="browse")
    for column, title, width in (("kind", "種別", 70), ("id", "ID", 190), ("name", "名前", 120), ("loot", "出現設定", 100), ("state", "状態", 60)):
        tree.heading(column, text=title)
        tree.column(column, width=width)
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    return tree
