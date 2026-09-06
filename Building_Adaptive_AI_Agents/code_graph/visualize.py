"""Draw the Code Knowledge Graph, color-coded like the course's notebook:
files = squares, functions = triangles, edges colored by relationship type."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

EDGE_COLORS = {
    "import": "#4C72B0",
    "call": "#DD8452",
    "co_edit": "#55A868",
    "contains": "#BBBBBB",
}


def plot_graph(graph: nx.MultiDiGraph, out_path: str = "code_graph.png") -> None:
    pos = nx.spring_layout(graph, seed=7, k=0.9)
    fig, ax = plt.subplots(figsize=(11, 8))

    files = [n for n, d in graph.nodes(data=True) if d.get("node_type") == "file"]
    funcs = [n for n, d in graph.nodes(data=True) if d.get("node_type") == "function"]

    nx.draw_networkx_nodes(graph, pos, nodelist=files, node_shape="s", node_color="#4C72B0", node_size=900, ax=ax)
    nx.draw_networkx_nodes(graph, pos, nodelist=funcs, node_shape="^", node_color="#DD8452", node_size=500, ax=ax)

    for edge_type, color in EDGE_COLORS.items():
        edgelist = [(u, v) for u, v, d in graph.edges(data=True) if d.get("edge_type") == edge_type]
        style = "dotted" if edge_type == "co_edit" else "solid"
        nx.draw_networkx_edges(graph, pos, edgelist=edgelist, edge_color=color, style=style, ax=ax, arrows=True, alpha=0.7)

    labels = {n: n.split("/")[-1] for n in graph.nodes()}
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=7, ax=ax)

    legend_handles = [plt.Line2D([0], [0], color=c, lw=2, label=t) for t, c in EDGE_COLORS.items()]
    ax.legend(handles=legend_handles, loc="upper left")
    ax.set_title("Code Knowledge Graph (squares = files, triangles = functions)")
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Saved graph plot to {out_path}")


if __name__ == "__main__":
    import sys

    from code_graph.build_graph import build_graph, deduplicate

    root = sys.argv[1] if len(sys.argv) > 1 else "sample_repo"
    g = build_graph(root)
    g, _ = deduplicate(g)
    plot_graph(g)
