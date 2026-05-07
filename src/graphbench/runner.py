from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .loader import load_conjectures
from .search import SearchConfig, search_counterexample


def run_benchmark(
    benchmark_path: Path,
    output_path: Path,
    config: SearchConfig,
    limit: int | None = None,
    only_id: int | None = None,
) -> list[dict[str, object]]:
    conjectures = load_conjectures(benchmark_path)
    if only_id is not None:
        conjectures = [conjecture for conjecture in conjectures if conjecture.conjecture_id == only_id]
    if limit is not None:
        conjectures = conjectures[:limit]

    rows: list[dict[str, object]] = []
    for index, conjecture in enumerate(conjectures, start=1):
        print(f"[{index}/{len(conjectures)}] conjecture {conjecture.conjecture_id}", flush=True)
        result = search_counterexample(conjecture, config)
        row = _result_row(conjecture, result)
        rows.append(row)
        print(
            f"  {'FOUND' if result.found else 'FAILED'} "
            f"score={result.best_score:.6g} time={result.elapsed_seconds:.2f}s "
            f"evaluated={result.evaluated}",
            flush=True,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["status"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _result_row(conjecture, result) -> dict[str, object]:
    row = {
        "conjecture_id": result.conjecture_id,
        "found": result.found,
        "elapsed_seconds": f"{result.elapsed_seconds:.6f}",
        "score": f"{result.best_score:.12g}",
        "graph6": result.best_graph6,
        "evaluated": result.evaluated,
        "classes": ",".join(conjecture.subgroup),
        "x": conjecture.x,
        "x_value": result.invariants.get(conjecture.x, ""),
        "y": conjecture.y,
        "y_value": result.invariants.get(conjecture.y, ""),
        "sign": conjecture.sign,
        "rhs": conjecture.rhs(result.invariants[conjecture.x]) if result.invariants else "",
    }
    for key in ("order", "size", "density", "minimum_degree", "maximum_degree", "average_degree"):
        row[key] = result.invariants.get(key, "")
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run GraphBench Part 1 violation search.")
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark/benchmark.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/part1_results.csv"))
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--population-size", type=int, default=120)
    parser.add_argument("--min-order", type=int, default=2)
    parser.add_argument("--max-order", type=int, default=48)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only-id", type=int)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = SearchConfig(
        time_limit=args.time_limit,
        population_size=args.population_size,
        min_order=args.min_order,
        max_order=args.max_order,
        seed=args.seed,
    )
    rows = run_benchmark(args.benchmark, args.output, config, args.limit, args.only_id)
    found = sum(1 for row in rows if row["found"])
    print(f"found {found}/{len(rows)}; wrote {args.output}")


if __name__ == "__main__":
    main()
