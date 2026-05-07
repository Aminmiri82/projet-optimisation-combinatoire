from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from .classes import satisfies_classes
from .conjecture import Conjecture
from .invariants import compute_invariants


@dataclass(frozen=True)
class Verification:
    valid: bool
    violation: float
    invariants: dict[str, float]
    reason: str


def verify_graph6(graph6: str, conjecture: Conjecture) -> Verification:
    graph = nx.from_graph6_bytes(graph6.encode("ascii"))
    if not satisfies_classes(graph, conjecture.subgroup):
        return Verification(False, float("-inf"), {}, "graph does not satisfy required classes")
    invariants = compute_invariants(graph, conjecture.required_invariants)
    violation = conjecture.violation(invariants)
    if violation <= 1e-9:
        return Verification(False, violation, invariants, "inequality is not strictly violated")
    return Verification(True, violation, invariants, "valid counterexample")
