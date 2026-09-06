"""
Mine `git log` to find files that are repeatedly changed together, i.e. the
"co_edit" relationship from the course (Lesson 3/4).
"""
from __future__ import annotations

import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path


def _commit_file_lists(repo_root: Path) -> list[list[str]]:
    result = subprocess.run(
        ["git", "log", "--name-only", "--pretty=format:__COMMIT__"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    commits: list[list[str]] = []
    current: list[str] = []
    for line in result.stdout.splitlines():
        if line == "__COMMIT__":
            if current:
                commits.append(current)
            current = []
        elif line.strip():
            current.append(line.strip())
    if current:
        commits.append(current)
    return commits


def parse_coedits(repo_root: str | Path, min_count: int = 2) -> list[dict]:
    """Return edges {src, dst, type: 'co_edit', weight} for file pairs that
    were changed together in at least `min_count` commits."""
    repo_root = Path(repo_root)
    pair_counts: Counter[tuple[str, str]] = Counter()

    for files in _commit_file_lists(repo_root):
        py_files = sorted(f for f in files if f.endswith(".py"))
        for a, b in combinations(py_files, 2):
            pair_counts[(a, b)] += 1

    edges = []
    for (a, b), count in pair_counts.items():
        if count >= min_count:
            edges.append({"src": a, "dst": b, "type": "co_edit", "weight": count})
    return edges


if __name__ == "__main__":
    import sys
    import json

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(parse_coedits(root), indent=2))
