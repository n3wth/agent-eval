"""Deferred scoring: a batch run's pending checks resolve later and
re-aggregate through the same code path the runner used."""

import json

from agent_eval.adapters.mock import MockAdapter
from agent_eval.checks import CheckContext
from agent_eval.memory import MemoryProbe, run_memory_probes
from agent_eval.score import find_pending, resolve_pending, score_file
from agent_eval.suite import Scenario, SuiteConfig, run_suite

DISTRACTORS = ["unrelated one", "unrelated two"]


def batch_memory_record():
    probes = [
        MemoryProbe(
            id="P1",
            kind="durability",
            tell=["I never want italics."],
            trigger="Draft a section.",
            fact_keywords=["italic"],
            checks=[{"type": "human", "question": "Did the preference hold?"}],
            distractor_sessions=0,
            cycles=2,
        ),
        MemoryProbe(
            id="P5",
            kind="discrimination",
            tell=["Just for this one task, keep it short."],
            trigger="Explain pooling.",
            checks=[{"type": "human", "question": "Did the one-off carry forward?"}],
            distractor_sessions=0,
            cycles=1,
        ),
    ]
    agent = MockAdapter({"behavior": "good"})
    return run_memory_probes(
        agent, probes, DISTRACTORS, ctx=CheckContext(interactive=False), control=False
    )


def test_batch_memory_run_is_pending_then_resolves():
    record = batch_memory_record()
    assert record["pending_count"] == 2
    assert record["d2_reportable"] is False

    refs = find_pending(record)
    assert len(refs) == 3  # two P1 curve triggers + one P5 trigger
    assert all(r["reply"] for r in refs)

    record = resolve_pending(record, asker=lambda label, q, reply: "pass")
    assert record["pending_count"] == 0
    assert record["d2_reportable"] is True
    assert record["durability_score"] == 4.0
    assert record["over_application_rate"] == 0.0
    assert record["resolved_checks"] == 3


def test_skipped_answers_stay_pending():
    record = batch_memory_record()
    record = resolve_pending(record, asker=lambda label, q, reply: None)
    assert record["pending_count"] == 2
    assert record["resolved_checks"] == 0


def test_resolved_checks_marked_human_scored():
    record = batch_memory_record()
    record = resolve_pending(record, asker=lambda label, q, reply: "fail")
    statuses = {
        c["scored_by"]
        for p in record["probes"]
        for t in p["triggers"]
        for c in t["checks"]
    }
    assert statuses == {"human"}


def test_suite_record_rescored_flips_pass_k():
    agent = MockAdapter({"rules": [{"match": "task", "reply": "did the thing"}]})
    scenario = Scenario(
        id="S1",
        prompt="task",
        checks=[{"type": "human", "question": "Done without rescue?"}],
    )
    record = run_suite(
        agent,
        SuiteConfig(scenarios=[scenario], runs=2),
        k=2,
        ctx=CheckContext(interactive=False),
    )
    assert record["pass_k_rate"] is None  # nothing scored yet
    record = resolve_pending(record, asker=lambda label, q, reply: "pass")
    assert record["pass_k_rate"] == 1.0


def test_score_file_round_trip(tmp_path):
    from agent_eval import storage

    record = batch_memory_record()
    path = storage.save_run(record, "memory", tmp_path)
    updated = score_file(path, asker=lambda label, q, reply: "pass")
    assert updated["d2_reportable"] is True
    on_disk = json.loads(path.read_text())
    assert on_disk["pending_count"] == 0
    assert "_path" not in on_disk
