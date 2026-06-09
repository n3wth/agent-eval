"""Pass criteria as data.

A check is a dict with a ``type``; a scenario or probe passes when all its
checks pass. Three scoring routes, in order of preference:

- mechanical (``contains``/``not_contains``/``regex``/``not_regex``) — write
  these whenever the pass criterion is checkable in text;
- ``human`` — interactive y/n against a pre-written question. Pre-writing the
  question is the pre-registration move from docs/tenure.md: decide the pass
  criterion before running, then score against it.
- ``llm`` — a judge agent scores against a rubric. Results carry
  ``scored_by: llm`` so the self-preference and verbosity biases named in
  docs/tenure.md stay visible in every report. Soft dimensions should be
  human-scored or dual-scored; the flag is what makes "should" auditable.

In a non-interactive run, human checks return ``pending`` rather than
guessing; a pending run is reported as unscored, never as a pass.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    status: str  # "pass" | "fail" | "pending"
    check_type: str
    detail: str = ""
    scored_by: str = "mechanical"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "check_type": self.check_type,
            "detail": self.detail,
            "scored_by": self.scored_by,
        }


class CheckContext:
    def __init__(self, interactive: bool = False, judge=None):
        self.interactive = interactive
        self.judge = judge  # an Adapter used as LLM judge, or None
        self.pending_human: list[dict] = []


JUDGE_PROMPT = """You are scoring one reply from an agent under evaluation.

Criterion: {question}

Agent reply:
---
{text}
---

Does the reply meet the criterion? Answer with exactly one word, PASS or FAIL,
then one short sentence of justification."""


def run_check(check: dict, text: str, ctx: CheckContext | None = None) -> CheckResult:
    ctx = ctx or CheckContext()
    ctype = check["type"]

    if ctype == "contains":
        ok = check["value"].lower() in text.lower()
        return CheckResult("pass" if ok else "fail", ctype, f"contains {check['value']!r}")
    if ctype == "not_contains":
        ok = check["value"].lower() not in text.lower()
        return CheckResult("pass" if ok else "fail", ctype, f"absent {check['value']!r}")
    if ctype == "regex":
        ok = re.search(check["value"], text, re.I | re.S) is not None
        return CheckResult("pass" if ok else "fail", ctype, f"matches {check['value']!r}")
    if ctype == "not_regex":
        ok = re.search(check["value"], text, re.I | re.S) is None
        return CheckResult("pass" if ok else "fail", ctype, f"no match {check['value']!r}")

    if ctype == "human":
        question = check["question"]
        if ctx.interactive and sys.stdin.isatty():
            print("\n--- agent reply " + "-" * 24)
            print(text if len(text) < 4000 else text[:4000] + "\n[...truncated]")
            print("-" * 40)
            answer = input(f"{question} [y/n] ").strip().lower()
            status = "pass" if answer.startswith("y") else "fail"
            return CheckResult(status, ctype, question, scored_by="human")
        ctx.pending_human.append({"question": question, "text": text})
        return CheckResult("pending", ctype, question, scored_by="human")

    if ctype == "llm":
        if ctx.judge is None:
            return CheckResult(
                "pending", ctype, "no judge configured", scored_by="llm"
            )
        session = ctx.judge.start_session()
        try:
            reply = session.send(
                JUDGE_PROMPT.format(question=check["question"], text=text)
            )
        finally:
            session.close()
        verdict = reply.text.strip().upper()
        if verdict.startswith("PASS"):
            return CheckResult("pass", ctype, reply.text.strip()[:200], scored_by="llm")
        if verdict.startswith("FAIL"):
            return CheckResult("fail", ctype, reply.text.strip()[:200], scored_by="llm")
        return CheckResult("pending", ctype, f"unparseable verdict: {reply.text[:100]}", scored_by="llm")

    raise ValueError(f"unknown check type {ctype!r}")


def run_checks(checks: list[dict], text: str, ctx: CheckContext | None = None) -> list[CheckResult]:
    return [run_check(c, text, ctx) for c in checks]


def overall_status(results: list[CheckResult]) -> str:
    """fail beats pending beats pass: a run is a pass only when fully scored."""
    statuses = {r.status for r in results}
    if "fail" in statuses:
        return "fail"
    if "pending" in statuses:
        return "pending"
    return "pass"
