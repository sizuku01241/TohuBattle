"""生成プレビュー表示用の純粋な差分処理。"""

import difflib


def unified_diff(relative_path: str, old_content: str | bytes | None, new_content: str | bytes) -> str:
    def lines(content):
        if content is None:
            return []
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return content.splitlines(keepends=True)

    result = "".join(difflib.unified_diff(lines(old_content), lines(new_content), fromfile=relative_path, tofile=relative_path))
    return result or "差分なし"
