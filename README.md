# GraphBench Challenge - Part 1

This repository contains a modular first heuristic for automatic conjecture refutation in graph theory.

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

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run
source .venv/bin/activate

Quick smoke run:

```bash
PYTHONPATH=src python3 -m graphbench --limit 5 --time-limit 2
```

Single conjecture:

```bash
PYTHONPATH=src python3 -m graphbench --only-id 980 --time-limit 10
```

Full benchmark:

```bash
PYTHONPATH=src python3 -m graphbench --time-limit 60
```

Results are written to `results/part1_results.csv`.

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
