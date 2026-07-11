"""Score how stable the 5-bucket path is across days for every product
under multiple normalizations.

Normalization methods:
    bucket0     : delta_from_bucket0  (path style; 5 values, [0]=0)
    day_mean    : delta_from_day_mean (centered)
    prev_bucket : delta_from_prev_bucket (4 step values)
    group       : delta_from_group_bucket_mean (group-relative)

Per (product, method) we report:
    cross_day_shape_corr_mean : Pearson r between day pairs (3 pairs).
    rank_corr_mean            : Spearman r between day pairs.
    sign_consistency          : fraction of bucket/day combinations whose sign
                                matches the cross-day mean sign.
    bucket_std_mean           : average across-day std of the per-bucket value.
    bucket_std_max            : worst across-day std.
    max_abs_avg_delta         : max |mean across days| of bucket value.
    max_delta_over_spread     : max_abs_avg_delta / median spread.
    max_delta_over_realized_vol : max_abs_avg_delta / mean realized vol of mid changes.
    one_day_overfit_score     : abs(avg) / max(abs(per-day vector)). Lower means
                                a single day dominates.
    all_days_positive_buckets : count of buckets where all 3 days share the
                                same non-zero sign.

Output: analysis/round5-hidden-paths/product_path_stability.csv
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import OUT_DIR, ALL_PRODUCTS, PRODUCT_TO_GROUP, DAYS, load_prices  # noqa: E402

METHODS = {
    "bucket0": "delta_from_bucket0",
    "day_mean": "delta_from_day_mean",
    "prev_bucket": "delta_from_prev_bucket",
    "group": "delta_from_group_bucket_mean",
}


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    a = pd.Series(a).rank()
    b = pd.Series(b).rank()
    return pearson(a.values, b.values)


def realized_vol(mid_series):
    diffs = np.diff(mid_series)
    if diffs.size == 0:
        return float("nan")
    return float(np.std(diffs))


def main():
    bucket_path = os.path.join(OUT_DIR, "product_bucket_paths.csv")
    bucket = pd.read_csv(bucket_path)
    print("loaded bucket rows=%d" % len(bucket))

    print("loading raw prices for spread / realized vol...")
    raw = load_prices()
    spread_med = raw.groupby("product")["spread"].median().to_dict()
    rvol = (
        raw.sort_values(["product", "day", "timestamp"])
        .groupby(["product", "day"])["mid"]
        .apply(lambda s: realized_vol(s.values))
        .reset_index()
        .rename(columns={"mid": "rvol_day"})
    )
    rvol_mean = rvol.groupby("product")["rvol_day"].mean().to_dict()

    rows = []
    for product in ALL_PRODUCTS:
        sub = bucket[bucket["product"] == product].sort_values(["day", "bucket"])
        for method_name, col in METHODS.items():
            # Build day -> vector of bucket values, dropping NaN (prev_bucket has NaN at bucket 0).
            day_vectors = []
            for day in DAYS:
                day_vals = sub[sub["day"] == day][col].values
                if method_name == "prev_bucket":
                    day_vals = day_vals[1:]  # drop NaN at bucket 0
                day_vectors.append(day_vals)
            stacked = np.array(day_vectors)  # shape (3, n_buckets_for_method)

            if np.any(np.isnan(stacked)):
                # Fall back: skip if any unexpected NaN.
                stacked = np.nan_to_num(stacked, nan=0.0)

            # Cross-day shape correlations.
            corr_pairs = []
            rank_pairs = []
            for i, j in combinations(range(stacked.shape[0]), 2):
                corr_pairs.append(pearson(stacked[i], stacked[j]))
                rank_pairs.append(spearman(stacked[i], stacked[j]))
            cross_day_shape_corr_mean = float(np.nanmean(corr_pairs)) if corr_pairs else float("nan")
            rank_corr_mean = float(np.nanmean(rank_pairs)) if rank_pairs else float("nan")

            # Average across days to get the canonical path; sign consistency vs that.
            avg = stacked.mean(axis=0)
            avg_signs = np.sign(avg)
            stacked_signs = np.sign(stacked)
            # zero is treated as not-matching for sign_consistency unless avg_sign is also 0.
            matches = (stacked_signs == avg_signs[None, :]) & (avg_signs[None, :] != 0)
            sign_consistency = float(matches.mean()) if matches.size else float("nan")

            bucket_std = stacked.std(axis=0, ddof=0)
            bucket_std_mean = float(np.nanmean(bucket_std)) if bucket_std.size else float("nan")
            bucket_std_max = float(np.nanmax(bucket_std)) if bucket_std.size else float("nan")

            abs_avg = np.abs(avg)
            max_abs_avg_delta = float(abs_avg.max()) if abs_avg.size else float("nan")

            sp = spread_med.get(product, np.nan)
            rv = rvol_mean.get(product, np.nan)
            max_delta_over_spread = (
                max_abs_avg_delta / sp if sp and sp > 0 else float("nan")
            )
            max_delta_over_rvol = (
                max_abs_avg_delta / rv if rv and rv > 0 else float("nan")
            )

            # one_day_overfit_score: ratio of |avg| to max single-day |value| across buckets.
            # Higher is better (signal robust across days). Computed at the strongest bucket.
            if abs_avg.size:
                strong_idx = int(np.argmax(abs_avg))
                strong_avg = float(abs_avg[strong_idx])
                strong_per_day = float(np.max(np.abs(stacked[:, strong_idx])))
                one_day_overfit_score = (
                    strong_avg / strong_per_day if strong_per_day > 0 else float("nan")
                )
            else:
                strong_idx = -1
                one_day_overfit_score = float("nan")

            # All-days-same-sign bucket count.
            same_sign = (
                (np.all(stacked > 0, axis=0))
                | (np.all(stacked < 0, axis=0))
            )
            all_days_positive_buckets = int(same_sign.sum())

            rows.append(
                {
                    "product": product,
                    "group": PRODUCT_TO_GROUP[product],
                    "method": method_name,
                    "n_buckets": int(stacked.shape[1]),
                    "cross_day_shape_corr_mean": round(cross_day_shape_corr_mean, 6),
                    "rank_corr_mean": round(rank_corr_mean, 6),
                    "sign_consistency": round(sign_consistency, 6),
                    "bucket_std_mean": round(bucket_std_mean, 4),
                    "bucket_std_max": round(bucket_std_max, 4),
                    "max_abs_avg_delta": round(max_abs_avg_delta, 4),
                    "max_delta_over_spread": round(max_delta_over_spread, 4)
                    if np.isfinite(max_delta_over_spread)
                    else float("nan"),
                    "max_delta_over_realized_vol": round(max_delta_over_rvol, 4)
                    if np.isfinite(max_delta_over_rvol)
                    else float("nan"),
                    "one_day_overfit_score": round(one_day_overfit_score, 6)
                    if np.isfinite(one_day_overfit_score)
                    else float("nan"),
                    "all_days_same_sign_buckets": all_days_positive_buckets,
                    "median_spread": round(float(sp), 6) if sp is not None else float("nan"),
                    "mean_realized_vol": round(float(rv), 6) if rv is not None else float("nan"),
                    "avg_path": "|".join("%.4f" % v for v in avg.tolist()),
                    "day2_path": "|".join("%.4f" % v for v in stacked[0].tolist()),
                    "day3_path": "|".join("%.4f" % v for v in stacked[1].tolist()),
                    "day4_path": "|".join("%.4f" % v for v in stacked[2].tolist()),
                }
            )

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values(["method", "product"]).reset_index(drop=True)
    out_path = os.path.join(OUT_DIR, "product_path_stability.csv")
    out_df.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(out_df)))


if __name__ == "__main__":
    main()
