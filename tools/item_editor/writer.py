import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
import time
from pathlib import Path
from .paths import ensure_writable


@dataclass
class WritePlan:
    path: Path
    new_content: str | bytes
    old_content: str | bytes | None
    kind: str


def _content_bytes(content: str | bytes) -> bytes:
    return content if isinstance(content, bytes) else content.encode("utf-8")


def plan(root: Path, files: dict[str, str | bytes]) -> list[WritePlan]:
    result = []
    for relative, content in sorted(files.items()):
        target = ensure_writable(root, root / relative)
        old = target.read_bytes() if target.exists() else None
        new_bytes = _content_bytes(content)
        result.append(WritePlan(target, content, old, "unchanged" if old == new_bytes else ("modify" if old is not None else "create")))
    return result


def apply(root: Path, plans: list[WritePlan]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1000000:06d}"
    history = root / "tools" / "items" / "history" / timestamp
    manifest_path = root / "tools" / "items" / "generated_manifest.json"
    try: manifest: dict[str, str] = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    except (OSError, json.JSONDecodeError): manifest = {}
    changed = False
    for entry in plans:
        if entry.kind == "unchanged":
            continue
        changed = True
        if entry.old_content is not None:
            backup = history / entry.path.relative_to(root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(entry.old_content if isinstance(entry.old_content, bytes) else entry.old_content.encode("utf-8"))
        entry.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = entry.path.with_name(entry.path.name + ".tmp")
        temporary.write_bytes(_content_bytes(entry.new_content))
        os.replace(temporary, entry.path)
        manifest[entry.path.relative_to(root).as_posix()] = hashlib.sha256(_content_bytes(entry.new_content)).hexdigest()
    if changed:
        history.mkdir(parents=True, exist_ok=True)
        (history / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    history_root = root / "tools" / "items" / "history"
    generations = sorted([path for path in history_root.iterdir() if path.is_dir()], key=lambda path: path.name) if history_root.exists() else []
    for old in generations[:-50]:
        for child in sorted(old.rglob("*"), reverse=True):
            if child.is_file(): child.unlink()
            elif child.is_dir(): child.rmdir()
        old.rmdir()
    return history
