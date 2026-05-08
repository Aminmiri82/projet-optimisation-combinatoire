# GraphBench Challenge

This repository contains a modular heuristic search engine and a FunSearch-style score evolution loop for automatic conjecture refutation in graph theory.

The Part 1 score follows the assignment recommendation exactly:

```text
violation(G) = y(G) - f(x(G))   for y <= f(x)
violation(G) = f(x(G)) - y(G)   for y >= f(x)
```

A graph is accepted only when the strict violation is positive and the required graph classes are satisfied.

During search, candidates are ranked with a small hand-written guidance score in `scoring.py`.
The guidance score is only used to choose promising parents when the raw violation is still
negative or tied. The final decision still uses the strict violation formula above.

The initial population includes simple extremal families: paths, cycles, cliques, random trees,
and spider trees. Spider trees are useful for conjectures involving total domination versus
matching, because they can increase total domination without increasing matching as quickly.

The benchmark uses reciprocal distance conventions for `proximity` and `remoteness`:
`proximity = 1 / max_average_distance` and `remoteness = 1 / min_average_distance`.
This matches the stored benchmark counterexample values.

## Install

From repo root:

```bash
./run.sh setup
```

Manual equivalent:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run Part 1

Recommended (single command):

```bash
./run.sh part1
```

Useful variants:

```bash
./run.sh smoke
./run.sh one 980 10
TIME_LIMIT=30 OUTPUT=results/part1_30s.csv ./run.sh part1
```

Manual CLI:

```bash
PYTHONPATH=src python3 -m graphbench --time-limit 60 --output results/part1_results.csv
```

## Run Part 2 (FunSearch)

Generated scoring functions live in `src/graphbench/funsearch/candidates/`.
Each candidate must define:

```python
def heuristic_score(G, invariants, conjecture):
    return conjecture.violation(invariants)
```

Evaluate the baseline candidate on a small subset:

```bash
PYTHONPATH=src python3 -m graphbench.funsearch.evaluator \
  src/graphbench/funsearch/candidates/baseline.py \
  --limit 10 \
  --time-limit 2 \
  --output results/funsearch/baseline_10.csv
```

To generate a new candidate with OpenRouter, set:

```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_MODEL="openai/gpt-5.5"
export OPENROUTER_REASONING_EFFORT="low"
```

Then run:

```bash
PYTHONPATH=src python3 -m graphbench.funsearch.evolve
```

Candidate generation first requests OpenRouter structured output with a JSON schema. If provider routing cannot satisfy that parameter combination, it falls back to JSON object mode, then plain text with local validation.

Evaluate the generated candidate:

```bash
PYTHONPATH=src python3 -m graphbench.funsearch.evaluator \
  src/graphbench/funsearch/candidates/candidate_001.py \
  --limit 30 \
  --time-limit 3 \
  --output results/funsearch/candidate_001_30.csv
```

The evaluator appends candidate summaries to `results/funsearch/registry.csv`.

Run a small generate/evaluate loop:

```bash
PYTHONPATH=src python3 -m graphbench.funsearch.cycle \
  --iterations 3 \
  --limit 30 \
  --time-limit 3
```

## Verify

Verify that all found counterexamples in a result CSV satisfy class constraints and strictly violate the corresponding conjecture:

```bash
./run.sh verify
```

Or with a custom result file:

```bash
./run.sh verify results/part1_30s.csv
```

Manual CLI:

```bash
PYTHONPATH=src python3 -m graphbench.verify_results --input results/part1_results.csv
```

## Where Results Are

- Part 1 default output: `results/part1_results.csv`
- Additional Part 1 experiments: `results/` (e.g., `results/v4`, `results/iterations`)
- FunSearch runs and candidate summaries: `results/funsearch/`
- Dashboard files: `results_dashboard/`
- Final reports: `report/report_fr.pdf`, `report/report_en.pdf`

## One-Command Reproduction

```bash
./run.sh all
```

This runs: smoke test, Part 1 benchmark, verification, and FunSearch baseline evaluation.

## Architecture

- `conjecture.py`: typed conjecture model and exact rational coefficient parsing.
- `loader.py`: benchmark CSV loading.
- `invariants.py`: invariant computation using benchmark column names.
- `classes.py`: graph class validators, including connected/tree/claw-free.
- `generators.py`: class-aware initial graph generators.
- `mutations.py`: local graph mutations.
- `repair.py`: repair after mutation.
- `scoring.py`: Part 1 raw violation score.
- `search.py`: population search loop.
- `runner.py`: CLI and benchmark result writing.
- `verify_results.py`: CLI verification for result CSV files.
