# Themis documentation

Themis documentation is split by purpose. Start with the repository README for installation and the basic demo path then use these documents for design, safety, setup and verification details.
- [../README.md](../README.md), project overview, quick start and CLI commands
- [architecture.md](architecture.md), agent pipeline, contracts and retrieval boundary
- [architecture.mmd](architecture.mmd), Mermaid architecture diagram source
- [safety_model.md](safety_model.md), read-only boundary, guardrails and human approval model
- [iq_integration.md](iq_integration.md), mock retrieval, Foundry setup and local configuration
- [foundry_verification.md](foundry_verification.md), current Foundry smoke-test evidence and IQ boundary
- [testing.md](testing.md), expected checks, coverage targets and known limits
- [limitations.md](limitations.md), explicit non-goals and current gaps

# Reading order

For a quick project review:
- read [../README.md](../README.md)
- run `uv run themis-review samples/change_risky.md`
- read [architecture.md](architecture.md)
- read [safety_model.md](safety_model.md)

For maintenance work:
- read [testing.md](testing.md)
- read [iq_integration.md](iq_integration.md)
- inspect the sample changes and context files in [../samples/](../samples/)
- run `uv run pytest -q`

For verification:
- read [testing.md](testing.md)
- read [limitations.md](limitations.md)
- read [foundry_verification.md](foundry_verification.md)
