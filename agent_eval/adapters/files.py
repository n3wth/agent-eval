"""File-based memory control.

Most personal agents keep continuity in files (memory markdown, vector
stores, conversation logs). The cold-start protocol in docs/tenure.md is
"mv it aside, do not delete; restore after" — this implements exactly that,
and nothing destructive.
"""

from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path

from .base import MemoryControl


class FileMemoryControl(MemoryControl):
    def __init__(self, paths: list[str], backup_dir: str | None = None):
        self.paths = [Path(p).expanduser() for p in paths]
        self.backup_root = Path(
            backup_dir or "~/.agent-eval/memory-backups"
        ).expanduser()

    def wipe(self) -> str:
        token = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        dest = self.backup_root / token
        dest.mkdir(parents=True, exist_ok=True)
        manifest = []
        for i, path in enumerate(self.paths):
            if not path.exists():
                continue
            target = dest / f"{i}-{path.name}"
            shutil.move(str(path), str(target))
            manifest.append((str(path), str(target)))
        (dest / "MANIFEST").write_text(
            "\n".join(f"{orig}\t{moved}" for orig, moved in manifest)
        )
        return token

    def restore(self, token: str) -> None:
        dest = self.backup_root / token
        manifest_file = dest / "MANIFEST"
        if not manifest_file.exists():
            raise FileNotFoundError(f"no memory snapshot for token {token}")
        for line in manifest_file.read_text().splitlines():
            if not line.strip():
                continue
            orig, moved = line.split("\t")
            orig_path = Path(orig)
            if orig_path.exists():
                # The agent recreated state while wiped (expected: the wiped
                # run writes new memory). Set the wiped-era state aside so the
                # restore is clean but nothing is lost.
                aside = dest / f"wiped-era-{orig_path.name}"
                shutil.move(str(orig_path), str(aside))
            orig_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(moved, str(orig_path))
