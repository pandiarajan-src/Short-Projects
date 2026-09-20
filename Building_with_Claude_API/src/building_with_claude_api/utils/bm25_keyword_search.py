"""
bm25_keyword_search.py 
=====================================
Lexical (keyword) search with BM25 -- the other half of hybrid RAG.

WHY THIS IS NOT CHROMADB
------------------------
Chroma *does* have first-class BM25 now: you declare a sparse-vector index in a
Schema and rank with the new `Search() / Knn() / Rrf()` API. But as of
chromadb 1.5.9 that path is served by Chroma Cloud / distributed Chroma only.
Ask the local in-memory client for it and you get:

    NotImplementedError: Search is not implemented for Local Chroma
    InvalidArgumentError: Sparse vector indexing is not enabled in local

So for a RAM-only learning setup, BM25 comes from `rank_bm25` -- a ~100-line
library that replaces the notebook's hand-written `BM25Index` class.
(The Cloud version is sketched at the bottom of this file, commented out.)

WHAT BM25 ACTUALLY DOES
-----------------------
It scores a document on three signals:
  * term frequency  -- how often does the query word appear here?
  * inverse doc freq -- how rare is that word across the whole corpus?
  * length normalisation -- long documents don't get to win just by being long.

Analogy: embeddings are a librarian who has read every book and knows what they
are *about*. BM25 is Ctrl+F with good judgement -- it has read nothing, but it
never misses the exact word you typed. Error codes, product SKUs, surnames,
"118,000" -- these are BM25's home turf and the embedding model's blind spot.

SETUP
-----
    pip install rank_bm25
    pip install chromadb      # only needed for the optional hybrid demo

RUN
---
    python bm25_keyword_search.py
"""

import re
from pathlib import Path
from typing import Any, Dict, List

from rank_bm25 import BM25Okapi
from building_with_claude_api.utils.chunking_basics import chunk_by_section
from building_with_claude_api.utils.chroma_semantic_search import build_collection, search as semantic_search



# ---------------------------------------------------------------------------
# 1. Tokenisation
# ---------------------------------------------------------------------------
def tokenize(text: str) -> List[str]:
    """Lowercase and split on non-word characters.

    This is the same default tokenizer the notebook used. It is deliberately
    naive: no stemming, so "running" and "run" are different words here. A
    production setup would add a stemmer (see snowballstemmer) and a stopword
    list, which is what Chroma's own BM25 encoder does.
    """
    return [t for t in re.split(r"\W+", text.lower()) if t]


# ---------------------------------------------------------------------------
# 2. The index
# ---------------------------------------------------------------------------
class KeywordIndex:
    """Thin wrapper over rank_bm25 so it mirrors the Chroma collection API.

    The notebook's BM25Index was ~170 lines: manual document frequency counts,
    IDF computation, score normalisation. rank_bm25 does the maths; we only
    keep the documents alongside it so we can return them.
    """

    def __init__(self, chunks: List[str], k1: float = 1.5, b: float = 0.75):
        # k1 controls how quickly repeated terms stop adding score
        # (diminishing returns); b controls how hard long documents are
        # penalised. 1.5 / 0.75 are the standard defaults, same as the
        # notebook's.
        self.documents = chunks
        self.tokenized = [tokenize(c) for c in chunks]

        # BM25 needs the whole corpus up front to compute IDF -- a word is
        # only "rare" relative to everything else. That's why there is no
        # incremental add(): re-instantiate when the corpus changes.
        self.bm25 = BM25Okapi(self.tokenized, k1=k1, b=b)
        print(f"Indexed {len(chunks)} chunks with BM25\n")

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Return the k highest-scoring chunks for the query."""
        scores = self.bm25.get_scores(tokenize(query))

        # Rank by score, drop anything that matched nothing at all.
        ranked = sorted(enumerate(scores), key=lambda p: p[1], reverse=True)
        hits = []
        for idx, score in ranked[:k]:
            if score <= 0:
                continue
            chunk = self.documents[idx]
            hits.append(
                {
                    "content": chunk,
                    "score": float(score),          # unbounded, not 0-1
                    "section": chunk.splitlines()[0][:60],
                    "position": idx,
                }
            )
        return hits


def print_hits(query: str, hits: List[Dict[str, Any]]) -> None:
    print(f"QUERY: {query}")
    print("-" * 70)
    if not hits:
        print("   (no lexical match -- none of these words appear in the corpus)\n")
        return
    for rank, hit in enumerate(hits, start=1):
        preview = hit["content"].replace("\n", " ")[:110]
        print(f"{rank}. bm25={hit['score']:.3f}  section={hit['section']!r}")
        print(f"   {preview}...")
    print()


# ---------------------------------------------------------------------------
# 3. Reciprocal Rank Fusion -- how the two halves get combined
# ---------------------------------------------------------------------------
def reciprocal_rank_fusion(
    result_lists: List[List[str]], k: int = 5, k_rrf: int = 60
) -> List[Dict[str, Any]]:
    """Merge several ranked lists of document IDs into one ranking.

    The problem: a cosine distance of 0.31 and a BM25 score of 4.7 are not
    comparable -- different scales, different meanings. RRF sidesteps this by
    throwing the scores away and keeping only *rank position*:

        score(doc) = sum over lists of  1 / (k_rrf + rank_in_that_list)

    Analogy: two judges score a competition on different scales, so instead of
    averaging their points you average their placings. A document that both
    retrievers put near the top beats one that a single retriever loved.

    k_rrf=60 is the value from the original RRF paper. It flattens the
    difference between rank 1 and rank 2 so no single list can dominate.
    """
    scores: Dict[str, float] = {}
    for results in result_lists:
        for rank, doc_id in enumerate(results, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k_rrf + rank)

    ordered = sorted(scores.items(), key=lambda p: p[1], reverse=True)
    return [{"id": doc_id, "rrf_score": s} for doc_id, s in ordered[:k]]


# ---------------------------------------------------------------------------
# 4. Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    report_path = Path(__file__).resolve().parent.parent / "report.md"
    with open(report_path, "r") as f:
        report_text = f.read()

    # Get the chunks
    chunks = chunk_by_section(report_text)

    # Index the Chunk based on keyword
    index = KeywordIndex(chunks=chunks)

    # BM25 wins on exact tokens...
    print_hits("INC-2023-Q4-011", index.search("INC-2023-Q4-011", k=2))
    print_hits("CyberSecurity", index.search("CyberSecurity", k=2))

    # ...and loses on paraphrase. The question shares no meaningful words with
    # the chunk that actually answers it ("latency", "reduced"), so BM25 ranks
    # on filler words and puts the wrong section first. Compare this exact
    # query in file 1, where the embedding model gets it right.
    print_hits("what is the future direction?", index.search("what is the future direction?", k=2))    
    

    # ----------------------------------------------------------------------
    # Optional: hybrid search, the notebook's actual end goal.
    # Runs only if file 1 and chromadb are available.
    # ----------------------------------------------------------------------
    try:
        collection = build_collection(chunks, name="hybrid_demo")
    except Exception as exc:
        # Most likely cause on a first run: the MiniLM model could not be
        # downloaded (no internet, proxy, or firewall).
        print(f"Skipping hybrid demo -- Chroma unavailable: {exc}")
        exit()

    query = "How the Historical Research happens?"

    # Both retrievers must speak the same ID language for fusion to work, so
    # we use the chunk's position in the corpus as the shared key.
    dense_ids = [f"chunk_{h['metadata']['position']}"
                 for h in semantic_search(collection, query, k=5)]
    sparse_ids = [f"chunk_{h['position']}" for h in index.search(query, k=5)]

    print(f"QUERY: {query}")
    print("-" * 70)
    print(f"dense  ranking: {dense_ids}")
    print(f"bm25   ranking: {sparse_ids}")
    fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=3)
    for rank, hit in enumerate(fused, start=1):
        print(f"{rank}. {hit['id']}  rrf={hit['rrf_score']:.5f}")


# ---------------------------------------------------------------------------
# APPENDIX: the same thing on Chroma Cloud, where it is all one query
# ---------------------------------------------------------------------------
# When you move off the in-memory client, everything above (BM25 index, RRF
# function, ID juggling) collapses into a single server-side call:
#
#   import chromadb
#   from chromadb import Schema, SparseVectorIndexConfig, Search, K, Knn, Rrf
#   from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction
#
#   schema = Schema()
#   schema.create_index(
#       config=SparseVectorIndexConfig(
#           source_key=K.DOCUMENT,
#           embedding_function=ChromaBm25EmbeddingFunction(),
#       ),
#       key="sparse_embedding",
#   )
#   client = chromadb.CloudClient(tenant=..., database=..., api_key=...)
#   collection = client.create_collection("report_chunks", schema=schema)
#   collection.add(ids=[...], documents=chunks)
#
#   hybrid = Rrf(
#       ranks=[
#           Knn(query=q, return_rank=True),                            # dense
#           Knn(query=q, key="sparse_embedding", return_rank=True),    # BM25
#       ],
#       weights=[0.7, 0.3],
#       k=60,
#   )
#   results = collection.search(
#       Search().rank(hybrid).limit(5).select(K.DOCUMENT, K.SCORE)
#   )
#
# Verified against chromadb 1.5.9: local EphemeralClient raises
# NotImplementedError here, so keep this for the Cloud/server deployment.
