"""
Parse `import` / `from ... import ...` statements in a Python repo and turn
them into file -> file edges, mirroring the "import relationship" described
in the course (Lesson 3/4): the skeleton edges that tell an agent what a
file depends on.

This is intentionally simple (stdlib `ast` only, no type inference) — good
enough to see the concept work, not a production-grade import resolver.
"""
from __future__ import annotations

import ast
from pathlib import Path


def _module_to_file(module_name: str, repo_root: Path) -> Path | None:
    """Best-effort: map `foo.bar` -> repo_root/foo/bar.py, only for
    modules that actually live inside this repo (local, first-party code)."""
    candidate = repo_root / (module_name.replace(".", "/") + ".py")
    if candidate.exists():
        return candidate
    # also handle `from foo import bar` where foo.py exists but bar is a symbol
    parts = module_name.split(".")
    if parts:
        candidate = repo_root / (parts[0] + ".py")
        if candidate.exists():
            return candidate
    return None


def parse_imports(repo_root: str | Path) -> list[dict]:
    """Return a list of edges: {src, dst, type: 'import'}."""
    repo_root = Path(repo_root)
    edges = []

    for py_file in repo_root.rglob("*.py"):
        if ".git" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]

            for target in targets:
                dst = _module_to_file(target, repo_root)
                if dst and dst != py_file:
                    edges.append(
                        {
                            "src": str(py_file.relative_to(repo_root)),
                            "dst": str(dst.relative_to(repo_root)),
                            "type": "import",
                        }
                    )
    return edges


if __name__ == "__main__":
    import sys
    import json

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(parse_imports(root), indent=2))
