# Scorecard

The rubric is a **grid**: 5 dimensions × 3 tenure states. Each cell scored **0–4**, anchored — every score has a written behavioral definition so the number means the same thing across runs, across time, and (if relevant) across agents.

## Universal 0–4 anchors

| Score | Meaning |
|-------|---------|
| 0 | Absent / broken |
| 1 | Present but unreliable |
| 2 | Works with babysitting |
| 3 | Works, occasional friction |
| 4 | Invisible — it just works |

## The grid

Score each dimension in each tenure state where it applies. `—` = not meaningful in that state.

| Dimension | Cold start | Warming | Warmed |
|-----------|-----------|---------|--------|
| D1 Competence | task done w/o handholding | — (≈ constant) | task done; warmed agent may *fake* higher via known context — isolate |
| D2 Memory | — (nothing to remember yet) | **sessions-to-stick** (the real number) | recall is invisible; re-asks = failure |
| D3 Customization | quality of **defaults** out of the box | shaping takes effect | depth of tunability; effort-to-effect |
| D4 Texture | asking many Qs = **correct** (onboarding) | asks fewer as it learns | asking known Qs = **failure**; anticipates |
| D5 Trust | earned by **honesty about limits** | the warming slope itself | earned by **anticipation**; slope flat-high OK |

The D4 row is the clearest proof of why tenure matters: the *same behavior* (asking lots of questions) scores 4 cold and 1 warmed.

## Per-dimension criteria

### D1 — Competence
- **Probe:** fixed suite of ~10–15 tasks from real work (`scenarios/suite.md`), not generic benchmarks.
- **Score on:** completion without handholding · correctness · recovers from its *own* errors vs. needs rescue.
- **Hermes anchor:** "Refactor this module, run the tests" via ACP. 4 = finishes and self-corrects. 2 = stalls on a tracked-tree repo, needs intervention (a known Hermes failure mode).

### D2 — Memory & continuity *(the differentiator)*
- **Probe:** scripted multi-session tell/recall (`probes/memory-probes.md`).
- **Score on:**
  - **Preference recall** — stated once → honored later unprompted.
  - **Correction stickiness** — corrected once → stays corrected, or re-corrected forever?
  - **Context accumulation** — learns your naming/repos/concerns, or starts cold?
- **Report as sessions-to-stick**, not pass/fail. 1 session = 4. ≥5 sessions = 1.
- **Hermes anchor:** "I never want italics in designs" on Monday → fresh session Friday asks for a design. Italics present = ≤1. Honored unprompted = 4.

### D3 — Customization & fit
- **Probe:** change a config/instruction → verify behavior *moved* in the intended direction.
- **Score on:** can you shape it at all · change takes effect · persists · effort-per-unit-of-change.
- **Cold-start variant:** how good are defaults *before* anyone configures anything.
- **Hermes anchor:** change the system instruction on the mini, resend the same task, confirm output changed as intended. One-line tune > rebuild.

### D4 — Collaboration texture
- **Probe:** deliberately ambiguous tasks + tasks where it *should* push back + tasks it *can't* finish (`probes/texture-probes.md`).
- **Score on:**
  - **Asks vs. guesses** — clarifies genuine ambiguity, doesn't interrupt on the obvious.
  - **Surfaces disagreement** — flags a bad idea vs. silently complies.
  - **Knows when stuck** — says "I'm blocked" vs. loops.
- **Tenure-sensitive** (see grid): same question scores opposite cold vs. warmed.
- **Hermes anchor:** under-specified task ("make the dashboard better"). 4 = asks the right one or two questions. 1 = barrels ahead, or drowns you in questions.

### D5 — Trust trajectory
- **Probe:** one question, answered **weekly**: "Would I delegate more to it than last week, or less?"
- **Score on:** the **sign of the slope**, not the level. Flat-high is fine. Trending-up is the win. Trending-down = something in D1–D4 is decaying — go find which.
- **Cold-start variant:** the *first-two-weeks trust curve for a new user* is the single most important artifact — it's the onboarding funnel.
- **Hermes anchor:** Week 1 supervise every ACP run → Week 3 fire-and-forget overnight jobs. That delta *is* the score.

## How to read a filled scorecard

- A high **warmed** column with a low **cold-start** column = **cold-start cliff**. Great for you, broken for new users.
- A flat D5 slope with decent D1 = **no warming**. A good tool, never a coworker.
- Low D5 at cold start with high D1 = likely **cold-start dishonesty** (competent but burns trust by faking familiarity).
