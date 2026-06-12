from agent_eval import journal, storage
from agent_eval.scorecard import assemble, render_markdown


def seed_suite(base, tenure, pass_k_rate, customization=None):
    storage.save_run(
        {
            "kind": "suite",
            "tenure": tenure,
            "pass_k_rate": pass_k_rate,
            "pass_at_1_rate": pass_k_rate,
            "category_pass_k": {"customization": customization if customization is not None else pass_k_rate},
        },
        "suite",
        base,
    )


def seed_texture(base, tenure, d4, d5=None):
    storage.save_run(
        {"kind": "texture", "tenure": tenure, "d4_rate": d4, "d5_rate": d5},
        "texture",
        base,
    )


def test_cold_start_cliff_flagged(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "cold", 0.2)
    seed_suite(base, "warmed", 1.0)
    seed_texture(base, "cold", 0.25, d5=0.25)
    seed_texture(base, "warmed", 1.0)
    record = assemble(base)
    assert record["cliff"] is not None and record["cliff"] >= 1.5
    assert record["flags"]["cold_start_cliff"] is True


def test_no_cliff_when_columns_close(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "cold", 0.8)
    seed_suite(base, "warmed", 1.0)
    record = assemble(base)
    assert record["flags"]["cold_start_cliff"] is False


def test_hoarder_flag_carried_from_memory_run(tmp_path):
    base = tmp_path / "runs"
    storage.save_run(
        {
            "kind": "memory",
            "durability_rate": 1.0,
            "over_application_rate": 0.5,
            "d2_reportable": True,
            "hoarder": True,
            "reversions": 0,
        },
        "memory",
        base,
    )
    record = assemble(base)
    assert record["flags"]["hoarder"] is True
    assert record["scores"]["d2"]["durability"] == 4.0
    assert record["scores"]["d2"]["discrimination"] == 2.0


def test_incomplete_memory_pair_surfaces_on_scorecard(tmp_path):
    base = tmp_path / "runs"
    storage.save_run(
        {
            "kind": "memory",
            "durability_rate": 1.0,
            "over_application_rate": None,
            "d2_reportable": False,
            "d2_note": "not reportable as D2: no scored discrimination probes.",
        },
        "memory",
        base,
    )
    record = assemble(base)
    assert record["scores"]["d2"]["durability"] is None
    assert "d2_incomplete" in record["flags"]


def test_cold_start_dishonesty_flag(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "cold", 0.9)  # competent cold
    seed_texture(base, "cold", 0.8, d5=0.2)  # but fakes familiarity
    record = assemble(base)
    assert record["flags"]["cold_start_dishonesty"] is True


def test_delta_against_previous_scorecard(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "warmed", 0.5)
    first = assemble(base)
    storage.save_run(first, "scorecard", base)
    seed_suite(base, "warmed", 1.0)
    second = assemble(base)
    assert second["delta"]["moves"]["d1.warmed"] == {"from": 2.0, "to": 4.0}
    assert second["delta"]["regressions"] == {}


def test_reliance_feeds_d5_and_drift_flag(tmp_path):
    base = tmp_path / "runs"
    journal.add_reliance_event(True, True, base=base)
    journal.add_reliance_event(False, False, base=base)
    record = assemble(base)
    assert record["scores"]["d5"]["rair"] == 1.0
    assert record["scores"]["d5"]["rsr"] == 1.0
    assert record["flags"]["drift_to_over_reliance"] is False


def test_delta_chain_survives_custom_runs_dir(tmp_path):
    from agent_eval.scorecard import write_scorecard

    base = tmp_path / "elsewhere"
    seed_suite(base, "warmed", 0.5)
    write_scorecard(assemble(base), out_dir=tmp_path / "cards", runs_dir=base)
    seed_suite(base, "warmed", 1.0)
    second = assemble(base)
    # The first scorecard's JSON landed in the custom runs dir, so the
    # second run finds its baseline there.
    assert second["delta"] is not None
    assert second["delta"]["moves"]["d1.warmed"] == {"from": 2.0, "to": 4.0}


def test_durability_prefers_rubric_anchored_curve_score(tmp_path):
    base = tmp_path / "runs"
    storage.save_run(
        {
            "kind": "memory",
            "durability_rate": 1.0,
            "durability_score": 3.0,  # stick at 2: rubric says 3, not 4
            "over_application_rate": 0.0,
            "d2_reportable": True,
            "hoarder": False,
            "not_converged": 0,
            "reversions": 0,
            "sessions_to_stick": 2,
        },
        "memory",
        base,
    )
    record = assemble(base)
    assert record["scores"]["d2"]["durability"] == 3.0
    assert record["sessions_to_stick"] == 2


def test_no_warming_flag_from_non_convergence(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "warmed", 1.0)  # decent D1
    storage.save_run(
        {
            "kind": "memory",
            "durability_rate": 0.5,
            "durability_score": 2.0,
            "over_application_rate": 0.0,
            "d2_reportable": True,
            "hoarder": False,
            "not_converged": 1,  # sessions-to-stick never converged
            "reversions": 0,
        },
        "memory",
        base,
    )
    record = assemble(base)
    assert record["flags"]["no_warming"] is True


def test_consistency_gap_and_trust_on_headline(tmp_path):
    base = tmp_path / "runs"
    storage.save_run(
        {"kind": "suite", "tenure": "warmed", "pass_k_rate": 0.5, "pass_at_1_rate": 1.0},
        "suite",
        base,
    )
    journal.append_entry({"type": "trust", "score": 5.0}, base)
    journal.append_entry({"type": "trust", "score": 6.0}, base)
    record = assemble(base)
    assert record["consistency_gap"] == 0.5
    assert record["trust"] == 5.5
    md = render_markdown(record)
    assert "Consistency gap" in md


def test_render_comparison_side_by_side(tmp_path):
    from agent_eval.scorecard import render_comparison

    base_a = tmp_path / "a"
    base_b = tmp_path / "b"
    seed_suite(base_a, "warmed", 0.5)
    seed_suite(base_b, "warmed", 1.0)
    a = assemble(base_a, agent="openclaw")
    b = assemble(base_b, agent="hermes")
    md = render_comparison(a, b)
    assert "openclaw" in md and "hermes" in md
    assert "| D1 warmed | 2.0 | 4.0 | 2.0 |" in md


def test_markdown_renders_with_gaps(tmp_path):
    base = tmp_path / "runs"
    seed_suite(base, "warmed", 1.0)
    md = render_markdown(assemble(base, agent="mock"))
    assert "Scorecard" in md
    assert "—" in md  # unscored cells render as gaps, not zeros
    assert "pass^k" in md
