#!/usr/bin/env python3
"""
Round 5 cross-product pressure and event-conditioned lead/lag scan.

This tests whether an event on one product's book or recent path predicts an
execution-aware edge on another product. It is intentionally broad across all
50x49 pairs, then ranked by day-stable executable edge.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5-nn-research"
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


def load_feature_frames() -> dict[str, pd.DataFrame]:
    frames = []
    for day in [2, 3, 4]:
        frames.append(pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=";"))
    df = pd.concat(frames, ignore_index=True)
    for c in ["bid_volume_2", "bid_volume_3", "ask_volume_2", "ask_volume_3"]:
        df[c] = df[c].fillna(0)
    df["depth_bid3"] = df["bid_volume_1"] + df["bid_volume_2"] + df["bid_volume_3"]
    df["depth_ask3"] = df["ask_volume_1"] + df["ask_volume_2"] + df["ask_volume_3"]
    df["imbalance1"] = (df["bid_volume_1"] - df["ask_volume_1"]) / (df["bid_volume_1"] + df["ask_volume_1"]).replace(0, np.nan)
    df["imbalance3"] = (df["depth_bid3"] - df["depth_ask3"]) / (df["depth_bid3"] + df["depth_ask3"]).replace(0, np.nan)
    df["microprice"] = (df["ask_price_1"] * df["bid_volume_1"] + df["bid_price_1"] * df["ask_volume_1"]) / (df["bid_volume_1"] + df["ask_volume_1"]).replace(0, np.nan)
    df["micro_minus_mid"] = df["microprice"] - df["mid_price"]
    df = df.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    out = {}
    for product, p in df.groupby("product", sort=True):
        p = p.copy().reset_index(drop=True)
        p["tick_index"] = p.groupby("day").cumcount()
        gp = p.groupby("day", sort=False)
        p["ret10"] = gp["mid_price"].diff(10)
        p["ret50"] = gp["mid_price"].diff(50)
        p["ret100"] = gp["mid_price"].diff(100)
        for h in HORIZONS:
            p[f"long_edge_{h}"] = gp["bid_price_1"].shift(-h) - p["ask_price_1"]
            p[f"short_edge_{h}"] = p["bid_price_1"] - gp["ask_price_1"].shift(-h)
        out[product] = p
    return out


def summarize_pair_event(target: pd.DataFrame, event: np.ndarray, label: dict) -> list[dict]:
    rows = []
    if int(np.nansum(event)) < MIN_COUNT_PER_DAY * 3:
        return rows
    ev = target.loc[event]
    for h in HORIZONS:
        for side, col in [("long", f"long_edge_{h}"), ("short", f"short_edge_{h}")]:
            stats = []
            for day in [2, 3, 4]:
                vals = ev.loc[ev["day"] == day, col].dropna().to_numpy()
                if len(vals) < MIN_COUNT_PER_DAY:
                    stats.append((day, len(vals), np.nan, np.nan))
                else:
                    stats.append((day, len(vals), float(vals.mean()), float((vals > 0).mean())))
            if any(not np.isfinite(x[2]) for x in stats):
                continue
            means = [x[2] for x in stats]
            if not all(m > 0 for m in means):
                continue
            vals = ev[col].dropna()
            row = dict(label)
            row.update({
                "side": side,
                "horizon": h,
                "count_total": int(sum(x[1] for x in stats)),
                "count_min_day": int(min(x[1] for x in stats)),
                "mean_all": float(vals.mean()),
                "median_all": float(vals.median()),
                "win_all": float((vals > 0).mean()),
                "mean_day2": means[0],
                "mean_day3": means[1],
                "mean_day4": means[2],
                "win_day2": stats[0][3],
                "win_day3": stats[1][3],
                "win_day4": stats[2][3],
                "worst_day_mean": float(min(means)),
                "rank_score": float(min(means) * math.log1p(len(vals)) * max(0.01, (vals > 0).mean())),
            })
            rows.append(row)
    return rows


def scan(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    signal_features = ["imbalance1", "imbalance3", "micro_minus_mid", "ret10", "ret50", "ret100"]
    products = sorted(frames)
    for source in products:
        src = frames[source]
        for feature in signal_features:
            s = src[feature].replace([np.inf, -np.inf], np.nan).dropna()
            if s.nunique() < 5:
                continue
            thresholds = [
                ("low_05", float(s.quantile(0.05)), "low"),
                ("low_10", float(s.quantile(0.10)), "low"),
                ("high_90", float(s.quantile(0.90)), "high"),
                ("high_95", float(s.quantile(0.95)), "high"),
            ]
            for name, threshold, direction in thresholds:
                if direction == "low":
                    event = (src[feature] <= threshold).to_numpy()
                else:
                    event = (src[feature] >= threshold).to_numpy()
                if int(event.sum()) < MIN_COUNT_PER_DAY * 3:
                    continue
                for target in products:
                    if target == source:
                        continue
                    if PRODUCT_TO_GROUP[target] != PRODUCT_TO_GROUP[source]:
                        continue
                    rows.extend(summarize_pair_event(frames[target], event, {
                        "event_type": "cross_product_pressure",
                        "source": source,
                        "source_group": PRODUCT_TO_GROUP[source],
                        "target": target,
                        "target_group": PRODUCT_TO_GROUP[target],
                        "same_group": PRODUCT_TO_GROUP[source] == PRODUCT_TO_GROUP[target],
                        "feature": feature,
                        "direction": direction,
                        "threshold_name": name,
                        "threshold": threshold,
                    }))
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = load_feature_frames()
    results = scan(frames)
    if results.empty:
        results.to_csv(OUT_DIR / "43_cross_pressure_leadlag_events.csv", index=False)
        print("no results")
        return
    results = results.sort_values(["rank_score", "worst_day_mean", "count_total"], ascending=[False, False, False]).reset_index(drop=True)
    results.head(500).to_csv(OUT_DIR / "43_cross_pressure_leadlag_top500.csv", index=False)
    results[results["same_group"]].head(500).to_csv(OUT_DIR / "43_cross_pressure_same_group_top500.csv", index=False)
    summary = results.groupby(["source", "target", "feature", "direction"], as_index=False).head(1)
    summary.head(1000).to_csv(OUT_DIR / "43_cross_pressure_leadlag_summary_top1000.csv", index=False)
    print("rows", len(results))
    print(results.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
