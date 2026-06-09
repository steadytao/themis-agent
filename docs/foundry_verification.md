# Foundry verification

Foundry mode is an optional context-retrieval path for `ContextRetrievalAgent`. Mock mode remains the guaranteed local demo path.

# Verified sample path

On 2026-06-09, the configured Foundry-backed retrieval path was verified against the included sample source material with:
```powershell
uv run themis-review samples\change_risky.md --context-mode foundry
```

The run used:
- model deployment: `gpt-4.1-mini`
- deployment SKU: `GlobalStandard`
- capacity: `10`
- source material: `samples/context_architecture.md`, `samples/context_network_policy.md`, `samples/context_deployment_runbook.md`

The rendered report included Foundry file-search citation markers in the retrieved excerpt and this citation line:
```text
Citations: context_architecture.md, context_network_policy.md, context_deployment_runbook.md
```

The structured run log recorded:
```text
recommendation: REVIEW REQUIRED
confidence: 0.10
source_id: foundry_agent
kind: foundry agent
citation_count: 3
```

Run logs are written under `.themis/runs/` and are intentionally ignored by Git because they are local run history.

# Source attachment

The configured Foundry agent was updated with sample source material using:
```powershell
uv run themis-setup attach-sources
```

That command attached three sample context files through a Foundry vector store. Earlier testing showed that a `gpt-4o` Standard deployment at capacity `1` could hit Azure request-rate limits before the review completed. The verified sample path uses `gpt-4.1-mini` on `GlobalStandard` capacity `10`.

# Verified scope

This verification shows that:
- the local Foundry configuration can be loaded
- optional Foundry dependencies can call the configured project
- the setup assistant can attach the sample source material to the configured Foundry agent
- the configured Foundry agent can retrieve from the attached sample source material
- Themis can pass Foundry context through the same `RetrievedContext` contract used by mock mode
- Themis can render source-level file-search citations in the markdown report

This verification covers the included sample source files and the risky sample change. Other source corpora, model deployments or scenarios should be verified separately before being presented as equivalent.

# Limits

This verification does not show that:
- every Foundry run will include citations
- arbitrary source material will be retrieved accurately without review
- Themis is suitable for production deployment gates
- Themis can replace human approval
