"""Run records on disk.

Every run writes a dated JSON record under runs/. The scorecard is assembled
from the latest record of each kind, and deltas are computed against the
previous scorecard — the dated trail is the product, per AGENTS.md: a
scorecard run once is worthless.
"""

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

_seq = itertools.count()


def runs_dir(base: str | Path = "runs") -> Path:
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_run(record: dict, kind: str, base: str | Path = "runs") -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    record = dict(record)
    record.setdefault("kind", kind)
    record.setdefault("date", time.strftime("%Y-%m-%d"))
    record.setdefault("timestamp", stamp)
    # The sequence keeps same-second saves distinct and in write order;
    # load_runs sorts by filename, so order must be lexicographic.
    path = runs_dir(base) / f"{stamp}-{next(_seq):04d}-{kind}.json"
    path.write_text(json.dumps(record, indent=2, default=str) + "\n")
    return path


def load_runs(kind: str | None = None, base: str | Path = "runs") -> list[dict]:
    """All runs, oldest first; optionally filtered by kind."""
    d = Path(base)
    if not d.exists():
        return []
    records = []
    for path in sorted(d.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if kind is None or rec.get("kind") == kind:
            rec["_path"] = str(path)
            records.append(rec)
    return records


def latest_run(kind: str, base: str | Path = "runs") -> dict | None:
    runs = load_runs(kind, base)
    return runs[-1] if runs else None
