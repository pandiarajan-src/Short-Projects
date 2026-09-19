"""

"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from .chunking_basics import chunk_by_section

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY", "missing-api-key")
EMBEDDING_MODEL = os.getenv("OPEN_ROUTER_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")

EMBED_CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Embedding Generation
def generate_embedding(text, model=EMBEDDING_MODEL, input_type="query"):
    result = EMBED_CLIENT.embeddings.create(
        input=[text], model=model, extra_body={"input_type": input_type}
    )

    vector = result.data[0].embedding
    return vector


if __name__ == "__main__":
    file = Path(__file__).resolve().parent.parent / "report.md"
    if file.exists():
        with open(file, "r") as f:
            text = f.read()

        section_chunks = chunk_by_section(text)
        for section_chunk in section_chunks:
            chunk_vector = generate_embedding(section_chunk)
            print(f"Chunk Text: {section_chunk}")
            print(f"Chunk Vector: {chunk_vector}")
            print(f"========"*3)





