# Comparing Agentic Frameworks

The coworker eval (`proposal.md`) scores one agent as a relationship. Comparing frameworks (LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, LlamaIndex, smolagents, a raw harness, or Hermes' own stack) is a different axis. This doc handles it.

This is also where benchmarks belong. They measure the engine and the task layer, which is exactly what framework comparison needs and what the coworker dimensions (D2, D4, D5) have to stay clear of. Quarantining benchmarks here keeps the rest of the eval from collapsing into a benchmark roundup.

## The category error to avoid first

Three layers of the stack, often conflated:

```
what you experience  ->  THE AGENT (Hermes-the-coworker)   <- proposal.md scores this
what builds it       ->  THE FRAMEWORK (LangGraph, CrewAI)  <- this doc
what runs underneath ->  THE MODEL (Opus, Llama)            <- benchmarks
```

A framework has no memory or texture of its own. It gives you the primitives to build them. So you don't score a framework on D2 directly. You score how well it lets you build a thing that scores well on D2. That reframe is the whole method.

## Two questions people conflate

This fork determines everything. Most framework "evals" online are sloppy because they mix the two silently.

**Q1 — Which framework produces the better coworker?** (outcome)
Build the same agent on each framework, then run the 5-dimension scorecard on each build. The framework is the independent variable; the coworker scores are the output. The coworker eval becomes the measurement instrument.

**Q2 — Which framework is better to build with?** (substrate)
Forget the resulting agent's quality. Evaluate the framework as an engineering substrate: how hard to build, debug, extend, operate. A separate scorecard, below.

Score both, separately. A framework can win Q1 and lose Q2 (great agent, hell to maintain) or the reverse.

## Q1: the outcome method

The trap is the confound. If you build the agent differently on each framework, you're comparing your two implementations, not the frameworks. The fair-comparison discipline (the HAL "holistic agent leaderboard" work is the reference; see `references.md`):

**Hold constant across arms:** model and version, sampling params (temperature, seed), system prompt and instructions, tool set and tool implementations, task dataset and grader, retry/timeout policy, and a fixed compute/cost budget.

**Vary only:** the orchestration framework.

**The confounds people get wrong:**
- **Scaffold confound.** Frameworks default to different prompts and tool formatting. Normalize these, or you're measuring prompt engineering, not the framework.
- **Cost not reported.** Plot accuracy vs. dollars (a Pareto frontier), not accuracy alone. The top-accuracy config is usually not on the efficient frontier.
- **Reasoning-effort confound.** More reasoning effort often lowers accuracy. Pin it across arms.
- **Single runs.** Variance is large. Run N rollouts per task and report pass^k (all-of-k succeed), not just pass@1 (best-of-k). The consistency gap between them is what kills agents in production.
- **Shortcuts and leakage.** Read the traces. Published harnesses have caught agents searching for the benchmark answer instead of solving the task, and taking unsafe actions. Scores alone hide this.

**Add a raw-harness control arm.** Bare model + tools, no framework. It's the latency and cost floor and the cleanest control. It isolates what each framework's abstraction costs (latency, tokens, lost control) against what it buys (observability, human-in-the-loop, memory).

## Q2: the substrate scorecard

Frameworks live or die on different things than coworkers do. Score each 0–4.

| #  | Dimension | The question | Why it bites |
|----|-----------|-------------|--------------|
| F1 | Control vs. magic | Can you see and override what the agent does, or is it a black box? | The top reason teams rip out a framework. LangGraph (explicit graph) vs. CrewAI (more magic) is this axis. |
| F2 | Observability / debuggability | When it misbehaves, can you find out why? | An agent loop you can't trace is unmaintainable no matter how good it is when it works. |
| F3 | State & memory primitives | How much of D2 does the framework give you vs. force you to build? | Directly predicts the Q1 D2 score. |
| F4 | Human-in-the-loop / interrupts | First-class pause/approve/resume, or bolted on? | Predicts the Q1 D4 score. Frameworks differ enormously here; checkpoint-based ones (LangGraph) make it native. |
| F5 | Escape hatches / lock-in | Can you drop to raw model calls when the abstraction fights you? Portability off the framework? | The abstraction will fight you eventually. Cost of leaving is real risk. |
| F6 | Operational surface | Latency overhead, failure modes, deploy and runtime cost the framework imposes. | Extra orchestration hops add latency and failure points the bare harness doesn't have. |

F1 is usually the headline. Most framework regret traces to "too much magic, couldn't control it when it mattered."

## How the named frameworks differ (orientation, not scores)

Treat any leaderboard number as point-in-time and re-verify before citing.

- **LangGraph** — explicit graph/DAG, conditional edges, checkpointer. Max control, native human-in-the-loop and rollback, native tracing via LangSmith. Owns the enterprise-control tier.
- **CrewAI** — role-based "crew," least boilerplate for multi-agent-with-roles, built-in short/long/entity memory stores. More magic, less control.
- **AutoGen** — conversation and event-driven multi-agent.
- **OpenAI Agents SDK** — handoff primitive, production-grade, OpenAI-leaning (lock-in risk on F5).
- **smolagents** — minimal, code-as-action (the model writes Python). Easy to inspect; single-agent.
- **LlamaIndex** — data and RAG-centric agents.
- **Raw harness** — the control arm. Floor on cost and latency, ceiling on control, zero framework affordances.

## OSS tooling per area, for running the eval

The frameworks above are what you'd build an agent on. This section is what you'd use to evaluate one. Different job, different tools. Organized by the stack layer each lives in, with a pick per area for Hermes' case. All open-source; treat any published score as point-in-time (see the caveat in `references.md`).

The portability rule that spans every layer: instrument with **OpenTelemetry / OpenInference** semantic conventions. Every serious 2026 tool ingests OTel, so tracing once and swapping backends beats coupling the eval to one vendor. This is the F5 (lock-in) lesson applied to the eval harness itself.

### Orchestration (the Q1 contestants)
What you compare. Covered above: **LangGraph** (control + native tracing), **CrewAI** (role-based, batteries-included memory), **AutoGen** (event-driven multi-agent), **smolagents** (minimal, code-as-action), **LlamaIndex** (RAG-centric), plus the **raw-harness** control arm and **Hermes' own stack**.
**Pick for Hermes:** Hermes is the incumbent; LangGraph is the strongest adopt-alternative to bake-off against, because its control and HITL set the bar you'd be giving up bespoke for.

### Observability / tracing (feeds D1 and D4)
Where the trajectory data for outcome-and-process scoring comes from. You can't score "knows when stuck" (D4/T3) or read shortcuts (the HAL discipline) without traces.
- **Langfuse** — MIT, self-hostable (Postgres + ClickHouse), framework-agnostic via OTel. Best when you're iterating on prompts and want full data control.
- **Arize Phoenix** — OTel-native, OpenInference conventions, single-node self-host (ELv2 license). Best if the eval leans on trace-level analysis.
- **Laminar** — OTel-native, built for long-running agents: transcript view, SQL over traces, session replay. Best for debugging agent runs, which is most of what D4 texture scoring is.
**Pick for Hermes:** Langfuse to self-host on the mini (MIT, no license friction, you already run a Langfuse instance per your ClickHouse stack), with OTel instrumentation so Phoenix or Laminar stays a swap away.

### Eval harness (runs the scenario suite, computes the scores)
Where the D1 task suite and pass^k live. This is the layer that turns a run into a number.
- **promptfoo** — declarative YAML test configs, local CLI, strong red-teaming. Lowest-friction for a fixed scenario suite re-run on every config change (your regression net). MIT; acquired by OpenAI March 2026, still open-source.
- **DeepEval** — deepest metric library, pytest-style, CI-friendly. Best when you want many built-in metrics and Python test integration. Note it leans on LLM-as-judge, which adds cost and needs human validation.
- **Ragas** — RAG-specific (faithfulness, context precision/recall). Only if Hermes does retrieval; otherwise skip.
- **HAL (hal-harness)** — the reference implementation of the hold-everything-constant, cost-controlled framework comparison from the Q1 method above. This is the harness for the framework bake-off, not day-to-day scoring.
**Pick for Hermes:** promptfoo for the re-runnable scenario suite (D1/D3 regression net), HAL when you actually run the Q1 framework bake-off. A common $0 stack is promptfoo + Phoenix; richer is DeepEval + Langfuse.

**For a web/UI surface, layer three gates** rather than leaning on one: static analysis (a runtime-guard linter that catches errors a syntax check misses), automated API/backend tests, and a headless-browser smoke test that loads each page and fails on any console error. The [hermes-webui `TESTING.md`](https://github.com/nesquena/hermes-webui/blob/master/TESTING.md) is the reference for this — it splits coverage across those three layers, marks which cases are manual-only (visual polish, responsive breakpoints, mid-stream reload), and writes every manual case as a runnable SETUP → STEPS → EXPECT → FAIL block, so the same doc drives both a human and a browser agent. That dual-audience, layered form is the model for the D1 web-surface portion of the scenario suite.

### Memory layer (the D2 systems under test, and where D2 primitives come from)
For framework comparison these are contestants (which memory system produces better D2 scores); for Hermes they're also adopt-options if you replace homegrown memory.
- **Letta** (formerly MemGPT) — tiered self-editing memory (core/recall/archival), agent curates via tool calls. The strongest open-source self-improving option; also the clearest place to watch for over-application (the agentic write path is where one-offs become standing rules, which is exactly what P5 tests).
- **Mem0** — open-source, widely adopted, extraction pipeline tuned for low token cost. Good default; its own 2026 review concedes staleness and cross-device identity as open problems.
- **Zep / Graphiti** — temporal knowledge graph with bi-temporal edges, built for "this fact was true from X to Y." Strong on the temporal and knowledge-update categories.
- **LangMem** — LangGraph's memory store, splits semantic/episodic/procedural with explicit update/delete. Natural if you're already on LangGraph.
**Pick for Hermes:** if you adopt rather than keep homegrown, Letta is the closest match to the coworker thesis (self-improving, tiered), but it's also the one to stress hardest on the D2 discrimination half. Run your own harness with frozen settings; the public LongMemEval/LoCoMo numbers are vendor-reported and not comparable (the Zep-vs-Mem0 dispute is the proof; see `references.md`).

### One caution on the memory scores
You'll see LongMemEval percentages quoted for these systems. Don't rank on them. They're self-reported, use different retrieval and grading settings, and the same system has been scored 30+ points apart by different parties. They tell you a system engaged with the benchmark, not that it'll be a good coworker memory for Hermes. Your own P1–P5 probes against a frozen harness are the only comparable signal.

## Where Hermes lands

Hermes is its own framework: provider, model, tools, and memory are your stack on the mini. So "testing agentic frameworks" isn't academic shopping. It's "is my homegrown Hermes stack better or worse than adopting LangGraph/CrewAI/etc. as the substrate?" Hermes is one contestant in a Q1+Q2 bake-off:

- **Q1:** does a Hermes-built coworker out-score a LangGraph-built one on the 5 dimensions? Bespoke can beat general, so you may win.
- **Q2:** but is your stack worse on F2 observability, F6 ops, or the bus-factor of being homegrown? You may lose, and that's the honest case for adopting something.

The bake-off makes build-vs-adopt evidence-based instead of sunk-cost-driven.

## Benchmarks to draw the Q1 task suite from

Use these for the D1/task layer only. Each measures the engine, not the coworker. Pick the one closest to Hermes' real work; a coworker eval should weight your own scenario suite (`scenarios/suite.md`) over any of them.

| Benchmark | Measures | Limitation |
|-----------|----------|------------|
| τ-bench / τ²-bench | Multi-turn tool + simulated-user interaction under policy; verifies final state | Reliability (pass^k) collapses below pass^1; narrow domains |
| SWE-bench (Verified) | Resolving real GitHub Python issues end-to-end | Coding-only, scaffold-sensitive, contamination risk |
| GAIA | General-assistant multi-step reasoning, web, files, tools | Validation answers public (leakage); near-saturating |
| WebArena | Tasks on sandboxed real web apps | Reference answers in task config; environment drift |
| BFCL v3 | Function/tool-calling accuracy, multi-turn | Calling accuracy is not task success |
| MCP-Bench | Tool-using agents against real MCP servers | New; coverage still expanding |

The τ-bench style (simulate the user with a model, constrain by policy, check final state) is the closest fit for a coworker agent, because it tests gathering information over turns rather than single-shot QA.
