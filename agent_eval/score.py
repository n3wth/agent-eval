"""Deferred human scoring: resolve a batch run's pending checks later.

The workflow this enables is the one coworker agents actually live in: kick
off a ``--batch`` run unattended (B7-style), then sit down with the saved
transcripts and score the human checks against their pre-written questions.
Pre-writing the question at probe-authoring time and answering it after the
fact is the pre-registration discipline from docs/tenure.md — the criterion
was fixed before the agent ran.

Resolution mutates check statuses in the saved record, then re-aggregates
through the same functions the runner used (aggregate_suite /
aggregate_memory / aggregate_texture), so a re-scored run is
indistinguishable from one scored live. Resolved checks are marked
``scored_by: human`` with a ``scored_at`` date.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Callable

from .memory import aggregate_memory
from .storage import load_runs
from .suite import aggregate_suite
from .texture import aggregate_texture

AGGREGATORS = {
    "suite": aggregate_suite,
    "memory": aggregate_memory,
    "texture": aggregate_texture,
}

RESCORABLE = ("human", "llm")


def find_pending(record: dict) -> list[dict]:
    """Every pending re-scorable check, with the reply it judges.

    Returns refs: {label, reply, check} where ``check`` is the live dict in
    the record — mutating it mutates the record.
    """
    refs: list[dict] = []

    def walk(container: dict, label: str) -> None:
        reply = container.get("reply", "")
        for check in container.get("checks", []):
            if check.get("status") == "pending" and check.get("check_type") in RESCORABLE:
                refs.append({"label": label, "reply": reply, "check": check})

    if record.get("kind") == "suite":
        for scenario in record.get("scenarios", []):
            for i, run in enumerate(scenario.get("runs", []), 1):
                walk(run, f"{scenario['id']} run {i}")
    elif record.get("kind") == "memory":
        for probe in record.get("probes", []):
            for i, t in enumerate(probe.get("triggers", []), 1):
                walk(t, f"{probe['id']} trigger {i}")
            for i, t in enumerate(probe.get("null_triggers", []), 1):
                walk(t, f"{probe['id']} NullMemory control {i}")
            for i, t in enumerate(probe.get("perturb_triggers", []), 1):
                walk(t, f"{probe['id']} perturbation {i}")
    elif record.get("kind") == "texture":
        for probe in record.get("probes", []):
            walk(probe, probe["id"])
    return refs


def ask_tty(label: str, question: str, reply: str) -> str | None:
    """Default asker: y/n/s on stdin. Returns pass/fail, or None to skip."""
    print(f"\n=== {label} " + "=" * max(4, 50 - len(label)))
    print(reply if len(reply) < 4000 else reply[:4000] + "\n[...truncated]")
    print("=" * 56)
    while True:
        answer = input(f"{question} [y/n/s(kip)] ").strip().lower()
        if answer.startswith("y"):
            return "pass"
        if answer.startswith("n"):
            return "fail"
        if answer.startswith("s"):
            return None


def resolve_pending(
    record: dict,
    asker: Callable[[str, str, str], str | None] = ask_tty,
) -> dict:
    """Resolve pending checks via ``asker``, then re-aggregate the record."""
    kind = record.get("kind")
    if kind not in AGGREGATORS:
        raise ValueError(f"cannot score records of kind {kind!r}")
    resolved = 0
    for ref in find_pending(record):
        verdict = asker(ref["label"], ref["check"].get("detail", ""), ref["reply"])
        if verdict is None:
            continue
        ref["check"]["status"] = verdict
        ref["check"]["scored_by"] = "human"
        ref["check"]["scored_at"] = time.strftime("%Y-%m-%d")
        resolved += 1
    record["resolved_checks"] = record.get("resolved_checks", 0) + resolved
    return AGGREGATORS[kind](record)


def latest_pending_record(base: str | Path = "runs") -> dict | None:
    """Most recent suite/memory/texture run that still has pending checks."""
    candidates = [
        r
        for kind in AGGREGATORS
        for r in load_runs(kind, base)
        if r.get("pending_count")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r.get("timestamp", ""))


def score_file(path: str | Path, asker: Callable = ask_tty) -> dict:
    """Score a saved run record in place."""
    p = Path(path)
    record = json.loads(p.read_text())
    record = resolve_pending(record, asker)
    to_save = {k: v for k, v in record.items() if k != "_path"}
    p.write_text(json.dumps(to_save, indent=2, default=str) + "\n")
    return record


def main_interactive(base: str | Path = "runs", path: str | Path | None = None) -> int:
    if path is None:
        record = latest_pending_record(base)
        if record is None:
            print("no runs with pending checks")
            return 0
        path = record["_path"]
    if not sys.stdin.isatty():
        print(f"scoring needs a tty; {path} left unchanged")
        return 1
    record = score_file(path)
    print(
        f"\nresolved {record.get('resolved_checks', 0)} check(s); "
        f"{record.get('pending_count', 0)} still pending"
    )
    print(f"updated: {path}")
    return 0
