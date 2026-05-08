from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .loader import load_conjectures
from .verify import verify_graph6


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify graph6 counterexamples from a result CSV.")
    parser.add_argument("--input", type=Path, required=True, help="Result CSV (e.g. results/part1_results.csv)")
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark/benchmark.csv"))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    conjectures = {c.conjecture_id: c for c in load_conjectures(args.benchmark)}

    total_rows = 0
    found_rows = 0
    valid_found = 0
    invalid_found = 0
    missing_ids = 0

    with args.input.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_rows += 1
            found = str(row.get("found", "")).strip().lower() == "true"
            if not found:
                continue
            found_rows += 1

            try:
                conjecture_id = int(row["conjecture_id"])
            except Exception:
                invalid_found += 1
                print(f"[INVALID] row {total_rows}: missing/invalid conjecture_id")
                continue

            conjecture = conjectures.get(conjecture_id)
            if conjecture is None:
                missing_ids += 1
                invalid_found += 1
                print(f"[INVALID] id={conjecture_id}: conjecture not found in benchmark")
                continue

            graph6 = (row.get("graph6") or "").strip()
            if not graph6:
                invalid_found += 1
                print(f"[INVALID] id={conjecture_id}: found=True but graph6 is empty")
                continue

            verdict = verify_graph6(graph6, conjecture)
            if verdict.valid:
                valid_found += 1
            else:
                invalid_found += 1
                print(f"[INVALID] id={conjecture_id}: {verdict.reason} (violation={verdict.violation:.6g})")

    print("\nVerification summary")
    print(f"- total rows: {total_rows}")
    print(f"- found rows: {found_rows}")
    print(f"- valid found: {valid_found}")
    print(f"- invalid found: {invalid_found}")
    if missing_ids:
        print(f"- missing conjecture ids: {missing_ids}")

    if invalid_found > 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
