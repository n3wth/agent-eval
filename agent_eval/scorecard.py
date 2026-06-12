"""Scorecard assembly: the dated deliverable.

Pulls the latest run of each instrument from runs/, maps rates onto the 0-4
anchors, raises the failure-mode flags from docs/scorecard.md, and computes
the delta against the previous scorecard. One scorecard is worthless; the
trend is the product, so every scorecard embeds its own comparison.

Score mapping (documented, so the number means the same thing every run):
rate -> score is linear, 4 x rate, rounded to one decimal. D1/D3 rates are
pass^k. D2 durability uses the rubric's sessions-to-stick anchors
(NullMemory-adjusted) when the memory run measured the curve, falling back
to 4 x rate; D2 discrimination is 1 - over_application_rate. D5 warmed
stays as the RAIR/RSR pair — it has no honest single-number form.
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

    d2_durability = None
    if mem and mem.get("d2_reportable"):
        # Prefer the rubric-anchored sessions-to-stick score from the curve;
        # older records carry only the rate.
        d2_durability = (
            mem.get("durability_score")
            if mem.get("durability_score") is not None
            else _to4(mem["durability_rate"])
        )

    scores = {
        "d1": {"cold": _to4(suite_rate("cold")), "warmed": _to4(suite_rate("warmed"))},
        "d2": {
            "durability": d2_durability,
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
        # Sessions-to-stick never converging is the no-warming signature
        # (docs/tenure.md); reversion is its weaker cousin.
        "no_warming": bool(
            mem
            and mem.get("d2_reportable")
            and (
                mem.get("not_converged", 0) >= 1
                or mem.get("reversions", 0) >= 1
                or (mem.get("durability_rate") or 0) <= 0.25
            )
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

    warmed_suite = suites.get("warmed")
    consistency_gap = None
    if (
        warmed_suite
        and warmed_suite.get("pass_at_1_rate") is not None
        and warmed_suite.get("pass_k_rate") is not None
    ):
        consistency_gap = round(
            warmed_suite["pass_at_1_rate"] - warmed_suite["pass_k_rate"], 2
        )

    trust_entries = journal.load_entries(base, "trust")
    trust = None
    if trust_entries:
        latest_month = max(e["date"][:7] for e in trust_entries)
        scores_in_month = [
            float(e["score"]) for e in trust_entries if e["date"][:7] == latest_month
        ]
        trust = round(sum(scores_in_month) / len(scores_in_month), 2)

    record = {
        "kind": "scorecard",
        "agent": agent,
        "date": time.strftime("%Y-%m-%d"),
        "scores": scores,
        "cliff": cliff,
        "consistency_gap": consistency_gap,
        # Durability detail follows the pair rule: shown only when
        # discrimination was scored too.
        "sessions_to_stick": (
            mem.get("sessions_to_stick") if mem and mem.get("d2_reportable") else None
        ),
        "trust": trust,
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
        f"- **Consistency gap:** {_fmt(record.get('consistency_gap'))} (pass@1 − pass^k, warmed; what a single demo run overstates)",
        f"- **Sessions-to-stick (median):** {_fmt(record.get('sessions_to_stick'))}",
        f"- **Trust scale (latest month mean):** {_fmt(record.get('trust'))}",
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


COMPARE_CELLS = [
    ("D1 cold", "d1", "cold"),
    ("D1 warmed", "d1", "warmed"),
    ("D2 durability", "d2", "durability"),
    ("D2 discrimination", "d2", "discrimination"),
    ("D3 cold", "d3", "cold"),
    ("D3 warmed", "d3", "warmed"),
    ("D4 cold", "d4", "cold"),
    ("D4 warmed", "d4", "warmed"),
    ("D5 cold (honesty)", "d5", "cold"),
    ("D5 RAIR", "d5", "rair"),
    ("D5 RSR", "d5", "rsr"),
]


def render_comparison(a: dict, b: dict) -> str:
    """Two scorecards side by side: agents, or the same agent across runs.

    Cross-agent data is the point (CONTRIBUTING.md); this is the table you'd
    publish. Cells the runs didn't score stay gaps in both columns.
    """
    name_a = f"{a.get('agent', 'A')} ({a.get('date', '?')})"
    name_b = f"{b.get('agent', 'B')} ({b.get('date', '?')})"
    lines = [
        f"# Comparison — {name_a} vs {name_b}",
        "",
        f"| Cell | {name_a} | {name_b} | Δ |",
        "|------|---:|---:|---:|",
    ]
    for label, dim, cell in COMPARE_CELLS:
        va = a.get("scores", {}).get(dim, {}).get(cell)
        vb = b.get("scores", {}).get(dim, {}).get(cell)
        delta = round(vb - va, 2) if va is not None and vb is not None else None
        lines.append(f"| {label} | {_fmt(va)} | {_fmt(vb)} | {_fmt(delta)} |")
    for label, key in [("Cold-start cliff", "cliff"), ("Consistency gap", "consistency_gap")]:
        va, vb = a.get(key), b.get(key)
        delta = round(vb - va, 2) if va is not None and vb is not None else None
        lines.append(f"| {label} | {_fmt(va)} | {_fmt(vb)} | {_fmt(delta)} |")
    flags_a = {k for k, v in a.get("flags", {}).items() if v is True}
    flags_b = {k for k, v in b.get("flags", {}).items() if v is True}
    lines.append("")
    lines.append(f"- Flags only on {name_a}: {', '.join(sorted(flags_a - flags_b)) or 'none'}")
    lines.append(f"- Flags only on {name_b}: {', '.join(sorted(flags_b - flags_a)) or 'none'}")
    lines.append(f"- Shared flags: {', '.join(sorted(flags_a & flags_b)) or 'none'}")
    lines.append("")
    return "\n".join(lines)


def write_scorecard(
    record: dict,
    out_dir: str | Path = "scorecards/runs",
    runs_dir: str | Path = "runs",
) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    md = out / f"run-{stamp}.md"
    md.write_text(render_markdown(record))
    # The JSON record must land in the same runs dir the next assemble()
    # reads, or the delta chain breaks — and the delta is the product.
    json_path = storage.save_run(record, "scorecard", runs_dir)
    return md, json_path
