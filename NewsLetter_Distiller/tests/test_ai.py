from pathlib import Path

import pytest
import responses

from newsletter_distiller.ai.prompts import load_prompt
from newsletter_distiller.ai.provider import (
    ANTHROPIC_API_KEY_ENV,
    OPENAI_COMPATIBLE_API_KEY_ENV,
    OPENAI_COMPATIBLE_BASE_URL_ENV,
    build_adapter,
)
from newsletter_distiller.ai.request import build_request
from newsletter_distiller.ai.vision import is_vision_capable
from newsletter_distiller.extraction.images import DownloadedImage
from newsletter_distiller.extraction.parse import ExtractedContent
from newsletter_distiller.errors import AIRequestError, PromptFileError, ProviderConfigError


def _extracted():
    return ExtractedContent(title="Test", text="Hello world " * 10, candidate_images=[])


def _images():
    return [
        DownloadedImage(
            id="IMAGE_1", src="https://example.com/a.png", alt="a chart",
            surrounding_text="ctx", position=0, content=b"BYTES", extension="png",
        )
    ]


# --- 4.1 provider-agnostic request builder --------------------------------

def test_build_request_from_extraction_output():
    request = build_request("sys", "user", _extracted(), _images(), vision_capable=True)
    assert request.system_prompt == "sys"
    assert request.article_text.startswith("Hello world")
    assert request.images[0].id == "IMAGE_1"
    assert request.images[0].content == b"BYTES"


def test_build_request_omits_bytes_when_not_vision_capable():
    request = build_request("sys", "user", _extracted(), _images(), vision_capable=False)
    assert request.images[0].content is None


# --- 4.2 prompt loading/validation -----------------------------------------

def test_load_prompt_missing_file(tmp_path):
    with pytest.raises(PromptFileError):
        load_prompt(tmp_path / "missing.txt", "system")


def test_load_prompt_empty_file(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("   \n  ")
    with pytest.raises(PromptFileError):
        load_prompt(path, "system")


def test_load_prompt_success(tmp_path):
    path = tmp_path / "ok.txt"
    path.write_text("Be concise.")
    assert load_prompt(path, "system") == "Be concise."


# --- 4.3 vision-capability lookup -------------------------------------------

@pytest.mark.parametrize("model", ["claude-sonnet-5", "gpt-4o-mini", "llava-13b"])
def test_known_vision_models_detected(model):
    assert is_vision_capable(model) is True


def test_unknown_model_defaults_to_text_only():
    assert is_vision_capable("some-future-text-model") is False


def test_override_wins_over_lookup():
    assert is_vision_capable("claude-sonnet-5", override=False) is False
    assert is_vision_capable("some-future-text-model", override=True) is True


# --- 4.4 Anthropic adapter ---------------------------------------------------

def test_anthropic_adapter_sends_multimodal_request(mocker):
    from newsletter_distiller.ai.anthropic_adapter import AnthropicAdapter

    fake_response = mocker.Mock()
    fake_block = mocker.Mock()
    fake_block.type = "text"
    fake_block.text = "# Digest\n\n![chart](IMAGE_1)"
    fake_response.content = [fake_block]

    adapter = AnthropicAdapter(api_key="sk-test", model="claude-sonnet-5")
    create_mock = mocker.patch.object(adapter._client.messages, "create", return_value=fake_response)

    request = build_request("sys", "user", _extracted(), _images(), vision_capable=True)
    markdown = adapter.distill(request)

    assert markdown == "# Digest\n\n![chart](IMAGE_1)"
    call_kwargs = create_mock.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-5"
    content_blocks = call_kwargs["messages"][0]["content"]
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[1]["type"] == "image"
    assert content_blocks[1]["source"]["media_type"] == "image/png"


def test_anthropic_adapter_maps_auth_error(mocker):
    import anthropic

    from newsletter_distiller.ai.anthropic_adapter import AnthropicAdapter

    adapter = AnthropicAdapter(api_key="sk-test", model="claude-sonnet-5")
    mocker.patch.object(
        adapter._client.messages,
        "create",
        side_effect=anthropic.AuthenticationError(
            "bad key", response=mocker.Mock(status_code=401, headers={}), body=None
        ),
    )
    request = build_request("sys", "user", _extracted(), _images(), vision_capable=False)
    with pytest.raises(AIRequestError):
        adapter.distill(request)


# --- 4.5 OpenAI-compatible adapter ------------------------------------------

@responses.activate
def test_openai_compatible_adapter_success():
    from newsletter_distiller.ai.openai_compatible_adapter import OpenAICompatibleAdapter

    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        json={"choices": [{"message": {"content": "# Digest"}}]},
        status=200,
    )
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1", api_key="ollama", model="llava-13b"
    )
    request = build_request("sys", "user", _extracted(), _images(), vision_capable=True)
    result = adapter.distill(request)
    assert result == "# Digest"

    sent_body = responses.calls[0].request.body
    assert b"image_url" in sent_body


@responses.activate
def test_openai_compatible_adapter_maps_auth_error():
    from newsletter_distiller.ai.openai_compatible_adapter import OpenAICompatibleAdapter

    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        status=401,
    )
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1", api_key="bad", model="llava-13b"
    )
    request = build_request("sys", "user", _extracted(), [], vision_capable=False)
    with pytest.raises(AIRequestError):
        adapter.distill(request)


@responses.activate
def test_openai_compatible_adapter_maps_rate_limit():
    from newsletter_distiller.ai.openai_compatible_adapter import OpenAICompatibleAdapter

    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        status=429,
    )
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1", api_key="key", model="llava-13b"
    )
    request = build_request("sys", "user", _extracted(), [], vision_capable=False)
    with pytest.raises(AIRequestError):
        adapter.distill(request)


@responses.activate
def test_openai_compatible_adapter_timeout():
    import requests as requests_lib

    from newsletter_distiller.ai.openai_compatible_adapter import OpenAICompatibleAdapter

    responses.add(
        responses.POST,
        "http://localhost:11434/v1/chat/completions",
        body=requests_lib.exceptions.Timeout("timed out"),
    )
    adapter = OpenAICompatibleAdapter(
        base_url="http://localhost:11434/v1", api_key="key", model="llava-13b", timeout=1.0
    )
    request = build_request("sys", "user", _extracted(), [], vision_capable=False)
    with pytest.raises(AIRequestError):
        adapter.distill(request)


# --- 4.6 provider-selection guardrail --------------------------------------

def test_build_adapter_no_provider_configured(monkeypatch):
    with pytest.raises(ProviderConfigError):
        build_adapter(provider=None, model="claude-sonnet-5", base_url=None, timeout=30.0)


def test_build_adapter_missing_api_key_env(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
    with pytest.raises(ProviderConfigError):
        build_adapter(provider="anthropic", model="claude-sonnet-5", base_url=None, timeout=30.0)


def test_build_adapter_anthropic_success(monkeypatch):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    adapter = build_adapter(provider="anthropic", model="claude-sonnet-5", base_url=None, timeout=30.0)
    assert adapter.__class__.__name__ == "AnthropicAdapter"


def test_build_adapter_openai_compatible_requires_base_url(monkeypatch):
    monkeypatch.setenv(OPENAI_COMPATIBLE_API_KEY_ENV, "ollama")
    with pytest.raises(ProviderConfigError):
        build_adapter(provider="openai-compatible", model="llava-13b", base_url=None, timeout=30.0)


def test_build_adapter_openai_compatible_success(monkeypatch):
    monkeypatch.setenv(OPENAI_COMPATIBLE_API_KEY_ENV, "ollama")
    adapter = build_adapter(
        provider="openai-compatible",
        model="llava-13b",
        base_url="http://localhost:11434/v1",
        timeout=30.0,
    )
    assert adapter.__class__.__name__ == "OpenAICompatibleAdapter"
