"""Shared helpers for provider adapters."""

from __future__ import annotations

from typing import Protocol

from newsletter_distiller.ai.request import DistillationRequest


class ProviderAdapter(Protocol):
    """A provider adapter turns a DistillationRequest into markdown text
    that references images only by placeholder ID (e.g. `IMAGE_2`).
    """

    def distill(self, request: DistillationRequest) -> str: ...


def format_image_manifest(request: DistillationRequest) -> str:
    """Render the candidate-image metadata as text for the user message.

    Every adapter includes this regardless of whether raw image bytes
    are also attached, since it's the sole signal for text-only models
    and a helpful anchor even for vision-capable ones.
    """
    if not request.images:
        return "No candidate images were found in this newsletter."

    lines = [
        "Candidate images found in the newsletter (reference by ID only, "
        "e.g. ![description](IMAGE_2), in your markdown output; omit any "
        "you judge to be advertisements or purely decorative):",
    ]
    for image in request.images:
        lines.append(
            f'- {image.id}: alt="{image.alt}" '
            f'context="{image.surrounding_text}"'
        )
    return "\n".join(lines)


def build_user_text(request: DistillationRequest) -> str:
    return (
        f"{request.user_prompt}\n\n"
        f"--- ARTICLE TEXT ---\n{request.article_text}\n\n"
        f"--- IMAGES ---\n{format_image_manifest(request)}"
    )
