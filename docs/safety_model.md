# Safety model

Themis is intentionally read-only.

It does not:
- deploy infrastructure
- scan live systems
- require cloud credentials in mock mode
- claim a change is safe
- replace human approval

Themis blocks or redacts apparent secrets, private keys, tokens and requests to deploy, exploit, bypass approval, suppress logging or hide risk.

Every report includes a human approval reminder, verification steps and rollback questions.

# Blocking guardrails

The input guardrail checks for apparent credential material and mutation-oriented requests before the final report is produced. Current blocking or redaction targets include:
- API keys, passwords, tokens and private keys
- requests to deploy or mutate infrastructure
- requests to scan live systems
- exploit-oriented requests
- requests to bypass approval
- requests to suppress logging
- requests to hide risk

Guardrail findings appear in the structured report as `GuardrailViolation` entries. The recommendation is reduced to `DO NOT PROCEED YET` when a violation is present.

# Reasoning guardrails

The report model requires a human-review note. The pipeline also keeps facts and assumptions in separate fields, reduces confidence when risks or evidence gaps are present, and always includes verification steps plus rollback questions.

The confidence score is not a safety score. It is a review-confidence signal based on available evidence, risk severity, unresolved gaps and guardrail findings.

# Output boundary

Themis should not produce destructive commands, live exploit instructions, credential material or claims that a change is safe. It is a review assistant for human approval. It is not an automated approver and should not be integrated into deployment gates without a separate threat model.

# Local state

CLI review history is stored under `.themis/runs/`. Foundry setup stores non-secret endpoint and agent identifiers under `.themis/foundry.local.json`. The `.themis/` directory is ignored by Git and should remain local.

Run logs redact guardrail excerpts before writing structured report data. They should still be treated as local review history because proposal text, risk summaries and retrieved context may contain sensitive operational detail.

# Setup boundary

The review pipeline is read-only. The setup assistant is an environment preparation tool and can create Azure or Foundry resources after confirmation. Use `uv run themis-setup check` when a diagnostic-only path is needed.
