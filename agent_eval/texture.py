"""Texture probe runner (D4, plus the cold-start honesty probe for D5).

Each probe is one provocation — an under-specified task, a subtly wrong
request, a task that should block — with pre-written pass criteria. Most
criteria need a human or an LLM judge; the runner records pending rather
than guessing in non-interactive runs.

Probes carry a ``tenure`` tag because the same behavior scores opposite cold
vs. warmed (the D4 flip): run the file once per tenure state and the runner
keeps only the probes tagged for that state (untagged probes run in both).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from .adapters.base import Adapter
from .checks import CheckContext, run_checks


@dataclass
class TextureProbe:
    id: str
    prompt: str | list[str]
    checks: list[dict]
    title: str = ""
    dimension: str = "d4"  # "d5" for the cold-start honesty probes
    tenure: str | None = None  # None = applies in any tenure state

    @property
    def turns(self) -> list[str]:
        return [self.prompt] if isinstance(self.prompt, str) else list(self.prompt)


def load_texture_probes(path: str | Path) -> list[TextureProbe]:
    data = yaml.safe_load(Path(path).read_text())
    probes = [
        TextureProbe(
            id=raw["id"],
            prompt=raw["prompt"],
            checks=raw.get("checks", []),
            title=raw.get("title", ""),
            dimension=raw.get("dimension", "d4"),
            tenure=raw.get("tenure"),
        )
        for raw in data.get("probes", [])
    ]
    if not probes:
        raise ValueError(f"{path}: no probes")
    return probes


def run_texture_probes(
    adapter: Adapter,
    probes: list[TextureProbe],
    tenure: str = "warmed",
    ctx: CheckContext | None = None,
) -> dict:
    ctx = ctx or CheckContext()
    results = []
    for probe in probes:
        if probe.tenure is not None and probe.tenure != tenure:
            continue
        start = time.monotonic()
        session = adapter.start_session()
        try:
            reply_text = ""
            for turn in probe.turns:
                reply_text = session.send(turn).text
        finally:
            session.close()
        checks = run_checks(probe.checks, reply_text, ctx)
        results.append(
            {
                "id": probe.id,
                "title": probe.title,
                "dimension": probe.dimension,
                "checks": [c.to_dict() for c in checks],
                "reply": reply_text,
                "latency_s": round(time.monotonic() - start, 3),
            }
        )

    record = {
        "kind": "texture",
        "tenure": tenure,
        "probes": results,
        "pending_human": ctx.pending_human,
    }
    return aggregate_texture(record)


def aggregate_texture(record: dict) -> dict:
    """Derive per-probe status and per-dimension rates from the raw record."""
    for probe in record["probes"]:
        statuses = {c["status"] for c in probe.get("checks", [])}
        if "fail" in statuses:
            probe["status"] = "fail"
        elif "pending" in statuses:
            probe["status"] = "pending"
        else:
            probe["status"] = "pass"

    results = record["probes"]

    def rate(dim: str):
        scored = [r for r in results if r["dimension"] == dim and r["status"] != "pending"]
        if not scored:
            return None
        return sum(1 for r in scored if r["status"] == "pass") / len(scored)

    record.update(
        {
            "d4_rate": rate("d4"),
            "d5_rate": rate("d5"),
            "pending_count": sum(1 for r in results if r["status"] == "pending"),
        }
    )
    return record
