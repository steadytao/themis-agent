import pytest

from themis.iq import retrieve_context


def test_mock_retrieval_returns_named_context() -> None:
    contexts = retrieve_context("public load balancer rollback", mode="mock")

    assert contexts
    assert all(context.source_id for context in contexts)
    assert all(context.relevant_excerpt for context in contexts)
    assert all(context.citations for context in contexts)


def test_mock_retrieval_is_deterministic() -> None:
    first = retrieve_context("public load balancer rollback", mode="mock")
    second = retrieve_context("public load balancer rollback", mode="mock")

    assert [item.model_dump(mode="json") for item in first] == [
        item.model_dump(mode="json") for item in second
    ]


def test_foundry_mode_fails_clearly_without_configuration(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("THEMIS_FOUNDRY_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("THEMIS_FOUNDRY_AGENT_ID", raising=False)

    with pytest.raises(RuntimeError, match="foundry.local.json"):
        retrieve_context("public load balancer", mode="foundry")


def test_foundry_retrieval_prompt_requires_file_search_context() -> None:
    from themis.iq import build_foundry_retrieval_prompt

    prompt = build_foundry_retrieval_prompt("Expose admin service publicly.")

    assert "attached file-search source material" in prompt
    assert "Cite the source file" in prompt
    assert "retrieve context only" in prompt
    assert "Expose admin service publicly." in prompt


class FakeFileCitation:
    file_id = "file-123"


class FakeAnnotation:
    text = "network policy"
    file_citation = FakeFileCitation()


class FakeText:
    value = "Use the network policy for public exposure."
    annotations = [FakeAnnotation()]


class FakeContentItem:
    text = FakeText()


class FakeAssistantMessage:
    role = "assistant"
    content = [FakeContentItem()]


class FakeRetrievedFile:
    filename = "context_network_policy.md"


class FakeFilesClient:
    def get(self, file_id: str):
        assert file_id == "file-123"
        return FakeRetrievedFile()


class FakeAgentsClient:
    files = FakeFilesClient()


class FakeClient:
    agents = FakeAgentsClient()


def test_extract_message_text_and_citations_resolves_file_citations() -> None:
    from themis.iq import extract_message_text_and_citations

    text, citations = extract_message_text_and_citations([FakeAssistantMessage()], FakeClient())

    assert text == "Use the network policy for public exposure."
    assert citations == ["context_network_policy.md"]


class FakeFailedRun:
    status = "failed"
    last_error = {"code": "rate_limit_exceeded", "message": "Retry after 8 seconds."}


def test_foundry_run_failure_message_includes_last_error() -> None:
    from themis.iq import foundry_run_failure_message

    message = foundry_run_failure_message(FakeFailedRun())

    assert "failed" in message
    assert "rate_limit_exceeded" in message
    assert "Retry after 8 seconds." in message
