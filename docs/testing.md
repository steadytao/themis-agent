# Testing

Themis tests should prove the review pipeline is deterministic in mock mode, safe at its boundaries and clear about its current limits.

# Current checks

Use:
```powershell
uv run pytest -q
uv run python -m compileall -q src app.py
& C:\Environment\docs-check.ps1 -Path README.md, SECURITY.md, docs
git -c core.autocrlf=false diff --check
```

The repository also supports a CLI smoke test:
```powershell
uv run themis-review samples/change_risky.md
uv run themis-review --list-runs
```

Run the Foundry smoke test only when local `.themis` configuration and quota are available:
```powershell
uv run themis-setup attach-sources
uv run themis-review samples/change_risky.md --context-mode foundry
```

The current local Foundry smoke uses `gpt-4.1-mini` on `GlobalStandard` capacity `10`. A one-capacity `gpt-4o` Standard deployment can hit Azure request-rate limits before the review completes.

# Required coverage

Behaviour changes should include tests for:
- risky changes producing `REVIEW REQUIRED` or `DO NOT PROCEED YET`
- incomplete changes producing `INSUFFICIENT EVIDENCE`
- safe changes still including verification steps
- apparent API keys or private keys being blocked or redacted
- requests to deploy, exploit, bypass approval, suppress logging or hide risk being blocked
- missing rollback evidence reducing confidence
- overbroad public exposure producing high-severity risk
- reports including rollback questions
- reports including human-review notes
- mock retrieval remaining deterministic
- Foundry mode failing clearly when configuration is missing
- local run logs being saved, listed and shown without re-running the review

# Local verification

Before relying on a local build, run:
```powershell
uv run pytest -q
uv run python -m compileall -q src app.py
uv run themis-review samples/change_safe.md
uv run themis-review samples/change_risky.md
uv run themis-review samples/change_incomplete.md
& C:\Environment\docs-check.ps1 -Path README.md, SECURITY.md, docs
git -c core.autocrlf=false diff --check
```

If Foundry mode will be shown or described as live, also run:
```powershell
uv sync --extra foundry
uv run themis-setup check
uv run themis-setup attach-sources
uv run themis-review samples/change_risky.md --context-mode foundry
```

Do not describe Foundry mode as live IQ-verified with citations if that final command has not passed against configured source material in the current environment with source-level citation evidence.
