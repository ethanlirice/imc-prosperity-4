"""Cross-product synchronized basket path analysis.

Hypothesis: within a 5-product family, the *basket-level* bucket path may move
together in a way that is more stable than any one product's path. If group
basket movement is the engine signal, the right exploit is a basket-level
overlay (1-vs-N residuals) rather than 5 independent free-alpha entries.

For each group on each day:
    basket_path[k] = sum (or mean) of mean_mid across the 5 products in bucket k.
    basket_centered[k] = basket_path[k] - basket_path[0]

We measure:
    - cross-day Pearson correlation of basket_centered shape (3 day pairs).
    - sign consistency of basket_centered.
    - basket movement magnitude vs. average product spread.

Then for each product within the group, we measure how much of its bucket
path movement is explained by the basket path:
    OLS regress  product_centered = alpha * basket_centered + epsilon
    R^2 per day, average R^2.

A high group basket cross-day corr with high average per-product R^2 implies
"the engine moves a basket-level fair value, products track basket". A low
basket corr but high product corr implies idiosyncratic per-product paths.

Output:
    analysis/round5/hidden-paths/basket_synchrony_group.csv
    analysis/round5/hidden-paths/basket_synchrony_product.csv
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import OUT_DIR, PRODUCT_GROUPS, PRODUCT_TO_GROUP, DAYS  # noqa: E402


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main():
    bucket = pd.read_csv(os.path.join(OUT_DIR, "product_bucket_paths.csv"))

    # Build per (group, day) basket path: sum of bucket means across 5 products,
    # centered on bucket 0.
    group_rows = []
    product_rows = []
    for group_name, products in PRODUCT_GROUPS.items():
        group_data = bucket[bucket["product"].isin(products)]
        # basket_path: per (day, bucket) summed mean_mid.
        sumdf = (
            group_data.groupby(["day", "bucket"])["mean_mid"].sum().unstack().sort_index()
        )  # rows=day, cols=bucket
        meandf = (
            group_data.groupby(["day", "bucket"])["mean_mid"].mean().unstack().sort_index()
        )
        if sumdf.shape != (3, 5):
            continue

        # Centered shapes per day.
        sum_centered = sumdf.values - sumdf.values[:, 0:1]
        mean_centered = meandf.values - meandf.values[:, 0:1]

        sum_corrs = [pearson(sum_centered[i], sum_centered[j]) for i, j in combinations(range(3), 2)]
        mean_corrs = [pearson(mean_centered[i], mean_centered[j]) for i, j in combinations(range(3), 2)]
        sum_avg = sum_centered.mean(axis=0)
        mean_avg = mean_centered.mean(axis=0)
        sum_signs = np.sign(sum_centered)
        sum_avg_signs = np.sign(sum_avg)
        sum_sign_match = (sum_signs == sum_avg_signs[None, :]) & (sum_avg_signs[None, :] != 0)
        mean_signs = np.sign(mean_centered)
        mean_avg_signs = np.sign(mean_avg)
        mean_sign_match = (mean_signs == mean_avg_signs[None, :]) & (mean_avg_signs[None, :] != 0)

        # Spread reference (average across the group).
        avg_spread = group_data["mean_spread"].mean()

        group_rows.append(
            {
                "group": group_name,
                "basket_sum_avg_path": "|".join("%.4f" % v for v in sum_avg.tolist()),
                "basket_mean_avg_path": "|".join("%.4f" % v for v in mean_avg.tolist()),
                "basket_sum_max_abs": round(float(np.max(np.abs(sum_avg))), 4),
                "basket_mean_max_abs": round(float(np.max(np.abs(mean_avg))), 4),
                "basket_sum_cross_day_corr": round(float(np.nanmean(sum_corrs)), 6),
                "basket_mean_cross_day_corr": round(float(np.nanmean(mean_corrs)), 6),
                "basket_sum_sign_consistency": round(float(sum_sign_match.mean()), 6) if sum_sign_match.size else float("nan"),
                "basket_mean_sign_consistency": round(float(mean_sign_match.mean()), 6) if mean_sign_match.size else float("nan"),
                "basket_sum_max_over_avg_spread": round(float(np.max(np.abs(sum_avg)) / max(avg_spread, 1e-9)), 4),
                "basket_mean_max_over_avg_spread": round(float(np.max(np.abs(mean_avg)) / max(avg_spread, 1e-9)), 4),
            }
        )

        # Per-product fit: product_centered = alpha * basket_mean_centered + eps.
        # Use the mean basket (not sum) because it's on the same scale as a product mid.
        for product in products:
            prod_data = bucket[bucket["product"] == product]
            prod_buckets = (
                prod_data.groupby(["day", "bucket"])["mean_mid"].mean().unstack().sort_index()
            )
            if prod_buckets.shape != (3, 5):
                continue
            prod_centered = prod_buckets.values - prod_buckets.values[:, 0:1]

            r2_per_day = []
            alpha_per_day = []
            beta_per_day = []
            for i in range(3):
                x = mean_centered[i]
                y = prod_centered[i]
                X = np.vstack([x, np.ones_like(x)]).T
                coef, *_ = np.linalg.lstsq(X, y, rcond=None)
                a, b = float(coef[0]), float(coef[1])
                pred = a * x + b
                ss_res = float(np.sum((y - pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
                r2_per_day.append(r2)
                alpha_per_day.append(a)
                beta_per_day.append(b)

            # Cross-day Pearson of (product_centered - alpha*basket_centered),
            # i.e. the residual after group-explained part.
            resid_stack = []
            for i in range(3):
                x = mean_centered[i]
                y = prod_centered[i]
                a = float(alpha_per_day[i])
                resid_stack.append(y - a * x)
            resid_stack = np.array(resid_stack)
            resid_corrs = [pearson(resid_stack[i], resid_stack[j]) for i, j in combinations(range(3), 2)]
            resid_avg = resid_stack.mean(axis=0)
            resid_max_abs = float(np.max(np.abs(resid_avg)))

            product_rows.append(
                {
                    "group": group_name,
                    "product": product,
                    "alpha_mean": round(float(np.nanmean(alpha_per_day)), 6),
                    "alpha_std": round(float(np.nanstd(alpha_per_day)), 6),
                    "r2_mean": round(float(np.nanmean(r2_per_day)), 6),
                    "r2_min": round(float(np.nanmin(r2_per_day)), 6),
                    "resid_avg_path": "|".join("%.4f" % v for v in resid_avg.tolist()),
                    "resid_max_abs": round(resid_max_abs, 4),
                    "resid_cross_day_corr": round(float(np.nanmean(resid_corrs)), 6) if resid_corrs else float("nan"),
                }
            )

    g_df = pd.DataFrame(group_rows).sort_values("basket_mean_cross_day_corr", ascending=False)
    p_df = pd.DataFrame(product_rows).sort_values(["group", "r2_mean"], ascending=[True, False])
    g_path = os.path.join(OUT_DIR, "basket_synchrony_group.csv")
    p_path = os.path.join(OUT_DIR, "basket_synchrony_product.csv")
    g_df.to_csv(g_path, index=False)
    p_df.to_csv(p_path, index=False)
    print("wrote %s rows=%d" % (g_path, len(g_df)))
    print("wrote %s rows=%d" % (p_path, len(p_df)))
    print()
    print("--- group basket synchrony, ranked ---")
    print(g_df.to_string(index=False))


if __name__ == "__main__":
    main()
