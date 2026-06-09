from pathlib import Path

from themis.agents.intake import parse_change_proposal
from themis.contracts import Recommendation
from themis.pipeline import run_review


def read_sample(name: str) -> str:
    return Path("samples", name).read_text(encoding="utf-8")


def test_risky_change_requires_review_or_stop() -> None:
    report = run_review(read_sample("change_risky.md"), context_mode="mock")

    assert report.recommendation in {
        Recommendation.REVIEW_REQUIRED,
        Recommendation.DO_NOT_PROCEED_YET,
    }
    assert any(risk.severity == "high" for risk in report.risks)
    assert any(risk.category == "network exposure" for risk in report.risks)


def test_incomplete_change_has_insufficient_evidence() -> None:
    report = run_review(read_sample("change_incomplete.md"), context_mode="mock")

    assert report.recommendation == Recommendation.INSUFFICIENT_EVIDENCE
    assert report.evidence_gaps
    assert report.confidence <= 0.45


def test_safe_change_still_requires_verification_and_rollback_questions() -> None:
    report = run_review(read_sample("change_safe.md"), context_mode="mock")

    assert report.recommendation == Recommendation.APPROVE_WITH_CONDITIONS
    assert report.verification_steps
    assert any(step.phase == "rollback" for step in report.verification_steps)
    assert report.rollback_questions
    assert "human" in " ".join(report.human_review_notes).lower()


def test_safe_sample_is_classified_as_certificate_rotation() -> None:
    proposal = parse_change_proposal(read_sample("change_safe.md"))

    assert proposal.change_type == "certificate rotation"
    assert proposal.network_exposure == "internal"


def test_missing_rollback_reduces_confidence_and_creates_gap() -> None:
    report = run_review(
        """
        # Admin portal routing update

        Expose the admin portal through a public endpoint for production.
        Authentication will be added later. Deploy during business hours.
        """,
        context_mode="mock",
    )

    assert report.confidence < 0.6
    assert any("rollback" in gap.missing_item.lower() for gap in report.evidence_gaps)


def test_overbroad_source_range_creates_high_severity_risk() -> None:
    report = run_review(
        """
        # Public listener update

        Service: admin portal
        Environment: production

        Expose the admin portal through a public Azure Application Gateway.
        Allow source range 0.0.0.0/0 for initial testing.
        Rollback will restore the previous listener.
        """,
        context_mode="mock",
    )

    assert any(risk.severity == "high" and "overbroad" in risk.claim.lower() for risk in report.risks)


def test_retrieved_context_informs_risk_and_gap_judgement() -> None:
    report = run_review(read_sample("change_risky.md"), context_mode="mock")

    assert any(
        "retrieved context" in risk.evidence.lower()
        and "source range" in risk.evidence.lower()
        for risk in report.risks
    )
    assert any(
        "retrieved context" in gap.why_it_matters.lower()
        for gap in report.evidence_gaps
        if gap.missing_item in {"Authentication model", "Approved source ranges"}
    )
    assert len(report.assumptions) == len(set(report.assumptions))


def test_business_hours_deployment_adds_pre_change_timing_step() -> None:
    report = run_review(read_sample("change_risky.md"), context_mode="mock")

    assert any(
        step.phase == "pre-change" and "business-hours" in step.step.lower()
        for step in report.verification_steps
    )


def test_mock_pipeline_is_deterministic() -> None:
    proposal = read_sample("change_risky.md")

    first = run_review(proposal, context_mode="mock")
    second = run_review(proposal, context_mode="mock")

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
