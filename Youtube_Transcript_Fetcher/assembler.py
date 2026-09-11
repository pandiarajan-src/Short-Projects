"""Deterministic Markdown assembly — no API calls, pure templating."""

import re

from youtube_client import Chapter


def sanitize_filename(title: str) -> str:
    """Turn a video title into a safe filename (without extension)."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "", title).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Untitled Video"


def _slugify(title: str) -> str:
    """Approximate a GitHub-style Markdown heading anchor slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def _extract_heading(body: str, fallback_title: str) -> str:
    """Return the text of a section's first level-2 (##) heading.

    Claude is asked to open each section with "## <chapter title>", but it
    often paraphrases the title we gave it rather than repeating it verbatim.
    The table of contents must link to whatever heading actually ended up in
    the document, so it's derived from the body itself instead of the
    pre-generation Chapter object — otherwise the two silently drift apart
    and every TOC link breaks.
    """
    for line in body.splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return fallback_title


def build_document(video_title: str, video_url: str, sections: list[tuple[Chapter, str]]) -> str:
    """Assemble the final Markdown document: title, video link, table of
    contents, then each chapter's generated section in order."""
    lines = [f"# {video_title}", "", f"**Video:** {video_url}", "", "## Table of Contents"]

    headings = [_extract_heading(body, chapter.title) for chapter, body in sections]
    for heading in headings:
        anchor = _slugify(heading)
        lines.append(f"- [{heading}](#{anchor})")

    lines.append("")

    for _, body in sections:
        lines.append(body)
        lines.append("")

    return "\n".join(lines).strip() + "\n"
