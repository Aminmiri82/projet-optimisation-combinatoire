def heuristic_score(G, invariants, conjecture):
    import math

    n_nodes = G.number_of_nodes()
    m_edges = G.number_of_edges()
    n = float(invariants.get("order", n_nodes) or n_nodes or 1.0)
    if n < 1.0:
        n = 1.0

    def fget(name, default=0.0):
        try:
            v = invariants.get(name, default)
            if v is None:
                return float(default)
            v = float(v)
            if math.isfinite(v):
                return v
        except Exception:
            pass
        return float(default)

    def norm(name):
        v = fget(name, 0.0)
        if name in ("order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree",
                    "clique_number", "domination_number", "total_domination_number", "independence_number",
                    "vertex_cover_number", "independent_domination_number", "matching_number"):
            return v / max(1.0, n)
        if name in ("size", "triangle_number", "first_zagreb_index", "second_zagreb_index",
                    "largest_distance_eigenvalue"):
            return v / max(1.0, n * n)
        if name == "density":
            return max(0.0, min(1.0, v))
        return v

    try:
        violation = float(conjecture.violation(invariants))
        if not math.isfinite(violation):
            violation = 0.0
    except Exception:
        violation = 0.0

    x_name = getattr(conjecture, "x", "")
    y_name = getattr(conjecture, "y", "")
    sign = getattr(conjecture, "sign", "<=")
    coeffs = getattr(conjecture, "coefficients", ()) or ()
    intercept = float(getattr(conjecture, "intercept", 0.0) or 0.0)
    x_value = fget(x_name, 0.0)
    y_value = fget(y_name, 0.0)

    poly = intercept
    derivative = 0.0
    xp = x_value
    for power, coefficient in enumerate(coeffs, start=1):
        try:
            c = float(coefficient)
        except Exception:
            c = 0.0
        poly += c * xp
        derivative += power * c * (x_value ** (power - 1))
        xp *= x_value

    if sign == "<=":
        raw_margin = y_value - poly
        wanted_high = y_name
        wanted_low = x_name
    else:
        raw_margin = poly - y_value
        wanted_high = x_name
        wanted_low = y_name

    scale = 1.0 + abs(y_value) + abs(poly)
    smooth_margin = math.tanh(raw_margin / scale)

    if n > 1.0:
        density = fget("density", (2.0 * float(m_edges)) / (n * (n - 1.0)))
    else:
        density = 0.0
    density = max(0.0, min(1.0, density))

    leaves_count = 0
    max_degree_seen = 0
    min_degree_seen = None
    degree_sum_sq = 0.0
    for _, d in G.degree():
        if d == 1:
            leaves_count += 1
        if d > max_degree_seen:
            max_degree_seen = d
        if min_degree_seen is None or d < min_degree_seen:
            min_degree_seen = d
        degree_sum_sq += float(d * d)
    leaves = float(leaves_count) / max(1.0, n)
    max_deg_norm = fget("maximum_degree", max_degree_seen) / max(1.0, n - 1.0)
    min_deg_norm = fget("minimum_degree", min_degree_seen if min_degree_seen is not None else 0.0) / max(1.0, n - 1.0)
    degree_var_hint = max(0.0, degree_sum_sq / max(1.0, n) - (2.0 * float(m_edges) / max(1.0, n)) ** 2) / max(1.0, n * n)

    triangles = fget("triangle_number", 0.0) / max(1.0, n * n)
    diameter = fget("diameter", 0.0) / max(1.0, n)
    radius = fget("radius", 0.0) / max(1.0, n)

    dense = set(("clique_number", "triangle_number", "size", "density", "maximum_degree", "average_degree",
                 "first_zagreb_index", "second_zagreb_index"))
    sparse = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                  "independent_domination_number", "matching_number"))

    deriv_dir = 0.0
    if derivative > 0.0:
        deriv_dir = 1.0
    elif derivative < 0.0:
        deriv_dir = -1.0
    deriv_mag = math.tanh(abs(derivative) / (1.0 + abs(poly)))

    score = 100.0 * violation
    score += 2.0 * smooth_margin
    score += 0.45 * math.tanh(raw_margin / max(1.0, math.sqrt(scale)))

    if sign == "<=":
        score += 0.22 * norm(y_name)
        score -= 0.10 * deriv_dir * deriv_mag * norm(x_name)
    else:
        score += 0.22 * norm(x_name)
        score -= 0.18 * norm(y_name)
        score += 0.10 * deriv_dir * deriv_mag * norm(x_name)

    if wanted_high in dense:
        score += 0.16 * density + 0.10 * triangles + 0.06 * max_deg_norm
    if wanted_high in sparse:
        score += 0.12 * (1.0 - density) + 0.08 * leaves + 0.08 * max(diameter, radius)
    if wanted_low in dense:
        score += 0.08 * (1.0 - density) + 0.03 * leaves
    if wanted_low in sparse:
        score += 0.07 * density + 0.04 * max_deg_norm

    subgroup = str(getattr(conjecture, "subgroup", "") or "")
    if "tree" in subgroup:
        score += 0.10 * (1.0 - density) + 0.08 * leaves + 0.08 * diameter
    if "connected" in subgroup:
        score += 0.02 * min_deg_norm
    if "regular" in subgroup:
        score -= 0.04 * degree_var_hint
    if "claw_free" in subgroup:
        score += 0.05 * density + 0.03 * triangles
    if "bipartite" in subgroup:
        score += 0.05 * (1.0 - triangles)

    if not math.isfinite(score):
        score = 0.0
    return float(score)
