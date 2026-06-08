from __future__ import annotations

from themis.contracts import ReviewReport


def render_markdown_report(report: ReviewReport) -> str:
    lines = [
        "# Themis infrastructure change review",
        "",
        "## Recommendation",
        report.recommendation.value,
        "",
        "## Confidence",
        f"{report.confidence:.2f}",
        "",
        "## Summary",
        report.summary,
        "",
        "## Facts",
        *_bullets(report.facts),
        "",
        "## Assumptions",
        *_bullets(report.assumptions),
        "",
        "## Retrieved context",
    ]
    for context in report.retrieved_context:
        lines.extend(
            [
                f"- `{context.source_id}` - {context.title} ({context.kind}, confidence {context.confidence:.2f})",
                f"  - {context.relevant_excerpt}",
            ]
        )
        if context.citations:
            lines.append(f"  - Citations: {', '.join(context.citations)}")

    lines.extend(["", "## Missing evidence"])
    for gap in report.evidence_gaps:
        lines.extend(
            [
                f"- **{gap.missing_item}** ({gap.blocking_level})",
                f"  - Why it matters: {gap.why_it_matters}",
                f"  - Owner question: {gap.question_for_owner}",
            ]
        )
    if not report.evidence_gaps:
        lines.append("- No major evidence gaps identified.")

    lines.extend(["", "## Risks"])
    for risk in report.risks:
        lines.extend(
            [
                f"- **{risk.category}** ({risk.severity}) - {risk.claim}",
                f"  - Evidence: {risk.evidence}",
                f"  - Impact: {risk.impact}",
                f"  - Mitigation: {risk.suggested_mitigation}",
            ]
        )
    if not report.risks:
        lines.append("- No high or medium risks identified from the submitted evidence.")

    lines.extend(["", "## Verification plan"])
    for step in report.verification_steps:
        lines.extend(
            [
                f"- **{step.phase}**: {step.step}",
                f"  - Expected result: {step.expected_result}",
                f"  - Failure action: {step.failure_action}",
            ]
        )

    lines.extend(["", "## Rollback questions", *_bullets(report.rollback_questions)])
    lines.extend(["", "## Human reviewer notes", *_bullets(report.human_review_notes)])

    if report.guardrail_violations:
        lines.extend(["", "## Guardrail violations"])
        for violation in report.guardrail_violations:
            lines.append(f"- {violation.kind}: {violation.reason} ({violation.redacted_excerpt})")

    lines.extend(["", "## Reasoning trace"])
    for step in report.reasoning_trace:
        lines.append(f"- **{step.agent}**: {step.summary} (`{step.output_reference}`)")

    return "\n".join(lines).strip() + "\n"


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]
