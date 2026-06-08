from __future__ import annotations

import argparse
import importlib.util
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from themis.azure_subscription_check import (
    AzureSetupAnswers,
    find_azure_cli,
    list_subscriptions,
    plan_azure_subscription_setup,
    plan_required_azure_subscription_setup,
    prompt_azure_setup,
    render_commands,
    run_azure_setup_commands,
)
from themis.foundry_configuration import (
    DEFAULT_CONFIG_PATH,
    load_effective_foundry_configuration,
    load_foundry_configuration,
    prompt_foundry_configuration,
    render_environment_commands,
    save_foundry_configuration,
)
from themis.foundry_resources import (
    DEFAULT_MODEL_DEPLOYMENT,
    DEFAULT_MODEL_VERSION,
    DEFAULT_SKU_NAME,
    ensure_foundry_project,
    list_models,
    list_usages,
    list_foundry_resources,
    preferred_model_choice,
    preferred_foundry_resource_name,
    prompt_foundry_project_setup,
)
from themis.setup_agent import (
    DEFAULT_AGENT_NAME,
    attach_source_material_to_configuration,
    create_foundry_agent,
    prompt_agent_setup,
)

AZURE_FREE_ACCOUNT_URL = "https://azure.microsoft.com/pricing/purchase-options/azure-account"
AZURE_FREE_SERVICES_URL = "https://azure.microsoft.com/pricing/free-services"
FOUNDRY_CREATE_PROJECT_URL = "https://learn.microsoft.com/azure/ai-studio/how-to/create-projects"
AZURE_CLI_LOGIN_URL = "https://learn.microsoft.com/cli/azure/authenticate-azure-cli"


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def run_checks(runner: CommandRunner | None = None) -> list[CheckResult]:
    runner = runner or _run_command
    results: list[CheckResult] = []

    az_path = find_azure_cli()
    results.append(
        CheckResult(
            name="Azure CLI",
            ok=az_path is not None,
            detail=az_path or "Azure CLI was not found on PATH.",
        )
    )
    if az_path is None:
        return results

    try:
        subscriptions = list_subscriptions(az_path, runner=runner)
    except RuntimeError as exc:
        results.append(
            CheckResult(
                name="Azure login",
                ok=False,
                detail=str(exc) or "Run az login.",
            )
        )
        return results

    if not subscriptions:
        results.append(
            CheckResult(
                name="Azure subscription",
                ok=False,
                detail="No Azure subscriptions are visible to this account.",
            )
        )
    else:
        names = ", ".join(item.name or item.subscription_id for item in subscriptions)
        results.append(CheckResult(name="Azure subscription", ok=True, detail=names))

    results.append(
        CheckResult(
            name="Foundry optional dependencies",
            ok=_module_exists("azure.ai.projects") and _module_exists("azure.identity"),
            detail=(
                "Installed."
                if _module_exists("azure.ai.projects") and _module_exists("azure.identity")
                else "Run: uv sync --extra foundry"
            ),
        )
    )

    config = load_effective_foundry_configuration()
    endpoint = config.project_endpoint if config else None
    agent_id = config.agent_id if config else None
    results.append(
        CheckResult(
            name="Foundry project endpoint",
            ok=bool(endpoint),
            detail=endpoint or "Run themis-setup to create .themis/foundry.local.json.",
        )
    )
    results.append(
        CheckResult(
            name="Foundry agent ID",
            ok=bool(agent_id),
            detail=agent_id or "Run themis-setup to create .themis/foundry.local.json.",
        )
    )
    return results


def render_setup_status(results: list[CheckResult]) -> str:
    lines = [
        "Themis setup check",
        "==================",
        "",
        "Themis mock mode works without Azure. Foundry mode needs Azure CLI, a signed-in account,",
        "an Azure subscription, optional Foundry dependencies, a Foundry project endpoint and an agent ID.",
        "",
    ]
    for result in results:
        status = "OK" if result.ok else "Needs setup"
        lines.append(f"{result.name}: {status} - {result.detail}")

    if any(result.name == "Azure CLI" and not result.ok for result in results):
        lines.extend(
            [
                "",
                "Install Azure CLI",
                "-----------------",
                "",
                "Install Azure CLI, then rerun this command:",
                "",
                "winget install --id Microsoft.AzureCLI --source winget",
                "az version",
                "",
                f"Azure CLI login docs: {AZURE_CLI_LOGIN_URL}",
            ]
        )

    if any(result.name == "Azure login" and not result.ok for result in results):
        lines.extend(
            [
                "",
                "Sign in",
                "-------",
                "",
                "az login",
                "az account list --all",
            ]
        )

    if any(result.name == "Azure subscription" and not result.ok for result in results):
        lines.extend(
            [
                "",
                "Azure subscription",
                "------------------",
                "",
                "This is an Azure subscription requirement, not a software licence requirement.",
                "If this is a new hackathon account, create an Azure free account or pay-as-you-go subscription.",
                "Microsoft documents free-account credits and free service allowances, but you should still",
                "watch Cost Management and delete resources after the demo.",
                "",
                f"Create account: {AZURE_FREE_ACCOUNT_URL}",
                f"Free services: {AZURE_FREE_SERVICES_URL}",
            ]
        )

    if any(result.name.startswith("Foundry") and not result.ok for result in results):
        lines.extend(
            [
                "",
                "Foundry setup",
                "-------------",
                "",
                "uv sync --extra foundry",
                "az login",
                "uv run themis-setup",
                "uv run themis-review samples/change_risky.md --context-mode foundry",
                "",
                f"Create a Foundry project: {FOUNDRY_CREATE_PROJECT_URL}",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Themis Azure and Foundry setup.")
    parser.add_argument(
        "--login",
        action="store_true",
        help="Run az login before checking subscriptions.",
    )
    subparsers = parser.add_subparsers(dest="command")
    parser.set_defaults(command="setup")
    subparsers.add_parser("setup", help="Run the interactive setup wizard.")
    subparsers.add_parser("check", help="Check local Azure and Foundry setup.")

    azure_parser = subparsers.add_parser(
        "azure-subscription-check",
        help="Prompt for subscription, provider and resource-group setup.",
    )
    azure_parser.add_argument(
        "--apply",
        action="store_true",
        help="Run the Azure CLI setup commands after prompting.",
    )

    foundry_parser = subparsers.add_parser(
        "foundry-configuration",
        help="Prompt for existing Foundry endpoint and agent ID, then save local config.",
    )
    foundry_parser.add_argument(
        "--path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path for local Foundry configuration.",
    )

    agent_parser = subparsers.add_parser(
        "setup-agent",
        help="Prompt for Foundry details and create the Themis context agent.",
    )
    agent_parser.add_argument(
        "--yes",
        action="store_true",
        help="Create the Foundry agent without an extra confirmation prompt.",
    )
    agent_parser.add_argument(
        "--path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path for local Foundry configuration.",
    )

    attach_parser = subparsers.add_parser(
        "attach-sources",
        help="Attach sample source material to the configured Foundry agent.",
    )
    attach_parser.add_argument(
        "--path",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path for local Foundry configuration.",
    )

    return parser


def main() -> int:
    try:
        _main()
    except (EOFError, KeyboardInterrupt):
        print()
        print("Setup cancelled.")
        return 130
    except ValueError as exc:
        print(f"Setup failed: {exc}")
        return 2
    return 0


def _main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.login:
        az_path = find_azure_cli()
        if az_path is None:
            print("Azure CLI was not found on PATH.")
        else:
            subprocess.run([az_path, "login"], check=False)

    if args.command == "setup":
        run_setup_wizard()
        return

    if args.command == "check":
        print(render_setup_status(run_checks()))
        return

    if args.command == "azure-subscription-check":
        answers = prompt_azure_setup()
        planned = render_commands(plan_azure_subscription_setup(answers))
        commands = None
        if args.apply:
            az_path = find_azure_cli()
            if az_path is None:
                print("Azure CLI was not found on PATH.")
                return
            commands = run_azure_setup_commands(answers, az_path=az_path)
        print("Azure subscription setup")
        print("========================")
        print()
        if args.apply and commands:
            for result in commands:
                status = "OK" if result.returncode == 0 else "FAILED"
                print(f"- {status}: {' '.join(result.args if isinstance(result.args, list) else [str(result.args)])}")
                if result.stdout.strip():
                    print(result.stdout.strip())
                if result.stderr.strip():
                    print(result.stderr.strip())
        else:
            print("Planned commands. Rerun with --apply to execute them.")
            print()
            print(planned)
        return

    if args.command == "foundry-configuration":
        config = prompt_foundry_configuration()
        config_path = Path(args.path)
        save_foundry_configuration(config, config_path)
        print("Foundry configuration saved")
        print("===========================")
        print()
        print(f"Saved local config to {config_path}.")
        print()
        print("PowerShell environment commands:")
        print(render_environment_commands(config))
        return

    if args.command == "setup-agent":
        endpoint, model_deployment, agent_name = prompt_agent_setup()
        if not args.yes:
            answer = input("Create this Foundry agent now? [y/N]: ").strip().lower()
            if answer not in {"y", "yes"}:
                print("No agent created.")
                return
        config = create_foundry_agent(
            project_endpoint=endpoint,
            model_deployment=model_deployment,
            agent_name=agent_name,
        )
        config_path = Path(args.path)
        save_foundry_configuration(config, config_path)
        print("Foundry agent created")
        print("=====================")
        print()
        print(f"Agent name: {config.agent_name}")
        print(f"Agent ID: {config.agent_id}")
        print(f"Saved local config to {config_path}.")
        print()
        print("PowerShell environment commands:")
        print(render_environment_commands(config))
        return

    if args.command == "attach-sources":
        config_path = Path(args.path)
        config = load_foundry_configuration(config_path)
        if config is None:
            print(f"No Foundry configuration found at {config_path}.")
            print("Run: uv run themis-setup")
            return
        updated = attach_source_material_to_configuration(config)
        save_foundry_configuration(updated, config_path)
        print("Foundry source material attached")
        print("==============================")
        print()
        print(f"Agent name: {updated.agent_name}")
        print(f"Vector store ID: {updated.vector_store_id}")
        print(f"Source files: {len(updated.source_file_ids)}")
        print(f"Saved local config to {config_path}.")
        return


def run_setup_wizard() -> None:
    print("Themis setup wizard")
    print("===================")
    print("This wizard checks Azure, prepares the resource group, and can create the Foundry agent.")
    print()

    az_path = find_azure_cli()
    if az_path is None:
        print("Azure CLI was not found.")
        print("Install it with:")
        print("winget install --id Microsoft.AzureCLI --source winget")
        print(f"Docs: {AZURE_CLI_LOGIN_URL}")
        return
    print(f"Azure CLI: {az_path}")

    subscriptions = _load_subscriptions_or_prompt_login(az_path)
    if not subscriptions:
        print()
        print("No Azure subscriptions are visible to this account.")
        print("This is an Azure subscription requirement, not a software licence requirement.")
        print(f"Create account: {AZURE_FREE_ACCOUNT_URL}")
        print(f"Free services: {AZURE_FREE_SERVICES_URL}")
        return

    print()
    print("Visible Azure subscriptions:")
    for index, subscription in enumerate(subscriptions, start=1):
        label = subscription.name or subscription.subscription_id
        print(f"{index}. {label}")

    default_subscription = subscriptions[0].name or subscriptions[0].subscription_id
    answers = AzureSetupAnswers(
        subscription=_prompt("Subscription name or ID", default_subscription),
        resource_group=_prompt("Resource group name", "rg-themis-agent"),
        region=_prompt("Azure region", "eastus2"),
        register_provider=_confirm("Register Microsoft.CognitiveServices provider?", default=True),
        create_resource_group=_confirm("Create the resource group if needed?", default=True),
    )

    print()
    print("Azure setup commands:")
    planned_commands = plan_required_azure_subscription_setup(answers, az_path=az_path)
    print(render_commands(planned_commands))
    if _confirm("Apply these Azure setup commands now?", default=True):
        results = _run_planned_commands(planned_commands, az_path=az_path)
        for result in results:
            command = result.args if isinstance(result.args, list) else [str(result.args)]
            status = "OK" if result.returncode == 0 else "FAILED"
            print(f"{status}: {' '.join(command)}")
            if result.stdout.strip():
                print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip())
            if result.returncode != 0:
                print("Stopping setup because an Azure command failed.")
                return

    print()
    print("Foundry project setup")
    print("=====================")
    print("The wizard can use an existing Foundry resource/project or create missing pieces.")
    print(f"Foundry project docs: {FOUNDRY_CREATE_PROJECT_URL}")
    default_resource_name = preferred_foundry_resource_name(
        list_foundry_resources(az_path, answers.resource_group)
    )
    default_model = preferred_model_choice(
        list_models(az_path, answers.resource_group, default_resource_name),
        usages=list_usages(az_path, answers.region),
    )
    foundry_answers = prompt_foundry_project_setup(
        default_resource_group=answers.resource_group,
        default_region=answers.region,
        default_resource_name=default_resource_name,
        default_model_name=default_model.model.name if default_model else DEFAULT_MODEL_DEPLOYMENT,
        default_model_version=(
            default_model.model.version if default_model else DEFAULT_MODEL_VERSION
        ),
        default_model_sku_name=default_model.sku_name if default_model else DEFAULT_SKU_NAME,
    )
    if not _confirm("Apply Foundry resource and deployment setup now?", default=True):
        print("No Foundry resources changed.")
        return

    try:
        foundry_project = ensure_foundry_project(
            foundry_answers,
            az_path=az_path,
            progress=lambda message: print(f"- {message}", flush=True),
        )
    except RuntimeError as exc:
        print(f"Foundry setup failed: {exc}")
        return

    print()
    print("Foundry project ready.")
    print(f"Resource: {foundry_project.resource_name}")
    print(f"Project: {foundry_project.project_name}")
    print(f"Endpoint: {foundry_project.project_endpoint}")
    print(f"Model deployment: {foundry_project.model_deployment}")
    print(
        "Created: "
        f"resource={'yes' if foundry_project.created_resource else 'no'}, "
        f"project={'yes' if foundry_project.created_project else 'no'}, "
        f"deployment={'yes' if foundry_project.created_deployment else 'no'}"
    )

    if not (_module_exists("azure.ai.projects") and _module_exists("azure.identity")):
        print()
        print("Foundry SDK dependencies are missing.")
        print("Run: uv sync --extra foundry")
        return

    agent_name = _prompt("Agent name", DEFAULT_AGENT_NAME)
    if not _confirm("Create the Themis Foundry agent now?", default=True):
        print("No Foundry agent created.")
        return

    config = create_foundry_agent(
        project_endpoint=foundry_project.project_endpoint,
        model_deployment=foundry_project.model_deployment,
        agent_name=agent_name,
    )
    save_foundry_configuration(config, DEFAULT_CONFIG_PATH)
    print()
    print("Foundry agent created.")
    print(f"Agent name: {config.agent_name}")
    print(f"Agent ID: {config.agent_id}")
    if config.vector_store_id:
        print(f"Vector store ID: {config.vector_store_id}")
        print(f"Source files: {len(config.source_file_ids)}")
    print(f"Saved local config to {DEFAULT_CONFIG_PATH}.")
    print()
    print("Next command:")
    print("uv run themis-review samples/change_risky.md --context-mode foundry")


def _load_subscriptions_or_prompt_login(az_path: str):
    try:
        subscriptions = list_subscriptions(az_path)
    except RuntimeError:
        subscriptions = []

    if subscriptions:
        return subscriptions

    if _confirm("No subscriptions were loaded. Run az login now?", default=True):
        subprocess.run([az_path, "login"], check=False)
        try:
            return list_subscriptions(az_path)
        except RuntimeError:
            return []
    return []


def _run_planned_commands(
    commands: list[list[str]],
    *,
    az_path: str,
) -> list[subprocess.CompletedProcess[str]]:
    return [_run_command([az_path, *command[1:]]) for command in commands]


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


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, check=False, text=True)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr=str(exc))


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
