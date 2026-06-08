from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from themis.contracts import RetrievedContext
from themis.foundry_configuration import load_effective_foundry_configuration

SAMPLE_CONTEXT_FILES = [
    Path("samples/context_architecture.md"),
    Path("samples/context_network_policy.md"),
    Path("samples/context_deployment_runbook.md"),
]


def retrieve_context(query: str, mode: Literal["mock", "foundry"] = "mock") -> list[RetrievedContext]:
    if mode == "mock":
        return _retrieve_mock_context(query)
    if mode == "foundry":
        return _retrieve_foundry_context(query)
    raise ValueError(f"Unsupported context retrieval mode: {mode}")


def _retrieve_mock_context(query: str) -> list[RetrievedContext]:
    query_terms = _terms(query)
    contexts: list[RetrievedContext] = []

    for path in SAMPLE_CONTEXT_FILES:
        if not path.exists():
            continue
        title, excerpt, score = _best_excerpt(path.read_text(encoding="utf-8"), query_terms)
        contexts.append(
            RetrievedContext(
                source_id=f"context_{path.stem}",
                title=title or path.stem.replace("_", " ").title(),
                kind="local markdown",
                relevant_excerpt=excerpt,
                reason_used="Matched local policy, architecture or runbook terms from the proposal.",
                confidence=score,
                citations=[path.as_posix()],
            )
        )

    return sorted(contexts, key=lambda item: (-item.confidence, item.source_id))


def _retrieve_foundry_context(query: str) -> list[RetrievedContext]:
    configuration = load_effective_foundry_configuration()
    if configuration is None:
        raise RuntimeError(
            "Foundry mode requires .themis/foundry.local.json or "
            "THEMIS_FOUNDRY_PROJECT_ENDPOINT and THEMIS_FOUNDRY_AGENT_ID. "
            "Run uv run themis-setup, or use mode='mock' for deterministic local retrieval."
        )

    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError(
            "Foundry mode requires the optional dependencies: uv sync --extra foundry"
        ) from exc

    client = AIProjectClient(
        endpoint=configuration.project_endpoint,
        credential=DefaultAzureCredential(),
    )
    thread = client.agents.threads.create()
    client.agents.messages.create(thread_id=thread.id, role="user", content=query)
    run = client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=configuration.agent_id,
    )
    if run.status != "completed":
        raise RuntimeError(foundry_run_failure_message(run))

    messages = list(client.agents.messages.list(thread_id=thread.id))
    excerpt, citations = extract_message_text_and_citations(messages, client)
    if not excerpt:
        raise RuntimeError("Foundry returned no assistant context text.")

    return [
        RetrievedContext(
            source_id="foundry_agent",
            title="Foundry agent response",
            kind="foundry agent",
            relevant_excerpt=excerpt[:1200],
            reason_used="Retrieved through configured Microsoft Foundry agent.",
            confidence=0.75,
            citations=citations,
        )
    ]


def foundry_run_failure_message(run: Any) -> str:
    message = f"Foundry run did not complete: {getattr(run, 'status', 'unknown')}"
    last_error = getattr(run, "last_error", None)
    if not last_error:
        return message
    if isinstance(last_error, dict):
        code = last_error.get("code")
        detail = last_error.get("message")
    else:
        code = getattr(last_error, "code", None)
        detail = getattr(last_error, "message", None)
    parts = [part for part in (code, detail) if part]
    if parts:
        message = f"{message} ({': '.join(str(part) for part in parts)})"
    return message


def extract_message_text_and_citations(
    messages: list[Any],
    client: Any,
) -> tuple[str, list[str]]:
    content_parts: list[str] = []
    citations: list[str] = []
    for message in messages:
        if getattr(message, "role", None) != "assistant":
            continue
        for item in getattr(message, "content", []):
            text = getattr(item, "text", None)
            value = getattr(text, "value", None)
            if value:
                content_parts.append(value)
            citations.extend(_annotation_citations(getattr(text, "annotations", []), client))
    return "\n".join(content_parts).strip(), _dedupe(citations)


def _annotation_citations(annotations: list[Any], client: Any) -> list[str]:
    citations: list[str] = []
    for annotation in annotations or []:
        file_citation = getattr(annotation, "file_citation", None)
        if file_citation is not None:
            file_id = getattr(file_citation, "file_id", None)
            if file_id:
                citations.append(_file_citation_label(client, file_id))
                continue
        url_citation = getattr(annotation, "url_citation", None)
        if url_citation is not None:
            url = getattr(url_citation, "url", None)
            title = getattr(url_citation, "title", None)
            if url and title:
                citations.append(f"{title}: {url}")
            elif url:
                citations.append(url)
            continue
        annotation_text = getattr(annotation, "text", None)
        if annotation_text:
            citations.append(str(annotation_text))
    return citations


def _file_citation_label(client: Any, file_id: str) -> str:
    try:
        foundry_file = client.agents.files.get(file_id)
    except Exception:  # noqa: BLE001 - citation resolution should not fail retrieval.
        return f"file:{file_id}"
    for attribute in ("filename", "file_name", "name", "id"):
        value = getattr(foundry_file, attribute, None)
        if value:
            return str(value)
    return f"file:{file_id}"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())
        if term not in {"the", "and", "for", "with", "this", "that", "will", "from"}
    }


def _best_excerpt(text: str, query_terms: set[str]) -> tuple[str, str, float]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), "")
    paragraphs = [line for line in lines if not line.startswith("#")]
    if not paragraphs:
        return title, text.strip()[:500], 0.25

    scored = []
    for paragraph in paragraphs:
        terms = _terms(paragraph)
        score = len(terms & query_terms)
        scored.append((score, paragraph))

    best_score, best = max(scored, key=lambda item: item[0])
    confidence = min(0.9, 0.35 + (best_score * 0.08))
    return title, best, confidence
