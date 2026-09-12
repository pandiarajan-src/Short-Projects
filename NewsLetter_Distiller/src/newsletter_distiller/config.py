"""Config loading: CLI flags override environment variables override
documented defaults. Secrets (API keys) are read only from the
environment inside `newsletter_distiller.ai.provider` — never here,
and never from a CLI flag.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from newsletter_distiller.ai.provider import (
    OPENAI_COMPATIBLE_BASE_URL_ENV,
    SUPPORTED_PROVIDERS,
)
from newsletter_distiller.errors import ConfigError

PROVIDER_ENV = "NEWSLETTER_DISTILLER_PROVIDER"
MODEL_ENV = "NEWSLETTER_DISTILLER_MODEL"
VISION_ENV = "NEWSLETTER_DISTILLER_VISION"

DEFAULT_SYSTEM_PROMPT_PATH = Path("prompts/system_prompt.txt")
DEFAULT_USER_PROMPT_PATH = Path("prompts/user_prompt.txt")
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_FETCH_TIMEOUT = 30.0
DEFAULT_IMAGE_TIMEOUT = 15.0
DEFAULT_AI_TIMEOUT = 120.0


@dataclass
class Config:
    url: str
    provider: str | None
    model: str | None
    base_url: str | None
    system_prompt_path: Path
    user_prompt_path: Path
    output_dir: Path
    overwrite: bool
    vision_override: bool | None
    fetch_timeout: float
    image_timeout: float
    ai_timeout: float


def _parse_vision_override(raw: str | None) -> bool | None:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ConfigError(f"invalid value for {VISION_ENV}/--vision: '{raw}' (expected true/false)")


def load_config(args) -> Config:
    """Merge CLI flags (highest priority) with environment variables and
    documented defaults into a single Config.

    Raises ConfigError immediately for a malformed value (not merely an
    absent one — provider/credential presence is checked by the ordered
    startup validation, since it also needs to run in a specific order
    relative to the other checks).
    """
    provider = args.provider or os.environ.get(PROVIDER_ENV)
    if provider and provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"unknown provider '{provider}' — supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    model = args.model or os.environ.get(MODEL_ENV)
    base_url = args.base_url or os.environ.get(OPENAI_COMPATIBLE_BASE_URL_ENV)

    vision_flag = args.vision if getattr(args, "vision", None) is not None else None
    vision_override = (
        vision_flag if vision_flag is not None else _parse_vision_override(os.environ.get(VISION_ENV))
    )

    return Config(
        url=args.url,
        provider=provider,
        model=model,
        base_url=base_url,
        system_prompt_path=Path(args.system_prompt or DEFAULT_SYSTEM_PROMPT_PATH),
        user_prompt_path=Path(args.user_prompt or DEFAULT_USER_PROMPT_PATH),
        output_dir=Path(args.output_dir or DEFAULT_OUTPUT_DIR),
        overwrite=bool(args.overwrite),
        vision_override=vision_override,
        fetch_timeout=DEFAULT_FETCH_TIMEOUT,
        image_timeout=DEFAULT_IMAGE_TIMEOUT,
        ai_timeout=DEFAULT_AI_TIMEOUT,
    )
