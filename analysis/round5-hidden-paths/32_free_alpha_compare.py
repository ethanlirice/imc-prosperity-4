"""Compare the known free-alpha 5-bucket fair path to the actual bucket means
for every product.

For each product:
    free_alpha_path[k] = base + d_k     (k = 0..4)

We compute, on day 2/3/4 separately and pooled:
    actual_path[k]         = mean_mid in bucket k
    error[k]               = actual_path[k] - free_alpha_path[k]
    abs_error[k]           = |error[k]|
    shape_corr             = Pearson(actual_path, free_alpha_path)
    delta_corr             = Pearson(actual_path - actual_path[0], free_alpha_d)
    coverage_label         = "v7_free_alpha" / "v5_only" / "not_in_v7" / "no_table"

We also report cross-day stability metrics drawn from product_path_stability.csv
so the next agent can compare known-trusted products to candidates.

Output: analysis/round5-hidden-paths/free_alpha_shape_comparison.csv
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
    FREE_ALPHA_TABLE,
    V7_FREE_ALPHA_PRODUCTS,
    free_alpha_path,
)


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main():
    bucket_path = os.path.join(OUT_DIR, "product_bucket_paths.csv")
    bucket = pd.read_csv(bucket_path)
    stab_path = os.path.join(OUT_DIR, "product_path_stability.csv")
    stab = pd.read_csv(stab_path)
    stab_b0 = stab[stab["method"] == "bucket0"].set_index("product")

    rows = []
    for product in ALL_PRODUCTS:
        sub = bucket[bucket["product"] == product].sort_values(["day", "bucket"])
        fa = free_alpha_path(product)  # may be None
        fa_d = None
        if fa is not None:
            fa_arr = np.array(fa, dtype=float)
            fa_d = fa_arr - fa_arr[0]
        else:
            fa_arr = None

        # Per-day comparisons.
        per_day_shape_corr = {}
        per_day_delta_corr = {}
        per_day_mae = {}
        per_day_anchor_err = {}
        for day in DAYS:
            day_vals = sub[sub["day"] == day].sort_values("bucket")
            actual = day_vals["mean_mid"].values
            actual_d = actual - actual[0] if actual.size else np.array([])
            if fa_arr is not None and actual.size == fa_arr.size:
                per_day_shape_corr[day] = pearson(actual, fa_arr)
                per_day_delta_corr[day] = pearson(actual_d, fa_d)
                per_day_mae[day] = float(np.mean(np.abs(actual - fa_arr)))
                per_day_anchor_err[day] = float(actual[0] - fa_arr[0])
            else:
                per_day_shape_corr[day] = float("nan")
                per_day_delta_corr[day] = float("nan")
                per_day_mae[day] = float("nan")
                per_day_anchor_err[day] = float("nan")

        # Pooled (avg across days) actual path.
        pooled = (
            sub.groupby("bucket")["mean_mid"]
            .mean()
            .sort_index()
            .values
        )
        pooled_d = pooled - pooled[0] if pooled.size else np.array([])
        if fa_arr is not None and pooled.size == fa_arr.size:
            pooled_shape_corr = pearson(pooled, fa_arr)
            pooled_delta_corr = pearson(pooled_d, fa_d)
            pooled_mae = float(np.mean(np.abs(pooled - fa_arr)))
            pooled_anchor_err = float(pooled[0] - fa_arr[0])
        else:
            pooled_shape_corr = float("nan")
            pooled_delta_corr = float("nan")
            pooled_mae = float("nan")
            pooled_anchor_err = float("nan")

        # Coverage label.
        if product in V7_FREE_ALPHA_PRODUCTS:
            coverage = "v7_free_alpha"
        elif product in FREE_ALPHA_TABLE:
            coverage = "table_only"
        else:
            coverage = "no_table"

        # Stability cross-reference (bucket0 method).
        if product in stab_b0.index:
            stab_row = stab_b0.loc[product]
            shape_stab = float(stab_row["cross_day_shape_corr_mean"])
            sign_stab = float(stab_row["sign_consistency"])
            same_sign_buckets = int(stab_row["all_days_same_sign_buckets"])
            max_abs_avg_delta = float(stab_row["max_abs_avg_delta"])
        else:
            shape_stab = float("nan")
            sign_stab = float("nan")
            same_sign_buckets = -1
            max_abs_avg_delta = float("nan")

        rows.append(
            {
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "coverage_label": coverage,
                "free_alpha_path": "|".join("%.4f" % v for v in fa_arr.tolist()) if fa_arr is not None else "",
                "free_alpha_d": "|".join("%.4f" % v for v in fa_d.tolist()) if fa_d is not None else "",
                "actual_pooled_path": "|".join("%.4f" % v for v in pooled.tolist()),
                "actual_pooled_d": "|".join("%.4f" % v for v in pooled_d.tolist()),
                "pooled_shape_corr": round(pooled_shape_corr, 6) if np.isfinite(pooled_shape_corr) else float("nan"),
                "pooled_delta_corr": round(pooled_delta_corr, 6) if np.isfinite(pooled_delta_corr) else float("nan"),
                "pooled_mae": round(pooled_mae, 4) if np.isfinite(pooled_mae) else float("nan"),
                "pooled_anchor_err": round(pooled_anchor_err, 4) if np.isfinite(pooled_anchor_err) else float("nan"),
                "day2_shape_corr": round(per_day_shape_corr[2], 6) if np.isfinite(per_day_shape_corr[2]) else float("nan"),
                "day3_shape_corr": round(per_day_shape_corr[3], 6) if np.isfinite(per_day_shape_corr[3]) else float("nan"),
                "day4_shape_corr": round(per_day_shape_corr[4], 6) if np.isfinite(per_day_shape_corr[4]) else float("nan"),
                "day2_delta_corr": round(per_day_delta_corr[2], 6) if np.isfinite(per_day_delta_corr[2]) else float("nan"),
                "day3_delta_corr": round(per_day_delta_corr[3], 6) if np.isfinite(per_day_delta_corr[3]) else float("nan"),
                "day4_delta_corr": round(per_day_delta_corr[4], 6) if np.isfinite(per_day_delta_corr[4]) else float("nan"),
                "day2_mae": round(per_day_mae[2], 4) if np.isfinite(per_day_mae[2]) else float("nan"),
                "day3_mae": round(per_day_mae[3], 4) if np.isfinite(per_day_mae[3]) else float("nan"),
                "day4_mae": round(per_day_mae[4], 4) if np.isfinite(per_day_mae[4]) else float("nan"),
                "stab_cross_day_corr": round(shape_stab, 6) if np.isfinite(shape_stab) else float("nan"),
                "stab_sign_consistency": round(sign_stab, 6) if np.isfinite(sign_stab) else float("nan"),
                "stab_same_sign_buckets": same_sign_buckets,
                "stab_max_abs_avg_delta": round(max_abs_avg_delta, 4)
                if np.isfinite(max_abs_avg_delta)
                else float("nan"),
            }
        )

    out_df = pd.DataFrame(rows)
    # Sort by stability of the actual delta path (so non-table products with strong delta can also be seen).
    out_df = out_df.sort_values(
        ["coverage_label", "stab_cross_day_corr"], ascending=[True, False]
    ).reset_index(drop=True)
    out_path = os.path.join(OUT_DIR, "free_alpha_shape_comparison.csv")
    out_df.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(out_df)))


if __name__ == "__main__":
    main()
