from __future__ import annotations

import networkx as nx

from .conjecture import Conjecture


def violation_score(G: nx.Graph, invariants: dict[str, float], conjecture: Conjecture) -> float:
    """Part 1 score recommended by the assignment: maximize raw violation."""
    del G
    return conjecture.violation(invariants)

