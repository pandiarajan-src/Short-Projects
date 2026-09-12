"""Provider selection: no silent default, env-only credentials.

Two adapters cover every supported backend (design.md: "Provider
adapters: two-adapter provider abstraction"): a native Anthropic
adapter, and a generic OpenAI-compatible adapter that covers Ollama,
DeepSeek, Kimi/Moonshot, and any other OpenAI-compatible endpoint.
"""

from __future__ import annotations

import os

from newsletter_distiller.ai.anthropic_adapter import AnthropicAdapter
from newsletter_distiller.ai.base import ProviderAdapter
from newsletter_distiller.ai.openai_compatible_adapter import OpenAICompatibleAdapter
from newsletter_distiller.errors import ProviderConfigError

PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI_COMPATIBLE = "openai-compatible"
SUPPORTED_PROVIDERS = (PROVIDER_ANTHROPIC, PROVIDER_OPENAI_COMPATIBLE)

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
OPENAI_COMPATIBLE_API_KEY_ENV = "NEWSLETTER_DISTILLER_API_KEY"
OPENAI_COMPATIBLE_BASE_URL_ENV = "NEWSLETTER_DISTILLER_BASE_URL"


def required_env_var(provider: str) -> str:
    """Name of the environment variable required for `provider`."""
    if provider == PROVIDER_ANTHROPIC:
        return ANTHROPIC_API_KEY_ENV
    if provider == PROVIDER_OPENAI_COMPATIBLE:
        return OPENAI_COMPATIBLE_API_KEY_ENV
    raise ProviderConfigError(
        f"unknown provider '{provider}' — supported providers: "
        f"{', '.join(SUPPORTED_PROVIDERS)}"
    )


def build_adapter(
    provider: str | None,
    model: str | None,
    base_url: str | None,
    timeout: float,
) -> ProviderAdapter:
    """Construct the adapter for `provider`.

    Raises ProviderConfigError if no provider was configured, the
    provider is unrecognized, or its required API key environment
    variable is not set — before any AI API request is made.
    """
    if not provider:
        raise ProviderConfigError(
            "no AI provider configured — set NEWSLETTER_DISTILLER_PROVIDER "
            f"(or pass --provider) to one of: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    if provider not in SUPPORTED_PROVIDERS:
        raise ProviderConfigError(
            f"unknown provider '{provider}' — supported providers: "
            f"{', '.join(SUPPORTED_PROVIDERS)}"
        )
    if not model:
        raise ProviderConfigError("no model configured — set --model or NEWSLETTER_DISTILLER_MODEL")

    env_var = required_env_var(provider)
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ProviderConfigError(
            f"required environment variable '{env_var}' is not set for provider '{provider}'"
        )

    if provider == PROVIDER_ANTHROPIC:
        return AnthropicAdapter(api_key=api_key, model=model, timeout=timeout)

    if not base_url:
        raise ProviderConfigError(
            "no base URL configured for the openai-compatible provider — set "
            f"--base-url or {OPENAI_COMPATIBLE_BASE_URL_ENV}"
        )
    return OpenAICompatibleAdapter(base_url=base_url, api_key=api_key, model=model, timeout=timeout)
