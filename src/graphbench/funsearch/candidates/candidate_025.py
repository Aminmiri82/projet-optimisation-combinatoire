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
    diff = poly - intercept
    diff_abs = abs(diff)
    # Slower Gaussian decay: weight ~ 1 for |violation| < 0.5, decays gently
    boundary_weight = math.exp(-2.0 * violation * violation)
    diff_ratio = diff_abs / (diff_abs + n + 1.0)
    score += 3.0 * boundary_weight * diff_ratio

    # ---------- Gradient guidance when violation negative ----------
    if violation < 0:
        if sign == '<=':
            direction = deriv
        else:
            direction = -deriv
        dir_norm = direction / (abs(deriv) + 1.0)
        # Distance factor: increases with |violation|, saturates at 1
        dist_factor = 1.0 - math.exp(-abs(violation) / 2.0)
        score += 1.0 * dir_norm * dist_factor

    # ---------- Density diversity bonus (small) ----------
    density = float(invariants.get('density', 0.0))
    if abs(violation) < 0.3:
        score += 0.02 * density * (1.0 - density)

    # ---------- Subgroup clues (cheap heuristics) ----------
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        score += 0.02 * (1.0 - max_deg / n)

    # ---------- Tie-breaker ----------
    score += 0.01 * y_val / n

    return float(score)
