from __future__ import annotations

import random

import networkx as nx

from .classes import find_induced_claw, satisfies_classes


def repair(G: nx.Graph, classes: tuple[str, ...], rng: random.Random) -> nx.Graph | None:
    graph = nx.Graph(G)
    graph.remove_edges_from(nx.selfloop_edges(graph))
    if graph.number_of_nodes() == 0:
        graph.add_node(0)

    if "tree" in classes:
        graph = _repair_tree(graph)
    elif "connected" in classes and not nx.is_connected(graph):
        _connect_components_in_place(graph, rng)

    if "claw_free" in classes:
        graph = _repair_claw_free(graph, rng)

    if satisfies_classes(graph, classes):
        return nx.convert_node_labels_to_integers(graph)
    return None


def _repair_tree(G: nx.Graph) -> nx.Graph:
    if G.number_of_nodes() <= 1:
        return nx.path_graph(max(1, G.number_of_nodes()))
    if nx.is_connected(G):
        tree = nx.minimum_spanning_tree(G)
    else:
        graph = G.copy()
        components = [list(component) for component in nx.connected_components(graph)]
        for left, right in zip(components, components[1:]):
            graph.add_edge(left[0], right[0])
        tree = nx.minimum_spanning_tree(graph)
    return nx.convert_node_labels_to_integers(tree)


def _connect_components_in_place(G: nx.Graph, rng: random.Random) -> None:
    components = [list(component) for component in nx.connected_components(G)]
    for left, right in zip(components, components[1:]):
        G.add_edge(rng.choice(left), rng.choice(right))


def _repair_claw_free(G: nx.Graph, rng: random.Random, max_steps: int = 200) -> nx.Graph:
    graph = G.copy()
    for _ in range(max_steps):
        claw = find_induced_claw(graph)
        if claw is None:
            return graph
        _, a, b, c = claw
        u, v = rng.choice([(a, b), (a, c), (b, c)])
        graph.add_edge(u, v)
    return graph

