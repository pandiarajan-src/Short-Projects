"""Command-line entry point for the skill-induction half of the project.

Usage:
    python -m skill_lab.cli seed
    python -m skill_lab.cli induct run-the-tests
    python -m skill_lab.cli review run-the-tests
    python -m skill_lab.cli list
"""
from __future__ import annotations

import argparse
from pathlib import Path

from skill_lab import skill_box, trace_store
from skill_lab.induction_engine import draft_skill

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
V1_SKILL_PATH = Path(__file__).resolve().parent.parent / "skills_box" / "run-the-tests_v1.md"


def cmd_seed(_args) -> None:
    n = trace_store.load_sample_traces(DATA_DIR / "sample_traces.json")
    v1_body = V1_SKILL_PATH.read_text().split("---\n", 2)[-1].strip()
    skill_box.seed_v1("run-the-tests", v1_body)
    print(f"Seeded {n} traces and registered run-the-tests v1 as active.")


def cmd_induct(args) -> None:
    traces = trace_store.get_traces_by_topic(args.topic)
    if not traces:
        print(f"No traces found for topic '{args.topic}'. Run `seed` first, or add traces for this topic.")
        return
    body, writer = draft_skill(args.topic, traces)
    version = skill_box.propose(args.topic, body, writer)
    print(f"Proposed {args.topic} v{version} (writer={writer}). Run `review {args.topic}` to inspect it.")


def cmd_review(args) -> None:
    print(skill_box.diff_active_vs_pending(args.topic))
    if args.approve is None:
        print("\nRun again with --approve \"reason\" or --reject \"reason\" to act on this proposal.")
        return
    if args.approve:
        v = skill_box.approve(args.topic, args.approve)
        print(f"\nApproved. v{v} is now active in the Skill Box.")
    elif args.reject:
        v = skill_box.reject(args.topic, args.reject)
        print(f"\nRejected v{v}: {args.reject}")


def cmd_list(_args) -> None:
    for row in skill_box.list_skill_box():
        print(f"{row['name']:20s} v{row['version']:<3d} {row['status']:10s} (writer={row['writer']})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Skill Induction / Skill Box CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="Load sample traces + register v1 skill").set_defaults(func=cmd_seed)

    p_induct = sub.add_parser("induct", help="Run the induction engine on a topic's traces")
    p_induct.add_argument("topic")
    p_induct.set_defaults(func=cmd_induct)

    p_review = sub.add_parser("review", help="Show active-vs-pending diff, optionally approve/reject")
    p_review.add_argument("topic")
    p_review.add_argument("--approve", nargs="?", const="approved", default=None, help="Approve with a reason")
    p_review.add_argument("--reject", default=None, help="Reject with a reason")
    p_review.set_defaults(func=cmd_review)

    sub.add_parser("list", help="List every skill + version in the Skill Box").set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
