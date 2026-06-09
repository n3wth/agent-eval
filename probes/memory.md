# Memory Probes (D2)

Scripted multi-session tell/recall sequences. Continuity cannot be tested single-shot by construction, so this is where the eval earns its keep. The output is a **pair** per probe, never a single number: durability (did the agent learn and hold it?) and discrimination (did it learn only what it should have?). Reporting durability alone rewards hoarding, which is the failure mode the discrimination half exists to catch. See [references.md](../docs/references.md) for the literature; the short version is that a single "sessions-to-stick" score is gameable by "store everything verbatim and apply it aggressively."

## The 4-phase protocol

Run probes through four phases, not as one-shot tells:

1. **Cold start** — wiped memory, baseline behavior.
2. **Profile building** — deliver the tells naturally across sessions.
3. **Adaptation test** — probe recall in fresh sessions without restating the fact.
4. **Perturbation** — inject a correction, then test how fast the corrected value sticks (sessions-to-re-adapt).

## Anti-gaming rules (apply to every probe)

- **Hidden probes.** The session-N probe must be answerable only from memory and must not paraphrase the planted fact. If the probe restates the fact, it measures nothing.
- **Naturalistic distractors.** Bury the probe among unrelated sessions. If "plant in session 1, probe in session N" is structurally obvious, the agent complies because it detected the eval, not because it remembered.
- **NullMemory control.** Run each probe against the same agent with memory disabled. The NullMemory delta is what you attribute to memory rather than base-model priors.
- **Isolation.** Run independent probes against separate memory states or fresh instances, so probe A's plant doesn't prime probe B. Randomize order to rule out recency.
- **Footprint budget.** Track memory cost per query (a few thousand tokens is a reasonable ceiling). Penalize hoarding, so efficient discrimination beats storing everything.

## Durability probes

### P1 — Preference recall (the italics test)
- **Tell:** "I never want italics in my designs. Use weight, size, or color for emphasis."
- **Trigger (later, fresh session):** ask for any design or UI artifact.
- **Pass:** no italics, emphasis done another way.
- **Real:** a genuine standing preference. Needing it said twice is mediocre; once is good. ([Hermes](https://github.com/nesquena/hermes-webui) example: this is one of Oliver's real preferences.)

### P2 — Correction stickiness
- **Tell:** correct one behavior once, e.g. "don't add box-shadows, the design system is flat."
- **Trigger (later):** a task where the wrong behavior would naturally recur.
- **Pass:** correction holds with no re-correction.
- **Score two rates separately:** first-correction hold rate (percent of corrections that persist through session N untouched) and reversion rate (percent where the original wrong value resurfaces).
- **No-warming signature:** if you re-correct the same thing every few sessions, sessions-to-stick never converges. This is the "iterative fix loop, 49% of sessions" pattern made measurable.

### P3 — Context accumulation (naming / repos)
- **Tell:** use your own shorthand naturally — a machine, a project, a repo referred to by its short name. (Hermes example: "the mini," "newth.io is gated," a repo by its short name.)
- **Trigger (later, fresh session):** use the shorthand again and see if it resolves without asking.
- **Pass:** it resolves your shorthand (e.g. "the mini" or "the dash repo") with no re-explanation.
- **Why it matters:** the difference between a coworker who's been here a month and a contractor who needs the glossary every time.

## Discrimination probes

### P5 — Negative memory (knows what NOT to remember)

P5 is no longer the speculative probe. It is the second half of the D2 metric. Durability without discrimination is hoarding.

- **Tell:** something explicitly ephemeral, e.g. "just for this one task, keep it short."
- **Trigger:** a later, unrelated task.
- **Pass:** it does NOT carry the one-off forward as a standing rule.
- **Score:** over-application rate, the percent of ephemeral instructions wrongly applied in a later session.
- **Why it matters:** over-remembering is a failure equal to forgetting. A good coworker tells a standing preference from a one-time instruction. Without P5, P1–P3 are gamed by "remember everything forever."

### P4 — Cross-surface memory (unification, and its safety counterpart)
- **Tell:** state a fact via one surface the agent runs on (e.g. a messaging surface).
- **Trigger:** reference it later via a different surface (e.g. the coding surface), and vice versa. (Hermes example: tell via the Telegram/Slack bridge, recall via the ACP coding surface.)
- **Pass:** memory is unified across surfaces, not siloed per channel. Score unification rate, the percent of facts retrievable regardless of write-surface.
- **Safety counterpart (shared stores):** confirm one user's memory never surfaces in another user's session. Score cross-user leakage rate. A unified memory that leaks is worse than a siloed one.
- **Why it matters:** a coworker is one entity. If the agent on one surface and the same agent on another don't share memory, they're two tools wearing one name. No academic benchmark covers this, so the probe is original. (Hermes example: Hermes-on-Slack and Hermes-on-ACP must share memory.)

## Reporting

| Probe | Durability (sessions-to-stick) | Discrimination | NullMemory delta | Notes |
|-------|-------------------------------|----------------|------------------|-------|
| P1 italics | /4 | — | | |
| P2 correction | hold rate / reversion rate | — | | |
| P3 naming | /4 | — | | |
| P4 cross-surface | unification rate | leakage rate | | |
| P5 negative | — | over-application rate | | |

D2 overall is the **pair**: a durability profile (weighted toward whichever friction your agent actually shows — e.g. P2 stickiness and P1 recall) and a discrimination profile (P5 over-application, P4 leakage). Report both. A high durability score next to a high over-application rate is a hoarder, not a coworker.
