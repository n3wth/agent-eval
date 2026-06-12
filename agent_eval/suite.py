"""Scenario suite runner (D1, D3).

Loads scenarios/suite.yaml, runs each scenario k times in fresh sessions,
and reports pass^k (all-of-k succeed) as the headline with pass@1 alongside
for contrast — never alone. A coworker you can't trust to repeat is not a
coworker; that rule is enforced here, not left to the report author. The
pass@1 − pass^k gap is itself a finding: the consistency gap, the capability
a single demo run overstates.

Tenure is a run parameter: ``--tenure cold`` wipes memory through the
adapter's memory control before the run and restores it after (the ABA
reversal from docs/tenure.md). The record carries the tenure label so the
scorecard can compute the cold-start cliff.

Records store full replies and per-run latency, and aggregation
(:func:`aggregate_suite`) is a pure function over the record — so a batch
run can be human-scored later (``agent-eval score``) and re-aggregated
through the same code path.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .adapters.base import Adapter
from .checks import CheckContext, run_checks

CATEGORIES = {"routine", "multi-step", "ambiguous", "stall-prone", "customization"}


@dataclass
class Scenario:
    id: str
    prompt: str | list[str]
    checks: list[dict]
    title: str = ""
    category: str = "routine"
    background: str = ""
    cold_start: bool = True
    notes: str = ""

    @property
    def turns(self) -> list[str]:
        return [self.prompt] if isinstance(self.prompt, str) else list(self.prompt)


@dataclass
class SuiteConfig:
    scenarios: list[Scenario]
    runs: int = 3
    name: str = "suite"
    warnings: list[str] = field(default_factory=list)


def load_suite(path: str | Path) -> SuiteConfig:
    data = yaml.safe_load(Path(path).read_text())
    warnings = []
    scenarios = []
    for raw in data.get("scenarios", []):
        if "TODO" in str(raw.get("prompt", "")):
            warnings.append(
                f"{raw.get('id', '?')}: prompt is a TODO placeholder — fill it with real work before scoring"
            )
        cat = raw.get("category", "routine")
        if cat not in CATEGORIES:
            raise ValueError(
                f"{raw.get('id', '?')}: unknown category {cat!r}; known: {sorted(CATEGORIES)}"
            )
        scenarios.append(
            Scenario(
                id=raw["id"],
                prompt=raw["prompt"],
                checks=raw.get("checks", []),
                title=raw.get("title", ""),
                category=cat,
                background=raw.get("background", ""),
                cold_start=raw.get("cold_start", True),
                notes=raw.get("notes", ""),
            )
        )
    if not scenarios:
        raise ValueError(f"{path}: no scenarios")
    return SuiteConfig(
        scenarios=scenarios,
        runs=int(data.get("defaults", {}).get("runs", 3)),
        name=data.get("suite", "suite"),
        warnings=warnings,
    )


def run_scenario(adapter: Adapter, scenario: Scenario, k: int, ctx: CheckContext) -> dict:
    runs = []
    for _ in range(k):
        start = time.monotonic()
        session = adapter.start_session()
        try:
            reply_text = ""
            error = None
            for turn in scenario.turns:
                reply = session.send(turn)
                reply_text = reply.text
                if not reply.ok:
                    error = reply.error
                    break
        finally:
            session.close()
        latency = round(time.monotonic() - start, 3)
        results = [] if error else run_checks(scenario.checks, reply_text, ctx)
        runs.append(
            {
                "checks": [r.to_dict() for r in results],
                "reply": reply_text,
                "error": error,
                "latency_s": latency,
            }
        )
    return {
        "id": scenario.id,
        "title": scenario.title,
        "category": scenario.category,
        "background": scenario.background,
        "runs": runs,
    }


def run_suite(
    adapter: Adapter,
    suite: SuiteConfig,
    tenure: str = "warmed",
    k: int | None = None,
    ctx: CheckContext | None = None,
) -> dict:
    ctx = ctx or CheckContext()
    k = k or suite.runs

    memory_token = None
    if tenure == "cold":
        mc = adapter.memory_control
        if mc is None:
            raise RuntimeError(
                "cold-start pass needs memory control; this adapter has none "
                "(set memory_paths in the adapter config)"
            )
        memory_token = mc.wipe()

    try:
        scenarios = suite.scenarios
        if tenure == "cold":
            scenarios = [s for s in scenarios if s.cold_start]
        results = [run_scenario(adapter, s, k, ctx) for s in scenarios]
    finally:
        if memory_token is not None:
            adapter.memory_control.restore(memory_token)

    record = {
        "kind": "suite",
        "suite": suite.name,
        "tenure": tenure,
        "k": k,
        "warnings": suite.warnings,
        "scenarios": results,
        "pending_human": ctx.pending_human,
    }
    return aggregate_suite(record)


def _run_status(run: dict) -> str:
    if run.get("error"):
        return "fail"
    statuses = {c["status"] for c in run.get("checks", [])}
    if "fail" in statuses:
        return "fail"
    if "pending" in statuses:
        return "pending"
    return "pass"


def aggregate_suite(record: dict) -> dict:
    """Derive pass@1 / pass^k and category rates from the raw record."""
    for scenario in record["scenarios"]:
        statuses = [_run_status(r) for r in scenario["runs"]]
        scenario["pass_at_1"] = "pass" in statuses
        scenario["pass_k"] = all(s == "pass" for s in statuses)
        scenario["pending"] = "pending" in statuses

    results = record["scenarios"]
    scored = [r for r in results if not r["pending"]]
    by_category: dict[str, list] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)

    record.update(
        {
            "pass_k_rate": (
                sum(1 for r in scored if r["pass_k"]) / len(scored) if scored else None
            ),
            "pass_at_1_rate": (
                sum(1 for r in scored if r["pass_at_1"]) / len(scored) if scored else None
            ),
            "category_pass_k": {
                cat: (
                    sum(1 for r in rs if r["pass_k"])
                    / len([r for r in rs if not r["pending"]])
                    if any(not r["pending"] for r in rs)
                    else None
                )
                for cat, rs in by_category.items()
            },
            "pending_count": sum(1 for r in results if r["pending"]),
        }
    )
    return record
