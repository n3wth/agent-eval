import pytest

from agent_eval.adapters.mock import MockAdapter
from agent_eval.memory import (
    MemoryProbe,
    ProbeValidationError,
    run_memory_probes,
    validate_probe,
)

DISTRACTORS = ["unrelated question one", "unrelated question two"]

# The mock stores standing instructions and echoes them as
# "[applying: <instruction>]", so checks read the toy memory directly.
ITALICS_PROBE = MemoryProbe(
    id="P1",
    kind="durability",
    tell=["I never want italics in my designs. Use weight instead."],
    trigger="Draft a hero section for a landing page.",
    fact_keywords=["italic"],
    checks=[{"type": "contains", "value": "never want italics"}],
    distractor_sessions=1,
    probe_repeats=2,
)

EPHEMERAL_PROBE = MemoryProbe(
    id="P5",
    kind="discrimination",
    tell=["Just for this one task, keep it to a single sentence."],
    trigger="Explain connection pooling.",
    checks=[{"type": "not_contains", "value": "just for this one task"}],
    distractor_sessions=1,
    probe_repeats=1,
)


def test_good_agent_durable_and_discriminating():
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    assert report["d2_reportable"] is True
    assert report["durability_rate"] == 1.0
    assert report["over_application_rate"] == 0.0
    assert report["hoarder"] is False


def test_hoarder_caught_by_the_pair():
    agent = MockAdapter({"behavior": "hoarder"})
    report = run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    # High durability AND high over-application: exactly what a single
    # memory number would have hidden.
    assert report["durability_rate"] == 1.0
    assert report["over_application_rate"] == 1.0
    assert report["hoarder"] is True


def test_amnesiac_fails_durability():
    agent = MockAdapter({"behavior": "amnesiac"})
    report = run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    assert report["durability_rate"] == 0.0
    assert report["over_application_rate"] == 0.0


def test_pending_human_checks_counted_for_the_cli_note():
    probe = MemoryProbe(
        id="PH",
        kind="discrimination",
        tell=["Just for this one task, keep it short."],
        trigger="Explain pooling.",
        checks=[{"type": "human", "question": "Did the one-off stick?"}],
        distractor_sessions=0,
        probe_repeats=1,
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE, probe], DISTRACTORS)
    assert report["pending_count"] == 1


def test_durability_alone_is_not_reportable_as_d2():
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE], DISTRACTORS)
    assert report["d2_reportable"] is False
    assert "pair" in report["d2_note"]
    assert "hoarder" not in report


def test_null_control_strips_base_model_priors():
    # Passes the check with or without memory: the win is priors, not
    # memory, so it must not count toward durability.
    probe = MemoryProbe(
        id="PX",
        kind="durability",
        tell=["I never want italics."],
        trigger="Draft a section.",
        fact_keywords=["italic"],
        checks=[{"type": "contains", "value": "ok:"}],
        distractor_sessions=0,
        probe_repeats=1,
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS)
    record = next(r for r in report["probes"] if r["id"] == "PX")
    assert record["status"] == "pass"
    assert record["null_control"] == "pass"
    assert record["null_delta"] == 0
    assert report["durability_rate"] == 0.0


def test_memory_restored_after_null_control():
    agent = MockAdapter({"behavior": "good"})
    agent.memory.append("pre-existing standing preference")
    run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    assert "pre-existing standing preference" in agent.memory


def test_restatement_lint_rejects_leaky_trigger():
    probe = MemoryProbe(
        id="BAD",
        kind="durability",
        tell=["I never want italics."],
        trigger="Make a design and remember: no italics.",
        fact_keywords=["italic"],
        checks=[],
    )
    with pytest.raises(ProbeValidationError, match="restates"):
        validate_probe(probe)


def test_durability_probe_requires_fact_keywords():
    probe = MemoryProbe(
        id="BAD2", kind="durability", tell=["x"], trigger="y", checks=[]
    )
    with pytest.raises(ProbeValidationError, match="fact_keywords"):
        validate_probe(probe)


def test_cross_surface_probe_skipped_without_second_adapter():
    probe = MemoryProbe(
        id="P4",
        kind="durability",
        tell=["newth.io is always gated behind basic auth."],
        trigger="Plan an uptime check for my site.",
        fact_keywords=["basic auth"],
        checks=[{"type": "contains", "value": "basic auth"}],
        trigger_surface="second",
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS)
    record = next(r for r in report["probes"] if r["id"] == "P4")
    assert record["status"] == "skipped"
