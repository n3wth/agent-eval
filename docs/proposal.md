# Proposal: Evaluating an AI Coworker

A method and scorecard, worked through Hermes (Oliver's mini agent, reachable via the `hermes-acp` skill on the mini and the messaging bridge MCP).

## 1. The premise

A coworker is not a tool you grade once. A tool you evaluate on output quality. A coworker you evaluate on the **relationship over time** — does working with it get better or worse the longer you do it? That reframes everything: the unit of evaluation is not a task, it's a *week*.

Two halves most evals collapse into one and get wrong:

- A **scorecard** — the *what* (dimensions and criteria). See `scorecard.md`.
- A **method** — the *how* (longitudinal, not single-shot). See §4.

The scorecard is worthless run once. Its value is the **delta between runs**.

The trap to name up front: it is tempting to score only what's cheap to measure (did the task pass?). But task pass-rate is the floor, not the differentiator. Coworker-ness lives in memory, fit, and collaboration texture — softer to measure, and the entire point. An eval that doesn't force you to measure the soft dimensions has failed before it starts.

## 2. Five dimensions

| #  | Dimension              | The question it answers                | Why it matters for "coworker"                    |
|----|------------------------|----------------------------------------|--------------------------------------------------|
| D1 | Competence             | Can it do the actual work?             | Table stakes. Necessary, least differentiating.  |
| D2 | Memory & continuity    | Does it remember me across sessions?   | *The* coworker test. A tool forgets; a coworker accumulates. |
| D3 | Customization & fit    | Can I shape it, and does shaping stick?| A coworker you can't train is a contractor.      |
| D4 | Collaboration texture  | Does it ask / push back / admit-stuck? | The difference between a colleague and a slot machine. |
| D5 | Trust trajectory       | Would I delegate *more* than last week?| The integral of the other four. The real score.  |

D1 is the floor. D2–D4 are where "coworker" is won or lost. D5 is the single number you'd quote — readable only as a *trend*, never a snapshot.

Full criteria and anchors: `scorecard.md`.

## 3. The tenure axis (the second dimension of the grid)

The five dimensions quietly assume *you, warmed in after weeks of use*. But an AI coworker is two different products depending on **how much it already knows about the person sitting down**. The cold-start stranger and the warmed-in colleague are different evals.

Three states:

| State        | Who                                  | What "good" looks like |
|--------------|--------------------------------------|------------------------|
| Cold start   | New user, zero memory, first session | Useful *without* knowing you. Asks the right onboarding questions. Honest about what it can't know. Fast time-to-first-value. |
| Warming      | A few sessions / days in             | *Visibly* getting better. Corrections stick. The "it remembered!" moment lands. |
| Warmed       | Weeks in, rich memory                | Invisible competence. Anticipates. Rarely re-asks. |

The criteria *flip* across this axis — most sharply for D4: at cold start, asking many questions is **correct** (good onboarding); when warmed, asking the same questions is a **failure**. Same behavior, opposite score. That's the proof you cannot evaluate texture without the tenure axis.

Three failure modes the axis catches that a flat scorecard misses:

1. **Cold-start cliff** — magic for warmed users, unusable for new ones. Endemic to personal agents built by/for one person. Hermes is exactly this risk profile.
2. **No warming** — competent but flat; session 50 feels like session 1. A good tool that never becomes a coworker. Oliver's "iterative fix loop, 49% of sessions" pattern is a no-warming signature.
3. **Cold-start dishonesty** — pretends to know you when it doesn't (hallucinated familiarity). Burns trust before there's any to spend.

Protocol for running the three passes — including the wiped-memory cold-start run — is in `tenure-protocol.md`.

## 4. The method

Four instruments, escalating in cost and signal:

1. **Fixed scenario suite** (D1, D3) — ~10–15 tasks from *real work*, not generic benchmarks. Re-run after *every* config change. This is the regression net. → `scenarios/suite.md`
2. **Memory probe set** (D2) — scripted tell-then-recall multi-session sequences. The only rigorous way to test continuity; cannot be done single-shot by construction. Report as *sessions-to-stick*, not pass/fail. → `probes/memory-probes.md`
3. **Daily-use journal** (D4) — 1–2 weeks of real use, logging friction, re-corrections, "wow" moments per session. Oliver already produces this genre (the Insights Report on Claude *is* a D4 journal) — point the same lens at Hermes. → `probes/texture-probes.md`
4. **Weekly trust-delta** (D5) — one line: "would I delegate more than last week?" Read the *sign of the slope*.

**Cadence:** baseline all five (cold + warmed passes) → use daily 1–2 weeks → re-score weekly. The deliverable is a scorecard *with a date column*, so you watch the trend. → `scorecards/template.md`

## 5. Why this fits Hermes specifically

- Hermes is reachable two ways — the **messaging bridge** (the MCP tools) and the **ACP coding surface** (the `hermes-acp` skill). The eval drives it as a *whole running agent*, end-to-end; the coworker experience is the integration, not any one endpoint.
- It's **yours** — provider/model/tools/memory all configurable. D3 (customization) is a rich axis, and the scenario suite doubles as a regression net *while you build*.
- Oliver's own history is the eval spec in disguise: iterative fix loops (D2 correction-stickiness), over-styling friction (D2 preference recall — the "never italics" test is real), Nightshift anti-stall (D4 knows-when-stuck).
- Hermes is built by/for Oliver, warmed on his context — so it's at **maximum risk of the cold-start cliff and Oliver is least able to see it**, because he is never cold. The wiped-memory cold-start pass is the highest-information run in the whole proposal.

## 6. One line

Evaluate the *week, not the task*. Five dimensions, three tenure states, 0–4 anchored; run via scenario suite + memory probes + daily journal; headline is trust-trajectory's slope. The soft dimensions and the cold-start pass are the differentiators — skip them and you've measured the engine, not the coworker.
