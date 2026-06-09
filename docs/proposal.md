# Proposal: Evaluating an AI Coworker

A method and scorecard, worked through Hermes (Oliver's mini agent, reachable via the `hermes-acp` skill on the mini and the messaging bridge MCP).

## 1. The premise

A coworker is not a tool you grade once. You evaluate a tool on output quality; you evaluate a coworker on the relationship over time: does working with it get better or worse the longer you use it? That reframes everything. The unit of evaluation is not a task, it's a week.

Most evals collapse two halves into one. A scorecard: the dimensions and criteria (`scorecard.md`). A method: longitudinal, not single-shot (§4). The scorecard is worthless run once. Its value is the delta between runs.

The trap to name up front: it's tempting to score only what's cheap to measure (did the task pass?). Task pass-rate is the floor, not the differentiator. Coworker-ness lives in memory, fit, and collaboration texture, which are softer to measure and the entire point. An eval that skips the soft dimensions has failed before it starts.

Where the soft dimensions get measured, they're tied to published methods, not vibes (`references.md`). Two of them are corrections to the obvious framing: "remember more" and "delegate more" both look like progress and both are half-wrong. Memory must be paired against over-application; delegation must be calibrated, not maximized. Those two fixes are §3 and the D2/D5 entries in the scorecard.

## 2. Five dimensions

| #  | Dimension              | The question it answers                | Why it matters for "coworker"                    |
|----|------------------------|----------------------------------------|--------------------------------------------------|
| D1 | Competence             | Can it do the actual work?             | Table stakes. Necessary, least differentiating.  |
| D2 | Memory & continuity    | Does it remember me, and only what it should? | The coworker test. A tool forgets; a coworker accumulates, without hoarding. |
| D3 | Customization & fit    | Can I shape it, and does shaping stick?| A coworker you can't train is a contractor.      |
| D4 | Collaboration texture  | Does it ask, push back, admit when stuck? | The difference between a colleague and a slot machine. |
| D5 | Reliance fit           | Do I delegate to it appropriately?     | Calibrated reliance, not maximal. The real score. |

D1 is the floor. D2–D4 are where "coworker" is won or lost. D5 is the single number you'd quote, readable only as a trend, never a snapshot.

Full criteria and anchors: `scorecard.md`. Two dimensions are paired metrics, not single numbers, because the single-number version of each rewards the failure mode:

- **D2** pairs durability (sessions-to-stick) with discrimination (over-application rate). Durability alone rewards hoarding.
- **D5** is a 2x2 of reliance (relied/overrode by agent right/wrong), not a delegation-volume line. Volume alone rewards over-reliance, and one bad delegation can cost more than weeks of saved time.

## 3. The tenure axis

The five dimensions assume a warmed-in user. But an AI coworker is two products depending on how much it already knows the person. The cold-start stranger and the warmed-in colleague are different evals. The split has a name in the trust literature: dispositional trust (what a stranger brings) vs. learned trust (built through use). See `references.md`.

Three states:

| State        | Who                                  | What "good" looks like |
|--------------|--------------------------------------|------------------------|
| Cold start   | New user, zero memory, first session | Useful without knowing you. Asks the right onboarding questions. Honest about what it can't know. Fast time-to-first-value. |
| Warming      | A few sessions or days in            | Visibly getting better. Corrections stick. The "it remembered" moment lands. |
| Warmed       | Weeks in, rich memory                | Invisible competence. Anticipates. Rarely re-asks. |

The criteria flip across this axis, most sharply for D4: at cold start, asking many questions is correct (good onboarding); when warmed, asking the same questions is a failure. Same behavior, opposite score. That's the proof you cannot evaluate texture without the tenure axis.

Three failure modes the axis catches that a flat scorecard misses:

1. **Cold-start cliff** — magic for warmed users, unusable for new ones. Endemic to personal agents built by and for one person. Hermes is exactly this risk profile.
2. **No warming** — competent but flat; session 50 feels like session 1. A good tool that never becomes a coworker. Oliver's "iterative fix loop, 49% of sessions" pattern is a no-warming signature.
3. **Cold-start dishonesty** — pretends to know you when it doesn't (hallucinated familiarity). Burns trust before there's any to spend.

The protocol for running the three passes, including the wiped-memory cold-start run framed as a single-case reversal design, is in `tenure-protocol.md`.

## 4. The method

Four instruments, escalating in cost and signal:

1. **Fixed scenario suite** (D1, D3) — ~10–15 tasks from real work, not generic benchmarks. Re-run after every config change. The regression net. Run each task N times and report pass^k, not just pass@1; consistency is what a coworker needs. → `scenarios/suite.md`
2. **Memory probe set** (D2) — scripted tell-then-recall multi-session sequences, paired with over-application and a NullMemory control. The only rigorous way to test continuity; cannot be done single-shot. → `probes/memory-probes.md`
3. **Daily-use journal** (D4, D5) — 1–2 weeks of real use, formalized as an experience-sampling protocol (fixed prompts, fixed cadence). Oliver already produces this genre; the Insights Report on Claude is a D4 journal. → `probes/texture-probes.md`
4. **Weekly reliance check** (D5) — RAIR and RSR computed from accept/override events, plus a validated trust scale. Read calibration, not volume.

**Cadence:** baseline all five (cold and warmed passes) → use daily for 1–2 weeks → re-score weekly. The deliverable is a scorecard with a date column, so you watch the trend. → `scorecards/template.md`

Comparing whole frameworks (Hermes' stack vs. LangGraph, CrewAI, and the rest) is a separate axis with its own method and its own home for benchmarks. → `framework-comparison.md`

## 5. Why this fits Hermes specifically

- Hermes is reachable two ways, the messaging bridge (the MCP tools) and the ACP coding surface (the `hermes-acp` skill). The eval drives it as a whole running agent, end to end; the coworker experience is the integration, not any one endpoint.
- It's yours. Provider, model, tools, and memory are all configurable. D3 is a rich axis, and the scenario suite doubles as a regression net while you build.
- Oliver's own history is the eval spec in disguise: iterative fix loops (D2 correction-stickiness), over-styling friction (D2 preference recall, the "never italics" test is real), Nightshift anti-stall (D4 knows-when-stuck).
- Hermes is built by and for Oliver, warmed on his context. So it's at maximum risk of the cold-start cliff and Oliver is least able to see it, because he's never cold. The wiped-memory cold-start pass is the highest-information run in the whole proposal.

## 6. One line

Evaluate the week, not the task. Five dimensions, three tenure states, scored 0–4; run via scenario suite, memory probes, and daily journal; headline is calibrated-reliance fit, not delegation volume. The soft dimensions and the cold-start pass are the differentiators. Skip them and you've measured the engine, not the coworker.
