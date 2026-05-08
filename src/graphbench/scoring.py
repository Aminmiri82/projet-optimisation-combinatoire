from __future__ import annotations

from collections.abc import Callable
import importlib.util
from pathlib import Path

import networkx as nx

from .conjecture import Conjecture


def violation_score(G: nx.Graph, invariants: dict[str, float], conjecture: Conjecture) -> float:
    """Part 1 score recommended by the assignment: maximize raw violation."""
    del G
    return conjecture.violation(invariants)


def heuristic_score(G: nx.Graph, invariants: dict[str, float], conjecture: Conjecture) -> float:
    """Hand-written guidance score used to rank candidates during search.

    A graph is still accepted only when the raw violation is strictly positive.
    This score only breaks ties and gives the local search a smoother direction
    before it reaches an actual counterexample.
    """
    violation = violation_score(G, invariants, conjecture)
    n = max(1.0, float(invariants.get("order", G.number_of_nodes())))

    y_value = _normalized_invariant(conjecture.y, invariants, n)
    x_value = _normalized_invariant(conjecture.x, invariants, n)
    derivative = _polynomial_derivative(conjecture, float(invariants[conjecture.x]))

    score = 100.0 * violation
    score += 0.15 * y_value if conjecture.sign == "<=" else -0.15 * y_value
    score += 0.12 * _clamp((1.0 if conjecture.sign == ">=" else -1.0) * derivative) * x_value
    score += _structural_guidance(G, invariants, conjecture)
    return score


def _polynomial_derivative(conjecture: Conjecture, x: float) -> float:
    total = 0.0
    for power, coefficient in enumerate(conjecture.coefficients, start=1):
        total += power * float(coefficient) * (x ** (power - 1))
    return total


def _normalized_invariant(name: str, invariants: dict[str, float], n: float) -> float:
    value = float(invariants.get(name, 0.0))
    if name in {"order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree"}:
        return value / n
    if name in {
        "size",
        "triangle_number",
        "first_zagreb_index",
        "second_zagreb_index",
        "largest_distance_eigenvalue",
    }:
        return value / max(1.0, n * n)
    if name in {
        "clique_number",
        "domination_number",
        "total_domination_number",
        "independence_number",
        "vertex_cover_number",
        "independent_domination_number",
        "matching_number",
    }:
        return value / n
    return value


def _structural_guidance(G: nx.Graph, invariants: dict[str, float], conjecture: Conjecture) -> float:
    n = max(1, G.number_of_nodes())
    density = float(invariants.get("density", nx.density(G) if n > 1 else 0.0))
    leaves = sum(1 for _, degree in G.degree() if degree == 1) / n
    triangles = float(invariants.get("triangle_number", 0.0)) / max(1.0, n * n)
    diameter = float(invariants.get("diameter", 0.0)) / n if "diameter" in invariants else 0.0

    score = 0.0
    wanted_high = conjecture.y if conjecture.sign == "<=" else conjecture.x
    wanted_low = conjecture.x if conjecture.sign == "<=" else conjecture.y

    dense_invariants = {"clique_number", "triangle_number", "size"}
    sparse_invariants = {
        "diameter",
        "radius",
        "domination_number",
        "total_domination_number",
        "independence_number",
        "independent_domination_number",
    }

    if wanted_high in dense_invariants:
        score += 0.08 * density + 0.08 * triangles
    if wanted_high in sparse_invariants:
        score += 0.06 * (1.0 - density) + 0.05 * leaves + 0.05 * diameter
    if wanted_low in dense_invariants:
        score += 0.04 * (1.0 - density)
    if wanted_low in sparse_invariants:
        score += 0.03 * density

    if "tree" in conjecture.subgroup:
        score += 0.04 * leaves + 0.04 * diameter
    if "claw_free" in conjecture.subgroup:
        score += 0.03 * density
    return score


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def load_heuristic_score(path: str | Path) -> Callable[[nx.Graph, dict[str, float], Conjecture], float]:
    """Load a generated heuristic_score function from a Python file."""
    module_path = Path(path)
    spec = importlib.util.spec_from_file_location(f"graphbench_candidate_{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load scorer from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scorer = getattr(module, "heuristic_score", None)
    if scorer is None or not callable(scorer):
        raise AttributeError(f"{module_path} must define callable heuristic_score(G, invariants, conjecture)")
    return scorer
