"""Rank products into a master candidate list for the next strategy agent.

For each product we pick the BEST `(path_type, threshold)` configuration as the
one that maximises `worst_day_pnl` subject to all-3-folds-positive (folds_positive==3).
If no config has all 3 folds positive, we fall back to max(worst_day_pnl) overall
and flag the product.

Then we attach stability metrics (best across normalisation methods) and v7
ownership labels.

Output: analysis/round5-hidden-paths/candidate_products.csv

Columns:
    product, group,
    best_path_type, best_threshold,
    folds_positive, total_pnl, worst_day_pnl, best_day_pnl, total_trades,
    folds_positive_any_config_count, all_3_fold_configs_count,
    stab_method, stab_cross_day_corr, stab_sign_consistency,
    stab_same_sign_buckets, stab_max_abs_avg_delta,
    stab_max_delta_over_spread, stab_max_delta_over_realized_vol,
    free_alpha_pooled_delta_corr, free_alpha_pooled_mae,
    v7_owner_label, v7_overlap_likely,
    notes
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
    V7_FREE_ALPHA_PRODUCTS,
    V7_MR_PRODUCTS,
    V7_RESIDUAL_PRODUCTS,
    V7_MM_BID_OFF,
    V7_MM_ASK_OFF,
    FREE_ALPHA_TABLE,
)


def v7_label(product):
    labels = []
    if product in V7_FREE_ALPHA_PRODUCTS:
        labels.append("free_alpha")
    if product in V7_MR_PRODUCTS:
        labels.append("mr")
    if product in V7_RESIDUAL_PRODUCTS:
        labels.append("residual")
    if product in V7_MM_BID_OFF:
        labels.append("mm_bid_off")
    if product in V7_MM_ASK_OFF:
        labels.append("mm_ask_off")
    return ",".join(labels) if labels else "unowned"


def main():
    summary = pd.read_csv(os.path.join(OUT_DIR, "path_proxy_backtest_summary.csv"))
    stab = pd.read_csv(os.path.join(OUT_DIR, "product_path_stability.csv"))
    fa = pd.read_csv(os.path.join(OUT_DIR, "free_alpha_shape_comparison.csv"))

    # Best stability row per product across the 4 methods, by cross_day_shape_corr_mean.
    stab_best = (
        stab.sort_values("cross_day_shape_corr_mean", ascending=False)
        .groupby("product", as_index=False)
        .first()
        .rename(
            columns={
                "method": "stab_method",
                "cross_day_shape_corr_mean": "stab_cross_day_corr",
                "sign_consistency": "stab_sign_consistency",
                "all_days_same_sign_buckets": "stab_same_sign_buckets",
                "max_abs_avg_delta": "stab_max_abs_avg_delta",
                "max_delta_over_spread": "stab_max_delta_over_spread",
                "max_delta_over_realized_vol": "stab_max_delta_over_realized_vol",
                "one_day_overfit_score": "stab_one_day_overfit_score",
            }
        )
    )

    # Best stability under bucket0 method specifically (matches v7 free-alpha shape).
    stab_b0 = stab[stab["method"] == "bucket0"].rename(
        columns={
            "cross_day_shape_corr_mean": "stab_b0_cross_day_corr",
            "sign_consistency": "stab_b0_sign_consistency",
            "all_days_same_sign_buckets": "stab_b0_same_sign_buckets",
            "max_abs_avg_delta": "stab_b0_max_abs_avg_delta",
        }
    )[
        [
            "product",
            "stab_b0_cross_day_corr",
            "stab_b0_sign_consistency",
            "stab_b0_same_sign_buckets",
            "stab_b0_max_abs_avg_delta",
        ]
    ]

    fa_use = fa[
        [
            "product",
            "coverage_label",
            "pooled_delta_corr",
            "pooled_mae",
            "day2_delta_corr",
            "day3_delta_corr",
            "day4_delta_corr",
        ]
    ].rename(
        columns={
            "pooled_delta_corr": "free_alpha_pooled_delta_corr",
            "pooled_mae": "free_alpha_pooled_mae",
            "day2_delta_corr": "free_alpha_d2_delta_corr",
            "day3_delta_corr": "free_alpha_d3_delta_corr",
            "day4_delta_corr": "free_alpha_d4_delta_corr",
        }
    )

    rows = []
    for product in ALL_PRODUCTS:
        sub = summary[summary["product"] == product]
        if sub.empty:
            continue
        # Best 3-fold configuration.
        threes = sub[sub["folds_positive"] == 3].sort_values(
            ["worst_day_pnl", "total_pnl"], ascending=[False, False]
        )
        if not threes.empty:
            best = threes.iloc[0]
            fallback = False
        else:
            twos = sub[sub["folds_positive"] == 2].sort_values(
                ["worst_day_pnl", "total_pnl"], ascending=[False, False]
            )
            if not twos.empty:
                best = twos.iloc[0]
            else:
                best = sub.sort_values(
                    ["worst_day_pnl", "total_pnl"], ascending=[False, False]
                ).iloc[0]
            fallback = True

        n_three = int((sub["folds_positive"] == 3).sum())
        any_pos = int((sub["folds_positive"] >= 1).sum())

        rows.append(
            {
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "best_path_type": best["path_type"],
                "best_threshold": int(best["threshold"]),
                "folds_positive": int(best["folds_positive"]),
                "total_pnl": float(best["total_pnl"]),
                "worst_day_pnl": float(best["worst_day_pnl"]),
                "best_day_pnl": float(best["best_day_pnl"]),
                "total_trades": int(best["total_trades"]),
                "all_3_fold_configs_count": n_three,
                "any_pos_fold_configs_count": any_pos,
                "no_3_fold_config": fallback,
            }
        )

    cand = pd.DataFrame(rows)
    cand = cand.merge(
        stab_best[
            [
                "product",
                "stab_method",
                "stab_cross_day_corr",
                "stab_sign_consistency",
                "stab_same_sign_buckets",
                "stab_max_abs_avg_delta",
                "stab_max_delta_over_spread",
                "stab_max_delta_over_realized_vol",
                "stab_one_day_overfit_score",
            ]
        ],
        on="product",
        how="left",
    )
    cand = cand.merge(stab_b0, on="product", how="left")
    cand = cand.merge(fa_use, on="product", how="left")

    cand["v7_owner_label"] = cand["product"].apply(v7_label)
    cand["v7_overlap_likely"] = cand["v7_owner_label"].apply(lambda s: s != "unowned")
    cand["in_free_alpha_table"] = cand["product"].isin(FREE_ALPHA_TABLE.keys())

    # Composite score: prioritise (3 folds positive) + worst-day + stability.
    cand["score"] = (
        cand["folds_positive"].astype(int) * 1_000_000
        + cand["worst_day_pnl"].clip(lower=-100000)
        + cand["stab_b0_cross_day_corr"].fillna(0) * 5000
    )

    cand = cand.sort_values(
        ["folds_positive", "worst_day_pnl", "total_pnl"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    out_path = os.path.join(OUT_DIR, "candidate_products.csv")
    cand.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(cand)))
    print()
    print("--- top 20 by worst-day PnL with all 3 folds positive ---")
    cols = [
        "product",
        "group",
        "best_path_type",
        "best_threshold",
        "folds_positive",
        "total_pnl",
        "worst_day_pnl",
        "stab_b0_cross_day_corr",
        "stab_b0_same_sign_buckets",
        "v7_owner_label",
    ]
    print(cand.head(20)[cols].to_string(index=False))


if __name__ == "__main__":
    main()
