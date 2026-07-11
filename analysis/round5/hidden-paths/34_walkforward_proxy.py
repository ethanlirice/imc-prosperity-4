"""Walk-forward path proxy backtest (vectorised).

For each (product, candidate path type, threshold), train a 5-bucket fair-value
path on two of the three days and run a simple offline crossing rule on the
held-out day:

  - if best_ask < path_fair - threshold and pos < +10  -> buy 1
  - if best_bid > path_fair + threshold and pos > -10  -> sell 1
  - if |mid - path_fair| <= exit_band                  -> close toward 0

Position cap = 10. exit_band = max(20.0, threshold/4) (small).

Candidate path types:
  bucket_mean       : average bucket mean across train days.
  bucket_delta_b0   : test day's own bucket0 + average delta_from_bucket0
                      across train days. SHAPE only, anchored to test-day
                      bucket0 to avoid level leakage.
  group_offset      : group_path[k] (test-day) + average per-product offset
                      across train days.
  group_scaled      : alpha * group_path[k] + beta where (alpha, beta) is
                      averaged across train days.

Thresholds: 20, 40, 80, 120, 160, 200, 300.

Speedup: pre-mask the (rare) signal ticks per (product, day, fair-vector,
threshold) and only loop over those for the position dynamics.

Outputs:
  path_proxy_backtest_summary.csv  — one row per (product, path_type, threshold).
  path_proxy_backtest_day.csv      — per-day breakdown.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import (  # noqa: E402
    OUT_DIR,
    ALL_PRODUCTS,
    PRODUCT_TO_GROUP,
    DAYS,
    N_BUCKETS,
    DATA_DIR,
)

THRESHOLDS = [20, 40, 80, 120, 160, 200, 300]
PATH_TYPES = ["bucket_mean", "bucket_delta_b0", "group_offset", "group_scaled"]
POS_LIMIT = 10


def fit_scale_offset(group_path, product_path):
    g = np.asarray(group_path, dtype=float)
    p = np.asarray(product_path, dtype=float)
    G = np.vstack([g, np.ones_like(g)]).T
    coef, *_ = np.linalg.lstsq(G, p, rcond=None)
    return float(coef[0]), float(coef[1])


def build_paths(bucket_df, group_path_df, product, train_days, test_day):
    """Return dict path_type -> 5-vector of fair values to use on the test day."""
    sub = bucket_df[bucket_df["product"] == product]
    train = sub[sub["day"].isin(train_days)]
    test = sub[sub["day"] == test_day]
    if len(test) != 5:
        return None
    train_buckets = train.groupby("bucket")["mean_mid"].mean().sort_index().values
    if train_buckets.size != 5:
        return None
    test_buckets = test.sort_values("bucket")["mean_mid"].values
    test_b0 = float(test_buckets[0])

    paths = {}
    paths["bucket_mean"] = train_buckets.copy()

    train_d = train.groupby(["day", "bucket"])["mean_mid"].mean().unstack()
    if train_d.shape[1] != 5:
        paths["bucket_delta_b0"] = train_buckets.copy()
    else:
        per_day_d = train_d.values - train_d.values[:, 0:1]
        avg_d = per_day_d.mean(axis=0)
        paths["bucket_delta_b0"] = test_b0 + avg_d

    group_name = PRODUCT_TO_GROUP[product]
    test_group = group_path_df[
        (group_path_df["group"] == group_name) & (group_path_df["day"] == test_day)
    ]
    if len(test_group) != 5:
        return None
    test_group_path = test_group.sort_values("bucket")["group_path_mean"].values
    train_offsets = []
    for d in train_days:
        gp = group_path_df[
            (group_path_df["group"] == group_name) & (group_path_df["day"] == d)
        ].sort_values("bucket")["group_path_mean"].values
        pp = train[train["day"] == d].sort_values("bucket")["mean_mid"].values
        if gp.size == 5 and pp.size == 5:
            train_offsets.append(pp - gp)
    if train_offsets:
        avg_offset = np.mean(train_offsets, axis=0)
        paths["group_offset"] = test_group_path + avg_offset
    else:
        paths["group_offset"] = train_buckets.copy()

    alphas, betas = [], []
    for d in train_days:
        gp = group_path_df[
            (group_path_df["group"] == group_name) & (group_path_df["day"] == d)
        ].sort_values("bucket")["group_path_mean"].values
        pp = train[train["day"] == d].sort_values("bucket")["mean_mid"].values
        if gp.size == 5 and pp.size == 5:
            a, b = fit_scale_offset(gp, pp)
            alphas.append(a)
            betas.append(b)
    if alphas:
        a_mean = float(np.mean(alphas))
        b_mean = float(np.mean(betas))
        paths["group_scaled"] = a_mean * test_group_path + b_mean
    else:
        paths["group_scaled"] = train_buckets.copy()

    return paths


def simulate_vec(bucket_arr, mid_arr, bid_arr, ask_arr, fair_per_bucket, threshold, exit_band):
    """Vectorised pre-mask + tight loop over signal ticks only."""
    fair_arr = fair_per_bucket[bucket_arr]
    valid = np.isfinite(fair_arr) & np.isfinite(bid_arr) & np.isfinite(ask_arr) & np.isfinite(mid_arr)

    is_buy = valid & (ask_arr < fair_arr - threshold)
    is_sell = valid & (bid_arr > fair_arr + threshold)
    is_exit = valid & (np.abs(mid_arr - fair_arr) <= exit_band)
    sig_mask = is_buy | is_sell | is_exit
    sig_idx = np.where(sig_mask)[0]

    pos = 0
    realized = 0.0
    avg_cost = 0.0
    trades = 0

    for i in sig_idx:
        a = ask_arr[i]
        bb = bid_arr[i]
        m = mid_arr[i]
        fair = fair_arr[i]

        if abs(m - fair) <= exit_band:
            if pos > 0:
                qty = pos
                realized += qty * bb
                pos = 0
                avg_cost = 0.0
                trades += qty
                continue
            if pos < 0:
                qty = -pos
                realized -= qty * a
                pos = 0
                avg_cost = 0.0
                trades += qty
                continue

        if a < fair - threshold and pos < POS_LIMIT:
            new_pos = pos + 1
            if pos >= 0:
                avg_cost = (avg_cost * pos + a) / new_pos if new_pos != 0 else 0.0
            else:
                realized += avg_cost - a
                if new_pos == 0:
                    avg_cost = 0.0
            pos = new_pos
            realized -= a
            trades += 1
        elif bb > fair + threshold and pos > -POS_LIMIT:
            new_pos = pos - 1
            if pos <= 0:
                denom = -new_pos if new_pos != 0 else 1
                avg_cost = (avg_cost * (-pos) + bb) / denom
            else:
                realized += bb - avg_cost
                if new_pos == 0:
                    avg_cost = 0.0
            pos = new_pos
            realized += bb
            trades += 1

    final_mid = float(mid_arr[-1])
    pnl = realized + pos * final_mid
    return pnl, trades, pos


def main():
    bucket_df = pd.read_csv(os.path.join(OUT_DIR, "product_bucket_paths.csv"))
    group_path_df = pd.read_csv(os.path.join(OUT_DIR, "group_path_summary.csv"))

    print("loading raw prices for tick-level simulation...", flush=True)
    frames = []
    for d in DAYS:
        path = os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % d)
        df = pd.read_csv(path, sep=";")
        df["mid"] = df["mid_price"].astype(float)
        df["best_bid"] = df["bid_price_1"].astype(float)
        df["best_ask"] = df["ask_price_1"].astype(float)
        df["bucket"] = np.minimum(N_BUCKETS - 1, df["timestamp"] * N_BUCKETS // 1_000_000).astype(int)
        df = df[["day", "timestamp", "product", "bucket", "mid", "best_bid", "best_ask"]]
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True).sort_values(["product", "day", "timestamp"]).reset_index(drop=True)

    # Pre-extract per (product, day) numpy arrays once.
    cache = {}
    for (prod, day), group in raw.groupby(["product", "day"], sort=False):
        cache[(prod, day)] = (
            group["bucket"].to_numpy(),
            group["mid"].to_numpy(dtype=float),
            group["best_bid"].to_numpy(dtype=float),
            group["best_ask"].to_numpy(dtype=float),
        )
    print("cached %d (product, day) arrays" % len(cache), flush=True)

    folds = [
        ((3, 4), 2),
        ((2, 4), 3),
        ((2, 3), 4),
    ]

    summary_rows = []
    day_rows = []

    for pi, product in enumerate(ALL_PRODUCTS):
        # Pre-build path vectors per fold once per product.
        per_fold_paths = {}
        for train_days, test_day in folds:
            per_fold_paths[(train_days, test_day)] = build_paths(
                bucket_df, group_path_df, product, train_days, test_day
            )

        for path_type in PATH_TYPES:
            for thr in THRESHOLDS:
                exit_band = max(20.0, thr / 4.0)
                fold_pnls = []
                fold_trades = []
                fold_positive = 0
                for (train_days, test_day) in folds:
                    paths = per_fold_paths[(train_days, test_day)]
                    if paths is None:
                        continue
                    fair = paths.get(path_type)
                    if fair is None or not np.all(np.isfinite(fair)):
                        continue
                    arrs = cache.get((product, test_day))
                    if arrs is None:
                        continue
                    bucket_arr, mid_arr, bid_arr, ask_arr = arrs
                    pnl, trades, end_pos = simulate_vec(
                        bucket_arr, mid_arr, bid_arr, ask_arr, fair, thr, exit_band
                    )
                    fold_pnls.append(pnl)
                    fold_trades.append(trades)
                    if pnl > 0:
                        fold_positive += 1
                    day_rows.append(
                        {
                            "product": product,
                            "group": PRODUCT_TO_GROUP[product],
                            "path_type": path_type,
                            "threshold": thr,
                            "exit_band": exit_band,
                            "train_days": "+".join(str(d) for d in train_days),
                            "test_day": test_day,
                            "pnl": round(float(pnl), 2),
                            "trades": int(trades),
                            "end_pos": int(end_pos),
                        }
                    )
                if not fold_pnls:
                    continue
                worst = float(min(fold_pnls))
                total = float(sum(fold_pnls))
                summary_rows.append(
                    {
                        "product": product,
                        "group": PRODUCT_TO_GROUP[product],
                        "path_type": path_type,
                        "threshold": thr,
                        "folds_run": len(fold_pnls),
                        "folds_positive": fold_positive,
                        "total_pnl": round(total, 2),
                        "worst_day_pnl": round(worst, 2),
                        "best_day_pnl": round(float(max(fold_pnls)), 2),
                        "mean_day_pnl": round(total / len(fold_pnls), 2),
                        "total_trades": int(sum(fold_trades)),
                    }
                )
        if (pi + 1) % 10 == 0:
            print("processed %d / %d products" % (pi + 1, len(ALL_PRODUCTS)), flush=True)

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["folds_positive", "worst_day_pnl", "total_pnl"], ascending=[False, False, False]
    )
    day_df = pd.DataFrame(day_rows)
    summary_df.to_csv(os.path.join(OUT_DIR, "path_proxy_backtest_summary.csv"), index=False)
    day_df.to_csv(os.path.join(OUT_DIR, "path_proxy_backtest_day.csv"), index=False)
    print("wrote summary rows=%d day rows=%d" % (len(summary_df), len(day_df)), flush=True)


if __name__ == "__main__":
    main()
