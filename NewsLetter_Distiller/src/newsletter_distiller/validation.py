"""Ordered fail-fast startup validation.

Runs before any network fetch or AI request, in this specific order, so
a configuration mistake is reported immediately rather than after
wasted work (cli-orchestration: "Ordered validation before network/API
calls").

The output folder's exact path depends on the newsletter's title, which
is only known after fetching — so this checks that the *base* output
directory is writable up front, while the slug-specific
already-exists/writable check (markdown-output-assembly: "Validate
output location before AI call") runs later, once extraction has
produced a title, but still strictly before the AI request.
"""

from __future__ import annotations

import os
from pathlib import Path

from newsletter_distiller.ai.prompts import load_prompt
from newsletter_distiller.ai.provider import PROVIDER_OPENAI_COMPATIBLE, required_env_var
from newsletter_distiller.config import Config
from newsletter_distiller.errors import OutputError, ProviderConfigError
from newsletter_distiller.extraction.url import validate_url_scheme


def validate_startup(config: Config) -> tuple[str, str]:
    """Run the ordered pre-flight checks and return the loaded
    (system_prompt, user_prompt) content for reuse by the pipeline.
    """
    validate_url_scheme(config.url)

    if not config.provider:
        raise ProviderConfigError(
            "no AI provider configured — set NEWSLETTER_DISTILLER_PROVIDER or pass --provider"
        )
    if not config.model:
        raise ProviderConfigError(
            "no model configured — set NEWSLETTER_DISTILLER_MODEL or pass --model"
        )

    env_var = required_env_var(config.provider)
    if not os.environ.get(env_var):
        raise ProviderConfigError(
            f"required environment variable '{env_var}' is not set for provider '{config.provider}'"
        )
    if config.provider == PROVIDER_OPENAI_COMPATIBLE and not config.base_url:
        raise ProviderConfigError(
            "no base URL configured for the openai-compatible provider — set "
            "--base-url or NEWSLETTER_DISTILLER_BASE_URL"
        )

    system_prompt = load_prompt(config.system_prompt_path, "system")
    user_prompt = load_prompt(config.user_prompt_path, "user")

    _validate_output_dir_writable(config.output_dir)

    return system_prompt, user_prompt


def _validate_output_dir_writable(output_dir: Path) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".newsletter_distiller_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise OutputError(f"output directory is not writable: {output_dir} ({exc})") from exc
