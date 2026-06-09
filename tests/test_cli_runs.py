import json
import sys
from pathlib import Path

from themis import cli


PROPOSAL = """
# Public listener update

Service: admin portal
Environment: production

Expose the admin portal through a public Azure Application Gateway.
Allow source range 0.0.0.0/0 for initial testing.
Rollback will restore the previous listener.
"""


def test_cli_configures_stdout_for_unicode_citation_markers(monkeypatch) -> None:
    calls = []

    class FakeStdout:
        def reconfigure(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(sys, "stdout", FakeStdout())

    cli._configure_stdout()

    assert calls == [{"encoding": "utf-8", "errors": "replace"}]


def test_review_cli_writes_local_run_log(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    proposal = tmp_path / "change.md"
    proposal.write_text(PROPOSAL, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["themis-review", str(proposal)])

    cli.main()

    output = capsys.readouterr().out
    run_logs = list((tmp_path / ".themis" / "runs").glob("*.json"))
    assert len(run_logs) == 1
    data = json.loads(run_logs[0].read_text(encoding="utf-8"))
    assert data["proposal_path"] == str(proposal)
    assert data["context_mode"] == "mock"
    assert data["report"]["recommendation"] == data["recommendation"]
    assert data["markdown"].startswith("# Themis infrastructure change review")
    assert f"Saved review log: {Path('.themis/runs') / run_logs[0].name}" in output


def test_review_cli_run_log_does_not_persist_raw_secret_excerpt(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    proposal = tmp_path / "change.md"
    proposal.write_text(PROPOSAL + "\nAPI_KEY=super-secret-value\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["themis-review", str(proposal)])

    cli.main()

    capsys.readouterr()
    run_log = next((tmp_path / ".themis" / "runs").glob("*.json"))
    log_text = run_log.read_text(encoding="utf-8")
    data = json.loads(log_text)

    assert "super-secret-value" not in log_text
    assert "[REDACTED]" in log_text
    assert data["report"]["guardrail_violations"][0]["excerpt"] == "API_KEY=[REDACTED]"


def test_review_cli_lists_and_shows_local_run_logs(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    proposal = tmp_path / "change.md"
    proposal.write_text(PROPOSAL, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["themis-review", str(proposal)])
    cli.main()
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["themis-review", "--list-runs"])
    cli.main()
    list_output = capsys.readouterr().out

    run_log = next((tmp_path / ".themis" / "runs").glob("*.json"))
    assert run_log.name in list_output
    assert "DO NOT PROCEED YET" in list_output

    monkeypatch.setattr(sys, "argv", ["themis-review", "--show-run", str(run_log)])
    cli.main()
    show_output = capsys.readouterr().out

    assert show_output.startswith("# Themis infrastructure change review")
    assert "## Recommendation" in show_output
