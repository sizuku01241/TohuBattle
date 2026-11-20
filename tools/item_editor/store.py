import json
import os
import time
from datetime import datetime
from pathlib import Path
from .models import Item, item_from_dict, item_to_dict


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="")
    os.replace(temporary, path)


def items_path(root: Path) -> Path:
    return root / "tools" / "items" / "items.json"


def settings_path(root: Path) -> Path:
    return root / "tools" / "items" / "settings.json"


def load_settings(root: Path) -> dict:
    path = settings_path(root)
    if not path.exists():
        return {"window_geometry": "1350x850", "last_key": "", "filters": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"window_geometry": "1350x850", "last_key": "", "filters": {}}


def save_settings(root: Path, settings: dict) -> Path:
    path = settings_path(root)
    atomic_write(path, json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    return path


def load_items(root: Path) -> list[Item]:
    path = items_path(root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("items.jsonのschema_versionは1である必要があります")
    return [item_from_dict(raw) for raw in data.get("items", [])]


def save_items(root: Path, items: list[Item]) -> Path:
    path = items_path(root)
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1000000:06d}"
        backup = root / "tools" / "items" / "history" / stamp / "tools" / "items" / "items.json"
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(path.read_bytes())
    payload = {"schema_version": 1, "items": [item_to_dict(item) for item in items]}
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    history_root = root / "tools" / "items" / "history"
    generations = sorted((entry for entry in history_root.iterdir() if entry.is_dir()), key=lambda entry: entry.name) if history_root.exists() else []
    for old in generations[:-50]:
        for child in sorted(old.rglob("*"), reverse=True):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        old.rmdir()
    return path
