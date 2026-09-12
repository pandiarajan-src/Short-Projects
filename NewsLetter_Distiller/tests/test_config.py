import argparse
from pathlib import Path

import pytest

from newsletter_distiller.ai.provider import ANTHROPIC_API_KEY_ENV
from newsletter_distiller.config import load_config
from newsletter_distiller.errors import ConfigError, OutputError, ProviderConfigError
from newsletter_distiller.validation import validate_startup


def _args(**overrides):
    defaults = dict(
        url="https://example.com/newsletter",
        provider=None,
        model=None,
        base_url=None,
        system_prompt=None,
        user_prompt=None,
        output_dir=None,
        overwrite=False,
        vision=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# --- 2.1 config loader -------------------------------------------------

def test_load_config_applies_defaults():
    config = load_config(_args())
    assert config.system_prompt_path == Path("prompts/system_prompt.txt")
    assert config.output_dir == Path("output")
    assert config.overwrite is False


def test_load_config_cli_flags_override_env(monkeypatch):
    monkeypatch.setenv("NEWSLETTER_DISTILLER_PROVIDER", "anthropic")
    config = load_config(_args(provider="openai-compatible"))
    assert config.provider == "openai-compatible"


def test_load_config_rejects_unknown_provider():
    with pytest.raises(ConfigError):
        load_config(_args(provider="not-a-real-provider"))


def test_load_config_rejects_bad_vision_env(monkeypatch):
    monkeypatch.setenv("NEWSLETTER_DISTILLER_VISION", "maybe")
    with pytest.raises(ConfigError):
        load_config(_args())


# --- 2.2 ordered fail-fast startup validation ---------------------------

def test_validate_startup_rejects_bad_url_before_anything_else(monkeypatch, tmp_path):
    config = load_config(_args(url="ftp://example.com/x"))
    with pytest.raises(Exception) as excinfo:
        validate_startup(config)
    assert "scheme" in str(excinfo.value)


def test_validate_startup_rejects_missing_provider():
    config = load_config(_args())
    with pytest.raises(ProviderConfigError):
        validate_startup(config)


def test_validate_startup_rejects_missing_api_key_env(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
    config = load_config(_args(provider="anthropic", model="claude-sonnet-5"))
    with pytest.raises(ProviderConfigError):
        validate_startup(config)


def test_validate_startup_rejects_missing_prompt_files(monkeypatch, tmp_path):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    config = load_config(
        _args(
            provider="anthropic",
            model="claude-sonnet-5",
            system_prompt=str(tmp_path / "missing_system.txt"),
            user_prompt=str(tmp_path / "missing_user.txt"),
        )
    )
    with pytest.raises(Exception) as excinfo:
        validate_startup(config)
    assert "prompt" in str(excinfo.value).lower()


def test_validate_startup_rejects_multiple_problems_reports_first(monkeypatch, tmp_path):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
    config = load_config(
        _args(
            provider="anthropic",
            model="claude-sonnet-5",
            system_prompt=str(tmp_path / "missing.txt"),
            user_prompt=str(tmp_path / "missing.txt"),
        )
    )
    # Missing API key comes before prompt-file checks in the ordered
    # sequence, so that's the error that should surface here.
    with pytest.raises(ProviderConfigError):
        validate_startup(config)


def test_validate_startup_succeeds_and_returns_prompts(monkeypatch, tmp_path):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    system_path = tmp_path / "system.txt"
    user_path = tmp_path / "user.txt"
    system_path.write_text("Be concise.")
    user_path.write_text("Summarize this newsletter.")
    output_dir = tmp_path / "out"

    config = load_config(
        _args(
            provider="anthropic",
            model="claude-sonnet-5",
            system_prompt=str(system_path),
            user_prompt=str(user_path),
            output_dir=str(output_dir),
        )
    )
    system_prompt, user_prompt = validate_startup(config)
    assert system_prompt == "Be concise."
    assert user_prompt == "Summarize this newsletter."
    assert output_dir.exists()


def test_validate_startup_rejects_unwritable_output_dir(monkeypatch, tmp_path):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, "sk-test")
    system_path = tmp_path / "system.txt"
    user_path = tmp_path / "user.txt"
    system_path.write_text("Be concise.")
    user_path.write_text("Summarize this newsletter.")

    readonly_parent = tmp_path / "readonly"
    readonly_parent.mkdir()
    readonly_parent.chmod(0o500)
    output_dir = readonly_parent / "out"

    config = load_config(
        _args(
            provider="anthropic",
            model="claude-sonnet-5",
            system_prompt=str(system_path),
            user_prompt=str(user_path),
            output_dir=str(output_dir),
        )
    )
    try:
        with pytest.raises(OutputError):
            validate_startup(config)
    finally:
        readonly_parent.chmod(0o700)
