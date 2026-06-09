# agent-eval

A method for evaluating an AI coworker: memory, customization, and trust over time, not one-shot task scores.

Evaluate the week, not the task.

Benchmarks score an agent on one task in isolation. That tells you the engine works. It tells you nothing about whether you'd want to work with it for a month. A coworker is judged on the relationship: does it remember what you told it, does it learn your conventions, does it know when to ask, does it get better the longer you use it. None of that shows up in a pass-rate.

This repo is a method for scoring that. Hermes (Oliver's mini agent) is the worked example, but it applies to any agent you'd treat as a coworker rather than a tool.

## What gets scored

Five dimensions, scored 0 to 4, across three tenure states: a brand-new user, a few sessions in, weeks in. The same behavior can score differently by tenure. Asking lots of questions is good onboarding on day one and a failure once the agent should know you.

| | Dimension | The question |
|---|-----------|--------------|
| D1 | Competence | Can it do the work, repeatably? |
| D2 | Memory | Does it remember what matters, and only that? |
| D3 | Customization | Can I shape it, and does the change stick? |
| D4 | Texture | Does it ask, push back, admit when stuck? |
| D5 | Reliance fit | Do I delegate to it appropriately? |

D1 is the floor. D2 through D4 are where coworker diverges from tool. D5 is the number you'd quote, and it only reads as a trend.

## The two corrections that keep it honest

Two framings look like progress and reward the wrong thing. The eval pairs each against its failure mode.

- **Memory.** "Remember more" rewards hoarding, where every one-off instruction becomes a standing rule. D2 pairs durability (does a preference stick?) against over-application (does an ephemeral one wrongly persist?).
- **Reliance.** "Delegate more" rewards over-trust, and one bad delegation can cost more than weeks of saved time. D5 scores calibrated reliance (relied when the agent was right, overrode when it was wrong), not delegation volume.

Both come from the trust-and-memory literature, cited in `docs/references.md`.

## Repo map

| Path | What's in it |
|------|--------------|
| `docs/proposal.md` | The full method. |
| `docs/scorecard.md` | The rubric: five dimensions by tenure, scored 0 to 4. |
| `docs/tenure-protocol.md` | The three passes, including the wiped-memory cold-start run. |
| `docs/framework-comparison.md` | Comparing whole frameworks, and the OSS tooling per stack layer for running the eval. Benchmarks live here. |
| `docs/references.md` | The published method behind each dimension. |
| `scenarios/suite.md` | The D1/D3 task suite (a template; fill with real work). |
| `probes/memory-probes.md` | D2 multi-session tell/recall, durability paired with discrimination. |
| `probes/texture-probes.md` | D4 ask/push-back/admit-stuck, plus the daily journal. |
| `scorecards/template.md` | A blank scored run with a date column. |

## Status

> [!NOTE]
> Design-only. No code drives Hermes yet. The first runnable step is filling `scenarios/suite.md` with real tasks, which turns the rubric into a baseline.
