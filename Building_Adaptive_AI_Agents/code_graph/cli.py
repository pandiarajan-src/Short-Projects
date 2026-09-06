"""Command-line entry point for the code knowledge graph half of the project.

Usage:
    python -m code_graph.cli build --repo sample_repo --out code_graph.pkl
    python -m code_graph.cli query  --graph code_graph.pkl "How do I improve autoplay?"
    python -m code_graph.cli plot   --graph code_graph.pkl --out code_graph.png
"""
from __future__ import annotations

import argparse

from code_graph.build_graph import build_graph, deduplicate, load_graph, save_graph
from code_graph.retrieve import graph_search, keyword_search
from code_graph.visualize import plot_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Knowledge Graph CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Parse a repo and build the graph")
    p_build.add_argument("--repo", required=True)
    p_build.add_argument("--out", default="code_graph.pkl")

    p_query = sub.add_parser("query", help="Run anchor + PageRank retrieval vs keyword search")
    p_query.add_argument("query")
    p_query.add_argument("--graph", default="code_graph.pkl")
    p_query.add_argument("--top-k", type=int, default=8)

    p_plot = sub.add_parser("plot", help="Render a PNG of the graph")
    p_plot.add_argument("--graph", default="code_graph.pkl")
    p_plot.add_argument("--out", default="code_graph.png")

    args = parser.parse_args()

    if args.command == "build":
        graph = build_graph(args.repo)
        graph, dropped = deduplicate(graph)
        save_graph(graph, args.out)
        print(f"Built graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges, "
              f"{len(dropped)} near-duplicate file(s) removed.")
        print(f"Saved to {args.out}")

    elif args.command == "query":
        graph = load_graph(args.graph)
        print(f"\nQuery: {args.query}\n")

        kw_hits = keyword_search(graph, args.query, top_k=args.top_k)
        print("Keyword / regex search results:")
        for n in kw_hits or ["  (no matches)"]:
            print(f"  - {n}")

        gs = graph_search(graph, args.query, top_k=args.top_k)
        print(f"\nAnchor node: {gs['anchor']}  (similarity {gs['anchor_score']:.3f})")
        print("Graph (personalized PageRank) results:")
        for n, s in gs["results"]:
            print(f"  - {n}  (score {s:.4f})")

    elif args.command == "plot":
        graph = load_graph(args.graph)
        plot_graph(graph, args.out)


if __name__ == "__main__":
    main()
