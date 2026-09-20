"""
07_RAG_semantic_BM25_Hybrid_excercise.py
=========================================
A learning-focused walkthrough of the full RAG (Retrieval-Augmented
Generation) pipeline:

    LOAD -> CHUNK -> EMBED -> STORE -> SEARCH -> ASSEMBLE -> (GENERATE)

Nothing new is implemented here. Every step calls a function that already
exists in utils/ -- this file's only job is to show, in order, how those
pieces click together to form a RAG system. Read it top to bottom once,
then run it.

THE SIX STEPS
--------------
1. LOAD    - read the raw source document from disk.
             utils/chunking_basics.py reads report.md in its own __main__,
             we do the same thing here explicitly.

2. CHUNK   - split the document into retrievable pieces.
             utils.chunking_basics.chunk_by_section()

3. EMBED   - turn a chunk of text into a vector of numbers that captures
             its *meaning*. We call this once, directly, just so you SEE a
             raw embedding vector -- in step 4, Chroma will do this same
             work for every chunk automatically (with a different, local
             model, so it doesn't need an API key).
             utils.embeddings.generate_embedding()

4. STORE   - persist the chunks so they can be searched later.
             Two parallel stores, because this exercise compares them:
               - a Chroma vector store   (semantic / dense)
               - a BM25 keyword index    (lexical / sparse)
             utils.chroma_semantic_search.build_collection()
             utils.bm25_keyword_search.KeywordIndex()

5. SEARCH  - given a user question, find the most relevant chunks.
             Three flavours are demoed:
               - semantic search   (meaning-based, good with paraphrasing)
               - BM25 search       (word-based, good with exact tokens/IDs)
               - hybrid search     (both, merged with Reciprocal Rank Fusion)
             utils.chroma_semantic_search.search()
             utils.bm25_keyword_search.KeywordIndex.search()
             utils.bm25_keyword_search.reciprocal_rank_fusion()

6. ASSEMBLE - stuff the retrieved chunks into a prompt template so an LLM
              can answer the question *using only that context*. This is
              the "Augmented" and "Generation" half of RAG -- retrieval is
              pointless if the model never sees what you found.

RUN
---
    uv run python 07_RAG_semantic_BM25_Hybrid_excercise.py
"""

from pathlib import Path
from typing import Any, Dict, List

from building_with_claude_api.utils.chunking_basics import chunk_by_section
from building_with_claude_api.utils.embeddings import generate_embedding
from building_with_claude_api.utils.chroma_semantic_search import (
    build_collection,
    search as semantic_search,
)
from building_with_claude_api.utils.bm25_keyword_search import (
    KeywordIndex,
    reciprocal_rank_fusion,
)
from building_with_claude_api.utils.llm_messages import chat, add_user_message


# ---------------------------------------------------------------------------
# STEP 1: LOAD
# ---------------------------------------------------------------------------
def load_document(path: Path) -> str:
    """Read the raw text we are going to build a RAG system over."""
    with open(path, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# STEP 2: CHUNK
# ---------------------------------------------------------------------------
def chunk_document(text: str) -> List[str]:
    """Split on '## ' headings so each chunk is one report section.

    Why chunk at all? An LLM's context window (and a vector index) needs
    bite-sized pieces, not one giant document -- and retrieval is more
    precise when a chunk is one coherent idea rather than the whole file.
    """
    return chunk_by_section(text)


# ---------------------------------------------------------------------------
# STEP 3: EMBED (illustration only)
# ---------------------------------------------------------------------------
def demo_embed_one_chunk(chunk: str) -> None:
    """Show what an embedding actually is: a long list of floats.

    This calls OpenRouter directly, so it needs OPEN_ROUTER_API_KEY in your
    .env file. It's just for intuition -- in the STORE step below, Chroma
    embeds every chunk itself using a free local model, so this call is not
    on the critical path of the pipeline.
    """
    try:
        vector = generate_embedding(chunk)
        print(f"Chunk preview: {chunk.splitlines()[0][:60]!r}")
        print(f"Embedding vector length: {len(vector)}")
        print(f"First 8 numbers: {[round(v, 4) for v in vector[:8]]}\n")
    except Exception as exc:
        # Most likely cause: OPEN_ROUTER_API_KEY missing. Not fatal -- the
        # rest of the pipeline below uses Chroma's own local embedder.
        print(f"Skipping explicit embed demo -- {exc}\n")


# ---------------------------------------------------------------------------
# STEP 4: STORE
# ---------------------------------------------------------------------------
def store_semantic(chunks: List[str]):
    """Dense store: Chroma embeds + indexes every chunk for vector search."""
    return build_collection(chunks, name="rag_demo")


def store_lexical(chunks: List[str]) -> KeywordIndex:
    """Sparse store: BM25 indexes the raw tokens of every chunk."""
    return KeywordIndex(chunks)


# ---------------------------------------------------------------------------
# STEP 5: SEARCH
# ---------------------------------------------------------------------------
def search_semantic_only(collection, query: str, k: int = 3) -> List[Dict[str, Any]]:
    return semantic_search(collection, query, k=k)


def search_lexical_only(index: KeywordIndex, query: str, k: int = 3) -> List[Dict[str, Any]]:
    return index.search(query, k=k)


def search_hybrid(
    collection, index: KeywordIndex, chunks: List[str], query: str, k: int = 3
) -> List[Dict[str, Any]]:
    """Run both retrievers and merge their rankings with RRF.

    Each retriever returns a ranked list of chunk IDs. RRF doesn't care that
    Chroma's distances and BM25's scores live on different scales -- it only
    looks at *rank position*, so a chunk both retrievers agree on floats to
    the top.
    """
    dense_ids = [
        f"chunk_{h['metadata']['position']}"
        for h in semantic_search(collection, query, k=5)
    ]
    sparse_ids = [f"chunk_{h['position']}" for h in index.search(query, k=5)]

    fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=k)

    # Turn "chunk_3" back into its actual text so ASSEMBLE has content to work with.
    hits = []
    for entry in fused:
        position = int(entry["id"].split("_")[1])
        hits.append(
            {
                "content": chunks[position],
                "rrf_score": entry["rrf_score"],
                "position": position,
            }
        )
    return hits


# ---------------------------------------------------------------------------
# STEP 6: ASSEMBLE
# ---------------------------------------------------------------------------
def assemble_prompt(query: str, hits: List[Dict[str, Any]]) -> str:
    """Turn retrieved chunks + the user question into one final LLM prompt.

    This is the "Augmented Generation" part of RAG: the model never sees
    the whole document, only the handful of chunks retrieval decided were
    relevant. Telling it to answer ONLY from context is what keeps a RAG
    system grounded instead of hallucinating from its training data.
    """
    context = "\n\n---\n\n".join(hit["content"] for hit in hits)

    prompt = f"""Answer the question using ONLY the context below. \
If the answer isn't in the context, say you don't know.

Context:
{context}

Question: {query}

Answer:"""
    return prompt


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    # 1. LOAD ----------------------------------------------------------------
    report_path = Path(__file__).resolve().parent / "report.md"
    document_text = load_document(report_path)
    print(f"[LOAD] Read {len(document_text)} characters from {report_path.name}\n")

    # 2. CHUNK -----------------------------------------------------------------
    chunks = chunk_document(document_text)
    print(f"[CHUNK] Split into {len(chunks)} section chunks\n")

    # 3. EMBED (just a peek at chunk 0, for intuition) ------------------------
    print("[EMBED] What one chunk's embedding vector looks like:")
    demo_embed_one_chunk(chunks[0])

    # 4. STORE -----------------------------------------------------------------
    print("[STORE] Building the semantic (Chroma) store...")
    collection = store_semantic(chunks)

    print("[STORE] Building the lexical (BM25) store...")
    keyword_index = store_lexical(chunks)

    # 5. SEARCH ------------------------------------------------------------
    # query = "How is the incident INC-2023-Q4-011 related to future direction?"
    query = "How the future direction looks?"

    print("=" * 70)
    print("SEMANTIC SEARCH -- ranks by meaning, best with paraphrased questions")
    print("=" * 70)
    semantic_hits = search_semantic_only(collection, query, k=3)
    for rank, hit in enumerate(semantic_hits, start=1):
        preview = hit["content"].replace("\n", " ")[:100]
        print(f"{rank}. similarity={hit['similarity']:.3f}  {preview}...")
    print()

    print("=" * 70)
    print("BM25 (LEXICAL) SEARCH -- ranks by exact word overlap")
    print("=" * 70)
    lexical_hits = search_lexical_only(keyword_index, query, k=3)
    if lexical_hits:
        for rank, hit in enumerate(lexical_hits, start=1):
            preview = hit["content"].replace("\n", " ")[:100]
            print(f"{rank}. bm25={hit['score']:.3f}  {preview}...")
    else:
        print("   (no lexical match)")
    print()

    print("=" * 70)
    print("HYBRID SEARCH -- semantic + BM25 merged with Reciprocal Rank Fusion")
    print("=" * 70)
    hybrid_hits = search_hybrid(collection, keyword_index, chunks, query, k=3)
    for rank, hit in enumerate(hybrid_hits, start=1):
        preview = hit["content"].replace("\n", " ")[:100]
        print(f"{rank}. rrf={hit['rrf_score']:.5f}  {preview}...")
    print()

    # 6. ASSEMBLE ------------------------------------------------------------
    print("=" * 70)
    print("ASSEMBLE -- the final prompt sent to the LLM, built from hybrid hits")
    print("=" * 70)
    final_prompt = assemble_prompt(query, hybrid_hits)
    print(final_prompt)
    print()

    # BONUS: actually send the assembled prompt to Claude and see the answer.
    # This isn't a new "step" of RAG -- ASSEMBLE already produced everything
    # the model needs -- but it closes the loop from retrieval to answer.
    print("=" * 70)
    print("BONUS: Claude's answer, grounded in the retrieved context")
    print("=" * 70)
    messages = []
    add_user_message(messages, final_prompt)
    answer = chat(messages)
    print(answer)
