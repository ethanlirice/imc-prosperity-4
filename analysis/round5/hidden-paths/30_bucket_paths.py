"""Build product/day/bucket path summaries.

For each (product, day, bucket=0..4) compute:
    mean_mid, median_mid, open_mid, close_mid, vwap_proxy_mid (weighted L1+L2+L3),
    micro_mid (L1 microprice), n_obs, mean_spread, mean_depth.

Then for each (product, day) compute deltas relative to:
    bucket0 (path style, matches FREE_ALPHA),
    full-day mean,
    previous bucket (bucket step),
    group index bucket mean (group is the 5-product family).

Output: analysis/round5/hidden-paths/product_bucket_paths.csv

Columns:
    product, group, day, bucket, n_obs,
    mean_mid, median_mid, open_mid, close_mid, vwap_mid, micro_mid,
    mean_spread, mean_depth,
    delta_from_bucket0, delta_from_day_mean, delta_from_prev_bucket,
    delta_from_group_bucket_mean
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import OUT_DIR, ALL_PRODUCTS, PRODUCT_TO_GROUP, load_prices, N_BUCKETS  # noqa: E402


def main():
    print("loading prices...")
    df = load_prices()
    print("rows=%d products=%d days=%d" % (len(df), df["product"].nunique(), df["day"].nunique()))

    # Bucket-level aggregates.
    grouped = df.groupby(["product", "day", "bucket"])
    agg = grouped.agg(
        n_obs=("mid", "size"),
        mean_mid=("mid", "mean"),
        median_mid=("mid", "median"),
        open_mid=("mid", "first"),
        close_mid=("mid", "last"),
        vwap_mid=("weighted_mid", "mean"),
        micro_mid=("micro_mid", "mean"),
        mean_spread=("spread", "mean"),
        mean_depth=("total_depth", "mean"),
    ).reset_index()

    # Day-level aggregates for delta-from-day-mean.
    day_agg = df.groupby(["product", "day"])["mid"].mean().reset_index()
    day_agg = day_agg.rename(columns={"mid": "day_mean_mid"})
    agg = agg.merge(day_agg, on=["product", "day"], how="left")

    # Group bucket mean (each row's product's group, on the same day+bucket, averaged across the 5 products).
    agg["group"] = agg["product"].map(PRODUCT_TO_GROUP)
    group_bucket_mean = (
        agg.groupby(["group", "day", "bucket"])["mean_mid"].mean().reset_index().rename(
            columns={"mean_mid": "group_bucket_mean"}
        )
    )
    agg = agg.merge(group_bucket_mean, on=["group", "day", "bucket"], how="left")

    # Bucket0 reference (for delta_from_bucket0 — the "free-alpha-shaped" delta).
    bucket0 = (
        agg[agg["bucket"] == 0][["product", "day", "mean_mid"]]
        .rename(columns={"mean_mid": "bucket0_mean_mid"})
    )
    agg = agg.merge(bucket0, on=["product", "day"], how="left")

    # Previous bucket reference per (product, day).
    agg = agg.sort_values(["product", "day", "bucket"]).reset_index(drop=True)
    agg["prev_bucket_mean_mid"] = (
        agg.groupby(["product", "day"])["mean_mid"].shift(1)
    )

    agg["delta_from_bucket0"] = agg["mean_mid"] - agg["bucket0_mean_mid"]
    agg["delta_from_day_mean"] = agg["mean_mid"] - agg["day_mean_mid"]
    agg["delta_from_prev_bucket"] = agg["mean_mid"] - agg["prev_bucket_mean_mid"]
    agg["delta_from_group_bucket_mean"] = agg["mean_mid"] - agg["group_bucket_mean"]

    out_cols = [
        "product",
        "group",
        "day",
        "bucket",
        "n_obs",
        "mean_mid",
        "median_mid",
        "open_mid",
        "close_mid",
        "vwap_mid",
        "micro_mid",
        "mean_spread",
        "mean_depth",
        "day_mean_mid",
        "group_bucket_mean",
        "bucket0_mean_mid",
        "prev_bucket_mean_mid",
        "delta_from_bucket0",
        "delta_from_day_mean",
        "delta_from_prev_bucket",
        "delta_from_group_bucket_mean",
    ]
    out_df = agg[out_cols].sort_values(["product", "day", "bucket"]).reset_index(drop=True)

    # Round most numeric outputs to 6 dp for compactness.
    for col in out_df.columns:
        if col in ("product", "group", "day", "bucket", "n_obs"):
            continue
        out_df[col] = out_df[col].astype(float).round(6)

    out_path = os.path.join(OUT_DIR, "product_bucket_paths.csv")
    out_df.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(out_df)))

    # Sanity: ensure 5 buckets per product per day.
    counts = out_df.groupby(["product", "day"]).size()
    bad = counts[counts != N_BUCKETS]
    if len(bad) > 0:
        print("WARNING: missing buckets for some (product, day):")
        print(bad.head())
    expected = len(ALL_PRODUCTS) * 3 * N_BUCKETS
    assert len(out_df) == expected, (len(out_df), expected)
    print("ok: 50 products x 3 days x 5 buckets = %d rows" % expected)


if __name__ == "__main__":
    main()
