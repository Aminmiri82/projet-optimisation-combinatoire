import math

def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    n = max(1.0, float(invariants.get('order', G.number_of_nodes())))
    # Safety: handle missing invariants
    x_val = float(invariants.get(conjecture.x, 0.0))
    y_val = float(invariants.get(conjecture.y, 0.0))
    # Compute polynomial and derivative at x_val
    coeffs = conjecture.coefficients
    poly = 0.0
    deriv = 0.0
    power = 1.0
    for c in coeffs:
        poly += float(c) * power
        power *= x_val
    # derivative: sum_{k=1} k * c_k * x^(k-1)
    power = 1.0
    for k, c in enumerate(coeffs, start=1):
        deriv += k * float(c) * power
        power *= x_val
    # Signed residual: violation is the distance from satisfying the inequality
    # We want to maximize the score, so negative violation should be penalized
    # Baseline: 10 * violation + small structural hints
    score = 10.0 * violation
    # Encourage graphs where the polynomial is far from the intercept when violation is negative
    # Use a smooth logistic-like term: sigmoid(-violation) * (poly - intercept)
    intercept = float(conjecture.intercept)
    diff = poly - intercept
    # If violation is negative, we want diff to be large in the direction that helps flip sign
    # Clamp sigmoid to avoid extreme values
    sig = 1.0 / (1.0 + math.exp(-5.0 * violation))  # sigmoid centered at 0, ~0 for violation<-1, ~1 for violation>1
    # Reward large absolute diff when violation is near zero (decision boundary)
    # Use a Gaussian-like weight centered at violation=0
    weight = math.exp(-10.0 * violation * violation)
    score += 2.0 * weight * abs(diff) / (1.0 + abs(diff))
    # Add small bonus for normalized y value depending on sign
    sign = conjecture.sign
    if sign == '<=':
        score += 0.05 * y_val / n
    else:
        score += 0.05 * (1.0 - y_val / n)
    # Encourage extreme values of x (high or low) when violation is small
    x_norm = x_val / n if n > 0 else 0.0
    # If sign is <=, we want y <= poly; so large poly helps violation become negative -> penalize
    # Actually we want to minimize violation, so for same violation, prefer graphs where derivative is large
    # to allow easier adjustment
    # Add a small term proportional to derivative magnitude
    score += 0.02 * abs(deriv) / (1.0 + abs(deriv))
    # Use density as a tie-breaker
    density = float(invariants.get('density', 0.0))
    # Prefer moderate density when violation is near zero (more room for change)
    if abs(violation) < 0.5:
        score += 0.01 * density * (1.0 - density)
    # Subgroup hints: if tree, prefer low density and high leaf fraction
    subgroup = conjecture.subgroup
    if 'tree' in subgroup:
        leaves = sum(1 for _, d in G.degree() if d == 1) / n
        score += 0.03 * leaves + 0.01 * (1.0 - density)
    if 'claw_free' in subgroup:
        score += 0.02 * density
    # Ensure finite
    return float(score)
