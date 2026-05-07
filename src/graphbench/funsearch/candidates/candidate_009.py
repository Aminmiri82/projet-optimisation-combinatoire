import math

def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get('order', G.number_of_nodes())))
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    coeffs = conjecture.coefficients
    intercept = float(conjecture.intercept)
    sign = conjecture.sign

    # Compute polynomial P(x) and its derivative P'(x)
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

    # ---------- core violation weight ----------
    score = 50.0 * violation

    # ---------- smooth boundary guidance ----------
    diff = poly - intercept
    diff_abs = abs(diff)
    boundary_weight = math.exp(-8.0 * violation * violation)
    diff_ratio = diff_abs / (diff_abs + n + 1.0)
    score += 3.5 * boundary_weight * diff_ratio

    # ---------- smooth derivative direction bonus ----------
    # For '<=': positive derivative helps (increases poly relative to y)
    # For '>=': negative derivative helps
    if sign == '<=':
        deriv_bonus = deriv / (abs(deriv) + 1.0)
    else:
        deriv_bonus = -deriv / (abs(deriv) + 1.0)
    # Smooth transition: weight near 1 when violation negative, near 0 when positive
    smooth_weight = 1.0 / (1.0 + math.exp(6.0 * violation))
    score += 0.5 * smooth_weight * deriv_bonus

    # ---------- moderate density encouragement (smooth) ----------
    density = float(invariants.get('density', 0.0))
    density_benefit = density * (1.0 - density)
    # Exponential decay away from violation=0
    score += 0.02 * math.exp(-abs(violation)) * density_benefit

    # ---------- subgroup-specific hints (cheap, based on invariants) ----------
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = float(invariants.get('number_of_leaves', 0.0))
        score += 0.03 * leaves / n
        score += 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        max_deg = float(invariants.get('maximum_degree', 0.0))
        score += 0.02 * (1.0 - max_deg / n)

    # ---------- tiny tie breaker ----------
    score += 0.01 * y_val / n

    return float(score)
