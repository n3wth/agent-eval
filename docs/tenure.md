# Tenure Protocol

How to run the three tenure passes. The central move: the builder of a personal agent is never cold, so their own usage never surfaces cold-start failure. You have to manufacture one. (e.g. Oliver is never cold on [Hermes](https://github.com/nesquena/hermes-webui).)

The tenure axis has a name in the trust literature: dispositional vs. learned trust (Merritt & Ilgen 2008; see [references.md](references.md)). Cold start measures dispositional trust, what a stranger brings before any interaction. The warming slope measures learned-trust accrual. This isn't a homegrown idea; it maps onto an established split.

## Pass 1 — Cold start (wiped memory)

The highest-information run in the proposal, and the one daily use can never produce. Treat it as a single-case reversal design (ABA): baseline warmed (A), wipe memory (B), restore (A). Naming it this way turns n=1 from a weakness into a recognized method, where the three phase-change moments demonstrate experimental control.

**Setup (cheap, about one afternoon):**
1. Locate Hermes' memory and state store on the mini (memory files, vector store, conversation history, wherever continuity lives).
2. `mv` it aside, do not delete; you restore it after. Confirm Hermes boots with zero knowledge of you.
3. Optionally strip baked-in personalization from the system prompt for a true stranger rather than a stranger with Oliver's defaults. Record which you chose.

**Run:**
- Execute the full [scenarios/suite.md](../scenarios/suite.md) as a stranger. Don't supply context you'd only know as Oliver.
- Score D1 (does it work without knowing you), D3 cold-start variant (default quality), D4 cold-start (does it ask the right onboarding questions, or fake familiarity), D5 cold-start (is it honest about its limits).
- D2 is `—` here by definition; nothing is remembered yet.
- **Give cold start a unit:** time-to-first-value, the turns or minutes until the first useful output as a stranger. That's the onboarding metric.

**Watch for cold-start dishonesty:** any assertion about "your setup, your repos, your preferences" that a wiped agent cannot know. Each instance is an over-confidence event and a D5 hit. The underspecified-context case (it lacks context, so the correct move is to ask, not assert) is the cold-start case made measurable.

**Teardown:** restore the memory store. Use a washout period (no measurement) between phases to handle carryover. Verify Hermes is warm again.

## Pass 2 — Warming (the slope)

The pass that defines D2. The only one needing multiple real sessions.

**Run:** execute the [probes/memory.md](../probes/memory.md) sequences over consecutive sessions, through the 4-phase protocol (cold-start, build, adapt, perturb).
- Plant in session 1, probe recall in session N without reminding. Record sessions-to-stick per probe, paired with the discrimination metrics (over-application, leakage). Durability alone is gameable.
- After the perturbation phase, record sessions-to-re-adapt: how fast a correction sticks.
- Log the "it remembered" moments too; they're the warming payoff that makes a tool feel like a coworker.

**No-warming red flag:** if sessions-to-stick never converges (you re-correct the same thing indefinitely), that's failure mode #2. The iterative-fix-loop pattern is its signature.

## Pass 3 — Warmed (your normal state)

The scorecard run from your real, rich-memory state.

**Run:** the daily-use journal ([probes/texture.md](../probes/texture.md) observed in the wild) for 1–2 weeks, plus the scenario suite re-run after any config change.
- Score D1, D3, D4, D5 warmed. Here, re-asking a known question is a failure, not onboarding.
- **Isolate warmed-competence inflation:** a warmed agent looks more competent because it already knows your repos and conventions. When scoring D1 warmed, note whether the win came from memory or raw capability. Otherwise D1 warmed and D1 cold disagree and you won't know why.

## Reporting the grid

Fill [scorecards/template.md](../scorecards/template.md) with two columns minimum, cold-start and warmed. The gap between them is a finding, not noise: it's the size of the cold-start cliff.

For a real coworker claim (others could adopt Hermes), the cold-start column carries more weight than the warmed one. You already know the warmed experience is good; that's why you built it.

## Threats to validity, and the mitigations

Single-user eval of your own agent has four named threats. Call each out and mitigate:

1. **Novelty effect** — early enthusiasm inflates scores. Mitigate by measuring past the novelty window and reading the slope, not the level. The multi-week design already does this.
2. **Demand characteristics** — the builder unconsciously steers and scores generously. Mitigate by deciding pass criteria before running (scripted probes are a form of pre-registration) and blinded scoring where possible.
3. **Confirmation bias** — you trust your own creation more. The strongest antidote is one real cold-start user, because the builder is structurally never cold.
4. **LLM-as-judge bias** — if any scoring is automated by a model, self-preference and verbosity biases apply. Keep the soft dimensions human-scored or dual-scored.

## A note on whose journal

The daily journal, run by the builder, is a warmed-user journal by definition. A genuine cold-start read needs either a wiped-memory builder (Pass 1, the practical option) or an actual new user driving the agent for two weeks (higher fidelity, more cost). Start with the wiped-memory builder. Escalate to a real new user only if the agent is meant to ship beyond you. **Hermes example:** start with wiped-memory Oliver; escalate to a real new user only if Hermes is meant to ship beyond him.
