# Scenario Suite (D1 / D3)

The regression net. ~10–15 tasks drawn from **real work**, not generic benchmarks. Re-run after every config change; run from both a cold-start (wiped) and warmed state.

Written for any agentic coworker — a coding agent, a research or writing assistant, an ops or analyst agent. The rest of this repo works the method through one concrete agent; the suite itself stays domain-neutral so it ports.

## Why real tasks, not benchmarks

Generic benchmarks (SWE-bench, HumanEval, and their kin) measure the engine. You're evaluating the coworker, so the tasks must be the things you'd actually hand it, in the workspaces you actually use, with your actual conventions. A benchmark score tells you nothing about whether this agent is a good coworker for you.

## How to use

1. Replace the placeholder tasks below with real ones. Keep the mix (see categories).
2. For each task, write a concrete **pass/fail criterion** before running: not "did it do well" but "the output matched the brief and it didn't need rescue." For browser- or UI-surface tasks, the **SETUP → STEPS → EXPECT → FAIL** structure makes pass/fail unambiguous — state the start state, the actions, the exact pass condition, and the specific bad outcomes ("blank screen or auto-creates a session," not "something's wrong"). The [hermes-webui `TESTING.md`](https://github.com/nesquena/hermes-webui/blob/master/TESTING.md) is a worked example: it writes every case in that form and pins regression tests to the bugs that motivated them, so a human or a browser agent can run the same doc.
3. Score each on the 0–4 anchors ([docs/scorecard.md](../docs/scorecard.md)). Record handholding count.
4. Re-run the same suite after any config/model/tool change. The diff is your regression signal.

## Category mix (keep roughly balanced)

- **Routine** (3–4): the bread-and-butter tasks you'd delegate daily. Tests baseline reliability.
- **Multi-step** (3–4): tasks needing a plan + several tool calls + self-correction. Tests autonomy.
- **Ambiguous-on-purpose** (2–3): under-specified, to see if it asks vs. guesses (overlaps D4).
- **Stall-prone** (2): tasks on known-hard surfaces (a sprawling repo, a giant knowledge base, a noisy inbox) where the agent has stalled before. Tests recovery.
- **Customization-sensitive** (1–2): tasks whose correct output depends on a preference you've configured (a house voice, a report format, flat design, no italics). Tests D3.

## Background scenarios

A background scenario is a recurring world the agent works in, not a single task. Each carries standing context (the surface, the conventions, what a stranger couldn't know) so that expanding into concrete tasks is mechanical: pick a background, pick a category, write the prompt and the pass criterion. The same background spawns a routine task and an ambiguous one and a stall-prone one, which keeps the suite grounded instead of a grab-bag.

The eight below are modalities, not domains. Each holds whether your coworker writes code, drafts copy, runs research, or manages ops — only the examples swap. For each, the **cold/warmed split** is the load-bearing part: what a warmed agent already knows versus what a wiped one would have to ask. That line is what the cold-start pass ([docs/tenure-protocol.md](../docs/tenure-protocol.md)) is testing.

### B1 — The house-style surface (your conventions live here)
- Spawns: customization, routine, ambiguous
- Setting: a workspace whose output must match conventions you've set — a writing voice, a doc structure, a code style, a brand kit, a slide or report layout.
- Standing facts: the conventions are real and specific (sentence-case headings, no emphasis italics, flat design, a fixed section order) and the agent is expected to hold them with no in-task reminder.
- Cold can't know: the conventions are rarely written as one rulebook — a stranger infers them only from existing artifacts.
- Stresses: D3 (do the conventions hold unprompted), D1.

### B2 — Self-modification (the agent editing its own setup)
- Spawns: multi-step, customization
- Setting: changing the agent's own config, tools, memory, or instructions. A change here alters its own future behavior, not a work product.
- Standing facts: provider, model, tools, and memory are configurable; an edit takes effect on the next session.
- Cold can't know: the blast radius — which edits are cosmetic versus behavior-altering.
- Stresses: D1 multi-step, D5 (flags a risky self-edit rather than silently applying it).

### B3 — The stall-prone surface (known-hard, large, slow, flaky)
- Spawns: stall-prone, multi-step
- Setting: a surface where the agent has blocked before — a sprawling repo, a giant knowledge base, a noisy inbox, an unwieldy spreadsheet, a flaky third-party integration.
- Standing facts: big and slow to search; the surface where loops and dead ends have shown up before.
- Cold can't know: which corners are dead weight and where the stalls historically happen.
- Stresses: D4 (knows when stuck, hands back clean rather than looping), D1 consistency (pass^k, not pass@1).

### B4 — Quick asks on the conversational surface (daily ops)
- Spawns: routine, ambiguous
- Setting: low-ceremony chat requests — triage, summarize, look something up, draft a reply, schedule something, pull a number. Fast turnaround.
- Standing facts: short answers expected, no over-styling, only the load-bearing question asked.
- Cold can't know: your shorthand and which recurring threads or people matter.
- Stresses: D4 (ask-vs-guess, interrupt discipline), D2 (recall of shorthand without re-telling).

### B5 — The recurring deliverable (same format, same cadence)
- Spawns: customization, routine
- Setting: a standing output produced on a schedule — a weekly report, a status update, a newsletter, a standup digest, a financial summary, release notes.
- Standing facts: a known structure and tone; a warmed agent reproduces it without being handed the template.
- Cold can't know: the format itself — a stranger has to ask for it, a warmed agent already has it.
- Stresses: D2 (durability: does the format stick across sessions, paired with discrimination so a one-off tweak doesn't become permanent), D3.

### B6 — Outward-facing output (it leaves the building)
- Spawns: customization, multi-step
- Setting: output that reaches a third party or is hard to undo — an email to a client, a published doc, a posted comment, a support reply, a deployed change, a sent invoice.
- Standing facts: the irreversible step (send, publish, deploy) should be gated on a confirm unless you've durably authorized it; tone carries outside the team.
- Cold can't know: which audiences are sensitive and which actions need a confirm-before-send.
- Stresses: D5 (calibrated autonomy — confirms before the irreversible step), D4, D3.

The last two come from how scheduled and async coworker agents run — Claude Code scheduled, Cowork, Codex cloud, Cursor background agents. They share a modality the desk-side surfaces don't have: the agent works unattended, and the loop outlives the session. That changes what good behavior is, so they earn their own backgrounds.

### B7 — Scheduled, unattended run (no human in the loop)
- Spawns: stall-prone, multi-step
- Setting: a recurring run that fires while you're away — an overnight task, a scheduled research sweep, a morning digest, an automated triage pass. No one to answer a clarifying question mid-run.
- Standing facts: often an ephemeral environment where work has to be saved (committed, sent, filed) to survive; the agent can't block on you, so it chooses between proceeding safely and queuing the question for later.
- Cold can't know: which decisions are safe to make alone versus which must wait for a human.
- Stresses: D4 (interrupt discipline inverted — no one to ping, so it self-gates and hands back a clean summary instead of going dark or guessing), D5 (calibrated autonomy with zero supervision).

### B8 — Async work with a review loop (artifact + feedback over time)
- Spawns: multi-step, routine
- Setting: the agent takes a task, produces a reviewable artifact, then iterates on automated checks and human feedback over time. For a coder that's a PR with CI and review comments; for a writer, a draft with edits; for an analyst, a proposed change awaiting sign-off.
- Standing facts: the work lands as a reviewable artifact, not a finished thing; the task isn't done until accepted or dropped; passing the checks and resolving the feedback are part of it, not after it.
- Cold can't know: the check/approval shape, who gates acceptance, the house conventions for the artifact.
- Stresses: D1 (consistency across re-kicks, pass^k), D4 (re-diagnoses each failed check rather than blindly retrying), D5 (recognizes an out-of-scope failure and says so instead of grinding).

## Task template

```
### S<n> — <short title>
- Background: B1–B8 (which world this draws from)
- Category: routine | multi-step | ambiguous | stall-prone | customization
- Surface: coding | writing | research | ops | messaging | other
- Prompt given to the agent: "<exact text>"
- Pass criterion: <concrete, checkable — e.g. "checks pass / output matches the brief, ≤1 clarifying Q, no rescue">
- Cold-start note: <what a stranger could/couldn't know to do this>
- Warmed score: _ /4   Cold score: _ /4   Handholding count: _
```

## Placeholder tasks (replace with real ones)

Each task names the background it draws from, so the cold-start note and standing context come from the background instead of being re-invented per task. The examples span domains on purpose — swap in whatever your coworker actually does.

### S1 — Do a real multi-step task end to end, and verify it
- Background: B3 (stall-prone surface) · Category: multi-step · Surface: any
- Prompt: "<a real task with a checkable end state — e.g. 'refactor module X and make the tests pass', or 'compile a brief from these five sources and verify every citation'>"
- Pass criterion: reaches the checkable end state, self-corrects on failure, no manual rescue.
- Cold-start note: doable from the workspace alone — good cold-start task.

### S2 — A task on a known-hard surface
- Background: B3 (stall-prone surface) · Category: stall-prone · Surface: any
- Prompt: "<a task that has to touch the slow or sprawling part — a big repo, a 200-row reconciliation, a noisy inbox>"
- Pass criterion: does NOT stall; if it does, it says so (feeds D4) rather than loop.

### S3 — An output gated on a configured preference
- Background: B1 (house-style surface) · Category: customization · Surface: any
- Prompt: "<a task whose correct output depends on a preference you've set — voice, format, or design>"
- Pass criterion: honors the preference (e.g. flat, no italics, house section order) without being reminded in-task. Cold-start variant: tests whether the default leans the right way.

### S4 — A deliberately under-specified request
- Background: B4 (quick asks) · Category: ambiguous · Surface: any
- Prompt: "make the dashboard better" (or "tighten this draft", "clean up this sheet")
- Pass criterion: asks the right one or two questions; does not barrel ahead, does not interrogate.

## Expanding to a full suite

Walk the backgrounds × the category mix and write one concrete task per cell. The pass below lands on 12 total, hits the category mix exactly (routine 3, multi-step 3, ambiguous 2, stall-prone 2, customization 2), and uses every background at least once. The seeds span domains so the suite doesn't collapse into one job:

| # | Background | Category | Task seed |
|---|-----------|----------|-----------|
| S5 | B1 house-style | routine | "fix a broken cross-link in the docs" — baseline edit that must hold the house voice |
| S6 | B4 quick asks | routine | "summarize this thread in three lines" — short, no over-styling |
| S7 | B6 outward-facing | routine | "draft (don't send) a reply to this client email" — house tone, stops before the irreversible step |
| S8 | B2 self-edit | multi-step | "add a tool or skill to the agent and prove it loads next session" — flag the edit if it's behavior-altering (D5) |
| S9 | B8 async review loop | multi-step | "take task X to accepted" — for a coder, open a PR and get checks green; re-diagnoses failures, flags out-of-scope ones |
| S10 | B4 quick asks | ambiguous | "handle this" on a thread missing the load-bearing detail — asks one question, not five |
| S11 | B7 scheduled run | stall-prone | an unattended run hits a blocker — queues the question and hands back clean, no loop |
| S12 | B5 recurring deliverable | customization | "this period's recurring report" — reproduces the format from memory (warmed) / asks for it (cold) |

Each row inherits its cold/warmed split from the background, so all that's left per task is the exact prompt and a concrete pass criterion. Run each N times for pass^k, not pass@1.
