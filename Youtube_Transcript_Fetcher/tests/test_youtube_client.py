from unittest.mock import MagicMock, patch

import pytest

import youtube_client
from youtube_client import TranscriptFetchError, get_video_id


class TestGetVideoId:
    def test_watch_url(self):
        assert get_video_id("https://www.youtube.com/watch?v=abc123XYZ_-") == "abc123XYZ_-"

    def test_watch_url_with_extra_params(self):
        assert get_video_id("https://www.youtube.com/watch?v=abc123XYZ_-&t=42s") == "abc123XYZ_-"

    def test_youtu_be_url(self):
        assert get_video_id("https://youtu.be/abc123XYZ_-") == "abc123XYZ_-"

    def test_youtu_be_url_with_query_string(self):
        # Regression test: the original script kept "?t=60" as part of the ID.
        assert get_video_id("https://youtu.be/abc123XYZ_-?t=60") == "abc123XYZ_-"

    def test_embed_url(self):
        assert get_video_id("https://www.youtube.com/embed/abc123XYZ_-") == "abc123XYZ_-"

    def test_shorts_url(self):
        assert get_video_id("https://www.youtube.com/shorts/abc123XYZ_-") == "abc123XYZ_-"

    def test_bare_video_id(self):
        assert get_video_id("abc123XYZ_-") == "abc123XYZ_-"

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            get_video_id("https://example.com/not-youtube")


class TestFetchMetadata:
    @patch("youtube_client.yt_dlp.YoutubeDL")
    def test_with_chapters(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "My Video",
            "duration": 600,
            "chapters": [
                {"title": "Intro", "start_time": 0, "end_time": 60},
                {"title": "Main Topic", "start_time": 60, "end_time": 600},
            ],
        }
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        metadata = youtube_client.fetch_metadata("abc123XYZ_-")

        assert metadata.title == "My Video"
        assert metadata.duration_seconds == 600
        assert len(metadata.chapters) == 2
        assert metadata.chapters[0].title == "Intro"
        assert metadata.chapters[1].end_seconds == 600

    @patch("youtube_client.yt_dlp.YoutubeDL")
    def test_without_chapters(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"title": "No Chapters", "duration": 120}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        metadata = youtube_client.fetch_metadata("abc123XYZ_-")

        assert metadata.chapters == []


class TestFetchTranscript:
    @patch("youtube_client.YouTubeTranscriptApi")
    def test_success(self, mock_api_class):
        snippet1 = MagicMock(text="Hello", start=0.0, duration=1.5)
        snippet2 = MagicMock(text="World", start=1.5, duration=1.5)
        mock_api_class.return_value.fetch.return_value = [snippet1, snippet2]

        transcript = youtube_client.fetch_transcript("abc123XYZ_-")

        assert transcript == [
            {"text": "Hello", "start": 0.0, "duration": 1.5},
            {"text": "World", "start": 1.5, "duration": 1.5},
        ]

    @patch("youtube_client.YouTubeTranscriptApi")
    def test_transcripts_disabled_raises_fetch_error(self, mock_api_class):
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_api_class.return_value.fetch.side_effect = TranscriptsDisabled("abc123XYZ_-")

        with pytest.raises(TranscriptFetchError):
            youtube_client.fetch_transcript("abc123XYZ_-")
