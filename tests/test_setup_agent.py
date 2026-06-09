from dataclasses import dataclass
from pathlib import Path

from themis.foundry_configuration import FoundryConfiguration
from themis.setup_agent import build_agent_instructions, create_foundry_agent


@dataclass
class FakeAgent:
    id: str
    name: str


class FakeAgentsClient:
    def __init__(self) -> None:
        self.created = []
        self.updated = []
        self.files = FakeFilesClient()
        self.vector_stores = FakeVectorStoresClient()

    def create_agent(self, **kwargs):
        self.created.append(kwargs)
        return FakeAgent(id="agent-123", name=kwargs["name"])

    def update_agent(self, **kwargs):
        self.updated.append(kwargs)
        return FakeAgent(id=kwargs["agent_id"], name="themis-context-retriever")


@dataclass
class FakeUploadedFile:
    id: str


class FakeFilesClient:
    def __init__(self) -> None:
        self.uploaded = []

    def upload(self, **kwargs):
        self.uploaded.append(kwargs)
        return FakeUploadedFile(id=f"file-{len(self.uploaded)}")


@dataclass
class FakeVectorStore:
    id: str


class FakeVectorStoresClient:
    def __init__(self) -> None:
        self.created = []

    def create_and_poll(self, **kwargs):
        self.created.append(kwargs)
        return FakeVectorStore(id="vs-123")


class FakeProjectClient:
    def __init__(self) -> None:
        self.agents = FakeAgentsClient()


def test_build_agent_instructions_keep_read_only_boundary() -> None:
    instructions = build_agent_instructions()

    assert "Do not approve changes" in instructions
    assert "Do not deploy infrastructure" in instructions
    assert "architecture" in instructions.lower()
    assert "file search source material" in instructions
    assert "Cite the source file" in instructions


def test_create_foundry_agent_returns_configuration() -> None:
    client = FakeProjectClient()

    config = create_foundry_agent(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        model_deployment="gpt-4.1-mini",
        agent_name="themis-context-retriever",
        client=client,
        source_paths=(),
    )

    assert config == FoundryConfiguration(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-123",
        model_deployment="gpt-4.1-mini",
        agent_name="themis-context-retriever",
    )
    assert client.agents.created[0]["model"] == "gpt-4.1-mini"
    assert client.agents.created[0]["name"] == "themis-context-retriever"


def test_attach_source_material_uploads_sources_and_updates_agent(tmp_path: Path) -> None:
    from themis.setup_agent import SourceMaterialResult, attach_source_material

    first = tmp_path / "context_architecture.md"
    second = tmp_path / "context_network_policy.md"
    first.write_text("# Architecture\n\nInternal admin services stay private.\n", encoding="utf-8")
    second.write_text("# Network policy\n\nPublic exposure needs explicit ranges.\n", encoding="utf-8")
    client = FakeProjectClient()

    result = attach_source_material(
        client=client,
        agent_id="agent-123",
        source_paths=(first, second),
        file_search_factory=lambda vector_store_ids: {
            "definitions": [{"type": "file_search"}],
            "resources": {"file_search": {"vector_store_ids": vector_store_ids}},
        },
    )

    assert result == SourceMaterialResult(
        vector_store_id="vs-123",
        file_ids=("file-1", "file-2"),
        source_paths=(str(first), str(second)),
    )
    assert [item["file_path"] for item in client.agents.files.uploaded] == [str(first), str(second)]
    assert client.agents.vector_stores.created == [
        {"file_ids": ["file-1", "file-2"], "name": "themis-source-material"}
    ]
    assert client.agents.updated == [
        {
            "agent_id": "agent-123",
            "tools": [{"type": "file_search"}],
            "tool_resources": {"file_search": {"vector_store_ids": ["vs-123"]}},
        }
    ]


def test_create_foundry_agent_records_attached_source_material(tmp_path: Path) -> None:
    source = tmp_path / "context_deployment_runbook.md"
    source.write_text("# Runbook\n\nRollback first.\n", encoding="utf-8")
    client = FakeProjectClient()

    config = create_foundry_agent(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        model_deployment="gpt-4o",
        agent_name="themis-context-retriever",
        client=client,
        source_paths=(source,),
        file_search_factory=lambda vector_store_ids: {
            "definitions": [{"type": "file_search"}],
            "resources": {"file_search": {"vector_store_ids": vector_store_ids}},
        },
    )

    assert config.vector_store_id == "vs-123"
    assert config.source_file_ids == ("file-1",)


def test_attach_source_material_to_configuration_preserves_agent_details(tmp_path: Path) -> None:
    from themis.setup_agent import attach_source_material_to_configuration

    source = tmp_path / "context_architecture.md"
    source.write_text("# Architecture\n\nPrivate by default.\n", encoding="utf-8")
    client = FakeProjectClient()
    config = FoundryConfiguration(
        project_endpoint="https://example.services.ai.azure.com/api/projects/themis-agent",
        agent_id="agent-123",
        model_deployment="gpt-4o",
        agent_name="themis-context-retriever",
    )

    updated = attach_source_material_to_configuration(
        config,
        client=client,
        source_paths=(source,),
        file_search_factory=lambda vector_store_ids: {
            "definitions": [{"type": "file_search"}],
            "resources": {"file_search": {"vector_store_ids": vector_store_ids}},
        },
    )

    assert updated.project_endpoint == config.project_endpoint
    assert updated.agent_id == config.agent_id
    assert updated.model_deployment == config.model_deployment
    assert updated.agent_name == config.agent_name
    assert updated.vector_store_id == "vs-123"
    assert updated.source_file_ids == ("file-1",)
