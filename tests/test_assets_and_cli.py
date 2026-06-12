"""The shipped YAML assets must load, lint clean, and drive the mock agent
end to end through the CLI."""

import json
import os
from pathlib import Path

import pytest

from agent_eval.adapters import build_adapter
from agent_eval.adapters.files import FileMemoryControl
from agent_eval.cli import main
from agent_eval.memory import load_probes
from agent_eval.suite import load_suite
from agent_eval.texture import load_texture_probes

REPO = Path(__file__).resolve().parent.parent


def test_shipped_suite_loads_and_keeps_the_category_mix():
    suite = load_suite(REPO / "scenarios" / "suite.yaml")
    counts = {}
    for s in suite.scenarios:
        counts[s.category] = counts.get(s.category, 0) + 1
    assert counts == {
        "routine": 3,
        "multi-step": 3,
        "ambiguous": 2,
        "stall-prone": 2,
        "customization": 2,
    }


def test_shipped_memory_probes_load_with_both_halves():
    probes, distractors = load_probes(REPO / "probes" / "memory.yaml")
    kinds = {p.kind for p in probes}
    assert kinds == {"durability", "discrimination"}
    assert distractors


def test_shipped_texture_probes_include_cold_honesty():
    probes = load_texture_probes(REPO / "probes" / "texture.yaml")
    assert any(p.dimension == "d5" and p.tenure == "cold" for p in probes)


def test_adapter_registry():
    agent = build_adapter({"adapter": "mock", "behavior": "good"})
    assert agent.start_session().send("hello").text.startswith("ok:")
    with pytest.raises(ValueError, match="unknown adapter"):
        build_adapter({"adapter": "nope"})


def test_file_memory_control_round_trip(tmp_path):
    store = tmp_path / "memory"
    store.mkdir()
    (store / "MEMORY.md").write_text("standing prefs")
    mc = FileMemoryControl([str(store)], backup_dir=str(tmp_path / "backups"))
    token = mc.wipe()
    assert not store.exists()
    # The agent writes fresh memory while wiped; restore must not clobber or lose it.
    store.mkdir()
    (store / "MEMORY.md").write_text("cold-run scribbles")
    mc.restore(token)
    assert (store / "MEMORY.md").read_text() == "standing prefs"


def test_file_memory_checkpoint_survives_rollbacks(tmp_path):
    store = tmp_path / "memory"
    store.mkdir()
    (store / "MEMORY.md").write_text("baseline")
    mc = FileMemoryControl([str(store)], backup_dir=str(tmp_path / "backups"))
    token = mc.checkpoint()
    (store / "MEMORY.md").write_text("probe A plant")
    mc.rollback(token)
    assert (store / "MEMORY.md").read_text() == "baseline"
    (store / "MEMORY.md").write_text("probe B plant")
    mc.rollback(token)  # the checkpoint is reusable
    assert (store / "MEMORY.md").read_text() == "baseline"
    # Probe-era state was set aside, not deleted.
    asides = list((tmp_path / "backups").glob(f"{token}/pre-rollback-*/memory/MEMORY.md"))
    assert len(asides) == 2


def test_cli_memory_flags_smoke(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(
        "name: mock\nruns_dir: runs\nagent:\n  adapter: mock\n  behavior: good\n"
    )
    probes = tmp_path / "memory.yaml"
    probes.write_text(
        """
probes:
  - id: P1
    kind: durability
    tell: "I never want italics in designs."
    fact_keywords: [italic]
    distractor_sessions: 0
    trigger: "Draft a hero section."
    checks: [{type: contains, value: "never want italics"}]
  - id: P5
    kind: discrimination
    tell: "Just for this one task, keep it short."
    distractor_sessions: 0
    trigger: "Explain pooling."
    checks: [{type: not_contains, value: "just for this one task"}]
"""
    )
    rc = main(
        [
            "run", "memory", "--config", "config.yaml", "--probes", str(probes),
            "--batch", "--cycles", "3", "--isolate", "--shuffle-seed", "11",
        ]
    )
    assert rc == 0
    record = json.loads(next((tmp_path / "runs").glob("*-memory.json")).read_text())
    assert record["shuffle_seed"] == 11
    assert record["isolated"] is True
    assert len(record["probes"][0]["triggers"]) == 3


def test_cli_score_non_tty_leaves_record_unchanged(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    from agent_eval import storage

    storage.save_run(
        {"kind": "texture", "tenure": "warmed", "pending_count": 1, "probes": []},
        "texture",
        "runs",
    )
    rc = main(["score"])
    assert rc == 1
    assert "tty" in capsys.readouterr().out


def test_cli_compare_smoke(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    from agent_eval import scorecard, storage

    storage.save_run(
        {"kind": "suite", "tenure": "warmed", "pass_k_rate": 1.0, "pass_at_1_rate": 1.0},
        "suite",
        "runs",
    )
    record = scorecard.assemble("runs", agent="mock")
    a = tmp_path / "a.json"
    a.write_text(json.dumps(record))
    assert main(["compare", str(a), str(a)]) == 0
    assert "Comparison" in capsys.readouterr().out


def test_cli_memory_run_against_mock(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(
        "name: mock\nruns_dir: runs\nagent:\n  adapter: mock\n  behavior: hoarder\n"
    )
    probes = tmp_path / "memory.yaml"
    probes.write_text(
        """
probes:
  - id: P1
    kind: durability
    tell: "I never want italics in designs."
    fact_keywords: [italic]
    distractor_sessions: 1
    probe_repeats: 1
    trigger: "Draft a hero section."
    checks:
      - type: contains
        value: "never want italics"
  - id: P5
    kind: discrimination
    tell: "Just for this one task, keep it short."
    distractor_sessions: 1
    probe_repeats: 1
    trigger: "Explain pooling."
    checks:
      - type: not_contains
        value: "just for this one task"
"""
    )
    rc = main(
        ["run", "memory", "--config", "config.yaml", "--probes", str(probes), "--batch"]
    )
    assert rc == 0
    saved = list((tmp_path / "runs").glob("*-memory.json"))
    assert len(saved) == 1
    record = json.loads(saved[0].read_text())
    assert record["hoarder"] is True


def test_cli_validate_passes_on_shipped_assets(monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    assert main(["validate"]) == 0
    out = capsys.readouterr().out
    assert "INVALID" not in out


def test_cli_scorecard_smoke(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text(
        "name: mock\nagent:\n  adapter: mock\n  behavior: good\n"
    )
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        """
scenarios:
  - id: S1
    category: routine
    prompt: "say ok"
    checks: [{type: contains, value: "ok"}]
"""
    )
    assert main(["run", "suite", "--config", "config.yaml", "--suite", str(suite), "--batch", "-k", "2"]) == 0
    assert main(["journal", "reliance", "--relied", "--right"]) == 0
    assert main(["scorecard", "--agent", "mock"]) == 0
    out = capsys.readouterr().out
    assert "D1 Competence" in out
