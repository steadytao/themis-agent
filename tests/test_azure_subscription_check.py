import json
import subprocess

from themis.azure_subscription_check import (
    AzureSetupAnswers,
    plan_azure_subscription_setup,
    plan_required_azure_subscription_setup,
    run_azure_setup_commands,
)


def test_plan_azure_subscription_setup_creates_group_commands() -> None:
    answers = AzureSetupAnswers(
        subscription="Azure subscription 1",
        resource_group="rg-themis-agent",
        region="eastus2",
        create_resource_group=True,
        register_provider=True,
    )

    commands = plan_azure_subscription_setup(answers)

    assert ["az", "account", "set", "--subscription", "Azure subscription 1"] in commands
    assert ["az", "provider", "register", "--namespace", "Microsoft.CognitiveServices"] in commands
    assert ["az", "group", "create", "--name", "rg-themis-agent", "--location", "eastus2"] in commands


def test_plan_azure_subscription_setup_can_skip_mutation_commands() -> None:
    answers = AzureSetupAnswers(
        subscription="Azure subscription 1",
        resource_group="rg-themis-agent",
        region="eastus2",
        create_resource_group=False,
        register_provider=False,
    )

    commands = plan_azure_subscription_setup(answers)

    assert commands == [["az", "account", "set", "--subscription", "Azure subscription 1"]]


def test_list_subscriptions_uses_runner() -> None:
    from themis.azure_subscription_check import list_subscriptions

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps([{"name": "Azure subscription 1", "id": "sub-1"}]),
            stderr="",
        )

    subscriptions = list_subscriptions("az", runner=runner)

    assert subscriptions[0].name == "Azure subscription 1"
    assert subscriptions[0].subscription_id == "sub-1"


def test_run_azure_setup_commands_uses_resolved_azure_cli_path() -> None:
    answers = AzureSetupAnswers(
        subscription="Azure subscription 1",
        resource_group="rg-themis-agent",
        region="eastus2",
        create_resource_group=False,
        register_provider=True,
    )
    seen_commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        seen_commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    results = run_azure_setup_commands(
        answers,
        runner=runner,
        az_path=r"C:\Environment\tools\bin\az.cmd",
    )

    assert [result.returncode for result in results] == [0, 0]
    assert seen_commands == [
        [
            r"C:\Environment\tools\bin\az.cmd",
            "account",
            "set",
            "--subscription",
            "Azure subscription 1",
        ],
        [
            r"C:\Environment\tools\bin\az.cmd",
            "provider",
            "register",
            "--namespace",
            "Microsoft.CognitiveServices",
        ],
    ]


def test_plan_required_azure_subscription_setup_skips_existing_provider_and_group() -> None:
    answers = AzureSetupAnswers(
        subscription="Azure subscription 1",
        resource_group="rg-themis-agent",
        region="eastus2",
        create_resource_group=True,
        register_provider=True,
    )

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[1:3] == ["provider", "show"]:
            return subprocess.CompletedProcess(command, 0, stdout="Registered\n", stderr="")
        if command[1:3] == ["group", "exists"]:
            return subprocess.CompletedProcess(command, 0, stdout="true\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    commands = plan_required_azure_subscription_setup(
        answers,
        az_path="az.cmd",
        display_command="az",
        runner=runner,
    )

    assert commands == [["az", "account", "set", "--subscription", "Azure subscription 1"]]


def test_plan_required_azure_subscription_setup_keeps_missing_provider_and_group() -> None:
    answers = AzureSetupAnswers(
        subscription="Azure subscription 1",
        resource_group="rg-themis-agent",
        region="eastus2",
        create_resource_group=True,
        register_provider=True,
    )

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[1:3] == ["provider", "show"]:
            return subprocess.CompletedProcess(command, 0, stdout="NotRegistered\n", stderr="")
        if command[1:3] == ["group", "exists"]:
            return subprocess.CompletedProcess(command, 0, stdout="false\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    commands = plan_required_azure_subscription_setup(
        answers,
        az_path="az.cmd",
        display_command="az",
        runner=runner,
    )

    assert commands == [
        ["az", "account", "set", "--subscription", "Azure subscription 1"],
        ["az", "provider", "register", "--namespace", "Microsoft.CognitiveServices"],
        ["az", "group", "create", "--name", "rg-themis-agent", "--location", "eastus2"],
    ]
