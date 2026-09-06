"""
Parse function definitions and function-to-function calls, mirroring the
"call relationship" edges from the course (Lesson 3/4).

Approach (deliberately simple, name-based matching):
1. Walk every .py file and record every `def name(...)` as a node,
   `path::name`.
2. Walk every function body and record every `Call` whose callee name
   matches a known function name anywhere in the repo.

This will produce some false positives on very common names (e.g. two
unrelated `run()` functions) — the same trade-off the course calls out
when it says this is a hint for the agent, not ground truth.
"""
from __future__ import annotations

import ast
from pathlib import Path


def _iter_functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def parse_calls(repo_root: str | Path) -> tuple[list[dict], list[dict]]:
    """Return (function_nodes, call_edges)."""
    repo_root = Path(repo_root)
    function_nodes = []  # {id, file, name}
    func_id_by_name = {}  # name -> [ids]  (may collide across files)
    file_asts = {}

    for py_file in repo_root.rglob("*.py"):
        if ".git" in py_file.parts:
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue
        file_asts[py_file] = tree
        rel = str(py_file.relative_to(repo_root))
        for fn in _iter_functions(tree):
            fid = f"{rel}::{fn.name}"
            function_nodes.append({"id": fid, "file": rel, "name": fn.name})
            func_id_by_name.setdefault(fn.name, []).append(fid)

    call_edges = []
    for py_file, tree in file_asts.items():
        rel = str(py_file.relative_to(repo_root))
        for fn in _iter_functions(tree):
            caller_id = f"{rel}::{fn.name}"
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                    for callee_id in func_id_by_name.get(callee_name, []):
                        if callee_id != caller_id:
                            call_edges.append({"src": caller_id, "dst": callee_id, "type": "call"})

    return function_nodes, call_edges


if __name__ == "__main__":
    import sys
    import json

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    nodes, edges = parse_calls(root)
    print(json.dumps({"functions": nodes, "calls": edges}, indent=2))
