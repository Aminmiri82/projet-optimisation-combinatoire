from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import ast


@dataclass(frozen=True)
class Conjecture:
    """A benchmark conjecture of the form y(G) <= f(x(G)) or y(G) >= f(x(G))."""

    conjecture_id: int
    text: str
    subgroup: tuple[str, ...]
    x: str
    y: str
    sign: str
    coefficients: tuple[Fraction, ...]
    intercept: Fraction
    degree: int

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Conjecture":
        subgroup = tuple(ast.literal_eval(row["Subgroup"]))
        coefficients = tuple(Fraction(value.strip()) for value in ast.literal_eval(row["Coefficients"]))
        return cls(
            conjecture_id=int(row["Conjecture ID"]),
            text=row["Conjecture"],
            subgroup=subgroup,
            x=row["X"],
            y=row["Y"],
            sign=row["Sign"],
            coefficients=coefficients,
            intercept=Fraction(row["Intercept"].strip()),
            degree=int(row["Degree"]),
        )

    @property
    def required_invariants(self) -> set[str]:
        return {self.x, self.y}

    def rhs(self, x_value: float) -> float:
        x = float(x_value)
        total = float(self.intercept)
        for power, coefficient in enumerate(self.coefficients, start=1):
            total += float(coefficient) * (x**power)
        return total

    def violation(self, invariants: dict[str, float]) -> float:
        lhs = float(invariants[self.y])
        rhs = self.rhs(float(invariants[self.x]))
        if self.sign == "<=":
            return lhs - rhs
        if self.sign == ">=":
            return rhs - lhs
        raise ValueError(f"Unsupported sign: {self.sign}")

    def is_counterexample(self, invariants: dict[str, float], epsilon: float = 1e-9) -> bool:
        return self.violation(invariants) > epsilon

