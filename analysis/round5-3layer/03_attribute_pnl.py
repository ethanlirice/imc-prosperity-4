"""
Phase 3: per-day PnL attribution by layer (MM/MR/stat-arb).

The backtester resets positions and PnL between days even in --merge-pnl mode,
so we accumulate per (day, product, layer) cash + position and mark to that
day's final mid. Total PnL = sum across (day, product, layer).

Trade classification:
- product in stat-arb pairs           -> stat
- otherwise:
    SUBMISSION buyer paid >= best_ask -> mr (aggressive take)
    SUBMISSION seller got <= best_bid -> mr (aggressive take)
    else (passive fill at quote)      -> mm
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("backtests/2026-04-28_21-35-41.log")
OUT = Path("analysis/round5-3layer/03_attribute_pnl.md")

PAIRS = [
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_PISTACHIO"),
    ("OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"),
    ("SNACKPACK_PISTACHIO", "SNACKPACK_RASPBERRY"),
]
STAT_ARB_PRODUCTS = {p for pair in PAIRS for p in pair}

DAY_OFFSETS = {2: 0, 3: 1_000_000, 4: 2_000_000}


def main() -> None:
    with LOG.open() as f:
        j = json.load(f)

    book: dict = {}
    final_mid: dict = {}
    final_pnl_by_day: dict = defaultdict(dict)
    for line in j["activitiesLog"].split("\n"):
        if not line or line.startswith("day;"):
            continue
        parts = line.split(";")
        day = int(parts[0])
        ts = int(parts[1])  # already merged
        product = parts[2]
        bid1 = float(parts[3]) if parts[3] else None
        ask1 = float(parts[9]) if parts[9] else None
        mid = float(parts[15]) if parts[15] else None
        pnl_row = float(parts[16]) if parts[16] else 0.0
        book[(ts, product)] = (day, bid1, ask1, mid)
        if mid is not None:
            final_mid[(day, product)] = mid
        final_pnl_by_day[(day, product)] = pnl_row

    # Per-day per-product per-layer cash and position.
    cash = defaultdict(float)  # (day, product, layer) -> cash
    pos = defaultdict(int)  # (day, product, layer) -> end-of-day position
    trades_count = defaultdict(int)  # (day, product, layer) -> trades

    for tr in j["tradeHistory"]:
        if tr["buyer"] != "SUBMISSION" and tr["seller"] != "SUBMISSION":
            continue
        ts = int(tr["timestamp"])
        product = tr["symbol"]
        price = float(tr["price"])
        qty = int(tr["quantity"])
        is_buy = tr["buyer"] == "SUBMISSION"

        info = book.get((ts, product))
        if info is None:
            continue
        day, bid, ask, _mid = info
        if product in STAT_ARB_PRODUCTS:
            layer = "stat"
        else:
            if is_buy and ask is not None and price >= ask:
                layer = "mr"
            elif (not is_buy) and bid is not None and price <= bid:
                layer = "mr"
            else:
                layer = "mm"

        cash_delta = -price * qty if is_buy else price * qty
        cash[(day, product, layer)] += cash_delta
        pos[(day, product, layer)] += (qty if is_buy else -qty)
        trades_count[(day, product, layer)] += 1

    # Mark each (day, product, layer) at that day's final mid.
    rows = []
    for key, c in cash.items():
        day, product, layer = key
        end_pos = pos[key]
        mid = final_mid.get((day, product))
        mark = mid * end_pos if mid is not None else 0.0
        rows.append(
            {
                "day": day,
                "product": product,
                "layer": layer,
                "cash": c,
                "end_pos": end_pos,
                "mark": mark,
                "pnl": c + mark,
                "trades": trades_count[key],
            }
        )
    df = pd.DataFrame(rows)

    # Layer totals across all days.
    layer_totals = df.groupby("layer")["pnl"].sum().to_dict()
    grand_total = float(df["pnl"].sum())

    # Per-product totals across all days, with layer breakdown columns.
    prod_layer = df.groupby(["product", "layer"])["pnl"].sum().unstack(fill_value=0.0)
    prod_layer["total"] = prod_layer.sum(axis=1)
    prod_layer = prod_layer.sort_values("total")

    # Per pair: sum of both legs' total across all layers.
    pair_rows = []
    for a, b in PAIRS:
        ta = float(prod_layer.loc[a, "total"]) if a in prod_layer.index else 0.0
        tb = float(prod_layer.loc[b, "total"]) if b in prod_layer.index else 0.0
        pair_rows.append({"pair": f"{a} / {b}", "leg_a_pnl": ta, "leg_b_pnl": tb, "pair_total": ta + tb})

    # Per-day totals (sanity check vs backtester output).
    per_day = df.groupby("day")["pnl"].sum().to_dict()

    md = ["# Phase 3 — v1 PnL attribution", "", f"Log: `{LOG}`", ""]
    md.append("## Layer totals (all days)\n")
    for k, v in sorted(layer_totals.items(), key=lambda x: x[1], reverse=True):
        md.append(f"- **{k}**: {v:,.0f}")
    md.append(f"- **grand total**: {grand_total:,.0f}")
    md.append("")
    md.append("## Per-day totals (sanity-check vs backtester)")
    for d in sorted(per_day):
        md.append(f"- day {d}: {per_day[d]:,.0f}")
    md.append("")
    md.append("## Per pair (legs aggregated, includes other layers if leg is shared)")
    md.append("")
    md.append(pd.DataFrame(pair_rows).round(0).to_markdown(index=False))
    md.append("")
    md.append("## Per product (sorted by total PnL ascending)")
    md.append("")
    md.append(prod_layer.round(0).to_markdown())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(md))
    print("\n".join(md[:25]))
    print("...")
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
