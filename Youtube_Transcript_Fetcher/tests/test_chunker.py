from unittest.mock import patch

import pytest

import chunker
from youtube_client import Chapter


class TestFormatTranscriptWithTimestamps:
    def test_formats_lines(self):
        transcript = [
            {"text": "Hello", "start": 0.0, "duration": 1.0},
            {"text": "World", "start": 1.4, "duration": 1.0},
        ]
        result = chunker.format_transcript_with_timestamps(transcript)
        assert result == "[0] Hello\n[1] World"


class TestGetChapters:
    def test_uses_real_chapters_without_calling_claude(self):
        real_chapters = [Chapter(title="Intro", start_seconds=0, end_seconds=60)]
        with patch("chunker.claude_client.infer_chapters") as mock_infer:
            result = chunker.get_chapters("Title", 60, [], real_chapters)
        mock_infer.assert_not_called()
        assert result == real_chapters

    def test_short_transcript_becomes_single_chapter(self):
        transcript = [{"text": "short", "start": 0.0, "duration": 1.0}]
        with patch("chunker.claude_client.infer_chapters") as mock_infer:
            result = chunker.get_chapters("My Video", 10, transcript, [])
        mock_infer.assert_not_called()
        assert len(result) == 1
        assert result[0].title == "My Video"
        assert result[0].end_seconds == 10

    def test_long_transcript_without_chapters_infers(self):
        long_text = "word " * 1000
        transcript = [{"text": long_text, "start": 0.0, "duration": 500.0}]
        inferred = [Chapter(title="Part 1", start_seconds=0, end_seconds=500)]
        with patch("chunker.claude_client.infer_chapters", return_value=inferred) as mock_infer:
            result = chunker.get_chapters("My Video", 500, transcript, [])
        mock_infer.assert_called_once()
        assert result == inferred


class TestBucketTranscriptByChapters:
    def test_buckets_snippets_by_time_range(self):
        chapters = [
            Chapter(title="Intro", start_seconds=0, end_seconds=10),
            Chapter(title="Body", start_seconds=10, end_seconds=20),
        ]
        transcript = [
            {"text": "a", "start": 1.0, "duration": 1.0},
            {"text": "b", "start": 9.0, "duration": 1.0},
            {"text": "c", "start": 11.0, "duration": 1.0},
            {"text": "d", "start": 25.0, "duration": 1.0},  # past the last chapter's end
        ]
        result = chunker.bucket_transcript_by_chapters(transcript, chapters)
        assert result[0] == (chapters[0], "a b")
        assert result[1] == (chapters[1], "c d")


class TestSplitOversizedChunks:
    def test_chunk_under_limit_passes_through(self):
        chapter = Chapter(title="Small", start_seconds=0, end_seconds=10)
        with patch("chunker.claude_client.count_tokens", return_value=100):
            result = chunker.split_oversized_chunks([(chapter, "some text")])
        assert result == [(chapter, "some text")]

    def test_chunk_over_limit_gets_split(self):
        chapter = Chapter(title="Big", start_seconds=0, end_seconds=100)
        text = " ".join(f"word{i}" for i in range(100))
        with patch("chunker.claude_client.count_tokens", return_value=chunker.config.MAX_CHAPTER_TOKENS * 3):
            result = chunker.split_oversized_chunks([(chapter, text)])
        assert len(result) == 3
        assert result[0][0].title == "Big (part 1/3)"
        assert result[0][0].start_seconds == 0
        assert result[1][0].start_seconds == pytest.approx(100 / 3)
        assert result[2][0].end_seconds == pytest.approx(100)

    def test_empty_chunk_is_skipped(self):
        chapter = Chapter(title="Empty", start_seconds=0, end_seconds=10)
        result = chunker.split_oversized_chunks([(chapter, "   ")])
        assert result == []
