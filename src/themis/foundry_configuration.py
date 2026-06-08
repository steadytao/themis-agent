from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from themis.foundry_resources import DEFAULT_MODEL_DEPLOYMENT

DEFAULT_CONFIG_PATH = Path(".themis/foundry.local.json")


@dataclass(frozen=True)
class FoundryConfiguration:
    project_endpoint: str
    agent_id: str
    model_deployment: str
    agent_name: str
    vector_store_id: str | None = None
    source_file_ids: tuple[str, ...] = ()


def save_foundry_configuration(
    configuration: FoundryConfiguration,
    path: Path = DEFAULT_CONFIG_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(configuration), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_foundry_configuration(path: Path = DEFAULT_CONFIG_PATH) -> FoundryConfiguration | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data.get("source_file_ids"), list):
        data["source_file_ids"] = tuple(data["source_file_ids"])
    return FoundryConfiguration(**data)


def load_effective_foundry_configuration(
    path: Path = DEFAULT_CONFIG_PATH,
) -> FoundryConfiguration | None:
    configuration = load_foundry_configuration(path)
    endpoint = os.getenv("THEMIS_FOUNDRY_PROJECT_ENDPOINT") or (
        configuration.project_endpoint if configuration else None
    )
    agent_id = os.getenv("THEMIS_FOUNDRY_AGENT_ID") or (
        configuration.agent_id if configuration else None
    )
    if not endpoint or not agent_id:
        return None
    return FoundryConfiguration(
        project_endpoint=endpoint,
        agent_id=agent_id,
        model_deployment=(
            os.getenv("THEMIS_FOUNDRY_MODEL_DEPLOYMENT")
            or (configuration.model_deployment if configuration else DEFAULT_MODEL_DEPLOYMENT)
        ),
        agent_name=(
            os.getenv("THEMIS_FOUNDRY_AGENT_NAME")
            or (configuration.agent_name if configuration else "themis-context-retriever")
        ),
        vector_store_id=configuration.vector_store_id if configuration else None,
        source_file_ids=configuration.source_file_ids if configuration else (),
    )


def render_environment_commands(configuration: FoundryConfiguration) -> str:
    return "\n".join(
        [
            f'$env:THEMIS_FOUNDRY_PROJECT_ENDPOINT = "{configuration.project_endpoint}"',
            f'$env:THEMIS_FOUNDRY_AGENT_ID = "{configuration.agent_id}"',
            "uv run themis-review samples/change_risky.md --context-mode foundry",
        ]
    )


def prompt_foundry_configuration() -> FoundryConfiguration:
    endpoint = _prompt("Foundry project endpoint")
    agent_id = _prompt("Foundry agent ID")
    model_deployment = _prompt("Model deployment name", DEFAULT_MODEL_DEPLOYMENT)
    agent_name = _prompt("Agent name", "themis-context-retriever")
    return FoundryConfiguration(
        project_endpoint=endpoint,
        agent_id=agent_id,
        model_deployment=model_deployment,
        agent_name=agent_name,
    )


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise ValueError(f"{label} is required.")
