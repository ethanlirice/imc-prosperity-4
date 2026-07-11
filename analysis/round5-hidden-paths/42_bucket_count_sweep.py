"""Bucket-count sensitivity sweep.

The FREE_ALPHA table is structured as 5 buckets. We test if the structure
disappears at neighbouring counts. If 4-bucket and 6-bucket stability scores
are dramatically lower than 5-bucket, the table was *fitted* to the bucket
count and the boundaries themselves are the relevant signal. If 5 is just one
of several counts that show structure, the underlying schedule is finer
and the 5-bucket choice is convenience.

For each bucket count C in {3, 4, 5, 6, 8, 10, 20}:
    For each product:
      - Compute bucket-mean path on each of D2/D3/D4.
      - Compute cross-day Pearson correlation of bucket0-anchored shape
        averaged over the 3 day pairs.
      - Compute sign consistency.
      - Track all-day-same-sign bucket count / total buckets.

We then output a long-format table summarising stability per (product, C).

Output:
    analysis/round5-hidden-paths/bucket_count_stability.csv
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import OUT_DIR, DATA_DIR, ALL_PRODUCTS, PRODUCT_TO_GROUP, DAYS  # noqa: E402

BUCKET_COUNTS = [3, 4, 5, 6, 8, 10, 20]


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main():
    frames = []
    for d in DAYS:
        df = pd.read_csv(os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % d), sep=";")
        df["mid"] = df["mid_price"].astype(float)
        frames.append(df[["day", "timestamp", "product", "mid"]])
    raw = pd.concat(frames, ignore_index=True)

    rows = []
    for C in BUCKET_COUNTS:
        # bucket size in timestamp units; final bucket includes 999_900.
        bucket_size = 1_000_000 // C
        raw_c = raw.copy()
        raw_c["bucket"] = np.minimum(C - 1, raw_c["timestamp"] // bucket_size).astype(int)
        agg = raw_c.groupby(["product", "day", "bucket"])["mid"].mean().reset_index().rename(columns={"mid": "mean_mid"})
        for product in ALL_PRODUCTS:
            sub = agg[agg["product"] == product]
            day_vecs = []
            for d in DAYS:
                vals = sub[sub["day"] == d].sort_values("bucket")["mean_mid"].values
                if vals.size == C:
                    day_vecs.append(vals - vals[0])  # bucket0-anchored shape
            if len(day_vecs) != 3:
                continue
            stack = np.array(day_vecs)
            corrs = [pearson(stack[i], stack[j]) for i, j in combinations(range(3), 2)]
            avg = stack.mean(axis=0)
            avg_signs = np.sign(avg)
            stack_signs = np.sign(stack)
            sign_match = (stack_signs == avg_signs[None, :]) & (avg_signs[None, :] != 0)
            same_sign = int(np.sum(np.all(stack > 0, axis=0) | np.all(stack < 0, axis=0)))
            rows.append(
                {
                    "product": product,
                    "group": PRODUCT_TO_GROUP[product],
                    "C": C,
                    "cross_day_corr_mean": round(float(np.nanmean(corrs)), 6),
                    "sign_consistency": round(float(sign_match.mean()), 6) if sign_match.size else float("nan"),
                    "all_days_same_sign_buckets": same_sign,
                    "all_days_same_sign_frac": round(same_sign / C, 6),
                    "max_abs_avg_delta": round(float(np.max(np.abs(avg))), 4),
                }
            )

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values(["product", "C"]).reset_index(drop=True)
    out_path = os.path.join(OUT_DIR, "bucket_count_stability.csv")
    out_df.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(out_df)))

    # Summary: for each C, what's the average cross-day shape corr across all
    # products? What's the share of products with corr >= 0.5?
    summary = (
        out_df.groupby("C")
        .agg(
            mean_corr=("cross_day_corr_mean", "mean"),
            median_corr=("cross_day_corr_mean", "median"),
            frac_strong=("cross_day_corr_mean", lambda s: float((s >= 0.5).mean())),
            mean_sign_consistency=("sign_consistency", "mean"),
        )
        .reset_index()
    )
    print()
    print("--- summary across products ---")
    print(summary.to_string(index=False))
    print()
    print("--- products with strong stability (corr >= 0.5) per C ---")
    strong = (
        out_df[out_df["cross_day_corr_mean"] >= 0.5]
        .groupby("C")
        .apply(
            lambda g: ", ".join(
                "%s(%.2f)" % (r.product, r.cross_day_corr_mean)
                for _, r in g.sort_values("cross_day_corr_mean", ascending=False).head(8).iterrows()
            )
        )
        .reset_index()
        .rename(columns={0: "top_products"})
    )
    print(strong.to_string(index=False))


if __name__ == "__main__":
    main()
