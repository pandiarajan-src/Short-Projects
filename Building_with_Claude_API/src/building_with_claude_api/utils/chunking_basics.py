"""

"""
import re
from pathlib import Path

def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    """
    Chunk by a set number of charactesr
    """
    chunks = []
    start_idx = 0

    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))

        chunk_text = text[start_idx:end_idx]
        chunks.append(chunk_text)

        start_idx = (
            end_idx - chunk_overlap if end_idx < len(text) else len(text)
        )

    return chunks

def chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1):
    """
    # Chunk by sentence
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    start_idx = 0

    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))

        current_chunk = sentences[start_idx:end_idx]
        chunks.append(" ".join(current_chunk))

        start_idx += max_sentences_per_chunk - overlap_sentences

        if start_idx < 0:
            start_idx = 0

    return chunks

def chunk_by_section(document_text):
    """
    # Chunk by section
    # """
    pattern = r"\n## "
    return re.split(pattern, document_text)


if __name__ == "__main__":

    file = Path(__file__).resolve().parent.parent / "report.md"
    if file.exists():
        with open(file, "r") as f:
            text = f.read()
        chunks = chunk_by_char(text=text, chunk_size=300, chunk_overlap=20)
        [print(chunk + "\n----\n") for chunk in chunks]

        sentense_chunks = chunk_by_sentence(text, max_sentences_per_chunk=10, overlap_sentences=2)
        [print(sentense_chunk + "\n----\n") for sentense_chunk in sentense_chunks]

        section_chunks = chunk_by_section(text)
        [print(section_chunk + "\n----\n") for section_chunk in section_chunks]
    else:
        print(f"File doesn't exists: {file.absolute()}")