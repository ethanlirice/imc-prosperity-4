from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
HORIZONS = [10, 50, 200, 500, 1000, 2000, 5000]


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_data():
    prices = []
    trades = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        if "day" not in df.columns:
            df["day"] = parse_day(path)
        prices.append(df)
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        df["day"] = parse_day(path)
        trades.append(df)
    if not prices or not trades:
        raise FileNotFoundError(f"Missing Round 4 data in {DATA_DIR}")
    return pd.concat(prices, ignore_index=True), pd.concat(trades, ignore_index=True)


def price_lookup(prices):
    return {
        (int(day), product): frame.sort_values("timestamp").reset_index(drop=True)
        for (day, product), frame in prices.groupby(["day", "product"])
    }


def value(row, name):
    val = row.get(name, np.nan)
    if pd.isna(val):
        return np.nan
    return float(val)


def future_mid(frame, timestamp, horizon):
    ts = frame["timestamp"].to_numpy()
    idx = np.searchsorted(ts, timestamp + horizon, side="left")
    if idx >= len(frame):
        return np.nan
    return float(frame.iloc[idx]["mid_price"])


def expand_events(trades, prices_by_key):
    rows = []
    price_exact = prices.set_index(["day", "product", "timestamp"])

    for _, trade in trades.iterrows():
        day = int(trade["day"])
        product = trade["symbol"]
        timestamp = int(trade["timestamp"])
        price = float(trade["price"])
        qty = int(trade["quantity"])

        try:
            book = price_exact.loc[(day, product, timestamp)]
        except KeyError:
            continue

        frame = prices_by_key.get((day, product))
        if frame is None:
            continue

        bid = value(book, "bid_price_1")
        ask = value(book, "ask_price_1")
        mid = value(book, "mid_price")
        spread = ask - bid if not pd.isna(bid) and not pd.isna(ask) else np.nan

        sides = [
            ("buy", trade["buyer"], trade["seller"], 1),
            ("sell", trade["seller"], trade["buyer"], -1),
        ]
        for side, trader, counterparty, direction in sides:
            if pd.isna(trader) or trader == "":
                continue

            row = {
                "day": day,
                "timestamp": timestamp,
                "trader": trader,
                "counterparty": counterparty,
                "product": product,
                "side": side,
                "direction": direction,
                "price": price,
                "qty": qty,
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "spread": spread,
                "signed_price_vs_mid": direction * (price - mid)
                if not pd.isna(mid)
                else np.nan,
                "touch_distance": price - ask
                if side == "buy" and not pd.isna(ask)
                else bid - price
                if side == "sell" and not pd.isna(bid)
                else np.nan,
                "at_or_through_touch": price >= ask
                if side == "buy" and not pd.isna(ask)
                else price <= bid
                if side == "sell" and not pd.isna(bid)
                else False,
                "inside_spread": bid < price < ask
                if not pd.isna(bid) and not pd.isna(ask)
                else False,
            }
            for horizon in HORIZONS:
                fmid = future_mid(frame, timestamp, horizon)
                row[f"future_mid_{horizon}"] = fmid
                row[f"edge_{horizon}"] = direction * (fmid - price)
                row[f"mid_move_{horizon}"] = direction * (fmid - mid)
            rows.append(row)

    return pd.DataFrame(rows)


def summarize(events):
    agg = {}
    for horizon in HORIZONS:
        agg[f"edge_mean_{horizon}"] = (f"edge_{horizon}", "mean")
        agg[f"edge_sum_{horizon}"] = (f"edge_{horizon}", "sum")
        agg[f"qty_edge_sum_{horizon}"] = (
            f"edge_{horizon}",
            lambda x, h=horizon: (x * events.loc[x.index, "qty"]).sum(),
        )
        agg[f"good_pct_{horizon}"] = (f"edge_{horizon}", lambda x: (x > 0).mean())
        agg[f"mid_move_mean_{horizon}"] = (f"mid_move_{horizon}", "mean")

    by_day = (
        events.groupby(["trader", "product", "side", "day"])
        .agg(
            events=("qty", "count"),
            total_qty=("qty", "sum"),
            avg_qty=("qty", "mean"),
            median_qty=("qty", "median"),
            mean_spread=("spread", "mean"),
            mean_signed_price_vs_mid=("signed_price_vs_mid", "mean"),
            touch_pct=("at_or_through_touch", "mean"),
            inside_pct=("inside_spread", "mean"),
            **agg,
        )
        .reset_index()
    )

    by_product = (
        events.groupby(["trader", "product", "side"])
        .agg(
            events=("qty", "count"),
            days=("day", "nunique"),
            total_qty=("qty", "sum"),
            avg_qty=("qty", "mean"),
            median_qty=("qty", "median"),
            mean_spread=("spread", "mean"),
            mean_signed_price_vs_mid=("signed_price_vs_mid", "mean"),
            touch_pct=("at_or_through_touch", "mean"),
            inside_pct=("inside_spread", "mean"),
            **agg,
        )
        .reset_index()
    )

    trader = (
        events.groupby("trader")
        .agg(
            events=("qty", "count"),
            products=("product", "nunique"),
            days=("day", "nunique"),
            buys=("side", lambda x: (x == "buy").sum()),
            sells=("side", lambda x: (x == "sell").sum()),
            total_qty=("qty", "sum"),
            avg_qty=("qty", "mean"),
            mean_edge_200=("edge_200", "mean"),
            good_pct_200=("edge_200", lambda x: (x > 0).mean()),
            qty_edge_200=("edge_200", lambda x: (x * events.loc[x.index, "qty"]).sum()),
            mean_mid_move_200=("mid_move_200", "mean"),
        )
        .reset_index()
        .sort_values("qty_edge_200", ascending=False)
    )

    pairs = (
        events.groupby(["trader", "counterparty", "product", "side"])
        .agg(
            events=("qty", "count"),
            avg_qty=("qty", "mean"),
            edge_mean_200=("edge_200", "mean"),
            good_pct_200=("edge_200", lambda x: (x > 0).mean()),
        )
        .reset_index()
        .sort_values(["trader", "events"], ascending=[True, False])
    )

    return by_day, by_product, trader, pairs


def timing(events):
    rows = []
    top_gap_rows = []
    for (trader, product, side, day), frame in events.groupby(
        ["trader", "product", "side", "day"]
    ):
        ordered = frame.sort_values("timestamp")
        gaps = ordered["timestamp"].diff().dropna()
        if len(gaps) == 0:
            continue
        rows.append(
            {
                "trader": trader,
                "product": product,
                "side": side,
                "day": day,
                "events": len(ordered),
                "mean_gap": gaps.mean(),
                "median_gap": gaps.median(),
                "min_gap": gaps.min(),
                "max_gap": gaps.max(),
                "std_gap": gaps.std(),
                "pct_gap_le_500": (gaps <= 500).mean(),
                "pct_gap_le_1000": (gaps <= 1000).mean(),
                "pct_gap_le_5000": (gaps <= 5000).mean(),
            }
        )
        vc = gaps.value_counts().head(5)
        for gap, count in vc.items():
            top_gap_rows.append(
                {
                    "trader": trader,
                    "product": product,
                    "side": side,
                    "day": day,
                    "gap": int(gap),
                    "count": int(count),
                    "share": float(count / len(gaps)),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(top_gap_rows)


def recurrence(events):
    keys = (
        events.groupby(["trader", "product", "side", "timestamp"])
        .agg(days=("day", "nunique"), events=("day", "count"))
        .reset_index()
    )
    return (
        keys.groupby(["trader", "product", "side"])
        .agg(
            unique_timestamp_side=("timestamp", "count"),
            repeated_2plus_days=("days", lambda x: (x >= 2).sum()),
            repeated_3_days=("days", lambda x: (x >= 3).sum()),
        )
        .reset_index()
        .sort_values(["trader", "repeated_2plus_days"], ascending=[True, False])
    )


def write_mark_reports(events, by_product, by_day, gap_summary, recur):
    for trader in sorted(events["trader"].unique()):
        slug = trader.lower().replace(" ", "_")
        path = OUT_DIR / f"{slug}_local.md"
        ef = events[events["trader"] == trader]
        bp = by_product[by_product["trader"] == trader].sort_values(
            ["qty_edge_sum_200", "events"], ascending=[False, False]
        )
        bd = by_day[by_day["trader"] == trader].sort_values(
            ["product", "side", "day"]
        )
        gs = gap_summary[gap_summary["trader"] == trader].sort_values(
            ["product", "side", "day"]
        )
        rc = recur[recur["trader"] == trader].sort_values(
            ["repeated_2plus_days", "unique_timestamp_side"],
            ascending=[False, False],
        )
        with path.open("w") as fh:
            print(f"# {trader} Local Taxonomy", file=fh)
            print("", file=fh)
            print(
                f"Events: {len(ef)}; products: {ef['product'].nunique()}; "
                f"days: {ef['day'].nunique()}; buys: {(ef['side'] == 'buy').sum()}; "
                f"sells: {(ef['side'] == 'sell').sum()}.",
                file=fh,
            )
            print("", file=fh)
            print("## Product/Side Summary", file=fh)
            cols = [
                "product",
                "side",
                "events",
                "days",
                "avg_qty",
                "touch_pct",
                "mean_signed_price_vs_mid",
                "edge_mean_50",
                "edge_mean_200",
                "edge_mean_500",
                "good_pct_200",
                "qty_edge_sum_200",
            ]
            print(bp[cols].to_string(index=False), file=fh)
            print("", file=fh)
            print("## Day Split", file=fh)
            dcols = [
                "product",
                "side",
                "day",
                "events",
                "avg_qty",
                "edge_mean_200",
                "good_pct_200",
                "qty_edge_sum_200",
            ]
            print(bd[dcols].to_string(index=False), file=fh)
            print("", file=fh)
            print("## Timing Gaps", file=fh)
            if len(gs) == 0:
                print("No repeated same product/side/day events.", file=fh)
            else:
                gcols = [
                    "product",
                    "side",
                    "day",
                    "events",
                    "median_gap",
                    "pct_gap_le_1000",
                    "pct_gap_le_5000",
                ]
                print(gs[gcols].to_string(index=False), file=fh)
            print("", file=fh)
            print("## Timestamp Recurrence Across Days", file=fh)
            rcols = [
                "product",
                "side",
                "unique_timestamp_side",
                "repeated_2plus_days",
                "repeated_3_days",
            ]
            print(rc[rcols].head(30).to_string(index=False), file=fh)


def write_overall(events, by_product, trader, gap_summary, recur):
    out = OUT_DIR / "all_marks_local_summary.md"
    with out.open("w") as fh:
        print("# Round 4 Mark Taxonomy Local Summary", file=fh)
        print("", file=fh)
        print("## Trader Ranking by t+200 Trade-Price Edge", file=fh)
        print(trader.to_string(index=False), file=fh)
        print("", file=fh)
        print("## Top Positive Product/Side Edges", file=fh)
        pos = by_product[by_product["events"] >= 10].sort_values(
            ["qty_edge_sum_200", "edge_mean_200"], ascending=[False, False]
        )
        cols = [
            "trader",
            "product",
            "side",
            "events",
            "days",
            "avg_qty",
            "edge_mean_200",
            "good_pct_200",
            "qty_edge_sum_200",
        ]
        print(pos[cols].head(40).to_string(index=False), file=fh)
        print("", file=fh)
        print("## Top Negative Product/Side Edges", file=fh)
        neg = by_product[by_product["events"] >= 10].sort_values(
            ["qty_edge_sum_200", "edge_mean_200"], ascending=[True, True]
        )
        print(neg[cols].head(40).to_string(index=False), file=fh)
        print("", file=fh)
        print("## Most Recurrent Timestamp Patterns", file=fh)
        print(
            recur.sort_values(
                ["repeated_2plus_days", "repeated_3_days"],
                ascending=[False, False],
            )
            .head(40)
            .to_string(index=False),
            file=fh,
        )
        print("", file=fh)
        print("## Tightest Timing Patterns", file=fh)
        tight = gap_summary[gap_summary["events"] >= 10].sort_values(
            ["pct_gap_le_1000", "median_gap"], ascending=[False, True]
        )
        print(tight.head(40).to_string(index=False), file=fh)
    return out


def main():
    global prices
    prices, trades = load_data()
    prices_by_key = price_lookup(prices)
    events = expand_events(trades, prices_by_key)
    by_day, by_product, trader, pairs = summarize(events)
    gap_summary, top_gaps = timing(events)
    recur = recurrence(events)

    events.to_csv(OUT_DIR / "all_mark_events.csv", index=False)
    by_day.to_csv(OUT_DIR / "all_mark_product_side_day.csv", index=False)
    by_product.to_csv(OUT_DIR / "all_mark_product_side.csv", index=False)
    trader.to_csv(OUT_DIR / "all_mark_trader_summary.csv", index=False)
    pairs.to_csv(OUT_DIR / "all_mark_counterparty_pairs.csv", index=False)
    gap_summary.to_csv(OUT_DIR / "all_mark_timing_gaps.csv", index=False)
    top_gaps.to_csv(OUT_DIR / "all_mark_top_gaps.csv", index=False)
    recur.to_csv(OUT_DIR / "all_mark_timestamp_recurrence.csv", index=False)

    write_mark_reports(events, by_product, by_day, gap_summary, recur)
    report = write_overall(events, by_product, trader, gap_summary, recur)
    print(f"Wrote {report}")
    print(f"Events: {len(events)}")


if __name__ == "__main__":
    main()
