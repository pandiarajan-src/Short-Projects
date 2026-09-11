"""Fetches video metadata and transcripts from YouTube."""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class TranscriptFetchError(Exception):
    """Raised when a transcript cannot be fetched for a video."""


@dataclass
class Chapter:
    title: str
    start_seconds: float
    end_seconds: float


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    duration_seconds: float
    chapters: list[Chapter]


def get_video_id(url_or_id: str) -> str:
    """Extract the 11-character video ID from a YouTube URL, or return it
    unchanged if it already looks like a bare video ID."""
    candidate = url_or_id.strip()

    if VIDEO_ID_RE.match(candidate):
        return candidate

    parsed = urlparse(candidate)
    host = parsed.netloc.lower()

    if "youtu.be" in host:
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif "youtube.com" in host:
        if parsed.path in ("/watch",):
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/embed/") or parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
        else:
            video_id = parse_qs(parsed.query).get("v", [""])[0]
    else:
        video_id = ""

    if not VIDEO_ID_RE.match(video_id):
        raise ValueError(f"Could not extract a valid YouTube video ID from: {url_or_id!r}")

    return video_id


def fetch_metadata(video_id: str) -> VideoMetadata:
    """Fetch title, duration, and chapter markers via yt-dlp (no download)."""
    # We only need metadata, never playable formats, so a video with no
    # resolvable formats (age/region locks, live-stream quirks, YouTube
    # anti-bot friction, etc.) should still yield title/duration/chapters
    # instead of raising.
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

    raw_chapters = info.get("chapters") or []
    chapters = [
        Chapter(
            title=c.get("title", "Untitled chapter"),
            start_seconds=float(c["start_time"]),
            end_seconds=float(c["end_time"]),
        )
        for c in raw_chapters
    ]

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title", video_id),
        duration_seconds=float(info.get("duration") or 0),
        chapters=chapters,
    )


def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch the timestamped transcript as a list of
    {"text", "start", "duration"} dicts."""
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        raise TranscriptFetchError(str(exc)) from exc

    return [
        {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
        for snippet in fetched
    ]
