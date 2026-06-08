# Foundry verification

Foundry mode is an optional adapter path for the `ContextRetrievalAgent`. Mock mode remains the guaranteed local demo path.

# Current evidence

The Foundry agent adapter path was smoke-tested locally on 2026-06-08 before source-material attachment with:
```powershell
uv run themis-review samples\change_risky.md --context-mode foundry
```

The command completed successfully and returned a `RetrievedContext` through the shared Themis contract:
```text
source_id: foundry_agent
kind: foundry agent
recommendation: REVIEW REQUIRED
```

The run also wrote a local `.themis/runs/` history entry. That local file is intentionally ignored by Git because it records environment-specific review history.

The configured Foundry agent was later updated with source material on 2026-06-08 with:
```powershell
uv run themis-setup attach-sources
```

That command completed and attached three sample context files through a Foundry vector store.

The original post-attachment run hit an Azure rate limit on a `gpt-4o` Standard deployment with capacity `1`. The project was then moved to a `gpt-4.1-mini` `GlobalStandard` deployment with capacity `10`. After that change, this command completed successfully:
```powershell
uv run themis-review samples\change_risky.md --context-mode foundry
```

The successful run returned a Foundry agent response through `RetrievedContext`, produced a `REVIEW REQUIRED` report and wrote a local run log under `.themis/runs/`.

The source-material setup path is implemented and the local contract supports citations. The current Foundry smoke proves a post-attachment Foundry run can complete. The rendered report still shows a single Foundry-agent context block rather than source-level file citations.

# What this proves

The smoke test proves:
- the local Foundry configuration can be loaded
- optional Foundry dependencies can call the configured project
- the configured Foundry agent can return assistant context
- Themis can pass that context through the same report contract used by mock mode
- the setup assistant can attach local source material to the configured Foundry agent
- the configured Foundry agent can run after source attachment when deployed on a model with sufficient request capacity

# What this does not prove

The current evidence does not prove:
- the response included Foundry file-search citations
- Microsoft IQ grounding was verified end to end after source attachment

# Public wording

Safe wording:
```text
Themis includes deterministic mock retrieval and an optional Foundry agent adapter. The Foundry adapter has a local source-material setup path and returns the same RetrievedContext contract as mock mode when the Foundry run completes.
```

Do not use stronger wording such as “Foundry IQ-grounded retrieval with citations” unless a later verification pass proves configured source material and source-level citation evidence.
