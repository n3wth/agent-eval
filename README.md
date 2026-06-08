# agent-eval

A method for evaluating an AI coworker. Not a tool you grade once, but a relationship you measure over time. Hermes (Oliver's mini agent) is the worked example throughout.

The premise: the unit of evaluation is a week, not a task. Task pass-rate is the floor. The differentiator is whether working with the agent gets better the longer you use it, and whether it helps someone it has never met.

## Layout

- `docs/proposal.md` — the full method. Read this first.
- `docs/scorecard.md` — the rubric: 5 dimensions by tenure axis, scored 0–4.
- `docs/tenure-protocol.md` — cold-start / warming / warmed passes, including the wiped-memory cold-start run.
- `docs/framework-comparison.md` — comparing whole frameworks (Hermes' stack vs. LangGraph, CrewAI, etc.), plus the OSS tooling per stack layer for running the eval. Where benchmarks live.
- `docs/references.md` — the published methods each dimension is grounded in.
- `scenarios/suite.md` — the D1/D3 task suite template (fill with real tasks).
- `probes/memory-probes.md` — D2 multi-session tell/recall, paired durability and discrimination.
- `probes/texture-probes.md` — D4 ask / push-back / admit-stuck, plus the daily journal.
- `scorecards/template.md` — a blank scored run with a date column.

## The two corrections that keep it honest

Two framings look like progress and are half-wrong. The eval pairs each against its failure mode:

- **Memory:** "remember more" rewards hoarding. D2 pairs durability against over-application rate.
- **Reliance:** "delegate more" rewards over-reliance. D5 scores calibrated reliance (relied-when-right, overrode-when-wrong), not delegation volume.

## Status

Design-only. No code drives Hermes yet. The rubric and protocols are reviewed before anything wires to the mini.
