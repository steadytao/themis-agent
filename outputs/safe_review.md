# Themis infrastructure change review

## Recommendation
APPROVE WITH CONDITIONS

## Confidence
0.85

## Summary
Themis reviewed 'Private metrics endpoint certificate rotation' for internal metrics API in production.

## Facts
- Service: internal metrics API.
- Environment: production.
- Change type: certificate rotation.
- Network exposure: internal.
- Deployment window: maintenance window.
- Rollback plan: provided.

## Assumptions
- Data sensitivity is not stated and should be confirmed by the owner.

## Retrieved context
- `context_context_architecture` - Context architecture note (local markdown, confidence 0.90)
  - Azure Application Gateway and load balancer changes must record the listener, target, certificate, source ranges and health probe being changed. Reviewers should be able to identify the previous known-good route before the change begins.
  - Citations: samples/context_architecture.md
- `context_context_deployment_runbook` - Context deployment runbook (local markdown, confidence 0.90)
  - Every infrastructure change should include pre-change checks, post-change health checks and a rollback plan with an owner, trigger and success condition. Rollback should restore a previous known-good state rather than rely on improvisation.
  - Citations: samples/context_deployment_runbook.md
- `context_context_network_policy` - Context network policy (local markdown, confidence 0.67)
  - Network security group changes should be reviewed for blast radius, logging and least privilege. Changes that increase public reachability require stronger verification than private-only changes.
  - Citations: samples/context_network_policy.md

## Missing evidence
- No major evidence gaps identified.

## Risks
- No high or medium risks identified from the submitted evidence.

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
