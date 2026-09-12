"""Determine whether a configured model is vision-capable.

A static lookup table can go stale as new models ship, so an explicit
override always wins over the table (design.md: "Vision-capability
detection"). Defaulting an unrecognized model to text-only is the safe
choice — never send binary bytes to a model that might reject or
silently ignore them.
"""

from __future__ import annotations

import re

VISION_MODEL_PATTERNS = (
    re.compile(r"^claude-", re.IGNORECASE),
    re.compile(r"^gpt-4o", re.IGNORECASE),
    re.compile(r"^gpt-5", re.IGNORECASE),
    re.compile(r"vision", re.IGNORECASE),
    re.compile(r"^qwen.*-vl", re.IGNORECASE),
    re.compile(r"^llava", re.IGNORECASE),
    re.compile(r"^gemini-", re.IGNORECASE),
)


def is_vision_capable(model: str, override: bool | None = None) -> bool:
    """Return whether `model` should receive raw image bytes.

    `override`, when not None, takes precedence over the lookup table.
    """
    if override is not None:
        return override

    return any(pattern.search(model) for pattern in VISION_MODEL_PATTERNS)
