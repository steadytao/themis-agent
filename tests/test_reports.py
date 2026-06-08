from pathlib import Path

from themis.pipeline import run_review
from themis.render.markdown_report import render_markdown_report


SAMPLE_OUTPUTS = {
    "change_safe.md": "safe_review.md",
    "change_risky.md": "risky_review.md",
    "change_incomplete.md": "incomplete_review.md",
}


def test_markdown_report_includes_required_sections() -> None:
    proposal = Path("samples/change_risky.md").read_text(encoding="utf-8")
    report = run_review(proposal, context_mode="mock")

    markdown = render_markdown_report(report)

    for heading in [
        "## Recommendation",
        "## Confidence",
        "## Facts",
        "## Assumptions",
        "## Missing evidence",
        "## Risks",
        "## Verification plan",
        "## Rollback questions",
        "## Human reviewer notes",
        "## Reasoning trace",
    ]:
        assert heading in markdown


def test_report_names_retrieved_context() -> None:
    proposal = Path("samples/change_safe.md").read_text(encoding="utf-8")
    report = run_review(proposal, context_mode="mock")
    markdown = render_markdown_report(report)

    assert "Retrieved context" in markdown
    assert "context_" in markdown


def test_report_does_not_claim_change_is_safe() -> None:
    proposal = Path("samples/change_safe.md").read_text(encoding="utf-8")
    report = run_review(proposal, context_mode="mock")
    markdown = render_markdown_report(report).lower()

    assert "the change is safe" not in markdown
    assert "automatically approved" not in markdown


def test_checked_sample_outputs_match_generated_reports() -> None:
    for sample_name, output_name in SAMPLE_OUTPUTS.items():
        proposal = Path("samples", sample_name).read_text(encoding="utf-8")
        expected = Path("outputs", output_name).read_text(encoding="utf-8")

        report = run_review(proposal, context_mode="mock")

        assert render_markdown_report(report) == expected
