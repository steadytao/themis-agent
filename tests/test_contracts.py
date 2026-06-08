import pytest
from pydantic import ValidationError

from themis.contracts import Recommendation, ReviewReport, VerificationStep


def test_review_report_requires_human_review_note() -> None:
    with pytest.raises(ValidationError):
        ReviewReport(
            recommendation=Recommendation.REVIEW_REQUIRED,
            confidence=0.7,
            summary="Review required.",
            facts=[],
            assumptions=[],
            retrieved_context=[],
            risks=[],
            evidence_gaps=[],
            verification_steps=[],
            rollback_questions=[],
            human_review_notes=[],
            reasoning_trace=[],
        )


def test_confidence_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        ReviewReport(
            recommendation=Recommendation.REVIEW_REQUIRED,
            confidence=1.2,
            summary="Review required.",
            facts=[],
            assumptions=[],
            retrieved_context=[],
            risks=[],
            evidence_gaps=[],
            verification_steps=[],
            rollback_questions=[],
            human_review_notes=["A human reviewer must approve the change."],
            reasoning_trace=[],
        )


def test_verification_step_rejects_unknown_phase() -> None:
    with pytest.raises(ValidationError):
        VerificationStep(
            phase="deploy",
            step="Deploy the change.",
            expected_result="Change deployed.",
            failure_action="Try again.",
        )
