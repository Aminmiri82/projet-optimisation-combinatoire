from __future__ import annotations

from itertools import combinations

import networkx as nx


def satisfies_classes(G: nx.Graph, classes: tuple[str, ...]) -> bool:
    return all(satisfies_class(G, graph_class) for graph_class in classes)


def satisfies_class(G: nx.Graph, graph_class: str) -> bool:
    if graph_class == "connected":
        return G.number_of_nodes() > 0 and nx.is_connected(G)
    if graph_class == "tree":
        return nx.is_tree(G)
    if graph_class == "claw_free":
        return is_claw_free(G)
    if graph_class == "planar":
        return nx.check_planarity(G, counterexample=False)[0]
    if graph_class == "bipartite":
        return nx.is_bipartite(G)
    raise ValueError(f"Unsupported graph class: {graph_class}")


def is_claw_free(G: nx.Graph) -> bool:
    return find_induced_claw(G) is None


def find_induced_claw(G: nx.Graph) -> tuple[int, int, int, int] | None:
    """Return center and three leaves of an induced K1,3, or None."""
    for center in G.nodes():
        neighbors = list(G.neighbors(center))
        if len(neighbors) < 3:
            continue
        for a, b, c in combinations(neighbors, 3):
            if not G.has_edge(a, b) and not G.has_edge(a, c) and not G.has_edge(b, c):
                return center, a, b, c
    return None

