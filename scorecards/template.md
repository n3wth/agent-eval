# Scorecard — Run <date>

One filled scorecard is one run. Keep them dated; the trend across runs is the actual product. Minimum two tenure columns (cold-start, warmed). The gap between them is the cold-start cliff.

**Agent:** [Hermes](https://github.com/nesquena/hermes-webui) (mini)  ·  **Config/version:** `<what changed since last run>`  ·  **Date:** `YYYY-MM-DD`

## Grid

| Dimension | Cold start | Warmed | Notes |
|-----------|-----------:|-------:|-------|
| D1 Competence | _/4 | _/4 | report pass^k, not just pass@1 |
| D2 Memory — durability | — | _/4 | sessions-to-stick (P1–P3) |
| D2 Memory — discrimination | — | _/4 | over-application (P5), leakage (P4) |
| D3 Customization | _/4 (defaults) | _/4 (depth) | |
| D4 Texture | _/4 | _/4 | same-question flip applies |
| D5 Reliance fit | _/4 (honesty) | RAIR _ / RSR _ | calibration, not volume |

## Headline

- **Reliance fit (D5):** RAIR and RSR vs. last run. Both up = calibration improving. This is the number you quote, not delegation volume.
- **Cold-start cliff size:** warmed avg − cold avg = ___ (large gap = adoption risk for anyone but the agent's primary user).
- **Memory pair:** durability ___ vs. over-application ___ (high durability + high over-application = hoarder).
- **Dominant friction this run:** <the one thing dragging the score>.

## Failure-mode check

- [ ] Cold-start cliff? (high warmed, low cold)
- [ ] No warming? (flat D5, decent D1, sessions-to-stick not converging)
- [ ] Cold-start dishonesty? (low cold D5 + high D1, faked familiarity)
- [ ] Hoarding? (high D2 durability + high over-application rate)
- [ ] Drifting to over-reliance? (rising RAIR, flat or falling RSR)
- [ ] Warmed-competence inflation isolated? (D1 warmed win attributed to memory vs. capability)

## Deltas since last run

- What config changed: …
- What moved on the scorecard: …
- Regression? (any dimension dropped): …
