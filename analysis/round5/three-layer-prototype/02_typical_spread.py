"""Compute typical bid-ask spread + mid-price quantiles per product, for
MM edge sizing and mean-reversion threshold calibration."""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5/three-layer-prototype")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = [pd.read_csv(p, sep=";") for p in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["bid_price_1", "ask_price_1", "mid_price"])
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    rows = []
    for product, sub in df.groupby("product"):
        spread = sub["spread"].to_numpy(dtype=float)
        mid = sub["mid_price"].to_numpy(dtype=float)
        # 1-step mid change in absolute ticks
        diffs = np.abs(np.diff(mid))
        rows.append(
            {
                "product": product,
                "spread_mean": float(np.mean(spread)),
                "spread_median": float(np.median(spread)),
                "spread_p10": float(np.percentile(spread, 10)),
                "spread_p90": float(np.percentile(spread, 90)),
                "mid_mean": float(np.mean(mid)),
                "mid_std": float(np.std(mid)),
                "abs_diff_mean": float(np.mean(diffs)),
                "abs_diff_p90": float(np.percentile(diffs, 90)),
                "n": int(len(sub)),
            }
        )
    out = pd.DataFrame(rows).sort_values("product")
    out.to_csv(OUT_DIR / "02_typical_spread.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
