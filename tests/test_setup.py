import json
import subprocess
import sys

from themis import setup
from themis.setup import CheckResult, render_setup_status, run_checks


def test_setup_reports_missing_azure_cli(monkeypatch) -> None:
    monkeypatch.setattr(setup, "find_azure_cli", lambda: None)

    results = run_checks()

    assert results == [
        CheckResult(name="Azure CLI", ok=False, detail="Azure CLI was not found on PATH.")
    ]
    report = render_setup_status(results)
    assert "Install Azure CLI" in report
    assert "```" not in report
    assert "| Check |" not in report


def test_setup_reports_missing_subscription(monkeypatch) -> None:
    monkeypatch.setattr(setup, "find_azure_cli", lambda: "az")

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        assert command[:3] == ["az", "account", "list"]
        return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")

    results = run_checks(runner=runner)
    report = render_setup_status(results)

    assert any(result.name == "Azure subscription" and not result.ok for result in results)
    assert "not a software licence" in report
    assert setup.AZURE_FREE_ACCOUNT_URL in report


def test_setup_reports_subscription_names(monkeypatch) -> None:
    monkeypatch.setattr(setup, "find_azure_cli", lambda: "az")
    subscriptions = [{"name": "Azure subscription 1"}]

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(subscriptions), stderr="")

    results = run_checks(runner=runner)

    assert any(
        result.name == "Azure subscription"
        and result.ok
        and "Azure subscription 1" in result.detail
        for result in results
    )


def test_module_exists_treats_missing_parent_package_as_missing(monkeypatch) -> None:
    def missing_parent(name: str):
        raise ModuleNotFoundError("No module named 'azure'")

    monkeypatch.setattr(setup.importlib.util, "find_spec", missing_parent)

    assert setup._module_exists("azure.ai.projects") is False


def test_default_setup_command_is_wizard() -> None:
    parser = setup.build_parser()

    args = parser.parse_args([])

    assert args.command == "setup"


def test_attach_sources_subcommand_is_available() -> None:
    parser = setup.build_parser()

    args = parser.parse_args(["attach-sources"])

    assert args.command == "attach-sources"


def test_main_handles_keyboard_interrupt(monkeypatch, capsys) -> None:
    def interrupt() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(setup, "run_setup_wizard", interrupt)
    monkeypatch.setattr(sys, "argv", ["themis-setup"])

    exit_code = setup.main()

    assert exit_code == 130
    assert "Setup cancelled." in capsys.readouterr().out


def test_main_handles_eof_error(monkeypatch, capsys) -> None:
    def interrupt() -> None:
        raise EOFError

    monkeypatch.setattr(setup, "run_setup_wizard", interrupt)
    monkeypatch.setattr(sys, "argv", ["themis-setup"])

    exit_code = setup.main()

    assert exit_code == 130
    assert "Setup cancelled." in capsys.readouterr().out


def test_main_handles_prompt_validation_error(monkeypatch, capsys) -> None:
    def fail() -> None:
        raise ValueError("Model name cannot be 'n'.")

    monkeypatch.setattr(setup, "run_setup_wizard", fail)
    monkeypatch.setattr(sys, "argv", ["themis-setup"])

    exit_code = setup.main()

    assert exit_code == 2
    assert "Setup failed: Model name cannot be 'n'." in capsys.readouterr().out
