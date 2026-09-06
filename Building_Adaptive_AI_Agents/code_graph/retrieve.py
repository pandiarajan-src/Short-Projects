"""
Retrieval over the Code Knowledge Graph, matching Lesson 3/4's two-step
process:
  1. Anchor selection  -> the node most semantically similar to the query
  2. Personalized PageRank -> rank every other node by importance *relative
     to the anchor*, walking outward through the graph

Also includes `keyword_search`, a plain substring/regex baseline, so you can
reproduce the course's "graph vs keyword search" comparison yourself.
"""
from __future__ import annotations

import re

import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

from code_graph.build_graph import build_vectorizer


def find_anchor(graph: nx.MultiDiGraph, query: str) -> tuple[str, float]:
    node_ids, vectorizer, matrix = build_vectorizer(graph)
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix).flatten()
    best_idx = sims.argmax()
    return node_ids[best_idx], float(sims[best_idx])


def personalized_pagerank(graph: nx.MultiDiGraph, anchor: str, top_k: int = 8) -> list[tuple[str, float]]:
    undirected = graph.to_undirected()
    personalization = {n: 0.0 for n in undirected.nodes()}
    personalization[anchor] = 1.0
    scores = nx.pagerank(undirected, personalization=personalization, weight=None)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [(n, s) for n, s in ranked if n != anchor][:top_k]


def graph_search(graph: nx.MultiDiGraph, query: str, top_k: int = 8) -> dict:
    anchor, anchor_score = find_anchor(graph, query)
    ranked = personalized_pagerank(graph, anchor, top_k=top_k)
    return {"anchor": anchor, "anchor_score": anchor_score, "results": ranked}


def keyword_search(graph: nx.MultiDiGraph, query: str, top_k: int = 8) -> list[str]:
    """Naive baseline: regex/substring match of query words against node
    ids and node text. This is what the course calls 'keyword search or
    regular expression matching' — fast, but blind to relationships."""
    words = [w for w in re.split(r"\W+", query.lower()) if w]
    hits = []
    for node_id, data in graph.nodes(data=True):
        haystack = (node_id + " " + data.get("text", "")).lower()
        score = sum(1 for w in words if w in haystack)
        if score > 0:
            hits.append((node_id, score))
    hits.sort(key=lambda kv: kv[1], reverse=True)
    return [n for n, _ in hits[:top_k]]


if __name__ == "__main__":
    import sys

    from code_graph.build_graph import build_graph, deduplicate

    root = sys.argv[1] if len(sys.argv) > 1 else "sample_repo"
    query = sys.argv[2] if len(sys.argv) > 2 else "How do I improve the autoplay button for clips?"

    g = build_graph(root)
    g, _ = deduplicate(g)

    print(f"Query: {query}\n")

    kw = keyword_search(g, query)
    print("Keyword search results:")
    for n in kw:
        print(f"  - {n}")

    gs = graph_search(g, query)
    print(f"\nGraph search anchor: {gs['anchor']} (similarity {gs['anchor_score']:.3f})")
    print("Graph (PageRank) results:")
    for n, s in gs["results"]:
        print(f"  - {n}  (score {s:.4f})")
