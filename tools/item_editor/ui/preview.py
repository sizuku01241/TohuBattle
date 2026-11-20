"""生成プレビュー表示用の純粋な差分処理。"""

import difflib


def build_preview_tab(frame, tk):
    """生成プレビューの一覧・差分表示を構築する。"""
    frame.columnconfigure(0, weight=0)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(0, weight=1)
    files = tk.Listbox(frame, width=42)
    files.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    text = tk.Text(frame, wrap="none", state="disabled")
    text.grid(row=0, column=1, sticky="nsew")
    return files, text


def unified_diff(relative_path: str, old_content: str | bytes | None, new_content: str | bytes) -> str:
    def lines(content):
        if content is None:
            return []
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return content.splitlines(keepends=True)

    result = "".join(difflib.unified_diff(lines(old_content), lines(new_content), fromfile=relative_path, tofile=relative_path))
    return result or "差分なし"
