# References & Grounding

The methods this eval uses, mapped to the dimension each one hardens. This is methodology grounding, not a benchmark leaderboard. Specific leaderboard numbers are point-in-time and deliberately omitted; re-verify any score before citing it. Benchmarks themselves live in [framework-comparison.md](framework-comparison.md), not here, because they measure the engine, not the coworker.

Each entry: what it gives the eval, and its limitation.

## D5 — Reliance fit (the largest correction)

The original D5 ("would I delegate more than last week") was wrong, not just imprecise. The trust-in-automation literature is explicit that the target is calibrated reliance, not maximal reliance.

- **[Lee & See (2004), "Trust in Automation: Designing for Appropriate Reliance."](https://journals.sagepub.com/doi/10.1518/hfes.46.1.50_30392)** The conceptual backbone: trust is an attitude, reliance is the behavior, the goal is matching reliance to actual capability. **Limitation:** pre-LLM.
- **[Schemmer et al. (2023, CHI), "Appropriate Reliance on AI Advice."](https://arxiv.org/abs/2302.02187)** The quantitative metric: RAIR (positive AI reliance, correctly deferring when the agent is right) and RSR (positive self-reliance, correctly overriding when it's wrong). Both rising together is calibration improving. **Limitation:** defined for discrete advice tasks; adapt to accept/override events on the ACP surface.
- **[Jian, Bisantz & Drury (2000), Trust in Automation Scale](https://www.tandfonline.com/doi/abs/10.1207/S15327566IJCE0401_04);** modern AI [short-form validation (Frontiers in AI, 2025)](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1582880/full). The validated weekly self-report instrument. **Limitation:** measures attitude, not behavior; pair with RAIR/RSR.
- **[Merritt & Ilgen (2008), "Not All Trust Is Created Equal."](https://journals.sagepub.com/doi/10.1518/001872008X288574)** Dispositional vs. learned trust: the tenure axis in the literature's own vocabulary. Cold start = dispositional, warming slope = learned. **Limitation:** lab task, not agents.
- **Trust-dynamics work (2024–2025):** trust builds slowly, collapses fast after one error, then partially repairs, and is feature-specific. **Use:** read the D5 slope as jagged (one bad week is not a decay trend) and prefer per-capability sub-scores.

## D2 — Memory & continuity (the gameable-metric fix)

- **[LongMemEval (ICLR 2025)](https://arxiv.org/abs/2410.10813).** Five memory abilities including single-session preference recall and knowledge update. **Limitation:** rewards store-everything-verbatim; doesn't penalize over-storage. This is the documented flaw that makes sessions-to-stick gameable on its own.
- **[PrefEval (ICLR 2025)](https://arxiv.org/abs/2502.09597).** Preference following, with the damning result that zero-shot adherence falls below 10% by ~10 turns. **Limitation:** long-context within one conversation, not cross-session; don't cite it as the persistence benchmark.
- **[BEAM, "Beyond a Million Tokens" (2025–2026 preprint, verify venue)](https://arxiv.org/abs/2510.27246).** Includes preference following, knowledge update, abstention, and contradiction resolution, the categories closest to correction-stickiness and over-remembering. **Limitation:** new, synthetic at extreme scale.
- **["Remembering More, Risking More" (2026 preprint, verify), Trigger-Probe + NullMemory](https://arxiv.org/abs/2605.17830).** The template for measuring over-remembering: probe against memory snapshots and a memory-disabled counterfactual; memory-induced violation rises with exposure length. **Use:** the NullMemory control arm and the over-application metric come from here.
- **[Dynamic personalized-agent adaptability (2025 preprint, verify), "sessions to adapt."](https://arxiv.org/abs/2504.06277)** The rigorous version of sessions-to-stick, with a 4-phase protocol (cold-start, build, adapt, perturb). **Limitation:** a protocol proposal, not an adopted leaderboard.
- **Architecture note.** [Letta/MemGPT](https://github.com/letta-ai/letta), [LangGraph](https://github.com/langchain-ai/langgraph)/[LangMem](https://github.com/langchain-ai/langmem), [Mem0](https://github.com/mem0ai/mem0), [Zep](https://github.com/getzep/graphiti), [CrewAI](https://github.com/crewAIInc/crewAI) all expose episodic/semantic/procedural memory differently, and the public Zep-vs-Mem0 benchmark dispute shows vendor numbers aren't comparable. Run your own harness with frozen settings; don't trust cross-vendor scores.

## D4 — Collaboration texture

- **[Sharma et al. (2023, Anthropic), "Towards Understanding Sycophancy."](https://arxiv.org/abs/2310.13548)** The named test for T2 (push-back): script a correct answer, push back, measure fold-rate. Ships an open dataset. **Limitation:** short-turn probes, not multi-week texture.
- **[AbstentionBench (Meta/FAIR, 2025)](https://arxiv.org/abs/2506.09038).** Whether a model abstains or asks on ill-posed input; scale doesn't help and reasoning fine-tuning makes it worse. The scenario taxonomy for T1 (asks vs. guesses). **Limitation:** single-turn QA, not interactive clarification.
- **[CLAMBER](https://aclanthology.org/2024.acl-long.578/) / [CLAM](https://arxiv.org/abs/2212.07769) / [ClarifyMT-Bench](https://arxiv.org/abs/2512.21120) (2024–2025).** The interactive clarification side: did it ask the load-bearing question, and is over-asking scored as failure too. **Limitation:** generic domains.
- **Calibration: [Kadavath et al. (2022)](https://arxiv.org/abs/2207.05221); [Lin, Hilton & Evans (2022)](https://arxiv.org/abs/2205.14334) verbalized confidence.** Expected Calibration Error (ECE) for "appropriate uncertainty": stated confidence should track actual correctness. Frontier models skew overconfident. **Use:** score expressed-confidence claims in T1 and cold-start honesty.
- **["Selectively Quitting Improves LLM Agent Safety" (2025 preprint, verify)](https://arxiv.org/abs/2510.16492)** and agent-failure-attribution work. The closest anchors for T3 (knows-when-stuck), where the eval leads the literature. **Use:** label which kind of stuck occurred (loop, fake-completion, clean hand-back).

## Cold start & onboarding

- **Dispositional trust (Merritt & Ilgen, above)** is the cold-start trust citation.
- **Time-to-First-Value / activation rate** (product-UX). Gives cold start a unit: turns or minutes to first useful output as a stranger. **Limitation:** SaaS-funnel origin, adapt to agents.
- **Hallucinated familiarity** is an over-confidence / false-premise event, measurable with ECE and AbstentionBench's underspecified-context scenario (lacking context, the correct move is to ask).

## Longitudinal method

- **[Bolger, Davis & Rafaeli (2003), diary studies](https://www.annualreviews.org/content/journals/10.1146/annurev.psych.54.101601.145030); Experience Sampling Method.** Formalizes the daily journal: fixed prompts, fixed cadence, within-person deltas, ~2-week window before fatigue. **Limitation:** reactivity (logging changes behavior).
- **[SPACE framework (Forsgren et al., 2021)](https://cacm.acm.org/practice/the-space-of-developer-productivity/).** The Satisfaction dimension for the coding (ACP) surface, and the multidimensional thesis ("productivity is never one metric") that mirrors this proposal's. **Limitation:** team-level origin; you're n=1.
- **Single-Case Experimental Design (ABA/reversal).** Reframes the wiped-memory pass (warmed → wiped → restored) as a recognized method, with washout periods for carryover. The single biggest credibility upgrade to the pitfalls section.

## Framework comparison & reliability (see `framework-comparison.md`)

- **[HAL, Holistic Agent Leaderboard (2025)](https://arxiv.org/abs/2510.11977).** The hold-everything-constant discipline, cost-controlled (accuracy vs. dollars) reporting, and log inspection that catches shortcuts and leakage. The reference for fair framework comparison.
- **pass^k vs. pass@k ([τ-bench origin](https://arxiv.org/abs/2406.12045)).** pass@k (any-of-k) overstates reliability; pass^k (all-of-k) is the operational floor. Report both.
- **["Beyond pass@1: A Reliability Science Framework" (2026 preprint, verify)](https://arxiv.org/abs/2603.29231).** Capability and reliability diverge with task horizon; a model that wins on short tasks can lose on long ones. **Use:** stratify reliability by task duration.

## OSS eval tooling (the per-layer picks in `framework-comparison.md`)

- **Eval harnesses.** [promptfoo](https://github.com/promptfoo/promptfoo) (declarative CLI, regression net; MIT, OpenAI-acquired March 2026, still open), [DeepEval](https://github.com/confident-ai/deepeval) (pytest-style, deep metric library, LLM-as-judge cost), [Ragas](https://github.com/explodinggradients/ragas) (RAG-only), [HAL/hal-harness](https://github.com/princeton-pli/hal-harness) (the framework bake-off harness). **Limitation:** LLM-as-judge metrics need human validation before you trust them.
- **Observability.** [Langfuse](https://github.com/langfuse/langfuse) (MIT, self-hostable Postgres + ClickHouse), [Arize Phoenix](https://github.com/Arize-ai/phoenix) (OTel-native, ELv2), [Laminar](https://github.com/lmnr-ai/lmnr) (built for long-running agents). **Use:** instrument with OpenTelemetry / OpenInference so the backend is swappable.
- **Memory systems under test.** Letta/MemGPT (tiered self-editing), Mem0 (extraction pipeline, wide adoption), Zep/Graphiti (temporal graph), LangMem (LangGraph store). **Limitation:** public LongMemEval/LoCoMo scores are self-reported and not comparable; freeze your own harness.

## A standing caveat

Several of the most useful 2025–2026 sources are recent preprints. The methodological claims here (calibrated reliance, paired memory metrics, pass^k, hold-everything-constant, ABA framing) are corroborated across multiple independent sources and safe to build on. Treat any specific score or leaderboard figure as point-in-time and re-verify before putting it in a final document.
