from pathlib import Path

import numpy as np
import pandas as pd


MARK = "Mark 01"
HORIZONS = (10, 50, 200, 500)

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_trades():
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No trade CSVs in {DATA_DIR}")
    return pd.concat(frames, ignore_index=True)


def load_prices():
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No price CSVs in {DATA_DIR}")
    return pd.concat(frames, ignore_index=True)


def flatten_columns(df):
    df = df.copy()
    df.columns = [
        "_".join(str(part) for part in col if part != "").rstrip("_")
        if isinstance(col, tuple)
        else col
        for col in df.columns
    ]
    return df


def event_rows(trades):
    mark_trades = trades[(trades["buyer"] == MARK) | (trades["seller"] == MARK)].copy()
    rows = []
    for _, row in mark_trades.iterrows():
        if row["buyer"] == MARK:
            side = "buy"
            counterparty = row["seller"]
            side_sign = 1
        else:
            side = "sell"
            counterparty = row["buyer"]
            side_sign = -1
        rows.append(
            {
                "day": row["day"],
                "timestamp": row["timestamp"],
                "product": row["symbol"],
                "side": side,
                "side_sign": side_sign,
                "counterparty": counterparty,
                "price": row["price"],
                "quantity": row["quantity"],
                "notional": row["price"] * row["quantity"],
            }
        )
    return pd.DataFrame(rows)


def relation_to_book(row):
    price = row["price"]
    bid = row["bid_price_1"]
    ask = row["ask_price_1"]
    if pd.isna(bid) or pd.isna(ask):
        return "missing_book"
    if price == bid:
        return "at_bid"
    if price == ask:
        return "at_ask"
    if price < bid:
        return "below_bid"
    if price > ask:
        return "above_ask"
    return "inside_spread"


def add_book_and_markouts(events, prices):
    book_cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "ask_price_1",
        "ask_volume_1",
        "mid_price",
    ]
    enriched = events.merge(prices[book_cols], on=["day", "timestamp", "product"], how="left")
    enriched["spread"] = enriched["ask_price_1"] - enriched["bid_price_1"]
    enriched["touch_depth"] = np.where(
        enriched["side"] == "buy",
        enriched["ask_volume_1"].abs(),
        enriched["bid_volume_1"].abs(),
    )
    enriched["price_minus_mid"] = enriched["price"] - enriched["mid_price"]
    enriched["signed_mid_edge"] = -enriched["side_sign"] * enriched["price_minus_mid"]
    enriched["price_minus_bid"] = enriched["price"] - enriched["bid_price_1"]
    enriched["price_minus_ask"] = enriched["price"] - enriched["ask_price_1"]
    enriched["book_relation"] = enriched.apply(relation_to_book, axis=1)

    price_lookup = {
        key: frame.sort_values("timestamp")[["timestamp", "mid_price"]].reset_index(drop=True)
        for key, frame in prices.groupby(["day", "product"])
    }

    for horizon in HORIZONS:
        future_mids = []
        for row in enriched.itertuples(index=False):
            frame = price_lookup.get((row.day, row.product))
            if frame is None:
                future_mids.append(np.nan)
                continue
            ts_values = frame["timestamp"].to_numpy()
            idx = np.searchsorted(ts_values, row.timestamp + horizon, side="left")
            if idx >= len(frame):
                future_mids.append(np.nan)
            else:
                future_mids.append(frame.at[idx, "mid_price"])
        enriched[f"future_mid_t{horizon}"] = future_mids
        enriched[f"signed_trade_markout_t{horizon}"] = (
            enriched[f"future_mid_t{horizon}"] - enriched["price"]
        ) * enriched["side_sign"]
        enriched[f"signed_mid_change_t{horizon}"] = (
            enriched[f"future_mid_t{horizon}"] - enriched["mid_price"]
        ) * enriched["side_sign"]
    return enriched


def add_regime_percentiles(events, prices):
    frames = []
    px = prices.copy()
    px["spread"] = px["ask_price_1"] - px["bid_price_1"]
    px["book_depth"] = px["bid_volume_1"].abs() + px["ask_volume_1"].abs()
    events = events.copy()
    events["book_depth"] = events["bid_volume_1"].abs() + events["ask_volume_1"].abs()
    for (day, product), event_frame in events.groupby(["day", "product"]):
        day_px = px[(px["day"] == day) & (px["product"] == product)]
        if day_px.empty:
            frames.append(event_frame)
            continue
        spread_vals = np.sort(day_px["spread"].dropna().to_numpy())
        depth_vals = np.sort(day_px["book_depth"].dropna().to_numpy())
        event_frame = event_frame.copy()
        event_frame["spread_day_pctile"] = [
            np.searchsorted(spread_vals, value, side="right") / len(spread_vals)
            if len(spread_vals) and not pd.isna(value)
            else np.nan
            for value in event_frame["spread"]
        ]
        event_frame["depth_day_pctile"] = [
            np.searchsorted(depth_vals, value, side="right") / len(depth_vals)
            if len(depth_vals) and not pd.isna(value)
            else np.nan
            for value in event_frame["book_depth"]
        ]
        frames.append(event_frame)
    return pd.concat(frames, ignore_index=True)


def write_product_side_summary(events):
    agg = events.groupby(["product", "side"]).agg(
        trades=("quantity", "count"),
        days=("day", "nunique"),
        total_qty=("quantity", "sum"),
        avg_qty=("quantity", "mean"),
        median_qty=("quantity", "median"),
        min_qty=("quantity", "min"),
        p90_qty=("quantity", lambda s: s.quantile(0.9)),
        max_qty=("quantity", "max"),
        avg_price=("price", "mean"),
        avg_spread=("spread", "mean"),
        avg_touch_depth=("touch_depth", "mean"),
        avg_spread_pctile=("spread_day_pctile", "mean"),
        avg_depth_pctile=("depth_day_pctile", "mean"),
        avg_signed_mid_edge=("signed_mid_edge", "mean"),
    )
    for horizon in HORIZONS:
        agg[(f"signed_trade_markout_t{horizon}", "mean")] = events.groupby(
            ["product", "side"]
        )[f"signed_trade_markout_t{horizon}"].mean()
        agg[(f"signed_mid_change_t{horizon}", "mean")] = events.groupby(
            ["product", "side"]
        )[f"signed_mid_change_t{horizon}"].mean()
    agg = flatten_columns(agg.reset_index())
    agg.to_csv(OUT_DIR / "mark_01_product_side_summary.csv", index=False)
    return agg


def write_day_markouts(events):
    named_aggs = {
        "trades": ("quantity", "count"),
        "total_qty": ("quantity", "sum"),
        "avg_qty": ("quantity", "mean"),
        "avg_signed_mid_edge": ("signed_mid_edge", "mean"),
        "avg_spread": ("spread", "mean"),
        "avg_spread_pctile": ("spread_day_pctile", "mean"),
    }
    for horizon in HORIZONS:
        named_aggs[f"trade_mo_t{horizon}_mean"] = (
            f"signed_trade_markout_t{horizon}",
            "mean",
        )
        named_aggs[f"trade_mo_t{horizon}_median"] = (
            f"signed_trade_markout_t{horizon}",
            "median",
        )
        named_aggs[f"mid_mo_t{horizon}_mean"] = (
            f"signed_mid_change_t{horizon}",
            "mean",
        )
        named_aggs[f"win_t{horizon}"] = (
            f"signed_trade_markout_t{horizon}",
            lambda s: (s > 0).mean(),
        )
    out = events.groupby(["day", "product", "side"]).agg(**named_aggs).reset_index()
    out.to_csv(OUT_DIR / "mark_01_product_side_day_markouts.csv", index=False)
    return out


def write_price_relation(events):
    out = (
        events.groupby(["product", "side", "book_relation"])
        .agg(
            trades=("quantity", "count"),
            avg_qty=("quantity", "mean"),
            avg_signed_mid_edge=("signed_mid_edge", "mean"),
            avg_trade_mo_t200=("signed_trade_markout_t200", "mean"),
        )
        .reset_index()
        .sort_values(["product", "side", "trades"], ascending=[True, True, False])
    )
    out.to_csv(OUT_DIR / "mark_01_price_relation.csv", index=False)
    return out


def write_counterparties(events):
    out = (
        events.groupby(["counterparty", "product", "side"])
        .agg(
            trades=("quantity", "count"),
            total_qty=("quantity", "sum"),
            avg_qty=("quantity", "mean"),
            avg_price=("price", "mean"),
            avg_signed_mid_edge=("signed_mid_edge", "mean"),
            avg_trade_mo_t200=("signed_trade_markout_t200", "mean"),
            avg_trade_mo_t500=("signed_trade_markout_t500", "mean"),
        )
        .reset_index()
        .sort_values(["trades", "total_qty"], ascending=[False, False])
    )
    out.to_csv(OUT_DIR / "mark_01_counterparties.csv", index=False)
    return out


def write_timing(events):
    rows = []
    for keys, frame in events.sort_values("timestamp").groupby(["day", "product", "side"]):
        gaps = frame["timestamp"].diff().dropna()
        day, product, side = keys
        if gaps.empty:
            rows.append(
                {
                    "day": day,
                    "product": product,
                    "side": side,
                    "events": len(frame),
                    "unique_timestamps": frame["timestamp"].nunique(),
                    "duplicate_timestamp_rows": len(frame) - frame["timestamp"].nunique(),
                    "gap_mean": np.nan,
                    "gap_median": np.nan,
                    "gap_min": np.nan,
                    "gap_p10": np.nan,
                    "gap_p90": np.nan,
                    "gap_max": np.nan,
                    "gap_mode": np.nan,
                    "mod_1000_top": frame["timestamp"].mod(1000).mode().iloc[0],
                    "mod_5000_top": frame["timestamp"].mod(5000).mode().iloc[0],
                }
            )
            continue
        mode = gaps.mode().iloc[0]
        rows.append(
            {
                "day": day,
                "product": product,
                "side": side,
                "events": len(frame),
                "unique_timestamps": frame["timestamp"].nunique(),
                "duplicate_timestamp_rows": len(frame) - frame["timestamp"].nunique(),
                "gap_mean": gaps.mean(),
                "gap_median": gaps.median(),
                "gap_min": gaps.min(),
                "gap_p10": gaps.quantile(0.1),
                "gap_p90": gaps.quantile(0.9),
                "gap_max": gaps.max(),
                "gap_mode": mode,
                "mod_1000_top": frame["timestamp"].mod(1000).mode().iloc[0],
                "mod_5000_top": frame["timestamp"].mod(5000).mode().iloc[0],
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "mark_01_timing.csv", index=False)

    gap_counts = []
    for keys, frame in events.sort_values("timestamp").groupby(["product", "side"]):
        gaps = frame["timestamp"].diff().dropna()
        product, side = keys
        for gap, count in gaps.value_counts().head(10).items():
            gap_counts.append(
                {"product": product, "side": side, "gap": gap, "count": count}
            )
    gap_out = pd.DataFrame(gap_counts)
    gap_out.to_csv(OUT_DIR / "mark_01_common_gaps.csv", index=False)
    return out, gap_out


def write_repeat_timestamps(events):
    key_cols = ["product", "side", "timestamp"]
    repeat = (
        events.groupby(key_cols)
        .agg(days=("day", lambda s: ",".join(str(x) for x in sorted(s.unique()))),
             day_count=("day", "nunique"),
             rows=("quantity", "count"),
             total_qty=("quantity", "sum"),
             avg_trade_mo_t200=("signed_trade_markout_t200", "mean"))
        .reset_index()
        .sort_values(["day_count", "rows", "product", "side", "timestamp"], ascending=[False, False, True, True, True])
    )
    repeat.to_csv(OUT_DIR / "mark_01_repeat_timestamps.csv", index=False)

    timestamp_bursts = (
        events.groupby(["day", "timestamp"])
        .agg(
            rows=("quantity", "count"),
            products=("product", lambda s: ",".join(sorted(s.unique()))),
            sides=("side", lambda s: ",".join(sorted(s.unique()))),
            total_qty=("quantity", "sum"),
        )
        .reset_index()
        .sort_values(["rows", "day", "timestamp"], ascending=[False, True, True])
    )
    timestamp_bursts.to_csv(OUT_DIR / "mark_01_timestamp_bursts.csv", index=False)
    return repeat, timestamp_bursts


def write_same_timestamp_interactions(events, trades):
    mark_keys = events[["day", "timestamp"]].drop_duplicates()
    same_ts = trades.merge(mark_keys, on=["day", "timestamp"], how="inner")
    other = same_ts[(same_ts["buyer"] != MARK) & (same_ts["seller"] != MARK)].copy()
    rows = []
    for _, row in other.iterrows():
        rows.append(
            {
                "day": row["day"],
                "timestamp": row["timestamp"],
                "product": row["symbol"],
                "other_buyer": row["buyer"],
                "other_seller": row["seller"],
                "price": row["price"],
                "quantity": row["quantity"],
            }
        )
    other_out = pd.DataFrame(rows)
    if not other_out.empty:
        other_out.to_csv(OUT_DIR / "mark_01_same_timestamp_other_trades.csv", index=False)
        buyer_counts = other_out["other_buyer"].value_counts()
        seller_counts = other_out["other_seller"].value_counts()
        mark_counts = pd.concat(
            [
                buyer_counts.rename("as_buyer"),
                seller_counts.rename("as_seller"),
            ],
            axis=1,
        ).fillna(0)
        mark_counts["total"] = mark_counts["as_buyer"] + mark_counts["as_seller"]
        mark_counts = mark_counts.reset_index().rename(columns={"index": "mark"})
        mark_counts.sort_values("total", ascending=False).to_csv(
            OUT_DIR / "mark_01_same_timestamp_other_marks.csv", index=False
        )
    else:
        other_out.to_csv(OUT_DIR / "mark_01_same_timestamp_other_trades.csv", index=False)
        pd.DataFrame(columns=["mark", "as_buyer", "as_seller", "total"]).to_csv(
            OUT_DIR / "mark_01_same_timestamp_other_marks.csv", index=False
        )
    return other_out


def write_size_distribution(events):
    out = (
        events.groupby(["product", "side", "quantity"])
        .agg(trades=("quantity", "count"))
        .reset_index()
        .sort_values(["product", "side", "trades"], ascending=[True, True, False])
    )
    out.to_csv(OUT_DIR / "mark_01_size_distribution.csv", index=False)
    return out


def write_quantity_weighted_markouts(events):
    rows = []
    for (product, side), frame in events.groupby(["product", "side"]):
        qty = frame["quantity"].sum()
        row = {
            "product": product,
            "side": side,
            "trades": len(frame),
            "total_qty": qty,
        }
        for horizon in HORIZONS:
            trade_col = f"signed_trade_markout_t{horizon}"
            mid_col = f"signed_mid_change_t{horizon}"
            row[f"trade_mo_t{horizon}_qty_weighted"] = (
                frame[trade_col] * frame["quantity"]
            ).sum() / qty
            row[f"trade_mo_t{horizon}_unit_sum"] = (
                frame[trade_col] * frame["quantity"]
            ).sum()
            row[f"mid_mo_t{horizon}_qty_weighted"] = (
                frame[mid_col] * frame["quantity"]
            ).sum() / qty
            row[f"mid_mo_t{horizon}_unit_sum"] = (
                frame[mid_col] * frame["quantity"]
            ).sum()
        rows.append(row)
    out = pd.DataFrame(rows).sort_values(["product", "side"])
    out.to_csv(OUT_DIR / "mark_01_quantity_weighted_markouts.csv", index=False)
    return out


def write_all_market_context(events, trades):
    product_counts = trades.groupby("symbol").size().rename("all_trades").reset_index()
    mark_counts = events.groupby("product").size().rename("mark01_trades").reset_index()
    out = product_counts.merge(mark_counts, left_on="symbol", right_on="product", how="left")
    out["mark01_trades"] = out["mark01_trades"].fillna(0).astype(int)
    out["mark01_share"] = out["mark01_trades"] / out["all_trades"]
    out = out[["symbol", "all_trades", "mark01_trades", "mark01_share"]]
    out.to_csv(OUT_DIR / "mark_01_market_share.csv", index=False)
    return out


def main():
    trades = load_trades()
    prices = load_prices()
    events = event_rows(trades)
    events = add_book_and_markouts(events, prices)
    events = add_regime_percentiles(events, prices)
    events.sort_values(["day", "timestamp", "product", "side"]).to_csv(
        OUT_DIR / "mark_01_events.csv", index=False
    )

    product_side = write_product_side_summary(events)
    day_markouts = write_day_markouts(events)
    price_relation = write_price_relation(events)
    counterparties = write_counterparties(events)
    timing, gap_counts = write_timing(events)
    repeats, bursts = write_repeat_timestamps(events)
    same_ts = write_same_timestamp_interactions(events, trades)
    size_dist = write_size_distribution(events)
    qty_weighted = write_quantity_weighted_markouts(events)
    market_share = write_all_market_context(events, trades)

    print(f"Mark 01 events: {len(events)}")
    print(f"Products: {', '.join(sorted(events['product'].unique()))}")
    print("\nProduct/side summary:")
    print(product_side.to_string(index=False))
    print("\nDay markouts:")
    print(day_markouts.to_string(index=False))
    print("\nCounterparties:")
    print(counterparties.head(30).to_string(index=False))
    print("\nPrice relation:")
    print(price_relation.to_string(index=False))
    print("\nTiming:")
    print(timing.to_string(index=False))
    print("\nCommon gaps:")
    print(gap_counts.head(50).to_string(index=False))
    print("\nRepeat timestamp keys:")
    print(repeats.head(50).to_string(index=False))
    print("\nTimestamp bursts:")
    print(bursts.head(50).to_string(index=False))
    print("\nSame timestamp other trades rows:", len(same_ts))
    print("\nSize distribution:")
    print(size_dist.to_string(index=False))
    print("\nQuantity-weighted markouts:")
    print(qty_weighted.to_string(index=False))
    print("\nMarket share:")
    print(market_share.to_string(index=False))


if __name__ == "__main__":
    main()
