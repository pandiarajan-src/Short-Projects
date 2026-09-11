from unittest.mock import MagicMock, patch

import httpx
import pytest

import claude_client


class TestStripPreamble:
    def test_removes_narration_before_heading(self):
        text = "Now I have enough information to write the study guide. Here it is:\n\n## Chapter 1 – Intro\n\nBody"
        assert claude_client._strip_preamble(text) == "## Chapter 1 – Intro\n\nBody"

    def test_leaves_clean_response_unchanged(self):
        text = "## Chapter 1 – Intro\n\nBody"
        assert claude_client._strip_preamble(text) == text

    def test_no_heading_found_returns_original(self):
        text = "Just some text with no heading at all"
        assert claude_client._strip_preamble(text) == text


class TestFormatTimestamp:
    def test_minutes_and_seconds(self):
        assert claude_client._format_timestamp(65) == "1:05"

    def test_hours_minutes_seconds(self):
        assert claude_client._format_timestamp(3725) == "1:02:05"

    def test_zero(self):
        assert claude_client._format_timestamp(0) == "0:00"


class TestStreamWithRetry:
    def _mock_stream_cm(self, final_message):
        cm = MagicMock()
        cm.__enter__.return_value.get_final_message.return_value = final_message
        cm.__exit__.return_value = False
        return cm

    @patch("claude_client.time.sleep")
    @patch("claude_client.get_client")
    def test_succeeds_first_try(self, mock_get_client, mock_sleep):
        final_message = MagicMock()
        mock_get_client.return_value.messages.stream.return_value = self._mock_stream_cm(final_message)

        result = claude_client._stream_with_retry("some content")

        assert result is final_message
        mock_sleep.assert_not_called()

    @patch("claude_client.time.sleep")
    @patch("claude_client.get_client")
    def test_retries_on_transient_network_error_then_succeeds(self, mock_get_client, mock_sleep):
        final_message = MagicMock()
        mock_get_client.return_value.messages.stream.side_effect = [
            httpx.ReadTimeout("timed out"),
            self._mock_stream_cm(final_message),
        ]

        result = claude_client._stream_with_retry("some content")

        assert result is final_message
        mock_sleep.assert_called_once()

    @patch("claude_client.time.sleep")
    @patch("claude_client.get_client")
    def test_reraises_after_exhausting_retries(self, mock_get_client, mock_sleep):
        mock_get_client.return_value.messages.stream.side_effect = httpx.ReadTimeout("timed out")

        with pytest.raises(httpx.ReadTimeout):
            claude_client._stream_with_retry("some content")

        assert mock_get_client.return_value.messages.stream.call_count == claude_client._STREAM_RETRY_ATTEMPTS
