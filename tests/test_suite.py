import pytest

from agent_eval.adapters.mock import MockAdapter
from agent_eval.checks import CheckContext
from agent_eval.suite import Scenario, SuiteConfig, load_suite, run_suite


def make_suite(scenarios, runs=2):
    return SuiteConfig(scenarios=scenarios, runs=runs)


def test_pass_k_catches_flakiness_that_pass_at_1_hides():
    # Alternates pass/fail: looks capable best-of-k, fails all-of-k.
    agent = MockAdapter(
        {"rules": [{"match": "flaky task", "replies": ["RESULT: done", "ERROR: gave up"]}]}
    )
    scenario = Scenario(
        id="S1", prompt="flaky task", checks=[{"type": "contains", "value": "RESULT: done"}]
    )
    record = run_suite(agent, make_suite([scenario]), k=2, ctx=CheckContext())
    result = record["scenarios"][0]
    assert result["pass_at_1"] is True
    assert result["pass_k"] is False
    assert record["pass_k_rate"] == 0.0
    assert record["pass_at_1_rate"] == 1.0


def test_consistent_agent_passes_pass_k():
    agent = MockAdapter({"rules": [{"match": "task", "reply": "RESULT: done"}]})
    scenario = Scenario(
        id="S1", prompt="task", checks=[{"type": "contains", "value": "RESULT: done"}]
    )
    record = run_suite(agent, make_suite([scenario]), k=3)
    assert record["pass_k_rate"] == 1.0


def test_cold_tenure_wipes_and_restores_memory():
    agent = MockAdapter({})
    agent.memory.append("I never want italics")
    scenario = Scenario(id="S1", prompt="do a thing", checks=[{"type": "contains", "value": "ok"}])
    record = run_suite(agent, make_suite([scenario]), tenure="cold", k=1)
    assert record["tenure"] == "cold"
    # The warmed store is back after the ABA pass.
    assert agent.memory == ["I never want italics"]


def test_cold_run_skips_non_cold_scenarios():
    agent = MockAdapter({})
    scenarios = [
        Scenario(id="S1", prompt="a", checks=[], cold_start=True),
        Scenario(id="S2", prompt="b", checks=[], cold_start=False),
    ]
    record = run_suite(agent, make_suite(scenarios), tenure="cold", k=1)
    assert [s["id"] for s in record["scenarios"]] == ["S1"]


def test_cold_tenure_requires_memory_control():
    class NoMemory(MockAdapter):
        @property
        def memory_control(self):
            return None

    scenario = Scenario(id="S1", prompt="a", checks=[])
    with pytest.raises(RuntimeError, match="memory control"):
        run_suite(NoMemory({}), make_suite([scenario]), tenure="cold", k=1)


def test_load_suite_warns_on_todo_placeholders(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text(
        """
suite: t
scenarios:
  - id: S1
    category: routine
    prompt: "TODO: fill me"
    checks: []
"""
    )
    suite = load_suite(path)
    assert any("TODO" in w for w in suite.warnings)


def test_load_suite_rejects_unknown_category(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text(
        """
scenarios:
  - id: S1
    category: vibes
    prompt: "x"
"""
    )
    with pytest.raises(ValueError, match="unknown category"):
        load_suite(path)
