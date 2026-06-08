from __future__ import annotations

from themis.contracts import ReviewReport


def risk_rows(report: ReviewReport) -> list[dict[str, str]]:
    return [
        {
            "Severity": risk.severity,
            "Category": risk.category,
            "Finding": risk.claim,
            "Evidence": risk.evidence,
            "Mitigation": risk.suggested_mitigation,
        }
        for risk in report.risks
    ]


def evidence_gap_rows(report: ReviewReport) -> list[dict[str, str]]:
    return [
        {
            "Level": gap.blocking_level,
            "Missing item": gap.missing_item,
            "Why it matters": gap.why_it_matters,
            "Question for owner": gap.question_for_owner,
        }
        for gap in report.evidence_gaps
    ]


def verification_rows(report: ReviewReport) -> list[dict[str, str]]:
    return [
        {
            "Phase": step.phase,
            "Step": step.step,
            "Expected result": step.expected_result,
            "Failure action": step.failure_action,
        }
        for step in report.verification_steps
    ]


def context_rows(report: ReviewReport) -> list[dict[str, str]]:
    return [
        {
            "Source": context.source_id,
            "Title": context.title,
            "Kind": context.kind,
            "Confidence": f"{context.confidence:.2f}",
            "Citations": ", ".join(context.citations),
        }
        for context in report.retrieved_context
    ]
