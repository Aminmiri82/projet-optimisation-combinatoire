import math

def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get('order', G.number_of_nodes())))
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    coeffs = conjecture.coefficients
    intercept = float(conjecture.intercept)
    sign = conjecture.sign

    # Polynomial P(x_val)
    poly = 0.0
    power = 1.0
    for c in coeffs:
        poly += float(c) * power
        power *= x_val

    # Derivative P'(x_val)
    deriv = 0.0
    power = 1.0
    for k, c in enumerate(coeffs, 1):
        deriv += k * float(c) * power
        power *= x_val

    # ---------- Base violation (dominant) ----------
    score = 50.0 * violation

    # ---------- Smooth boundary term ----------
    diff = poly - intercept
    v_sq = violation * violation
    # Use exponential decay that stays near 1 for |violation| < 0.2, decays quickly
    boundary_weight = math.exp(-8.0 * v_sq)
    diff_norm = abs(diff) / (abs(diff) + n + 1.0)
    score += 4.0 * boundary_weight * diff_norm

    # ---------- Gradient guidance when violation negative ----------
    if sign == '<=':
        dir_norm = deriv / (abs(deriv) + 1.0)
    else:
        dir_norm = -deriv / (abs(deriv) + 1.0)
    if violation < 0:
        # Continuous push: increases with distance from boundary but saturates
        dist_factor = 1.0 - math.exp(-abs(diff) / (n + 1.0))
        score += 0.7 * dir_norm * dist_factor

    # ---------- Small penalty for moving away from boundary (when violation negative) ----------
    if violation < 0:
        # If direction is opposite to what we want, penalize
        away = max(0.0, -dir_norm) * 0.2
        score -= away

    # ---------- Density diversity bonus (small) ----------
    density = float(invariants.get('density', 0.0))
    if abs(violation) < 0.5:
        score += 0.02 * density * (1.0 - density)

    # ---------- Subgroup clues (cheap heuristics) ----------
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        # Claw‑free graphs: lower max degree often helps
        score += 0.02 * (1.0 - max_deg / n)

    # ---------- Tie‑breaker ----------
    score += 0.01 * y_val / n

    return float(score)
