# Contributing

This repo is a method, not a product. The most useful contributions sharpen the method or port it to a new agent.

## What helps most

- **Fill the scenario suite with real tasks.** [scenarios/suite.md](scenarios/suite.md) ships as a template. A filled suite — concrete prompts and pass criteria from real work — is what turns the rubric into a baseline. This is the first runnable step.
- **Add or refine a probe.** New memory ([probes/memory.md](probes/memory.md)) or texture ([probes/texture.md](probes/texture.md)) probes that test a coworker behavior the current set misses. A probe must be answerable only from the thing it measures, and must not restate the planted fact.
- **Ground a claim.** If a dimension rests on a method, it should cite one ([docs/references.md](docs/references.md)). New citations are welcome with a verified link (arXiv abs, DOI, or ACL Anthology) and a one-line note on what it contributes and its limitation. Do not add a link you have not opened.
- **Report a run.** Score a real agent against the rubric and share the dated scorecard. Cross-agent data is the point.

## House rules

- The method stays agent-neutral; Hermes is the worked example, never the assumed subject. Keep concrete examples clearly labeled.
- Match the voice: terse, claim-first, no marketing, no emoji, no `---` dividers. See [TASTE.md](TASTE.md).
- Keep the two corrections intact. Memory is always durability *paired with* discrimination; reliance is always calibrated, never maximized. A change that scores "remember more" or "delegate more" as a win is a regression.
- Cross-doc links are relative. Verify links resolve before opening a PR.

## Process

Open an issue to discuss a larger change first. For small fixes (typo, broken link, a citation), a PR is fine. Keep PRs scoped to one concern.
