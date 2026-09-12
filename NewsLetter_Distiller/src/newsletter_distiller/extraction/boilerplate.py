"""Mechanical boilerplate stripping — structural rules only, no ad/content
judgment. That judgment is deferred to the AI provider integration stage.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag

# Substrings matched case-insensitively against an element's tag name, id,
# and class list. Any match removes the element (and its children) entirely.
BOILERPLATE_MARKERS = (
    "nav",
    "navbar",
    "footer",
    "pre-header",
    "preheader",
    "unsubscribe",
    "social-share",
    "share-icons",
    "sponsor-banner",
)

# An <img> at or below this size (in either dimension) is treated as a
# tracking pixel, not a content image.
TRACKING_PIXEL_MAX_DIMENSION = 2


def _matches_boilerplate(tag: Tag) -> bool:
    haystacks = [tag.name or ""]
    tag_id = tag.get("id")
    if tag_id:
        haystacks.append(tag_id)
    classes = tag.get("class") or []
    haystacks.extend(classes)

    haystack = " ".join(haystacks).lower()
    return any(marker in haystack for marker in BOILERPLATE_MARKERS)


def _is_tracking_pixel(img: Tag) -> bool:
    for attr in ("width", "height"):
        value = img.get(attr)
        if value is None:
            continue
        try:
            if int(str(value).strip()) <= TRACKING_PIXEL_MAX_DIMENSION:
                return True
        except ValueError:
            continue
    return False


def strip_boilerplate(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove structural boilerplate elements and tracking-pixel images
    from `soup` in place, and return it for convenient chaining.
    """
    for tag in soup.find_all(True):
        if tag.decomposed:
            continue
        if _matches_boilerplate(tag):
            tag.decompose()

    for img in soup.find_all("img"):
        if _is_tracking_pixel(img):
            img.decompose()

    return soup
