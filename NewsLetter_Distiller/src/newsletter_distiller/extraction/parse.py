"""Extract main article text and candidate images, in reading order."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from newsletter_distiller.errors import EmptyContentError
from newsletter_distiller.extraction.boilerplate import strip_boilerplate

# Below this many alphanumeric characters, extracted text is considered
# "no usable content" rather than a thin-but-real article.
MIN_SUBSTANTIVE_CHARS = 80

TEXT_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li")
HEADING_PREFIXES = {f"h{level}": "#" * level + " " for level in range(1, 7)}


@dataclass
class CandidateImage:
    position: int
    src: str
    alt: str
    surrounding_text: str


@dataclass
class ExtractedContent:
    title: str
    text: str
    candidate_images: list[CandidateImage] = field(default_factory=list)


def _block_text(tag: Tag) -> str:
    prefix = HEADING_PREFIXES.get(tag.name, "- " if tag.name == "li" else "")
    text = tag.get_text(" ", strip=True)
    return f"{prefix}{text}" if text else ""


def extract_content(html: str, base_url: str) -> ExtractedContent:
    """Parse `html`, strip boilerplate, and return the article text plus
    every candidate image with its metadata, in reading order.

    Raises EmptyContentError if no substantive text survives extraction.
    """
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    strip_boilerplate(soup)

    text_blocks: list[str] = []
    candidate_images: list[CandidateImage] = []
    position = 0

    for tag in soup.find_all(TEXT_TAGS + ("img",)):
        if tag.decomposed:
            continue
        if tag.name == "img":
            src = tag.get("src")
            if not src:
                continue
            surrounding = text_blocks[-1] if text_blocks else ""
            candidate_images.append(
                CandidateImage(
                    position=position,
                    src=urljoin(base_url, src),
                    alt=(tag.get("alt") or "").strip(),
                    surrounding_text=surrounding,
                )
            )
            position += 1
        else:
            block = _block_text(tag)
            if block:
                text_blocks.append(block)
                position += 1

    text = "\n\n".join(text_blocks)

    if len(_alnum_only(text)) < MIN_SUBSTANTIVE_CHARS:
        raise EmptyContentError(
            "no substantive article text found after stripping boilerplate "
            "(possible paywall, bot-block, or unsupported page layout)"
        )

    return ExtractedContent(title=title, text=text, candidate_images=candidate_images)


def _alnum_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum())
