import subprocess

from themis.foundry_resources import (
    FoundryProjectAnswers,
    ensure_foundry_project,
    extract_project_endpoint,
    list_foundry_resources,
    list_models,
    list_usages,
    preferred_foundry_resource_name,
    preferred_model,
    preferred_model_choice,
    reject_confirmation_value,
)


def test_extract_project_endpoint_finds_nested_foundry_endpoint() -> None:
    endpoint = extract_project_endpoint(
        {
            "properties": {
                "connectionDetails": {
                    "projectEndpoint": "https://example.services.ai.azure.com/api/projects/themis-agent"
                }
            }
        }
    )

    assert endpoint == "https://example.services.ai.azure.com/api/projects/themis-agent"


def test_preferred_foundry_resource_name_uses_existing_domain_ready_resource() -> None:
    resources = list_foundry_resources(
        "az.cmd",
        "rg-themis-agent",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":"themis-agent-foundry","properties":{"customSubDomainName":null,'
                '"endpoints":{"AI Foundry API":"https://themis-agent-foundry.services.ai.azure.com/"}}},'
                '{"name":"themis-agent-resource","properties":{"customSubDomainName":"themis-agent-resource",'
                '"endpoints":{"AI Foundry API":"https://themis-agent-resource.services.ai.azure.com/"}}}'
                "]"
            ),
            stderr="",
        ),
    )

    assert preferred_foundry_resource_name(resources) == "themis-agent-resource"


def test_reject_confirmation_value_rejects_yes_no_as_model_name() -> None:
    assert reject_confirmation_value("n", label="Model name") == "Model name cannot be 'n'."
    assert reject_confirmation_value("yes", label="Model name") == "Model name cannot be 'yes'."
    assert reject_confirmation_value("gpt-4.1-mini", label="Model name") is None


def test_preferred_model_uses_current_preferred_model_from_catalogue() -> None:
    models = list_models(
        "az.cmd",
        "rg-themis-agent",
        "themis-agent-resource",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":"gpt-4o-mini","version":"2024-07-18","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-03-31T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"}]},'
                '{"name":"gpt-4.1-mini","version":"2025-04-14","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-14T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"}]}'
                "]"
            ),
            stderr="",
        ),
    )

    model = preferred_model(models, now_iso="2026-06-08T00:00:00Z")

    assert model is not None
    assert model.name == "gpt-4.1-mini"
    assert model.version == "2025-04-14"


def test_preferred_model_choice_uses_quota_backed_sku() -> None:
    models = list_models(
        "az.cmd",
        "rg-themis-agent",
        "themis-agent-resource",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":"gpt-4.1-mini","version":"2025-04-14","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-14T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"},{"name":"GlobalStandard"}]},'
                '{"name":"gpt-4o","version":"2024-08-06","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-01T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"}]},'
                '{"name":"gpt-4o","version":"2024-11-20","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-01T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"}]}'
                "]"
            ),
            stderr="",
        ),
    )
    usages = list_usages(
        "az.cmd",
        "eastus2",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":{"value":"OpenAI.Standard.gpt4.1-mini"},"currentValue":0.0,"limit":0.0},'
                '{"name":{"value":"OpenAI.GlobalStandard.gpt4.1-mini"},"currentValue":0.0,"limit":200.0},'
                '{"name":{"value":"OpenAI.Standard.gpt-4o"},"currentValue":0.0,"limit":50.0}'
                "]"
            ),
            stderr="",
        ),
    )

    choice = preferred_model_choice(models, usages=usages, now_iso="2026-06-08T00:00:00Z")

    assert choice is not None
    assert choice.model.name == "gpt-4.1-mini"
    assert choice.model.version == "2025-04-14"
    assert choice.sku_name == "GlobalStandard"


def test_preferred_model_choice_prefers_current_mini_model_with_demo_capacity() -> None:
    models = list_models(
        "az.cmd",
        "rg-themis-agent",
        "themis-agent-resource",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":"gpt-4.1-mini","version":"2025-04-14","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-14T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"},{"name":"GlobalStandard"}]},'
                '{"name":"gpt-4o","version":"2024-11-20","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-01T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"}]}'
                "]"
            ),
            stderr="",
        ),
    )
    usages = list_usages(
        "az.cmd",
        "eastus2",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":{"value":"OpenAI.GlobalStandard.gpt4.1-mini"},"currentValue":0.0,"limit":200.0},'
                '{"name":{"value":"OpenAI.Standard.gpt-4o"},"currentValue":1.0,"limit":50.0}'
                "]"
            ),
            stderr="",
        ),
    )

    choice = preferred_model_choice(models, usages=usages, now_iso="2026-06-08T00:00:00Z")

    assert choice is not None
    assert choice.model.name == "gpt-4.1-mini"
    assert choice.model.version == "2025-04-14"
    assert choice.sku_name == "GlobalStandard"


def test_preferred_model_choice_can_use_normalised_global_standard_quota() -> None:
    models = list_models(
        "az.cmd",
        "rg-themis-agent",
        "themis-agent-resource",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":"gpt-4.1-mini","version":"2025-04-14","format":"OpenAI",'
                '"lifecycleStatus":"GenerallyAvailable","deprecation":{"inference":"2026-10-14T00:00:00Z"},'
                '"capabilities":{"chatCompletion":"true"},"skus":[{"name":"Standard"},{"name":"GlobalStandard"}]}'
                "]"
            ),
            stderr="",
        ),
    )
    usages = list_usages(
        "az.cmd",
        "eastus2",
        runner=lambda command: subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "["
                '{"name":{"value":"OpenAI.Standard.gpt4.1-mini"},"currentValue":0.0,"limit":0.0},'
                '{"name":{"value":"OpenAI.GlobalStandard.gpt4.1-mini"},"currentValue":0.0,"limit":200.0}'
                "]"
            ),
            stderr="",
        ),
    )

    choice = preferred_model_choice(models, usages=usages, now_iso="2026-06-08T00:00:00Z")

    assert choice is not None
    assert choice.model.name == "gpt-4.1-mini"
    assert choice.sku_name == "GlobalStandard"


def test_ensure_foundry_project_creates_missing_resources() -> None:
    answers = FoundryProjectAnswers(
        resource_group="rg-themis-agent",
        region="eastus2",
        resource_name="themis-foundry",
        project_name="themis-agent",
        model_deployment="gpt-4.1-mini",
        model_name="gpt-4.1-mini",
        model_version="2025-04-14",
        deploy_model=True,
        create_missing=True,
        model_sku_name="GlobalStandard",
    )
    seen_commands: list[list[str]] = []
    project_show_calls = 0

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        nonlocal project_show_calls
        seen_commands.append(command)
        if command[1:4] == ["cognitiveservices", "account", "show"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command[1:4] == ["cognitiveservices", "account", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:4] == ["cognitiveservices", "account", "update"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "show"]:
            project_show_calls += 1
            if project_show_calls == 1:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "deployment", "show"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command[1:5] == ["cognitiveservices", "account", "deployment", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    result = ensure_foundry_project(answers, az_path="az.cmd", runner=runner)

    assert result.project_endpoint == "https://themis-foundry.services.ai.azure.com/api/projects/themis-agent"
    assert result.created_resource is True
    assert result.created_project is True
    assert result.created_deployment is True
    assert [
        "az.cmd",
        "cognitiveservices",
        "account",
        "create",
        "--name",
        "themis-foundry",
        "--resource-group",
        "rg-themis-agent",
        "--kind",
        "AIServices",
        "--sku",
        "S0",
        "--location",
        "eastus2",
        "--allow-project-management",
        "--yes",
        "--output",
        "json",
    ] in seen_commands
    assert [
        "az.cmd",
        "cognitiveservices",
        "account",
        "deployment",
        "create",
        "--name",
        "themis-foundry",
        "--resource-group",
        "rg-themis-agent",
        "--deployment-name",
        "gpt-4.1-mini",
        "--model-name",
        "gpt-4.1-mini",
        "--model-version",
        "2025-04-14",
        "--model-format",
        "OpenAI",
        "--sku-capacity",
        "10",
        "--sku-name",
        "GlobalStandard",
        "--output",
        "json",
    ] in seen_commands


def test_ensure_foundry_project_reports_progress_before_long_operations() -> None:
    answers = FoundryProjectAnswers(
        resource_group="rg-themis-agent",
        region="eastus2",
        resource_name="themis-foundry",
        project_name="themis-agent",
        model_deployment="gpt-4.1-mini",
        model_name="gpt-4.1-mini",
        model_version="2025-04-14",
        deploy_model=True,
        create_missing=True,
    )
    events: list[str] = []
    project_show_calls = 0

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        nonlocal project_show_calls
        if command[1:4] == ["cognitiveservices", "account", "show"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command[1:4] == ["cognitiveservices", "account", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:4] == ["cognitiveservices", "account", "update"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "show"]:
            project_show_calls += 1
            if project_show_calls == 1:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "deployment", "show"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command[1:5] == ["cognitiveservices", "account", "deployment", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    ensure_foundry_project(
        answers,
        az_path="az.cmd",
        runner=runner,
        progress=events.append,
    )

    assert events == [
        "Checking Foundry resource themis-foundry.",
        "Creating Foundry resource themis-foundry. This can take several minutes.",
        "Configuring Foundry resource domain themis-foundry.",
        "Checking Foundry project themis-agent.",
        "Creating Foundry project themis-agent.",
        "Checking model deployment gpt-4.1-mini.",
        "Creating model deployment gpt-4.1-mini. This can take several minutes.",
    ]


def test_ensure_foundry_project_configures_existing_resource_domain_before_project_create() -> None:
    answers = FoundryProjectAnswers(
        resource_group="rg-themis-agent",
        region="eastus2",
        resource_name="themis-foundry",
        project_name="themis-agent",
        model_deployment="gpt-4.1-mini",
        model_name="gpt-4.1-mini",
        model_version="2025-04-14",
        deploy_model=False,
        create_missing=True,
    )
    seen_commands: list[list[str]] = []
    project_show_calls = 0

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        nonlocal project_show_calls
        seen_commands.append(command)
        if command[1:4] == ["cognitiveservices", "account", "show"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"properties":{"customSubDomainName":null}}',
                stderr="",
            )
        if command[1:4] == ["cognitiveservices", "account", "update"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "show"]:
            project_show_calls += 1
            if project_show_calls == 1:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        if command[1:5] == ["cognitiveservices", "account", "project", "create"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    ensure_foundry_project(answers, az_path="az.cmd", runner=runner)

    update_index = seen_commands.index(
        [
            "az.cmd",
            "cognitiveservices",
            "account",
            "update",
            "--name",
            "themis-foundry",
            "--resource-group",
            "rg-themis-agent",
            "--custom-domain",
            "themis-foundry",
            "--output",
            "json",
        ]
    )
    project_create_index = seen_commands.index(
        [
            "az.cmd",
            "cognitiveservices",
            "account",
            "project",
            "create",
            "--name",
            "themis-foundry",
            "--resource-group",
            "rg-themis-agent",
            "--project-name",
            "themis-agent",
            "--location",
            "eastus2",
            "--output",
            "json",
        ]
    )
    assert update_index < project_create_index


def test_ensure_foundry_project_uses_existing_resources() -> None:
    answers = FoundryProjectAnswers(
        resource_group="rg-themis-agent",
        region="eastus2",
        resource_name="themis-foundry",
        project_name="themis-agent",
        model_deployment="gpt-4.1-mini",
        model_name="gpt-4.1-mini",
        model_version="2025-04-14",
        deploy_model=True,
        create_missing=True,
    )
    seen_commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        seen_commands.append(command)
        if command[1:4] == ["cognitiveservices", "account", "show"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"properties":{"customSubDomainName":"themis-foundry"}}',
                stderr="",
            )
        if command[1:5] == ["cognitiveservices", "account", "project", "show"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"properties":{"endpoint":"https://existing.services.ai.azure.com/api/projects/themis-agent"}}',
                stderr="",
            )
        if command[1:5] == ["cognitiveservices", "account", "deployment", "show"]:
            return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    result = ensure_foundry_project(answers, az_path="az.cmd", runner=runner)

    assert result.project_endpoint == "https://existing.services.ai.azure.com/api/projects/themis-agent"
    assert result.created_resource is False
    assert result.created_project is False
    assert result.created_deployment is False
    assert not any("create" in command for command in seen_commands)
