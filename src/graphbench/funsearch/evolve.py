from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .codegen import extract_candidate_code, next_candidate_path
from .openrouter_client import call_openrouter
from .prompts import SYSTEM_PROMPT, build_user_prompt, read_sources


CANDIDATE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "heuristic_candidate",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Complete Python code for one function named heuristic_score(G, invariants, conjecture), including a final return statement.",
                },
                "notes": {
                    "type": "string",
                    "description": "Brief rationale for the scoring changes.",
                },
            },
            "required": ["code", "notes"],
            "additionalProperties": False,
        },
    },
}

JSON_OBJECT_RESPONSE_FORMAT = {"type": "json_object"}


def select_best_sources(registry_path: Path, candidates_dir: Path, top_k: int) -> list[Path]:
    baseline = candidates_dir / "baseline.py"
    if not registry_path.exists():
        return [baseline]

    rows = list(csv.DictReader(registry_path.open(newline="", encoding="utf-8")))
    rows.sort(key=lambda row: (-int(row.get("found", 0)), float(row.get("cost", "inf"))))
    paths = []
    for row in rows:
        path = Path(row["candidate"])
        if path.exists() and path not in paths:
            paths.append(path)
        if len(paths) >= top_k:
            break
    if baseline.exists() and baseline not in paths:
        paths.append(baseline)
    return paths[:top_k]


def summarize_registry(registry_path: Path, max_rows: int = 8) -> str:
    if not registry_path.exists():
        return "No generated candidates evaluated yet. Use the baseline as the starting point."
    rows = list(csv.DictReader(registry_path.open(newline="", encoding="utf-8")))
    rows.sort(key=lambda row: (-int(row.get("found", 0)), float(row.get("cost", "inf"))))
    lines = ["candidate,found,total,cost,avg_time_found"]
    for row in rows[:max_rows]:
        lines.append(
            f"{Path(row['candidate']).name},{row['found']},{row['total']},{row['cost']},{row['avg_time_found']}"
        )
    return "\n".join(lines)


def generate_candidate(
    candidates_dir: Path,
    registry_path: Path,
    top_k: int,
    model: str | None,
    reasoning_effort: str | None,
) -> Path:
    best_paths = select_best_sources(registry_path, candidates_dir, top_k)
    prompt = build_user_prompt(read_sources(best_paths), summarize_registry(registry_path))
    last_error = None
    strategies = [
        ("json_schema", CANDIDATE_RESPONSE_FORMAT),
        ("json_object", JSON_OBJECT_RESPONSE_FORMAT),
        ("plain_text", None),
    ]
    for attempt in range(6):
        strategy_name, response_format = strategies[min(attempt // 2, len(strategies) - 1)]
        repair = "" if attempt == 0 else f"\n\nPrevious attempt was invalid: {last_error}\nReturn a complete function with a final return."
        if strategy_name == "json_object":
            repair += "\nReturn valid JSON with keys code and notes."
        elif strategy_name == "plain_text":
            repair += "\nReturn only the Python function as plain text."
        try:
            content = call_openrouter(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt + repair},
                ],
                model=model,
                reasoning_effort=reasoning_effort,
                response_format=response_format,
                plugins=[{"id": "response-healing"}] if response_format is not None else None,
            )
        except RuntimeError as exc:
            last_error = exc
            continue
        try:
            try:
                parsed = json.loads(content)
                candidate_text = parsed["code"]
            except (json.JSONDecodeError, KeyError, TypeError):
                candidate_text = content
            code = extract_candidate_code(candidate_text)
            break
        except ValueError as exc:
            last_error = exc
    else:
        raise ValueError(f"OpenRouter did not return a valid candidate after 6 attempts: {last_error}")
    path = next_candidate_path(candidates_dir)
    path.write_text(code, encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a new heuristic_score candidate via OpenRouter.")
    parser.add_argument("--candidates-dir", type=Path, default=Path("src/graphbench/funsearch/candidates"))
    parser.add_argument("--registry", type=Path, default=Path("results/funsearch/registry.csv"))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--model", default=None)
    parser.add_argument("--reasoning-effort", default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    path = generate_candidate(args.candidates_dir, args.registry, args.top_k, args.model, args.reasoning_effort)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
