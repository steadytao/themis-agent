from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from themis.foundry_configuration import FoundryConfiguration
from themis.foundry_resources import DEFAULT_MODEL_DEPLOYMENT


DEFAULT_AGENT_NAME = "themis-context-retriever"
DEFAULT_AGENT_DESCRIPTION = (
    "Retrieves architecture, network policy and deployment runbook context for "
    "Themis infrastructure change reviews."
)
DEFAULT_SOURCE_MATERIAL_NAME = "themis-source-material"
DEFAULT_SOURCE_MATERIAL_PATHS = (
    Path("samples/context_architecture.md"),
    Path("samples/context_network_policy.md"),
    Path("samples/context_deployment_runbook.md"),
)
FileSearchFactory = Callable[[list[str]], Any]


@dataclass(frozen=True)
class SourceMaterialResult:
    vector_store_id: str
    file_ids: tuple[str, ...]
    source_paths: tuple[str, ...]


def build_agent_instructions() -> str:
    return "\n".join(
        [
            "You retrieve relevant context for infrastructure change review.",
            "Return concise excerpts from configured knowledge sources.",
            "Prefer architecture, network policy, deployment runbook, rollback, identity, monitoring and public exposure context.",
            "If no knowledge source is configured, say so plainly.",
            "Do not approve changes.",
            "Do not deploy infrastructure.",
            "Do not scan live systems.",
            "Do not provide exploit instructions.",
        ]
    )


def create_foundry_agent(
    *,
    project_endpoint: str,
    model_deployment: str,
    agent_name: str = DEFAULT_AGENT_NAME,
    client: Any | None = None,
    source_paths: Sequence[Path] | None = DEFAULT_SOURCE_MATERIAL_PATHS,
    file_search_factory: FileSearchFactory | None = None,
) -> FoundryConfiguration:
    if client is None:
        client = _build_project_client(project_endpoint)
    agent = client.agents.create_agent(
        model=model_deployment,
        name=agent_name,
        description=DEFAULT_AGENT_DESCRIPTION,
        instructions=build_agent_instructions(),
        temperature=0.0,
    )
    source_material = None
    if source_paths:
        source_material = attach_source_material(
            client=client,
            agent_id=agent.id,
            source_paths=source_paths,
            file_search_factory=file_search_factory,
        )
    return FoundryConfiguration(
        project_endpoint=project_endpoint,
        agent_id=agent.id,
        model_deployment=model_deployment,
        agent_name=agent_name,
        vector_store_id=source_material.vector_store_id if source_material else None,
        source_file_ids=source_material.file_ids if source_material else (),
    )


def attach_source_material(
    *,
    client: Any,
    agent_id: str,
    source_paths: Sequence[Path],
    file_search_factory: FileSearchFactory | None = None,
) -> SourceMaterialResult:
    paths = tuple(path for path in source_paths if path.exists())
    if not paths:
        raise ValueError("No source material files exist.")

    file_ids = []
    for path in paths:
        uploaded = _upload_agent_file(client, path)
        file_ids.append(uploaded.id)

    vector_store = client.agents.vector_stores.create_and_poll(
        file_ids=file_ids,
        name=DEFAULT_SOURCE_MATERIAL_NAME,
    )
    file_search = (
        file_search_factory([vector_store.id])
        if file_search_factory
        else _default_file_search([vector_store.id])
    )
    client.agents.update_agent(
        agent_id=agent_id,
        tools=_file_search_value(file_search, "definitions"),
        tool_resources=_file_search_value(file_search, "resources"),
    )
    return SourceMaterialResult(
        vector_store_id=vector_store.id,
        file_ids=tuple(file_ids),
        source_paths=tuple(str(path) for path in paths),
    )


def attach_source_material_to_configuration(
    configuration: FoundryConfiguration,
    *,
    client: Any | None = None,
    source_paths: Sequence[Path] = DEFAULT_SOURCE_MATERIAL_PATHS,
    file_search_factory: FileSearchFactory | None = None,
) -> FoundryConfiguration:
    if client is None:
        client = _build_project_client(configuration.project_endpoint)
    source_material = attach_source_material(
        client=client,
        agent_id=configuration.agent_id,
        source_paths=source_paths,
        file_search_factory=file_search_factory,
    )
    return FoundryConfiguration(
        project_endpoint=configuration.project_endpoint,
        agent_id=configuration.agent_id,
        model_deployment=configuration.model_deployment,
        agent_name=configuration.agent_name,
        vector_store_id=source_material.vector_store_id,
        source_file_ids=source_material.file_ids,
    )


def prompt_agent_setup() -> tuple[str, str, str]:
    endpoint = _prompt("Foundry project endpoint")
    model_deployment = _prompt("Model deployment name", DEFAULT_MODEL_DEPLOYMENT)
    agent_name = _prompt("Agent name", DEFAULT_AGENT_NAME)
    return endpoint, model_deployment, agent_name


def _build_project_client(project_endpoint: str):
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError("Run: uv sync --extra foundry") from exc
    return AIProjectClient(endpoint=project_endpoint, credential=DefaultAzureCredential())


def _upload_agent_file(client: Any, path: Path):
    purpose = _file_purpose_agents()
    files = client.agents.files
    if hasattr(files, "upload_and_poll"):
        return files.upload_and_poll(file_path=str(path), purpose=purpose)
    return files.upload(file_path=str(path), purpose=purpose)


def _file_purpose_agents():
    try:
        from azure.ai.agents.models import FilePurpose
    except ImportError:
        return "agents"
    return FilePurpose.AGENTS


def _default_file_search(vector_store_ids: list[str]):
    try:
        from azure.ai.agents.models import FileSearchTool
    except ImportError as exc:
        raise RuntimeError("Run: uv sync --extra foundry") from exc
    return FileSearchTool(vector_store_ids=vector_store_ids)


def _file_search_value(file_search: Any, name: str):
    if isinstance(file_search, dict):
        return file_search[name]
    return getattr(file_search, name)


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise ValueError(f"{label} is required.")
