# agent-eval

a method for evaluating an AI coworker — memory, customization, trust over time, not one-shot task scores.

evaluate the week, not the task.

benchmarks score an agent on one task in isolation. tells you the engine works. tells you nothing about whether you'd want to work with the thing for a month. a coworker is judged on the relationship — does it remember what you told it, does it learn your conventions, does it know when to ask, does it get better the longer you use it. none of that shows up in a pass-rate.

this repo is a method for scoring that. Hermes (Oliver's mini agent) is the worked example, but it applies to any agent you'd treat as a coworker rather than a tool.

## what gets scored

five dimensions, 0 to 4, across three tenure states — brand-new user, a few sessions in, weeks in. same behavior can score differently by tenure. asking lots of questions is good onboarding on day one and a failure once it should know you.

| | dimension | the question |
|---|-----------|--------------|
| D1 | competence | can it do the work, repeatably? |
| D2 | memory | does it remember what matters, and only that? |
| D3 | customization | can i shape it, and does the change stick? |
| D4 | texture | does it ask, push back, admit when stuck? |
| D5 | reliance fit | do i delegate to it appropriately? |

D1 is the floor. D2 through D4 are where coworker diverges from tool. D5 is the number you'd quote, and it only reads as a trend.

## the two corrections that keep it honest

two framings look like progress and reward the wrong thing. the eval pairs each against its failure mode.

- **memory.** "remember more" rewards hoarding — every one-off instruction becomes a standing rule. D2 pairs durability (does a preference stick?) against over-application (does an ephemeral one wrongly persist?).
- **reliance.** "delegate more" rewards over-trust, and one bad delegation can cost more than weeks of saved time. D5 scores calibrated reliance — relied when the agent was right, overrode when it was wrong — not delegation volume.

both come from the trust-and-memory literature, cited in `docs/references.md`.

## repo map

| path | what's in it |
|------|--------------|
| `docs/proposal.md` | the full method. |
| `docs/scorecard.md` | the rubric: five dimensions by tenure, scored 0 to 4. |
| `docs/tenure-protocol.md` | the three passes, including the wiped-memory cold-start run. |
| `docs/framework-comparison.md` | comparing whole frameworks, and the OSS tooling per stack layer for running the eval. benchmarks live here. |
| `docs/references.md` | the published method behind each dimension. |
| `scenarios/suite.md` | the D1/D3 task suite — a template, fill with real work. |
| `probes/memory-probes.md` | D2 multi-session tell/recall, durability paired with discrimination. |
| `probes/texture-probes.md` | D4 ask/push-back/admit-stuck, plus the daily journal. |
| `scorecards/template.md` | a blank scored run with a date column. |

## status

> [!NOTE]
> design-only. no code drives Hermes yet. first runnable step is filling `scenarios/suite.md` with real tasks — that turns the rubric into a baseline.
