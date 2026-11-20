"""食べ物/使用タブの未対応項目表示。"""

UNSUPPORTED_USE_MESSAGE = "常時効果・使用中断・音声は未対応"


def build_use_tab(frame, ttk, entry, fields, food_enabled, always_eat):
    """食べ物・使用タブを構築する。"""
    ttk.Checkbutton(frame, text="食べ物を有効化", variable=food_enabled).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
    entry(frame, 1, "空腹回復", fields["nutrition"])
    entry(frame, 2, "満腹度", fields["saturation"])
    ttk.Checkbutton(frame, text="常に食べられる", variable=always_eat).grid(row=3, column=1, sticky="w")
    entry(frame, 4, "使用時間(秒)", fields["duration"])
    entry(frame, 5, "移動速度係数", fields["movement"])
    ttk.Label(frame, text="アニメーション").grid(row=6, column=0, sticky="w", padx=5)
    ttk.Combobox(frame, textvariable=fields["animation"], values=("eat", "drink", "bow", "block", "none"), state="readonly", width=22).grid(row=6, column=1, sticky="ew", padx=5)
    ttk.Label(frame, text=UNSUPPORTED_USE_MESSAGE, foreground="#996600").grid(row=7, column=0, columnspan=2, sticky="w", pady=10)
