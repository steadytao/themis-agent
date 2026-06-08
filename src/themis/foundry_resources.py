from __future__ import annotations

from datetime import UTC, datetime
import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]
ProgressReporter = Callable[[str], None]

DEFAULT_FOUNDRY_RESOURCE_NAME = "themis-agent-foundry"
DEFAULT_FOUNDRY_PROJECT_NAME = "themis-agent"
DEFAULT_MODEL_DEPLOYMENT = "gpt-4.1-mini"
DEFAULT_MODEL_VERSION = "2025-04-14"
DEFAULT_SKU_CAPACITY = "10"
DEFAULT_SKU_NAME = "GlobalStandard"
PREFERRED_MODEL_NAMES = ("gpt-4.1-mini", "gpt-5-mini", "o4-mini", "gpt-4o", "gpt-4o-mini")


@dataclass(frozen=True)
class FoundryProjectAnswers:
    resource_group: str
    region: str
    resource_name: str
    project_name: str
    model_deployment: str
    model_name: str
    model_version: str
    deploy_model: bool
    create_missing: bool
    model_sku_name: str = DEFAULT_SKU_NAME


@dataclass(frozen=True)
class FoundryResource:
    name: str
    custom_domain: str | None
    foundry_endpoint: str | None


@dataclass(frozen=True)
class FoundryModel:
    name: str
    version: str
    format: str
    lifecycle_status: str
    inference_deprecation: str | None
    chat_completion: bool
    sku_names: tuple[str, ...]


@dataclass(frozen=True)
class CognitiveServicesUsage:
    name: str
    current_value: float
    limit: float

    @property
    def available(self) -> float:
        return self.limit - self.current_value


@dataclass(frozen=True)
class FoundryModelChoice:
    model: FoundryModel
    sku_name: str


@dataclass(frozen=True)
class FoundryProjectSetupResult:
    project_endpoint: str
    model_deployment: str
    resource_name: str
    project_name: str
    created_resource: bool
    created_project: bool
    created_deployment: bool


def prompt_foundry_project_setup(
    *,
    default_resource_group: str,
    default_region: str,
    default_resource_name: str = DEFAULT_FOUNDRY_RESOURCE_NAME,
    default_model_name: str = DEFAULT_MODEL_DEPLOYMENT,
    default_model_version: str = DEFAULT_MODEL_VERSION,
    default_model_sku_name: str = DEFAULT_SKU_NAME,
) -> FoundryProjectAnswers:
    resource_group = _prompt("Resource group name", default_resource_group)
    region = _prompt("Azure region", default_region)
    resource_name = _prompt("Foundry resource name", default_resource_name)
    project_name = _prompt("Foundry project name", DEFAULT_FOUNDRY_PROJECT_NAME)
    create_missing = _confirm("Create missing Foundry resource and project automatically?", True)
    deploy_model = _confirm("Create the model deployment if missing?", True)
    model_deployment = _prompt("Model deployment name", default_model_name)
    model_name = _prompt(
        "Model name",
        model_deployment,
        validator=lambda value: reject_confirmation_value(value, label="Model name"),
    )
    model_version = _prompt("Model version", default_model_version)
    model_sku_name = _prompt(
        "Model SKU name",
        default_model_sku_name,
        validator=lambda value: reject_confirmation_value(value, label="Model SKU name"),
    )
    return FoundryProjectAnswers(
        resource_group=resource_group,
        region=region,
        resource_name=resource_name,
        project_name=project_name,
        model_deployment=model_deployment,
        model_name=model_name,
        model_version=model_version,
        deploy_model=deploy_model,
        create_missing=create_missing,
        model_sku_name=model_sku_name,
    )


def list_foundry_resources(
    az_path: str,
    resource_group: str,
    runner: CommandRunner | None = None,
) -> list[FoundryResource]:
    runner = runner or _run_command
    result = runner(
        [
            az_path,
            "cognitiveservices",
            "account",
            "list",
            "--resource-group",
            resource_group,
            "--output",
            "json",
        ]
    )
    if result.returncode != 0:
        return []
    accounts = json.loads(result.stdout or "[]")
    resources: list[FoundryResource] = []
    for account in accounts if isinstance(accounts, list) else []:
        if not isinstance(account, dict):
            continue
        properties = account.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        endpoints = properties.get("endpoints")
        if not isinstance(endpoints, dict):
            endpoints = {}
        name = account.get("name")
        if not isinstance(name, str) or not name:
            continue
        custom_domain = properties.get("customSubDomainName")
        foundry_endpoint = endpoints.get("AI Foundry API")
        resources.append(
            FoundryResource(
                name=name,
                custom_domain=custom_domain if isinstance(custom_domain, str) else None,
                foundry_endpoint=foundry_endpoint if isinstance(foundry_endpoint, str) else None,
            )
        )
    return resources


def preferred_foundry_resource_name(resources: list[FoundryResource]) -> str:
    for resource in resources:
        if resource.custom_domain and resource.foundry_endpoint:
            return resource.name
    for resource in resources:
        if resource.foundry_endpoint:
            return resource.name
    return DEFAULT_FOUNDRY_RESOURCE_NAME


def list_models(
    az_path: str,
    resource_group: str,
    resource_name: str,
    runner: CommandRunner | None = None,
) -> list[FoundryModel]:
    runner = runner or _run_command
    result = runner(
        [
            az_path,
            "cognitiveservices",
            "account",
            "list-models",
            "--name",
            resource_name,
            "--resource-group",
            resource_group,
            "--output",
            "json",
        ]
    )
    if result.returncode != 0:
        return []
    raw_models = json.loads(result.stdout or "[]")
    models: list[FoundryModel] = []
    for raw_model in raw_models if isinstance(raw_models, list) else []:
        if not isinstance(raw_model, dict):
            continue
        name = raw_model.get("name")
        version = raw_model.get("version")
        model_format = raw_model.get("format")
        if not all(isinstance(value, str) and value for value in (name, version, model_format)):
            continue
        capabilities = raw_model.get("capabilities")
        if not isinstance(capabilities, dict):
            capabilities = {}
        deprecation = raw_model.get("deprecation")
        if not isinstance(deprecation, dict):
            deprecation = {}
        skus = raw_model.get("skus")
        sku_names = tuple(
            sku.get("name")
            for sku in (skus if isinstance(skus, list) else [])
            if isinstance(sku, dict) and isinstance(sku.get("name"), str)
        )
        models.append(
            FoundryModel(
                name=name,
                version=version,
                format=model_format,
                lifecycle_status=(
                    raw_model.get("lifecycleStatus")
                    if isinstance(raw_model.get("lifecycleStatus"), str)
                    else ""
                ),
                inference_deprecation=(
                    deprecation.get("inference")
                    if isinstance(deprecation.get("inference"), str)
                    else None
                ),
                chat_completion=capabilities.get("chatCompletion") == "true",
                sku_names=sku_names,
            )
        )
    return models


def list_usages(
    az_path: str,
    region: str,
    runner: CommandRunner | None = None,
) -> list[CognitiveServicesUsage]:
    runner = runner or _run_command
    result = runner(
        [
            az_path,
            "cognitiveservices",
            "usage",
            "list",
            "--location",
            region,
            "--output",
            "json",
        ]
    )
    if result.returncode != 0:
        return []
    raw_usages = json.loads(result.stdout or "[]")
    usages: list[CognitiveServicesUsage] = []
    for raw_usage in raw_usages if isinstance(raw_usages, list) else []:
        if not isinstance(raw_usage, dict):
            continue
        raw_name = raw_usage.get("name")
        if not isinstance(raw_name, dict):
            continue
        name = raw_name.get("value")
        if not isinstance(name, str) or not name:
            continue
        current_value = _float_value(raw_usage.get("currentValue"))
        limit = _float_value(raw_usage.get("limit"))
        usages.append(
            CognitiveServicesUsage(
                name=name,
                current_value=current_value,
                limit=limit,
            )
        )
    return usages


def preferred_model(
    models: list[FoundryModel],
    *,
    now_iso: str | None = None,
) -> FoundryModel | None:
    choice = preferred_model_choice(models, now_iso=now_iso)
    return choice.model if choice else None


def preferred_model_choice(
    models: list[FoundryModel],
    *,
    usages: list[CognitiveServicesUsage] | None = None,
    now_iso: str | None = None,
) -> FoundryModelChoice | None:
    usage_by_name = {usage.name: usage for usage in usages or []}
    deployable = [
        (model, sku_name)
        for model in models
        for sku_name in _deployable_skus(model, usage_by_name, now_iso=now_iso)
    ]
    for preferred_name in PREFERRED_MODEL_NAMES:
        candidates = [
            (model, sku_name)
            for model, sku_name in deployable
            if model.name == preferred_name
        ]
        if candidates:
            model, sku_name = max(candidates, key=lambda choice: choice[0].version)
            return FoundryModelChoice(model=model, sku_name=sku_name)
    if not deployable:
        return None
    model, sku_name = min(deployable, key=lambda choice: _model_sort_key(choice[0]))
    return FoundryModelChoice(model=model, sku_name=sku_name)


def reject_confirmation_value(value: str, *, label: str) -> str | None:
    if value.strip().lower() in {"y", "yes", "n", "no"}:
        return f"{label} cannot be {value!r}."
    return None


def _is_deployable_chat_model(model: FoundryModel, *, now_iso: str | None) -> bool:
    if model.format != "OpenAI":
        return False
    if not model.chat_completion:
        return False
    if model.lifecycle_status == "Deprecated":
        return False
    if not any(sku in {"Standard", "GlobalStandard", "DataZoneStandard"} for sku in model.sku_names):
        return False
    if model.inference_deprecation is None:
        return True
    return _parse_azure_datetime(model.inference_deprecation) > _parse_azure_datetime(
        now_iso or datetime.now(UTC).isoformat()
    )


def _deployable_skus(
    model: FoundryModel,
    usage_by_name: dict[str, CognitiveServicesUsage],
    *,
    now_iso: str | None,
) -> tuple[str, ...]:
    if not _is_deployable_chat_model(model, now_iso=now_iso):
        return ()
    allowed_skus = [
        sku
        for sku in model.sku_names
        if sku in {"Standard", "GlobalStandard", "DataZoneStandard"}
    ]
    if not usage_by_name:
        return tuple(dict.fromkeys(allowed_skus))
    return tuple(
        dict.fromkeys(
            sku
            for sku in allowed_skus
            if _available_quota(model.name, sku, usage_by_name) >= float(DEFAULT_SKU_CAPACITY)
        )
    )


def _available_quota(
    model_name: str,
    sku_name: str,
    usage_by_name: dict[str, CognitiveServicesUsage],
) -> float:
    return max(
        (
            usage_by_name[quota_name].available
            for quota_name in _quota_names(model_name, sku_name)
            if quota_name in usage_by_name
        ),
        default=0.0,
    )


def _quota_names(model_name: str, sku_name: str) -> tuple[str, ...]:
    names = [model_name]
    if model_name.startswith("gpt-4.1"):
        names.append(model_name.replace("gpt-4.1", "gpt4.1", 1))
    return tuple(
        f"{provider}.{sku_name}.{name}"
        for name in dict.fromkeys(names)
        for provider in ("OpenAI", "AIServices")
    )


def _model_sort_key(model: FoundryModel) -> tuple[int, str, str]:
    try:
        preferred_index = PREFERRED_MODEL_NAMES.index(model.name)
    except ValueError:
        preferred_index = len(PREFERRED_MODEL_NAMES)
    return preferred_index, model.name, model.version


def _parse_azure_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _float_value(value: Any) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def ensure_foundry_project(
    answers: FoundryProjectAnswers,
    *,
    az_path: str,
    runner: CommandRunner | None = None,
    progress: ProgressReporter | None = None,
) -> FoundryProjectSetupResult:
    runner = runner or _run_command
    progress = progress or _ignore_progress
    created_resource = False
    created_project = False
    created_deployment = False

    progress(f"Checking Foundry resource {answers.resource_name}.")
    account = _run_json(_account_show_command(az_path, answers), runner)
    if account is None:
        if not answers.create_missing:
            raise RuntimeError(
                f"Foundry resource {answers.resource_name!r} was not found."
            )
        progress(
            f"Creating Foundry resource {answers.resource_name}. "
            "This can take several minutes."
        )
        _run_required(_account_create_command(az_path, answers), runner)
        progress(f"Configuring Foundry resource domain {answers.resource_name}.")
        _run_required(_account_update_domain_command(az_path, answers), runner)
        created_resource = True
        account = _run_json(_account_show_command(az_path, answers), runner) or {}
    elif _account_domain(account) is None:
        if not answers.create_missing:
            raise RuntimeError(
                f"Foundry resource {answers.resource_name!r} has no custom domain."
            )
        progress(f"Configuring Foundry resource domain {answers.resource_name}.")
        _run_required(_account_update_domain_command(az_path, answers), runner)
        account = _run_json(_account_show_command(az_path, answers), runner) or account

    progress(f"Checking Foundry project {answers.project_name}.")
    project = _run_json(_project_show_command(az_path, answers), runner)
    if project is None:
        if not answers.create_missing:
            raise RuntimeError(f"Foundry project {answers.project_name!r} was not found.")
        progress(f"Creating Foundry project {answers.project_name}.")
        _run_required(_project_create_command(az_path, answers), runner)
        created_project = True
        project = _run_json(_project_show_command(az_path, answers), runner)
        if project is None:
            raise RuntimeError("Foundry project was created but could not be loaded.")

    if answers.deploy_model:
        progress(f"Checking model deployment {answers.model_deployment}.")
        deployment = _run_json(_deployment_show_command(az_path, answers), runner)
        if deployment is None:
            if not answers.create_missing:
                raise RuntimeError(
                    f"Model deployment {answers.model_deployment!r} was not found."
                )
            progress(
                f"Creating model deployment {answers.model_deployment}. "
                "This can take several minutes."
            )
            _run_required(_deployment_create_command(az_path, answers), runner)
            created_deployment = True

    endpoint = extract_project_endpoint(project)
    if endpoint is None:
        endpoint = build_project_endpoint(
            resource_name=_account_domain(account) or answers.resource_name,
            project_name=answers.project_name,
        )

    return FoundryProjectSetupResult(
        project_endpoint=endpoint,
        model_deployment=answers.model_deployment,
        resource_name=answers.resource_name,
        project_name=answers.project_name,
        created_resource=created_resource,
        created_project=created_project,
        created_deployment=created_deployment,
    )


def extract_project_endpoint(project: dict[str, Any]) -> str | None:
    for value in _walk_values(project):
        if not isinstance(value, str):
            continue
        if "://" not in value:
            continue
        if "/api/projects/" in value and "services.ai.azure.com" in value:
            return value
    return None


def build_project_endpoint(*, resource_name: str, project_name: str) -> str:
    return f"https://{resource_name}.services.ai.azure.com/api/projects/{project_name}"


def _account_domain(account: dict[str, Any]) -> str | None:
    properties = account.get("properties")
    if not isinstance(properties, dict):
        return None
    custom_domain = properties.get("customSubDomainName")
    return custom_domain if isinstance(custom_domain, str) and custom_domain else None


def _account_show_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "show",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--output",
        "json",
    ]


def _account_create_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "create",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--kind",
        "AIServices",
        "--sku",
        "S0",
        "--location",
        answers.region,
        "--allow-project-management",
        "--yes",
        "--output",
        "json",
    ]


def _account_update_domain_command(
    az_path: str,
    answers: FoundryProjectAnswers,
) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "update",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--custom-domain",
        answers.resource_name,
        "--output",
        "json",
    ]


def _project_show_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "project",
        "show",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--project-name",
        answers.project_name,
        "--output",
        "json",
    ]


def _project_create_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "project",
        "create",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--project-name",
        answers.project_name,
        "--location",
        answers.region,
        "--output",
        "json",
    ]


def _deployment_show_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "deployment",
        "show",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--deployment-name",
        answers.model_deployment,
        "--output",
        "json",
    ]


def _deployment_create_command(az_path: str, answers: FoundryProjectAnswers) -> list[str]:
    return [
        az_path,
        "cognitiveservices",
        "account",
        "deployment",
        "create",
        "--name",
        answers.resource_name,
        "--resource-group",
        answers.resource_group,
        "--deployment-name",
        answers.model_deployment,
        "--model-name",
        answers.model_name,
        "--model-version",
        answers.model_version,
        "--model-format",
        "OpenAI",
        "--sku-capacity",
        DEFAULT_SKU_CAPACITY,
        "--sku-name",
        answers.model_sku_name,
        "--output",
        "json",
    ]


def _run_json(
    command: list[str],
    runner: CommandRunner,
) -> dict[str, Any] | None:
    result = runner(command)
    if result.returncode != 0:
        return None
    if not result.stdout.strip():
        return {}
    data = json.loads(result.stdout)
    return data if isinstance(data, dict) else {}


def _run_required(command: list[str], runner: CommandRunner) -> dict[str, Any]:
    result = runner(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(command)}")
    if not result.stdout.strip():
        return {}
    data = json.loads(result.stdout)
    return data if isinstance(data, dict) else {}


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, check=False, text=True)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr=str(exc))


def _walk_values(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value


def _ignore_progress(_: str) -> None:
    return


def _prompt(
    label: str,
    default: str | None = None,
    validator: Callable[[str], str | None] | None = None,
) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        error = validator(value) if validator else None
        if error:
            raise ValueError(error)
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
