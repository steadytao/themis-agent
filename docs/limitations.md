# Limitations

Themis has a deliberately narrow scope.
- Samples are synthetic.
- The default path is deterministic local retrieval.
- Foundry mode requires external setup and should be described only at the level actually verified.
- Themis is advisory and does not approve changes.
- The review pipeline does not deploy, scan live systems or mutate cloud resources.

# Current limits

The current parser is heuristic. It is intended for a controlled demo scenario and testable sample changes, not arbitrary production change records.

The current risk model covers selected infrastructure-review concerns:
- public exposure
- unclear authentication
- broad source ranges
- business-hours deployment
- missing observability
- missing rollback evidence

It does not model every cloud service, every identity pattern or every deployment system.

# Foundry and IQ limits

Mock mode is the guaranteed path. Foundry mode depends on Azure subscription state, regional model quota, optional dependencies and local `.themis` configuration. The setup assistant can create or use a Foundry agent and `uv run themis-setup attach-sources` can attach the sample context files through Foundry file search.

The included sample-source Foundry file-search path has been verified with source-level citations using `gpt-4.1-mini` on `GlobalStandard` capacity `10`. The evidence is in [foundry_verification.md](foundry_verification.md). Other source corpora, model deployments or scenarios should be verified separately before being presented as equivalent.

# Non-goals

Themis does not:
- deploy infrastructure
- scan live systems
- exploit targets
- replace security review
- replace owner approval
- prove compliance
- certify a change as safe

The optional setup assistant is outside that review boundary. It can create Azure and Foundry resources after confirmation.
