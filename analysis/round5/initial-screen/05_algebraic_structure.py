import itertools
import math
from fractions import Fraction
from functools import reduce
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")

GROUPS = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": [
        "ROBOT_VACUUMING",
        "ROBOT_MOPPING",
        "ROBOT_DISHES",
        "ROBOT_LAUNDRY",
        "ROBOT_IRONING",
    ],
    "UV_VISOR": [
        "UV_VISOR_YELLOW",
        "UV_VISOR_AMBER",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_MAGENTA",
    ],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
}

Z_LEVELS = [1.5, 2.0, 2.5, 3.0]
HORIZONS = [1, 5, 20, 100]


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices


def gcd_many(values: tuple[int, ...]) -> int:
    nonzero = [abs(v) for v in values if v != 0]
    if not nonzero:
        return 1
    return reduce(math.gcd, nonzero)


def canonical_coeff(coeff: tuple[int, ...]) -> tuple[int, ...] | None:
    if all(v == 0 for v in coeff):
        return None
    g = gcd_many(coeff)
    coeff = tuple(v // g for v in coeff)
    first = next(v for v in coeff if v != 0)
    if first < 0:
        coeff = tuple(-v for v in coeff)
    return coeff


def coefficient_grid(n: int = 5, max_abs: int = 4, max_l1: int = 8) -> np.ndarray:
    seen = set()
    rows = []
    for coeff in itertools.product(range(-max_abs, max_abs + 1), repeat=n):
        if sum(v != 0 for v in coeff) < 2:
            continue
        if sum(abs(v) for v in coeff) > max_l1:
            continue
        canon = canonical_coeff(coeff)
        if canon is None or canon in seen:
            continue
        seen.add(canon)
        rows.append(canon)
    return np.array(rows, dtype=float)


COEFF_GRID = coefficient_grid()


def adf_t_stat(resid: np.ndarray) -> float:
    if len(resid) < 20:
        return float("nan")
    lag = resid[:-1]
    de = np.diff(resid)
    x = np.column_stack([np.ones_like(lag), lag])
    try:
        coef = np.linalg.lstsq(x, de, rcond=None)[0]
        err = de - x @ coef
        dof = max(1, len(de) - x.shape[1])
        sigma2 = float(err @ err / dof)
        inv = np.linalg.inv(x.T @ x)
        se = math.sqrt(max(0.0, sigma2 * inv[1, 1]))
        return float(coef[1] / se) if se > 1e-12 else float("nan")
    except np.linalg.LinAlgError:
        return float("nan")


def acf1(resid: np.ndarray) -> float:
    if len(resid) < 3:
        return float("nan")
    a = resid[:-1]
    b = resid[1:]
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def half_life(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0 or phi >= 1:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def day_demeaned(series: np.ndarray, days: np.ndarray) -> np.ndarray:
    out = series.astype(float).copy()
    for day in np.unique(days):
        mask = days == day
        out[mask] -= float(out[mask].mean())
    return out


def coeff_label(products: list[str], coeff: np.ndarray) -> str:
    parts = []
    for product, value in zip(products, coeff):
        ivalue = int(round(value))
        if ivalue == 0:
            continue
        parts.append(f"{ivalue:+d}*{product}")
    return " ".join(parts).lstrip("+")


def rounded_int_vector(vec: np.ndarray, max_denominator: int = 8) -> np.ndarray:
    if np.max(np.abs(vec)) <= 1e-12:
        return np.zeros_like(vec, dtype=int)
    scaled = vec / np.max(np.abs(vec))
    fracs = [Fraction(float(v)).limit_denominator(max_denominator) for v in scaled]
    lcm = 1
    for frac in fracs:
        lcm = math.lcm(lcm, frac.denominator)
    ints = np.array([frac.numerator * (lcm // frac.denominator) for frac in fracs], dtype=int)
    g = gcd_many(tuple(int(v) for v in ints))
    if g > 0:
        ints = ints // g
    first_nonzero = next((v for v in ints if v != 0), 1)
    if first_nonzero < 0:
        ints = -ints
    return ints


def residual_metrics(series: np.ndarray, days: np.ndarray) -> dict[str, float]:
    resid = series - float(np.mean(series))
    day_resid = day_demeaned(series, days)
    daily_sd = []
    daily_adf = []
    daily_hl = []
    for day in sorted(np.unique(days)):
        r = day_resid[days == day]
        phi = acf1(r)
        daily_sd.append(float(np.std(r)))
        daily_adf.append(adf_t_stat(r))
        daily_hl.append(half_life(phi))
    abs_resid = np.abs(day_resid)
    phi = acf1(day_resid)
    day_means = [float(np.mean(series[days == day])) for day in sorted(np.unique(days))]
    return {
        "resid_mean": float(np.mean(series)),
        "resid_sd": float(np.std(day_resid)),
        "resid_sd_full_intercept": float(np.std(resid)),
        "resid_range": float(np.max(day_resid) - np.min(day_resid)),
        "resid_p50_abs": float(np.quantile(abs_resid, 0.50)),
        "resid_p90_abs": float(np.quantile(abs_resid, 0.90)),
        "resid_p95_abs": float(np.quantile(abs_resid, 0.95)),
        "resid_p99_abs": float(np.quantile(abs_resid, 0.99)),
        "resid_max_abs": float(np.max(abs_resid)),
        "resid_acf1": phi,
        "half_life": half_life(phi),
        "adf_t": adf_t_stat(day_resid),
        "adf_days_lt_-2_8": int(sum(np.isfinite(v) and v < -2.8 for v in daily_adf)),
        "daily_sd_min": float(np.min(daily_sd)),
        "daily_sd_max": float(np.max(daily_sd)),
        "daily_half_life_max": float(np.max(daily_hl)),
        "day_mean_min": float(np.min(day_means)),
        "day_mean_max": float(np.max(day_means)),
        "day_mean_range": float(np.max(day_means) - np.min(day_means)),
    }


def relation_row(
    group: str,
    products: list[str],
    relation_type: str,
    coeff: np.ndarray,
    values: np.ndarray,
    days: np.ndarray,
    spreads: dict[str, float],
) -> dict[str, object]:
    series = values @ coeff
    metrics = residual_metrics(series, days)
    l1 = float(np.sum(np.abs(coeff)))
    l2 = float(np.sqrt(np.sum(coeff * coeff)))
    median_half_spread = float(np.median([spreads[p] for p in products]) / 2.0)
    one_way_cost = float(sum(abs(c) * spreads[p] / 2.0 for p, c in zip(products, coeff)))
    round_trip_cost = 2.0 * one_way_cost
    sd = metrics["resid_sd"]
    row = {
        "group": group,
        "relation_type": relation_type,
        "coefficients": ",".join(str(int(round(v))) for v in coeff),
        "relation": coeff_label(products, coeff),
        "nonzero_terms": int(np.sum(np.abs(coeff) > 1e-12)),
        "l1_abs_coeff": l1,
        "l2_abs_coeff": l2,
        "resid_sd_per_l1": sd / l1 if l1 > 0 else float("nan"),
        "one_way_cross_cost": one_way_cost,
        "round_trip_cross_cost": round_trip_cost,
        "round_trip_cost_z": round_trip_cost / sd if sd > 1e-12 else float("inf"),
        "median_half_spread_z": median_half_spread / sd if sd > 1e-12 else float("inf"),
        **metrics,
    }
    return row


def threshold_rows(
    group: str,
    products: list[str],
    coeff: np.ndarray,
    relation_type: str,
    values: np.ndarray,
    days: np.ndarray,
) -> list[dict[str, object]]:
    series = values @ coeff
    resid = day_demeaned(series, days)
    sigma = float(np.std(resid))
    if sigma <= 1e-12:
        return []
    rows = []
    for z in Z_LEVELS:
        threshold = z * sigma
        mask_base = np.abs(resid) >= threshold
        for horizon in HORIZONS:
            valid = np.zeros(len(resid), dtype=bool)
            for day in np.unique(days):
                idx = np.flatnonzero(days == day)
                valid[idx[:-horizon]] = True
            mask = mask_base & valid
            current = resid[mask]
            future = resid[np.flatnonzero(mask) + horizon]
            if len(current) == 0:
                mean_improve = 0.0
                good_pct = 0.0
            else:
                improve = np.sign(current) * (current - future)
                mean_improve = float(np.mean(improve))
                good_pct = float(np.mean(improve > 0.0))
            rows.append(
                {
                    "group": group,
                    "relation_type": relation_type,
                    "coefficients": ",".join(str(int(round(v))) for v in coeff),
                    "relation": coeff_label(products, coeff),
                    "z": z,
                    "threshold_points": threshold,
                    "horizon": horizon,
                    "trigger_n": int(len(current)),
                    "trigger_pct": float(len(current) / len(resid)),
                    "mean_reversion_points": mean_improve,
                    "good_pct": good_pct,
                }
            )
    return rows


def fit_target_basket(pivot: pd.DataFrame, target: str, components: list[str]) -> dict[str, float]:
    frame = pivot[[target] + components].dropna()
    y = frame[target].to_numpy(dtype=float)
    x = frame[components].to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    coef = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ coef
    return {
        "alpha": float(coef[0]),
        **{f"beta_{component}": float(beta) for component, beta in zip(components, coef[1:])},
        "r2": float(1.0 - np.var(resid) / np.var(y)) if np.var(y) > 1e-12 else float("nan"),
        "resid_sd": float(np.std(resid)),
        "adf_t": adf_t_stat(resid),
        "half_life": half_life(acf1(resid)),
    }


def basket_stability(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, products in GROUPS.items():
        g = prices[prices["product"].isin(products)]
        full_pivot = g.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        for target in products:
            components = [p for p in products if p != target]
            full = fit_target_basket(full_pivot, target, components)
            day_betas = []
            day_r2 = []
            day_sd = []
            day_hl = []
            for day, day_df in g.groupby("day"):
                day_pivot = day_df.pivot(index="timestamp", columns="product", values="mid_price")
                dm = fit_target_basket(day_pivot, target, components)
                betas = [dm[f"beta_{component}"] for component in components]
                day_betas.append(betas)
                day_r2.append(dm["r2"])
                day_sd.append(dm["resid_sd"])
                day_hl.append(dm["half_life"])
                for key, value in dm.items():
                    if key == "alpha":
                        continue
                    rows_key = f"d{int(day)}_{key}"
                    full[rows_key] = value
            beta_arr = np.array(day_betas, dtype=float)
            mean_beta = beta_arr.mean(axis=0)
            max_beta_abs_dev = float(np.max(np.abs(beta_arr - mean_beta)))
            mean_abs_beta = float(np.mean(np.abs(mean_beta)))
            rows.append(
                {
                    "group": group,
                    "target": target,
                    "components": ",".join(components),
                    "r2": full["r2"],
                    "resid_sd": full["resid_sd"],
                    "adf_t": full["adf_t"],
                    "half_life": full["half_life"],
                    "min_day_r2": float(np.min(day_r2)),
                    "max_day_resid_sd": float(np.max(day_sd)),
                    "max_day_half_life": float(np.max(day_hl)),
                    "max_beta_abs_dev": max_beta_abs_dev,
                    "beta_stability_ratio": max_beta_abs_dev / mean_abs_beta if mean_abs_beta > 1e-12 else float("inf"),
                    **{k: v for k, v in full.items() if k.startswith("beta_")},
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["r2", "resid_sd", "max_beta_abs_dev"], ascending=[False, True, True]
    )


def pca_rows(group: str, products: list[str], values: np.ndarray, days: np.ndarray) -> tuple[dict[str, object], np.ndarray]:
    demeaned = np.column_stack([day_demeaned(values[:, i], days) for i in range(values.shape[1])])
    cov = np.cov(demeaned, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    total = float(np.sum(eigvals))
    smallest_vec = eigvecs[:, -1]
    if np.sum(smallest_vec) < 0:
        smallest_vec = -smallest_vec
    smallest_int = rounded_int_vector(smallest_vec, max_denominator=8)
    day_cosines = []
    for day in sorted(np.unique(days)):
        day_values = values[days == day]
        day_demean = day_values - day_values.mean(axis=0, keepdims=True)
        day_cov = np.cov(day_demean, rowvar=False)
        _, day_vecs = np.linalg.eigh(day_cov)
        day_small = day_vecs[:, 0]
        cosine = float(np.dot(day_small, smallest_vec) / (np.linalg.norm(day_small) * np.linalg.norm(smallest_vec)))
        day_cosines.append(abs(cosine))
    row = {
        "group": group,
        "pc1_var_share": float(eigvals[0] / total) if total > 0 else float("nan"),
        "pc2_var_share": float(eigvals[1] / total) if total > 0 else float("nan"),
        "smallest_var": float(eigvals[-1]),
        "smallest_var_share": float(eigvals[-1] / total) if total > 0 else float("nan"),
        "condition_pc1_to_smallest": float(eigvals[0] / eigvals[-1]) if eigvals[-1] > 1e-12 else float("inf"),
        "smallest_vec": ",".join(f"{v:.6f}" for v in smallest_vec),
        "smallest_int_coefficients": ",".join(str(int(v)) for v in smallest_int),
        "smallest_int_relation": coeff_label(products, smallest_int),
        "min_day_smallest_vec_abs_cosine": float(np.min(day_cosines)),
    }
    return row, smallest_int.astype(float)


def scan_integer_relations(
    group: str,
    products: list[str],
    values: np.ndarray,
    days: np.ndarray,
    spreads: dict[str, float],
) -> list[dict[str, object]]:
    demeaned = np.column_stack([day_demeaned(values[:, i], days) for i in range(values.shape[1])])
    cov = np.cov(demeaned, rowvar=False)
    variances = np.einsum("ij,jk,ik->i", COEFF_GRID, cov, COEFF_GRID)
    l1 = np.sum(np.abs(COEFF_GRID), axis=1)
    score = np.sqrt(np.maximum(variances, 0.0)) / l1
    best_idx = np.argsort(score)[:80]
    rows = []
    seen = set()
    for idx in best_idx:
        coeff = COEFF_GRID[idx]
        key = tuple(int(v) for v in coeff)
        if key in seen:
            continue
        seen.add(key)
        rows.append(relation_row(group, products, "integer_search", coeff, values, days, spreads))
    return rows


def signed_index_relations(
    group: str,
    products: list[str],
    values: np.ndarray,
    days: np.ndarray,
    spreads: dict[str, float],
) -> list[dict[str, object]]:
    rows = []
    for signs in itertools.product([-1, 1], repeat=len(products)):
        if signs[0] < 0:
            continue
        coeff = np.array(signs, dtype=float)
        if np.all(coeff == 1) or np.any(coeff < 0):
            rows.append(relation_row(group, products, "signed_index", coeff, values, days, spreads))
    return rows


def pair_sign_rows(group: str, products: list[str], values: np.ndarray, days: np.ndarray) -> list[dict[str, object]]:
    rows = []
    for i, a in enumerate(products):
        for j, b in enumerate(products[i + 1 :], start=i + 1):
            xa = day_demeaned(values[:, i], days)
            xb = day_demeaned(values[:, j], days)
            ra = np.diff(values[:, i])
            rb = np.diff(values[:, j])
            same_day = days[1:] == days[:-1]
            ra = ra[same_day]
            rb = rb[same_day]
            corr_mid = float(np.corrcoef(xa, xb)[0, 1]) if np.std(xa) > 0 and np.std(xb) > 0 else float("nan")
            corr_ret = float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else float("nan")
            daily_corrs = []
            for day in sorted(np.unique(days)):
                mask = days == day
                da = values[mask, i]
                db = values[mask, j]
                if np.std(da) > 0 and np.std(db) > 0:
                    daily_corrs.append(float(np.corrcoef(da, db)[0, 1]))
            rows.append(
                {
                    "group": group,
                    "a": a,
                    "b": b,
                    "corr_mid_day_demeaned": corr_mid,
                    "corr_ret": corr_ret,
                    "min_abs_daily_mid_corr": float(np.min(np.abs(daily_corrs))) if daily_corrs else float("nan"),
                    "same_sign": bool(corr_mid > 0),
                    "sign_flipped": bool(corr_mid < 0),
                }
            )
    return rows


def write_report(
    group_summary: pd.DataFrame,
    relations: pd.DataFrame,
    thresholds: pd.DataFrame,
    basket: pd.DataFrame,
    pairs: pd.DataFrame,
) -> None:
    bounded = relations[relations["relation_type"] == "integer_search"].copy()
    best_by_group = bounded.sort_values(["resid_sd_per_l1", "resid_sd"]).groupby("group").head(1)
    best_nonpair = (
        bounded[bounded["nonzero_terms"] >= 3]
        .sort_values(["resid_sd_per_l1", "resid_sd"])
        .groupby("group")
        .head(1)
    )
    top_threshold = thresholds[
        (thresholds["z"] == 2.5) & (thresholds["horizon"] == 20)
    ].sort_values(["mean_reversion_points", "good_pct", "trigger_n"], ascending=False)
    best_basket = basket.groupby("group").head(1)
    top_neg_pairs = pairs.sort_values("corr_mid_day_demeaned").head(15)

    lines = [
        "# Round 5 Lens 1 - Algebraic Structure",
        "",
        "Scope: all 10 Round 5 product groups, days 2/3/4. Prices use mid-price.",
        "Residual metrics for integer and signed-index identities are day-demeaned, so coefficients must stay fixed while each day may have its own intercept.",
        "ADF is the same lightweight ADF(0) t-statistic used by earlier round 5 notebooks.",
        "",
        "## Top Findings",
        "",
        "- **PEBBLES has a near-exact equal-weight sum identity.** The best integer relation is `+1` on all five PEBBLES products with residual sigma "
        f"{float(best_by_group[best_by_group['group'] == 'PEBBLES']['resid_sd'].iloc[0]):.6f}, "
        f"p95 abs residual {float(best_by_group[best_by_group['group'] == 'PEBBLES']['resid_p95_abs'].iloc[0]):.6f}, "
        f"ADF t {float(best_by_group[best_by_group['group'] == 'PEBBLES']['adf_t'].iloc[0]):.6f}, "
        f"half-life {float(best_by_group[best_by_group['group'] == 'PEBBLES']['half_life'].iloc[0]):.6f} ticks. "
        "This is the algebraic source of the prior PEBBLES 1-vs-4 basket result: every coefficient is effectively `-1` against the other four.",
        "- **Crossing the whole PEBBLES basket is not attractive by spread math.** For the all-five sum, the estimated round-trip crossing cost is "
        f"{float(best_by_group[best_by_group['group'] == 'PEBBLES']['round_trip_cross_cost'].iloc[0]):.6f}, or "
        f"{float(best_by_group[best_by_group['group'] == 'PEBBLES']['round_trip_cost_z'].iloc[0]):.2f} residual sigmas. "
        "Use it as a fair-value/skew anchor, not a market-order basket.",
        "- **SNACKPACK has strong sign-flipped pairs but no fast algebraic identity.** The most negative pair is "
        f"{top_neg_pairs.iloc[0]['a']} vs {top_neg_pairs.iloc[0]['b']} with day-demeaned mid corr "
        f"{float(top_neg_pairs.iloc[0]['corr_mid_day_demeaned']):.6f} and return corr {float(top_neg_pairs.iloc[0]['corr_ret']):.6f}; "
        "the best multi-term integer residual is still much wider and slower than PEBBLES.",
        "- **No other group shows a PEBBLES-grade null dimension.** The next best non-pair integer relation by residual sigma per unit coefficient is "
        f"{best_nonpair[best_nonpair['group'] != 'PEBBLES'].iloc[0]['group']} with resid_sd_per_l1 "
        f"{float(best_nonpair[best_nonpair['group'] != 'PEBBLES'].iloc[0]['resid_sd_per_l1']):.6f}, versus PEBBLES "
        f"{float(best_nonpair[best_nonpair['group'] == 'PEBBLES']['resid_sd_per_l1'].iloc[0]):.6f}.",
        "",
        "## PCA / Null Structure By Group",
        "",
        group_summary[
            [
                "group",
                "pc1_var_share",
                "smallest_var_share",
                "condition_pc1_to_smallest",
                "min_day_smallest_vec_abs_cosine",
                "smallest_int_relation",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Best Bounded Small-Integer Relation Per Group",
        "",
        best_by_group[
            [
                "group",
                "relation",
                "resid_sd",
                "resid_sd_per_l1",
                "resid_p95_abs",
                "adf_t",
                "adf_days_lt_-2_8",
                "half_life",
                "daily_half_life_max",
                "round_trip_cross_cost",
                "round_trip_cost_z",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Best Non-Pair Small-Integer Relation Per Group",
        "",
        best_nonpair[
            [
                "group",
                "relation",
                "nonzero_terms",
                "resid_sd",
                "resid_sd_per_l1",
                "resid_p95_abs",
                "adf_t",
                "half_life",
                "round_trip_cost_z",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Day-Stable 1-vs-4 Basket Fits",
        "",
        best_basket[
            [
                "group",
                "target",
                "r2",
                "min_day_r2",
                "resid_sd",
                "adf_t",
                "half_life",
                "max_day_half_life",
                "max_beta_abs_dev",
                "beta_stability_ratio",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Executable Threshold Lens",
        "",
        "Rows below use each group's best bounded small-integer relation. `mean_reversion_points` is signed residual improvement after 20 ticks when `|residual| >= 2.5 sigma`.",
        "",
        top_threshold.head(20)[
            [
                "group",
                "relation",
                "z",
                "threshold_points",
                "horizon",
                "trigger_n",
                "trigger_pct",
                "mean_reversion_points",
                "good_pct",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Strongest Sign-Flipped Pairs",
        "",
        top_neg_pairs[
            ["group", "a", "b", "corr_mid_day_demeaned", "corr_ret", "min_abs_daily_mid_corr"]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- Promote **PEBBLES algebraic fair value** first: equal-weight group sum and target-vs-other-four forms are equivalent enough for implementation.",
        "- Treat **SNACKPACK** as slower sign-flipped structure only. It has useful correlation evidence, but threshold reversion and spread/cost math are weaker than PEBBLES.",
        "- Do not allocate implementation effort to hidden integer baskets in the remaining eight groups from this lens; their residual scales, PCA null shares, and day-stability are not competitive.",
    ]
    (OUT_DIR / "05_algebraic_structure.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    spreads = prices.groupby("product")["spread"].median().to_dict()
    relation_rows = []
    threshold_rows_out = []
    pca_out = []
    pair_rows_out = []

    for group, products in GROUPS.items():
        g = prices[prices["product"].isin(products)].copy()
        pivot = g.pivot(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()
        pivot = pivot.reindex(columns=products)
        values = pivot.to_numpy(dtype=float)
        days = pivot.index.get_level_values("day").to_numpy()

        pca_row, pca_int = pca_rows(group, products, values, days)
        pca_out.append(pca_row)
        pca_key = tuple(int(v) for v in pca_int)

        rows = scan_integer_relations(group, products, values, days, spreads)
        if any(pca_int) and pca_key not in {tuple(int(float(x)) for x in row["coefficients"].split(",")) for row in rows}:
            rows.append(relation_row(group, products, "pca_smallest_rational", pca_int, values, days, spreads))
        rows.extend(signed_index_relations(group, products, values, days, spreads))
        relation_rows.extend(rows)

        bounded_rows = pd.DataFrame(rows)
        best = (
            bounded_rows[bounded_rows["relation_type"] == "integer_search"]
            .sort_values(["resid_sd_per_l1", "resid_sd"])
            .iloc[0]
        )
        coeff = np.array([int(x) for x in best["coefficients"].split(",")], dtype=float)
        threshold_rows_out.extend(
            threshold_rows(group, products, coeff, "best_integer", values, days)
        )
        pair_rows_out.extend(pair_sign_rows(group, products, values, days))

    relations = pd.DataFrame(relation_rows).sort_values(
        ["resid_sd_per_l1", "resid_sd", "nonzero_terms"]
    )
    group_summary = pd.DataFrame(pca_out).sort_values("smallest_var_share")
    thresholds = pd.DataFrame(threshold_rows_out)
    basket = basket_stability(prices)
    pairs = pd.DataFrame(pair_rows_out)

    group_summary.to_csv(OUT_DIR / "05_group_pca_summary.csv", index=False)
    relations.to_csv(OUT_DIR / "05_integer_relations.csv", index=False)
    thresholds.to_csv(OUT_DIR / "05_threshold_reversion.csv", index=False)
    basket.to_csv(OUT_DIR / "05_basket_stability.csv", index=False)
    pairs.to_csv(OUT_DIR / "05_sign_pairs.csv", index=False)
    write_report(group_summary, relations, thresholds, basket, pairs)

    print("Wrote:")
    for name in [
        "05_algebraic_structure.md",
        "05_group_pca_summary.csv",
        "05_integer_relations.csv",
        "05_threshold_reversion.csv",
        "05_basket_stability.csv",
        "05_sign_pairs.csv",
    ]:
        print(f"- {OUT_DIR / name}")


if __name__ == "__main__":
    main()
