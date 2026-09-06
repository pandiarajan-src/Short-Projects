"""
End-to-end demo tying both halves of the project together. Run this first
to see everything work with zero configuration:

    python demo.py

Part 1 mirrors Lesson 2 (Behavior Adaptation / skill induction):
  seed traces -> induct a v2 skill -> show the human-review diff -> approve it

Part 2 mirrors Lessons 3-4 (Knowledge Adaptation / code knowledge graph):
  build a graph over sample_repo/ -> compare keyword search vs graph search
  on the exact "autoplay" and "verify_token" style questions from the course
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def part1_skill_induction() -> None:
    print("=" * 70)
    print("PART 1 — Behavior Adaptation: trace -> skill induction -> Skill Box")
    print("=" * 70)

    from skill_lab import skill_box, trace_store
    from skill_lab.induction_engine import draft_skill

    n = trace_store.load_sample_traces(ROOT / "data" / "sample_traces.json")
    v1_body = (ROOT / "skills_box" / "run-the-tests_v1.md").read_text().split("---\n", 2)[-1].strip()
    skill_box.seed_v1("run-the-tests", v1_body)
    print(f"\nSeeded {n} traces of an agent repeatedly hitting the same pytest error.")
    print("Registered v1 of 'run-the-tests' as active (a bare 'run pytest' skill).\n")

    traces = trace_store.get_traces_by_topic("run-the-tests")
    body, writer = draft_skill("run-the-tests", traces)
    version = skill_box.propose("run-the-tests", body, writer)
    print(f"Induction Engine (writer='{writer}') proposed run-the-tests v{version}:\n")
    print(body)

    print("--- Human review gate ---")
    print(skill_box.diff_active_vs_pending("run-the-tests"))

    reason = "Confirms the PYTHONPATH=src fix and test-extras install across 3 runs; matches our repo layout."
    approved_version = skill_box.approve("run-the-tests", reason)
    print(f"\n[human] approve('{reason}')")
    print(f"-> v{approved_version} promoted to ACTIVE in the Skill Box.\n")


def part2_code_knowledge_graph() -> None:
    print("=" * 70)
    print("PART 2 — Knowledge Adaptation: Code Knowledge Graph vs keyword search")
    print("=" * 70)

    from code_graph.build_graph import build_graph, deduplicate, save_graph
    from code_graph.retrieve import graph_search, keyword_search
    from code_graph.visualize import plot_graph

    repo = ROOT / "sample_repo"
    graph = build_graph(repo)
    graph, dropped = deduplicate(graph)
    print(f"\nBuilt graph over sample_repo/: {graph.number_of_nodes()} nodes, "
          f"{graph.number_of_edges()} edges, {len(dropped)} duplicate file(s) removed.")

    save_graph(graph, ROOT / "code_graph.pkl")
    plot_graph(graph, str(ROOT / "code_graph.png"))

    questions = [
        "How do I improve the autoplay button for clips?",
        "Where do we verify a token?",
    ]

    for q in questions:
        print(f"\n--- Query: \"{q}\" ---")
        kw = keyword_search(graph, q)
        print("Keyword search finds:      ", kw or "(nothing)")

        gs = graph_search(graph, q)
        graph_hits = [n for n, _ in gs["results"]]
        print(f"Graph anchor:                {gs['anchor']}  (similarity {gs['anchor_score']:.3f})")
        print("Graph (PageRank) finds:     ", graph_hits)

        only_in_graph = [n for n in graph_hits if n not in kw]
        if only_in_graph:
            print(f"-> Files the graph found that keyword search MISSED: {only_in_graph}")

    print(f"\nSaved graph to code_graph.pkl and a picture to code_graph.png — open the PNG to see it.")


if __name__ == "__main__":
    part1_skill_induction()
    print()
    part2_code_knowledge_graph()
    print("\nDone. Try `python -m skill_lab.cli list` and "
          "`python -m code_graph.cli query \"your own question\" --graph code_graph.pkl` next.")
