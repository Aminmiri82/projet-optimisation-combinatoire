from __future__ import annotations

import networkx as nx


def heuristic_score(G: nx.Graph, invariants: dict[str, float], conjecture) -> float:
    """Baseline hand-written score from Part 1."""
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get("order", G.number_of_nodes())))

    def normalized(name: str) -> float:
        value = float(invariants.get(name, 0.0))
        if name in {"order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree"}:
            return value / n
        if name in {"size", "triangle_number", "first_zagreb_index", "second_zagreb_index", "largest_distance_eigenvalue"}:
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

    derivative = 0.0
    x_value = float(invariants[conjecture.x])
    for power, coefficient in enumerate(conjecture.coefficients, start=1):
        derivative += power * float(coefficient) * (x_value ** (power - 1))

    wanted_high = conjecture.y if conjecture.sign == "<=" else conjecture.x
    wanted_low = conjecture.x if conjecture.sign == "<=" else conjecture.y
    dense = {"clique_number", "triangle_number", "size"}
    sparse = {
        "diameter",
        "radius",
        "domination_number",
        "total_domination_number",
        "independence_number",
        "independent_domination_number",
    }

    density = float(invariants.get("density", nx.density(G) if n > 1 else 0.0))
    leaves = sum(1 for _, degree in G.degree() if degree == 1) / n
    triangles = float(invariants.get("triangle_number", 0.0)) / max(1.0, n * n)
    diameter = float(invariants.get("diameter", 0.0)) / n if "diameter" in invariants else 0.0

    score = 100.0 * violation
    score += 0.15 * normalized(conjecture.y) if conjecture.sign == "<=" else -0.15 * normalized(conjecture.y)
    score += 0.12 * max(-1.0, min(1.0, (1.0 if conjecture.sign == ">=" else -1.0) * derivative)) * normalized(conjecture.x)
    if wanted_high in dense:
        score += 0.08 * density + 0.08 * triangles
    if wanted_high in sparse:
        score += 0.06 * (1.0 - density) + 0.05 * leaves + 0.05 * diameter
    if wanted_low in dense:
        score += 0.04 * (1.0 - density)
    if wanted_low in sparse:
        score += 0.03 * density
    if "tree" in conjecture.subgroup:
        score += 0.04 * leaves + 0.04 * diameter
    if "claw_free" in conjecture.subgroup:
        score += 0.03 * density
    return score

