"""Daily-use journal (D4, D5) as an append-only JSONL log.

Two entry types share the file:

- ``journal`` — the experience-sampling entry from probes/texture.md
  (friction, re-corrections, wow moments, interrupt quality);
- ``reliance`` — one accept/override event with whether the agent was right,
  feeding the weekly RAIR/RSR in reliance.py.

Fixed prompts, fixed cadence: the within-person deltas are what roll up, not
the narrative.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

JOURNAL_FIELDS = [
    ("surface", "Surface (coding | messaging | ...)"),
    ("tenure", "Tenure state (cold | warming | warmed)"),
    ("friction", "Friction moments (annoyed / re-asked / over-styled / looped)"),
    ("recorrections", "Re-corrections (anything you had to say again — feeds D2)"),
    ("wow", '"Wow" moments (anticipated / nailed it unprompted)'),
    ("interrupt_quality", "Interrupt quality (too much | too little | right)"),
]


def journal_path(base: str | Path = "runs") -> Path:
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d / "journal.jsonl"


def append_entry(entry: dict, base: str | Path = "runs") -> None:
    entry = dict(entry)
    entry.setdefault("date", time.strftime("%Y-%m-%d"))
    with journal_path(base).open("a") as f:
        f.write(json.dumps(entry) + "\n")


def load_entries(base: str | Path = "runs", entry_type: str | None = None) -> list[dict]:
    path = journal_path(base)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry_type is None or entry.get("type") == entry_type:
            entries.append(entry)
    return entries


def add_journal_entry_interactive(base: str | Path = "runs") -> dict:
    entry: dict = {"type": "journal"}
    for key, prompt in JOURNAL_FIELDS:
        entry[key] = input(f"{prompt}: ").strip()
    append_entry(entry, base)
    return entry


def add_trust_score(score: float, note: str = "", base: str | Path = "runs") -> dict:
    """One trust-scale self-rating (1-7), the weekly repeated measure from
    docs/scorecard.md D5. The harness records the number; administer
    whichever validated instrument you've adopted and log its mean here."""
    if not 1 <= score <= 7:
        raise ValueError("trust score is a 1-7 scale")
    entry = {"type": "trust", "score": float(score), "note": note}
    append_entry(entry, base)
    return entry


def add_reliance_event(
    relied: bool,
    agent_right: bool,
    capability: str = "general",
    note: str = "",
    base: str | Path = "runs",
) -> dict:
    entry = {
        "type": "reliance",
        "relied": relied,
        "agent_right": agent_right,
        "capability": capability,
        "note": note,
    }
    append_entry(entry, base)
    return entry
