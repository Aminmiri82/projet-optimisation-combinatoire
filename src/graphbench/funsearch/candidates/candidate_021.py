import math

def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get('order', G.number_of_nodes())))
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    coeffs = conjecture.coefficients
    intercept = float(conjecture.intercept)
    sign = conjecture.sign

    # Evaluate polynomial P(x_val)
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
    diff = poly - y_val  # difference between polynomial and y
    diff_abs = abs(diff)
    v_sq = violation * violation
    # Logistic-like weight: near 1 for small |violation|, decays smoothly
    boundary_weight = 1.0 / (1.0 + 50.0 * v_sq)
    diff_ratio = diff_abs / (diff_abs + n + 1.0)
    score += 5.0 * boundary_weight * diff_ratio

    # ---------- Gradient guidance when violation negative ----------
    # Direction: positive derivative helps for '<=', negative for '>='
    if sign == '<=':
        direction = deriv
    else:
        direction = -deriv
    dir_norm = direction / (abs(deriv) + 1.0)
    if violation < 0:
        # Continuous push: increases with distance from boundary but saturates
        dist_factor = 1.0 - math.exp(-diff_abs / (n + 1.0))
        # Use a sigmoid to smoothly reduce gradient influence near violation=0
        grad_weight = 1.0 / (1.0 + math.exp(10.0 * violation))  # sigmoid centered at 0
        score += 1.0 * dir_norm * dist_factor * grad_weight

    # ---------- Density diversity bonus (continuous) ----------
    density = float(invariants.get('density', 0.0))
    # Encourage moderate density, more strongly near violation=0
    density_bonus = density * (1.0 - density)
    density_weight = 1.0 / (1.0 + v_sq)  # weight near boundary
    score += 0.05 * density_bonus * density_weight

    # ---------- Subgroup clues (cheap heuristics) ----------
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        # Claw‑free graphs have bounded neighborhoods; lower max degree often helps
        score += 0.02 * (1.0 - max_deg / n)

    # ---------- Tie‑breaker ----------
    score += 0.01 * y_val / n

    return float(score)
