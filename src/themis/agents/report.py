from __future__ import annotations

from themis.contracts import (
    ChangeProposal,
    EvidenceGap,
    GuardrailViolation,
    ReasoningTraceStep,
    Recommendation,
    RetrievedContext,
    ReviewReport,
    RiskFinding,
    VerificationStep,
)


def build_review_report(
    proposal: ChangeProposal,
    context: list[RetrievedContext],
    risks: list[RiskFinding],
    gaps: list[EvidenceGap],
    verification: list[VerificationStep],
    guardrail_violations: list[GuardrailViolation] | None = None,
) -> ReviewReport:
    violations = guardrail_violations or []
    recommendation = _recommendation(risks, gaps, violations)
    confidence = _confidence(risks, gaps, violations)
    assumptions = _assumptions(proposal, risks)

    return ReviewReport(
        recommendation=recommendation,
        confidence=confidence,
        summary=f"Themis reviewed '{proposal.title}' for {proposal.service} in {proposal.environment}.",
        facts=_facts(proposal),
        assumptions=assumptions,
        retrieved_context=context,
        risks=risks,
        evidence_gaps=gaps,
        verification_steps=verification,
        rollback_questions=[
            "Who owns the rollback decision during the change window?",
            "What condition triggers rollback instead of continued troubleshooting?",
            "How will reviewers confirm the old path is restored?",
        ],
        human_review_notes=[
            "Themis is advisory. A human reviewer must approve, reject or request changes before deployment.",
            "The report separates evidence from assumptions; unresolved assumptions should be treated as review work.",
        ],
        reasoning_trace=[
            ReasoningTraceStep(
                agent="ChangeIntakeAgent",
                summary="Parsed the proposal into service, environment, exposure, identity and rollback fields.",
                output_reference="ChangeProposal",
            ),
            ReasoningTraceStep(
                agent="ContextRetrievalAgent",
                summary="Retrieved local or Foundry context using the shared RetrievedContext contract.",
                output_reference="RetrievedContext[]",
            ),
            ReasoningTraceStep(
                agent="RiskAnalysisAgent",
                summary="Ranked security, reliability and operational risks from the proposal.",
                output_reference="RiskFinding[]",
            ),
            ReasoningTraceStep(
                agent="EvidenceGapAgent",
                summary="Identified missing evidence and owner questions.",
                output_reference="EvidenceGap[]",
            ),
            ReasoningTraceStep(
                agent="VerificationPlannerAgent",
                summary="Prepared pre-change, post-change and rollback verification steps.",
                output_reference="VerificationStep[]",
            ),
            ReasoningTraceStep(
                agent="ReviewReportAgent",
                summary="Produced a structured advisory report with confidence and human-review notes.",
                output_reference="ReviewReport",
            ),
        ],
        guardrail_violations=violations,
    )


def _recommendation(
    risks: list[RiskFinding],
    gaps: list[EvidenceGap],
    violations: list[GuardrailViolation],
) -> Recommendation:
    if violations:
        return Recommendation.DO_NOT_PROCEED_YET
    if len(gaps) >= 4:
        return Recommendation.INSUFFICIENT_EVIDENCE
    if any(gap.blocking_level == "blocking" for gap in gaps) and len(gaps) >= 3:
        return Recommendation.DO_NOT_PROCEED_YET
    if any(risk.severity == "high" for risk in risks) or gaps:
        return Recommendation.REVIEW_REQUIRED
    return Recommendation.APPROVE_WITH_CONDITIONS


def _confidence(
    risks: list[RiskFinding],
    gaps: list[EvidenceGap],
    violations: list[GuardrailViolation],
) -> float:
    confidence = 0.85
    confidence -= len([risk for risk in risks if risk.severity == "high"]) * 0.15
    confidence -= len([risk for risk in risks if risk.severity == "medium"]) * 0.06
    confidence -= len([gap for gap in gaps if gap.blocking_level == "blocking"]) * 0.12
    confidence -= len([gap for gap in gaps if gap.blocking_level == "conditional"]) * 0.06
    confidence -= len(violations) * 0.2
    return max(0.1, min(0.95, round(confidence, 2)))


def _facts(proposal: ChangeProposal) -> list[str]:
    return [
        f"Service: {proposal.service}.",
        f"Environment: {proposal.environment}.",
        f"Change type: {proposal.change_type}.",
        f"Network exposure: {proposal.network_exposure}.",
        f"Deployment window: {proposal.deployment_window}.",
        f"Rollback plan: {proposal.rollback_plan}.",
    ]


def _assumptions(proposal: ChangeProposal, risks: list[RiskFinding]) -> list[str]:
    assumptions = [risk.assumption for risk in risks if risk.assumption]
    if proposal.data_sensitivity == "unknown":
        assumptions.append("Data sensitivity is not stated and should be confirmed by the owner.")
    return assumptions or ["No major unstated assumptions were needed beyond the submitted proposal."]
