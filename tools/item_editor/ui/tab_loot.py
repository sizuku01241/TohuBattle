"""出現設定タブの選択肢。"""

POOL_VALUES = ("common", "supply", "ground")
RARITY_VALUES = tuple(str(value) for value in range(1, 8))


def build_loot_tab(frame, ttk, entry, fields, add_row, remove_row):
    """出現設定タブの表と編集欄を構築する。"""
    ttk.Label(frame, text="複数行を保持します。行を切り替えても自動反映されます。", foreground="#555").grid(row=0, column=0, columnspan=4, sticky="w", pady=4)
    table = ttk.Treeview(frame, columns=("pool", "rarity", "amount", "weight", "prob"), show="headings", height=8)
    for column, title, width in (("pool", "pool", 100), ("rarity", "★", 50), ("amount", "個数", 70), ("weight", "出現確率(0〜1)", 130), ("prob", "1チェスト確率", 130)):
        table.heading(column, text=title)
        table.column(column, width=width)
    table.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=6)
    frame.rowconfigure(1, weight=1)
    matrix = ttk.Treeview(frame, columns=("pool", "r1", "r2", "r3", "r4", "r5", "r6", "r7"), show="headings", height=4)
    for column, title in (("pool", "pool"), *((f"r{i}", f"★{i}") for i in range(1, 8))):
        matrix.heading(column, text=title)
        matrix.column(column, width=80, anchor="center")
    matrix.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(10, 4))
    ttk.Label(frame, text="マトリクス: 件数 / 出現確率合計。セルをクリックすると、そのpool・レア度の行を追加します。", foreground="#555").grid(row=5, column=0, columnspan=4, sticky="w")
    ttk.Button(frame, text="行を追加", command=add_row).grid(row=2, column=0, padx=3, pady=5, sticky="w")
    ttk.Button(frame, text="選択行を削除", command=remove_row).grid(row=2, column=1, padx=3, pady=5, sticky="w")
    form = ttk.Frame(frame)
    form.grid(row=3, column=0, columnspan=4, sticky="ew")
    form.columnconfigure(1, weight=1)
    ttk.Label(form, text="選択行を編集").grid(row=0, column=0, columnspan=4, sticky="w")
    ttk.Label(form, text="pool").grid(row=1, column=0)
    ttk.Combobox(form, textvariable=fields["pool"], values=POOL_VALUES, state="readonly", width=12).grid(row=1, column=1)
    ttk.Label(form, text="★").grid(row=1, column=2)
    ttk.Combobox(form, textvariable=fields["rarity"], values=RARITY_VALUES, state="readonly", width=8).grid(row=1, column=3)
    entry(form, 2, "個数", fields["amount"])
    entry(form, 3, "出現確率(0〜1)", fields["weight"])
    return table, matrix
