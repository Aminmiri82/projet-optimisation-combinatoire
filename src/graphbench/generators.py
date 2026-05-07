from __future__ import annotations

import random

import networkx as nx

from .classes import satisfies_classes
from .repair import repair


def generate_initial_population(
    classes: tuple[str, ...],
    rng: random.Random,
    size: int,
    min_order: int = 4,
    max_order: int = 32,
) -> list[nx.Graph]:
    population: list[nx.Graph] = []
    for graph in seed_graphs(classes, min_order, max_order):
        graph = repair(graph, classes, rng)
        if graph is not None and satisfies_classes(graph, classes):
            population.append(_normalize_nodes(graph))
        if len(population) >= size:
            return population

    attempts = 0
    while len(population) < size and attempts < size * 80:
        attempts += 1
        n = rng.randint(min_order, max_order)
        graph = generate_graph(classes, rng, n)
        graph = repair(graph, classes, rng)
        if graph is not None and satisfies_classes(graph, classes):
            population.append(_normalize_nodes(graph))
    return population


def seed_graphs(classes: tuple[str, ...], min_order: int, max_order: int) -> list[nx.Graph]:
    orders = sorted({2, 3, min_order, min(6, max_order), max_order})
    orders = [order for order in orders if 2 <= order <= max_order]
    graphs: list[nx.Graph] = []
    for n in orders:
        graphs.append(nx.path_graph(n))
        if n >= 3 and "tree" not in classes:
            graphs.append(nx.cycle_graph(n))
        if "tree" not in classes:
            graphs.append(nx.complete_graph(n))
    graphs.extend(_spider_seed_graphs(max_order))
    graphs.extend(_double_star_seed_graphs(max_order))
    graphs.extend(_damaged_clique_chain_seed_graphs(max_order))
    graphs.extend(_sparse_connected_seed_graphs(max_order))
    graphs.extend(_triangle_path_seed_graphs(max_order))
    graphs.extend(_triangle_tail_seed_graphs(max_order))
    graphs.extend(_clique_path_clique_seed_graphs(max_order))
    graphs.extend(_branched_path_seed_graphs(max_order))
    return graphs


def _spider_seed_graphs(max_order: int) -> list[nx.Graph]:
    patterns = ([3, 3, 3, 1], [3, 3, 3, 3, 1], [1, 3, 3, 3, 3], [3, 3, 3, 3, 3, 1])
    graphs = []
    for lengths in patterns:
        if 1 + sum(lengths) <= max_order:
            graphs.append(_spider(lengths))
    return graphs


def _spider(lengths: list[int] | tuple[int, ...]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_node(0)
    next_node = 1
    for length in lengths:
        previous = 0
        for _ in range(length):
            graph.add_edge(previous, next_node)
            previous = next_node
            next_node += 1
    return graph


def _double_star_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for leaves in (4, 6, 8, 10):
        if 2 + 2 * leaves <= max_order:
            graphs.append(_double_star(leaves, leaves))
    return graphs


def _double_star(left_leaves: int, right_leaves: int) -> nx.Graph:
    graph = nx.Graph()
    graph.add_edge(0, 1)
    next_node = 2
    for _ in range(left_leaves):
        graph.add_edge(0, next_node)
        next_node += 1
    for _ in range(right_leaves):
        graph.add_edge(1, next_node)
        next_node += 1
    return graph


def _damaged_clique_chain_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for clique_size, copies in ((5, 2), (6, 2), (7, 2), (7, 3)):
        if clique_size * copies <= max_order:
            graphs.append(_damaged_clique_chain(clique_size, copies))
    return graphs


def _damaged_clique_chain(clique_size: int, copies: int) -> nx.Graph:
    graph = nx.Graph()
    offset = 0
    previous_bridge = None
    for _ in range(copies):
        nodes = list(range(offset, offset + clique_size))
        graph.add_nodes_from(nodes)
        graph.add_edges_from((u, v) for index, u in enumerate(nodes) for v in nodes[index + 1 :])
        graph.remove_edge(nodes[0], nodes[1])
        if previous_bridge is not None:
            graph.add_edge(previous_bridge, nodes[0])
        previous_bridge = nodes[1]
        offset += clique_size
    return graph


def _sparse_connected_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for n, probability, seed in ((10, 0.22, 17), (12, 0.18, 681), (16, 0.16, 113), (18, 0.14, 271)):
        if n <= max_order:
            rng = random.Random(seed)
            graph = nx.gnp_random_graph(n, probability, seed=seed)
            graphs.append(connect_components(graph, rng))
    return graphs


def _triangle_path_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for length in (2, 3, 4):
        n = 3 + 3 * length
        if n <= max_order:
            graphs.append(_triangle_with_attached_paths(length))
    return graphs


def _triangle_with_attached_paths(length: int) -> nx.Graph:
    graph = nx.cycle_graph(3)
    next_node = 3
    for root in range(3):
        previous = root
        for _ in range(length):
            graph.add_edge(previous, next_node)
            previous = next_node
            next_node += 1
    return graph


def _triangle_tail_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for length in (5, 6, 7):
        if 3 + length <= max_order:
            graphs.append(_triangle_tail(length))
    return graphs


def _triangle_tail(length: int) -> nx.Graph:
    graph = nx.cycle_graph(3)
    previous = 0
    next_node = 3
    for _ in range(length):
        graph.add_edge(previous, next_node)
        previous = next_node
        next_node += 1
    return graph


def _clique_path_clique_seed_graphs(max_order: int) -> list[nx.Graph]:
    graphs = []
    for clique_size, path_length in ((3, 3), (3, 4), (3, 5), (4, 4), (5, 5)):
        n = 2 * clique_size + path_length
        if n <= max_order:
            graphs.append(_clique_path_clique(clique_size, clique_size, path_length))
    return graphs


def _clique_path_clique(left_size: int, right_size: int, path_length: int) -> nx.Graph:
    graph = nx.Graph()
    left = list(range(left_size))
    path = list(range(left_size, left_size + path_length))
    right = list(range(left_size + path_length, left_size + path_length + right_size))
    graph.add_nodes_from(left + path + right)
    graph.add_edges_from((u, v) for index, u in enumerate(left) for v in left[index + 1 :])
    graph.add_edges_from((u, v) for index, u in enumerate(right) for v in right[index + 1 :])

    previous = left[0]
    for node in path:
        graph.add_edge(previous, node)
        previous = node
    graph.add_edge(previous, right[0])
    return graph


def _branched_path_seed_graphs(max_order: int) -> list[nx.Graph]:
    patterns = (
        (17, ((1, 2), (5, 1), (11, 2))),
        (18, ((1, 2), (6, 1), (12, 2))),
        (20, ((2, 2), (7, 1), (13, 2))),
    )
    graphs = []
    for path_length, branches in patterns:
        if path_length + sum(length for _, length in branches) <= max_order:
            graphs.append(_branched_path(path_length, branches))
    return graphs


def _branched_path(path_length: int, branches: tuple[tuple[int, int], ...]) -> nx.Graph:
    graph = nx.path_graph(path_length)
    next_node = path_length
    for position, branch_length in branches:
        previous = position
        for _ in range(branch_length):
            graph.add_edge(previous, next_node)
            previous = next_node
            next_node += 1
    return graph


def generate_graph(classes: tuple[str, ...], rng: random.Random, n: int) -> nx.Graph:
    if "tree" in classes:
        return generate_tree(rng, n)
    if "claw_free" in classes:
        return generate_claw_free(rng, n)
    return generate_connected(rng, n)


def generate_connected(rng: random.Random, n: int) -> nx.Graph:
    kind = rng.choice(["random_tree", "tree_plus_edges", "path", "cycle", "complete", "gnp"])
    if kind == "random_tree":
        return generate_tree(rng, n)
    if kind == "path":
        return nx.path_graph(n)
    if kind == "cycle" and n >= 3:
        return nx.cycle_graph(n)
    if kind == "complete":
        return nx.complete_graph(n)
    if kind == "gnp":
        p = rng.uniform(0.08, 0.45)
        graph = nx.gnp_random_graph(n, p, seed=rng.randrange(2**32))
        return connect_components(graph, rng)

    graph = generate_tree(rng, n)
    possible = list(nx.non_edges(graph))
    rng.shuffle(possible)
    for u, v in possible[: rng.randint(0, max(1, n))]:
        graph.add_edge(u, v)
    return graph


def generate_tree(rng: random.Random, n: int) -> nx.Graph:
    kind = rng.choice(["random", "path", "star", "broom"])
    if kind == "path":
        return nx.path_graph(n)
    if kind == "star":
        return nx.star_graph(n - 1)
    if kind == "broom":
        handle = rng.randint(2, max(2, n - 1))
        graph = nx.path_graph(handle)
        for node in range(handle, n):
            graph.add_edge(handle - 1, node)
        return graph
    return nx.random_labeled_tree(n, seed=rng.randrange(2**32))


def generate_claw_free(rng: random.Random, n: int) -> nx.Graph:
    kind = rng.choice(["cycle_power", "complete", "line_graph", "dense"])
    if kind == "complete":
        return nx.complete_graph(n)
    if kind == "dense":
        graph = nx.gnp_random_graph(n, rng.uniform(0.45, 0.85), seed=rng.randrange(2**32))
        return connect_components(graph, rng)
    if kind == "line_graph":
        base_n = max(4, int(n**0.5) + rng.randint(2, 7))
        base = generate_connected(rng, base_n)
        line = nx.convert_node_labels_to_integers(nx.line_graph(base))
        if line.number_of_nodes() == 0:
            return nx.complete_graph(max(1, n))
        return resize_by_twins(line, rng, n)

    graph = nx.cycle_graph(max(3, n))
    if n >= 5:
        for node in list(graph.nodes()):
            if rng.random() < 0.35:
                graph.add_edge(node, (node + 2) % n)
    return graph


def connect_components(G: nx.Graph, rng: random.Random) -> nx.Graph:
    graph = G.copy()
    if graph.number_of_nodes() == 0 or nx.is_connected(graph):
        return graph
    components = [list(component) for component in nx.connected_components(graph)]
    for left, right in zip(components, components[1:]):
        graph.add_edge(rng.choice(left), rng.choice(right))
    return graph


def resize_by_twins(G: nx.Graph, rng: random.Random, target_n: int) -> nx.Graph:
    graph = G.copy()
    while graph.number_of_nodes() > target_n and graph.number_of_nodes() > 1:
        graph.remove_node(rng.choice(list(graph.nodes())))
        if not nx.is_connected(graph):
            graph = connect_components(graph, rng)
    while graph.number_of_nodes() < target_n:
        source = rng.choice(list(graph.nodes()))
        new_node = max(graph.nodes(), default=-1) + 1
        graph.add_node(new_node)
        for neighbor in list(graph.neighbors(source)):
            graph.add_edge(new_node, neighbor)
        if rng.random() < 0.5:
            graph.add_edge(new_node, source)
    return graph


def _normalize_nodes(G: nx.Graph) -> nx.Graph:
    return nx.convert_node_labels_to_integers(G)
