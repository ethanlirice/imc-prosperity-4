from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
TRADER = "Mark 14"
HORIZONS = [10, 50, 200, 500]
PRE_OFFSETS = [100, 200, 500, 1000, 2000, 5000]


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_prices():
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        frames.append(df)
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    prices["best_bid_depth"] = prices["bid_volume_1"].fillna(0)
    prices["best_ask_depth"] = -prices["ask_volume_1"].fillna(0)
    bid_cols = [c for c in prices.columns if c.startswith("bid_volume_")]
    ask_cols = [c for c in prices.columns if c.startswith("ask_volume_")]
    prices["bid_depth_3"] = prices[bid_cols].fillna(0).sum(axis=1)
    prices["ask_depth_3"] = -prices[ask_cols].fillna(0).sum(axis=1)
    return prices


def load_trades():
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        day = parse_day(path)
        if "day" not in df.columns:
            df["day"] = day
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def first_mid_at_or_after(price_lookup, day, product, ts):
    frame = price_lookup[(day, product)]
    times = frame["timestamp"].to_numpy()
    idx = np.searchsorted(times, ts, side="left")
    if idx >= len(frame):
        return np.nan
    return float(frame["mid_price"].iloc[idx])


def first_row_after(price_lookup, day, product, ts):
    frame = price_lookup[(day, product)]
    times = frame["timestamp"].to_numpy()
    idx = np.searchsorted(times, ts, side="right")
    if idx >= len(frame):
        return None
    return frame.iloc[idx]


def row_at_or_after(price_lookup, day, product, ts):
    frame = price_lookup[(day, product)]
    times = frame["timestamp"].to_numpy()
    idx = np.searchsorted(times, ts, side="left")
    if idx >= len(frame):
        return None
    return frame.iloc[idx]


def side_markout(side, future_mid, price):
    if pd.isna(future_mid):
        return np.nan
    if side == "buy":
        return float(future_mid) - float(price)
    return float(price) - float(future_mid)


def side_mid_markout(side, future_mid, current_mid):
    if pd.isna(future_mid) or pd.isna(current_mid):
        return np.nan
    if side == "buy":
        return float(future_mid) - float(current_mid)
    return float(current_mid) - float(future_mid)


def qtile(x, q):
    if len(x) == 0:
        return np.nan
    return float(np.nanquantile(x, q))


def fmt_num(x, digits=3):
    if pd.isna(x):
        return ""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.{digits}f}"


def to_md_table(df, cols, max_rows=None, digits=3):
    if max_rows is not None:
        df = df.head(max_rows)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float) or isinstance(val, np.floating):
                vals.append(fmt_num(float(val), digits))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def build_events(trades, prices, price_lookup):
    mark = trades[(trades["buyer"] == TRADER) | (trades["seller"] == TRADER)].copy()
    mark["side"] = np.where(mark["buyer"] == TRADER, "buy", "sell")
    mark["counterparty"] = np.where(mark["buyer"] == TRADER, mark["seller"], mark["buyer"])

    book_cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "ask_price_1",
        "ask_volume_1",
        "mid_price",
        "spread",
        "best_bid_depth",
        "best_ask_depth",
        "bid_depth_3",
        "ask_depth_3",
    ]
    book = prices[book_cols].rename(columns={"product": "symbol"})
    mark = mark.merge(book, on=["day", "timestamp", "symbol"], how="left")

    for horizon in HORIZONS:
        future = []
        for row in mark.itertuples(index=False):
            future.append(
                first_mid_at_or_after(
                    price_lookup,
                    int(row.day),
                    row.symbol,
                    int(row.timestamp) + horizon,
                )
            )
        mark[f"future_mid_t{horizon}"] = future
        mark[f"edge_t{horizon}"] = [
            side_markout(s, f, p)
            for s, f, p in zip(mark["side"], mark[f"future_mid_t{horizon}"], mark["price"])
        ]
        mark[f"midmo_t{horizon}"] = [
            side_mid_markout(s, f, m)
            for s, f, m in zip(mark["side"], mark[f"future_mid_t{horizon}"], mark["mid_price"])
        ]

    price_loc = []
    touch_improve = []
    mid_edge = []
    for row in mark.itertuples(index=False):
        price = float(row.price)
        bid = float(row.bid_price_1)
        ask = float(row.ask_price_1)
        mid = float(row.mid_price)
        if price == bid:
            loc = "at_bid"
        elif price == ask:
            loc = "at_ask"
        elif bid < price < ask:
            loc = "inside"
        elif price < bid:
            loc = "below_bid"
        elif price > ask:
            loc = "above_ask"
        else:
            loc = "unknown"
        price_loc.append(loc)
        if row.side == "buy":
            touch_improve.append(ask - price)
            mid_edge.append(mid - price)
        else:
            touch_improve.append(price - bid)
            mid_edge.append(price - mid)
    mark["price_location"] = price_loc
    mark["side_touch_improve"] = touch_improve
    mark["side_mid_edge"] = mid_edge

    # Day/product spread percentile for the book state at each event.
    spread_pctile = []
    spread_arrays = {
        key: np.sort(frame["spread"].dropna().to_numpy())
        for key, frame in prices.groupby(["day", "product"])
    }
    for row in mark.itertuples(index=False):
        arr = spread_arrays[(int(row.day), row.symbol)]
        spread_pctile.append(np.searchsorted(arr, row.spread, side="right") / len(arr))
    mark["spread_pctile_day_product"] = spread_pctile
    return mark


def summarize_events(mark):
    agg = {
        "timestamp": "count",
        "quantity": ["sum", "mean", "median"],
        "edge_t10": ["mean", "sum"],
        "edge_t50": ["mean", "sum"],
        "edge_t200": ["mean", "sum"],
        "edge_t500": ["mean", "sum"],
        "midmo_t200": "mean",
    }
    day = mark.groupby(["symbol", "side", "day"]).agg(agg)
    day.columns = [
        "n",
        "qty_sum",
        "qty_mean",
        "qty_median",
        "edge_t10_mean",
        "edge_t10_sum",
        "edge_t50_mean",
        "edge_t50_sum",
        "edge_t200_mean",
        "edge_t200_sum",
        "edge_t500_mean",
        "edge_t500_sum",
        "midmo_t200_mean",
    ]
    day = day.reset_index().sort_values(["symbol", "side", "day"])

    overall = mark.groupby(["symbol", "side"]).agg(agg)
    overall.columns = day.columns[3:].tolist()
    overall = overall.reset_index().sort_values(["edge_t200_sum"], ascending=False)
    return day, overall


def summarize_book(mark, prices):
    loc_pivot = (
        pd.crosstab([mark["symbol"], mark["side"]], mark["price_location"], normalize="index")
        .reset_index()
    )
    for col in ["at_bid", "at_ask", "inside", "below_bid", "above_ask"]:
        if col not in loc_pivot.columns:
            loc_pivot[col] = 0.0
    base = (
        mark.groupby(["symbol", "side"])
        .agg(
            n=("timestamp", "count"),
            spread_mean=("spread", "mean"),
            spread_p50=("spread", "median"),
            spread_pctile_mean=("spread_pctile_day_product", "mean"),
            best_bid_depth_mean=("best_bid_depth", "mean"),
            best_ask_depth_mean=("best_ask_depth", "mean"),
            side_touch_improve_mean=("side_touch_improve", "mean"),
            side_mid_edge_mean=("side_mid_edge", "mean"),
        )
        .reset_index()
    )
    out = base.merge(loc_pivot, on=["symbol", "side"], how="left")

    product_spread = (
        prices.groupby("product")
        .agg(all_spread_mean=("spread", "mean"), all_spread_p50=("spread", "median"))
        .reset_index()
        .rename(columns={"product": "symbol"})
    )
    return out.merge(product_spread, on="symbol", how="left")


def summarize_sizes(mark):
    rows = []
    for (symbol, side), frame in mark.groupby(["symbol", "side"]):
        counts = frame["quantity"].value_counts().sort_values(ascending=False)
        rows.append(
            {
                "symbol": symbol,
                "side": side,
                "n": len(frame),
                "qty_mean": frame["quantity"].mean(),
                "qty_p50": frame["quantity"].median(),
                "qty_p90": frame["quantity"].quantile(0.9),
                "qty_min": frame["quantity"].min(),
                "qty_max": frame["quantity"].max(),
                "top_sizes": ", ".join(f"{int(k)}x{int(v)}" for k, v in counts.head(5).items()),
            }
        )
    return pd.DataFrame(rows).sort_values(["symbol", "side"])


def summarize_timing(mark):
    rows = []
    for keys, frame in mark.sort_values("timestamp").groupby(["symbol", "side", "day"]):
        gaps = frame["timestamp"].sort_values().diff().dropna()
        rows.append(
            {
                "symbol": keys[0],
                "side": keys[1],
                "day": keys[2],
                "n": len(frame),
                "first_ts": int(frame["timestamp"].min()),
                "last_ts": int(frame["timestamp"].max()),
                "gap_mean": gaps.mean() if len(gaps) else np.nan,
                "gap_p50": gaps.median() if len(gaps) else np.nan,
                "gap_p10": qtile(gaps, 0.1),
                "gap_p90": qtile(gaps, 0.9),
                "gap_min": gaps.min() if len(gaps) else np.nan,
                "gap_max": gaps.max() if len(gaps) else np.nan,
            }
        )
    timing = pd.DataFrame(rows).sort_values(["symbol", "side", "day"])

    mod_rows = []
    for symbol, frame in mark.groupby("symbol"):
        for mod in [1000, 5000, 10000]:
            counts = (frame["timestamp"] % mod).value_counts().sort_values(ascending=False)
            top = ", ".join(f"{int(k)}:{int(v)}" for k, v in counts.head(5).items())
            mod_rows.append({"symbol": symbol, "mod": mod, "top_buckets": top})
    mods = pd.DataFrame(mod_rows)
    return timing, mods


def summarize_repeats(mark):
    rows = []
    for keys, frame in mark.groupby(["symbol", "side"]):
        key_counts = frame.groupby("timestamp")["day"].nunique()
        rows.append(
            {
                "symbol": keys[0],
                "side": keys[1],
                "unique_timestamp_keys": len(key_counts),
                "repeated_2plus_days": int((key_counts >= 2).sum()),
                "repeated_3_days": int((key_counts >= 3).sum()),
            }
        )
    cross_day = pd.DataFrame(rows).sort_values(["symbol", "side"])

    dup = (
        mark.groupby(["day", "timestamp"])
        .agg(
            mark14_events=("symbol", "count"),
            products=("symbol", lambda x: ",".join(sorted(set(x)))),
            sides=("side", lambda x: ",".join(sorted(set(x)))),
        )
        .reset_index()
    )
    dup = dup[dup["mark14_events"] > 1].sort_values(["mark14_events", "day", "timestamp"], ascending=[False, True, True])
    return cross_day, dup


def summarize_counterparties(mark, trades):
    cp = (
        mark.groupby(["symbol", "side", "counterparty"])
        .agg(
            n=("timestamp", "count"),
            qty_sum=("quantity", "sum"),
            edge_t200_mean=("edge_t200", "mean"),
            edge_t200_sum=("edge_t200", "sum"),
        )
        .reset_index()
        .sort_values(["edge_t200_sum"], ascending=False)
    )

    other_rows = []
    trade_groups = {
        key: frame
        for key, frame in trades.groupby(["day", "timestamp"])
    }
    for row in mark.itertuples(index=False):
        same_ts = trade_groups[(int(row.day), int(row.timestamp))]
        other = same_ts[
            (same_ts["buyer"] != TRADER) & (same_ts["seller"] != TRADER)
        ]
        same_product_other = other[other["symbol"] == row.symbol]
        participants = sorted(set(other["buyer"]).union(set(other["seller"])))
        participants = [p for p in participants if pd.notna(p)]
        other_rows.append(
            {
                "day": row.day,
                "timestamp": row.timestamp,
                "symbol": row.symbol,
                "side": row.side,
                "other_trades_same_ts": len(other),
                "other_same_product_same_ts": len(same_product_other),
                "other_participants": ",".join(participants),
            }
        )
    co = pd.DataFrame(other_rows)
    co_summary = (
        co.groupby(["symbol", "side"])
        .agg(
            n=("timestamp", "count"),
            pct_any_other_same_ts=("other_trades_same_ts", lambda x: (x > 0).mean()),
            mean_other_trades_same_ts=("other_trades_same_ts", "mean"),
            pct_same_product_other=("other_same_product_same_ts", lambda x: (x > 0).mean()),
        )
        .reset_index()
    )
    return cp, co_summary


def summarize_executable(mark, price_lookup):
    rows = []
    for row in mark.itertuples(index=False):
        entry = first_row_after(price_lookup, int(row.day), row.symbol, int(row.timestamp))
        if entry is None:
            continue
        future = first_mid_at_or_after(
            price_lookup,
            int(row.day),
            row.symbol,
            int(entry.timestamp) + 200,
        )
        if pd.isna(future):
            continue
        if row.side == "buy":
            entry_px = float(entry.ask_price_1)
            executable_edge = future - entry_px
            slippage = entry_px - float(row.price)
        else:
            entry_px = float(entry.bid_price_1)
            executable_edge = entry_px - future
            slippage = float(row.price) - entry_px
        rows.append(
            {
                "symbol": row.symbol,
                "side": row.side,
                "day": int(row.day),
                "timestamp": int(row.timestamp),
                "qty": int(row.quantity),
                "entry_ts": int(entry.timestamp),
                "historical_edge_t200": float(row.edge_t200),
                "executable_edge_t200": executable_edge,
                "slippage": slippage,
            }
        )
    exec_df = pd.DataFrame(rows)
    summary = (
        exec_df.groupby(["symbol", "side"])
        .agg(
            n=("timestamp", "count"),
            historical_mean=("historical_edge_t200", "mean"),
            executable_mean=("executable_edge_t200", "mean"),
            executable_sum=("executable_edge_t200", "sum"),
            mean_slippage=("slippage", "mean"),
        )
        .reset_index()
        .sort_values("executable_sum", ascending=False)
    )
    return exec_df, summary


def summarize_pre_event(mark, trades, price_lookup):
    rows = []
    for row in mark.itertuples(index=False):
        for offset in PRE_OFFSETS:
            entry = row_at_or_after(price_lookup, int(row.day), row.symbol, int(row.timestamp) - offset)
            future = first_mid_at_or_after(
                price_lookup,
                int(row.day),
                row.symbol,
                int(row.timestamp) + 200,
            )
            if entry is None or pd.isna(future):
                continue
            if row.side == "buy":
                cross_px = float(entry.ask_price_1)
                cross_edge = future - cross_px
                passive_px = float(entry.bid_price_1) + 1
                fill_trades = trades[
                    (trades["day"] == int(row.day))
                    & (trades["symbol"] == row.symbol)
                    & (trades["timestamp"] >= int(entry.timestamp))
                    & (trades["timestamp"] <= int(row.timestamp))
                    & (trades["price"] <= passive_px)
                ]
                passive_edge = future - passive_px
            else:
                cross_px = float(entry.bid_price_1)
                cross_edge = cross_px - future
                passive_px = float(entry.ask_price_1) - 1
                fill_trades = trades[
                    (trades["day"] == int(row.day))
                    & (trades["symbol"] == row.symbol)
                    & (trades["timestamp"] >= int(entry.timestamp))
                    & (trades["timestamp"] <= int(row.timestamp))
                    & (trades["price"] >= passive_px)
                ]
                passive_edge = passive_px - future
            rows.append(
                {
                    "symbol": row.symbol,
                    "side": row.side,
                    "day": int(row.day),
                    "offset": offset,
                    "cross_edge": cross_edge,
                    "passive_fill": len(fill_trades) > 0,
                    "passive_edge_if_filled": passive_edge if len(fill_trades) > 0 else np.nan,
                    "passive_edge_per_event": passive_edge if len(fill_trades) > 0 else 0.0,
                }
            )
    pre = pd.DataFrame(rows)
    summary = (
        pre.groupby(["symbol", "offset"])
        .agg(
            n=("cross_edge", "count"),
            cross_mean=("cross_edge", "mean"),
            passive_fill_rate=("passive_fill", "mean"),
            passive_mean_if_filled=("passive_edge_if_filled", "mean"),
            passive_edge_per_event=("passive_edge_per_event", "mean"),
        )
        .reset_index()
        .sort_values(["symbol", "offset"])
    )
    return summary


def write_outputs():
    prices = load_prices()
    trades = load_trades()
    price_lookup = {
        key: frame.sort_values("timestamp").reset_index(drop=True)
        for key, frame in prices.groupby(["day", "product"])
    }
    mark = build_events(trades, prices, price_lookup)

    product_day, product_summary = summarize_events(mark)
    book = summarize_book(mark, prices)
    sizes = summarize_sizes(mark)
    timing, mods = summarize_timing(mark)
    repeats, duplicate_ts = summarize_repeats(mark)
    cp, co = summarize_counterparties(mark, trades)
    exec_df, exec_summary = summarize_executable(mark, price_lookup)
    pre_summary = summarize_pre_event(mark, trades, price_lookup)

    outputs = {
        "mark_14_events.csv": mark,
        "mark_14_product_side_day_markouts.csv": product_day,
        "mark_14_product_side_summary.csv": product_summary,
        "mark_14_book_relation.csv": book,
        "mark_14_size_distribution.csv": sizes,
        "mark_14_timing_gaps.csv": timing,
        "mark_14_timing_modulo.csv": mods,
        "mark_14_repeat_timestamps.csv": repeats,
        "mark_14_duplicate_timestamps.csv": duplicate_ts,
        "mark_14_counterparties.csv": cp,
        "mark_14_cooccurrence.csv": co,
        "mark_14_executable_next_tick.csv": exec_df,
        "mark_14_executable_next_tick_summary.csv": exec_summary,
        "mark_14_pre_event_oracle.csv": pre_summary,
    }
    for name, df in outputs.items():
        df.to_csv(OUT_DIR / name, index=False)

    strong = product_summary[product_summary["symbol"].isin(["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_4000", "VEV_5200"])]
    markouts_cols = [
        "symbol",
        "side",
        "n",
        "qty_mean",
        "edge_t10_mean",
        "edge_t50_mean",
        "edge_t200_mean",
        "edge_t500_mean",
        "midmo_t200_mean",
    ]
    book_cols = [
        "symbol",
        "side",
        "n",
        "spread_mean",
        "all_spread_mean",
        "spread_pctile_mean",
        "side_touch_improve_mean",
        "side_mid_edge_mean",
        "at_bid",
        "at_ask",
        "inside",
    ]
    day_cols = [
        "symbol",
        "side",
        "day",
        "n",
        "edge_t10_mean",
        "edge_t50_mean",
        "edge_t200_mean",
        "edge_t500_mean",
    ]
    exec_cols = [
        "symbol",
        "side",
        "n",
        "historical_mean",
        "executable_mean",
        "mean_slippage",
    ]
    pre100 = pre_summary[pre_summary["offset"] == 100].sort_values("passive_edge_per_event", ascending=False)
    pre_cols = [
        "symbol",
        "offset",
        "n",
        "cross_mean",
        "passive_fill_rate",
        "passive_mean_if_filled",
        "passive_edge_per_event",
    ]

    total_qty = int(mark["quantity"].sum())
    product_counts = (
        mark.groupby("symbol")
        .agg(events=("timestamp", "count"), qty=("quantity", "sum"), t200=("edge_t200", "mean"))
        .reset_index()
        .sort_values("events", ascending=False)
    )

    lines = []
    lines.append("# Mark 14 Counterparty Taxonomy")
    lines.append("")
    lines.append("Scope: Round 4 raw `data/ROUND4` days 1-3. Forward markouts use first product mid at timestamp >= event timestamp + horizon, signed from Mark 14's side: buy = future_mid - trade_price, sell = trade_price - future_mid. Book relation uses same timestamp top of book.")
    lines.append("")
    lines.append("## Executive read")
    lines.append("")
    lines.append(f"- Mark 14 appears in {len(mark):,} trade rows, total quantity {total_qty:,}, across {mark['symbol'].nunique()} products.")
    lines.append("- The historical trade-price signal is real on HYDROGEL_PACK, VELVETFRUIT_EXTRACT, and VEV_4000, but the same raw-data recheck shows next-tick crossing loses after spread/slippage. This matches the prior rejected copy-strategy backtests in `DATA.md` / `TRADING.md`.")
    lines.append("- The edge is mostly spread capture / price selection: main-product buys print at bid and sells print at ask, while t+200 side-signed mid-to-mid markouts are tiny (HGP +0.14/+0.27; VFE -0.09/-0.16; VEV_4000 -0.25/+0.01).")
    lines.append("- Behavior is best classified as passive adverse selection of liquidity takers, not a visible-book liquidity-taker signal we can chase after the ID appears.")
    lines.append("- Strategy implication for v314159: ignore direct copy and do not tighten in response. Mark 14 does not justify a reactive active sleeve; any use should be passive-only/widening and must pass both backtest modes.")
    lines.append("")
    lines.append("## Products and side bias")
    lines.append("")
    lines.append(to_md_table(product_counts, ["symbol", "events", "qty", "t200"]))
    lines.append("")
    lines.append(to_md_table(product_summary[markouts_cols].sort_values(["symbol", "side"]), markouts_cols))
    lines.append("")
    lines.append("## Product + side + day markouts")
    lines.append("")
    lines.append(to_md_table(product_day[day_cols], day_cols))
    lines.append("")
    lines.append("## Size signature")
    lines.append("")
    lines.append(to_md_table(sizes, ["symbol", "side", "n", "qty_mean", "qty_p50", "qty_p90", "qty_min", "qty_max", "top_sizes"]))
    lines.append("")
    lines.append("## Book and spread relation")
    lines.append("")
    lines.append(to_md_table(book[book_cols].sort_values(["symbol", "side"]), book_cols))
    lines.append("")
    lines.append("## Counterparty interactions")
    lines.append("")
    lines.append(to_md_table(cp.head(20), ["symbol", "side", "counterparty", "n", "qty_sum", "edge_t200_mean", "edge_t200_sum"]))
    lines.append("")
    lines.append(to_md_table(co.sort_values(["symbol", "side"]), ["symbol", "side", "n", "pct_any_other_same_ts", "mean_other_trades_same_ts", "pct_same_product_other"]))
    lines.append("")
    lines.append("## Timing, periodicity, and repeated timestamps")
    lines.append("")
    lines.append(to_md_table(timing.sort_values(["symbol", "side", "day"]), ["symbol", "side", "day", "n", "first_ts", "last_ts", "gap_mean", "gap_p50", "gap_p10", "gap_p90", "gap_min", "gap_max"]))
    lines.append("")
    lines.append(to_md_table(mods, ["symbol", "mod", "top_buckets"]))
    lines.append("")
    lines.append(to_md_table(repeats, ["symbol", "side", "unique_timestamp_keys", "repeated_2plus_days", "repeated_3_days"]))
    lines.append("")
    lines.append(f"Within-day duplicate Mark 14 timestamps: {len(duplicate_ts)} day/timestamp pairs with more than one Mark 14 event.")
    if len(duplicate_ts):
        lines.append(to_md_table(duplicate_ts.head(20), ["day", "timestamp", "mark14_events", "products", "sides"]))
    lines.append("")
    lines.append("## Executability recheck")
    lines.append("")
    lines.append(to_md_table(exec_summary[exec_cols], exec_cols))
    lines.append("")
    lines.append("Prior full strategy tests in shared docs: no-exit direct cross none=-2,024,289 / worse=-2,010,123; t+200 exit direct cross none=-5,428,091 / worse=-5,181,259; exact-quantity copy all none=worse=-1,175,572; exact-quantity copy on strong products none=worse=-1,179,912.")
    lines.append("")
    lines.append("## Pre-event oracle check")
    lines.append("")
    lines.append(to_md_table(pre100[pre_cols], pre_cols))
    lines.append("")
    lines.append("This is an oracle because it assumes side and timing before the Mark 14 print. It confirms the prior pattern: crossing before the event is still negative, while passive fill proxies can be positive because they approximate Mark 14's favorable historical trade prices.")
    lines.append("")
    lines.append("## Classification")
    lines.append("")
    lines.append("- Market-maker: partial/passive, but not a broad symmetric market maker. Mark 14 is two-sided only in HGP/VFE/VEV_4000 and only buys the smaller option samples.")
    lines.append("- Liquidity-taker: no on the main products. Mark 14 buys at bid and sells at ask in the same-timestamp book, so the visible aggressor is the other Mark.")
    lines.append("- Informed/adverse: adverse to counterparties at the trade price, mainly through spread capture. There is little evidence of exploitable post-event directional mid drift after the ID is observed.")
    lines.append("- Noise: no for HGP/VFE/VEV_4000 as a historical fill-quality signal; weak/small-sample for VEV_5200 and smaller options.")
    lines.append("")
    lines.append("## v314159 comparison")
    lines.append("")
    lines.append("- HYDROGEL_PACK: keep v314159 behavior unless a one-factor test proves otherwise. Mark 14 trade-price edge is +8.16, but next-tick executable edge is -7.78 overall and mid-to-mid drift is only about +0.2, so do not copy or tighten.")
    lines.append("- VELVETFRUIT_EXTRACT: v314159 already suppresses VFE sells after M67/M49, not Mark 14. Mark 14 adds no clear post-event directional edge (mid-to-mid is negative on both sides), so the default recommendation is ignore.")
    lines.append("- VEV_4000: strong historical trade-price signal (+10.29) but entirely non-executable by chasing; v314159's deep-ITM structural sleeve should not be changed from this Mark alone.")
    lines.append("- VEV_5200 and other options: small buy-only samples and weak markouts. Ignore for baseline changes; this does not alter the existing Mark 22 option mask.")
    lines.append("")
    lines.append("## Files created")
    lines.append("")
    for name in ["mark_14.py", *outputs.keys()]:
        lines.append(f"- `notebooks/round4/mark_taxonomy/{name}`")

    (OUT_DIR / "mark_14.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_DIR / 'mark_14.md'}")


if __name__ == "__main__":
    write_outputs()
