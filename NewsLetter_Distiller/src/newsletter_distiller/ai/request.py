"""Provider-agnostic distillation request shape.

Both adapters (Anthropic native, OpenAI-compatible) consume the same
`DistillationRequest` and are responsible for translating it into their
own wire format.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from newsletter_distiller.extraction.images import DownloadedImage
from newsletter_distiller.extraction.parse import ExtractedContent


@dataclass
class RequestImage:
    id: str
    alt: str
    surrounding_text: str
    content: bytes | None
    extension: str


@dataclass
class DistillationRequest:
    system_prompt: str
    user_prompt: str
    article_text: str
    images: list[RequestImage] = field(default_factory=list)


def build_request(
    system_prompt: str,
    user_prompt: str,
    extracted: ExtractedContent,
    downloaded_images: list[DownloadedImage],
    vision_capable: bool,
) -> DistillationRequest:
    """Combine prompts, article text, and image metadata/IDs into one
    request understood identically by every provider adapter.

    Raw image bytes are attached only when `vision_capable` is True;
    otherwise the AI relies solely on alt text/context for any
    ad-vs-concept judgment (ai-provider-integration: Attach image bytes
    only for vision-capable models).
    """
    images = [
        RequestImage(
            id=image.id,
            alt=image.alt,
            surrounding_text=image.surrounding_text,
            content=image.content if vision_capable else None,
            extension=image.extension,
        )
        for image in downloaded_images
    ]

    return DistillationRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        article_text=extracted.text,
        images=images,
    )
