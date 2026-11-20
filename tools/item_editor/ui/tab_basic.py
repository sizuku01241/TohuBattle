"""基本タブで使う選択肢と表示ルール。"""

KIND_VALUES = ("custom", "vanilla")


def filter_vanilla_candidates(candidates, query):
    """入力文字列でVanilla ID候補を絞り込む。手入力自体はUI側で許可する。"""
    normalized = str(query or "").strip().lower()
    values = tuple(sorted(candidates))
    if not normalized:
        return values
    return tuple(value for value in values if normalized in value.lower())
