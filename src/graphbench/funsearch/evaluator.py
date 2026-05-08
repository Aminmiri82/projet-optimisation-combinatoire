from __future__ import annotations

import argparse
import csv
from pathlib import Path

from graphbench.loader import load_conjectures
from graphbench.runner import _result_row
from graphbench.scoring import load_heuristic_score
from graphbench.search import SearchConfig, search_counterexample


def evaluate_candidate(
    candidate_path: Path,
    benchmark_path: Path,
    output_path: Path,
    time_limit: float,
    population_size: int,
    max_order: int,
    seed: int,
    limit: int | None = None,
) -> dict[str, object]:
    scorer = load_heuristic_score(candidate_path)
    config = SearchConfig(
        time_limit=time_limit,
        population_size=population_size,
        max_order=max_order,
        seed=seed,
        scorer=scorer,
    )
    conjectures = load_conjectures(benchmark_path)
    if limit is not None:
        conjectures = conjectures[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, conjecture in enumerate(conjectures, start=1):
        print(f"[{index}/{len(conjectures)}] {candidate_path.stem} on {conjecture.conjecture_id}", flush=True)
        result = search_counterexample(conjecture, config)
        rows.append(_result_row(conjecture, result))
        print(
            f"  {'FOUND' if result.found else 'FAILED'} "
            f"time={result.elapsed_seconds:.2f}s score={result.best_score:.6g}",
            flush=True,
        )

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["status"])
        writer.writeheader()
        writer.writerows(rows)

    found = sum(row["found"] for row in rows)
    cost = sum(float(row["elapsed_seconds"]) if row["found"] else 2.0 * time_limit for row in rows)
    summary = {
        "candidate": str(candidate_path),
        "output": str(output_path),
        "found": found,
        "total": len(rows),
        "cost": f"{cost:.6f}",
        "avg_time_found": f"{sum(float(row['elapsed_seconds']) for row in rows if row['found']) / max(1, found):.6f}",
    }
    return summary


def append_registry(registry_path: Path, summary: dict[str, object]) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    exists = registry_path.exists()
    with registry_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate one generated FunSearch candidate scorer.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark/benchmark.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/funsearch/eval.csv"))
    parser.add_argument("--registry", type=Path, default=Path("results/funsearch/registry.csv"))
    parser.add_argument("--time-limit", type=float, default=5.0)
    parser.add_argument("--population-size", type=int, default=120)
    parser.add_argument("--max-order", type=int, default=48)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    summary = evaluate_candidate(
        args.candidate,
        args.benchmark,
        args.output,
        args.time_limit,
        args.population_size,
        args.max_order,
        args.seed,
        args.limit,
    )
    append_registry(args.registry, summary)
    print(summary)


if __name__ == "__main__":
    main()

