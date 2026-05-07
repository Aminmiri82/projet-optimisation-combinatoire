from __future__ import annotations

import random

import networkx as nx

from .classes import satisfies_classes
from .repair import repair


def mutate(G: nx.Graph, classes: tuple[str, ...], rng: random.Random, max_order: int = 64) -> nx.Graph | None:
    if "tree" in classes:
        operations = [_add_leaf, _remove_leaf, _subdivide_edge, _move_leaf]
    elif "claw_free" in classes:
        operations = [_add_edge, _add_true_twin, _subdivide_edge, _remove_non_bridge_edge, _densify_local]
    else:
        operations = [
            _add_edge,
            _remove_non_bridge_edge,
            _add_leaf,
            _remove_vertex,
            _subdivide_edge,
            _densify_local,
            _add_path,
        ]

    for _ in range(20):
        graph = G.copy()
        rng.choice(operations)(graph, rng, max_order)
        repaired = repair(graph, classes, rng)
        if repaired is not None and satisfies_classes(repaired, classes):
            return repaired
    return None


def _add_edge(G: nx.Graph, rng: random.Random, _: int) -> None:
    non_edges = list(nx.non_edges(G))
    if non_edges:
        G.add_edge(*rng.choice(non_edges))


def _remove_non_bridge_edge(G: nx.Graph, rng: random.Random, _: int) -> None:
    if G.number_of_edges() == 0:
        return
    bridges = set(nx.bridges(G)) if nx.is_connected(G) else set()
    candidates = [edge for edge in G.edges() if edge not in bridges and (edge[1], edge[0]) not in bridges]
    if candidates:
        G.remove_edge(*rng.choice(candidates))


def _add_leaf(G: nx.Graph, rng: random.Random, max_order: int) -> None:
    if G.number_of_nodes() >= max_order:
        return
    parent = rng.choice(list(G.nodes()))
    new_node = max(G.nodes(), default=-1) + 1
    G.add_edge(parent, new_node)


def _remove_vertex(G: nx.Graph, rng: random.Random, _: int) -> None:
    if G.number_of_nodes() <= 2:
        return
    candidates = list(G.nodes())
    rng.shuffle(candidates)
    for node in candidates:
        graph = G.copy()
        graph.remove_node(node)
        if graph.number_of_nodes() > 0 and nx.is_connected(graph):
            G.remove_node(node)
            return


def _remove_leaf(G: nx.Graph, rng: random.Random, _: int) -> None:
    leaves = [node for node, degree in G.degree() if degree == 1]
    if G.number_of_nodes() > 2 and leaves:
        G.remove_node(rng.choice(leaves))


def _subdivide_edge(G: nx.Graph, rng: random.Random, max_order: int) -> None:
    if G.number_of_nodes() >= max_order or G.number_of_edges() == 0:
        return
    u, v = rng.choice(list(G.edges()))
    new_node = max(G.nodes(), default=-1) + 1
    G.remove_edge(u, v)
    G.add_edge(u, new_node)
    G.add_edge(new_node, v)


def _move_leaf(G: nx.Graph, rng: random.Random, _: int) -> None:
    leaves = [node for node, degree in G.degree() if degree == 1]
    if not leaves or G.number_of_nodes() <= 2:
        return
    leaf = rng.choice(leaves)
    old_parent = next(G.neighbors(leaf))
    possible = [node for node in G.nodes() if node not in {leaf, old_parent}]
    if not possible:
        return
    G.remove_edge(leaf, old_parent)
    G.add_edge(leaf, rng.choice(possible))


def _densify_local(G: nx.Graph, rng: random.Random, _: int) -> None:
    if G.number_of_nodes() < 3:
        return
    center = rng.choice(list(G.nodes()))
    neighborhood = list(G.neighbors(center))
    rng.shuffle(neighborhood)
    for u in neighborhood[:4]:
        for v in neighborhood[:4]:
            if u < v and rng.random() < 0.4:
                G.add_edge(u, v)


def _add_path(G: nx.Graph, rng: random.Random, max_order: int) -> None:
    if G.number_of_nodes() + 2 > max_order:
        return
    start = rng.choice(list(G.nodes()))
    length = rng.randint(2, min(5, max_order - G.number_of_nodes()))
    previous = start
    for _ in range(length):
        new_node = max(G.nodes(), default=-1) + 1
        G.add_edge(previous, new_node)
        previous = new_node


def _add_true_twin(G: nx.Graph, rng: random.Random, max_order: int) -> None:
    if G.number_of_nodes() >= max_order:
        return
    source = rng.choice(list(G.nodes()))
    new_node = max(G.nodes(), default=-1) + 1
    G.add_node(new_node)
    for neighbor in list(G.neighbors(source)):
        G.add_edge(new_node, neighbor)
    G.add_edge(new_node, source)
