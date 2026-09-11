"""Configuration for the transcript-to-study-notes pipeline.

All model/runtime knobs live here so they can be tuned without touching
pipeline code. Prompt text lives in prompts.py, not here.
"""

import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Model & generation settings
MODEL = "claude-sonnet-4-6"
EFFORT = "medium"  # low | medium | high | max
CHAPTER_GENERATION_MAX_TOKENS = 8000
CHAPTER_INFERENCE_MAX_TOKENS = 8000
THINKING = {"type": "adaptive"}

# Chunking
# Chapters whose transcript text exceeds this many tokens are sub-split
# before being sent to Claude, to keep each generation call fast and focused.
MAX_CHAPTER_TOKENS = 50_000
# Minimum number of transcript characters in a chapter before it's worth
# asking Claude to infer sub-chapters at all (very short videos stay as one).
MIN_CHARS_FOR_CHAPTER_INFERENCE = 2_000

# Output
OUTPUT_DIR_NAME = "ClaudeOutput"

# Web search tool used during chapter generation so reference links are real
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}
