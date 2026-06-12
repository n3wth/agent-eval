"""Reliance fit (D5): the 2x2, never delegation volume.

From logged accept/override events, compute weekly:

- RAIR — of the events where the agent was right, the fraction where you
  relied (correctly deferred);
- RSR — of the events where the agent was wrong, the fraction where you
  overrode (correct self-reliance).

Both rising together is calibration improving; that is the win. The drift
check catches the failure a volume line would reward: RAIR rising while RSR
falls or stays flat means you are deferring more without the agent earning
it. The slope is jagged and per-capability by nature (trust collapses fast
after one error, and you may calibrate on refactors while staying skeptical
on financial actions), so events carry an optional capability tag and one
bad week is not a trend.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict


def _week(date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def summarize(events: list[dict], by: str = "week") -> dict:
    """events: [{date, relied: bool, agent_right: bool, capability?, note?}]"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        key = _week(e["date"]) if by == "week" else e.get("capability", "general")
        groups[key].append(e)

    rows = []
    for key in sorted(groups):
        es = groups[key]
        right = [e for e in es if e["agent_right"]]
        wrong = [e for e in es if not e["agent_right"]]
        rows.append(
            {
                "group": key,
                "events": len(es),
                "rair": (sum(1 for e in right if e["relied"]) / len(right)) if right else None,
                "rsr": (sum(1 for e in wrong if not e["relied"]) / len(wrong)) if wrong else None,
                "over_reliance_events": sum(1 for e in wrong if e["relied"]),
                "under_reliance_events": sum(1 for e in right if not e["relied"]),
            }
        )

    return {
        "kind": "reliance",
        "by": by,
        "rows": rows,
        "drift_to_over_reliance": _drift(rows),
        "total_events": len(events),
    }


def _drift(rows: list[dict]) -> bool:
    """RAIR up while RSR flat or down across the scored groups."""
    scored = [r for r in rows if r["rair"] is not None and r["rsr"] is not None]
    if len(scored) < 2:
        return False
    first, last = scored[0], scored[-1]
    return (last["rair"] - first["rair"]) > 0.05 and (last["rsr"] - first["rsr"]) <= 0
