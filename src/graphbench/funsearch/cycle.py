from __future__ import annotations

import argparse
from pathlib import Path

from .evaluator import append_registry, evaluate_candidate
from .evolve import generate_candidate


def run_cycles(
    iterations: int,
    candidates_dir: Path,
    registry_path: Path,
    benchmark_path: Path,
    results_dir: Path,
    limit: int | None,
    time_limit: float,
    population_size: int,
    max_order: int,
    seed: int,
    model: str | None,
    reasoning_effort: str | None,
) -> None:
    for iteration in range(1, iterations + 1):
        print(f"=== FunSearch iteration {iteration}/{iterations}: generate ===", flush=True)
        candidate_path = generate_candidate(
            candidates_dir=candidates_dir,
            registry_path=registry_path,
            top_k=3,
            model=model,
            reasoning_effort=reasoning_effort,
        )
        print(f"=== FunSearch iteration {iteration}/{iterations}: evaluate {candidate_path.name} ===", flush=True)
        output_path = results_dir / f"{candidate_path.stem}.csv"
        summary = evaluate_candidate(
            candidate_path=candidate_path,
            benchmark_path=benchmark_path,
            output_path=output_path,
            time_limit=time_limit,
            population_size=population_size,
            max_order=max_order,
            seed=seed,
            limit=limit,
        )
        append_registry(registry_path, summary)
        print(summary, flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run generate/evaluate cycles for FunSearch-style scoring.")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--candidates-dir", type=Path, default=Path("src/graphbench/funsearch/candidates"))
    parser.add_argument("--registry", type=Path, default=Path("results/funsearch/registry.csv"))
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark/benchmark.csv"))
    parser.add_argument("--results-dir", type=Path, default=Path("results/funsearch"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--time-limit", type=float, default=3.0)
    parser.add_argument("--population-size", type=int, default=120)
    parser.add_argument("--max-order", type=int, default=48)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default=None)
    parser.add_argument("--reasoning-effort", default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run_cycles(
        iterations=args.iterations,
        candidates_dir=args.candidates_dir,
        registry_path=args.registry,
        benchmark_path=args.benchmark,
        results_dir=args.results_dir,
        limit=args.limit,
        time_limit=args.time_limit,
        population_size=args.population_size,
        max_order=args.max_order,
        seed=args.seed,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
    )


if __name__ == "__main__":
    main()

