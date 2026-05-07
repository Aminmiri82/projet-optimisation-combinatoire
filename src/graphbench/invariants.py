from __future__ import annotations

from functools import lru_cache
import math

import networkx as nx
import numpy as np


CHEAP_INVARIANTS = {
    "order",
    "size",
    "density",
    "minimum_degree",
    "maximum_degree",
    "average_degree",
    "triangle_number",
}


def graph_key(G: nx.Graph) -> bytes:
    return nx.to_graph6_bytes(G, header=False)


def compute_invariants(G: nx.Graph, needed: set[str] | None = None) -> dict[str, float]:
    """Compute requested graph invariants.

    The benchmark column names are used directly so conjectures can refer to the
    returned dictionary without a translation layer.
    """
    needed = set(needed or ())
    needed.update(CHEAP_INVARIANTS)
    result: dict[str, float] = {}

    n = G.number_of_nodes()
    m = G.number_of_edges()
    degrees = [degree for _, degree in G.degree()]

    result["order"] = n
    result["size"] = m
    result["density"] = nx.density(G) if n > 1 else 0.0
    result["minimum_degree"] = min(degrees, default=0)
    result["maximum_degree"] = max(degrees, default=0)
    result["average_degree"] = (2.0 * m / n) if n else 0.0
    result["triangle_number"] = sum(nx.triangles(G).values()) // 3

    if "diameter" in needed:
        result["diameter"] = nx.diameter(G) if n > 1 and nx.is_connected(G) else math.inf
    if "radius" in needed:
        result["radius"] = nx.radius(G) if n > 1 and nx.is_connected(G) else math.inf
    if "clique_number" in needed:
        result["clique_number"] = _clique_number(G)
    if "independence_number" in needed or "vertex_cover_number" in needed:
        alpha = _independence_number(G)
        result["independence_number"] = alpha
        result["vertex_cover_number"] = n - alpha
    if "domination_number" in needed:
        result["domination_number"] = _domination_number(G)
    if "total_domination_number" in needed:
        result["total_domination_number"] = _total_domination_number(G)
    if "independent_domination_number" in needed:
        result["independent_domination_number"] = _independent_domination_number(G)
    if "matching_number" in needed:
        result["matching_number"] = len(nx.algorithms.matching.max_weight_matching(G, maxcardinality=True))
    if "second_smallest_laplace_eigenvalue" in needed:
        result["second_smallest_laplace_eigenvalue"] = _algebraic_connectivity(G)
    if "largest_eigenvalue" in needed:
        result["largest_eigenvalue"] = _largest_adjacency_eigenvalue(G)
    if "largest_distance_eigenvalue" in needed:
        result["largest_distance_eigenvalue"] = _largest_distance_eigenvalue(G)
    if "proximity" in needed:
        result["proximity"] = _proximity(G)
    if "remoteness" in needed:
        result["remoteness"] = _remoteness(G)
    if "randic_index" in needed:
        result["randic_index"] = _randic_index(G)
    if "harmonic_index" in needed:
        result["harmonic_index"] = _harmonic_index(G)
    if "first_zagreb_index" in needed:
        result["first_zagreb_index"] = sum(d * d for d in degrees)
    if "second_zagreb_index" in needed:
        result["second_zagreb_index"] = sum(G.degree[u] * G.degree[v] for u, v in G.edges())

    missing = needed.difference(result)
    if missing:
        raise KeyError(f"Unsupported invariant(s): {sorted(missing)}")
    return result


@lru_cache(maxsize=20000)
def compute_invariants_from_graph6(g6: bytes, needed_key: tuple[str, ...]) -> dict[str, float]:
    graph = nx.from_graph6_bytes(g6.strip())
    return compute_invariants(graph, set(needed_key))


def compute_cached(G: nx.Graph, needed: set[str]) -> dict[str, float]:
    return dict(compute_invariants_from_graph6(graph_key(G).strip(), tuple(sorted(needed))))


def _clique_number(G: nx.Graph) -> int:
    if G.number_of_nodes() == 0:
        return 0
    return max((len(clique) for clique in nx.find_cliques(G)), default=0)


def _independence_number(G: nx.Graph) -> int:
    complement = nx.complement(G)
    return _clique_number(complement)


def _domination_number(G: nx.Graph) -> int:
    nodes = tuple(G.nodes())
    closed_masks = _closed_neighborhood_masks(G, nodes)
    all_mask = (1 << len(nodes)) - 1
    return _minimum_subset_cover(closed_masks, all_mask)


def _total_domination_number(G: nx.Graph) -> int:
    nodes = tuple(G.nodes())
    masks = []
    for node in nodes:
        mask = 0
        for neighbor in G.neighbors(node):
            mask |= 1 << nodes.index(neighbor)
        masks.append(mask)
    all_mask = (1 << len(nodes)) - 1
    return _minimum_subset_cover(tuple(masks), all_mask)


def _independent_domination_number(G: nx.Graph) -> int:
    nodes = tuple(G.nodes())
    index = {node: idx for idx, node in enumerate(nodes)}
    closed_masks = _closed_neighborhood_masks(G, nodes)
    all_mask = (1 << len(nodes)) - 1

    best = len(nodes) + 1

    def dfs(position: int, chosen_mask: int, dominated_mask: int, count: int) -> None:
        nonlocal best
        if count >= best:
            return
        if dominated_mask == all_mask:
            best = count
            return
        if position >= len(nodes):
            return
        remaining = len(nodes) - position
        if count + remaining < 0:
            return

        node = nodes[position]
        blocked = False
        for neighbor in G.neighbors(node):
            if chosen_mask & (1 << index[neighbor]):
                blocked = True
                break
        if not blocked:
            dfs(
                position + 1,
                chosen_mask | (1 << position),
                dominated_mask | closed_masks[position],
                count + 1,
            )
        dfs(position + 1, chosen_mask, dominated_mask, count)

    dfs(0, 0, 0, 0)
    return best if best <= len(nodes) else math.inf


def _closed_neighborhood_masks(G: nx.Graph, nodes: tuple[int, ...]) -> tuple[int, ...]:
    index = {node: idx for idx, node in enumerate(nodes)}
    masks = []
    for node in nodes:
        mask = 1 << index[node]
        for neighbor in G.neighbors(node):
            mask |= 1 << index[neighbor]
        masks.append(mask)
    return tuple(masks)


def _minimum_subset_cover(masks: tuple[int, ...], all_mask: int) -> int:
    if all_mask == 0:
        return 0
    full_cover = 0
    for mask in masks:
        full_cover |= mask
    if full_cover != all_mask:
        return math.inf

    @lru_cache(maxsize=None)
    def dp(covered: int) -> int:
        if covered == all_mask:
            return 0
        first_uncovered = next(i for i in range(len(masks)) if not (covered & (1 << i)))
        best = math.inf
        for idx, mask in enumerate(masks):
            if mask & (1 << first_uncovered):
                best = min(best, 1 + dp(covered | mask))
        return best

    return dp(0)


def _algebraic_connectivity(G: nx.Graph) -> float:
    n = G.number_of_nodes()
    if n <= 1:
        return 0.0
    adjacency = nx.to_numpy_array(G, dtype=float)
    matrix = np.diag(adjacency.sum(axis=1)) - adjacency
    values = np.linalg.eigvalsh(matrix)
    values.sort()
    return float(values[1])


def _largest_adjacency_eigenvalue(G: nx.Graph) -> float:
    if G.number_of_nodes() == 0:
        return 0.0
    matrix = nx.to_numpy_array(G, dtype=float)
    return float(np.linalg.eigvalsh(matrix)[-1])


def _largest_distance_eigenvalue(G: nx.Graph) -> float:
    if G.number_of_nodes() == 0:
        return 0.0
    distances = dict(nx.all_pairs_shortest_path_length(G))
    nodes = list(G.nodes())
    matrix = np.array([[distances[u][v] for v in nodes] for u in nodes], dtype=float)
    return float(np.linalg.eigvalsh(matrix)[-1])


def _average_distances(G: nx.Graph) -> list[float]:
    if G.number_of_nodes() <= 1:
        return [0.0]
    distances = dict(nx.all_pairs_shortest_path_length(G))
    values = []
    for node in G.nodes():
        values.append(sum(distances[node].values()) / (G.number_of_nodes() - 1))
    return values


def _proximity(G: nx.Graph) -> float:
    return min(_average_distances(G))


def _remoteness(G: nx.Graph) -> float:
    return max(_average_distances(G))


def _randic_index(G: nx.Graph) -> float:
    total = 0.0
    for u, v in G.edges():
        total += 1.0 / math.sqrt(G.degree[u] * G.degree[v])
    return total


def _harmonic_index(G: nx.Graph) -> float:
    return sum(2.0 / (G.degree[u] + G.degree[v]) for u, v in G.edges())
