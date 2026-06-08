# Tenure Protocol

How to run the three tenure passes. The central move: **you (Oliver) are never cold**, so your own usage will never surface cold-start failure. You must manufacture a cold start.

## Pass 1 — Cold start (wiped memory)

The highest-information run in the whole proposal, and the one your daily use can never produce.

**Setup (cheap, ~one afternoon):**
1. Locate Hermes' memory/state store on the mini (memory files, vector store, conversation history — wherever continuity lives).
2. `mv` it aside (do not delete — you restore it after). Confirm Hermes now boots with zero knowledge of you.
3. Optionally also neutralize any baked-in personalization in the system prompt, if you want a *true* stranger rather than "stranger with Oliver's defaults." Decide and record which.

**Run:**
- Execute the full `scenarios/suite.md` as a stranger. Do not supply context you'd only know as Oliver.
- Score **D1** (does it work without knowing you), **D3 cold-start variant** (default quality), **D4 cold-start** (does it ask the *right* onboarding questions, or fake familiarity), **D5 cold-start** (is it honest about its limits).
- D2 is `—` here by definition (nothing remembered yet).

**Watch specifically for cold-start dishonesty:** any moment Hermes asserts something about "your setup / your repos / your preferences" that it cannot actually know from a wiped state. Each instance is a D5 hit.

**Teardown:** restore the memory store. Verify Hermes is warm again.

## Pass 2 — Warming (the slope)

The dimension D2 is *defined by*. This is the only pass that needs multiple real sessions.

**Run:** execute the `probes/memory-probes.md` sequences over consecutive sessions.
- Tell it something in session 1. Check recall in session N without reminding.
- Record **sessions-to-stick** per probe. That number *is* the D2 warming score.
- Also subjectively log the "it remembered!" moments — these are the warming payoff that makes a tool feel like a coworker.

**No-warming red flag:** if sessions-to-stick never converges (you re-correct the same thing indefinitely), that's failure mode #2. The iterative-fix-loop pattern is its signature.

## Pass 3 — Warmed (your normal state)

The scorecard as originally conceived. Run from your real, rich-memory state.

**Run:** the daily-use journal (`probes/texture-probes.md` observed in the wild) for 1–2 weeks, plus the scenario suite re-run after any config change.
- Score **D1/D3/D4/D5 warmed**. Here, re-asking a known question is a *failure*, not onboarding.
- **Isolate the warmed-competence inflation:** a warmed agent looks more competent because it already knows your repos/conventions. When scoring D1 warmed, note where the win came from *memory* vs. *raw capability* — otherwise D1 warmed and D1 cold disagree and you won't know why.

## Reporting the grid

Fill `scorecards/template.md` with **two columns minimum**: cold-start and warmed. The **gap between them is a finding, not noise** — it's the size of the cold-start cliff.

For a real coworker claim (others could adopt Hermes), the cold-start column carries more weight than the warmed one, because you already know the warmed experience is good — that's why you built it.

## A note on whose journal

The §4 daily journal, run by Oliver, is a *warmed*-user journal by definition. A genuine cold-start read needs either:
- a wiped-memory Oliver (Pass 1, the practical option), or
- an actual new user driving Hermes for two weeks (higher fidelity, more cost).

Start with wiped-memory Oliver. Escalate to a real new user only if Hermes is meant to ship beyond you.
