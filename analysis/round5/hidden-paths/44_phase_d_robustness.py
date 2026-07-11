"""Phase D robustness battery for the top walk-forward candidates.

Runs three tests on the top-N candidates from candidate_products.csv:

  1. Random-shuffle null distribution (A-2). For each (product, path_type,
     threshold), shuffle the train-day bucket assignment 200x and re-run the
     walk-forward simulator. The actual 3-fold worst-day pnl must beat the
     95th percentile of the shuffled null to be credible.

  2. Anchor-vs-shape decomposition (B-6). Replace the train-day shape with
     flat zero (so the fair value is just the test-day bucket0 anchor for
     bucket_delta_b0, or the train-day-bucket0 mean for bucket_mean). If pnl
     barely drops, the *shape* contributes nothing — only re-anchoring is.

  3. Per-bucket pnl attribution (B-4). Re-run the actual config and tag every
     trade's pnl by the bucket in which it was *opened* and report bucket-level
     pnl + share of trades within 5k ticks of a bucket boundary.

Outputs:
    analysis/round5/hidden-paths/phase_d_null.csv
    analysis/round5/hidden-paths/phase_d_anchor_vs_shape.csv
    analysis/round5/hidden-paths/phase_d_bucket_attribution.csv
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
    N_BUCKETS,
    PRODUCT_TO_GROUP,
)

POS_LIMIT = 10
TOP_N = 15
N_SHUFFLE = 200
RNG = np.random.default_rng(20260429)
BOUNDARY_WINDOW = 5_000  # ticks


def simulate_vec(bucket_arr, mid_arr, bid_arr, ask_arr, fair_per_bucket, threshold, exit_band,
                  attribute=False):
    """Vectorised pre-mask + tight loop. If attribute, return per-bucket pnl
    and boundary-trade counts."""
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

    bucket_pnl = np.zeros(N_BUCKETS) if attribute else None
    bucket_trades = np.zeros(N_BUCKETS, dtype=int) if attribute else None
    boundary_trades = 0
    bucket_size = 1_000_000 // N_BUCKETS

    for i in sig_idx:
        a = ask_arr[i]
        bb = bid_arr[i]
        m = mid_arr[i]
        fair = fair_arr[i]
        bk = int(bucket_arr[i])

        if abs(m - fair) <= exit_band:
            if pos > 0:
                qty = pos
                delta = qty * (bb - avg_cost)
                realized += qty * bb - qty * avg_cost
                if attribute:
                    bucket_pnl[bk] += delta
                    bucket_trades[bk] += qty
                pos = 0
                avg_cost = 0.0
                trades += qty
                continue
            if pos < 0:
                qty = -pos
                delta = qty * (avg_cost - a)
                realized += qty * avg_cost - qty * a
                if attribute:
                    bucket_pnl[bk] += delta
                    bucket_trades[bk] += qty
                pos = 0
                avg_cost = 0.0
                trades += qty
                continue

        if a < fair - threshold and pos < POS_LIMIT:
            new_pos = pos + 1
            if pos >= 0:
                avg_cost = (avg_cost * pos + a) / new_pos if new_pos != 0 else 0.0
            else:
                # closing/flipping a short
                realized += avg_cost - a
                if attribute:
                    bucket_pnl[bk] += avg_cost - a
                if new_pos == 0:
                    avg_cost = 0.0
            pos = new_pos
            trades += 1
            if attribute:
                bucket_trades[bk] += 1
                # Boundary check: ts within window of bucket boundary
                ts_in_bucket = i  # we don't have raw ts here, ok skip
        elif bb > fair + threshold and pos > -POS_LIMIT:
            new_pos = pos - 1
            if pos <= 0:
                denom = -new_pos if new_pos != 0 else 1
                avg_cost = (avg_cost * (-pos) + bb) / denom
            else:
                realized += bb - avg_cost
                if attribute:
                    bucket_pnl[bk] += bb - avg_cost
                if new_pos == 0:
                    avg_cost = 0.0
            pos = new_pos
            trades += 1
            if attribute:
                bucket_trades[bk] += 1

    final_mid = float(mid_arr[-1])
    pnl = realized + pos * final_mid - (pos * avg_cost if pos != 0 else 0.0) if attribute else realized + pos * final_mid
    # Reconcile: original simulator: pnl = realized + pos*final_mid where realized
    # is cash flow style. We'll keep the original formula for total pnl.
    pnl = realized + pos * final_mid - 0.0
    return pnl, trades, bucket_pnl, bucket_trades


def fit_scale_offset(group_path, product_path):
    g = np.asarray(group_path, dtype=float)
    p = np.asarray(product_path, dtype=float)
    G = np.vstack([g, np.ones_like(g)]).T
    coef, *_ = np.linalg.lstsq(G, p, rcond=None)
    return float(coef[0]), float(coef[1])


def build_path(bucket_df, group_path_df, product, train_days, test_day, path_type):
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

    if path_type == "bucket_mean":
        return train_buckets.copy()
    if path_type == "bucket_delta_b0":
        train_d = train.groupby(["day", "bucket"])["mean_mid"].mean().unstack()
        if train_d.shape[1] != 5:
            return train_buckets.copy()
        avg_d = (train_d.values - train_d.values[:, 0:1]).mean(axis=0)
        return test_b0 + avg_d
    group_name = PRODUCT_TO_GROUP[product]
    test_group = group_path_df[
        (group_path_df["group"] == group_name) & (group_path_df["day"] == test_day)
    ]
    if len(test_group) != 5:
        return None
    test_group_path = test_group.sort_values("bucket")["group_path_mean"].values
    if path_type == "group_offset":
        offsets = []
        for d in train_days:
            gp = group_path_df[
                (group_path_df["group"] == group_name) & (group_path_df["day"] == d)
            ].sort_values("bucket")["group_path_mean"].values
            pp = train[train["day"] == d].sort_values("bucket")["mean_mid"].values
            if gp.size == 5 and pp.size == 5:
                offsets.append(pp - gp)
        if offsets:
            return test_group_path + np.mean(offsets, axis=0)
        return train_buckets.copy()
    if path_type == "group_scaled":
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
            return float(np.mean(alphas)) * test_group_path + float(np.mean(betas))
        return train_buckets.copy()
    return None


def shape_only_zero(path_vec, path_type, test_b0, train_buckets):
    """Replace shape with flat zero. The 'anchor' is whatever the path type would
    use as its bucket0 baseline."""
    if path_type == "bucket_delta_b0":
        return np.full(5, test_b0)
    # For all train-built paths we use the train mean of bucket0.
    return np.full(5, float(train_buckets[0]))


def main():
    bucket_df = pd.read_csv(os.path.join(OUT_DIR, "product_bucket_paths.csv"))
    group_path_df = pd.read_csv(os.path.join(OUT_DIR, "group_path_summary.csv"))
    cand_df = pd.read_csv(os.path.join(OUT_DIR, "candidate_products.csv"))
    cand_df = cand_df.sort_values("worst_day_pnl", ascending=False).head(TOP_N)
    print("loaded %d candidates" % len(cand_df), flush=True)

    print("loading raw prices...", flush=True)
    frames = []
    for d in DAYS:
        df = pd.read_csv(os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % d), sep=";")
        df["mid"] = df["mid_price"].astype(float)
        df["best_bid"] = df["bid_price_1"].astype(float)
        df["best_ask"] = df["ask_price_1"].astype(float)
        df["bucket"] = np.minimum(N_BUCKETS - 1, df["timestamp"] * N_BUCKETS // 1_000_000).astype(int)
        frames.append(df[["day", "timestamp", "product", "bucket", "mid", "best_bid", "best_ask"]])
    raw = pd.concat(frames, ignore_index=True).sort_values(["product", "day", "timestamp"]).reset_index(drop=True)

    cache = {}
    for (prod, day), g in raw.groupby(["product", "day"], sort=False):
        cache[(prod, day)] = (
            g["bucket"].to_numpy(),
            g["mid"].to_numpy(dtype=float),
            g["best_bid"].to_numpy(dtype=float),
            g["best_ask"].to_numpy(dtype=float),
            g["timestamp"].to_numpy(),
        )

    folds = [((3, 4), 2), ((2, 4), 3), ((2, 3), 4)]
    null_rows = []
    anchor_rows = []
    bucket_rows = []

    for _, cand in cand_df.iterrows():
        product = cand["product"]
        path_type = cand["best_path_type"]
        thr = int(cand["best_threshold"])
        exit_band = max(20.0, thr / 4.0)
        actual_worst = float(cand["worst_day_pnl"])
        actual_total = float(cand["total_pnl"])

        # ---------- Build per-fold paths (actual) ----------
        per_fold = {}
        per_fold_train_buckets = {}
        for train_days, test_day in folds:
            fair = build_path(bucket_df, group_path_df, product, train_days, test_day, path_type)
            sub_train = bucket_df[(bucket_df["product"] == product) & (bucket_df["day"].isin(train_days))]
            tb = sub_train.groupby("bucket")["mean_mid"].mean().sort_index().values
            per_fold[(train_days, test_day)] = fair
            per_fold_train_buckets[(train_days, test_day)] = tb

        # ---------- Anchor-vs-shape: replace shape with flat-zero ----------
        flat_pnls = []
        for train_days, test_day in folds:
            fair = per_fold[(train_days, test_day)]
            if fair is None:
                continue
            arrs = cache.get((product, test_day))
            if arrs is None:
                continue
            bucket_arr, mid_arr, bid_arr, ask_arr, ts_arr = arrs
            test_b0 = bucket_df[(bucket_df["product"] == product) & (bucket_df["day"] == test_day) & (bucket_df["bucket"] == 0)]["mean_mid"].iloc[0]
            tb = per_fold_train_buckets[(train_days, test_day)]
            flat = shape_only_zero(fair, path_type, test_b0, tb)
            pnl, _, _, _ = simulate_vec(bucket_arr, mid_arr, bid_arr, ask_arr, flat, thr, exit_band)
            flat_pnls.append(pnl)
        flat_total = float(sum(flat_pnls)) if flat_pnls else 0.0
        flat_worst = float(min(flat_pnls)) if flat_pnls else 0.0
        anchor_rows.append({
            "product": product,
            "path_type": path_type,
            "threshold": thr,
            "actual_total_pnl": actual_total,
            "actual_worst_pnl": actual_worst,
            "flat_shape_total_pnl": round(flat_total, 2),
            "flat_shape_worst_pnl": round(flat_worst, 2),
            "shape_explains_pct": round(100.0 * (actual_total - flat_total) / max(abs(actual_total), 1.0), 2),
        })

        # ---------- Per-bucket pnl attribution (actual config) ----------
        agg_bucket_pnl = np.zeros(N_BUCKETS)
        agg_bucket_trades = np.zeros(N_BUCKETS, dtype=int)
        boundary_count = 0
        total_trades_local = 0
        bucket_size = 1_000_000 // N_BUCKETS
        for train_days, test_day in folds:
            fair = per_fold[(train_days, test_day)]
            if fair is None:
                continue
            arrs = cache.get((product, test_day))
            if arrs is None:
                continue
            bucket_arr, mid_arr, bid_arr, ask_arr, ts_arr = arrs
            pnl, trades, bp, bt = simulate_vec(
                bucket_arr, mid_arr, bid_arr, ask_arr, fair, thr, exit_band, attribute=True
            )
            if bp is not None:
                agg_bucket_pnl += bp
                agg_bucket_trades += bt
            # Boundary: a "trade" timestamp's distance to nearest bucket boundary
            # — approximate by ts modulo bucket_size, take min(ts%bs, bs-ts%bs)
            # but we don't track which ticks were trades. Use signal mask as proxy.
            fair_arr_v = fair[bucket_arr]
            is_buy = (ask_arr < fair_arr_v - thr)
            is_sell = (bid_arr > fair_arr_v + thr)
            is_exit = (np.abs(mid_arr - fair_arr_v) <= exit_band)
            mask = is_buy | is_sell | is_exit
            sig_ts = ts_arr[mask]
            mod = sig_ts % bucket_size
            dist = np.minimum(mod, bucket_size - mod)
            boundary_count += int(np.sum(dist <= BOUNDARY_WINDOW))
            total_trades_local += int(mask.sum())
        bucket_rows.append({
            "product": product,
            "path_type": path_type,
            "threshold": thr,
            "bucket0_pnl": round(float(agg_bucket_pnl[0]), 2),
            "bucket1_pnl": round(float(agg_bucket_pnl[1]), 2),
            "bucket2_pnl": round(float(agg_bucket_pnl[2]), 2),
            "bucket3_pnl": round(float(agg_bucket_pnl[3]), 2),
            "bucket4_pnl": round(float(agg_bucket_pnl[4]), 2),
            "bucket0_trades": int(agg_bucket_trades[0]),
            "bucket1_trades": int(agg_bucket_trades[1]),
            "bucket2_trades": int(agg_bucket_trades[2]),
            "bucket3_trades": int(agg_bucket_trades[3]),
            "bucket4_trades": int(agg_bucket_trades[4]),
            "boundary_signal_share": round(boundary_count / max(total_trades_local, 1), 4),
            "total_signal_ticks": total_trades_local,
        })

        # ---------- Null distribution: shuffle bucket assignment for train days ----------
        null_worsts = np.zeros(N_SHUFFLE)
        null_totals = np.zeros(N_SHUFFLE)
        sub = bucket_df[bucket_df["product"] == product]
        for s in range(N_SHUFFLE):
            fold_pnls = []
            for train_days, test_day in folds:
                # shuffle train bucket means
                train = sub[sub["day"].isin(train_days)]
                tb = train.groupby("bucket")["mean_mid"].mean().sort_index().values
                if tb.size != 5:
                    continue
                perm = RNG.permutation(5)
                tb_sh = tb[perm]
                # Also shuffle deltas if path_type is bucket_delta_b0
                if path_type == "bucket_delta_b0":
                    train_d = train.groupby(["day", "bucket"])["mean_mid"].mean().unstack()
                    if train_d.shape[1] != 5:
                        continue
                    avg_d = (train_d.values - train_d.values[:, 0:1]).mean(axis=0)
                    avg_d_sh = avg_d[RNG.permutation(5)]
                    test_b0 = sub[(sub["day"] == test_day) & (sub["bucket"] == 0)]["mean_mid"].iloc[0]
                    fair = test_b0 + avg_d_sh
                elif path_type == "bucket_mean":
                    fair = tb_sh
                else:
                    # group_offset / group_scaled: shuffle the group path target order
                    group_name = PRODUCT_TO_GROUP[product]
                    test_group = group_path_df[
                        (group_path_df["group"] == group_name) & (group_path_df["day"] == test_day)
                    ].sort_values("bucket")["group_path_mean"].values
                    if test_group.size != 5:
                        continue
                    test_group_sh = test_group[RNG.permutation(5)]
                    if path_type == "group_offset":
                        offsets = []
                        for d in train_days:
                            gp = group_path_df[
                                (group_path_df["group"] == group_name) & (group_path_df["day"] == d)
                            ].sort_values("bucket")["group_path_mean"].values
                            pp = train[train["day"] == d].sort_values("bucket")["mean_mid"].values
                            if gp.size == 5 and pp.size == 5:
                                offsets.append(pp - gp)
                        if not offsets:
                            continue
                        fair = test_group_sh + np.mean(offsets, axis=0)
                    else:
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
                        if not alphas:
                            continue
                        fair = float(np.mean(alphas)) * test_group_sh + float(np.mean(betas))
                arrs = cache.get((product, test_day))
                if arrs is None:
                    continue
                bucket_arr, mid_arr, bid_arr, ask_arr, ts_arr = arrs
                pnl, _, _, _ = simulate_vec(bucket_arr, mid_arr, bid_arr, ask_arr, fair, thr, exit_band)
                fold_pnls.append(pnl)
            if fold_pnls:
                null_worsts[s] = min(fold_pnls)
                null_totals[s] = sum(fold_pnls)
            else:
                null_worsts[s] = np.nan
                null_totals[s] = np.nan
        null_worsts = null_worsts[~np.isnan(null_worsts)]
        null_totals = null_totals[~np.isnan(null_totals)]
        p95_worst = float(np.quantile(null_worsts, 0.95)) if null_worsts.size else float("nan")
        p95_total = float(np.quantile(null_totals, 0.95)) if null_totals.size else float("nan")
        p_worst = float(np.mean(null_worsts >= actual_worst)) if null_worsts.size else float("nan")
        p_total = float(np.mean(null_totals >= actual_total)) if null_totals.size else float("nan")
        null_rows.append({
            "product": product,
            "path_type": path_type,
            "threshold": thr,
            "actual_worst": actual_worst,
            "actual_total": actual_total,
            "null_worst_p95": round(p95_worst, 2),
            "null_total_p95": round(p95_total, 2),
            "null_mean_worst": round(float(np.mean(null_worsts)), 2),
            "null_mean_total": round(float(np.mean(null_totals)), 2),
            "p_value_worst": round(p_worst, 4),
            "p_value_total": round(p_total, 4),
            "beats_p95_worst": bool(actual_worst > p95_worst),
        })
        print("done %s thr=%d  null mean_total=%.0f p95_total=%.0f p_total=%.3f  shape_pct=%.1f" % (
            product, thr, np.mean(null_totals), p95_total, p_total,
            anchor_rows[-1]["shape_explains_pct"]
        ), flush=True)

    nd = pd.DataFrame(null_rows).sort_values("actual_total", ascending=False)
    ad = pd.DataFrame(anchor_rows).sort_values("actual_total_pnl", ascending=False)
    bd = pd.DataFrame(bucket_rows).sort_values("product")
    nd.to_csv(os.path.join(OUT_DIR, "phase_d_null.csv"), index=False)
    ad.to_csv(os.path.join(OUT_DIR, "phase_d_anchor_vs_shape.csv"), index=False)
    bd.to_csv(os.path.join(OUT_DIR, "phase_d_bucket_attribution.csv"), index=False)
    print("\n--- null distribution ---")
    print(nd.to_string(index=False))
    print("\n--- anchor vs shape ---")
    print(ad.to_string(index=False))
    print("\n--- per-bucket attribution ---")
    print(bd.to_string(index=False))


if __name__ == "__main__":
    main()
