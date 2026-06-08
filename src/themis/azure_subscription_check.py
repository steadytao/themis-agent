from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class AzureSubscription:
    name: str
    subscription_id: str


@dataclass(frozen=True)
class AzureSetupAnswers:
    subscription: str
    resource_group: str
    region: str
    create_resource_group: bool
    register_provider: bool


def find_azure_cli() -> str | None:
    return shutil.which("az") or shutil.which("az.cmd")


def list_subscriptions(
    az_path: str,
    runner: CommandRunner | None = None,
) -> list[AzureSubscription]:
    runner = runner or _run_command
    result = runner([az_path, "account", "list", "--all", "--output", "json"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Azure CLI account list failed.")
    return [
        AzureSubscription(name=item.get("name", ""), subscription_id=item.get("id", ""))
        for item in json.loads(result.stdout or "[]")
    ]


def plan_azure_subscription_setup(
    answers: AzureSetupAnswers,
    az_command: str = "az",
) -> list[list[str]]:
    commands = [[az_command, "account", "set", "--subscription", answers.subscription]]
    if answers.register_provider:
        commands.append(
            [
                az_command,
                "provider",
                "register",
                "--namespace",
                "Microsoft.CognitiveServices",
            ]
        )
    if answers.create_resource_group:
        commands.append(
            [
                az_command,
                "group",
                "create",
                "--name",
                answers.resource_group,
                "--location",
                answers.region,
            ]
        )
    return commands


def plan_required_azure_subscription_setup(
    answers: AzureSetupAnswers,
    *,
    az_path: str,
    display_command: str = "az",
    runner: CommandRunner | None = None,
) -> list[list[str]]:
    runner = runner or _run_command
    commands = [[display_command, "account", "set", "--subscription", answers.subscription]]
    if answers.register_provider and not _provider_registered(az_path, runner):
        commands.append(
            [
                display_command,
                "provider",
                "register",
                "--namespace",
                "Microsoft.CognitiveServices",
            ]
        )
    if answers.create_resource_group and not _resource_group_exists(
        az_path,
        answers.resource_group,
        runner,
    ):
        commands.append(
            [
                display_command,
                "group",
                "create",
                "--name",
                answers.resource_group,
                "--location",
                answers.region,
            ]
        )
    return commands


def prompt_azure_setup() -> AzureSetupAnswers:
    subscription = _prompt("Subscription name or ID")
    resource_group = _prompt("Resource group name", "rg-themis-agent")
    region = _prompt("Azure region", "eastus2")
    register_provider = _confirm("Register Microsoft.CognitiveServices provider?", default=True)
    create_resource_group = _confirm(f"Create resource group {resource_group} if needed?", default=True)
    return AzureSetupAnswers(
        subscription=subscription,
        resource_group=resource_group,
        region=region,
        create_resource_group=create_resource_group,
        register_provider=register_provider,
    )


def run_azure_setup_commands(
    answers: AzureSetupAnswers,
    runner: CommandRunner | None = None,
    az_path: str | None = None,
) -> list[subprocess.CompletedProcess[str]]:
    runner = runner or _run_command
    az_command = az_path or find_azure_cli()
    if az_command is None:
        raise RuntimeError("Azure CLI was not found on PATH.")
    return [
        runner(command)
        for command in plan_azure_subscription_setup(answers, az_command=az_command)
    ]


def render_commands(commands: list[list[str]]) -> str:
    return "\n".join(_quote_command(command) for command in commands)


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, check=False, text=True)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr=str(exc))


def _provider_registered(az_path: str, runner: CommandRunner) -> bool:
    result = runner(
        [
            az_path,
            "provider",
            "show",
            "--namespace",
            "Microsoft.CognitiveServices",
            "--query",
            "registrationState",
            "--output",
            "tsv",
        ]
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "registered"


def _resource_group_exists(
    az_path: str,
    resource_group: str,
    runner: CommandRunner,
) -> bool:
    result = runner([az_path, "group", "exists", "--name", resource_group, "--output", "tsv"])
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise ValueError(f"{label} is required.")


def _confirm(label: str, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes"}


def _quote_command(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)
