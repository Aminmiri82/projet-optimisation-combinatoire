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

    def sigmoid(z):
        if z > 40.0:
            return 1.0
        if z < -40.0:
            return 0.0
        return 1.0 / (1.0 + math.exp(-z))

    def norm(name):
        v = fget(name, 0.0)
        if name in ("order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree",
                    "clique_number", "domination_number", "total_domination_number", "independence_number",
                    "vertex_cover_number", "independent_domination_number", "matching_number",
                    "chromatic_number", "edge_connectivity", "vertex_connectivity", "zero_forcing_number",
                    "power_domination_number", "metric_dimension"):
            return v / max(1.0, n)
        if name in ("size", "triangle_number", "first_zagreb_index", "second_zagreb_index",
                    "largest_distance_eigenvalue", "wiener_index", "hyper_wiener_index", "energy"):
            return v / max(1.0, n * n)
        if name == "density":
            return max(0.0, min(1.0, v))
        if abs(v) > 1000000.0:
            return squash(v / max(1.0, abs(v)))
        return v

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
            try:
                derivative += power * c * (x_value ** (power - 1))
            except Exception:
                pass
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
    log_scale = 1.0 + math.log1p(abs(y_value) + abs(poly) + abs(x_value))
    smooth_margin = squash(raw_margin / scale)
    local_margin = squash(raw_margin / root_scale)
    micro_margin = squash(raw_margin / log_scale)
    near_positive = sigmoid(raw_margin / root_scale)

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

    avg_degree_seen = degree_sum / max(1.0, n)
    leaves = float(leaves_count) / max(1.0, n)
    isolated = float(isolated_count) / max(1.0, n)
    max_deg_norm = fget("maximum_degree", max_degree_seen) / max(1.0, n - 1.0)
    min_deg_norm = fget("minimum_degree", min_degree_seen if min_degree_seen is not None else 0.0) / max(1.0, n - 1.0)
    avg_deg_norm = fget("average_degree", avg_degree_seen) / max(1.0, n - 1.0)
    degree_var = max(0.0, degree_sum_sq / max(1.0, n) - avg_degree_seen * avg_degree_seen)
    degree_var_hint = degree_var / max(1.0, n * n)
    irregularity_hint = squash(degree_var / max(1.0, avg_degree_seen + 1.0))

    triangles = fget("triangle_number", 0.0) / max(1.0, n * n)
    diameter = fget("diameter", 0.0) / max(1.0, n)
    radius = fget("radius", 0.0) / max(1.0, n)
    clique = fget("clique_number", 0.0) / max(1.0, n)
    independence = fget("independence_number", 0.0) / max(1.0, n)
    matching = fget("matching_number", 0.0) / max(1.0, n)

    dense = set(("clique_number", "triangle_number", "size", "density", "maximum_degree", "average_degree",
                 "first_zagreb_index", "second_zagreb_index", "chromatic_number", "matching_number",
                 "edge_connectivity", "vertex_connectivity"))
    sparse = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                  "independent_domination_number", "vertex_cover_number", "zero_forcing_number",
                  "power_domination_number", "metric_dimension"))
    distance_like = set(("diameter", "radius", "wiener_index", "hyper_wiener_index", "largest_distance_eigenvalue"))
    tree_like = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                     "independent_domination_number", "wiener_index"))

    deriv_mag = squash(abs(derivative) / (1.0 + abs(poly) + abs(y_value)))
    high_norm = norm(wanted_high)
    low_norm = norm(wanted_low)
    x_norm = norm(x_name)
    y_norm = norm(y_name)

    score = 100.0 * violation

    # Multi-scale smooth objective: gives gradient both far from and close to refutation.
    score += 2.55 * smooth_margin
    score += 0.62 * local_margin
    score += 0.10 * micro_margin
    score += 0.16 * near_positive

    # Favor the direction implied by the conjectured inequality, but keep it secondary.
    score += 0.25 * high_norm - 0.11 * low_norm
    score += 0.13 * x_direction * deriv_mag * x_norm
    if sign == "<=":
        score += 0.045 * y_norm
    else:
        score -= 0.045 * y_norm

    # Generic shape priors for common invariant families.
    if wanted_high in dense:
        score += 0.19 * density + 0.10 * triangles + 0.08 * max_deg_norm + 0.045 * avg_deg_norm + 0.025 * clique
    if wanted_high in sparse:
        score += 0.145 * (1.0 - density) + 0.095 * leaves + 0.085 * max(diameter, radius) + 0.025 * isolated + 0.025 * independence
    if wanted_high in distance_like:
        score += 0.05 * (1.0 - density) + 0.035 * leaves + 0.025 * irregularity_hint
    if wanted_low in dense:
        score += 0.095 * (1.0 - density) + 0.045 * leaves + 0.03 * max(diameter, radius)
    if wanted_low in sparse:
        score += 0.085 * density + 0.055 * max_deg_norm + 0.03 * triangles + 0.015 * matching
    if wanted_low in distance_like:
        score += 0.04 * density + 0.025 * max_deg_norm
    if wanted_high in tree_like and wanted_low in dense:
        score += 0.045 * (1.0 - density) + 0.035 * leaves
    if wanted_high in dense and wanted_low in tree_like:
        score += 0.045 * density + 0.035 * max_deg_norm

    subgroup = str(getattr(conjecture, "subgroup", "") or "").lower()
    if "tree" in subgroup:
        score += 0.13 * (1.0 - density) + 0.11 * leaves + 0.095 * diameter - 0.045 * triangles
    if "connected" in subgroup:
        score += 0.026 * min_deg_norm - 0.045 * isolated
    if "regular" in subgroup:
        score -= 0.065 * degree_var_hint + 0.025 * (1.0 - irregularity_hint)
    if "claw_free" in subgroup:
        score += 0.06 * density + 0.04 * triangles - 0.025 * leaves
    if "bipartite" in subgroup:
        score += 0.06 * (1.0 - min(1.0, 12.0 * triangles)) + 0.02 * (1.0 - density)
    if "planar" in subgroup:
        score += 0.035 * (1.0 - density) + 0.02 * min(1.0, avg_degree_seen / 6.0)
    if "eulerian" in subgroup:
        score += 0.02 * min_deg_norm - 0.02 * leaves

    score += 0.006 * squash((n - 6.0) / 10.0)
    score += 0.0045 * irregularity_hint

    if not math.isfinite(score):
        score = 0.0
    return float(score)
