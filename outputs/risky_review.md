# Themis infrastructure change review

## Recommendation
REVIEW REQUIRED

## Confidence
0.10

## Summary
Themis reviewed 'Public admin service exposure' for internal admin portal in production.

## Facts
- Service: internal admin portal.
- Environment: production.
- Change type: network exposure.
- Network exposure: public.
- Deployment window: business hours.
- Rollback plan: provided.

## Assumptions
- The service may rely on network placement rather than explicit authentication.

## Retrieved context
- `context_context_architecture` - Context architecture note (local markdown, confidence 0.90)
  - Azure Application Gateway and load balancer changes must record the listener, target, certificate, source ranges and health probe being changed. Reviewers should be able to identify the previous known-good route before the change begins.
  - Citations: samples/context_architecture.md
- `context_context_network_policy` - Context network policy (local markdown, confidence 0.90)
  - Public endpoints must not use 0.0.0.0/0 or unrestricted source ranges for administrative surfaces without a named exception. Approved CIDR ranges, WAF policy and negative-access tests should be recorded before deployment.
  - Citations: samples/context_network_policy.md
- `context_context_deployment_runbook` - Context deployment runbook (local markdown, confidence 0.75)
  - Every infrastructure change should include pre-change checks, post-change health checks and a rollback plan with an owner, trigger and success condition. Rollback should restore a previous known-good state rather than rely on improvisation.
  - Citations: samples/context_deployment_runbook.md

## Missing evidence
- **Authentication model** (blocking)
  - Why it matters: Retrieved context expects authentication or access-denial evidence for public or administrative access.
  - Owner question: Which identity provider, policy and negative-access test prove unauthorised access is denied?
- **Owner approval** (conditional)
  - Why it matters: The service owner should accept the exposure and operational risk.
  - Owner question: Which owner approved this change and where is that recorded?

## Risks
- **network exposure** (high) - The change introduces or modifies public network exposure.
  - Evidence: public
  - Impact: An internal or administrative service may become reachable beyond the intended audience.
  - Mitigation: Confirm approved source ranges, authentication, WAF policy and explicit owner approval before proceeding.
- **identity/authentication** (high) - The authentication model is missing or unclear.
  - Evidence: missing or unclear
  - Impact: Unauthorised access may not be prevented if the routing change exposes the service.
  - Mitigation: Document the authentication requirement and verify unauthorised requests are denied.
- **network exposure** (high) - The proposed source range is overbroad.
  - Evidence: Proposal references any source or 0.0.0.0/0.
  - Impact: The exposed service may be reachable from more networks than intended.
  - Mitigation: Replace broad source ranges with approved CIDR ranges and record the approval.
- **network exposure** (high) - Retrieved context requires approved source ranges for this exposure.
  - Evidence: Retrieved context `Context architecture note` expects approved source ranges; the proposal does not provide approved source-range evidence.
  - Impact: The public route may be broader than the documented policy or runbook permits.
  - Mitigation: Record the approved CIDR ranges, approval source and negative-access test before review.
- **identity/authentication** (high) - Retrieved context requires authentication evidence for public or administrative access.
  - Evidence: Retrieved context `Context network policy` expects authentication or access-denial evidence; the proposal leaves the authentication model unclear.
  - Impact: The change may expose an administrative surface before identity controls are verified.
  - Mitigation: Document the identity provider, access policy and negative-access test before review.
- **deployment window** (medium) - The change is scheduled during business hours.
  - Evidence: business hours
  - Impact: A failed routing or TLS change may affect active users and lengthen recovery pressure.
  - Mitigation: Use a maintenance window or document why business-hours deployment is justified.

## Verification plan
- **pre-change**: Confirm the service owner has approved the change and accepted the proposed exposure boundary.
  - Expected result: Owner approval is recorded before implementation.
  - Failure action: Do not proceed until ownership and approval are clear.
- **pre-change**: Confirm why a business-hours deployment is necessary.
  - Expected result: Risk owner accepts the timing or the change moves to a maintenance window.
  - Failure action: Reschedule the change.
- **pre-change**: Confirm the rollback artefact and previous routing configuration are available.
  - Expected result: Rollback path can be executed without new design work.
  - Failure action: Treat the change as not ready for review.
- **post-change**: Verify service health through the intended endpoint and no unexpected public paths.
  - Expected result: Only the approved route is reachable and health checks are green.
  - Failure action: Rollback or disable the new route.
- **post-change**: Verify unauthorised requests are denied and logged.
  - Expected result: Unauthorised access receives denial and creates observable telemetry.
  - Failure action: Rollback or remove public exposure.
- **rollback**: Restore the previous target, listener or routing rule if verification fails.
  - Expected result: Traffic returns to the prior known-good path.
  - Failure action: Escalate to incident handling if rollback does not restore service.

## Rollback questions
- Who owns the rollback decision during the change window?
- What condition triggers rollback instead of continued troubleshooting?
- How will reviewers confirm the old path is restored?

## Human reviewer notes
- Themis is advisory. A human reviewer must approve, reject or request changes before deployment.
- The report separates evidence from assumptions; unresolved assumptions should be treated as review work.

## Reasoning trace
- **ChangeIntakeAgent**: Parsed the proposal into service, environment, exposure, identity and rollback fields. (`ChangeProposal`)
- **ContextRetrievalAgent**: Retrieved local or Foundry context using the shared RetrievedContext contract. (`RetrievedContext[]`)
- **RiskAnalysisAgent**: Ranked security, reliability and operational risks from the proposal. (`RiskFinding[]`)
- **EvidenceGapAgent**: Identified missing evidence and owner questions. (`EvidenceGap[]`)
- **VerificationPlannerAgent**: Prepared pre-change, post-change and rollback verification steps. (`VerificationStep[]`)
- **ReviewReportAgent**: Produced a structured advisory report with confidence and human-review notes. (`ReviewReport`)
