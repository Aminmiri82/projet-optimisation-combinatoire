from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import math
import random
import time

import networkx as nx

from .conjecture import Conjecture
from .generators import generate_graph, generate_initial_population
from .invariants import compute_cached
from .mutations import mutate
from .repair import repair
from .scoring import heuristic_score, violation_score


@dataclass
class SearchConfig:
    time_limit: float = 60.0
    population_size: int = 0
    min_order: int = 2
    max_order: int = 48
    seed: int = 0
    fresh_probability: float = 0.12
    scorer: Callable[[nx.Graph, dict[str, float], Conjecture], float] = heuristic_score


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
    population_size = _effective_population_size(conjecture, config.population_size)

    population = generate_initial_population(
        conjecture.subgroup,
        rng,
        population_size,
        config.min_order,
        max_order,
    )
    if not population:
        population = [nx.path_graph(max(2, config.min_order))]

    scored: list[tuple[float, float, nx.Graph, dict[str, float]]] = []
    best_score = float("-inf")
    best_graph = population[0]
    best_invariants: dict[str, float] = {}
    evaluated = 0

    for graph in population:
        if time.monotonic() - start >= config.time_limit:
            break
        objective, score, invariants = _evaluate(graph, conjecture, needed, config.scorer)
        evaluated += 1
        scored.append((objective, score, graph, invariants))
        if score > best_score:
            best_score, best_graph, best_invariants = score, graph, invariants
        if conjecture.is_counterexample(invariants):
            return _result(conjecture, True, start, score, graph, invariants, evaluated)

    scored.sort(key=lambda item: item[0], reverse=True)
    while time.monotonic() - start < config.time_limit:
        if not scored:
            break
        parent = _select_parent(scored, rng)
        if rng.random() < config.fresh_probability:
            n = rng.randint(config.min_order, max_order)
            candidate = repair(generate_graph(conjecture.subgroup, rng, n), conjecture.subgroup, rng)
        else:
            candidate = mutate(parent, conjecture.subgroup, rng, max_order)

        if candidate is None:
            continue

        try:
            objective, score, invariants = _evaluate(candidate, conjecture, needed, config.scorer)
        except (KeyError, nx.NetworkXException, ValueError, OverflowError):
            continue

        evaluated += 1
        if score > best_score:
            best_score, best_graph, best_invariants = score, candidate, invariants
        if conjecture.is_counterexample(invariants):
            verified = compute_cached(candidate, needed)
            if conjecture.is_counterexample(verified):
                return _result(conjecture, True, start, score, candidate, verified, evaluated)

        scored.append((objective, score, candidate, invariants))
        scored.sort(key=lambda item: item[0], reverse=True)
        if len(scored) > population_size:
            keep_elite = int(population_size * 0.75)
            elite = scored[:keep_elite]
            tail = scored[keep_elite:]
            rng.shuffle(tail)
            scored = elite + tail[: population_size - keep_elite]
            scored.sort(key=lambda item: item[0], reverse=True)

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


def _effective_population_size(conjecture: Conjecture, configured_population_size: int) -> int:
    if configured_population_size > 0:
        return configured_population_size

    needed = set(conjecture.required_invariants)
    high_population_pairs = (
        {"density", "proximity"},
    )
    medium_population_pairs = (
        {"second_zagreb_index", "independent_domination_number"},
        {"largest_distance_eigenvalue", "proximity"},
        {"average_degree", "clique_number"},
        {"clique_number", "minimum_degree"},
        {"radius", "remoteness"},
    )
    if any(pair <= needed for pair in high_population_pairs):
        return 120
    if any(pair <= needed for pair in medium_population_pairs):
        return 60
    return 30


def _evaluate(
    graph: nx.Graph,
    conjecture: Conjecture,
    needed: set[str],
    scorer: Callable[[nx.Graph, dict[str, float], Conjecture], float],
) -> tuple[float, float, dict[str, float]]:
    invariants = compute_cached(graph, needed)
    try:
        raw_objective = scorer(graph, invariants, conjecture)
        objective = float(raw_objective) if raw_objective is not None else float("-inf")
    except Exception:
        objective = float("-inf")
    if not math.isfinite(objective):
        objective = float("-inf")
    return objective, violation_score(graph, invariants, conjecture), invariants


def _select_parent(
    scored: list[tuple[float, float, nx.Graph, dict[str, float]]],
    rng: random.Random,
) -> nx.Graph:
    if rng.random() < 0.75:
        top_count = max(1, len(scored) // 5)
        return rng.choice(scored[:top_count])[2]
    return rng.choice(scored)[2]


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
