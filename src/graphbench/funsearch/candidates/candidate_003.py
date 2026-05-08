import math

def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get('order', G.number_of_nodes())))
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    coeffs = conjecture.coefficients
    intercept = float(conjecture.intercept)
    sign = conjecture.sign
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
    score = 50.0 * violation
    diff = poly - intercept
    weight = math.exp(-8.0 * violation * violation)
    diff_norm = abs(diff) / (abs(diff) + n + 1.0)
    score += 3.5 * weight * diff_norm
    if sign == '<=':
        deriv_bonus = deriv / (abs(deriv) + 1.0)
    else:
        deriv_bonus = -deriv / (abs(deriv) + 1.0)
    if violation < 0:
        score += 0.5 * deriv_bonus
    density = float(invariants.get('density', 0.0))
    if abs(violation) < 0.3:
        score += 0.02 * density * (1.0 - density)
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        score += 0.02 * (1.0 - max_deg / n)
    score += 0.01 * y_val / n
    return float(score)
