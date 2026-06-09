# AGENTS.md

How to think about this framework before you touch it. This is the mental model, not a task list — for contribution mechanics see [CONTRIBUTING.md](CONTRIBUTING.md), for voice see [TASTE.md](TASTE.md).

## The one idea

Evaluate the week, not the task. This repo scores an agent as a **coworker** — a relationship that gets better or worse over time — not as a tool you grade once. Every design choice follows from that. If a change makes the eval better at scoring a single task in isolation, it's probably pulling in the wrong direction.

The corollary: a scorecard run once is worthless. Its value is the **delta between runs**. Anything that can't be compared across time or across agents is not yet a measurement here.

## What the five dimensions are for

| | | Load-bearing? |
|---|---|---|
| D1 Competence | Can it do the work, repeatably? | The floor. Necessary, least differentiating. |
| D2 Memory | Does it remember what matters, and *only* that? | Core. The clearest tool-vs-coworker split. |
| D3 Customization | Can I shape it, and does it stick? | Core. |
| D4 Texture | Does it ask, push back, admit when stuck? | Core. |
| D5 Reliance fit | Do I delegate appropriately? | The headline number — but only as a trend. |

D1 is table stakes; do not let the eval collapse into a D1 benchmark (that's what `docs/frameworks.md` quarantines). D2–D4 are where "coworker" is won. D5 is what you'd quote, and it's meaningless as a snapshot.

## The two corrections — guard these hardest

Two obvious framings are half-wrong, and most naive agent evals get them wrong. They are the easiest things to accidentally break.

1. **Memory is a pair, never a single number.** "Remember more" rewards hoarding — every one-off becomes a standing rule. So D2 is always **durability paired with discrimination**. A change that raises a memory score by storing/applying more, without checking over-application, is a regression even if the number goes up.
2. **Reliance is calibrated, never maximized.** "Delegate more" rewards over-trust, and one bad delegation can cost more than weeks of saved time. D5 is a 2x2 (relied/overrode × agent right/wrong), not a delegation-volume line. A change that treats "more delegation" as the win is wrong.

If you find yourself optimizing for "remember more" or "delegate more," stop — you've reintroduced the exact failure the framework was built to catch.

## The tenure axis — why the same behavior scores differently

An agent is two products depending on how much it knows you. The criteria **flip** across tenure:

- **Cold start** (new user, zero memory): asking many onboarding questions is *correct*; honesty about what it can't know is the win.
- **Warmed** (weeks in): asking those same questions is a *failure*; anticipation is the win.

This is the proof that you cannot score texture or reliance without the tenure axis. When editing any dimension, ask: does this criterion hold at cold start *and* warmed, and does it flip correctly between them?

## The failure modes the whole thing exists to catch

A filled scorecard is read for these patterns, not just totals:

- **Cold-start cliff** — high warmed, low cold. Magic for the builder, unusable for anyone new. A personal agent is at maximum risk, and the builder is least able to see it because they are never cold. The wiped-memory cold-start run (`docs/tenure.md`) manufactures the cold start you can't otherwise observe — it's the highest-information pass.
- **No warming** — flat D5, decent D1; session 50 feels like session 1. A good tool that never became a coworker.
- **Cold-start dishonesty** — faking familiarity it can't have. Burns trust before there's any to spend.
- **Hoarder** — high D2 durability *and* high over-application. The pair catches what a single memory score hides.
- **Drift to over-reliance** — rising deference the agent hasn't earned. The 2x2 catches what a volume line would reward.

## Hard rules when editing

- **Agent-neutral method, labeled examples.** The method applies to any coworker agent. Hermes is *the worked example*, never the assumed subject. Keep concrete examples clearly marked (`**Hermes example:**`, anchors). Don't let Hermes specifics become load-bearing in a sentence about the method.
- **Soft claims are grounded.** D2/D4/D5 are the easiest to fake, so each rests on a published method in `docs/references.md`. New methodological claims need a verified citation, not a gut call. Don't add a link you haven't opened.
- **Benchmarks live in `docs/frameworks.md`, nowhere else.** They measure the engine; this scores the coworker. Quarantining them keeps the eval from collapsing into a benchmark roundup.
- **Probes must be honest.** A probe must be answerable only from the thing it measures and must not restate the planted fact. Every memory probe runs against a NullMemory control.
- **Run for consistency, not best-of.** Report pass^k (all-of-k succeed), not pass@1. A coworker you can't trust to repeat is not a coworker.
- **The invariants above are enforced in `agent_eval/` and pinned by `tests/`.** The memory pair, the NullMemory control, the restatement lint, the 2x2, pass^k as headline — a code change that weakens one must fail a test; if it doesn't, add the test. Run `python -m pytest` before pushing.

## Where things live

- `docs/proposal.md` — the full method (read this first)
- `docs/harness.md` — the runnable harness; `agent_eval/` is the code, `tests/` pin the invariants
- `configs/` — per-agent adapter configs (OpenClaw, Hermes, mock, generic shell/http)
- `docs/scorecard.md` — the rubric, dimensions × tenure, 0–4 anchors
- `docs/tenure.md` — the three passes incl. the wiped-memory cold start
- `docs/frameworks.md` — framework comparison + OSS tooling + benchmarks
- `docs/references.md` — the published method behind each dimension
- `scenarios/suite.md` — the D1/D3 task suite (template; fill with real work)
- `probes/memory.md` — D2 durability paired with discrimination
- `probes/texture.md` — D4 ask/push-back/admit-stuck + the journal
- `scorecards/template.md` — a blank dated run
