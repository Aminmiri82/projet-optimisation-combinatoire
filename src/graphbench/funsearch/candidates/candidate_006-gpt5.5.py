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
        try:
            d = float(default)
            if math.isfinite(d):
                return d
        except Exception:
            pass
        return 0.0

    n = finite_float(invariants.get("order", n_nodes), n_nodes)
    if n < 1.0:
        n = 1.0

    def fget(name, default=0.0):
        if not name:
            return finite_float(default, 0.0)
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

    linear_like = set((
        "order", "diameter", "radius", "maximum_degree", "minimum_degree", "average_degree",
        "clique_number", "domination_number", "total_domination_number", "independence_number",
        "vertex_cover_number", "independent_domination_number", "matching_number", "chromatic_number",
        "edge_connectivity", "vertex_connectivity", "zero_forcing_number", "power_domination_number",
        "metric_dimension", "path_cover_number", "annihilation_number", "k_residual_index",
        "slater_number", "sub_total_domination_number", "restrained_domination_number",
        "connected_domination_number", "upper_domination_number", "forcing_number",
        "feedback_vertex_set_number", "girth", "circumference", "minimum_maximal_matching_number"
    ))
    quadratic_like = set((
        "size", "triangle_number", "first_zagreb_index", "second_zagreb_index", "wiener_index",
        "hyper_wiener_index", "largest_distance_eigenvalue", "energy", "laplacian_energy",
        "distance_energy", "eccentric_connectivity_index", "gutman_index", "degree_sum",
        "forgotten_index", "harmonic_index", "randic_index", "atom_bond_connectivity_index",
        "geometric_arithmetic_index", "sum_connectivity_index"
    ))

    def norm(name):
        v = fget(name, 0.0)
        if name in linear_like:
            return v / max(1.0, n)
        if name in quadratic_like:
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
        try:
            term = c * xp
            if math.isfinite(term):
                poly += term
        except Exception:
            pass
        try:
            if power == 1:
                derivative += c
            else:
                dterm = power * c * (x_value ** (power - 1))
                if math.isfinite(dterm):
                    derivative += dterm
        except Exception:
            pass
        try:
            xp *= x_value
            if not math.isfinite(xp) or abs(xp) > 1.0e150:
                xp = 0.0
        except Exception:
            xp = 0.0

    if not math.isfinite(poly):
        poly = 0.0
    if not math.isfinite(derivative):
        derivative = 0.0

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
    if not math.isfinite(raw_margin):
        raw_margin = 0.0

    abs_total = abs(y_value) + abs(poly) + abs(x_value)
    scale = 1.0 + abs(y_value) + abs(poly)
    root_scale = max(1.0, math.sqrt(scale))
    log_scale = 1.0 + math.log1p(abs_total)
    n_scale = max(1.0, math.sqrt(n))
    poly_scale = max(1.0, abs(derivative) * max(1.0, abs(x_value)) / max(1.0, len(coeffs)))

    smooth_margin = squash(raw_margin / scale)
    local_margin = squash(raw_margin / root_scale)
    micro_margin = squash(raw_margin / log_scale)
    size_margin = squash(raw_margin / n_scale)
    deriv_margin = squash(raw_margin / (1.0 + math.sqrt(poly_scale)))
    near_positive = sigmoid(raw_margin / root_scale)
    almost_positive = sigmoid(raw_margin / log_scale)
    far_progress = sigmoid(raw_margin / scale)
    deficit = max(0.0, -raw_margin)
    closeness = 1.0 / (1.0 + deficit / root_scale)
    rel_closeness = 1.0 / (1.0 + deficit / scale)

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
    odd_count = 0
    for _, d in G.degree():
        if d == 0:
            isolated_count += 1
        elif d == 1:
            leaves_count += 1
        if d & 1:
            odd_count += 1
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
    odd_frac = float(odd_count) / max(1.0, n)
    max_deg_norm = fget("maximum_degree", max_degree_seen) / max(1.0, n - 1.0)
    min_deg_norm = fget("minimum_degree", min_degree_seen if min_degree_seen is not None else 0.0) / max(1.0, n - 1.0)
    avg_deg_norm = fget("average_degree", avg_degree_seen) / max(1.0, n - 1.0)
    degree_var = max(0.0, degree_sum_sq / max(1.0, n) - avg_degree_seen * avg_degree_seen)
    degree_var_hint = degree_var / max(1.0, n * n)
    irregularity_hint = squash(degree_var / max(1.0, avg_degree_seen + 1.0))
    hub_hint = squash((max_degree_seen - avg_degree_seen) / max(1.0, n))
    leaf_or_iso = min(1.0, leaves + isolated)

    triangles = fget("triangle_number", 0.0) / max(1.0, n * n)
    diameter = fget("diameter", 0.0) / max(1.0, n)
    radius = fget("radius", 0.0) / max(1.0, n)
    clique = fget("clique_number", 0.0) / max(1.0, n)
    independence = fget("independence_number", 0.0) / max(1.0, n)
    matching = fget("matching_number", 0.0) / max(1.0, n)
    chromatic = fget("chromatic_number", 0.0) / max(1.0, n)
    connectivity = max(fget("edge_connectivity", 0.0), fget("vertex_connectivity", 0.0)) / max(1.0, n)

    dense = set(("clique_number", "triangle_number", "size", "density", "maximum_degree", "average_degree",
                 "first_zagreb_index", "second_zagreb_index", "chromatic_number", "matching_number",
                 "edge_connectivity", "vertex_connectivity", "energy", "laplacian_energy", "forgotten_index",
                 "degree_sum", "second_zagreb_index", "harmonic_index"))
    sparse = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                  "independent_domination_number", "vertex_cover_number", "zero_forcing_number",
                  "power_domination_number", "metric_dimension", "path_cover_number", "annihilation_number",
                  "restrained_domination_number", "connected_domination_number", "upper_domination_number",
                  "forcing_number", "feedback_vertex_set_number"))
    distance_like = set(("diameter", "radius", "wiener_index", "hyper_wiener_index", "largest_distance_eigenvalue",
                         "distance_energy", "eccentric_connectivity_index", "gutman_index"))
    tree_like = set(("diameter", "radius", "domination_number", "total_domination_number", "independence_number",
                     "independent_domination_number", "wiener_index", "path_cover_number", "annihilation_number",
                     "zero_forcing_number", "power_domination_number"))

    deriv_mag = squash(abs(derivative) / (1.0 + abs(poly) + abs(y_value)))
    high_norm = norm(wanted_high)
    low_norm = norm(wanted_low)
    x_norm = norm(x_name)
    y_norm = norm(y_name)

    score = 100.0 * violation

    score += 2.62 * smooth_margin
    score += 0.73 * local_margin
    score += 0.10 * micro_margin
    score += 0.038 * size_margin
    score += 0.050 * deriv_margin
    score += 0.135 * near_positive
    score += 0.040 * almost_positive
    score += 0.035 * far_progress
    score += 0.070 * closeness
    score += 0.030 * rel_closeness

    score += 0.270 * high_norm - 0.116 * low_norm
    score += 0.135 * x_direction * deriv_mag * x_norm
    if sign == "<=":
        score += 0.036 * y_norm
    else:
        score -= 0.036 * y_norm

    if wanted_high in dense:
        score += 0.190 * density + 0.106 * triangles + 0.086 * max_deg_norm + 0.047 * avg_deg_norm + 0.025 * clique + 0.019 * chromatic
    if wanted_high in sparse:
        score += 0.153 * (1.0 - density) + 0.096 * leaves + 0.092 * max(diameter, radius) + 0.027 * isolated + 0.026 * independence + 0.020 * hub_hint
    if wanted_high in distance_like:
        score += 0.056 * (1.0 - density) + 0.036 * leaf_or_iso + 0.027 * irregularity_hint + 0.020 * max(diameter, radius)
    if wanted_low in dense:
        score += 0.100 * (1.0 - density) + 0.049 * leaves + 0.034 * max(diameter, radius) + 0.019 * independence
    if wanted_low in sparse:
        score += 0.090 * density + 0.058 * max_deg_norm + 0.032 * triangles + 0.017 * matching + 0.013 * connectivity
    if wanted_low in distance_like:
        score += 0.045 * density + 0.028 * max_deg_norm + 0.013 * avg_deg_norm
    if wanted_high in tree_like and wanted_low in dense:
        score += 0.049 * (1.0 - density) + 0.038 * leaves + 0.013 * hub_hint
    if wanted_high in dense and wanted_low in tree_like:
        score += 0.049 * density + 0.038 * max_deg_norm + 0.013 * triangles

    subgroup = str(getattr(conjecture, "subgroup", "") or "").lower()
    if "tree" in subgroup:
        score += 0.136 * (1.0 - density) + 0.116 * leaves + 0.103 * diameter - 0.050 * triangles - 0.020 * isolated
    if "connected" in subgroup:
        score += 0.030 * min_deg_norm - 0.052 * isolated
    if "regular" in subgroup:
        score -= 0.070 * degree_var_hint + 0.028 * (1.0 - irregularity_hint)
    if "claw_free" in subgroup:
        score += 0.064 * density + 0.043 * triangles - 0.028 * leaves
    if "bipartite" in subgroup:
        score += 0.064 * (1.0 - min(1.0, 12.0 * triangles)) + 0.022 * (1.0 - density) - 0.013 * clique
    if "planar" in subgroup:
        score += 0.037 * (1.0 - density) + 0.022 * min(1.0, avg_degree_seen / 6.0) - 0.011 * max(0.0, avg_degree_seen - 6.0) / max(1.0, n)
    if "eulerian" in subgroup:
        score += 0.025 * min_deg_norm - 0.025 * leaves - 0.021 * odd_frac
    if "cubic" in subgroup:
        score -= 0.019 * abs(avg_degree_seen - 3.0) / max(1.0, n)

    score += 0.0062 * squash((n - 6.0) / 10.0)
    score += 0.0049 * irregularity_hint
    score += 0.0028 * hub_hint

    if not math.isfinite(score):
        score = 0.0
    return float(score)
