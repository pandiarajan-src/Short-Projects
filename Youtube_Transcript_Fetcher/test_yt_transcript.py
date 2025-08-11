"""
Unit tests for yt_transcript.py.
"""

# Ensure the script directory is in the Python path for imports
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yt_transcript
import unittest
from unittest.mock import patch, MagicMock, mock_open


class TestMainFunction(unittest.TestCase):
    """Unit tests for the main function in yt_transcript.py."""
    @patch("yt_transcript.YouTubeTranscriptApi")
    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_main_success(self, mock_print, mock_file, mock_api_class):
        """Test successful transcript fetch and file write."""
        test_args = ["yt_transcript.py", "https://youtu.be/abc123", "output.txt"]
        with patch.object(sys, "argv", test_args):
            mock_api_instance = MagicMock()
            mock_transcript = [MagicMock(text="Hello"), MagicMock(text="World")]
            mock_api_instance.fetch.return_value = mock_transcript
            mock_api_class.return_value = mock_api_instance

            yt_transcript.main()

            mock_api_instance.fetch.assert_called_once_with("abc123")
            mock_file.assert_called_once_with("output.txt", "w", encoding="utf-8")
            handle = mock_file()
            handle.write.assert_any_call("Hello\n")
            handle.write.assert_any_call("World\n")
            mock_print.assert_any_call("Transcript saved to output.txt")

    @patch("builtins.print")
    def test_main_missing_args(self, mock_print):
        """Test script exits with usage message if arguments are missing."""
        test_args = ["yt_transcript.py"]
        with patch.object(sys, "argv", test_args), \
             self.assertRaises(SystemExit) as cm:
            yt_transcript.main()
        mock_print.assert_called_with(yt_transcript.USAGE)
        self.assertEqual(cm.exception.code, 1)

    @patch("yt_transcript.YouTubeTranscriptApi")
    @patch("builtins.print")
    def test_main_transcript_error(self, mock_print, mock_api_class):
        """Test error handling for TranscriptsDisabled exception."""
        test_args = ["yt_transcript.py", "abc123", "output.txt"]
        with patch.object(sys, "argv", test_args):
            mock_api_instance = MagicMock()
            mock_api_instance.fetch.side_effect = yt_transcript.TranscriptsDisabled("Disabled")
            mock_api_class.return_value = mock_api_instance
            with self.assertRaises(SystemExit) as cm:
                yt_transcript.main()
            self.assertTrue(any(
                "Error:" in str(call_args[0][0]) and "Disabled" in str(call_args[0][0])
                for call_args in mock_print.call_args_list
            ))
            self.assertEqual(cm.exception.code, 1)

    @patch("yt_transcript.YouTubeTranscriptApi")
    @patch("builtins.print")
    def test_main_no_transcript_found(self, mock_print, mock_api_class):
        """Test error handling for NoTranscriptFound exception."""
        test_args = ["yt_transcript.py", "abc123", "output.txt"]
        with patch.object(sys, "argv", test_args):
            mock_api_instance = MagicMock()
            video_id = "abc123"
            requested_language_codes = ["en"]
            transcript_data = {}
            mock_api_instance.fetch.side_effect = yt_transcript.NoTranscriptFound(
                video_id, requested_language_codes, transcript_data
            )
            mock_api_class.return_value = mock_api_instance
            with self.assertRaises(SystemExit) as cm:
                yt_transcript.main()
            self.assertTrue(any(
                "Error:" in str(call_args[0][0]) for call_args in mock_print.call_args_list
            ))
            self.assertEqual(cm.exception.code, 1)

    @patch("yt_transcript.YouTubeTranscriptApi")
    @patch("builtins.print")
    def test_main_video_unavailable(self, mock_print, mock_api_class):
        """Test error handling for VideoUnavailable exception."""
        test_args = ["yt_transcript.py", "abc123", "output.txt"]
        with patch.object(sys, "argv", test_args):
            mock_api_instance = MagicMock()
            mock_api_instance.fetch.side_effect = yt_transcript.VideoUnavailable("Unavailable")
            mock_api_class.return_value = mock_api_instance
            with self.assertRaises(SystemExit) as cm:
                yt_transcript.main()
            self.assertTrue(any(
                "Error:" in str(call_args[0][0]) and "Unavailable" in str(call_args[0][0])
                for call_args in mock_print.call_args_list
            ))
            self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
