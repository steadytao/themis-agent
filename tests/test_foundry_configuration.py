import json
from pathlib import Path

from themis.foundry_configuration import (
    FoundryConfiguration,
    load_effective_foundry_configuration,
    load_foundry_configuration,
    render_environment_commands,
    save_foundry_configuration,
)


def test_foundry_configuration_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "foundry.local.json"
    config = FoundryConfiguration(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-123",
        model_deployment="gpt-4.1-mini",
        agent_name="themis-context-retriever",
        vector_store_id="vs-123",
        source_file_ids=("file-1", "file-2"),
    )

    save_foundry_configuration(config, path)

    assert json.loads(path.read_text(encoding="utf-8"))["agent_id"] == "agent-123"
    assert json.loads(path.read_text(encoding="utf-8"))["vector_store_id"] == "vs-123"
    assert load_foundry_configuration(path) == config


def test_effective_foundry_configuration_uses_local_file(tmp_path: Path) -> None:
    path = tmp_path / "foundry.local.json"
    config = FoundryConfiguration(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-123",
        model_deployment="gpt-4o",
        agent_name="themis-context-retriever",
    )
    save_foundry_configuration(config, path)

    assert load_effective_foundry_configuration(path) == config


def test_effective_foundry_configuration_prefers_environment_over_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "foundry.local.json"
    save_foundry_configuration(
        FoundryConfiguration(
            project_endpoint="https://file.services.ai.azure.com/api/projects/themis-agent",
            agent_id="agent-from-file",
            model_deployment="gpt-4o",
            agent_name="agent-from-file",
        ),
        path,
    )
    monkeypatch.setenv(
        "THEMIS_FOUNDRY_PROJECT_ENDPOINT",
        "https://env.services.ai.azure.com/api/projects/themis-agent",
    )
    monkeypatch.setenv("THEMIS_FOUNDRY_AGENT_ID", "agent-from-env")
    monkeypatch.setenv("THEMIS_FOUNDRY_MODEL_DEPLOYMENT", "env-model")
    monkeypatch.setenv("THEMIS_FOUNDRY_AGENT_NAME", "agent-from-env")

    config = load_effective_foundry_configuration(path)

    assert config == FoundryConfiguration(
        project_endpoint="https://env.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-from-env",
        model_deployment="env-model",
        agent_name="agent-from-env",
    )


def test_render_environment_commands() -> None:
    config = FoundryConfiguration(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-123",
        model_deployment="gpt-4.1-mini",
        agent_name="themis-context-retriever",
    )

    commands = render_environment_commands(config)

    assert "$env:THEMIS_FOUNDRY_PROJECT_ENDPOINT" in commands
    assert "$env:THEMIS_FOUNDRY_AGENT_ID" in commands
    assert "agent-123" in commands
