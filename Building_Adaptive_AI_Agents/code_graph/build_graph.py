"""
Assemble parsed imports / calls / co-edits into one property graph, the
"Code Knowledge Graph" from Lessons 3 & 4 of the course.

Nodes:  files (square in the course viz) and functions (triangle)
Edges:  import (file->file), call (function->function), co_edit (file<->file)
"""
from __future__ import annotations

import pickle
from pathlib import Path

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

from code_graph.parse_calls import parse_calls
from code_graph.parse_coedits import parse_coedits
from code_graph.parse_imports import parse_imports


def build_graph(repo_root: str | Path) -> nx.MultiDiGraph:
    repo_root = Path(repo_root)
    graph = nx.MultiDiGraph()

    # --- file nodes ---
    for py_file in repo_root.rglob("*.py"):
        if ".git" in py_file.parts:
            continue
        rel = str(py_file.relative_to(repo_root))
        graph.add_node(rel, node_type="file", text=py_file.read_text(encoding="utf-8"))

    # --- function nodes ---
    function_nodes, call_edges = parse_calls(repo_root)
    for fn in function_nodes:
        graph.add_node(fn["id"], node_type="function", text=fn["name"].replace("_", " "))
        # a function "belongs to" its file — cheap structural edge, not one
        # of the course's 3 relationship types, just useful for traversal
        graph.add_edge(fn["file"], fn["id"], edge_type="contains")

    # --- import edges ---
    for edge in parse_imports(repo_root):
        graph.add_edge(edge["src"], edge["dst"], edge_type="import")

    # --- call edges ---
    for edge in call_edges:
        graph.add_edge(edge["src"], edge["dst"], edge_type="call")

    # --- co-edit edges (undirected in spirit -> add both directions) ---
    for edge in parse_coedits(repo_root):
        graph.add_edge(edge["src"], edge["dst"], edge_type="co_edit", weight=edge["weight"])
        graph.add_edge(edge["dst"], edge["src"], edge_type="co_edit", weight=edge["weight"])

    return graph


def deduplicate(graph: nx.MultiDiGraph, similarity_threshold: float = 0.96) -> tuple[nx.MultiDiGraph, list[tuple[str, str]]]:
    """Course Lesson 4: audit the graph for near-duplicate nodes (e.g. two
    near-identical files) before it's used for retrieval. Returns the
    cleaned graph and the list of (kept, dropped) duplicate pairs."""
    file_nodes = [n for n, d in graph.nodes(data=True) if d.get("node_type") == "file"]
    if len(file_nodes) < 2:
        return graph, []

    texts = [graph.nodes[n]["text"] for n in file_nodes]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    sims = (matrix @ matrix.T).toarray()

    dropped_pairs = []
    to_drop = set()
    for i in range(len(file_nodes)):
        for j in range(i + 1, len(file_nodes)):
            if sims[i, j] >= similarity_threshold and file_nodes[j] not in to_drop:
                to_drop.add(file_nodes[j])
                dropped_pairs.append((file_nodes[i], file_nodes[j]))

    cleaned = graph.copy()
    cleaned.remove_nodes_from(to_drop)
    return cleaned, dropped_pairs


def build_vectorizer(graph: nx.MultiDiGraph):
    """Build a TF-IDF space over every node's text, used later to find the
    'anchor' node for a query (a free, local, open-source stand-in for the
    embedding-based semantic similarity search used in the course)."""
    node_ids = list(graph.nodes())
    texts = [graph.nodes[n].get("text", "") for n in node_ids]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    matrix = vectorizer.fit_transform(texts)
    return node_ids, vectorizer, matrix


def save_graph(graph: nx.MultiDiGraph, path: str | Path) -> None:
    with open(path, "wb") as f:
        pickle.dump(graph, f)


def load_graph(path: str | Path) -> nx.MultiDiGraph:
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "sample_repo"
    g = build_graph(root)
    g, dropped = deduplicate(g)
    print(f"Nodes: {g.number_of_nodes()}  Edges: {g.number_of_edges()}  Duplicates removed: {len(dropped)}")
    save_graph(g, "code_graph.pkl")
    print("Saved to code_graph.pkl")
