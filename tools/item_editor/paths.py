from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_inside(root: Path, relative: str | Path) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"project-root外への書き込みは禁止されています: {relative}") from exc
    return target


ALLOWED_PREFIXES = (
    "behavior_pack/items",
    "behavior_pack/scripts/item/loot",
    "behavior_pack/scripts/item/custom",
    "resource_pack/textures/items",
    "resource_pack/textures/item_texture.json",
    "resource_pack/texts",
    "tools/items",
)


def ensure_writable(root: Path, target: Path) -> Path:
    target = target.resolve()
    target.relative_to(root.resolve())
    rel = target.relative_to(root.resolve()).as_posix()
    if not any(rel == prefix or rel.startswith(prefix + "/") for prefix in ALLOWED_PREFIXES):
        raise ValueError(f"許可されていない書き込み先です: {rel}")
    return target
