#!/usr/bin/env python3
"""
Module to fetch and save YouTube video transcripts using youtube_transcript_api.
"""

import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

def get_video_id(url_or_id: str) -> str:
    """Extract the video ID from a YouTube URL or return the ID if already provided."""
    if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
        # Example formats: https://youtu.be/VIDEOID or https://www.youtube.com/watch?v=VIDEOID
        if "v=" in url_or_id:
            return url_or_id.split("v=")[1].split("&")[0]
        return url_or_id.rstrip("/").split("/")[-1]
    return url_or_id  # Already an ID

USAGE = "Usage: python yt_transcript.py <YouTube URL or ID> <output_file.txt/md>"

def main():
    """
    Main entry point for the script.

    Parses command-line arguments to fetch the transcript of a YouTube video and save it to a specified output file.
    Handles errors related to unavailable transcripts or videos, and prints appropriate error messages.
    """
    """Main entry point for the script."""
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(1)

    video_id = get_video_id(sys.argv[1])
    output_file = sys.argv[2]
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    with open(output_file, "w", encoding="utf-8") as file_handle:
        for entry in transcript:
            file_handle.write(entry.text + "\n")

    print(f"Transcript saved to {output_file}")

if __name__ == "__main__":
    main()
