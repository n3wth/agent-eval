from agent_eval.checks import CheckContext, overall_status, run_check, run_checks


def test_mechanical_checks():
    assert run_check({"type": "contains", "value": "Hello"}, "well hello there").status == "pass"
    assert run_check({"type": "not_contains", "value": "shadow"}, "box-shadow: none").status == "fail"
    assert run_check({"type": "regex", "value": r"\?"}, "which one?").status == "pass"
    assert run_check({"type": "not_regex", "value": "<em>"}, "plain text").status == "pass"


def test_human_check_pending_when_not_interactive():
    ctx = CheckContext(interactive=False)
    result = run_check({"type": "human", "question": "Did it work?"}, "reply", ctx)
    assert result.status == "pending"
    assert result.scored_by == "human"
    assert ctx.pending_human[0]["question"] == "Did it work?"


def test_overall_status_fail_beats_pending_beats_pass():
    ctx = CheckContext(interactive=False)
    results = run_checks(
        [
            {"type": "contains", "value": "ok"},
            {"type": "human", "question": "q?"},
        ],
        "ok",
        ctx,
    )
    assert overall_status(results) == "pending"
    results = run_checks(
        [
            {"type": "contains", "value": "missing"},
            {"type": "human", "question": "q?"},
        ],
        "ok",
        ctx,
    )
    assert overall_status(results) == "fail"


def test_llm_judge_flags_scorer(tmp_path):
    from agent_eval.adapters.mock import MockAdapter

    judge = MockAdapter({"rules": [{"match": ".", "reply": "PASS — criterion met."}]})
    ctx = CheckContext(judge=judge)
    result = run_check({"type": "llm", "question": "any good?"}, "some reply", ctx)
    assert result.status == "pass"
    assert result.scored_by == "llm"


def test_llm_check_without_judge_is_pending():
    result = run_check({"type": "llm", "question": "q?"}, "reply", CheckContext())
    assert result.status == "pending"
