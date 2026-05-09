#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"

usage() {
  cat <<'EOF'
Usage:
  ./run.sh setup
  ./run.sh smoke
  ./run.sh part1
  ./run.sh one <CONJECTURE_ID> [TIME_LIMIT]
  ./run.sh verify [CSV_PATH]
  ./run.sh funsearch-baseline
  ./run.sh all

Environment overrides:
  TIME_LIMIT=<seconds>        (default: 60 for part1, 2 for smoke)
  OUTPUT=<csv path>           (default: results/part1_results.csv)
  LIMIT=<int>                 (optional limit for part1)
  SEED=<int>                  (default: 0)
  POPULATION_SIZE=<int>       (default: 0, adaptive v5; use 120 for v4-style fixed size)
EOF
}

ensure_venv() {
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "[setup] creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi
  echo "[setup] installing dependencies"
  "$PIP_BIN" install -r requirements.txt
}

run_part1() {
  local time_limit="${TIME_LIMIT:-60}"
  local output="${OUTPUT:-results/part1_results.csv}"
  local seed="${SEED:-0}"
  local population_size="${POPULATION_SIZE:-0}"
  local extra=()
  if [[ -n "${LIMIT:-}" ]]; then
    extra+=(--limit "$LIMIT")
  fi
  echo "[part1] running benchmark with time-limit=${time_limit}s population-size=${population_size} output=${output}"
  PYTHONPATH=src "$PYTHON_BIN" -m graphbench \
    --time-limit "$time_limit" \
    --output "$output" \
    --seed "$seed" \
    --population-size "$population_size" \
    "${extra[@]}"
}


run_smoke() {
  local time_limit="${TIME_LIMIT:-2}"
  echo "[smoke] running quick check with limit=5 time-limit=${time_limit}s"
  PYTHONPATH=src "$PYTHON_BIN" -m graphbench --limit 5 --time-limit "$time_limit"
}

run_one() {
  local conjecture_id="${1:-}"
  local time_limit="${2:-10}"
  if [[ -z "$conjecture_id" ]]; then
    echo "Missing conjecture id"
    usage
    exit 1
  fi
  echo "[one] running conjecture id=${conjecture_id} time-limit=${time_limit}s"
  PYTHONPATH=src "$PYTHON_BIN" -m graphbench --only-id "$conjecture_id" --time-limit "$time_limit"
}

run_funsearch_baseline() {
  local out="results/funsearch/baseline_10.csv"
  echo "[funsearch] evaluating baseline scorer to ${out}"
  PYTHONPATH=src "$PYTHON_BIN" -m graphbench.funsearch.evaluator \
    src/graphbench/funsearch/candidates/baseline.py \
    --limit 10 \
    --time-limit 2 \
    --output "$out"
}

run_verify() {
  local input_csv="${1:-results/part1_results.csv}"
  echo "[verify] checking counterexamples from ${input_csv}"
  PYTHONPATH=src "$PYTHON_BIN" -m graphbench.verify_results --input "$input_csv"
}

cmd="${1:-}"
case "$cmd" in
  setup)
    ensure_venv
    ;;
  smoke)
    ensure_venv
    run_smoke
    ;;
  part1)
    ensure_venv
    run_part1
    ;;
  one)
    ensure_venv
    shift
    run_one "$@"
    ;;
  funsearch-baseline)
    ensure_venv
    run_funsearch_baseline
    ;;
  verify)
    ensure_venv
    shift
    run_verify "$@"
    ;;
  all)
    ensure_venv
    run_smoke
    run_part1
    run_verify "results/part1_results.csv"
    run_funsearch_baseline
    ;;
  *)
    usage
    exit 1
    ;;
esac
