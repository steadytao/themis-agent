# Themis infrastructure change review

## Recommendation
INSUFFICIENT EVIDENCE

## Confidence
0.37

## Summary
Themis reviewed 'Admin route update' for admin portal in production.

## Facts
- Service: admin portal.
- Environment: production.
- Change type: configuration.
- Network exposure: unknown.
- Deployment window: unknown.
- Rollback plan: unknown.

## Assumptions
- The service may rely on network placement rather than explicit authentication.

## Retrieved context
- `context_context_deployment_runbook` - Context deployment runbook (local markdown, confidence 0.67)
  - Every infrastructure change should include pre-change checks, post-change health checks and a rollback plan with an owner, trigger and success condition. Rollback should restore a previous known-good state rather than rely on improvisation.
  - Citations: samples/context_deployment_runbook.md
- `context_context_architecture` - Context architecture note (local markdown, confidence 0.59)
  - Azure Application Gateway and load balancer changes must record the listener, target, certificate, source ranges and health probe being changed. Reviewers should be able to identify the previous known-good route before the change begins.
  - Citations: samples/context_architecture.md
- `context_context_network_policy` - Context network policy (local markdown, confidence 0.51)
  - Public endpoints must not use 0.0.0.0/0 or unrestricted source ranges for administrative surfaces without a named exception. Approved CIDR ranges, WAF policy and negative-access tests should be recorded before deployment.
  - Citations: samples/context_network_policy.md

## Missing evidence
- **Authentication model** (blocking)
  - Why it matters: Public or administrative access must not rely on unclear identity controls.
  - Owner question: Which identity provider, policy and negative-access test prove unauthorised access is denied?
- **Rollback plan** (blocking)
  - Why it matters: Reviewers need to know how the previous routing state can be restored.
  - Owner question: What exact rollback steps and success checks will be used?
- **Owner approval** (conditional)
  - Why it matters: The service owner should accept the exposure and operational risk.
  - Owner question: Which owner approved this change and where is that recorded?
- **Post-change verification** (conditional)
  - Why it matters: A working-looking deployment can still expose the wrong path or fail negative checks.
  - Owner question: What health, access-denial, log and alert checks will be run after the change?

## Risks
- **identity/authentication** (medium) - The authentication model is missing or unclear.
  - Evidence: unknown
  - Impact: Unauthorised access may not be prevented if the routing change exposes the service.
  - Mitigation: Document the authentication requirement and verify unauthorised requests are denied.
- **rollback** (medium) - The rollback path is not documented.
  - Evidence: No rollback statement found.
  - Impact: Recovery may depend on improvisation during an incident.
  - Mitigation: Document the rollback trigger, owner, steps and verification result.

## Verification plan
- **pre-change**: Confirm the service owner has approved the change and accepted the proposed exposure boundary.
  - Expected result: Owner approval is recorded before implementation.
  - Failure action: Do not proceed until ownership and approval are clear.
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
