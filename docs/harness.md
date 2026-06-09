# Harness

The runnable half of the method. The docs say what to measure and why; `agent_eval/` measures it. Everything the prose guards — pass^k, the memory pair, the 2x2, the restatement rule, the NullMemory control — is enforced in code and pinned by tests, so a careless run can't quietly reintroduce the failure the framework was built to catch.

## Install and dry-run

```sh
pip install -e ".[dev]"
agent-eval validate                                  # lint the suite and probes
agent-eval run memory --config configs/mock.yaml --batch   # whole pipeline, toy agent
python -m pytest                                     # the invariants, as tests
```

The mock agent's behaviors are the named failure modes (`good`, `hoarder`, `amnesiac`), so you can watch the harness catch a hoarder before pointing it at anything real.

## Pointing it at a real agent

An adapter is three capabilities: fresh sessions, send-and-reply, and (optionally) memory control. Two generic adapters cover most agents; the named ones are presets over them, so agent-specific knowledge lives in config, not code.

| Adapter | For | Config |
|---------|-----|--------|
| `shell` | any agent with a CLI | `command` template with `{message}` / `{session_id}` |
| `http` | any agent with a JSON endpoint | `url`, `payload`, `response_field` |
| `openclaw` | OpenClaw via its CLI | preset defaults; override per install ([configs/openclaw.yaml](../configs/openclaw.yaml)) |
| `hermes` | Hermes via hermes-webui | preset defaults; override per install ([configs/hermes.yaml](../configs/hermes.yaml)) |
| `mock` | tests and dry runs | `behavior: good \| hoarder \| amnesiac` |

`memory_paths` is the key that unlocks the tenure work: list wherever your agent keeps continuity (memory files, vector store, session history) and the harness can run the wiped-memory cold-start pass and the NullMemory control. The wipe is the protocol from [tenure.md](tenure.md) verbatim — move aside, never delete, restore after — implemented in `agent_eval/adapters/files.py`.

A new agent that doesn't fit either generic shape needs one subclass of `Adapter` in `agent_eval/adapters/` and a line in the registry. Sessions must be real conversation boundaries: the memory probes test cross-session continuity, so an adapter that fakes "new session" by clearing a prompt buffer is measuring nothing.

## The instruments, as commands

```sh
agent-eval run suite   --config configs/openclaw.yaml --tenure warmed   # D1, D3
agent-eval run suite   --config configs/openclaw.yaml --tenure cold     # the wiped pass
agent-eval run memory  --config configs/openclaw.yaml                   # D2, the pair
agent-eval run texture --config configs/openclaw.yaml --tenure warmed   # D4 (+ cold honesty for D5)
agent-eval journal add                                                  # daily, 1-2 weeks
agent-eval journal reliance --relied --right --capability refactor      # one accept/override event
agent-eval reliance                                                     # weekly RAIR / RSR
agent-eval scorecard --agent openclaw                                   # the dated deliverable
```

Cadence as in [proposal.md](proposal.md) §4: baseline cold and warmed, use daily for one to two weeks logging journal and reliance events, re-score weekly. Each run writes a dated JSON record under `runs/` (gitignored — run data is private); the scorecard assembles the latest of each and computes its own delta against the previous scorecard.

## What the code enforces

- **pass^k is the headline.** The suite runner computes both rates and prints pass@1 only as contrast. Each scenario runs k times (default 3) in fresh sessions.
- **The memory pair, or nothing.** A memory run with only durability probes (or only discrimination) reports `d2_reportable: false`, and the scorecard shows the gap with a warning instead of a durability number. Durability alone rewards hoarding; the refusal is the point.
- **NullMemory subtraction.** Every durability probe re-runs with continuity broken (memory wiped between sessions, not just once — a single wipe would let the tell session write fresh memory and pass anyway). A probe the control also passes is base-model priors and counts zero toward durability.
- **The restatement lint.** A trigger containing a `fact_keyword` is rejected at load: a probe that restates the planted fact measures compliance, not memory.
- **D5 is the 2x2.** RAIR (of agent-right events, the fraction you relied) and RSR (of agent-wrong events, the fraction you overrode). An empty quadrant reads as unknown, never as zero, and the drift check flags RAIR rising while RSR is flat or falling — the pattern a delegation-volume metric would have rewarded.
- **Pending is not pass.** Human-scored checks left unanswered in `--batch` mode mark the run pending; pending runs are excluded from rates, not rounded up.
- **Judges are labeled.** `llm` checks carry `scored_by: llm` in every record, so the self-preference and verbosity biases from [tenure.md](tenure.md) stay visible. Keep the soft dimensions human-scored or dual-scored.

## Score mapping

Rates map to the 0–4 anchors linearly (4 × rate, one decimal) so a score means the same thing across runs and agents. D1 from suite pass^k per tenure; D3 from the customization-category scenarios; D2 durability from the NullMemory-adjusted rate, discrimination from 1 − over-application; D4 from texture pass rate per tenure; D5 cold from the honesty probes, D5 warmed stays the RAIR/RSR pair because it has no honest single-number form.

## Filling it in

The shipped suite and probes are the seeds from [scenarios/suite.md](../scenarios/suite.md) and [probes/memory.md](../probes/memory.md) in runnable form, with `TODO` markers where only your real work will do. `agent-eval validate` warns on every TODO left in place; a suite of placeholders measures nothing, and a planted preference you don't actually hold makes the warmed pass meaningless. Write the pass criterion (or the human-check question) before the run — that's the pre-registration move that keeps the builder honest.
