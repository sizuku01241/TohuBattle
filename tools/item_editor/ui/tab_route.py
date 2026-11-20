def build_route_tab(frame, tk, ttk, items, simulate):
    pool = tk.StringVar(value="common"); rarity = tk.StringVar(value="1"); trials = tk.StringVar(value="1000"); result = tk.StringVar(value="チェストスロット上限: 通常3 / サプライ3。概算表示")
    ttk.Label(frame, text="pool").grid(row=0, column=0); ttk.Combobox(frame, textvariable=pool, values=("common", "supply"), state="readonly").grid(row=0, column=1)
    ttk.Label(frame, text="レア度").grid(row=0, column=2); ttk.Combobox(frame, textvariable=rarity, values=tuple(str(i) for i in range(1, 8)), state="readonly", width=5).grid(row=0, column=3)
    ttk.Label(frame, text="試行回数").grid(row=0, column=4); ttk.Entry(frame, textvariable=trials, width=8).grid(row=0, column=5)
    chest = ttk.Frame(frame); chest.grid(row=1, column=0, columnspan=6, pady=4)
    cells = [tk.StringVar(value="空") for _ in range(27)]
    for index, cell in enumerate(cells): ttk.Label(chest, textvariable=cell, relief="groove", width=14, anchor="center").grid(row=index // 9, column=index % 9, padx=1, pady=1)
    table = ttk.Treeview(frame, columns=("id", "name", "weight", "prob", "expected"), show="headings", height=12)
    for key, label in zip(table["columns"], ("ID", "表示名", "weight", "実際の出現率", "期待個数")): table.heading(key, text=label)
    table.grid(row=3, column=0, columnspan=6, sticky="nsew", pady=8)
    ttk.Label(frame, text="ground は現在の生成対象外。ゲーム実装に従い common/supply のみ表示。実機確認待ち", foreground="#996600").grid(row=4, column=0, columnspan=6, sticky="w")
    def run():
        table.delete(*table.get_children())
        try: data = simulate(items, pool.get(), int(rarity.get()), 3, int(trials.get()), 1)
        except (TypeError, ValueError): result.set("入力値を確認"); return
        result.set("概算（JS sort(() => random()-0.5) はPythonで完全再現不可）")
        for row in data["rows"]: table.insert("", "end", values=(row["id"], row["name"], row["weight"], f'{row["probability"]:.1%}', f'{row["expected"]:.3f}'))
    def open_chest():
        data = simulate(items, pool.get(), int(rarity.get()), 3, 1, 1)
        for cell in cells: cell.set("空")
        for index, row in enumerate([r for r in data["rows"] if r["probability"] > 0][:3]): cells[index].set(f'{row["name"]}\n×1')
    ttk.Button(frame, text="チェストを開ける", command=open_chest).grid(row=2, column=0, pady=4)
    ttk.Button(frame, text="N回試行", command=run).grid(row=2, column=1, pady=4); ttk.Label(frame, textvariable=result).grid(row=2, column=2, columnspan=4, sticky="w")
