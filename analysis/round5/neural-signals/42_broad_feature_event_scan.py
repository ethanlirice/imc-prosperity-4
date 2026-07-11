#!/usr/bin/env python3
"""
Round 5 broad feature/event scanner.

Research-only candidate generator. It converts NN-style feature intuition into
deterministic events that can be audited day by day:
- product x time bucket priors
- group-relative rank and residual regimes
- microprice, spread, depth, and book-imbalance regimes
- trailing extrema / turning-point detectors
- volatility and simple repeated path motifs

All edge summaries are executable:
long edge = future bid1 - current ask1
short edge = current bid1 - future ask1
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5" / "neural-signals"

HORIZONS = [10, 50, 100, 200, 500, 1000]
MIN_COUNT_PER_DAY = 20
GROUPS = {
    "GALAXY": ["GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_SOLAR_FLAMES"],
    "SLEEP": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UV": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    "TRANSLATOR": ["TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"],
    "SNACKPACK": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"],
}
PRODUCT_TO_GROUP = {p: g for g, ps in GROUPS.items() for p in ps}


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        frames.append(pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=";"))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    df["group"] = df["product"].map(PRODUCT_TO_GROUP)
    df["tick_index"] = df.groupby(["product", "day"]).cumcount()
    return df


def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["bid_price_2", "bid_price_3", "ask_price_2", "ask_price_3", "bid_volume_2", "bid_volume_3", "ask_volume_2", "ask_volume_3"]:
        out[c] = out[c].fillna(0)
    out["spread"] = out["ask_price_1"] - out["bid_price_1"]
    out["depth_bid3"] = out["bid_volume_1"] + out["bid_volume_2"] + out["bid_volume_3"]
    out["depth_ask3"] = out["ask_volume_1"] + out["ask_volume_2"] + out["ask_volume_3"]
    out["depth_total3"] = out["depth_bid3"] + out["depth_ask3"]
    out["imbalance1"] = (out["bid_volume_1"] - out["ask_volume_1"]) / (out["bid_volume_1"] + out["ask_volume_1"]).replace(0, np.nan)
    out["imbalance3"] = (out["depth_bid3"] - out["depth_ask3"]) / out["depth_total3"].replace(0, np.nan)
    out["microprice"] = (out["ask_price_1"] * out["bid_volume_1"] + out["bid_price_1"] * out["ask_volume_1"]) / (out["bid_volume_1"] + out["ask_volume_1"]).replace(0, np.nan)
    out["micro_minus_mid"] = out["microprice"] - out["mid_price"]
    g = out.groupby(["product", "day"], sort=False)
    out["ret1"] = g["mid_price"].diff()
    for w in [5, 10, 20, 50, 100, 200]:
        out[f"ret_{w}"] = g["mid_price"].diff(w)
    for w in [20, 50, 100, 200]:
        out[f"vol_{w}"] = g["ret1"].transform(lambda s, ww=w: s.rolling(ww, min_periods=max(5, ww // 4)).std())
        out[f"trail_min_{w}"] = g["mid_price"].transform(lambda s, ww=w: s.rolling(ww, min_periods=max(5, ww // 4)).min())
        out[f"trail_max_{w}"] = g["mid_price"].transform(lambda s, ww=w: s.rolling(ww, min_periods=max(5, ww // 4)).max())
        out[f"at_trail_min_{w}"] = (out["mid_price"] <= out[f"trail_min_{w}"]).astype(float)
        out[f"at_trail_max_{w}"] = (out["mid_price"] >= out[f"trail_max_{w}"]).astype(float)
    signs = np.sign(out["ret1"].fillna(0)).astype(int).astype(str)
    out["motif3"] = signs.groupby([out["product"], out["day"]]).transform(lambda s: s.shift(2).fillna("0") + s.shift(1).fillna("0") + s)
    out["motif5"] = signs.groupby([out["product"], out["day"]]).transform(lambda s: s.shift(4).fillna("0") + s.shift(3).fillna("0") + s.shift(2).fillna("0") + s.shift(1).fillna("0") + s)
    return out


def add_group_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    keys = ["day", "timestamp", "group"]
    grp = out.groupby(keys, sort=False)
    sum_mid = grp["mid_price"].transform("sum")
    count_mid = grp["mid_price"].transform("count").clip(lower=2)
    out["group_mid_mean"] = grp["mid_price"].transform("mean")
    out["group_mid_ex_self"] = (sum_mid - out["mid_price"]) / (count_mid - 1)
    out["group_residual"] = out["mid_price"] - out["group_mid_ex_self"]
    resid_mean = grp["group_residual"].transform("mean")
    resid_std = grp["group_residual"].transform("std").replace(0, np.nan)
    out["group_residual_z"] = ((out["group_residual"] - resid_mean) / resid_std).fillna(0.0)
    out["group_mid_rank"] = grp["mid_price"].rank(method="first") - 1
    out["group_micro_rank"] = grp["micro_minus_mid"].rank(method="first") - 1
    out["group_imbalance_rank"] = grp["imbalance3"].rank(method="first") - 1
    return out.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)


def add_forward_edges(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["product", "day"], sort=False)
    for h in HORIZONS:
        df[f"future_bid_{h}"] = g["bid_price_1"].shift(-h)
        df[f"future_ask_{h}"] = g["ask_price_1"].shift(-h)
        df[f"long_edge_{h}"] = df[f"future_bid_{h}"] - df["ask_price_1"]
        df[f"short_edge_{h}"] = df["bid_price_1"] - df[f"future_ask_{h}"]
    return df


def summarize_event(frame: pd.DataFrame, event: pd.Series | np.ndarray, label: dict) -> list[dict]:
    rows = []
    event_arr = np.asarray(event, dtype=bool)
    if int(event_arr.sum()) < MIN_COUNT_PER_DAY * 3:
        return rows
    day_arr = frame["day"].to_numpy(dtype=int)
    for h in HORIZONS:
        for side, col in [("long", f"long_edge_{h}"), ("short", f"short_edge_{h}")]:
            edge = frame[col].to_numpy(dtype=float)
            finite = event_arr & np.isfinite(edge)
            if int(finite.sum()) < MIN_COUNT_PER_DAY * 3:
                continue
            stats = []
            for day in [2, 3, 4]:
                vals = edge[finite & (day_arr == day)]
                if len(vals) < MIN_COUNT_PER_DAY:
                    stats.append((day, len(vals), np.nan, np.nan))
                else:
                    stats.append((day, len(vals), float(vals.mean()), float((vals > 0).mean())))
            if any(not np.isfinite(x[2]) for x in stats):
                continue
            means = [x[2] for x in stats]
            counts = [x[1] for x in stats]
            if not all(m > 0 for m in means):
                continue
            row = dict(label)
            all_vals = edge[finite]
            row.update({
                "side": side,
                "horizon": h,
                "count_total": int(sum(counts)),
                "count_min_day": int(min(counts)),
                "mean_all": float(all_vals.mean()),
                "median_all": float(np.median(all_vals)),
                "win_all": float(np.mean(all_vals > 0)),
                "mean_day2": means[0],
                "mean_day3": means[1],
                "mean_day4": means[2],
                "win_day2": stats[0][3],
                "win_day3": stats[1][3],
                "win_day4": stats[2][3],
                "worst_day_mean": float(min(means)),
                "rank_score": float(min(means) * math.log1p(sum(counts)) * max(0.01, np.mean(all_vals > 0))),
            })
            rows.append(row)
    return rows


def scan_numeric_regimes(df: pd.DataFrame) -> pd.DataFrame:
    features = [
        "spread", "depth_total3", "imbalance1", "imbalance3", "micro_minus_mid",
        "ret_5", "ret_10", "ret_20", "ret_50", "ret_100", "ret_200",
        "vol_20", "vol_50", "vol_100", "vol_200",
        "group_residual", "group_residual_z", "group_mid_rank", "group_micro_rank", "group_imbalance_rank",
    ]
    quantiles = [0.01, 0.05, 0.10, 0.20, 0.80, 0.90, 0.95, 0.99]
    rows = []
    for product, frame in df.groupby("product", sort=True):
        for feature in features:
            s = frame[feature].replace([np.inf, -np.inf], np.nan).dropna()
            if s.nunique() < 3:
                continue
            qs = s.quantile(quantiles).to_dict()
            for q, threshold in qs.items():
                if not np.isfinite(threshold):
                    continue
                if q < 0.5:
                    event = frame[feature] <= threshold
                    direction = "low"
                else:
                    event = frame[feature] >= threshold
                    direction = "high"
                rows.extend(summarize_event(frame, event, {
                    "event_type": "numeric_regime",
                    "product": product,
                    "group": PRODUCT_TO_GROUP[product],
                    "feature": feature,
                    "direction": direction,
                    "threshold": float(threshold),
                    "quantile": float(q),
                }))
    return pd.DataFrame(rows)


def scan_boolean_and_motifs(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    bool_features = [f"at_trail_min_{w}" for w in [20, 50, 100, 200]] + [f"at_trail_max_{w}" for w in [20, 50, 100, 200]]
    for product, frame in df.groupby("product", sort=True):
        for feature in bool_features:
            event = frame[feature] == 1.0
            rows.extend(summarize_event(frame, event, {
                "event_type": "trailing_extrema",
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "feature": feature,
                "direction": "true",
                "threshold": 1.0,
                "quantile": np.nan,
            }))
        for feature in ["motif3", "motif5"]:
            counts = frame[feature].value_counts()
            for motif, count in counts.items():
                if count < MIN_COUNT_PER_DAY * 3:
                    continue
                rows.extend(summarize_event(frame, frame[feature] == motif, {
                    "event_type": "path_motif",
                    "product": product,
                    "group": PRODUCT_TO_GROUP[product],
                    "feature": feature,
                    "direction": str(motif),
                    "threshold": np.nan,
                    "quantile": np.nan,
                }))
    return pd.DataFrame(rows)


def scan_time_product_priors(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, frame in df.groupby("product", sort=True):
        for width in [100, 200, 500, 1000, 2000]:
            bucket = (frame["tick_index"] // width).astype(int)
            for b, count in bucket.value_counts().items():
                if count < MIN_COUNT_PER_DAY * 3:
                    continue
                rows.extend(summarize_event(frame, bucket == b, {
                    "event_type": "product_time_bucket",
                    "product": product,
                    "group": PRODUCT_TO_GROUP[product],
                    "feature": "tick_index",
                    "direction": f"bucket_{int(b)}_width_{width}",
                    "threshold": int(b),
                    "quantile": np.nan,
                }))
    return pd.DataFrame(rows)


def rank_and_write(name: str, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df.to_csv(OUT_DIR / name, index=False)
        return df
    out = df.sort_values(["rank_score", "worst_day_mean", "count_total"], ascending=[False, False, False]).reset_index(drop=True)
    out.to_csv(OUT_DIR / name, index=False)
    out.head(500).to_csv(OUT_DIR / name.replace(".csv", "_top500.csv"), index=False)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_forward_edges(add_group_features(add_basic_features(load_prices())))
    numeric = rank_and_write("42_numeric_regime_events.csv", scan_numeric_regimes(df))
    motifs = rank_and_write("42_extrema_motif_events.csv", scan_boolean_and_motifs(df))
    priors = rank_and_write("42_product_time_bucket_events.csv", scan_time_product_priors(df))
    combined = pd.concat([numeric.head(500), motifs.head(500), priors.head(500)], ignore_index=True)
    combined = rank_and_write("42_combined_feature_events.csv", combined)
    print("numeric", len(numeric), "motifs/extrema", len(motifs), "priors", len(priors))
    print(combined.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
