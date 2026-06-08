from __future__ import annotations

from themis.contracts import ChangeProposal, RetrievedContext, RiskFinding


def analyse_risks(proposal: ChangeProposal, context: list[RetrievedContext]) -> list[RiskFinding]:
    del context
    lower = proposal.raw_text.lower()
    risks: list[RiskFinding] = []

    if proposal.network_exposure == "public":
        risks.append(
            RiskFinding(
                category="network exposure",
                severity="high",
                claim="The change introduces or modifies public network exposure.",
                evidence=proposal.network_exposure,
                assumption=None,
                impact="An internal or administrative service may become reachable beyond the intended audience.",
                suggested_mitigation="Confirm approved source ranges, authentication, WAF policy and explicit owner approval before proceeding.",
            )
        )

    if proposal.identity_changes in {"missing or unclear", "unknown"} and (
        proposal.network_exposure == "public" or proposal.data_sensitivity == "sensitive"
    ):
        risks.append(
            RiskFinding(
                category="identity/authentication",
                severity="high" if proposal.network_exposure == "public" else "medium",
                claim="The authentication model is missing or unclear.",
                evidence=proposal.identity_changes,
                assumption="The service may rely on network placement rather than explicit authentication.",
                impact="Unauthorised access may not be prevented if the routing change exposes the service.",
                suggested_mitigation="Document the authentication requirement and verify unauthorised requests are denied.",
            )
        )

    if "0.0.0.0/0" in lower or "any source" in lower or "all sources" in lower:
        risks.append(
            RiskFinding(
                category="network exposure",
                severity="high",
                claim="The proposed source range is overbroad.",
                evidence="Proposal references any source or 0.0.0.0/0.",
                assumption=None,
                impact="The exposed service may be reachable from more networks than intended.",
                suggested_mitigation="Replace broad source ranges with approved CIDR ranges and record the approval.",
            )
        )

    if proposal.deployment_window == "business hours":
        risks.append(
            RiskFinding(
                category="deployment window",
                severity="medium",
                claim="The change is scheduled during business hours.",
                evidence=proposal.deployment_window,
                assumption=None,
                impact="A failed routing or TLS change may affect active users and lengthen recovery pressure.",
                suggested_mitigation="Use a maintenance window or document why business-hours deployment is justified.",
            )
        )

    if "monitoring" not in lower and "alert" not in lower and "logs" not in lower:
        risks.append(
            RiskFinding(
                category="logging/observability",
                severity="medium",
                claim="The proposal does not describe monitoring, logging or alert verification.",
                evidence="No observability evidence found in proposal.",
                assumption=None,
                impact="A failed or abused exposure may not be detected quickly.",
                suggested_mitigation="Add log, metric and alert checks to the post-change verification plan.",
            )
        )

    if proposal.rollback_plan == "unknown":
        risks.append(
            RiskFinding(
                category="rollback",
                severity="medium",
                claim="The rollback path is not documented.",
                evidence="No rollback statement found.",
                assumption=None,
                impact="Recovery may depend on improvisation during an incident.",
                suggested_mitigation="Document the rollback trigger, owner, steps and verification result.",
            )
        )

    return risks
