# agent-eval

A method for evaluating an AI coworker — not a tool you grade once, but a relationship you measure over time. Hermes (Oliver's mini agent) is the worked example throughout.

The premise: the unit of evaluation is a **week**, not a task. Task pass-rate is the floor. The differentiator is whether working with the agent gets *better the longer you do it* — and whether it's useful to someone it has never met.

## Layout

- `docs/proposal.md` — the full method. Read this first.
- `docs/scorecard.md` — the rubric: 5 dimensions × tenure axis, 0–4 anchored.
- `docs/tenure-protocol.md` — how to run the cold-start / warming / warmed passes, including the wiped-memory cold-start run.
- `scenarios/suite.md` — the D1/D3 task suite template (fill with real tasks).
- `probes/memory-probes.md` — D2 multi-session tell/recall sequences.
- `probes/texture-probes.md` — D4 ask/push-back/admit-stuck probes.
- `scorecards/template.md` — a blank scored run with a date column.

## Status

Design-only. No code drives Hermes yet — the rubric and protocols are reviewed before anything wires to the mini.

## The one line

Evaluate the *week, not the task*. Score five dimensions — competence, memory, fit, texture, trust — on a 0–4 scale, across three tenure states (cold / warming / warmed), and read **trust-trajectory's slope** as the headline. The soft dimensions and the cold-start pass are the differentiators; any eval that skips them measures the engine, not the coworker.
