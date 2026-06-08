from __future__ import annotations

from themis.contracts import ChangeProposal, EvidenceGap, RiskFinding, VerificationStep


def plan_verification(
    proposal: ChangeProposal,
    risks: list[RiskFinding],
    gaps: list[EvidenceGap],
) -> list[VerificationStep]:
    del risks, gaps
    steps = [
        VerificationStep(
            phase="pre-change",
            step="Confirm the service owner has approved the change and accepted the proposed exposure boundary.",
            expected_result="Owner approval is recorded before implementation.",
            failure_action="Do not proceed until ownership and approval are clear.",
        ),
        VerificationStep(
            phase="pre-change",
            step="Confirm the rollback artefact and previous routing configuration are available.",
            expected_result="Rollback path can be executed without new design work.",
            failure_action="Treat the change as not ready for review.",
        ),
        VerificationStep(
            phase="post-change",
            step="Verify service health through the intended endpoint and no unexpected public paths.",
            expected_result="Only the approved route is reachable and health checks are green.",
            failure_action="Rollback or disable the new route.",
        ),
        VerificationStep(
            phase="post-change",
            step="Verify unauthorised requests are denied and logged.",
            expected_result="Unauthorised access receives denial and creates observable telemetry.",
            failure_action="Rollback or remove public exposure.",
        ),
        VerificationStep(
            phase="rollback",
            step="Restore the previous target, listener or routing rule if verification fails.",
            expected_result="Traffic returns to the prior known-good path.",
            failure_action="Escalate to incident handling if rollback does not restore service.",
        ),
    ]

    if proposal.deployment_window == "business hours":
        steps.insert(
            1,
            VerificationStep(
                phase="pre-change",
                step="Confirm why a business-hours deployment is necessary.",
                expected_result="Risk owner accepts the timing or the change moves to a maintenance window.",
                failure_action="Reschedule the change.",
            ),
        )

    return steps
