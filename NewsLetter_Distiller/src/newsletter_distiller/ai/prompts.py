"""Load and validate the system/user prompt files."""

from __future__ import annotations

from pathlib import Path

from newsletter_distiller.errors import PromptFileError


def load_prompt(path: Path, label: str) -> str:
    """Read `path` and return its content.

    Raises PromptFileError if the file is missing or contains only
    whitespace — checked before any AI API call is made.
    """
    if not path.exists():
        raise PromptFileError(f"{label} prompt file not found: {path}")
    if not path.is_file():
        raise PromptFileError(f"{label} prompt path is not a file: {path}")

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise PromptFileError(f"{label} prompt file is empty: {path}")

    return content
