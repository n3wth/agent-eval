"""Memory probe runner (D2).

Implements the 4-phase protocol from probes/memory.md: tell in one session,
bury under distractor sessions, probe in fresh sessions without restating,
and (for correction probes) perturb. The output is always the pair —
durability and discrimination — and the report refuses to present one
without the other, because durability alone rewards hoarding.

Anti-gaming rules enforced in code, not prose:

- A probe whose trigger restates the planted fact measures nothing, so the
  loader rejects any trigger containing a ``fact_keyword``.
- Every durability probe runs against a NullMemory control: the same
  protocol with continuity broken (memory wiped between sessions). A probe
  the control also passes is attributable to base-model priors, not memory;
  its delta is 0 and it does not count toward durability.
- Distractor sessions sit between tell and trigger so "plant then probe"
  is not structurally obvious.

Cross-surface probes (P4) take a second adapter — same agent, different
surface — tell on one, trigger on the other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .adapters.base import Adapter
from .checks import CheckContext, overall_status, run_checks


class ProbeValidationError(ValueError):
    pass


@dataclass
class MemoryProbe:
    id: str
    kind: str  # "durability" | "discrimination"
    tell: list[str]
    trigger: str
    checks: list[dict]
    fact_keywords: list[str] = field(default_factory=list)
    distractor_sessions: int = 2
    probe_repeats: int = 2
    perturb: dict | None = None  # {tell: str, trigger: str, checks: [...]}
    trigger_surface: str = "primary"  # "second" for cross-surface (P4)
    title: str = ""


def load_probes(path: str | Path) -> tuple[list[MemoryProbe], list[str]]:
    data = yaml.safe_load(Path(path).read_text())
    distractors = data.get("distractors") or [
        "What time zone is UTC-8 in winter?",
        "Give me a one-line shell command to count files in a directory.",
        "Summarize the difference between TCP and UDP in two sentences.",
        "What's a reasonable default font size for body text?",
    ]
    probes = []
    for raw in data.get("probes", []):
        probe = MemoryProbe(
            id=raw["id"],
            kind=raw["kind"],
            tell=[raw["tell"]] if isinstance(raw["tell"], str) else list(raw["tell"]),
            trigger=raw["trigger"],
            checks=raw.get("checks", []),
            fact_keywords=raw.get("fact_keywords", []),
            distractor_sessions=int(raw.get("distractor_sessions", 2)),
            probe_repeats=int(raw.get("probe_repeats", 2)),
            perturb=raw.get("perturb"),
            trigger_surface=raw.get("trigger_surface", "primary"),
            title=raw.get("title", ""),
        )
        validate_probe(probe)
        probes.append(probe)
    if not probes:
        raise ProbeValidationError(f"{path}: no probes")
    return probes, distractors


def validate_probe(probe: MemoryProbe) -> None:
    if probe.kind not in ("durability", "discrimination"):
        raise ProbeValidationError(f"{probe.id}: kind must be durability or discrimination")
    if probe.kind == "durability" and not probe.fact_keywords:
        raise ProbeValidationError(
            f"{probe.id}: durability probes need fact_keywords for the restatement lint"
        )
    for kw in probe.fact_keywords:
        if kw.lower() in probe.trigger.lower():
            raise ProbeValidationError(
                f"{probe.id}: trigger restates the planted fact ({kw!r}); "
                "a probe that restates the fact measures nothing"
            )


def _one_shot_session(adapter: Adapter, message: str):
    session = adapter.start_session()
    try:
        return session.send(message)
    finally:
        session.close()


def _run_protocol(
    adapter: Adapter,
    trigger_adapter: Adapter,
    probe: MemoryProbe,
    distractors: list[str],
    ctx: CheckContext,
    break_continuity: bool = False,
) -> dict:
    """Tell -> distractors -> repeated triggers, each in a fresh session.

    ``break_continuity`` is the NullMemory control: wipe memory after every
    session so nothing carries over. Wiping between sessions (rather than
    once up front) matters — an agent wiped once would still write fresh
    memory during the tell session and pass the trigger.
    """
    mc = adapter.memory_control

    def cut():
        if break_continuity and mc is not None:
            mc.wipe()  # discard interim writes; caller restores the real store

    tell_session = adapter.start_session()
    try:
        for t in probe.tell:
            tell_session.send(t)
    finally:
        tell_session.close()
    cut()

    if not break_continuity:
        for i in range(probe.distractor_sessions):
            _one_shot_session(adapter, distractors[i % len(distractors)])

    trigger_results = []
    for _ in range(probe.probe_repeats):
        reply = _one_shot_session(trigger_adapter, probe.trigger)
        results = run_checks(probe.checks, reply.text, ctx)
        trigger_results.append(
            {
                "status": overall_status(results),
                "checks": [r.to_dict() for r in results],
                "reply_excerpt": reply.text[:500],
            }
        )
        cut()
    return {"triggers": trigger_results}


def run_memory_probes(
    adapter: Adapter,
    probes: list[MemoryProbe],
    distractors: list[str],
    ctx: CheckContext | None = None,
    second_adapter: Adapter | None = None,
    control: bool = True,
) -> dict:
    ctx = ctx or CheckContext()
    mc = adapter.memory_control
    results = []

    for probe in probes:
        trigger_adapter = adapter
        if probe.trigger_surface == "second":
            if second_adapter is None:
                results.append(
                    {
                        "id": probe.id,
                        "kind": probe.kind,
                        "status": "skipped",
                        "note": "cross-surface probe needs a second adapter (--second-config)",
                    }
                )
                continue
            trigger_adapter = second_adapter

        main = _run_protocol(adapter, trigger_adapter, probe, distractors, ctx)
        statuses = [t["status"] for t in main["triggers"]]
        passed = all(s == "pass" for s in statuses)
        pending = "pending" in statuses
        # Passed the first trigger, failed a later one: the planted value
        # surfaced then slipped — the reversion signature from P2.
        reverted = (
            statuses[0] == "pass" and any(s == "fail" for s in statuses[1:])
        )

        record: dict = {
            "id": probe.id,
            "kind": probe.kind,
            "title": probe.title,
            "status": "pending" if pending else ("pass" if passed else "fail"),
            "reverted": reverted,
            "triggers": main["triggers"],
        }

        if probe.kind == "durability" and control:
            if mc is None:
                record["null_control"] = "unavailable: adapter has no memory control"
            else:
                token = mc.wipe()  # stash the real store for the control run
                try:
                    null = _run_protocol(
                        adapter, trigger_adapter, probe, distractors, ctx,
                        break_continuity=True,
                    )
                finally:
                    mc.restore(token)
                null_statuses = [t["status"] for t in null["triggers"]]
                null_passed = all(s == "pass" for s in null_statuses)
                record["null_control"] = "pass" if null_passed else "fail"
                if not pending:
                    record["null_delta"] = int(passed) - int(null_passed)

        if probe.perturb and record["status"] == "pass":
            _one_shot_session(adapter, probe.perturb["tell"])
            reply = _one_shot_session(trigger_adapter, probe.perturb["trigger"])
            presults = run_checks(probe.perturb.get("checks", []), reply.text, ctx)
            record["perturbation"] = {
                "status": overall_status(presults),
                "checks": [r.to_dict() for r in presults],
            }

        results.append(record)

    return _aggregate(results, ctx)


def _aggregate(results: list[dict], ctx: CheckContext) -> dict:
    durability = [r for r in results if r.get("kind") == "durability" and r["status"] in ("pass", "fail")]
    discrimination = [r for r in results if r.get("kind") == "discrimination" and r["status"] in ("pass", "fail")]

    # A durability pass the NullMemory control also passed is base-model
    # priors, not memory: it does not count.
    attributable = [
        r for r in durability
        if r["status"] == "pass" and r.get("null_delta", 1) != 0
    ]
    durability_rate = len(attributable) / len(durability) if durability else None
    # Discrimination checks are written so pass = the one-off was NOT carried
    # forward; a fail is an over-application event.
    over_application_rate = (
        sum(1 for r in discrimination if r["status"] == "fail") / len(discrimination)
        if discrimination
        else None
    )

    d2_reportable = durability_rate is not None and over_application_rate is not None
    report = {
        "kind": "memory",
        "probes": results,
        "durability_rate": durability_rate,
        "over_application_rate": over_application_rate,
        "reversions": sum(1 for r in durability if r.get("reverted")),
        "d2_reportable": d2_reportable,
        "pending_count": sum(1 for r in results if r.get("status") == "pending"),
        "pending_human": ctx.pending_human,
    }
    if not d2_reportable:
        missing = "discrimination" if over_application_rate is None else "durability"
        report["d2_note"] = (
            f"not reportable as D2: no scored {missing} probes. "
            "Memory is a pair — report both or neither (AGENTS.md)."
        )
    else:
        report["hoarder"] = durability_rate >= 0.75 and over_application_rate >= 0.25
    return report
