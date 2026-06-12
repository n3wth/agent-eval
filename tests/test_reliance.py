from agent_eval.reliance import summarize


def ev(date, relied, right):
    return {"date": date, "relied": relied, "agent_right": right}


def test_rair_and_rsr_are_the_2x2_not_volume():
    events = [
        ev("2026-06-01", True, True),   # appropriate reliance
        ev("2026-06-01", True, True),
        ev("2026-06-01", False, True),  # under-reliance
        ev("2026-06-02", True, False),  # over-reliance
        ev("2026-06-02", False, False), # appropriate self-reliance
    ]
    summary = summarize(events)
    row = summary["rows"][0]
    assert row["rair"] == 2 / 3
    assert row["rsr"] == 1 / 2
    assert row["over_reliance_events"] == 1
    assert row["under_reliance_events"] == 1


def test_drift_to_over_reliance_flagged():
    # Week 1: calibrated. Week 3: deferring more (RAIR up) while RSR falls —
    # the pattern a delegation-volume line would have rewarded.
    week1 = [
        ev("2026-06-01", True, True),
        ev("2026-06-01", False, True),
        ev("2026-06-01", False, False),
        ev("2026-06-01", False, False),
    ]
    week3 = [
        ev("2026-06-15", True, True),
        ev("2026-06-15", True, True),
        ev("2026-06-15", True, False),
        ev("2026-06-15", False, False),
    ]
    summary = summarize(week1 + week3)
    assert summary["drift_to_over_reliance"] is True


def test_both_rising_is_not_drift():
    week1 = [
        ev("2026-06-01", True, True),
        ev("2026-06-01", False, True),
        ev("2026-06-01", True, False),
        ev("2026-06-01", False, False),
    ]
    week3 = [
        ev("2026-06-15", True, True),
        ev("2026-06-15", True, True),
        ev("2026-06-15", False, False),
        ev("2026-06-15", False, False),
    ]
    summary = summarize(week1 + week3)
    assert summary["drift_to_over_reliance"] is False


def test_empty_quadrants_yield_none_not_zero():
    summary = summarize([ev("2026-06-01", True, True)])
    row = summary["rows"][0]
    assert row["rair"] == 1.0
    assert row["rsr"] is None  # no agent-wrong events: RSR is unknowable, not 0


def test_per_capability_grouping():
    events = [
        dict(ev("2026-06-01", True, True), capability="refactor"),
        dict(ev("2026-06-01", True, False), capability="finance"),
    ]
    summary = summarize(events, by="capability")
    groups = {r["group"] for r in summary["rows"]}
    assert groups == {"refactor", "finance"}
