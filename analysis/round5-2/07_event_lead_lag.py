from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
REPORT_PATH = OUT_DIR / "07_event_lead_lag.md"

LAGS = [1, 2, 5, 10, 20, 50, 100, 200]
MOTIF_WINDOW = 5
EVENT_Q = 0.95
VOL_ROLL = 100

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

PRODUCT_TO_GROUP = {product: group for group, products in GROUPS.items() for product in products}


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_day_pivots(prices: pd.DataFrame) -> dict[int, pd.DataFrame]:
    return {
        int(day): day_df.pivot(index="timestamp", columns="product", values="mid_price").sort_index()
        for day, day_df in prices.groupby("day")
    }


def safe_mean(values: pd.Series) -> float:
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    return float(values.mean()) if len(values) else float("nan")


def aggregate_event_rows(rows: list[dict]) -> pd.DataFrame:
    raw = pd.DataFrame(rows)
    raw = raw[raw["leader"] != raw["follower"]].copy()
    raw["mean"] = raw["sum_signed"] / raw["n"].replace(0, np.nan)
    keys = ["kind", "lag", "leader", "follower"]
    raw["has_events"] = raw["n"] > 0
    raw["positive_day"] = raw["mean"] > 0
    grouped = (
        raw.groupby(keys, as_index=False)
        .agg(
            n=("n", "sum"),
            sum_signed=("sum_signed", "sum"),
            days=("has_events", "sum"),
            positive_days=("positive_day", "sum"),
            min_day_mean=("mean", "min"),
            max_day_mean=("mean", "max"),
        )
        .copy()
    )
    grouped["mean_markout"] = grouped["sum_signed"] / grouped["n"].replace(0, np.nan)
    grouped["leader_group"] = grouped["leader"].map(PRODUCT_TO_GROUP)
    grouped["follower_group"] = grouped["follower"].map(PRODUCT_TO_GROUP)
    return grouped.drop(columns=["sum_signed"])


def scan_event_markouts(day_pivots: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for day, pivot in day_pivots.items():
        print(f"Scanning event markouts day {day}...")
        products = list(pivot.columns)
        mids = pivot.to_numpy(dtype=float)
        rets = np.diff(mids, axis=0)
        abs_rets = np.abs(rets)
        thresholds = np.nanquantile(abs_rets, EVENT_Q, axis=0)
        thresholds = np.where(thresholds > 0, thresholds, np.inf)
        signs = np.sign(rets)
        rolling_vol = (
            pd.DataFrame(abs_rets, columns=products)
            .rolling(VOL_ROLL, min_periods=20)
            .mean()
            .to_numpy(dtype=float)
        )
        vol_cut = np.nanmedian(rolling_vol, axis=0)

        for lag in LAGS:
            usable = len(rets) - lag
            if usable <= 0:
                continue
            fwd = mids[1 + lag :, :] - mids[1:-lag, :]
            leader_signs = signs[:usable, :]
            large = (abs_rets[:usable, :] >= thresholds[None, :]) & (leader_signs != 0)
            sign_only = leader_signs != 0
            high_vol = rolling_vol[:usable, :] >= vol_cut[None, :]
            masks = {
                "large_move": large,
                "sign_only": sign_only,
                "large_high_vol": large & high_vol,
                "large_low_vol": large & ~high_vol,
            }
            for kind, mask_matrix in masks.items():
                event_signal = leader_signs * mask_matrix
                sums_matrix = event_signal.T @ fwd
                counts = mask_matrix.sum(axis=0).astype(int)
                for leader_idx, leader in enumerate(products):
                    n = int(counts[leader_idx])
                    if n == 0:
                        continue
                    for follower_idx, follower in enumerate(products):
                        rows.append(
                            {
                                "day": day,
                                "kind": kind,
                                "lag": lag,
                                "leader": leader,
                                "follower": follower,
                                "n": n,
                                "sum_signed": float(sums_matrix[leader_idx, follower_idx]),
                            }
                        )
    return aggregate_event_rows(rows)


def event_mask_for_kind(
    kind: str,
    leader_abs_ret: np.ndarray,
    leader_sign: np.ndarray,
    threshold: float,
    leader_rolling_vol: np.ndarray,
    vol_cut: float,
) -> np.ndarray:
    sign_only = leader_sign != 0
    large = (leader_abs_ret >= threshold) & sign_only
    if kind == "large_move":
        return large
    if kind == "sign_only":
        return sign_only
    if kind == "large_high_vol":
        return large & (leader_rolling_vol >= vol_cut)
    if kind == "large_low_vol":
        return large & (leader_rolling_vol < vol_cut)
    raise ValueError(f"Unknown event kind: {kind}")


def enrich_good_pct(day_pivots: dict[int, pd.DataFrame], table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return table
    out = table.copy()
    good_pcts = []
    for _, row in out.iterrows():
        good = 0
        n_total = 0
        for pivot in day_pivots.values():
            products = list(pivot.columns)
            leader_idx = products.index(row["leader"])
            follower_idx = products.index(row["follower"])
            mids = pivot.to_numpy(dtype=float)
            rets = np.diff(mids, axis=0)
            usable = len(rets) - int(row["lag"])
            if usable <= 0:
                continue
            leader_ret = rets[:usable, leader_idx]
            leader_abs = np.abs(rets[:, leader_idx])
            threshold = float(np.nanquantile(leader_abs, EVENT_Q))
            threshold = threshold if threshold > 0 else float("inf")
            rolling_vol = (
                pd.Series(leader_abs)
                .rolling(VOL_ROLL, min_periods=20)
                .mean()
                .to_numpy(dtype=float)
            )
            vol_cut = float(np.nanmedian(rolling_vol))
            mask = event_mask_for_kind(
                row["kind"],
                np.abs(leader_ret),
                np.sign(leader_ret),
                threshold,
                rolling_vol[:usable],
                vol_cut,
            )
            if not np.any(mask):
                continue
            fwd = mids[1 + int(row["lag"]) :, follower_idx] - mids[1 : -int(row["lag"]), follower_idx]
            signed = np.sign(leader_ret[mask]) * fwd[mask]
            good += int(np.sum(signed > 0))
            n_total += int(len(signed))
        good_pcts.append(good / n_total if n_total else float("nan"))
    out["good_pct"] = good_pcts
    return out


def cross_group_summary(events: pd.DataFrame, kind: str) -> pd.DataFrame:
    subset = events[(events["kind"] == kind) & (events["leader_group"] != events["follower_group"])]
    rows = []
    for key, g in subset.groupby(["lag", "leader_group", "follower_group"]):
        weighted = np.average(g["mean_markout"], weights=g["n"])
        rows.append(
            {
                "lag": key[0],
                "leader_group": key[1],
                "follower_group": key[2],
                "n": int(g["n"].sum()),
                "mean_markout": float(weighted),
                "positive_pair_pct": float((g["mean_markout"] > 0).mean()),
                "positive_days_min": int(g["positive_days"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values(["mean_markout", "positive_pair_pct"], ascending=False)


def within_group_motifs(day_pivots: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for day, pivot in day_pivots.items():
        print(f"Scanning within-group motifs day {day}...")
        for group, products in GROUPS.items():
            frame = pivot[products].dropna()
            mids = frame.to_numpy(dtype=float)
            rets = np.diff(mids, axis=0)
            abs_rets = np.abs(rets)
            thresholds = np.nanquantile(abs_rets, EVENT_Q, axis=0)
            thresholds = np.where(thresholds > 0, thresholds, np.inf)
            signs = np.sign(rets)
            usable = len(rets) - MOTIF_WINDOW
            if usable <= 0:
                continue
            for leader_idx, leader in enumerate(products):
                event_idx = np.flatnonzero(
                    (abs_rets[:usable, leader_idx] >= thresholds[leader_idx])
                    & (signs[:usable, leader_idx] != 0)
                )
                if len(event_idx) == 0:
                    continue
                responder_total = 0
                cascade_2 = 0
                cascade_3 = 0
                first_counts = {product: 0 for product in products if product != leader}
                for idx in event_idx:
                    direction = signs[idx, leader_idx]
                    responders = []
                    first_tick_by_product = {}
                    for follower_idx, follower in enumerate(products):
                        if follower_idx == leader_idx:
                            continue
                        window = signs[idx + 1 : idx + 1 + MOTIF_WINDOW, follower_idx]
                        hits = np.flatnonzero(window == direction)
                        if len(hits):
                            responders.append(follower)
                            first_tick_by_product[follower] = int(hits[0])
                    responder_total += len(responders)
                    cascade_2 += int(len(responders) >= 2)
                    cascade_3 += int(len(responders) >= 3)
                    if first_tick_by_product:
                        first_tick = min(first_tick_by_product.values())
                        first = sorted(
                            product
                            for product, tick in first_tick_by_product.items()
                            if tick == first_tick
                        )[0]
                        first_counts[first] += 1
                n = int(len(event_idx))
                top_first, top_first_count = max(first_counts.items(), key=lambda item: item[1])
                rows.append(
                    {
                        "day": day,
                        "group": group,
                        "leader": leader,
                        "n": n,
                        "avg_responders_5t": responder_total / n,
                        "cascade2_pct": cascade_2 / n,
                        "cascade3_pct": cascade_3 / n,
                        "top_first_responder": top_first,
                        "top_first_pct": top_first_count / n,
                    }
                )
    raw = pd.DataFrame(rows)
    out = []
    for (group, leader), g in raw.groupby(["group", "leader"]):
        top = g.groupby("top_first_responder")["top_first_pct"].sum().idxmax()
        out.append(
            {
                "group": group,
                "leader": leader,
                "n": int(g["n"].sum()),
                "days": int(g["day"].nunique()),
                "avg_responders_5t": float(np.average(g["avg_responders_5t"], weights=g["n"])),
                "cascade2_pct": float(np.average(g["cascade2_pct"], weights=g["n"])),
                "cascade3_pct": float(np.average(g["cascade3_pct"], weights=g["n"])),
                "top_first_responder": top,
                "top_first_pct_avg": float(g[g["top_first_responder"] == top]["top_first_pct"].mean()),
            }
        )
    return pd.DataFrame(out).sort_values(
        ["cascade3_pct", "avg_responders_5t", "n"], ascending=False
    )


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


def residual_shock_markouts(day_pivots: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for group in ["PEBBLES", "SNACKPACK", "UV_VISOR", "TRANSLATOR"]:
        print(f"Scanning residual shocks group {group}...")
        products = GROUPS[group]
        combined = pd.concat(
            [pivot[products] for pivot in day_pivots.values()], keys=day_pivots.keys()
        ).dropna()
        for target in products:
            components = [product for product in products if product != target]
            y = combined[target].to_numpy(dtype=float)
            x = combined[components].to_numpy(dtype=float)
            x_design = np.column_stack([np.ones(len(x)), x])
            coef = np.linalg.lstsq(x_design, y, rcond=None)[0]
            full_resid = y - x_design @ coef
            sigma = float(np.std(full_resid))
            if sigma <= 1e-12:
                continue
            for day, pivot in day_pivots.items():
                frame = pivot[products].dropna()
                day_y = frame[target].to_numpy(dtype=float)
                day_x = frame[components].to_numpy(dtype=float)
                resid = day_y - np.column_stack([np.ones(len(day_x)), day_x]) @ coef
                z = resid / sigma
                shock_base = np.abs(z) >= 2.0
                for lag in LAGS:
                    usable = len(resid) - lag
                    if usable <= 0:
                        continue
                    shock = shock_base[:usable]
                    n = int(shock.sum())
                    if n == 0:
                        continue
                    direction = -np.sign(resid[:usable][shock])
                    target_delta = day_y[lag:] - day_y[:-lag]
                    resid_delta = resid[lag:] - resid[:-lag]
                    target_markout = direction * target_delta[shock]
                    resid_reversion = direction * resid_delta[shock]
                    rows.append(
                        {
                            "day": day,
                            "group": group,
                            "target": target,
                            "lag": lag,
                            "n": n,
                            "target_sum": float(np.sum(target_markout)),
                            "resid_sum": float(np.sum(resid_reversion)),
                            "good": int(np.sum(target_markout > 0)),
                            "resid_sigma": sigma,
                            "adf_t": adf_t_stat(full_resid),
                        }
                    )
    raw = pd.DataFrame(rows)
    out = []
    for key, g in raw.groupby(["group", "target", "lag"]):
        n = int(g["n"].sum())
        day_means = g.assign(mean=lambda x: x["target_sum"] / x["n"]).set_index("day")["mean"]
        out.append(
            {
                "group": key[0],
                "target": key[1],
                "lag": key[2],
                "n": n,
                "days": int(g["day"].nunique()),
                "positive_days": int((day_means > 0).sum()),
                "mean_target_markout": float(g["target_sum"].sum() / n),
                "good_pct": float(g["good"].sum() / n),
                "mean_resid_reversion": float(g["resid_sum"].sum() / n),
                "resid_sigma": float(g["resid_sigma"].mean()),
                "adf_t": float(g["adf_t"].mean()),
                "min_day_target_markout": float(day_means.min()),
            }
        )
    return pd.DataFrame(out).sort_values(
        ["mean_resid_reversion", "mean_target_markout"], ascending=False
    )


def top_event_table(events: pd.DataFrame, kind: str, n_min: int, require_all_days: bool = True) -> pd.DataFrame:
    table = events[(events["kind"] == kind) & (events["n"] >= n_min)].copy()
    if require_all_days:
        table = table[(table["days"] == 3) & (table["positive_days"] == 3)]
    return table.sort_values(["mean_markout", "n"], ascending=False)


def fmt_table(df: pd.DataFrame, cols: list[str], n: int, decimals: int = 4) -> str:
    if df.empty:
        return "No rows passed the filter."
    return df.head(n)[cols].round(decimals).to_markdown(index=False)


def write_report(
    day_pivots: dict[int, pd.DataFrame],
    events: pd.DataFrame,
    cross_groups: pd.DataFrame,
    motifs: pd.DataFrame,
    residuals: pd.DataFrame,
    spread_by_product: pd.Series,
) -> None:
    large = top_event_table(events, "large_move", n_min=250)
    sign_only = top_event_table(events, "sign_only", n_min=5_000)
    high_vol = top_event_table(events, "large_high_vol", n_min=100)
    low_vol = top_event_table(events, "large_low_vol", n_min=100)
    residual_candidates = residuals[
        (residuals["days"] == 3)
        & (residuals["positive_days"] == 3)
        & (residuals["n"] >= 100)
        & (residuals["mean_resid_reversion"] > 0)
    ].sort_values(["mean_resid_reversion", "mean_target_markout"], ascending=False)
    pebbles_fast = residual_candidates[
        (residual_candidates["group"] == "PEBBLES") & (residual_candidates["lag"] <= 20)
    ].sort_values(["mean_resid_reversion", "mean_target_markout"], ascending=False)

    for table in [large, sign_only, high_vol, low_vol]:
        if not table.empty:
            table["follower_median_spread"] = table["follower"].map(spread_by_product)
            table["markout_to_spread"] = table["mean_markout"] / table["follower_median_spread"]

    large = enrich_good_pct(day_pivots, large.head(50))
    sign_only = enrich_good_pct(day_pivots, sign_only.head(50))
    high_vol = enrich_good_pct(day_pivots, high_vol.head(40))
    low_vol = enrich_good_pct(day_pivots, low_vol.head(40))

    lines = [
        "# Round 5 Lens 3 - Event Lead-Lag and Regime Signals",
        "",
        "Data: `data/ROUND5` prices, days 2, 3, and 4. Markouts are midpoint-to-midpoint after the leader move is observable: if a leader return from `t` to `t+1` has sign `s`, follower markout is `s * (mid[t+1+lag] - mid[t+1])`.",
        f"Large-move events are product/day moves at or above the {EVENT_Q:.0%} absolute-return quantile. Volatility regimes use a {VOL_ROLL}-tick rolling mean absolute return split at each product/day median.",
        "",
        "## Actionable Read",
        "",
    ]

    if not residual_candidates.empty:
        best = residual_candidates.iloc[0]
        lines.append(
            f"- Strongest delayed residual-shock candidate is {best['target']} ({best['group']}) at lag {int(best['lag'])}: mean residual reversion {best['mean_resid_reversion']:.4f}, target-only markout {best['mean_target_markout']:.4f}, good_pct {best['good_pct']:.3f}, n={int(best['n'])}, positive on {int(best['positive_days'])}/3 days. This is a slow 100-200 tick research candidate, not the first implementation."
        )
    if not pebbles_fast.empty:
        best = pebbles_fast.iloc[0]
        lines.append(
            f"- Best fast PEBBLES residual shock is {best['target']} at lag {int(best['lag'])}: mean residual reversion {best['mean_resid_reversion']:.4f}, target-only markout {best['mean_target_markout']:.4f}, good_pct {best['good_pct']:.3f}, n={int(best['n'])}, ADF t {best['adf_t']:.2f}. This supports the existing PEBBLES basket-arb priority."
        )
    if not large.empty:
        best = large.iloc[0]
        lines.append(
            f"- Best persistent large-move follower pair is {best['leader']} -> {best['follower']} at lag {int(best['lag'])}: mean markout {best['mean_markout']:.4f}, good_pct {best['good_pct']:.3f}, n={int(best['n'])}, but only {best['markout_to_spread']:.3f}x follower median spread."
        )
    if not sign_only.empty:
        best = sign_only.iloc[0]
        lines.append(
            f"- Best sign-only pair is {best['leader']} -> {best['follower']} at lag {int(best['lag'])}: mean markout {best['mean_markout']:.4f}, good_pct {best['good_pct']:.3f}, n={int(best['n'])}; this is too small versus spread for standalone crossing."
        )
    if not high_vol.empty and not low_vol.empty:
        best_h = high_vol.iloc[0]
        same_low = low_vol[
            (low_vol["leader"] == best_h["leader"])
            & (low_vol["follower"] == best_h["follower"])
            & (low_vol["lag"] == best_h["lag"])
        ]
        if not same_low.empty:
            low = same_low.iloc[0]
            lines.append(
                f"- Volatility conditioning changes magnitude but not enough to create a new strategy: {best_h['leader']} -> {best_h['follower']} lag {int(best_h['lag'])} high-vol mean {best_h['mean_markout']:.4f} vs low-vol {low['mean_markout']:.4f}."
            )
    lines.extend(
        [
            "",
            "## Persistent Large-Move Pair Markouts",
            "",
            fmt_table(
                large,
                [
                    "lag",
                    "leader",
                    "follower",
                    "leader_group",
                    "follower_group",
                    "n",
                    "mean_markout",
                    "good_pct",
                    "min_day_mean",
                    "follower_median_spread",
                    "markout_to_spread",
                ],
                15,
            ),
            "",
            "## Persistent Sign-Only Pair Markouts",
            "",
            fmt_table(
                sign_only,
                [
                    "lag",
                    "leader",
                    "follower",
                    "leader_group",
                    "follower_group",
                    "n",
                    "mean_markout",
                    "good_pct",
                    "min_day_mean",
                    "follower_median_spread",
                    "markout_to_spread",
                ],
                15,
            ),
            "",
            "## Volatility-Regime Conditioned Large Moves",
            "",
            "High-volatility leader events:",
            "",
            fmt_table(
                high_vol,
                [
                    "lag",
                    "leader",
                    "follower",
                    "n",
                    "mean_markout",
                    "good_pct",
                    "min_day_mean",
                    "markout_to_spread",
                ],
                10,
            ),
            "",
            "Low-volatility leader events:",
            "",
            fmt_table(
                low_vol,
                [
                    "lag",
                    "leader",
                    "follower",
                    "n",
                    "mean_markout",
                    "good_pct",
                    "min_day_mean",
                    "markout_to_spread",
                ],
                10,
            ),
            "",
            "## Cross-Group Leader Categories",
            "",
            "Top aggregate large-move cross-group markouts. `positive_pair_pct` is the share of product-pair cells inside the group pair with positive conditional mean.",
            "",
            fmt_table(
                cross_groups[cross_groups["n"] >= 5_000],
                [
                    "lag",
                    "leader_group",
                    "follower_group",
                    "n",
                    "mean_markout",
                    "positive_pair_pct",
                    "positive_days_min",
                ],
                20,
            ),
            "",
            "## Within-Group Sequence Motifs",
            "",
            fmt_table(
                motifs[motifs["days"] == 3],
                [
                    "group",
                    "leader",
                    "n",
                    "avg_responders_5t",
                    "cascade2_pct",
                    "cascade3_pct",
                    "top_first_responder",
                    "top_first_pct_avg",
                ],
                20,
            ),
            "",
            "## Delayed Mean Reversion After Basket Residual Shocks",
            "",
            fmt_table(
                residual_candidates,
                [
                    "group",
                    "target",
                    "lag",
                    "n",
                    "mean_resid_reversion",
                    "mean_target_markout",
                    "good_pct",
                    "min_day_target_markout",
                    "resid_sigma",
                    "adf_t",
                ],
                25,
            ),
            "",
            "## Interpretation",
            "",
            "- Large-move lead-lag effects can reach roughly one median spread at long lags, but hit rates are only slightly above coin-flip; sign-only effects are smaller. Treat them as inventory skew context unless a simulator confirms executable edge.",
            "- Cross-group leader categories do not produce a clean tradable hierarchy; the best aggregate effects are diluted across product pairs, and hit rates stay close to coin-flip at the pair level.",
            "- Within-group motifs are useful diagnostics for synchronized groups, not a standalone trigger: high cascade rates mostly identify simultaneous group movement after a large print.",
            "- Residual shock reversion is the only lens here that produces persistent conditional markouts. Slow TRANSLATOR/UV/SNACKPACK shocks deserve follow-up, while fast PEBBLES shocks remain the cleanest implementation path because the basket relation is already structurally confirmed.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    day_pivots = make_day_pivots(prices)
    spread_by_product = prices.groupby("product")["spread"].median()

    events = scan_event_markouts(day_pivots)
    cross_groups = cross_group_summary(events, "large_move")
    motifs = within_group_motifs(day_pivots)
    residuals = residual_shock_markouts(day_pivots)
    write_report(day_pivots, events, cross_groups, motifs, residuals, spread_by_product)

    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
