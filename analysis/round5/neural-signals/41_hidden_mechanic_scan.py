#!/usr/bin/env python3
"""
Round 5 hidden-mechanic scanner inspired by NN reference notes.

This is research-only. It searches deterministic event families that a neural
network/tree model would find but that are easier to validate directly:
- visible bid/ask price suffix events across all displayed levels
- timestamp and tick-index modulo priors

Outputs are execution-aware. Long edge enters at current ask1 and exits at
future bid1; short edge enters at current bid1 and exits at future ask1.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5" / "neural-signals"

PRICE_COLS = [
    "bid_price_1",
    "bid_price_2",
    "bid_price_3",
    "ask_price_1",
    "ask_price_2",
    "ask_price_3",
]

HORIZONS = [10, 50, 100, 200, 500, 1000]
SUFFIX_BASES = [10, 50, 100, 500, 1000]
TIME_PERIODS = [5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]
MIN_COUNT_PER_DAY = 20


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = DATA_DIR / f"prices_round_5_day_{day}.csv"
        df = pd.read_csv(path, sep=";")
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    data = data.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    data["tick_index"] = data.groupby(["product", "day"]).cumcount()
    return data


def add_forward_edges(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["product", "day"], sort=False)
    for h in HORIZONS:
        df[f"future_bid_{h}"] = g["bid_price_1"].shift(-h)
        df[f"future_ask_{h}"] = g["ask_price_1"].shift(-h)
        df[f"future_mid_{h}"] = g["mid_price"].shift(-h)
        df[f"long_edge_{h}"] = df[f"future_bid_{h}"] - df["ask_price_1"]
        df[f"short_edge_{h}"] = df["bid_price_1"] - df[f"future_ask_{h}"]
        df[f"mid_delta_{h}"] = df[f"future_mid_{h}"] - df["mid_price"]
    return df


def has_enough_each_day(frame: pd.DataFrame, event_mask: np.ndarray) -> bool:
    days = frame["day"].to_numpy()
    return all(int(np.sum(event_mask & (days == day))) >= MIN_COUNT_PER_DAY for day in [2, 3, 4])


def summarize_keyed(frame: pd.DataFrame, keys: np.ndarray, label_base: dict) -> list[dict]:
    rows = []
    base = int(label_base["base"])
    valid_key = np.isfinite(keys)
    if not np.any(valid_key):
        return rows
    key_values = keys.astype(float)
    key_values = np.where(valid_key, key_values, -1).astype(int)
    day_idx = frame["day"].to_numpy(dtype=int) - 2
    for h in HORIZONS:
        for side in ["long", "short"]:
            col = f"{side}_edge_{h}"
            edge = frame[col].to_numpy(dtype=float)
            finite = valid_key & np.isfinite(edge)
            if not np.any(finite):
                continue
            counts = []
            sums = []
            wins = []
            for d in [0, 1, 2]:
                m = finite & (day_idx == d)
                k = key_values[m]
                e = edge[m]
                counts.append(np.bincount(k, minlength=base))
                sums.append(np.bincount(k, weights=e, minlength=base))
                wins.append(np.bincount(k, weights=(e > 0).astype(float), minlength=base))
            counts_arr = np.vstack(counts)
            sums_arr = np.vstack(sums)
            wins_arr = np.vstack(wins)
            good_count = np.min(counts_arr, axis=0) >= MIN_COUNT_PER_DAY
            with np.errstate(divide="ignore", invalid="ignore"):
                means_arr = sums_arr / counts_arr
                win_arr = wins_arr / counts_arr
            good_mean = np.all(means_arr > 0, axis=0)
            for key in np.flatnonzero(good_count & good_mean):
                day_counts = counts_arr[:, key].astype(int)
                day_means = means_arr[:, key]
                day_wins = win_arr[:, key]
                total_count = int(day_counts.sum())
                total_sum = float(sums_arr[:, key].sum())
                total_wins = float(wins_arr[:, key].sum())
                row = dict(label_base)
                row.update({
                    "residue": int(key),
                    "side": side,
                    "horizon": h,
                    "count_total": total_count,
                    "count_min_day": int(day_counts.min()),
                    "mean_all": total_sum / total_count,
                    "median_all": np.nan,
                    "win_all": total_wins / total_count,
                    "mean_day2": float(day_means[0]),
                    "mean_day3": float(day_means[1]),
                    "mean_day4": float(day_means[2]),
                    "win_day2": float(day_wins[0]),
                    "win_day3": float(day_wins[1]),
                    "win_day4": float(day_wins[2]),
                    "stable_positive": True,
                    "stable_negative": False,
                    "same_sign": True,
                    "worst_day_mean": float(np.min(day_means)),
                    "score": float(np.min(day_means) * math.log1p(total_count)),
                })
                rows.append(row)
    return rows


def summarize_event(frame: pd.DataFrame, event_mask: np.ndarray, label: dict) -> list[dict]:
    rows = []
    event = frame[event_mask].copy()
    if event.empty:
        return rows
    for h in HORIZONS:
        for side, edge_col in [("long", f"long_edge_{h}"), ("short", f"short_edge_{h}")]:
            day_rows = []
            ok = True
            for day in [2, 3, 4]:
                d = event[event["day"] == day]
                vals = d[edge_col].dropna().values
                if len(vals) == 0:
                    ok = False
                    day_rows.append((day, 0, np.nan, np.nan, np.nan))
                    continue
                day_rows.append((day, len(vals), float(np.mean(vals)), float(np.median(vals)), float(np.mean(vals > 0))))
            if not ok:
                continue
            means = [x[2] for x in day_rows]
            counts = [x[1] for x in day_rows]
            if min(counts) < MIN_COUNT_PER_DAY:
                continue
            signs = [1 if x > 0 else -1 if x < 0 else 0 for x in means]
            stable_positive = all(x > 0 for x in means)
            stable_negative = all(x < 0 for x in means)
            row = dict(label)
            row.update({
                "side": side,
                "horizon": h,
                "count_total": int(sum(counts)),
                "count_min_day": int(min(counts)),
                "mean_all": float(np.nanmean(event[edge_col])),
                "median_all": float(np.nanmedian(event[edge_col])),
                "win_all": float(np.nanmean(event[edge_col] > 0)),
                "mean_day2": means[0],
                "mean_day3": means[1],
                "mean_day4": means[2],
                "win_day2": day_rows[0][4],
                "win_day3": day_rows[1][4],
                "win_day4": day_rows[2][4],
                "stable_positive": stable_positive,
                "stable_negative": stable_negative,
                "same_sign": len(set(signs)) == 1 and signs[0] != 0,
                "worst_day_mean": float(min(means)),
                "score": float(np.sign(np.nanmean(means)) * min(abs(x) for x in means) * math.log1p(sum(counts))),
            })
            rows.append(row)
    return rows


def scan_suffix_events(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    products = sorted(df["product"].unique())
    for product in products:
        frame = df[df["product"] == product].copy()
        for base in SUFFIX_BASES:
            for field in PRICE_COLS:
                keys = np.mod(frame[field].to_numpy(dtype=float), base)
                rows.extend(summarize_keyed(frame, keys, {
                    "event_type": "visible_price_suffix",
                    "product": product,
                    "base": base,
                    "field": field,
                }))
    return pd.DataFrame(rows)


def scan_time_buckets(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    products = sorted(df["product"].unique())
    for product in products:
        frame = df[df["product"] == product].copy()
        for source in ["timestamp", "tick_index"]:
            values = frame[source].to_numpy(dtype=int)
            for period in TIME_PERIODS:
                buckets = values % period
                rows.extend(summarize_keyed(frame, buckets.astype(float), {
                    "event_type": f"{source}_bucket",
                    "product": product,
                    "base": period,
                    "field": source,
                }))
    return pd.DataFrame(rows)


def rank_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events
    e = events.copy()
    e["robust"] = e["same_sign"] & (e["count_min_day"] >= 3)
    e["positive_edge"] = e["mean_all"] > 0
    e["abs_worst"] = e[["mean_day2", "mean_day3", "mean_day4"]].abs().min(axis=1)
    e["rank_score"] = np.where(
        e["robust"] & e["positive_edge"],
        e["abs_worst"] * np.log1p(e["count_total"]) * e["win_all"].clip(lower=0.01),
        -1e9,
    )
    return e.sort_values(["rank_score", "count_total"], ascending=[False, False]).reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_forward_edges(load_prices())

    suffix = rank_events(scan_suffix_events(df))
    suffix.to_csv(OUT_DIR / "41_suffix_event_summary.csv", index=False)
    suffix.head(500).to_csv(OUT_DIR / "41_suffix_event_top500.csv", index=False)

    uv420 = suffix[(suffix["product"] == "UV_VISOR_RED") & (suffix["base"] == 1000) & (suffix["residue"] == 420)]
    uv420.to_csv(OUT_DIR / "41_uv_red_420_detail.csv", index=False)

    buckets = rank_events(scan_time_buckets(df))
    buckets.to_csv(OUT_DIR / "41_time_bucket_summary.csv", index=False)
    buckets.head(500).to_csv(OUT_DIR / "41_time_bucket_top500.csv", index=False)

    combined = pd.concat([suffix.head(500), buckets.head(500)], ignore_index=True)
    combined = rank_events(combined)
    combined.to_csv(OUT_DIR / "41_combined_top1000_ranked.csv", index=False)

    print("suffix rows", len(suffix), "time bucket rows", len(buckets))
    print("top suffix")
    print(suffix.head(20).to_string(index=False))
    print("UV_VISOR_RED 420")
    print(uv420.head(30).to_string(index=False))
    print("top time buckets")
    print(buckets.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
