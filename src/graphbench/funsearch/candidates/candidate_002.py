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
    # Base score: large weight on violation
    score = 50.0 * violation
    # Smooth term near decision boundary: reward large |poly - intercept| when violation is small
    diff = poly - intercept
    weight_boundary = math.exp(-5.0 * violation * violation)  # Gaussian, ~1 near 0, ~0 far
    # Normalize diff to avoid extreme values dominating
    diff_norm = abs(diff) / (abs(diff) + n)
    score += 3.0 * weight_boundary * diff_norm
    # Directional bonus: if violation is negative, encourage sign flip
    # For sign '<=' we want y <= poly, so negative violation means y > poly (bad).
    # We want poly to increase relative to y. Reward positive derivative when violation negative.
    # For sign '>=' we want y >= poly, so negative violation means y < poly (bad).
    # Reward negative derivative when violation negative.
    if sign == '<=':
        deriv_bonus = deriv / (abs(deriv) + 1.0)
    else:
        deriv_bonus = -deriv / (abs(deriv) + 1.0)
    # Only apply when violation is negative (i.e., we are on wrong side)
    if violation < 0:
        score += 0.5 * deriv_bonus
    # Encourage moderate density when violation is small (more flexible)
    density = float(invariants.get('density', 0.0))
    if abs(violation) < 0.3:
        score += 0.02 * density * (1.0 - density)
    # Subgroup-specific hints (cheap, based on invariants)
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        # Claw-free graphs have bounded neighborhoods; reward low max degree
        score += 0.02 * (1.0 - max_deg / n)
    # Tie-breaking with normalized y value
    score += 0.01 * y_val / n
    # Ensure finite and return
    return float(score)
