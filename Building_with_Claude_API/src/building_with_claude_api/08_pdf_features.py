"""
"""

from pathlib import Path
from building_with_claude_api.utils.llm_messages import (
    add_pdf_to_user_message,
    chat,
    chat_internal,
)

prompt = """
    1. Read, understand the document.
    2. Extract the images available in the pdf and send me the png. If you have more than one image send them all as seperate image blocks.
    3. Summarize the rest of the text in 5 bullet points
    4. Respond with JSON output
"""

if __name__ == "__main__":
    messages = []
    image_path = Path(__file__).resolve().parent / "pdfs/earth.pdf"
    add_pdf_to_user_message(messages, image_path, prompt)
    response = chat_internal(messages, model="claude-sonnet-4-5")
    print(response)