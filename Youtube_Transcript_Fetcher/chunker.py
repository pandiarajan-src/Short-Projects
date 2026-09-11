"""Splits a video's transcript into per-chapter chunks ready for Claude."""

import math

import claude_client
import config
from youtube_client import Chapter


def format_transcript_with_timestamps(transcript: list[dict]) -> str:
    """Render transcript snippets as "[start_seconds] text" lines."""
    lines = [f"[{snippet['start']:.0f}] {snippet['text']}" for snippet in transcript]
    return "\n".join(lines)


def get_chapters(video_title: str, duration_seconds: float, transcript: list[dict], real_chapters: list[Chapter]) -> list[Chapter]:
    """Return real YouTube chapters if present, else infer them with Claude.
    Very short transcripts skip inference entirely and become one chapter."""
    if real_chapters:
        return real_chapters

    full_text = " ".join(snippet["text"] for snippet in transcript)
    if len(full_text) < config.MIN_CHARS_FOR_CHAPTER_INFERENCE:
        return [Chapter(title=video_title, start_seconds=0.0, end_seconds=duration_seconds)]

    timestamped_text = format_transcript_with_timestamps(transcript)
    return claude_client.infer_chapters(video_title, duration_seconds, timestamped_text)


def bucket_transcript_by_chapters(transcript: list[dict], chapters: list[Chapter]) -> list[tuple[Chapter, str]]:
    """Assign each transcript snippet to the chapter whose time range
    contains its start time, and join each chapter's snippets into text."""
    buckets: list[list[str]] = [[] for _ in chapters]

    for snippet in transcript:
        start = snippet["start"]
        chapter_index = _find_chapter_index(start, chapters)
        buckets[chapter_index].append(snippet["text"])

    return [(chapter, " ".join(text_parts)) for chapter, text_parts in zip(chapters, buckets)]


def _find_chapter_index(start_time: float, chapters: list[Chapter]) -> int:
    for index, chapter in enumerate(chapters):
        if chapter.start_seconds <= start_time < chapter.end_seconds:
            return index
    # Snippet falls after the last chapter's end (rounding at the tail) — keep it.
    return len(chapters) - 1


def split_oversized_chunks(chunks: list[tuple[Chapter, str]]) -> list[tuple[Chapter, str]]:
    """Sub-split any chapter whose transcript text exceeds the configured
    token budget, so each Claude call stays fast and focused."""
    result: list[tuple[Chapter, str]] = []

    for chapter, text in chunks:
        if not text.strip():
            continue
        token_count = claude_client.count_tokens(text)
        if token_count <= config.MAX_CHAPTER_TOKENS:
            result.append((chapter, text))
            continue

        num_parts = math.ceil(token_count / config.MAX_CHAPTER_TOKENS)
        words = text.split()
        words_per_part = math.ceil(len(words) / num_parts)
        span = chapter.end_seconds - chapter.start_seconds

        for part_index in range(num_parts):
            part_words = words[part_index * words_per_part : (part_index + 1) * words_per_part]
            if not part_words:
                continue
            part_start = chapter.start_seconds + span * (part_index / num_parts)
            part_end = chapter.start_seconds + span * ((part_index + 1) / num_parts)
            sub_chapter = Chapter(
                title=f"{chapter.title} (part {part_index + 1}/{num_parts})",
                start_seconds=part_start,
                end_seconds=part_end,
            )
            result.append((sub_chapter, " ".join(part_words)))

    return result
