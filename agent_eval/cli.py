"""agent-eval: the command line for the coworker eval.

    agent-eval validate                              # lint suite + probes
    agent-eval run suite   --config configs/mock.yaml [--tenure cold|warmed] [-k 3]
    agent-eval run memory  --config configs/mock.yaml [--second-config ...]
    agent-eval run texture --config configs/mock.yaml [--tenure cold|warmed]
    agent-eval journal add                           # interactive daily entry
    agent-eval journal reliance --relied --right     # one accept/override event
    agent-eval reliance                              # weekly RAIR / RSR
    agent-eval scorecard                             # assemble the dated scorecard

Cadence (docs/proposal.md): baseline cold and warmed, use daily for 1-2
weeks logging journal + reliance events, re-score weekly. The scorecard
deltas only mean something if the runs are dated and comparable.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import journal as journal_mod
from . import memory as memory_mod
from . import reliance as reliance_mod
from . import scorecard as scorecard_mod
from . import storage
from . import suite as suite_mod
from . import texture as texture_mod
from .checks import CheckContext
from .config import EvalConfig

DEFAULT_SUITE = "scenarios/suite.yaml"
DEFAULT_MEMORY = "probes/memory.yaml"
DEFAULT_TEXTURE = "probes/texture.yaml"


def _ctx(args, cfg: EvalConfig) -> CheckContext:
    judge = cfg.build_judge() if getattr(args, "judge", False) else None
    return CheckContext(interactive=not args.batch, judge=judge)


def _report(record: dict, path) -> None:
    print(json.dumps({k: v for k, v in record.items() if k not in ("scenarios", "probes")}, indent=2, default=str))
    print(f"\nsaved: {path}")
    if record.get("pending_count"):
        print(
            f"note: {record['pending_count']} result(s) pending human scoring — "
            "re-run without --batch to score interactively"
        )


def cmd_run(args) -> int:
    cfg = EvalConfig.load(args.config)
    agent = cfg.build_agent()
    ctx = _ctx(args, cfg)

    if args.instrument == "suite":
        suite = suite_mod.load_suite(args.suite)
        for w in suite.warnings:
            print(f"warning: {w}", file=sys.stderr)
        record = suite_mod.run_suite(agent, suite, tenure=args.tenure, k=args.k, ctx=ctx)
        record["agent"] = cfg.name
        path = storage.save_run(record, "suite", cfg.runs_dir)
        _report(record, path)
        if record["pass_k_rate"] is not None:
            print(f"\npass^{record['k']}: {record['pass_k_rate']:.0%}   (pass@1: {record['pass_at_1_rate']:.0%} — for contrast, not the headline)")
        return 0

    if args.instrument == "memory":
        probes, distractors = memory_mod.load_probes(args.probes or DEFAULT_MEMORY)
        second = EvalConfig.load(args.second_config).build_agent() if args.second_config else None
        record = memory_mod.run_memory_probes(
            agent, probes, distractors, ctx=ctx,
            second_adapter=second, control=not args.no_control,
        )
        record["agent"] = cfg.name
        path = storage.save_run(record, "memory", cfg.runs_dir)
        _report(record, path)
        return 0

    if args.instrument == "texture":
        probes = texture_mod.load_texture_probes(args.probes or DEFAULT_TEXTURE)
        record = texture_mod.run_texture_probes(agent, probes, tenure=args.tenure, ctx=ctx)
        record["agent"] = cfg.name
        path = storage.save_run(record, "texture", cfg.runs_dir)
        _report(record, path)
        return 0

    raise ValueError(args.instrument)


def cmd_validate(args) -> int:
    failures = 0
    try:
        suite = suite_mod.load_suite(args.suite)
        print(f"suite: {len(suite.scenarios)} scenario(s) ok")
        for w in suite.warnings:
            print(f"  warning: {w}")
    except Exception as e:
        print(f"suite: INVALID — {e}")
        failures += 1
    try:
        probes, _ = memory_mod.load_probes(args.memory)
        kinds = {p.kind for p in probes}
        print(f"memory: {len(probes)} probe(s) ok")
        if kinds != {"durability", "discrimination"}:
            print(
                "  warning: probes cover only "
                f"{kinds or '{}'} — D2 needs both halves or it is not reportable"
            )
    except Exception as e:
        print(f"memory: INVALID — {e}")
        failures += 1
    try:
        tprobes = texture_mod.load_texture_probes(args.texture)
        print(f"texture: {len(tprobes)} probe(s) ok")
    except Exception as e:
        print(f"texture: INVALID — {e}")
        failures += 1
    return 1 if failures else 0


def cmd_journal(args) -> int:
    if args.journal_cmd == "add":
        entry = journal_mod.add_journal_entry_interactive(args.runs_dir)
        print(f"logged journal entry for {entry['date']}")
        return 0
    if args.journal_cmd == "reliance":
        entry = journal_mod.add_reliance_event(
            relied=args.relied,
            agent_right=args.right,
            capability=args.capability,
            note=args.note,
            base=args.runs_dir,
        )
        quadrant = {
            (True, True): "appropriate reliance",
            (True, False): "OVER-RELIANCE",
            (False, True): "under-reliance",
            (False, False): "appropriate self-reliance",
        }[(entry["relied"], entry["agent_right"])]
        print(f"logged: {quadrant}")
        return 0
    raise ValueError(args.journal_cmd)


def cmd_reliance(args) -> int:
    events = journal_mod.load_entries(args.runs_dir, "reliance")
    if not events:
        print("no reliance events logged yet (agent-eval journal reliance ...)")
        return 0
    summary = reliance_mod.summarize(events, by=args.by)
    print(f"{'group':<12} {'events':>6} {'RAIR':>6} {'RSR':>6}")
    for row in summary["rows"]:
        rair = f"{row['rair']:.2f}" if row["rair"] is not None else "—"
        rsr = f"{row['rsr']:.2f}" if row["rsr"] is not None else "—"
        print(f"{row['group']:<12} {row['events']:>6} {rair:>6} {rsr:>6}")
    if summary["drift_to_over_reliance"]:
        print("\nFLAG: drifting to over-reliance — RAIR rising while RSR is flat or falling.")
    return 0


def cmd_scorecard(args) -> int:
    record = scorecard_mod.assemble(args.runs_dir, agent=args.agent)
    md, _ = scorecard_mod.write_scorecard(record)
    print(scorecard_mod.render_markdown(record))
    print(f"saved: {md}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-eval", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run an instrument against an agent")
    run.add_argument("instrument", choices=["suite", "memory", "texture"])
    run.add_argument("--config", required=True, help="agent config yaml (configs/)")
    run.add_argument("--tenure", choices=["cold", "warming", "warmed"], default="warmed")
    run.add_argument("--suite", default=DEFAULT_SUITE)
    run.add_argument("--probes", default=None)
    run.add_argument("-k", type=int, default=None, help="runs per scenario for pass^k")
    run.add_argument("--second-config", default=None, help="second surface for cross-surface probes (P4)")
    run.add_argument("--no-control", action="store_true", help="skip the NullMemory control (recorded as skipped)")
    run.add_argument("--batch", action="store_true", help="non-interactive; human checks become pending")
    run.add_argument("--judge", action="store_true", help="use the configured LLM judge for `llm` checks")
    run.set_defaults(func=cmd_run)

    val = sub.add_parser("validate", help="lint the suite and probe files")
    val.add_argument("--suite", default=DEFAULT_SUITE)
    val.add_argument("--memory", default=DEFAULT_MEMORY)
    val.add_argument("--texture", default=DEFAULT_TEXTURE)
    val.set_defaults(func=cmd_validate)

    jr = sub.add_parser("journal", help="daily journal and reliance events")
    jr.add_argument("--runs-dir", default="runs")
    jsub = jr.add_subparsers(dest="journal_cmd", required=True)
    jsub.add_parser("add", help="interactive daily entry")
    rel = jsub.add_parser("reliance", help="log one accept/override event")
    g1 = rel.add_mutually_exclusive_group(required=True)
    g1.add_argument("--relied", dest="relied", action="store_true")
    g1.add_argument("--overrode", dest="relied", action="store_false")
    g2 = rel.add_mutually_exclusive_group(required=True)
    g2.add_argument("--right", dest="right", action="store_true", help="the agent was right")
    g2.add_argument("--wrong", dest="right", action="store_false", help="the agent was wrong")
    rel.add_argument("--capability", default="general", help="per-capability tag (refactor, finance, ...)")
    rel.add_argument("--note", default="")
    jr.set_defaults(func=cmd_journal)

    rl = sub.add_parser("reliance", help="weekly RAIR / RSR from logged events")
    rl.add_argument("--runs-dir", default="runs")
    rl.add_argument("--by", choices=["week", "capability"], default="week")
    rl.set_defaults(func=cmd_reliance)

    sc = sub.add_parser("scorecard", help="assemble the dated scorecard from the latest runs")
    sc.add_argument("--runs-dir", default="runs")
    sc.add_argument("--agent", default="agent")
    sc.set_defaults(func=cmd_scorecard)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
