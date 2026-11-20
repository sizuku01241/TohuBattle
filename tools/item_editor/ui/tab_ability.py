"""右クリック能力タブの選択肢。"""

TARGET_VALUES = ("self", "cone", "circle", "line", "look")
EFFECT_VALUES = ("heal", "potion_effect")


def build_ability_tab(frame, tk, ttk, entry, fields, ability_enabled, trigger, target_type):
    """右クリック能力タブの入力欄と範囲プレビューを構築する。"""
    ttk.Checkbutton(frame, text="右クリック能力を有効化", variable=ability_enabled).grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(frame, text="発動").grid(row=1, column=0, sticky="w", padx=5, pady=4)
    ttk.Combobox(frame, textvariable=trigger, values=("tap", "hold"), state="readonly", width=22).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Label(frame, text="対象形状").grid(row=2, column=0, sticky="w", padx=5, pady=4)
    ttk.Combobox(frame, textvariable=target_type, values=TARGET_VALUES, state="readonly", width=22).grid(row=2, column=1, sticky="ew", padx=5)
    entry(frame, 3, "半径", fields["radius"])
    entry(frame, 4, "角度", fields["angle"])
    entry(frame, 5, "幅", fields["width"])
    ttk.Label(frame, text="効果kind").grid(row=6, column=0, sticky="w", padx=5)
    ttk.Combobox(frame, textvariable=fields["target"], values=EFFECT_VALUES, state="readonly", width=22).grid(row=6, column=1, sticky="ew", padx=5)
    entry(frame, 7, "効果ID", fields["effect_id"])
    entry(frame, 8, "効果時間(秒)", fields["effect_duration"])
    entry(frame, 9, "効果レベル", fields["effect_level"])
    entry(frame, 10, "回復量", fields["heal"])
    ttk.Label(frame, text="対象判定はabilityContext経由。ダメージ/ノックバック/発火は未対応。", foreground="#996600").grid(row=11, column=0, columnspan=2, sticky="w", pady=10)
    canvas = tk.Canvas(frame, width=360, height=220, background="#20242b", highlightthickness=0)
    canvas.grid(row=0, column=2, rowspan=12, padx=18, pady=8, sticky="nsew")
    return canvas


def draw_ability_preview(canvas, target_type, radius_value, width_value):
    """能力範囲の簡易プレビューを描画する。"""
    canvas.delete("all")
    center_x, center_y = 180, 110
    canvas.create_oval(center_x - 4, center_y - 4, center_x + 4, center_y + 4, fill="#ffffff", outline="")
    try:
        radius = max(10, min(95, float(radius_value or 3) * 20))
    except (TypeError, ValueError):
        radius = 60
    if target_type == "circle":
        canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="#55ccff", width=3)
    elif target_type == "line":
        try:
            width = max(5, float(width_value or 1) * 10)
        except (TypeError, ValueError):
            width = 10
        canvas.create_rectangle(center_x, center_y - width, center_x + radius, center_y + width, outline="#55ccff", width=3)
    elif target_type == "cone":
        canvas.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=-45, extent=90, outline="#55ccff", width=3, style="arc")
    elif target_type == "look":
        canvas.create_line(center_x, center_y, center_x + radius, center_y, fill="#55ccff", width=4)
    else:
        canvas.create_text(center_x, center_y - radius - 15, text="self", fill="#ffffff")
