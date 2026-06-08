# Scenario Suite (D1 / D3)

The regression net. ~10–15 tasks drawn from **real work**, not generic benchmarks. Re-run after every config change; run from both a cold-start (wiped) and warmed state.

## Why real tasks, not benchmarks

Generic benchmarks (SWE-bench, HumanEval) measure the *engine*. You're evaluating the *coworker* — so the tasks must be the things you'd actually hand a coworker, in your actual repos, with your actual conventions. A benchmark score tells you nothing about whether Hermes is a good coworker *for Oliver*.

## How to use

1. Replace the placeholder tasks below with real ones. Keep the mix (see categories).
2. For each task, write a concrete **pass/fail criterion** before running — not "did it do well" but "the tests pass and it didn't need rescue."
3. Score each on the 0–4 anchors (`docs/scorecard.md`). Record handholding count.
4. Re-run the *same* suite after any config/model/tool change. The diff is your regression signal.

## Category mix (keep roughly balanced)

- **Routine** (3–4): the bread-and-butter tasks you'd delegate daily. Tests baseline reliability.
- **Multi-step** (3–4): tasks needing a plan + several tool calls + self-correction. Tests autonomy.
- **Ambiguous-on-purpose** (2–3): under-specified, to see if it asks vs. guesses (overlaps D4).
- **Stall-prone** (2): tasks on known-hard surfaces (large tracked-tree repos) where Hermes has stalled before. Tests recovery.
- **Customization-sensitive** (1–2): tasks whose *correct* output depends on a preference you've configured (e.g. flat design, no italics). Tests D3.

## Task template

```
### S<n> — <short title>
- Category: routine | multi-step | ambiguous | stall-prone | customization
- Surface: ACP coding | messaging bridge | other
- Prompt given to Hermes: "<exact text>"
- Pass criterion: <concrete, checkable — e.g. "tests green, ≤1 clarifying Q, no rescue">
- Cold-start note: <what a stranger could/couldn't know to do this>
- Warmed score: _ /4   Cold score: _ /4   Handholding count: _
```

## Placeholder tasks (replace with real ones)

### S1 — Refactor a module and run its tests
- Category: multi-step · Surface: ACP coding
- Prompt: "<your real module + 'refactor X and make the tests pass'>"
- Pass criterion: tests green, self-corrects on failure, no manual rescue.
- Cold-start note: a stranger can do this from the repo alone — good cold-start task.

### S2 — A task in a large tracked-tree repo
- Category: stall-prone · Surface: ACP coding
- Pass criterion: does NOT stall; if it does, does it *say so* (→ D4) rather than loop.

### S3 — A design task gated on a configured preference
- Category: customization · Surface: messaging bridge or ACP
- Prompt: "<a UI/design task>"
- Pass criterion: honors the configured preference (e.g. flat, no italics) *without* being reminded in-task. Cold-start variant: tests whether the *default* leans the right way.

### S4 — A deliberately under-specified request
- Category: ambiguous · Surface: any
- Prompt: "make the dashboard better"
- Pass criterion: asks the right one or two questions; does not barrel ahead, does not interrogate.

> Add S5–S15 from real work. Aim for ~12 total across the category mix.
