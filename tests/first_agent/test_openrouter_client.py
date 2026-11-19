import json

import httpx
import pytest

from tutorials.first_agent import openrouter_client as module


def mock_http(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    original_sdk = module.OpenRouter
    monkeypatch.setattr(
        module,
        "OpenRouter",
        lambda **kwargs: original_sdk(
            client=httpx.Client(transport=httpx.MockTransport(handler)), **kwargs
        ),
    )


def completed_response(**overrides):
    return {
        "completed_at": None,
        "created_at": 1,
        "error": None,
        "frequency_penalty": None,
        "id": "resp_fixture",
        "incomplete_details": None,
        "instructions": None,
        "metadata": None,
        "model": "provider/fixed-model",
        "object": "response",
        "output": [],
        "parallel_tool_calls": False,
        "presence_penalty": None,
        "status": "completed",
        "temperature": None,
        "tool_choice": "auto",
        "tools": [],
        "top_p": None,
        **overrides,
    }


def test_sends_responses_payload_without_mutating_it(monkeypatch) -> None:
    payload = {"model": "", "input": "Find launch notes", "tools": []}

    def handler(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/responses"
        assert request.headers["Authorization"] == "Bearer fixture-key"
        assert json.loads(request.content) == {
            **payload,
            "model": "provider/fixed-model",
            "stream": False,
            "store": False,
            "service_tier": "auto",
        }
        return httpx.Response(200, json=completed_response())

    mock_http(monkeypatch, handler)
    client = module.OpenRouterClient("fixture-key", "provider/fixed-model")
    assert client.create_response(payload)["status"] == "completed"
    assert payload["model"] == ""
    assert "store" not in payload
    assert "fixture-key" not in repr(client)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(401, text="private-provider-error"),
        httpx.Response(200, text="private-invalid-json"),
        httpx.Response(200, json=[]),
        httpx.Response(200, json=completed_response(status="incomplete")),
        httpx.Response(
            200,
            json=completed_response(
                error={"code": "server_error", "message": "private"}
            ),
        ),
    ],
)
def test_rejects_failed_responses_without_exposing_bodies(monkeypatch, response):
    mock_http(monkeypatch, lambda request: response)
    with pytest.raises(module.OpenRouterError) as error:
        module.OpenRouterClient("fixture-key", "provider/model").create_response({})
    assert "private" not in str(error.value)
    assert "fixture-key" not in str(error.value)


def test_timeout_does_not_retry(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("private transport details", request=request)

    mock_http(monkeypatch, handler)
    with pytest.raises(module.OpenRouterError, match="timed out"):
        module.OpenRouterClient("fixture-key", "provider/model").create_response({})
    assert len(calls) == 1


def test_from_env_preserves_shell_overrides(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "OPENROUTER_API_KEY=file-key\nOPENROUTER_MODEL=provider/file-model\n"
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "shell-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "provider/shell-model")
    client = module.OpenRouterClient.from_env()
    assert client.api_key == "shell-key"
    assert client.model == "provider/shell-model"


def test_missing_settings_fail_before_network(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    with pytest.raises(ValueError, match="Set OPENROUTER"):
        module.OpenRouterClient.from_env()


@pytest.mark.parametrize("flag", ["stream", "background"])
def test_rejects_unsupported_execution_modes(flag):
    with pytest.raises(ValueError, match="synchronous, non-streaming"):
        module.OpenRouterClient("fixture-key", "provider/model").create_response(
            {flag: True}
        )


def test_server_error_does_not_retry(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, text="private provider body")

    mock_http(monkeypatch, handler)
    with pytest.raises(module.OpenRouterError):
        module.OpenRouterClient("fixture-key", "provider/model").create_response({})
    assert len(calls) == 1


def test_storing_responses_is_not_enabled():
    with pytest.raises(ValueError, match="store=False"):
        module.OpenRouterClient("fixture-key", "provider/model").create_response(
            {"store": True}
        )


def test_real_sdk_serializes_the_tool_and_parses_its_call(monkeypatch):
    from tutorials.first_agent.part_01.main import run

    def handler(request):
        body = json.loads(request.content)
        assert body["tools"][0]["name"] == "search_notes"
        assert body["tool_choice"] == {"type": "function", "name": "search_notes"}
        assert body["parallel_tool_calls"] is False
        return httpx.Response(
            200,
            json=completed_response(
                output=[
                    {
                        "type": "function_call",
                        "call_id": "sdk-search",
                        "name": "search_notes",
                        "arguments": '{"query":"launch"}',
                    }
                ]
            ),
        )

    mock_http(monkeypatch, handler)
    result = run(
        module.OpenRouterClient("fixture-key", "provider/model"), "Find launch"
    )
    assert result.reason == "tool_result"
    assert "support scope is unclear" in result.answer
