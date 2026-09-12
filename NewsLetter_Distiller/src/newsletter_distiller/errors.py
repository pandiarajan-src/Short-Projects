"""Stage-attributed exceptions.

Every failure the CLI can hit carries the pipeline stage it happened in,
so the top-level entry point can print a distinct, actionable message per
stage instead of a bare traceback.
"""

from __future__ import annotations


class DistillerError(Exception):
    """Base class for all expected (non-programmer-error) failures."""

    stage = "distiller"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"[{self.stage}] {self.message}"


class ConfigError(DistillerError):
    stage = "config"


class ValidationError(DistillerError):
    stage = "validation"


class FetchError(DistillerError):
    stage = "fetch"


class EmptyContentError(DistillerError):
    stage = "extraction"


class PromptFileError(DistillerError):
    stage = "ai"


class ProviderConfigError(DistillerError):
    stage = "ai"


class AIRequestError(DistillerError):
    stage = "ai"


class OutputError(DistillerError):
    stage = "output"


class UnknownImagePlaceholderError(OutputError):
    stage = "output"
