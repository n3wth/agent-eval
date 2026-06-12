"""Memory probe runner (D2).

Implements the 4-phase protocol from probes/memory.md: tell in one session,
bury under distractor sessions, probe across a curve of fresh sessions
without restating, and perturb. The output is always the pair — durability
and discrimination — and the report refuses to present one without the
other, because durability alone rewards hoarding.

Durability is scored as the rubric defines it (docs/scorecard.md):
**sessions-to-stick**, the first probe session where conforming behavior
appears and holds through the end of the curve (≥2 consecutive when the
curve is long enough). Stick at 1 scores 4, at 2 scores 3, at 3–4 scores 2,
at ≥5 scores 1; never converging scores 0 — the no-warming signature.
After a perturbation tell, the same machinery yields sessions-to-re-adapt.

Anti-gaming rules enforced in code, not prose:

- A probe whose trigger restates the planted fact measures nothing, so the
  loader rejects any trigger containing a ``fact_keyword``.
- Every durability probe runs against a NullMemory control: the same
  tell/trigger with continuity broken (memory wiped between sessions). A
  probe the control also passes is attributable to base-model priors, not
  memory; it scores 0 regardless of its curve.
- Distractor sessions sit between tell and trigger so "plant then probe"
  is not structurally obvious.
- ``isolate=True`` checkpoints memory before the run and rolls back between
  probes, so probe A's plant cannot prime probe B — and leaves the store as
  it was found. Needs a copy-capable memory control.
- ``shuffle_seed`` randomizes probe order to rule out recency; the seed is
  recorded so the run stays reproducible.

Aggregation (:func:`aggregate_memory`) is a pure function over the saved
record, so a run scored later (``agent-eval score``) re-derives every rate
from the same code path the runner used.

Cross-surface probes (P4) take a second adapter — same agent, different
surface — tell on one, trigger on the other.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .adapters.base import Adapter
from .checks import CheckContext, run_checks

STICK_SCORES = {1: 4, 2: 3, 3: 2, 4: 2}  # ≥5 -> 1, never -> 0


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
    cycles: int = 2  # trigger sessions on the curve
    perturb: dict | None = None  # {tell: str, trigger: str, checks: [...], cycles: int}
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
            cycles=int(raw.get("cycles", raw.get("probe_repeats", 2))),
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


def _one_shot(adapter: Adapter, message: str):
    session = adapter.start_session()
    try:
        return session.send(message)
    finally:
        session.close()


def _trigger_once(trigger_adapter: Adapter, prompt: str, checks: list[dict], ctx) -> dict:
    start = time.monotonic()
    reply = _one_shot(trigger_adapter, prompt)
    latency = round(time.monotonic() - start, 3)
    results = run_checks(checks, reply.text, ctx)
    return {
        "checks": [r.to_dict() for r in results],
        "reply": reply.text,
        "error": reply.error,
        "latency_s": latency,
    }


def _run_curve(
    adapter: Adapter,
    trigger_adapter: Adapter,
    probe: MemoryProbe,
    distractors: list[str],
    ctx: CheckContext,
    break_continuity: bool = False,
) -> list[dict]:
    """Tell -> distractors -> a curve of trigger sessions, each fresh.

    ``break_continuity`` is the NullMemory control: wipe memory after every
    session so nothing carries over. Wiping between sessions (rather than
    once up front) matters — an agent wiped once would still write fresh
    memory during the tell session and pass the trigger. The control runs a
    single trigger; a curve without continuity is flat by construction.
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

    if break_continuity:
        triggers = [_trigger_once(trigger_adapter, probe.trigger, probe.checks, ctx)]
        cut()
        return triggers

    for i in range(probe.distractor_sessions):
        _one_shot(adapter, distractors[i % len(distractors)])

    triggers = []
    for c in range(probe.cycles):
        if c > 0 and probe.distractor_sessions > 0:
            _one_shot(adapter, distractors[c % len(distractors)])
        triggers.append(_trigger_once(trigger_adapter, probe.trigger, probe.checks, ctx))
    return triggers


def run_memory_probes(
    adapter: Adapter,
    probes: list[MemoryProbe],
    distractors: list[str],
    ctx: CheckContext | None = None,
    second_adapter: Adapter | None = None,
    control: bool = True,
    isolate: bool = False,
    shuffle_seed: int | None = None,
) -> dict:
    ctx = ctx or CheckContext()
    mc = adapter.memory_control

    if shuffle_seed is not None:
        probes = list(probes)
        random.Random(shuffle_seed).shuffle(probes)

    baseline = None
    if isolate:
        if mc is None or not mc.supports_isolation:
            raise RuntimeError(
                "--isolate needs a copy-capable memory control "
                "(checkpoint/rollback); this adapter's cannot"
            )
        baseline = mc.checkpoint()

    results = []
    try:
        for i, probe in enumerate(probes):
            if baseline is not None and i > 0:
                mc.rollback(baseline)

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

            record: dict = {
                "id": probe.id,
                "kind": probe.kind,
                "title": probe.title,
                "triggers": _run_curve(adapter, trigger_adapter, probe, distractors, ctx),
            }

            if probe.kind == "durability" and control:
                if mc is None:
                    record["null_control"] = "unavailable: adapter has no memory control"
                else:
                    token = mc.wipe()  # stash the real store for the control run
                    try:
                        record["null_triggers"] = _run_curve(
                            adapter, trigger_adapter, probe, distractors, ctx,
                            break_continuity=True,
                        )
                    finally:
                        mc.restore(token)

            if probe.perturb:
                _one_shot(adapter, probe.perturb["tell"])
                perturb_checks = probe.perturb.get("checks", [])
                record["perturb_triggers"] = [
                    _trigger_once(
                        trigger_adapter, probe.perturb["trigger"], perturb_checks, ctx
                    )
                    for _ in range(int(probe.perturb.get("cycles", 2)))
                ]

            results.append(record)
    finally:
        if baseline is not None:
            mc.rollback(baseline)  # leave the store as it was found

    record = {
        "kind": "memory",
        "probes": results,
        "isolated": isolate,
        "shuffle_seed": shuffle_seed,
        "pending_human": ctx.pending_human,
    }
    return aggregate_memory(record)


def _status_of(trigger: dict) -> str:
    if trigger.get("error"):
        return "fail"
    statuses = {c["status"] for c in trigger.get("checks", [])}
    if "fail" in statuses:
        return "fail"
    if "pending" in statuses:
        return "pending"
    return "pass"


def _stick(statuses: list[str]) -> int | None:
    """First 1-based index from which every later probe passes.

    With a one-trigger curve this degrades to pass/fail at 1; the rubric's
    "holds for >=2 consecutive" needs cycles >= 2 (the default).
    """
    for i in range(len(statuses)):
        if all(s == "pass" for s in statuses[i:]):
            if len(statuses) - i >= 2 or len(statuses) == 1:
                return i + 1
            return None
    return None


def _stick_score(stick: int | None) -> int:
    if stick is None:
        return 0
    return STICK_SCORES.get(stick, 1)


def aggregate_memory(record: dict) -> dict:
    """Derive every per-probe and summary metric from the raw record."""
    for probe in record["probes"]:
        if probe.get("status") == "skipped":
            continue
        statuses = [_status_of(t) for t in probe["triggers"]]
        null_statuses = [_status_of(t) for t in probe.get("null_triggers", [])]
        pending = "pending" in statuses or "pending" in null_statuses

        stick = None if pending else _stick(statuses)
        probe["sessions_to_stick"] = stick
        probe["reverted"] = any(
            statuses[i] == "pass" and "fail" in statuses[i + 1 :]
            for i in range(len(statuses))
        )

        if null_statuses:
            null_passed = all(s == "pass" for s in null_statuses)
            probe["null_control"] = "pass" if null_passed else "fail"
            if not pending:
                probe["null_delta"] = int(stick is not None) - int(null_passed)

        score = _stick_score(stick)
        if probe.get("null_delta") == 0:
            score = 0  # the control passed too: priors, not memory
        probe["score_0_4"] = None if pending else score

        if pending:
            probe["status"] = "pending"
        elif probe["kind"] == "durability":
            probe["status"] = "pass" if (stick is not None and score > 0) else "fail"
        else:
            probe["status"] = "pass" if stick is not None else "fail"

        if probe.get("perturb_triggers"):
            p_statuses = [_status_of(t) for t in probe["perturb_triggers"]]
            if "pending" in p_statuses:
                probe["perturbation"] = {"status": "pending"}
            else:
                re_adapt = _stick(p_statuses)
                probe["perturbation"] = {
                    "status": "pass" if re_adapt is not None else "fail",
                    "sessions_to_re_adapt": re_adapt,
                }

    results = record["probes"]
    durability = [r for r in results if r.get("kind") == "durability" and r.get("status") in ("pass", "fail")]
    discrimination = [r for r in results if r.get("kind") == "discrimination" and r.get("status") in ("pass", "fail")]

    durability_rate = (
        sum(1 for r in durability if r["status"] == "pass") / len(durability)
        if durability
        else None
    )
    durability_score = (
        round(sum(r["score_0_4"] for r in durability) / len(durability), 1)
        if durability
        else None
    )
    # Discrimination checks are written so pass = the one-off was NOT carried
    # forward; a fail is an over-application event.
    over_application_rate = (
        sum(1 for r in discrimination if r["status"] == "fail") / len(discrimination)
        if discrimination
        else None
    )

    sticks = [r["sessions_to_stick"] for r in durability if r["sessions_to_stick"] is not None]
    d2_reportable = durability_rate is not None and over_application_rate is not None

    record.update(
        {
            "durability_rate": durability_rate,
            "durability_score": durability_score,
            "sessions_to_stick": sorted(sticks)[len(sticks) // 2] if sticks else None,
            "not_converged": sum(1 for r in durability if r["sessions_to_stick"] is None),
            "over_application_rate": over_application_rate,
            "reversions": sum(1 for r in durability if r.get("reverted")),
            "d2_reportable": d2_reportable,
            "pending_count": sum(1 for r in results if r.get("status") == "pending"),
        }
    )
    if not d2_reportable:
        missing = "discrimination" if over_application_rate is None else "durability"
        record["d2_note"] = (
            f"not reportable as D2: no scored {missing} probes. "
            "Memory is a pair — report both or neither (AGENTS.md)."
        )
        record.pop("hoarder", None)
    else:
        record["hoarder"] = durability_rate >= 0.75 and over_application_rate >= 0.25
        record.pop("d2_note", None)
    return record
