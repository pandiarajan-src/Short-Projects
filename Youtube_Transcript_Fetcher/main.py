#!/usr/bin/env python3
"""CLI entry point: fetch a YouTube video's transcript, enrich it with
Claude into a beginner-friendly Markdown study guide split by chapter, and
write it to ClaudeOutput/<Video Title>.md.

Usage: python main.py <YouTube URL or ID>
"""

import sys
from pathlib import Path

import anthropic
import httpx

import assembler
import chunker
import claude_client
import config
import youtube_client

USAGE = "Usage: python main.py <YouTube URL or ID>"


def run(url_or_id: str) -> Path:
    video_id = youtube_client.get_video_id(url_or_id)
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print(f"Fetching metadata for {video_url} ...")
    metadata = youtube_client.fetch_metadata(video_id)

    print(f"Fetching transcript for '{metadata.title}' ...")
    transcript = youtube_client.fetch_transcript(video_id)

    print("Determining chapters ...")
    chapters = chunker.get_chapters(metadata.title, metadata.duration_seconds, transcript, metadata.chapters)
    print(f"Found {len(chapters)} chapter(s).")

    chunks = chunker.bucket_transcript_by_chapters(transcript, chapters)
    chunks = chunker.split_oversized_chunks(chunks)

    sections = []
    for index, (chapter, text) in enumerate(chunks, start=1):
        print(f"Generating section {index}/{len(chunks)}: {chapter.title}")
        try:
            body = claude_client.generate_chapter_section(metadata.title, chapter, text)
        except (anthropic.APIError, httpx.TransportError) as exc:
            print(f"  Skipping '{chapter.title}' after generation error: {exc}")
            continue
        sections.append((chapter, body))

    if not sections:
        raise RuntimeError("No chapter sections were generated successfully.")

    document = assembler.build_document(metadata.title, video_url, sections)

    output_dir = Path(__file__).parent / config.OUTPUT_DIR_NAME
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{assembler.sanitize_filename(metadata.title)}.md"
    output_path.write_text(document, encoding="utf-8")

    print(f"Study guide saved to {output_path}")
    return output_path


def main() -> None:
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    try:
        run(sys.argv[1])
    except (youtube_client.TranscriptFetchError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
