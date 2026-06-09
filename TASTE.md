# TASTE

Not a style guide. A log of decisions I already made about how these docs read, and why. Taste isn't a rulebook you follow — it's caring enough to keep editing past "good enough," saying "no, not that" until what's left means something. This file can't give you that. It can only stop an AI editor (or a tired me) from dragging the docs back toward the average.

So read it as: here's what I chose, and what I was choosing against. The proposal (`docs/proposal.md`) is the real reference — it shows the voice better than this file describes it.

## What I was choosing against

AI converges on the expected answer: the most popular template, the safest phrasing, the sentence everyone writes. That produces docs that are technically fine and feel like nothing. The whole point of these is that a specific person with specific opinions about evaluating agents wrote them. If an edit makes a doc sound like it could've come from anyone, it's wrong, even if every rule below passes.

## Decisions I made

- **Lead with the claim.** I cut the warm-ups. State the position, then defend it. No "it's worth noting that," no setup paragraph before the point. If a sentence is clearing its throat, I deleted it.
- **One idea per sentence, lengths varied.** A long sentence builds the argument; a short one lands it. I wrote against the flat, uniform rhythm AI defaults to.
- **Concrete nouns, always.** I named the failure mode (cold-start cliff, hoarder, no-warming), the metric (RAIR, pass^k), the real example (the italics test) instead of reaching for a generic word. Specificity is where the person shows up.
- **Active voice.** The agent asks, the score flips, the probe catches.
- **Cite or soften.** Soft claims rest on a named method (`references.md`) or they get hedged down. "From the trust literature," never "studies show." I refused to wave at unnamed authority.
- **Name the trap.** The move I kept reaching for: surface the seductive-wrong framing ("remember more," "delegate more"), then correct it. It's the most "me" thing in the repo. Systematizing it here already dulls it slightly — so use it where it earns its place, don't paint-by-numbers it.

## What I cut on sight

Emojis. Hype words (powerful, seamless, game-changing). `---` dividers. AI-scent vocabulary (delve, leverage, utilize, pivotal, crucial, robust, holistic — except the proper noun HAL Holistic Agent Leaderboard). Formal transitions (moreover, furthermore, additionally, in conclusion). Hedges (perhaps, somewhat, arguably, "might" when I mean "does"). Empty intensifiers (very, really, extremely). Echoes — the same point said twice in different words. Stock openers, formulaic closers, the "No X. No Y. Just Z." cadence.

These are the floor, not the goal. Clearing them makes a doc not-bad. It doesn't make it good.

## Choices that look like mistakes but aren't

- **`(verify venue)` tags on preprints stay.** They read like hedging. They're honesty about source quality — keep them.
- **Terms of art stay.** RAIR, pass^k, ECE, NullMemory, ABA reversal design. The reader needs them. Define on first use, then use freely.
- **Second person stays.** The docs talk to the operator running the eval. That "you" is deliberate.

## Before shipping a sentence

The mechanical checks (does it make a claim, can a skeptic ask "source?", is there a shorter version, does it echo something above) are necessary and boring. The one that matters: does it still sound like a person decided this, or did I let it drift to the default? If the latter, that's the edit.
