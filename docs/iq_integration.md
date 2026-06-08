# Microsoft IQ integration

Themis keeps Microsoft IQ/Foundry retrieval behind the `ContextRetrievalAgent` contract. Mock mode is the guaranteed retrieval path. Foundry mode is currently a Foundry agent adapter unless configured source material and verification prove an IQ-grounded retrieval path.

The stable interface is:
```python
retrieve_context(query, mode="mock" | "foundry") -> list[RetrievedContext]
```

## Mock mode

Mock mode reads local markdown files from `samples/`. It is deterministic and used by tests. Each returned `RetrievedContext` includes a citation to the local markdown source.

## Foundry mode

Foundry mode requires optional dependencies and local project configuration:
```powershell
uv sync --extra foundry
az login
uv run themis-setup
uv run themis-review samples/change_risky.md --context-mode foundry
```

The configured Foundry agent should have source material containing the same kind of architecture, network policy and deployment runbook context used by the mock samples. The setup wizard creates new agents with file-search source material when the sample context files are present. The default model deployment is `gpt-4.1-mini` on `GlobalStandard` capacity `10` which is the deployment shape used for the current local smoke test.

For an existing configured agent, attach the source material with:
```powershell
uv run themis-setup attach-sources
```

This command uploads the sample context files, creates a vector store and updates the configured Foundry agent with file search. It stores the vector-store ID and uploaded file IDs in `.themis/foundry.local.json`. The file contains resource identifiers, not credentials; it should remain local.

The Foundry agent adapter path has been smoke-tested locally. Source attachment has also been tested. The post-source-attachment Foundry review command completed after moving the configured agent from `gpt-4o` capacity `1` to `gpt-4.1-mini` GlobalStandard capacity `10`. See [foundry_verification.md](foundry_verification.md) for the current evidence and the remaining IQ-grounding boundary.

Do not describe Foundry mode as live IQ-verified with citations until it has returned a real response through this adapter and the response is grounded in configured source material with source-level citation evidence.

The default wizard writes `.themis/foundry.local.json` with the Foundry project endpoint and agent ID. `themis-review --context-mode foundry` reads that file automatically. `THEMIS_FOUNDRY_PROJECT_ENDPOINT`, `THEMIS_FOUNDRY_AGENT_ID`, `THEMIS_FOUNDRY_MODEL_DEPLOYMENT` and `THEMIS_FOUNDRY_AGENT_NAME` are optional overrides for local testing or alternate projects.

CLI reviews write local history files under `.themis/runs/` for both mock and Foundry modes. Use `uv run themis-review --list-runs` to list them and `uv run themis-review --show-run .themis/runs/<run-log>.json` to print a saved report. These logs are local state and should not be committed.

## Setup assistant

The setup assistant checks the local prerequisites without creating cloud resources:
```powershell
uv run themis-setup check
uv run themis-setup --login check
```

It checks Azure CLI, Azure login, visible subscriptions, optional Foundry dependencies and the effective Foundry configuration from `.themis/foundry.local.json` plus any environment overrides.

The default command is an interactive setup wizard:
```powershell
uv run themis-setup
```

It prompts for subscription, resource group, region, Foundry resource name, project name, model deployment and agent name. It uses existing Foundry resources where present, creates missing resources when confirmed, derives the project endpoint and creates the Foundry agent only after confirmation.

It also has narrower interactive setup commands:
```powershell
uv run themis-setup azure-subscription-check
uv run themis-setup azure-subscription-check --apply
uv run themis-setup foundry-configuration
uv run themis-setup setup-agent
uv run themis-setup attach-sources
```
- `azure-subscription-check` prompts for subscription, resource group and region. Without `--apply`, it prints the planned Azure CLI commands. With `--apply`, it sets the subscription, registers `Microsoft.CognitiveServices` if requested and creates the resource group if requested.
- `foundry-configuration` stores an existing Foundry endpoint and agent ID in `.themis/foundry.local.json`.
- `setup-agent` prompts for project endpoint, model deployment and agent name. It asks for confirmation before creating the Foundry agent through the Azure AI Foundry SDK. Use the default wizard when you want resource/project/deployment creation handled automatically.
- `attach-sources` uses the saved Foundry configuration, uploads the sample context files, creates a vector store and updates the configured agent with file search.
- The local configuration file stores resource identifiers such as endpoint, agent ID, vector-store ID and uploaded file IDs. Do not put credentials in it. Environment variables override endpoint and agent settings when both are present.

If no subscription is visible, the assistant explains that an Azure subscription is required. This is not a software licence requirement. New users can review Microsoft's Azure account and free services pages:
```text
https://azure.microsoft.com/pricing/purchase-options/azure-account
https://azure.microsoft.com/pricing/free-services
```
