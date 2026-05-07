from __future__ import annotations

from dataclasses import dataclass
import random
import time

import networkx as nx

from .classes import satisfies_classes
from .conjecture import Conjecture
from .generators import generate_graph, generate_initial_population
from .invariants import compute_cached
from .mutations import mutate
from .repair import repair
from .scoring import violation_score


@dataclass
class SearchConfig:
    time_limit: float = 60.0
    population_size: int = 120
    min_order: int = 4
    max_order: int = 48
    seed: int = 0
    fresh_probability: float = 0.12


@dataclass
class SearchResult:
    conjecture_id: int
    found: bool
    elapsed_seconds: float
    best_score: float
    best_graph6: str
    invariants: dict[str, float]
    evaluated: int


def search_counterexample(conjecture: Conjecture, config: SearchConfig) -> SearchResult:
    rng = random.Random(config.seed + conjecture.conjecture_id)
    start = time.monotonic()
    needed = set(conjecture.required_invariants)
    max_order = _effective_max_order(config.max_order, needed)

    population = generate_initial_population(
        conjecture.subgroup,
        rng,
        config.population_size,
        config.min_order,
        max_order,
    )
    if not population:
        population = [nx.path_graph(max(2, config.min_order))]

    scored: list[tuple[float, nx.Graph, dict[str, float]]] = []
    best_score = float("-inf")
    best_graph = population[0]
    best_invariants: dict[str, float] = {}
    evaluated = 0

    for graph in population:
        score, invariants = _evaluate(graph, conjecture, needed)
        evaluated += 1
        scored.append((score, graph, invariants))
        if score > best_score:
            best_score, best_graph, best_invariants = score, graph, invariants
        if conjecture.is_counterexample(invariants):
            return _result(conjecture, True, start, score, graph, invariants, evaluated)

    while time.monotonic() - start < config.time_limit:
        parent = _select_parent(scored, rng)
        if rng.random() < config.fresh_probability:
            n = rng.randint(config.min_order, max_order)
            candidate = repair(generate_graph(conjecture.subgroup, rng, n), conjecture.subgroup, rng)
        else:
            candidate = mutate(parent, conjecture.subgroup, rng, max_order)

        if candidate is None or not satisfies_classes(candidate, conjecture.subgroup):
            continue

        try:
            score, invariants = _evaluate(candidate, conjecture, needed)
        except (KeyError, nx.NetworkXException, ValueError, OverflowError):
            continue

        evaluated += 1
        if score > best_score:
            best_score, best_graph, best_invariants = score, candidate, invariants
        if conjecture.is_counterexample(invariants) and satisfies_classes(candidate, conjecture.subgroup):
            verified = compute_cached(candidate, needed)
            if conjecture.is_counterexample(verified):
                return _result(conjecture, True, start, score, candidate, verified, evaluated)

        scored.append((score, candidate, invariants))
        scored.sort(key=lambda item: item[0], reverse=True)
        if len(scored) > config.population_size:
            keep_elite = int(config.population_size * 0.75)
            elite = scored[:keep_elite]
            tail = scored[keep_elite:]
            rng.shuffle(tail)
            scored = elite + tail[: config.population_size - keep_elite]

    return _result(conjecture, False, start, best_score, best_graph, best_invariants, evaluated)


def _effective_max_order(configured_max_order: int, needed: set[str]) -> int:
    exact_expensive = {
        "clique_number",
        "independence_number",
        "vertex_cover_number",
        "domination_number",
        "total_domination_number",
        "independent_domination_number",
    }
    if needed & exact_expensive:
        return min(configured_max_order, 28)
    return configured_max_order


def _evaluate(
    graph: nx.Graph,
    conjecture: Conjecture,
    needed: set[str],
) -> tuple[float, dict[str, float]]:
    invariants = compute_cached(graph, needed)
    return violation_score(graph, invariants, conjecture), invariants


def _select_parent(
    scored: list[tuple[float, nx.Graph, dict[str, float]]],
    rng: random.Random,
) -> nx.Graph:
    scored.sort(key=lambda item: item[0], reverse=True)
    if rng.random() < 0.75:
        top_count = max(1, len(scored) // 5)
        return rng.choice(scored[:top_count])[1]
    return rng.choice(scored)[1]


def _result(
    conjecture: Conjecture,
    found: bool,
    start: float,
    score: float,
    graph: nx.Graph,
    invariants: dict[str, float],
    evaluated: int,
) -> SearchResult:
    graph6 = nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()
    return SearchResult(
        conjecture_id=conjecture.conjecture_id,
        found=found,
        elapsed_seconds=time.monotonic() - start,
        best_score=score,
        best_graph6=graph6,
        invariants=invariants,
        evaluated=evaluated,
    )
