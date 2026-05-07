from __future__ import annotations

import re
import ast
from pathlib import Path


FUNCTION_RE = re.compile(r"def\s+heuristic_score\s*\(")


def extract_candidate_code(text: str) -> str:
    stripped = text.strip()
    fence = re.search(r"```(?:python)?\s*(.*?)```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1).strip()
    if not FUNCTION_RE.search(stripped):
        raise ValueError("Generated text does not define heuristic_score.")
    try:
        compile(stripped, "<generated heuristic_score>", "exec")
        tree = ast.parse(stripped)
    except SyntaxError as exc:
        raise ValueError(f"Generated code has invalid Python syntax: {exc}") from exc
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "heuristic_score"]
    if not functions:
        raise ValueError("Generated code must contain heuristic_score.")
    if not _all_paths_have_return(functions[0].body):
        raise ValueError("Generated heuristic_score has a branch that can fall through without returning a value.")
    return stripped + "\n"


def _all_paths_have_return(statements: list[ast.stmt]) -> bool:
    for statement in statements:
        if isinstance(statement, ast.Return):
            return True
        if isinstance(statement, ast.Raise):
            return True
        if isinstance(statement, ast.If):
            if statement.orelse and _all_paths_have_return(statement.body) and _all_paths_have_return(statement.orelse):
                return True
    return False


def next_candidate_path(candidates_dir: Path) -> Path:
    candidates_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(candidates_dir.glob("candidate_*.py"))
    if not existing:
        return candidates_dir / "candidate_001.py"
    last = max(int(path.stem.split("_")[-1]) for path in existing)
    return candidates_dir / f"candidate_{last + 1:03d}.py"
