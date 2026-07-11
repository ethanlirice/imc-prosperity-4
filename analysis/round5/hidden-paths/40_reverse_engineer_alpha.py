"""Reverse-engineer how the FREE_ALPHA table was constructed.

The published table has shape (base, d1, d2, d3, d4) per product. The current
trader treats `path[k] = base + d_k` and then evaluates on bucket k =
int(t * 5 // 1_000_000).

We test many hypotheses for what `base` and `d_k` actually were computed from:

Hypotheses for `base`:
    H_b1: base = bucket0 mean on a specific day (d2/d3/d4) or pooled
    H_b2: base = day mean on a specific day or pooled
    H_b3: base = global mean across all 3 days
    H_b4: base = mean over a leading window [0, W] for W in
          {100, 1000, 5000, 10000, 100000, 200000}

Hypotheses for `d_k` (for k=1..4):
    H_d1: d_k = bucket_k_mean - bucket_0_mean on day X
    H_d2: d_k = bucket_k_mean - bucket_0_mean pooled across days
    H_d3: d_k = bucket_k_mean - base for the chosen base
    H_d4: d_k = mean over [200k*k, 200k*(k+1)] minus base

For the entire table we score each hypothesis by mean-absolute-error (MAE) and
median-absolute-error across all 50 products. The lowest-MAE hypothesis tells
us how the table was built.

If a single hypothesis fits all 50 products to within (say) 1 tick, the
construction is recovered and we can extrapolate paths for any product without
walk-forward simulation.

Output:
    analysis/round5/hidden-paths/reverse_engineer_alpha_summary.csv
    analysis/round5/hidden-paths/reverse_engineer_alpha_per_product.csv
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import (  # noqa: E402
    OUT_DIR,
    DATA_DIR,
    DAYS,
    ALL_PRODUCTS,
    FREE_ALPHA_TABLE,
    N_BUCKETS,
)


def load_long_prices():
    frames = []
    for d in DAYS:
        df = pd.read_csv(os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % d), sep=";")
        df["mid"] = df["mid_price"].astype(float)
        df["bucket"] = np.minimum(N_BUCKETS - 1, df["timestamp"] * N_BUCKETS // 1_000_000).astype(int)
        frames.append(df[["day", "timestamp", "product", "bucket", "mid"]])
    return pd.concat(frames, ignore_index=True)


def main():
    long_df = load_long_prices()

    # ----------------- Build candidate base estimates per product -----------------
    # 1. bucket0 mean on specific days and pooled.
    # 2. day mean on specific days and pooled.
    # 3. leading window means for various widths.
    # 4. specific timestamps (first tick, t=0 mid).

    base_estimates = {}  # name -> {product: value}

    for d in DAYS:
        b0 = long_df[(long_df["day"] == d) & (long_df["bucket"] == 0)].groupby("product")["mid"].mean()
        base_estimates["bucket0_mean_d%d" % d] = b0.to_dict()
        dm = long_df[long_df["day"] == d].groupby("product")["mid"].mean()
        base_estimates["day_mean_d%d" % d] = dm.to_dict()

    pooled_b0 = long_df[long_df["bucket"] == 0].groupby("product")["mid"].mean().to_dict()
    base_estimates["bucket0_mean_pooled"] = pooled_b0
    pooled_day_mean = long_df.groupby("product")["mid"].mean().to_dict()
    base_estimates["day_mean_pooled"] = pooled_day_mean

    for w in (100, 1000, 5000, 10000, 100000, 200000):
        for d in DAYS:
            sub = long_df[(long_df["day"] == d) & (long_df["timestamp"] < w)]
            if sub.empty:
                continue
            base_estimates["leading_w%d_d%d" % (w, d)] = sub.groupby("product")["mid"].mean().to_dict()
        sub = long_df[long_df["timestamp"] < w]
        base_estimates["leading_w%d_pooled" % w] = sub.groupby("product")["mid"].mean().to_dict()

    # First-tick mid per day (timestamp 0).
    for d in DAYS:
        sub = long_df[(long_df["day"] == d) & (long_df["timestamp"] == 0)]
        base_estimates["first_tick_d%d" % d] = sub.set_index("product")["mid"].to_dict()
    first_tick_pooled = long_df[long_df["timestamp"] == 0].groupby("product")["mid"].mean().to_dict()
    base_estimates["first_tick_pooled"] = first_tick_pooled

    # Score each base hypothesis by MAE vs published anchor.
    base_rows = []
    pub_base = {p: float(v[0]) for p, v in FREE_ALPHA_TABLE.items()}
    products = sorted(pub_base.keys())
    for name, est in base_estimates.items():
        diffs = []
        for p in products:
            if p in est:
                diffs.append(est[p] - pub_base[p])
        if not diffs:
            continue
        diffs = np.array(diffs)
        base_rows.append({
            "estimator": name,
            "n": len(diffs),
            "mae": float(np.mean(np.abs(diffs))),
            "median_abs": float(np.median(np.abs(diffs))),
            "rmse": float(np.sqrt(np.mean(diffs ** 2))),
            "max_abs": float(np.max(np.abs(diffs))),
            "bias": float(np.mean(diffs)),
        })
    base_score = pd.DataFrame(base_rows).sort_values("mae")

    # ----------------- Build candidate delta estimators per product -----------------
    # For each base estimator, a paired delta estimator:
    #   delta_k(prod) = bucket_k_mean_estimator - base_estimator
    # We test:
    #   per-day bucket means d2/d3/d4
    #   pooled bucket means
    #   median pooling
    delta_estimators = {}

    for d in DAYS:
        bm = long_df[long_df["day"] == d].groupby(["product", "bucket"])["mid"].mean().unstack()
        bmm = long_df[long_df["day"] == d].groupby(["product", "bucket"])["mid"].median().unstack()
        delta_estimators["bucket_mean_d%d" % d] = bm
        delta_estimators["bucket_median_d%d" % d] = bmm

    bm_pooled = long_df.groupby(["product", "bucket"])["mid"].mean().unstack()
    delta_estimators["bucket_mean_pooled"] = bm_pooled
    bmm_pooled = long_df.groupby(["product", "bucket"])["mid"].median().unstack()
    delta_estimators["bucket_median_pooled"] = bmm_pooled
    # Mean across-day-means (each day equal weight).
    by_day_mean = (
        long_df.groupby(["day", "product", "bucket"])["mid"].mean()
        .unstack()
        .groupby("product")
        .mean()
    )
    delta_estimators["bucket_mean_avg_across_days"] = by_day_mean

    # For the published delta to recover from delta_k = bucket_k_estimator - base,
    # we test EVERY (base_estimator, bucket_estimator) pair.
    pair_rows = []
    pub_d = {p: np.array(FREE_ALPHA_TABLE[p][1:], dtype=float) for p in products}

    for base_name, base_est in base_estimates.items():
        for delta_name, delta_df in delta_estimators.items():
            mae_per_prod = []
            for p in products:
                if p not in base_est or p not in delta_df.index:
                    continue
                row = delta_df.loc[p]
                if not isinstance(row, pd.Series):
                    continue
                if row.size != 5:
                    continue
                bucket_means = row.values
                est_d = bucket_means[1:] - base_est[p]
                err = est_d - pub_d[p]
                mae_per_prod.append(np.mean(np.abs(err)))
            if not mae_per_prod:
                continue
            arr = np.array(mae_per_prod)
            pair_rows.append({
                "base": base_name,
                "delta": delta_name,
                "n": len(arr),
                "mean_mae": float(np.mean(arr)),
                "median_mae": float(np.median(arr)),
                "max_mae": float(np.max(arr)),
                "p95_mae": float(np.quantile(arr, 0.95)),
            })
    pair_score = pd.DataFrame(pair_rows).sort_values("mean_mae")

    out_summary = os.path.join(OUT_DIR, "reverse_engineer_alpha_summary.csv")
    out_pair = os.path.join(OUT_DIR, "reverse_engineer_alpha_pairs.csv")
    base_score.to_csv(out_summary, index=False)
    pair_score.to_csv(out_pair, index=False)

    print("--- top base estimators (vs published base) ---")
    print(base_score.head(15).to_string(index=False))
    print()
    print("--- top base+delta estimator pairs (vs published d1..d4) ---")
    print(pair_score.head(20).to_string(index=False))

    # ----------------- Per-product break-down for the best pair -----------------
    if not pair_score.empty:
        best = pair_score.iloc[0]
        base_name = best["base"]
        delta_name = best["delta"]
        base_est = base_estimates[base_name]
        delta_df = delta_estimators[delta_name]
        rows = []
        for p in products:
            if p not in base_est or p not in delta_df.index:
                continue
            row = delta_df.loc[p]
            est_b = float(base_est[p])
            est_bk = row.values
            est_d = est_bk[1:] - est_b
            pub = FREE_ALPHA_TABLE[p]
            rows.append({
                "product": p,
                "pub_base": pub[0],
                "est_base": round(est_b, 4),
                "base_err": round(est_b - pub[0], 4),
                "pub_d1": pub[1],
                "est_d1": round(float(est_d[0]), 4),
                "d1_err": round(float(est_d[0] - pub[1]), 4),
                "pub_d2": pub[2],
                "est_d2": round(float(est_d[1]), 4),
                "d2_err": round(float(est_d[1] - pub[2]), 4),
                "pub_d3": pub[3],
                "est_d3": round(float(est_d[2]), 4),
                "d3_err": round(float(est_d[2] - pub[3]), 4),
                "pub_d4": pub[4],
                "est_d4": round(float(est_d[3]), 4),
                "d4_err": round(float(est_d[3] - pub[4]), 4),
                "max_abs_err": round(float(max(abs(est_b - pub[0]), max(abs(est_d - np.array(pub[1:]))))), 4),
            })
        per_prod = pd.DataFrame(rows).sort_values("max_abs_err")
        out_per = os.path.join(OUT_DIR, "reverse_engineer_alpha_per_product.csv")
        per_prod.to_csv(out_per, index=False)
        print()
        print("best pair: base=%s delta=%s -> mean MAE=%.4f median=%.4f max=%.4f" % (
            base_name, delta_name, best["mean_mae"], best["median_mae"], best["max_mae"]))
        print()
        print("--- per-product residual on best pair (sample 10 best fits) ---")
        print(per_prod.head(10).to_string(index=False))
        print()
        print("--- per-product residual on best pair (worst 10 fits) ---")
        print(per_prod.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
