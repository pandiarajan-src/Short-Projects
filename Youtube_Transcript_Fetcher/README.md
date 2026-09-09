# YouTube Transcript Fetcher

A small command-line tool that downloads the transcript/captions of a YouTube video and saves it to a text or markdown file.

## Features

- Accepts a full YouTube URL (`youtube.com/watch?v=...` or `youtu.be/...`) or a bare video ID
- Saves the transcript as plain text, one caption entry per line
- Clear error messages when a video has no transcript, transcripts are disabled, or the video is unavailable

## Requirements

- Python 3.7+
- [`youtube_transcript_api`](https://pypi.org/project/youtube-transcript-api/)

## Installation

```bash
pip install youtube-transcript-api
```

No other setup is required — the tool is a single script.

## Usage

```bash
python yt_transcript.py <YouTube URL or ID> <output_file.txt/md>
```

### Examples

```bash
# Using a full URL
python yt_transcript.py https://www.youtube.com/watch?v=dQw4w9WgXcQ transcript.txt

# Using a short URL
python yt_transcript.py https://youtu.be/dQw4w9WgXcQ transcript.txt

# Using just the video ID
python yt_transcript.py dQw4w9WgXcQ transcript.md
```

On success, the transcript text is written to the output file (one line per caption entry) and the script prints:

```
Transcript saved to transcript.txt
```

## Error Handling

If a transcript can't be fetched, the script prints an error and exits with a non-zero status. This happens when:

- **Transcripts are disabled** for the video
- **No transcript is found** for the requested video/language
- **The video is unavailable** (private, deleted, region-locked, etc.)

## Running Tests

Unit tests are included in [test_yt_transcript.py](test_yt_transcript.py) and use Python's built-in `unittest` framework with mocked API calls (no network access needed).

```bash
python -m unittest test_yt_transcript.py -v
```

## Project Structure

```
Youtube_Transcript_Fetcher/
├── yt_transcript.py       # Main script: fetches and saves transcripts
├── test_yt_transcript.py  # Unit tests
└── README.md
```

## How It Works

1. Parses the video URL/ID from the command line to extract the raw YouTube video ID.
2. Calls `YouTubeTranscriptApi().fetch(video_id)` to retrieve the transcript.
3. Writes each transcript entry's text to the specified output file, one per line.
