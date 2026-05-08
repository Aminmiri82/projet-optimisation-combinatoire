import math

def heuristic_score(G, invariants, conjecture):
    # Extract basic invariants
    n = float(invariants.get('order', G.number_of_nodes()))
    if n <= 0.0:
        n = 1.0
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    coeffs = conjecture.coefficients
    intercept = float(conjecture.intercept)
    sign = conjecture.sign

    # Evaluate polynomial P(x_val) and its derivative
    poly = 0.0
    power = 1.0
    for c in coeffs:
        poly += float(c) * power
        power *= x_val
    deriv = 0.0
    power = 1.0
    for k, c in enumerate(coeffs, 1):
        deriv += k * float(c) * power
        power *= x_val

    # Violation is the primary signal
    violation = conjecture.violation(invariants)
    score = 50.0 * violation

    # Smooth guidance near decision boundary
    diff = poly - intercept
    diff_abs = abs(diff)
    # Weight that is high when violation is small (near boundary)
    boundary_weight = math.exp(-6.0 * violation * violation)
    # Normalized diff magnitude, scaled to avoid dominating
    diff_norm = diff_abs / (diff_abs + n + 1.0)
    score += 4.0 * boundary_weight * diff_norm

    # Directional derivative bonus: encourage moving towards boundary when violation is negative
    if sign == '<=':
        deriv_sign = deriv
    else:
        deriv_sign = -deriv
    # Penalize moving away from boundary (deriv_sign negative means derivative points opposite to desired direction)
    if violation < 0:
        # Reward positive deriv_sign, penalize negative
        deriv_bonus = deriv_sign / (abs(deriv) + 1.0)
        # Additional small penalty for moving away
        if deriv_sign < 0:
            deriv_bonus -= 0.3 * abs(deriv_sign) / (abs(deriv) + 1.0)
        score += 0.6 * deriv_bonus

    # Density flexibility: moderate density helps when violation is small
    density = float(invariants.get('density', 0.0))
    if abs(violation) < 0.3:
        # Peak at density 0.5
        score += 0.025 * 4.0 * density * (1.0 - density)

    # Subgroup hints (cheap, based on invariants)
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        score += 0.02 * (1.0 - max_deg / n)

    # Tie-breaker: prefer larger y values (often leads to more extreme graphs)
    score += 0.01 * y_val / n

    return float(score)
