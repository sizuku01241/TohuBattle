"""履歴ダイアログから利用する履歴操作の公開面。"""

from ..ui_logic import history_entries, restore_history


def open_history_dialog(parent, tk, ttk, entries, on_restore):
    """履歴一覧ダイアログを構築する。復元処理は呼び出し側へ委譲する。"""
    dialog = tk.Toplevel(parent)
    dialog.title("履歴")
    dialog.geometry("600x400")
    listbox = tk.Listbox(dialog)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)
    for entry in entries:
        additions = " ".join(f"+ {key}" for key in entry.get("added", []))
        removals = " ".join(f"- {key}" for key in entry.get("removed", []))
        difference = " ".join(value for value in (additions, removals) if value)
        suffix = f" / {difference}" if difference else ""
        listbox.insert("end", f"{entry['name']} (items {entry.get('items', 0)}件 / ファイル {entry['files']}個{suffix})")
    ttk.Button(dialog, text="選択した履歴を復元", command=lambda: on_restore(dialog, listbox)).pack(pady=(0, 10))
    return dialog

__all__ = ["history_entries", "restore_history", "open_history_dialog"]
