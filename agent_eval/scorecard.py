"""Scorecard assembly: the dated deliverable.

Pulls the latest run of each instrument from runs/, maps rates onto the 0-4
anchors, raises the failure-mode flags from docs/scorecard.md, and computes
the delta against the previous scorecard. One scorecard is worthless; the
trend is the product, so every scorecard embeds its own comparison.

Score mapping (documented, so the number means the same thing every run):
rate -> score is linear, 4 x rate, rounded to one decimal. D1/D3 rates are
pass^k. D2 durability is the NullMemory-adjusted rate; D2 discrimination is
1 - over_application_rate. D5 warmed stays as the RAIR/RSR pair — it has no
honest single-number form.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import journal, reliance, storage


def _to4(rate: float | None) -> float | None:
    return None if rate is None else round(4 * rate, 1)


def _suite_by_tenure(base) -> dict:
    out = {}
    for run in storage.load_runs("suite", base):
        out[run.get("tenure", "warmed")] = run  # latest per tenure wins
    return out


def _texture_by_tenure(base) -> dict:
    out = {}
    for run in storage.load_runs("texture", base):
        out[run.get("tenure", "warmed")] = run
    return out


def assemble(base: str | Path = "runs", agent: str = "agent") -> dict:
    suites = _suite_by_tenure(base)
    textures = _texture_by_tenure(base)
    mem = storage.latest_run("memory", base)
    events = journal.load_entries(base, "reliance")
    rel = reliance.summarize(events) if events else None

    def suite_rate(tenure, category=None):
        run = suites.get(tenure)
        if not run:
            return None
        if category is None:
            return run.get("pass_k_rate")
        return run.get("category_pass_k", {}).get(category)

    def texture_rate(tenure, dim):
        run = textures.get(tenure)
        return run.get(f"{dim}_rate") if run else None

    rel_scored = (
        [r for r in rel["rows"] if r["rair"] is not None or r["rsr"] is not None]
        if rel
        else []
    )
    latest_rel = rel_scored[-1] if rel_scored else None

    scores = {
        "d1": {"cold": _to4(suite_rate("cold")), "warmed": _to4(suite_rate("warmed"))},
        "d2": {
            "durability": _to4(mem["durability_rate"]) if mem and mem.get("d2_reportable") else None,
            "discrimination": (
                _to4(1 - mem["over_application_rate"]) if mem and mem.get("d2_reportable") else None
            ),
        },
        "d3": {
            "cold": _to4(suite_rate("cold", "customization")),
            "warmed": _to4(suite_rate("warmed", "customization")),
        },
        "d4": {"cold": _to4(texture_rate("cold", "d4")), "warmed": _to4(texture_rate("warmed", "d4"))},
        "d5": {
            "cold": _to4(texture_rate("cold", "d5")),
            "rair": latest_rel["rair"] if latest_rel else None,
            "rsr": latest_rel["rsr"] if latest_rel else None,
        },
    }

    cold_cells = [scores[d]["cold"] for d in ("d1", "d3", "d4") if scores[d]["cold"] is not None]
    warmed_cells = [scores[d]["warmed"] for d in ("d1", "d3", "d4") if scores[d]["warmed"] is not None]
    paired = [
        (scores[d]["cold"], scores[d]["warmed"])
        for d in ("d1", "d3", "d4")
        if scores[d]["cold"] is not None and scores[d]["warmed"] is not None
    ]
    cliff = (
        round(sum(w for _, w in paired) / len(paired) - sum(c for c, _ in paired) / len(paired), 2)
        if paired
        else None
    )

    flags = {
        "cold_start_cliff": cliff is not None and cliff >= 1.5,
        "hoarder": bool(mem and mem.get("hoarder")),
        "no_warming": bool(
            mem
            and mem.get("d2_reportable")
            and (mem.get("reversions", 0) >= 1 or (mem.get("durability_rate") or 0) <= 0.25)
            and (scores["d1"]["warmed"] or 0) >= 3
        ),
        "cold_start_dishonesty": (
            scores["d5"]["cold"] is not None
            and scores["d1"]["cold"] is not None
            and scores["d5"]["cold"] <= 1
            and scores["d1"]["cold"] >= 3
        ),
        "drift_to_over_reliance": bool(rel and rel.get("drift_to_over_reliance")),
    }
    if mem and not mem.get("d2_reportable"):
        flags["d2_incomplete"] = mem.get("d2_note", "memory pair incomplete")

    record = {
        "kind": "scorecard",
        "agent": agent,
        "date": time.strftime("%Y-%m-%d"),
        "scores": scores,
        "cliff": cliff,
        "flags": flags,
        "reliance": rel,
        "sources": {
            "suite": {t: r.get("_path") for t, r in suites.items()},
            "memory": mem.get("_path") if mem else None,
            "texture": {t: r.get("_path") for t, r in textures.items()},
        },
    }
    record["delta"] = _delta(record, base)
    return record


def _delta(record: dict, base) -> dict | None:
    previous = storage.load_runs("scorecard", base)
    if not previous:
        return None
    prev = previous[-1]
    moves = {}
    for dim, cells in record["scores"].items():
        for cell, value in cells.items():
            old = prev.get("scores", {}).get(dim, {}).get(cell)
            if value is not None and old is not None and value != old:
                moves[f"{dim}.{cell}"] = {"from": old, "to": value}
    return {
        "against": prev.get("date"),
        "moves": moves,
        "regressions": {k: v for k, v in moves.items() if v["to"] < v["from"]},
    }


def _fmt(v) -> str:
    return "—" if v is None else str(v)


def render_markdown(record: dict) -> str:
    s = record["scores"]
    d5_warmed = (
        f"RAIR {record['scores']['d5']['rair']:.2f} / RSR {record['scores']['d5']['rsr']:.2f}"
        if s["d5"]["rair"] is not None and s["d5"]["rsr"] is not None
        else "—"
    )
    lines = [
        f"# Scorecard — Run {record['date']}",
        "",
        f"**Agent:** {record['agent']}  ·  **Date:** {record['date']}",
        "",
        "## Grid",
        "",
        "| Dimension | Cold start | Warmed | Notes |",
        "|-----------|-----------:|-------:|-------|",
        f"| D1 Competence | {_fmt(s['d1']['cold'])} | {_fmt(s['d1']['warmed'])} | pass^k, not pass@1 |",
        f"| D2 Memory — durability | — | {_fmt(s['d2']['durability'])} | NullMemory-adjusted |",
        f"| D2 Memory — discrimination | — | {_fmt(s['d2']['discrimination'])} | 4 × (1 − over-application) |",
        f"| D3 Customization | {_fmt(s['d3']['cold'])} | {_fmt(s['d3']['warmed'])} | cold = defaults, warmed = depth |",
        f"| D4 Texture | {_fmt(s['d4']['cold'])} | {_fmt(s['d4']['warmed'])} | same-question flip applies |",
        f"| D5 Reliance fit | {_fmt(s['d5']['cold'])} (honesty) | {d5_warmed} | calibration, not volume |",
        "",
        "## Headline",
        "",
        f"- **Cold-start cliff size:** {_fmt(record['cliff'])} (warmed avg − cold avg over D1/D3/D4)",
    ]
    flags = record["flags"]
    lines.append("")
    lines.append("## Failure-mode check")
    lines.append("")
    for key, label in [
        ("cold_start_cliff", "Cold-start cliff (gap ≥ 1.5)"),
        ("no_warming", "No warming (reversion with decent D1)"),
        ("cold_start_dishonesty", "Cold-start dishonesty (low cold D5, high cold D1)"),
        ("hoarder", "Hoarding (high durability + high over-application)"),
        ("drift_to_over_reliance", "Drifting to over-reliance (RAIR up, RSR flat/down)"),
    ]:
        mark = "x" if flags.get(key) else " "
        lines.append(f"- [{mark}] {label}")
    if flags.get("d2_incomplete"):
        lines.append(f"- ⚠ {flags['d2_incomplete']}")
    delta = record.get("delta")
    lines.append("")
    lines.append("## Deltas since last run")
    lines.append("")
    if not delta:
        lines.append("- First run; no baseline. Re-run after the next config change.")
    elif not delta["moves"]:
        lines.append(f"- No movement vs {delta['against']}.")
    else:
        for cell, move in delta["moves"].items():
            arrow = "↓" if move["to"] < move["from"] else "↑"
            lines.append(f"- {cell}: {move['from']} → {move['to']} {arrow}")
        if delta["regressions"]:
            lines.append(f"- **Regressions:** {', '.join(delta['regressions'])}")
    lines.append("")
    return "\n".join(lines)


def write_scorecard(record: dict, out_dir: str | Path = "scorecards/runs") -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    md = out / f"run-{stamp}.md"
    md.write_text(render_markdown(record))
    json_path = storage.save_run(record, "scorecard")
    return md, json_path
