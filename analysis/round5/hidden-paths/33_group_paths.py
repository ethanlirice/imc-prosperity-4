"""Group-level path search.

For each 5-product family, on each day:
  - group_path[k]   = mean across the 5 products of mean_mid in bucket k.
  - For each product p in the group:
      offset_only:   p_path[k] - group_path[k]      (additive offset)
      scale_offset:  fit alpha, beta minimizing      (a*group_path[k] + b - p_path[k])^2
      residual_path[k] = p_path[k] - alpha*group_path[k] - beta

We compute, per (group, product):
  - cross-day stability of the residual path (Pearson r between day pairs averaged),
  - sign consistency of residual_path across days,
  - max|avg residual_path|,
  - rms residual,
  - whether the offset_only alpha=1 is actually a good fit (R^2),
  - whether the residual path has a predictable bucket-direction pattern.

Outputs:
  group_path_summary.csv          — per (group, day, bucket) the group_path mean.
  group_product_residual_paths.csv — per (group, product) summary stats including
                                     residual path values per bucket and stability.
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import OUT_DIR, ALL_PRODUCTS, PRODUCT_GROUPS, PRODUCT_TO_GROUP, DAYS  # noqa: E402


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def fit_scale_offset(group_path, product_path):
    """Return (alpha, beta, r2) for product = alpha*group + beta + eps."""
    g = np.asarray(group_path, dtype=float)
    p = np.asarray(product_path, dtype=float)
    if g.size < 2:
        return float("nan"), float("nan"), float("nan")
    G = np.vstack([g, np.ones_like(g)]).T
    coef, *_ = np.linalg.lstsq(G, p, rcond=None)
    alpha, beta = coef[0], coef[1]
    pred = alpha * g + beta
    ss_res = float(np.sum((p - pred) ** 2))
    ss_tot = float(np.sum((p - p.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(alpha), float(beta), float(r2)


def main():
    bucket_path = os.path.join(OUT_DIR, "product_bucket_paths.csv")
    bucket = pd.read_csv(bucket_path)

    # group_path[group, day, bucket] = mean across the 5 products of mean_mid.
    group_path = (
        bucket.groupby(["group", "day", "bucket"])["mean_mid"]
        .mean()
        .reset_index()
        .rename(columns={"mean_mid": "group_path_mean"})
    )

    # Also include a vol-weighted version: 1/var weighting (using mean_depth as proxy).
    # For now keep simple: also export median across products in the group.
    group_path_med = (
        bucket.groupby(["group", "day", "bucket"])["mean_mid"]
        .median()
        .reset_index()
        .rename(columns={"mean_mid": "group_path_median"})
    )
    group_path = group_path.merge(group_path_med, on=["group", "day", "bucket"], how="left")

    # group bucket0 reference per (group, day) for path-style deltas.
    g0 = (
        group_path[group_path["bucket"] == 0][["group", "day", "group_path_mean"]]
        .rename(columns={"group_path_mean": "group_bucket0"})
    )
    group_path = group_path.merge(g0, on=["group", "day"], how="left")
    group_path["group_path_d"] = group_path["group_path_mean"] - group_path["group_bucket0"]

    group_path = group_path.sort_values(["group", "day", "bucket"]).reset_index(drop=True)
    group_path["group_path_mean"] = group_path["group_path_mean"].round(6)
    group_path["group_path_median"] = group_path["group_path_median"].round(6)
    group_path["group_path_d"] = group_path["group_path_d"].round(6)

    out_summary = os.path.join(OUT_DIR, "group_path_summary.csv")
    group_path.to_csv(out_summary, index=False)
    print("wrote %s rows=%d" % (out_summary, len(group_path)))

    # Residual paths per product.
    rows = []
    for group_name, products in PRODUCT_GROUPS.items():
        for product in products:
            # day -> {offset_residual: 5-vec, scale_residual: 5-vec, alpha, beta, r2}.
            offset_resids = {}
            scale_resids = {}
            alphas = {}
            betas = {}
            r2s = {}
            for day in DAYS:
                gp = group_path[(group_path["group"] == group_name) & (group_path["day"] == day)].sort_values("bucket")["group_path_mean"].values
                pp = bucket[(bucket["product"] == product) & (bucket["day"] == day)].sort_values("bucket")["mean_mid"].values
                if gp.size != 5 or pp.size != 5:
                    continue
                offset_resids[day] = pp - gp  # additive only
                alpha, beta, r2 = fit_scale_offset(gp, pp)
                pred = alpha * gp + beta
                scale_resids[day] = pp - pred
                alphas[day] = alpha
                betas[day] = beta
                r2s[day] = r2

            if not offset_resids:
                continue

            offset_stack = np.array([offset_resids[d] for d in DAYS])  # shape (3, 5)
            scale_stack = np.array([scale_resids[d] for d in DAYS])  # shape (3, 5)

            # Cross-day stability for offset residual.
            offset_pair_corrs = [pearson(offset_stack[i], offset_stack[j]) for i, j in combinations(range(3), 2)]
            scale_pair_corrs = [pearson(scale_stack[i], scale_stack[j]) for i, j in combinations(range(3), 2)]

            offset_avg = offset_stack.mean(axis=0)
            scale_avg = scale_stack.mean(axis=0)

            # Sign consistency.
            offset_signs = np.sign(offset_stack)
            offset_avg_signs = np.sign(offset_avg)
            offset_sign_match = (
                (offset_signs == offset_avg_signs[None, :]) & (offset_avg_signs[None, :] != 0)
            )
            scale_signs = np.sign(scale_stack)
            scale_avg_signs = np.sign(scale_avg)
            scale_sign_match = (
                (scale_signs == scale_avg_signs[None, :]) & (scale_avg_signs[None, :] != 0)
            )

            offset_all_same_sign = int(
                np.sum(np.all(offset_stack > 0, axis=0) | np.all(offset_stack < 0, axis=0))
            )
            scale_all_same_sign = int(
                np.sum(np.all(scale_stack > 0, axis=0) | np.all(scale_stack < 0, axis=0))
            )

            rows.append(
                {
                    "group": group_name,
                    "product": product,
                    "alpha_mean": round(float(np.mean(list(alphas.values()))), 6),
                    "beta_mean": round(float(np.mean(list(betas.values()))), 4),
                    "r2_mean": round(float(np.mean(list(r2s.values()))), 6),
                    "alpha_std": round(float(np.std(list(alphas.values()))), 6),
                    "beta_std": round(float(np.std(list(betas.values()))), 4),
                    "offset_avg_path": "|".join("%.4f" % v for v in offset_avg.tolist()),
                    "offset_max_abs": round(float(np.max(np.abs(offset_avg))), 4),
                    "offset_cross_day_corr_mean": round(float(np.nanmean(offset_pair_corrs)), 6)
                    if offset_pair_corrs
                    else float("nan"),
                    "offset_sign_consistency": round(float(offset_sign_match.mean()), 6)
                    if offset_sign_match.size
                    else float("nan"),
                    "offset_all_days_same_sign_buckets": offset_all_same_sign,
                    "scale_avg_path": "|".join("%.4f" % v for v in scale_avg.tolist()),
                    "scale_max_abs": round(float(np.max(np.abs(scale_avg))), 4),
                    "scale_cross_day_corr_mean": round(float(np.nanmean(scale_pair_corrs)), 6)
                    if scale_pair_corrs
                    else float("nan"),
                    "scale_sign_consistency": round(float(scale_sign_match.mean()), 6)
                    if scale_sign_match.size
                    else float("nan"),
                    "scale_all_days_same_sign_buckets": scale_all_same_sign,
                    "rms_offset_resid": round(float(np.sqrt(np.mean(offset_stack ** 2))), 4),
                    "rms_scale_resid": round(float(np.sqrt(np.mean(scale_stack ** 2))), 4),
                }
            )

    res_df = pd.DataFrame(rows)
    res_df = res_df.sort_values(["group", "scale_cross_day_corr_mean"], ascending=[True, False]).reset_index(drop=True)
    out_res = os.path.join(OUT_DIR, "group_product_residual_paths.csv")
    res_df.to_csv(out_res, index=False)
    print("wrote %s rows=%d" % (out_res, len(res_df)))


if __name__ == "__main__":
    main()
