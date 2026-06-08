# Memory Probes (D2)

Scripted multi-session tell/recall sequences. This is the **only** rigorous way to test continuity — it cannot be done single-shot by construction. The output of each probe is a number: **sessions-to-stick**.

## How to run

1. **Session 1:** deliver the "tell." Note it.
2. **Sessions 2…N:** in a *fresh session* (no reminder, no re-statement), trigger a situation where the remembered fact *should* apply.
3. **Score:** the session number at which Hermes first honors it unprompted = sessions-to-stick. Lower is better. 1 = 4/4. ≥5 = 1/4. Never = 0/4 (no-warming failure).

Run probes in parallel across the warming window — don't serialize them, or the eval takes weeks.

## P1 — Preference recall (the italics test)

- **Tell (S1):** "I never want italics in my designs. Use weight, size, or color for emphasis."
- **Trigger (later):** ask for any design/UI artifact, fresh session, no reminder.
- **Pass:** output has no italics, emphasis done another way.
- **Real:** this is a genuine Oliver preference (in his memory). A coworker that needs this said twice is mediocre; once is good.

## P2 — Correction stickiness

- **Tell (S1):** correct a specific behavior once — e.g. "don't add box-shadows, the design system is flat."
- **Trigger (later):** a task where the wrong behavior would naturally recur.
- **Pass:** correction holds without re-correction.
- **No-warming signature:** if you re-correct the same thing every few sessions, sessions-to-stick never converges. This is the "iterative fix loop, 49% of sessions" pattern made measurable.

## P3 — Context accumulation (naming / repos)

- **Tell (S1):** use your real shorthand naturally — e.g. refer to "the mini," "newth.io is gated," a repo by its short name.
- **Trigger (later):** use the shorthand again, fresh session, and see if Hermes resolves it without asking.
- **Pass:** it knows what "the mini" / "the dash repo" means without a re-explanation.
- **Why it matters:** this is the difference between a coworker who's been here a month and a contractor who needs the glossary every time.

## P4 — Cross-surface memory

- **Tell:** state a fact via the **messaging bridge** (Telegram/Slack).
- **Trigger:** reference it later via the **ACP coding surface** (or vice versa).
- **Pass:** memory is unified across surfaces, not siloed per channel.
- **Why it matters:** a coworker is one entity. If Hermes-on-Slack and Hermes-on-ACP don't share memory, it's two tools wearing one name.

## P5 — Negative memory (knows what NOT to remember)

- **Tell:** something explicitly ephemeral — "just for this one task, do X."
- **Trigger:** a later unrelated task.
- **Pass:** it does NOT carry the one-off forward as a standing rule.
- **Why it matters:** over-remembering is also a failure. A good coworker distinguishes a standing preference from a one-time instruction. This guards against P1–P3 being gamed by "remember everything forever."

## Reporting

| Probe | Tell | sessions-to-stick | D2 score | Notes |
|-------|------|-------------------|----------|-------|
| P1 italics | … | | /4 | |
| P2 correction | … | | /4 | |
| P3 naming | … | | /4 | |
| P4 cross-surface | … | | /4 | |
| P5 negative | … | | /4 | |

D2 overall = the profile across these, weighted toward P2 (stickiness) and P1 (recall) — the two that map directly to Oliver's known friction patterns.
