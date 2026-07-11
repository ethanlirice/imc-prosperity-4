"""Trade-flow VWAP paths.

For each (product, day, bucket) compute trade VWAP from
trades_round_5_day_*.csv and compare to the quote-mid bucket mean computed in
30_bucket_paths.py. The difference (trade_vwap - quote_mid) per bucket is a
participant-disagreement / direction-of-aggression signal.

Stability of the *trade-mid difference* across days is then a separate path
hypothesis: it asks whether the engine consistently transacted higher or
lower than the quote mid in specific time windows.

Output: analysis/round5/hidden-paths/trade_vwap_paths.csv
        analysis/round5/hidden-paths/trade_vwap_path_stability.csv
"""
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from _common import (  # noqa: E402
    OUT_DIR,
    DATA_DIR,
    ALL_PRODUCTS,
    PRODUCT_TO_GROUP,
    DAYS,
    N_BUCKETS,
)


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return float("nan")
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def load_trades():
    frames = []
    for d in DAYS:
        df = pd.read_csv(os.path.join(DATA_DIR, "trades_round_5_day_%d.csv" % d), sep=";")
        df["day"] = d
        df["bucket"] = np.minimum(N_BUCKETS - 1, df["timestamp"] * N_BUCKETS // 1_000_000).astype(int)
        df = df.rename(columns={"symbol": "product"})
        frames.append(df[["day", "timestamp", "product", "bucket", "price", "quantity"]])
    return pd.concat(frames, ignore_index=True)


def main():
    trades = load_trades()
    print("trades=%d products=%d" % (len(trades), trades["product"].nunique()))

    # Trade VWAP per (product, day, bucket).
    trades["pq"] = trades["price"] * trades["quantity"]
    grp = trades.groupby(["product", "day", "bucket"]).agg(
        n_trades=("price", "size"),
        sum_qty=("quantity", "sum"),
        sum_pq=("pq", "sum"),
        first_ts=("timestamp", "min"),
        last_ts=("timestamp", "max"),
    ).reset_index()
    grp["trade_vwap"] = grp["sum_pq"] / grp["sum_qty"]

    quote = pd.read_csv(os.path.join(OUT_DIR, "product_bucket_paths.csv"))
    quote = quote[["product", "day", "bucket", "mean_mid", "median_mid"]].rename(
        columns={"mean_mid": "quote_mean_mid", "median_mid": "quote_median_mid"}
    )
    merged = grp.merge(quote, on=["product", "day", "bucket"], how="left")
    merged["trade_minus_quote"] = merged["trade_vwap"] - merged["quote_mean_mid"]

    # Save raw VWAP path table.
    out_path = os.path.join(OUT_DIR, "trade_vwap_paths.csv")
    merged_out = merged[
        [
            "product",
            "day",
            "bucket",
            "n_trades",
            "sum_qty",
            "trade_vwap",
            "quote_mean_mid",
            "trade_minus_quote",
        ]
    ].copy()
    for c in ("trade_vwap", "quote_mean_mid", "trade_minus_quote"):
        merged_out[c] = merged_out[c].round(6)
    merged_out.to_csv(out_path, index=False)
    print("wrote %s rows=%d" % (out_path, len(merged_out)))

    # Stability of trade_minus_quote path across days.
    rows = []
    for product in ALL_PRODUCTS:
        sub = merged[merged["product"] == product]
        # Build per-day 5-vector of trade_minus_quote and trade_vwap.
        diff_stack = []
        vwap_stack = []
        for d in DAYS:
            row = sub[sub["day"] == d].sort_values("bucket")
            if len(row) != 5:
                continue
            diff_stack.append(row["trade_minus_quote"].values)
            vwap_stack.append(row["trade_vwap"].values)
        if len(diff_stack) != 3:
            continue
        diff_stack = np.array(diff_stack)
        vwap_stack = np.array(vwap_stack)
        diff_corrs = [pearson(diff_stack[i], diff_stack[j]) for i, j in combinations(range(3), 2)]
        vwap_corrs = [pearson(vwap_stack[i], vwap_stack[j]) for i, j in combinations(range(3), 2)]

        diff_avg = diff_stack.mean(axis=0)
        diff_signs = np.sign(diff_stack)
        diff_avg_signs = np.sign(diff_avg)
        diff_sign_match = (diff_signs == diff_avg_signs[None, :]) & (diff_avg_signs[None, :] != 0)
        diff_all_same_sign = int(
            np.sum(np.all(diff_stack > 0, axis=0) | np.all(diff_stack < 0, axis=0))
        )

        rows.append(
            {
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "diff_cross_day_corr": round(float(np.nanmean(diff_corrs)), 6),
                "vwap_cross_day_corr_after_b0": round(
                    float(
                        np.nanmean(
                            [
                                pearson(
                                    vwap_stack[i] - vwap_stack[i, 0],
                                    vwap_stack[j] - vwap_stack[j, 0],
                                )
                                for i, j in combinations(range(3), 2)
                            ]
                        )
                    ),
                    6,
                ),
                "diff_avg_path": "|".join("%.4f" % v for v in diff_avg.tolist()),
                "diff_max_abs": round(float(np.max(np.abs(diff_avg))), 4),
                "diff_sign_consistency": round(float(diff_sign_match.mean()), 6)
                if diff_sign_match.size
                else float("nan"),
                "diff_all_days_same_sign_buckets": diff_all_same_sign,
                "n_trades_total": int(sub["n_trades"].sum()),
            }
        )

    stab = pd.DataFrame(rows).sort_values("diff_cross_day_corr", ascending=False)
    out_stab = os.path.join(OUT_DIR, "trade_vwap_path_stability.csv")
    stab.to_csv(out_stab, index=False)
    print("wrote %s rows=%d" % (out_stab, len(stab)))
    print()
    print("--- top 12 by trade_minus_quote cross-day corr ---")
    print(stab.head(12).to_string(index=False))
    print()
    print("--- bottom 12 (most NEGATIVE cross-day corr) ---")
    print(stab.tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
