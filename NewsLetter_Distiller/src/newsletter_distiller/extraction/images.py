"""Download candidate image bytes and assign stable placeholder IDs."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from newsletter_distiller.extraction.parse import CandidateImage

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_TIMEOUT_SECONDS = 15.0


@dataclass
class DownloadedImage:
    id: str
    src: str
    alt: str
    surrounding_text: str
    position: int
    content: bytes
    extension: str


def _extension_for(content_type: str, src: str) -> str:
    guess = content_type.split("/")[-1].split(";")[0].strip().lower() if content_type else ""
    if guess in {"jpeg", "jpg", "png", "gif", "webp", "svg+xml"}:
        return "jpg" if guess == "jpeg" else guess.replace("+xml", "")
    suffix = src.rsplit(".", 1)[-1].split("?")[0].lower()
    if suffix in {"jpg", "jpeg", "png", "gif", "webp", "svg"}:
        return "jpg" if suffix == "jpeg" else suffix
    return "png"


def download_images(
    candidates: list[CandidateImage],
    timeout: float = DEFAULT_IMAGE_TIMEOUT_SECONDS,
) -> list[DownloadedImage]:
    """Download bytes for every candidate image, skipping ones that fail.

    A failed download logs a warning and is excluded from the result —
    it does not abort the run (content-extraction: Download candidate
    image bytes and assign stable IDs).
    """
    downloaded: list[DownloadedImage] = []
    next_id = 1

    for candidate in candidates:
        try:
            response = requests.get(candidate.src, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("skipping candidate image %s: %s", candidate.src, exc)
            continue

        content_type = response.headers.get("Content-Type", "")
        downloaded.append(
            DownloadedImage(
                id=f"IMAGE_{next_id}",
                src=candidate.src,
                alt=candidate.alt,
                surrounding_text=candidate.surrounding_text,
                position=candidate.position,
                content=response.content,
                extension=_extension_for(content_type, candidate.src),
            )
        )
        next_id += 1

    return downloaded
