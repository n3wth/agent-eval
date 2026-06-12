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
    cycles=2,
)

EPHEMERAL_PROBE = MemoryProbe(
    id="P5",
    kind="discrimination",
    tell=["Just for this one task, keep it to a single sentence."],
    trigger="Explain connection pooling.",
    checks=[{"type": "not_contains", "value": "just for this one task"}],
    distractor_sessions=1,
    cycles=1,
)


def test_good_agent_durable_and_discriminating():
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    assert report["d2_reportable"] is True
    assert report["durability_rate"] == 1.0
    assert report["over_application_rate"] == 0.0
    assert report["hoarder"] is False
    # Conforms from the first probe session: the rubric's top anchor.
    p1 = next(p for p in report["probes"] if p["id"] == "P1")
    assert p1["sessions_to_stick"] == 1
    assert p1["score_0_4"] == 4
    assert report["durability_score"] == 4.0


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
    p1 = next(p for p in report["probes"] if p["id"] == "P1")
    assert p1["sessions_to_stick"] is None
    assert p1["score_0_4"] == 0
    assert report["not_converged"] == 1


def test_slow_learner_shows_the_warming_curve():
    # Applies memory only from its 3rd session on. Curve: tell=s1, then
    # triggers at s2, s3, s4 -> fail, pass, pass -> sessions-to-stick 2.
    probe = MemoryProbe(
        id="PS",
        kind="durability",
        tell=["I never want italics in my designs."],
        trigger="Draft a section.",
        fact_keywords=["italic"],
        checks=[{"type": "contains", "value": "never want italics"}],
        distractor_sessions=0,
        cycles=3,
    )
    agent = MockAdapter({"behavior": "slow", "warmup_sessions": 3})
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS, control=False)
    ps = next(p for p in report["probes"] if p["id"] == "PS")
    assert ps["sessions_to_stick"] == 2
    assert ps["score_0_4"] == 3
    assert ps["reverted"] is False


def test_reversion_detected_on_the_curve():
    # Passes the first trigger, fails a later one: the P2 reversion signature.
    probe = MemoryProbe(
        id="PR",
        kind="durability",
        tell=["I never want shadows."],
        trigger="style the card",
        fact_keywords=["shadow"],
        checks=[{"type": "contains", "value": "HELD"}],
        distractor_sessions=0,
        cycles=2,
    )
    agent = MockAdapter(
        {"behavior": "good", "rules": [{"match": "style the card", "replies": ["HELD", "slipped"]}]}
    )
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS, control=False)
    pr = next(p for p in report["probes"] if p["id"] == "PR")
    assert pr["reverted"] is True
    assert pr["sessions_to_stick"] is None
    assert report["reversions"] == 1


def test_perturbation_measures_sessions_to_re_adapt():
    probe = MemoryProbe(
        id="PP",
        kind="durability",
        tell=["I never want italics in my designs."],
        trigger="Draft a section.",
        fact_keywords=["italic"],
        checks=[{"type": "contains", "value": "never want italics"}],
        distractor_sessions=0,
        cycles=2,
        perturb={
            "tell": "Correction: from now on, use serif fonts everywhere.",
            "trigger": "Draft another section.",
            "checks": [{"type": "contains", "value": "serif fonts"}],
            "cycles": 2,
        },
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS, control=False)
    pp = next(p for p in report["probes"] if p["id"] == "PP")
    assert pp["perturbation"]["status"] == "pass"
    assert pp["perturbation"]["sessions_to_re_adapt"] == 1


def test_durability_alone_is_not_reportable_as_d2():
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE], DISTRACTORS)
    assert report["d2_reportable"] is False
    assert "pair" in report["d2_note"]
    assert "hoarder" not in report


def test_pending_human_checks_counted_for_the_cli_note():
    probe = MemoryProbe(
        id="PH",
        kind="discrimination",
        tell=["Just for this one task, keep it short."],
        trigger="Explain pooling.",
        checks=[{"type": "human", "question": "Did the one-off stick?"}],
        distractor_sessions=0,
        cycles=1,
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [ITALICS_PROBE, probe], DISTRACTORS)
    assert report["pending_count"] == 1


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
        cycles=1,
    )
    agent = MockAdapter({"behavior": "good"})
    report = run_memory_probes(agent, [probe, EPHEMERAL_PROBE], DISTRACTORS)
    record = next(r for r in report["probes"] if r["id"] == "PX")
    assert record["status"] == "fail"
    assert record["null_control"] == "pass"
    assert record["null_delta"] == 0
    assert record["score_0_4"] == 0
    assert report["durability_rate"] == 0.0


def test_memory_restored_after_null_control():
    agent = MockAdapter({"behavior": "good"})
    agent.memory.append("pre-existing standing preference")
    run_memory_probes(agent, [ITALICS_PROBE, EPHEMERAL_PROBE], DISTRACTORS)
    assert "pre-existing standing preference" in agent.memory


def test_isolation_keeps_probes_from_priming_each_other():
    planter = MemoryProbe(
        id="PA",
        kind="durability",
        tell=["I always want sentence-case headings."],
        trigger="Draft a doc outline.",
        fact_keywords=["sentence-case"],
        checks=[{"type": "contains", "value": "sentence-case"}],
        distractor_sessions=0,
        cycles=1,
    )
    watcher = MemoryProbe(
        id="PB",
        kind="discrimination",
        tell=["Just for this one task, answer briefly."],
        trigger="Explain indexes.",
        # Without isolation, PA's plant leaks into PB's session.
        checks=[{"type": "not_contains", "value": "sentence-case"}],
        distractor_sessions=0,
        cycles=1,
    )
    leaky = run_memory_probes(
        MockAdapter({"behavior": "good"}), [planter, watcher], DISTRACTORS, control=False
    )
    assert next(p for p in leaky["probes"] if p["id"] == "PB")["status"] == "fail"

    agent = MockAdapter({"behavior": "good"})
    agent.memory.append("baseline fact")
    isolated = run_memory_probes(
        agent, [planter, watcher], DISTRACTORS, control=False, isolate=True
    )
    assert next(p for p in isolated["probes"] if p["id"] == "PB")["status"] == "pass"
    # And the store is left as it was found.
    assert agent.memory == ["baseline fact"]


def test_isolation_requires_a_copy_capable_control():
    class NoIsolation(MockAdapter):
        @property
        def memory_control(self):
            return None

    with pytest.raises(RuntimeError, match="isolate"):
        run_memory_probes(
            NoIsolation({}), [ITALICS_PROBE], DISTRACTORS, control=False, isolate=True
        )


def test_shuffle_seed_recorded_and_deterministic():
    probes = [ITALICS_PROBE, EPHEMERAL_PROBE]
    a = run_memory_probes(
        MockAdapter({"behavior": "good"}), probes, DISTRACTORS, control=False, shuffle_seed=7
    )
    b = run_memory_probes(
        MockAdapter({"behavior": "good"}), probes, DISTRACTORS, control=False, shuffle_seed=7
    )
    assert a["shuffle_seed"] == 7
    assert [p["id"] for p in a["probes"]] == [p["id"] for p in b["probes"]]


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
