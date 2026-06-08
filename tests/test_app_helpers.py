from pathlib import Path

from themis.pipeline import run_review


def test_risk_rows_include_reviewer_fields() -> None:
    from themis.ui_rows import risk_rows

    report = run_review(Path("samples/change_risky.md").read_text(encoding="utf-8"))

    rows = risk_rows(report)

    assert rows
    assert {"Severity", "Category", "Finding", "Evidence", "Mitigation"} <= rows[0].keys()


def test_evidence_gap_rows_include_owner_questions() -> None:
    from themis.ui_rows import evidence_gap_rows

    report = run_review(Path("samples/change_incomplete.md").read_text(encoding="utf-8"))

    rows = evidence_gap_rows(report)

    assert rows
    assert {"Level", "Missing item", "Why it matters", "Question for owner"} <= rows[0].keys()


def test_verification_rows_group_steps_by_phase() -> None:
    from themis.ui_rows import verification_rows

    report = run_review(Path("samples/change_safe.md").read_text(encoding="utf-8"))

    rows = verification_rows(report)

    assert rows
    assert {"Phase", "Step", "Expected result", "Failure action"} <= rows[0].keys()
    assert {row["Phase"] for row in rows} >= {"pre-change", "post-change", "rollback"}
