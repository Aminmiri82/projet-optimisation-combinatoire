from __future__ import annotations

import csv
from pathlib import Path

from .conjecture import Conjecture


def load_conjectures(path: str | Path) -> list[Conjecture]:
    """Load benchmark conjectures without exposing known counterexamples to the search."""
    with Path(path).open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        return [Conjecture.from_row(row) for row in reader]

