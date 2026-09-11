"""Thin wrapper around the Anthropic SDK for this pipeline's two call sites:
inferring chapters when a video has none, and generating a study-guide
section for a single chapter."""

import json
import time

import anthropic
import httpx

import config
import prompts
from youtube_client import Chapter

_client = None

# Mid-stream network hiccups (idle read timeouts, dropped connections) surface
# as raw httpx exceptions rather than the SDK's typed APIConnectionError, since
# they occur while iterating the response body rather than on initial connect.
_TRANSIENT_STREAM_ERRORS = (anthropic.APIConnectionError, httpx.TransportError)
_STREAM_RETRY_ATTEMPTS = 3
_STREAM_RETRY_BASE_DELAY_SECONDS = 2

CHAPTER_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_seconds": {"type": "number"},
                    "end_seconds": {"type": "number"},
                },
                "required": ["title", "start_seconds", "end_seconds"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["chapters"],
    "additionalProperties": False,
}


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def count_tokens(text: str) -> int:
    response = get_client().messages.count_tokens(
        model=config.MODEL,
        messages=[{"role": "user", "content": text}],
    )
    return response.input_tokens


def infer_chapters(video_title: str, duration_seconds: float, transcript_text: str) -> list[Chapter]:
    """Ask Claude to split a chapterless video's transcript into chapters."""
    duration_label = _format_timestamp(duration_seconds)
    user_content = prompts.CHAPTER_INFERENCE_USER_TEMPLATE.format(
        video_title=video_title,
        duration_label=duration_label,
        transcript_text=transcript_text,
    )

    response = get_client().messages.create(
        model=config.MODEL,
        max_tokens=config.CHAPTER_INFERENCE_MAX_TOKENS,
        thinking=config.THINKING,
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": CHAPTER_LIST_SCHEMA},
        },
        system=prompts.CHAPTER_INFERENCE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    text = next(block.text for block in response.content if block.type == "text")
    data = json.loads(text)
    return [
        Chapter(
            title=c["title"],
            start_seconds=float(c["start_seconds"]),
            end_seconds=float(c["end_seconds"]),
        )
        for c in data["chapters"]
    ]


def generate_chapter_section(video_title: str, chapter: Chapter, transcript_text: str) -> str:
    """Generate the enriched Markdown study-guide section for one chapter."""
    user_content = prompts.CHAPTER_GENERATION_USER_TEMPLATE.format(
        video_title=video_title,
        chapter_title=chapter.title,
        start_label=_format_timestamp(chapter.start_seconds),
        end_label=_format_timestamp(chapter.end_seconds),
        transcript_text=transcript_text,
    )

    message = _stream_with_retry(user_content)

    text = "\n\n".join(block.text for block in message.content if block.type == "text").strip()
    return _strip_preamble(text)


def _strip_preamble(text: str) -> str:
    """Drop any narration Claude wrote before its first '## ' heading (e.g.
    "Now I have enough information to write the study guide...") — this
    shows up often when the web_search tool is used, despite the system
    prompt asking for no preamble, so it's enforced defensively here too."""
    heading_index = text.find("\n## ")
    if text.startswith("## "):
        return text
    if heading_index != -1:
        return text[heading_index + 1 :]
    return text


def _stream_with_retry(user_content: str):
    """Run the chapter-generation stream, retrying on transient network
    errors (idle read timeouts, dropped connections) with backoff — a single
    flaky connection shouldn't fail an otherwise-successful multi-hour run."""
    last_error = None
    for attempt in range(_STREAM_RETRY_ATTEMPTS):
        try:
            with get_client().messages.stream(
                model=config.MODEL,
                max_tokens=config.CHAPTER_GENERATION_MAX_TOKENS,
                thinking=config.THINKING,
                output_config={"effort": config.EFFORT},
                tools=[config.WEB_SEARCH_TOOL],
                system=[
                    {
                        "type": "text",
                        "text": prompts.CHAPTER_GENERATION_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                return stream.get_final_message()
        except _TRANSIENT_STREAM_ERRORS as exc:
            last_error = exc
            if attempt < _STREAM_RETRY_ATTEMPTS - 1:
                time.sleep(_STREAM_RETRY_BASE_DELAY_SECONDS * (2**attempt))

    raise last_error


def _format_timestamp(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
