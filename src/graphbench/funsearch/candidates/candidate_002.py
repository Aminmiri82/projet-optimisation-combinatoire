def heuristic_score(G, invariants, conjecture):
    import math

    n_nodes = G.number_of_nodes()
    m_edges = G.number_of_edges()

    def finite_float(v, default=0.0):
        try:
            v = float(v)
            if math.isfinite(v):
                return v
        except Exception:
            pass
        return float(default)

    n = finite_float(invariants.get("order", n_nodes), n_nodes)
    if n < 1.0:
        n = 1.0

    def fget(name, default=0.0):
        if not name:
            return float(default)
        return finite_float(invariants.get(name, default), default)

    def squash(z):
        if z > 30.0:
            return 1.0
        if z < -30.0:
            return -1.0
        return math.tanh(z)

    def norm(name):
        v = fget(name, 0.0)
        if name in ("order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree",
                    "clique_number", "domination_number", "total_domination_number", "independence_number",
                    "vertex_cover_number", "independent_domination_number", "matching_number",
                    "chromatic_number", "edge_connectivity", "vertex_connectivity"):
            return v / max(1.0, n)
        if name in ("size", "triangle_number", "first_zagreb_index", "second_zagreb_index",
                    "largest_distance_eigenvalue", "wiener_index"):
            return v / max(1.0, n * n)
        if name == "density":
            return max(0.0, min(1.0, v))
        return squash(v / max(1.0, abs(v))) if abs(v) > 1.0e6 else v

    try:
        violation = finite_float(conjecture.violation(invariants), 0.0)
    except Exception:
        violation = 0.0

    x_name = str(getattr(conjecture, "x", "") or "")
    y_name = str(getattr(conjecture, "y", "") or "")
    sign = str(getattr(conjecture, "sign", "<=") or "<=")
    coeffs = getattr(conjecture, "coefficients", ()) or ()
    intercept = finite_float(getattr(conjecture, "intercept", 0.0), 0.0)
    x_value = fget(x_name, 0.0)
    y_value = fget(y_name, 0.0)

    poly = intercept
    derivative = 0.0
    xp = x_value
    for power, coefficient in enumerate(coeffs, start=1):
        c = finite_float(coefficient, 0.0)
        poly += c * xp
        if power == 1:
            derivative += c
        else:
            derivative += power * c * (x_value ** (power - 1))
        xp *= x_value

    if sign == "<=":
        raw_margin = y_value - poly
        wanted_high = y_name
        wanted_low = x_name
        x_direction = -1.0 if derivative > 0.0 else (1.0 if derivative < 0.0 else 0.0)
    else:
        raw_margin = poly - y_value
        wanted_high = x_name
        wanted_low = y_name
        x_direction = 1.0 if derivative > 0.0 else (-1.0 if derivative < 0.0 else 0.0)

    scale = 1.0 + abs(y_value) + abs(poly)
    root_scale = max(1.0, math.sqrt(scale))
    smooth_margin = squash(raw_margin / scale)
    local_margin = squash(raw_margin / root_scale)
    near_positive = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, raw_margin / root_scale))))

    if n > 1.0:
        density_default = (2.0 * float(m_edges)) / max(1.0, n * (n - 1.0))
    else:
        density_default = 0.0
    density = max(0.0, min(1.0, fget("density", density_default)))

    leaves_count = 0
    isolated_count = 0
    max_degree_seen = 0
    min_degree_seen = None
    degree_sum = 0.0
    degree_sum_sq = 0.0
    for _, d in G.degree():
        if d == 0:
            isolated_count += 1
        elif d == 1:
            leaves_count += 1
        if d > max_degree_seen:
            max_degree_seen = d
        if min_degree_seen is None or d < min_degree_seen:
            min_degree_seen = d
        fd = float(d)
        degree_sum += fd
        degree_sum_sq += fd * fd

    avg_degree = degree_sum / max(1.0, n)
    leaves = float(leaves_count) / max(1.0, n)
    isolated = float(isolated_count) / max(1.0, n)
    max_deg_norm = fget("maximum_degree", max_degree_seen) / max(1.0, n - 1.0)
    min_deg_norm = fget("minimum_degree", min_degree_seen if min_degree_seen is not None else 0.0) / max(1.0, n - 1.0)
    degree_var = max(0.0, degree_sum_sq / max(1.0, n) - avg_degree * avg_degree)
    degree_var_hint = degree_var / max(1.0, n * n)
    irregularity_hint = squash(degree_var / max(1.0, avg_degree + 1.0))

    triangles = fget("triangle_number", 0.0) / max(1.0, n * n)
    diameter = fget("diameter", 0.0) / max(1.0, n)
    radius = fget("radius", 0.0) / max(1.0, n)
    avg_deg_norm = fget("average_degree", avg_degree) / max(1.0, n - 1.0)

    dense = set(("clique_number", "triangle_number", "size", "density", "maximum_degree", "average_degree",
                 "first_zagreb_index", "second_zagreb_index", "chromatic_number", "matching_number"))
    sparse = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                  "independent_domination_number", "vertex_cover_number"))
    tree_like = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                     "independent_domination_number"))

    deriv_mag = squash(abs(derivative) / (1.0 + abs(poly) + abs(y_value)))
    high_norm = norm(wanted_high)
    low_norm = norm(wanted_low)
    x_norm = norm(x_name)
    y_norm = norm(y_name)

    score = 100.0 * violation

    # Smooth objective: reward becoming close to a violation even while still negative.
    score += 2.35 * smooth_margin
    score += 0.55 * local_margin
    score += 0.18 * near_positive

    # Directly favor the side that must be large and disfavor the side that must be small,
    # but keep this weaker than the actual polynomial margin.
    score += 0.24 * high_norm - 0.10 * low_norm
    score += 0.12 * x_direction * deriv_mag * x_norm
    if sign == "<=":
        score += 0.05 * y_norm
    else:
        score -= 0.05 * y_norm

    # Cheap structural priors matched to common invariant families.
    if wanted_high in dense:
        score += 0.18 * density + 0.10 * triangles + 0.08 * max_deg_norm + 0.04 * avg_deg_norm
    if wanted_high in sparse:
        score += 0.14 * (1.0 - density) + 0.09 * leaves + 0.09 * max(diameter, radius) + 0.03 * isolated
    if wanted_low in dense:
        score += 0.09 * (1.0 - density) + 0.04 * leaves + 0.03 * max(diameter, radius)
    if wanted_low in sparse:
        score += 0.08 * density + 0.05 * max_deg_norm + 0.03 * triangles
    if wanted_high in tree_like and wanted_low in dense:
        score += 0.04 * (1.0 - density) + 0.03 * leaves
    if wanted_high in dense and wanted_low in tree_like:
        score += 0.04 * density + 0.03 * max_deg_norm

    subgroup = str(getattr(conjecture, "subgroup", "") or "").lower()
    if "tree" in subgroup:
        score += 0.12 * (1.0 - density) + 0.10 * leaves + 0.10 * diameter - 0.04 * triangles
    if "connected" in subgroup:
        score += 0.025 * min_deg_norm - 0.04 * isolated
    if "regular" in subgroup:
        score -= 0.06 * degree_var_hint + 0.025 * (1.0 - irregularity_hint)
    if "claw_free" in subgroup:
        score += 0.06 * density + 0.04 * triangles - 0.025 * leaves
    if "bipartite" in subgroup:
        score += 0.06 * (1.0 - min(1.0, 12.0 * triangles)) + 0.02 * (1.0 - density)
    if "planar" in subgroup:
        score += 0.035 * (1.0 - density) + 0.02 * min(1.0, avg_degree / 6.0)

    # Deterministic tie breakers that prefer nontrivial, editable graphs without dominating the score.
    score += 0.006 * squash((n - 6.0) / 10.0)
    score += 0.004 * irregularity_hint

    if not math.isfinite(score):
        score = 0.0
    return float(score)
