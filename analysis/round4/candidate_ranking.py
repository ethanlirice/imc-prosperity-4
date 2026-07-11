import sys
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
_scores = HERE / "informed_trader_trade_scores.csv"
_extrema = HERE / "informed_trader_extrema_hits.csv"
if not _scores.is_file() or not _extrema.is_file():
    print(
        "Missing informed_trader_*.csv — run `python notebooks/round4/informed_trader_analysis.py` first.",
        file=sys.stderr,
    )
    sys.exit(1)
scores = pd.read_csv(_scores)
extrema = pd.read_csv(_extrema)

summary_rows = []
for trader, frame in scores.groupby("trader"):
    product_stats = (
        frame.groupby("symbol")
        .agg(
            trades=("good", "count"),
            good_pct=("good", "mean"),
            mean_edge=("signed_edge", "mean"),
            unit_edge=("signed_edge", "sum"),
            qty_edge=("signed_edge", lambda x: (x * frame.loc[x.index, "qty"]).sum()),
            days=("day", "nunique"),
            buys=("side", lambda x: (x == "buy").sum()),
            sells=("side", lambda x: (x == "sell").sum()),
        )
        .reset_index()
    )
    strong = product_stats[(product_stats["trades"] >= 10) & (product_stats["good_pct"] > 0.65)]
    extrema_trader = extrema[extrema["trader"] == trader]
    summary_rows.append(
        {
            "trader": trader,
            "all_trades": len(frame),
            "overall_good_pct": frame["good"].mean(),
            "strong_products": ",".join(strong["symbol"].tolist()),
            "strong_product_count": len(strong),
            "strong_unit_edge": strong["unit_edge"].sum(),
            "strong_qty_edge": strong["qty_edge"].sum(),
            "strong_copy10_edge": strong["unit_edge"].sum() * 10,
            "extrema_hits": len(extrema_trader),
            "buy_at_min_hits": (extrema_trader["side"] == "buy_at_min").sum(),
            "sell_at_max_hits": (extrema_trader["side"] == "sell_at_max").sum(),
            "extrema_products": ",".join(sorted(extrema_trader["symbol"].unique())),
        }
    )

ranking = pd.DataFrame(summary_rows).sort_values(
    ["strong_copy10_edge", "sell_at_max_hits", "buy_at_min_hits"],
    ascending=[False, False, False],
)
print("Trader ranking:")
print(ranking.to_string(index=False))

print("\nStrong product detail:")
detail = (
    scores.groupby(["trader", "symbol"])
    .agg(
        trades=("good", "count"),
        good_pct=("good", "mean"),
        avg_qty=("qty", "mean"),
        unit_edge=("signed_edge", "sum"),
        qty_edge=("signed_edge", lambda x: (x * scores.loc[x.index, "qty"]).sum()),
        mean_edge=("signed_edge", "mean"),
        days=("day", "nunique"),
        buys=("side", lambda x: (x == "buy").sum()),
        sells=("side", lambda x: (x == "sell").sum()),
    )
    .reset_index()
)
detail = detail[(detail["trades"] >= 10) & (detail["good_pct"] > 0.65)]
detail = detail.sort_values(["unit_edge", "good_pct"], ascending=[False, False])
print(detail.to_string(index=False))

for trader in ["Mark 14", "Mark 01", "Mark 67"]:
    frame = scores[scores["trader"] == trader]
    print(f"\nCandidate detail: {trader}")
    print(
        frame.groupby(["symbol", "side"])
        .agg(
            trades=("good", "count"),
            good_pct=("good", "mean"),
            avg_qty=("qty", "mean"),
            unit_edge=("signed_edge", "sum"),
            qty_edge=("signed_edge", lambda x: (x * frame.loc[x.index, "qty"]).sum()),
            days=("day", "nunique"),
        )
        .sort_values(["unit_edge"], ascending=False)
        .to_string()
    )
