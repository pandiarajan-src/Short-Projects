"""
chroma_semantic_search.py
=========================================
Semantic (dense vector) search with ChromaDB's in-memory client.

WHAT "IN-MEMORY" MEANS
----------------------
`chromadb.EphemeralClient()` keeps everything in RAM. Nothing is written to
disk, and the data vanishes when the script exits. Perfect for learning and
tests. Swap in `PersistentClient(path="./chroma_db")` when you want it to last.

EMBEDDINGS
----------
We use Chroma's *default* embedding function: all-MiniLM-L6-v2, a small model
that runs locally via ONNX. No API key, no VoyageAI account. The model
(~80 MB) is downloaded once on first run and cached afterwards.

SETUP
-----
    pip install chromadb

RUN
---
    uv run python chroma_semantic_search.py
"""

import re
from pathlib import Path
from typing import Any, Dict, List
from building_with_claude_api.utils.chunking_basics import chunk_by_section

import chromadb

# ---------------------------------------------------------------------------
# 1. Chunking is available from export from chunking_basics.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 2. Build the in-memory Chroma collection
# ---------------------------------------------------------------------------
def build_collection(chunks: List[str], name: str = "report_chunks"):
    """Create a RAM-only collection and load the chunks into it.

    Three things happen implicitly here, each of which was manual code in the
    notebook:
      1. Every document is embedded (Chroma calls the embedding function).
      2. Vectors are stored in an HNSW index for fast nearest-neighbour lookup.
      3. Cosine distance is used for comparison.
    """
    # EphemeralClient == RAM only. Nothing touches your disk.
    client = chromadb.EphemeralClient()

    # A "collection" is Chroma's equivalent of a table. Deleting first makes
    # the script safe to re-run inside a notebook or REPL.
    collection = client.get_or_create_collection(
        name=name,
        # "cosine" matches the notebook's VectorIndex default. Chroma's own
        # default is "l2" (Euclidean), so we set it explicitly.
        configuration={"hnsw": {"space": "cosine"}},
        # No embedding_function argument => Chroma uses all-MiniLM-L6-v2.
    )

    # IDs are required and must be unique. We also attach metadata: the first
    # line of each chunk, which doubles as a human-readable section title.
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[
            {"section": chunk.splitlines()[0][:60], "position": i}
            for i, chunk in enumerate(chunks)
        ],
    )

    print(f"Indexed {collection.count()} chunks in memory\n")
    return collection


# ---------------------------------------------------------------------------
# 3. Search
# ---------------------------------------------------------------------------
def search(collection, query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Semantic search. Chroma embeds the query and finds the nearest chunks.

    Note what you do NOT write: no embedding call, no distance maths, no sort.
    """
    results = collection.query(
        query_texts=[query],           # a list, because you can batch queries
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns parallel lists nested one level deep (one entry per query
    # in query_texts). We asked one question, so we read index [0] everywhere.
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append(
            {
                "content": doc,
                "metadata": meta,
                "distance": dist,
                # With cosine space, distance is in [0, 2] and *lower is
                # better*. Similarity is the intuitive flip of it.
                "similarity": 1 - dist,
            }
        )
    return hits


def print_hits(query: str, hits: List[Dict[str, Any]]) -> None:
    print(f"QUERY: {query}")
    print("-" * 70)
    for rank, hit in enumerate(hits, start=1):
        preview = hit["content"].replace("\n", " ")[:110]
        print(f"{rank}. similarity={hit['similarity']:.3f}  "
              f"section={hit['metadata']['section']!r}")
        print(f"   {preview}...")
    print()


# ---------------------------------------------------------------------------
# 4. Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Get the chunks to load
    report_path = Path(__file__).resolve().parent.parent / "report.md"
    with open(report_path, "r") as f:
        report_text = f.read()
    chunks = chunk_by_section(report_text)

    # Build the ChromaDB RAG collection from chunks
    collection = build_collection(chunks=chunks)

    # Get the query from user
    user_query = input("Enter your query to search: =>")

    # Search the query to get the hit list
    hit_list = search(collection=collection, query=user_query, k=2)

    # Print the hit list
    print_hits(user_query, hits=hit_list)

    # ----------------------------------------------------------------------
    # Bonus: metadata and substring filters happen *inside* Chroma, before
    # ranking. Cheap, and something the notebook's VectorIndex could not do.
    # ----------------------------------------------------------------------
    print("Filtered search (only chunks containing the literal word 'Cybersecurity'):")
    filtered = collection.query(
        query_texts=["Cybersecurity Operations"],
        n_results=2,
        where_document={"$contains": "Cybersecurity"},
    )
    print(filtered["ids"], "\n")

    # ----------------------------------------------------------------------
    # WHERE SEMANTIC SEARCH FAILS
    # ----------------------------------------------------------------------
    # Try an exact identifier, a product code, or a rare proper noun. Dense
    # embeddings smooth meaning together, so "INC-2023-Q4-011" and
    # "INC-2026-Q4-011" look almost identical to the model. That blind spot is
    # exactly what BM25 fixes -- see bm25_keyword_search.py.
    print_hits("INC-2026-Q4-011", search(collection, "INC-2023-Q4-011", k=2))

