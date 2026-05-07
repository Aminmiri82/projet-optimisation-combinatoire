from __future__ import annotations

from pathlib import Path


SYSTEM_PROMPT = """You improve a Python heuristic score for graph conjecture refutation.
Return structured JSON with a code field containing Python code for one function named heuristic_score(G, invariants, conjecture).
The function must be deterministic, fast, and side-effect free.
It may use only builtins, import math inside the function if needed, and NetworkX APIs through the provided graph G.
It must not import benchmark data, use conjecture IDs, store hard-coded solutions, read files, or use randomness.
Final counterexample validity is checked elsewhere; this function only ranks candidates during search.
"""


def build_user_prompt(best_sources: list[str], results_summary: str) -> str:
    examples = "\n\n".join(
        f"# Candidate {index}\n{source.strip()}" for index, source in enumerate(best_sources, start=1)
    )
    return f"""We need a better score function for this assignment-required signature:

def heuristic_score(G, invariants, conjecture):
    \"\"\"
    G: NetworkX graph
    invariants: dict of already computed graph invariants
    conjecture: object with x, y, sign, coefficients, intercept, subgroup, and violation(invariants)
    return: numeric score to maximize
    \"\"\"

The baseline is raw violation plus small structural guidance. It already finds many counterexamples.
Improve average search time by making the score smoother before violation becomes positive.

Benchmark result summary:
{results_summary}

Best current sources:
{examples}

Requirements:
- Return only one complete Python function named heuristic_score in the JSON code field.
- Do not wrap the function in Markdown.
- Do not use conjecture.conjecture_id or hard-code conjecture IDs.
- Avoid expensive exact graph algorithms; invariants already contains the expensive values needed.
- Handle missing invariants with .get defaults.
- Return a finite float.
- The function must have an unconditional final return statement at the outer indentation level.
"""


def read_sources(paths: list[Path]) -> list[str]:
    return [path.read_text(encoding="utf-8") for path in paths]
