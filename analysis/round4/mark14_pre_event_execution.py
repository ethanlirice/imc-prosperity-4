from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent

TRADER = "Mark 14"
STRONG_PRODUCTS = {"HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_4000"}
FORWARD_HORIZON = 200
OFFSETS = [100, 200, 500, 1000, 2000, 5000]
PASSIVE_LEVELS = ["join_bbo", "improve_1", "mid_passive"]


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_data():
    trades = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        trades.append(df)

    prices = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        prices.append(df)

    if not trades or not prices:
        raise FileNotFoundError(f"Missing Round 4 data under {DATA_DIR}")

    return pd.concat(trades, ignore_index=True), pd.concat(prices, ignore_index=True)


def as_float(row, column):
    value = row.get(column, np.nan)
    if pd.isna(value):
        return None
    return float(value)


def row_at_or_before(frame, timestamp):
    rows = frame[frame["timestamp"] <= timestamp]
    if len(rows) == 0:
        return None
    return rows.iloc[-1]


def first_mid_after_within(frame, timestamp, horizon):
    rows = frame[
        (frame["timestamp"] > timestamp)
        & (frame["timestamp"] <= timestamp + horizon)
    ]
    if len(rows) == 0:
        return None
    return float(rows.iloc[-1]["mid_price"])


def passive_limit(row, side, level):
    bid = as_float(row, "bid_price_1")
    ask = as_float(row, "ask_price_1")
    if bid is None or ask is None:
        return None

    if level == "join_bbo":
        return bid if side == "buy" else ask

    if level == "improve_1":
        if ask - bid <= 1:
            return None
        return bid + 1 if side == "buy" else ask - 1

    if level == "mid_passive":
        if ask - bid <= 1:
            return None
        if side == "buy":
            px = np.floor((bid + ask) / 2)
            return min(float(px), ask - 1)
        px = np.ceil((bid + ask) / 2)
        return max(float(px), bid + 1)

    raise ValueError(level)


def side_direction(side):
    return 1 if side == "buy" else -1


def passive_fill(trade_frame, day, symbol, start_ts, end_ts, side, limit_px):
    window = trade_frame[
        (trade_frame["day"] == day)
        & (trade_frame["symbol"] == symbol)
        & (trade_frame["timestamp"] > start_ts)
        & (trade_frame["timestamp"] <= end_ts)
    ]
    if side == "buy":
        hits = window[window["price"] <= limit_px]
    else:
        hits = window[window["price"] >= limit_px]
    if len(hits) == 0:
        return None
    return hits.iloc[0]


def book_volume(row, prefix):
    total = 0.0
    for level in (1, 2, 3):
        value = row.get(f"{prefix}_volume_{level}", np.nan)
        if not pd.isna(value):
            total += abs(float(value))
    return total


def build_events(trades, price_lookup):
    rows = []
    for _, trade in trades.iterrows():
        if trade["buyer"] != TRADER and trade["seller"] != TRADER:
            continue

        day = int(trade["day"])
        symbol = trade["symbol"]
        timestamp = int(trade["timestamp"])
        side = "buy" if trade["buyer"] == TRADER else "sell"
        frame = price_lookup.get((day, symbol))
        if frame is None:
            continue

        event_row = row_at_or_before(frame, timestamp)
        future_mid = first_mid_after_within(frame, timestamp, FORWARD_HORIZON)
        if event_row is None or future_mid is None:
            continue

        direction = side_direction(side)
        event_mid = float(event_row["mid_price"])
        mark_price = float(trade["price"])
        historical_edge = direction * (future_mid - mark_price)
        mid_edge = direction * (future_mid - event_mid)
        bid_vol = book_volume(event_row, "bid")
        ask_vol = book_volume(event_row, "ask")
        imbalance = np.nan
        if bid_vol + ask_vol > 0:
            imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)

        rows.append(
            {
                "day": day,
                "symbol": symbol,
                "timestamp": timestamp,
                "side": side,
                "direction": direction,
                "qty": int(trade["quantity"]),
                "mark_price": mark_price,
                "event_mid": event_mid,
                "future_mid": future_mid,
                "historical_edge": historical_edge,
                "event_mid_edge": mid_edge,
                "event_spread": as_float(event_row, "ask_price_1")
                - as_float(event_row, "bid_price_1"),
                "event_imbalance": imbalance,
                "signed_event_imbalance": direction * imbalance
                if not pd.isna(imbalance)
                else np.nan,
            }
        )

    return pd.DataFrame(rows)


def analyze_offsets(events, price_lookup, trades):
    early_rows = []
    passive_rows = []
    feature_rows = []

    for _, event in events.iterrows():
        day = int(event["day"])
        symbol = event["symbol"]
        event_ts = int(event["timestamp"])
        side = event["side"]
        direction = int(event["direction"])
        frame = price_lookup[(day, symbol)]

        for offset in OFFSETS:
            pre_row = row_at_or_before(frame, event_ts - offset)
            if pre_row is None:
                continue

            pre_ts = int(pre_row["timestamp"])
            bid = as_float(pre_row, "bid_price_1")
            ask = as_float(pre_row, "ask_price_1")
            if bid is None or ask is None:
                continue

            pre_mid = float(pre_row["mid_price"])
            entry_px = ask if side == "buy" else bid
            early_edge = direction * (float(event["future_mid"]) - entry_px)
            signed_pre_move = direction * (float(event["event_mid"]) - pre_mid)
            bid_vol = book_volume(pre_row, "bid")
            ask_vol = book_volume(pre_row, "ask")
            imbalance = np.nan
            if bid_vol + ask_vol > 0:
                imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)

            early_rows.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "event_ts": event_ts,
                    "pre_ts": pre_ts,
                    "offset": offset,
                    "side": side,
                    "qty": int(event["qty"]),
                    "entry_px": entry_px,
                    "future_mid": float(event["future_mid"]),
                    "edge": early_edge,
                    "qty_edge": early_edge * int(event["qty"]),
                    "spread": ask - bid,
                    "signed_pre_move": signed_pre_move,
                    "signed_imbalance": direction * imbalance
                    if not pd.isna(imbalance)
                    else np.nan,
                }
            )

            feature_rows.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "event_ts": event_ts,
                    "offset": offset,
                    "side": side,
                    "signed_pre_move": signed_pre_move,
                    "pre_spread": ask - bid,
                    "signed_imbalance": direction * imbalance
                    if not pd.isna(imbalance)
                    else np.nan,
                }
            )

            for level in PASSIVE_LEVELS:
                limit_px = passive_limit(pre_row, side, level)
                if limit_px is None:
                    continue
                fill = passive_fill(trades, day, symbol, pre_ts, event_ts, side, limit_px)
                filled = fill is not None
                fill_ts = int(fill["timestamp"]) if filled else np.nan
                fill_trade_price = float(fill["price"]) if filled else np.nan
                edge = direction * (float(event["future_mid"]) - limit_px)
                passive_rows.append(
                    {
                        "day": day,
                        "symbol": symbol,
                        "event_ts": event_ts,
                        "pre_ts": pre_ts,
                        "offset": offset,
                        "level": level,
                        "side": side,
                        "limit_px": limit_px,
                        "filled": filled,
                        "fill_ts": fill_ts,
                        "fill_trade_price": fill_trade_price,
                        "future_mid": float(event["future_mid"]),
                        "edge_if_filled": edge if filled else np.nan,
                        "qty_edge_if_filled": edge * int(event["qty"])
                        if filled
                        else np.nan,
                    }
                )

    return (
        pd.DataFrame(early_rows),
        pd.DataFrame(passive_rows),
        pd.DataFrame(feature_rows),
    )


def summarize_early(early):
    return (
        early.groupby(["symbol", "offset"])
        .agg(
            events=("edge", "count"),
            good_pct=("edge", lambda x: (x > 0).mean()),
            mean_edge=("edge", "mean"),
            unit_edge=("edge", "sum"),
            qty_edge=("qty_edge", "sum"),
            mean_spread=("spread", "mean"),
        )
        .reset_index()
        .sort_values(["symbol", "offset"])
    )


def summarize_passive(passive):
    filled_edge = lambda x: x.dropna().mean()
    filled_good = lambda x: (x.dropna() > 0).mean() if len(x.dropna()) else np.nan
    return (
        passive.groupby(["symbol", "offset", "level"])
        .agg(
            events=("filled", "count"),
            fills=("filled", "sum"),
            fill_rate=("filled", "mean"),
            good_pct_if_filled=("edge_if_filled", filled_good),
            mean_edge_if_filled=("edge_if_filled", filled_edge),
            unit_edge_if_filled=("edge_if_filled", "sum"),
            qty_edge_if_filled=("qty_edge_if_filled", "sum"),
        )
        .reset_index()
        .assign(edge_per_event=lambda df: df["unit_edge_if_filled"] / df["events"])
        .sort_values(["symbol", "offset", "level"])
    )


def summarize_features(features):
    return (
        features.groupby(["symbol", "offset"])
        .agg(
            events=("signed_pre_move", "count"),
            mean_signed_pre_move=("signed_pre_move", "mean"),
            pct_buy_after_dip_sell_after_rally=("signed_pre_move", lambda x: (x < 0).mean()),
            mean_pre_spread=("pre_spread", "mean"),
            mean_signed_imbalance=("signed_imbalance", "mean"),
            pct_imbalance_with_signal=("signed_imbalance", lambda x: (x > 0).mean()),
        )
        .reset_index()
        .sort_values(["symbol", "offset"])
    )


def summarize_side_sequence(events):
    rows = []
    for (day, symbol), frame in events.groupby(["day", "symbol"]):
        ordered = frame.sort_values("timestamp").reset_index(drop=True)
        for idx in range(len(ordered) - 1):
            current = ordered.iloc[idx]
            nxt = ordered.iloc[idx + 1]
            rows.append(
                {
                    "day": int(day),
                    "symbol": symbol,
                    "timestamp": int(current["timestamp"]),
                    "side": current["side"],
                    "next_side": nxt["side"],
                    "same_side_next": current["side"] == nxt["side"],
                    "gap_to_next": int(nxt["timestamp"]) - int(current["timestamp"]),
                }
            )

    seq = pd.DataFrame(rows)
    if len(seq) == 0:
        return seq, pd.DataFrame()

    summary = (
        seq.groupby("symbol")
        .agg(
            events_with_next=("same_side_next", "count"),
            same_side_next_pct=("same_side_next", "mean"),
            mean_gap_to_next=("gap_to_next", "mean"),
            median_gap_to_next=("gap_to_next", "median"),
            pct_next_within_500=("gap_to_next", lambda x: (x <= 500).mean()),
            pct_next_within_1000=("gap_to_next", lambda x: (x <= 1000).mean()),
        )
        .reset_index()
        .sort_values("symbol")
    )
    return seq, summary


def summarize_timestamp_recurrence(events):
    recurrence = (
        events.groupby(["symbol", "timestamp", "side"])
        .agg(days=("day", "nunique"), events=("day", "count"), avg_qty=("qty", "mean"))
        .reset_index()
    )

    summary = (
        recurrence.groupby("symbol")
        .agg(
            unique_symbol_timestamp_side=("timestamp", "count"),
            repeated_2plus_days=("days", lambda x: (x >= 2).sum()),
            repeated_3_days=("days", lambda x: (x >= 3).sum()),
        )
        .reset_index()
        .sort_values("symbol")
    )

    cv_rows = []
    days = sorted(events["day"].unique())
    for heldout in days:
        train = events[events["day"] != heldout]
        actual = events[events["day"] == heldout]
        actual_keys = set(zip(actual["symbol"], actual["timestamp"], actual["side"]))
        actual_symbol_ts = set(zip(actual["symbol"], actual["timestamp"]))

        for threshold in (1, 2):
            train_sched = (
                train.groupby(["symbol", "timestamp", "side"])["day"]
                .nunique()
                .reset_index(name="train_days")
            )
            train_sched = train_sched[train_sched["train_days"] >= threshold]
            pred_keys = set(
                zip(train_sched["symbol"], train_sched["timestamp"], train_sched["side"])
            )
            pred_symbol_ts = set(zip(train_sched["symbol"], train_sched["timestamp"]))
            true_pos = len(pred_keys & actual_keys)
            wrong_side = len(
                [
                    key
                    for key in pred_keys
                    if (key[0], key[1]) in actual_symbol_ts and key not in actual_keys
                ]
            )
            cv_rows.append(
                {
                    "heldout_day": int(heldout),
                    "threshold_train_days": threshold,
                    "predicted_events": len(pred_keys),
                    "actual_events": len(actual_keys),
                    "true_positive_events": true_pos,
                    "wrong_side_same_timestamp": wrong_side,
                    "precision": true_pos / len(pred_keys) if pred_keys else np.nan,
                    "recall": true_pos / len(actual_keys) if actual_keys else np.nan,
                    "timestamp_recall_any_side": len(pred_symbol_ts & actual_symbol_ts)
                    / len(actual_symbol_ts)
                    if actual_symbol_ts
                    else np.nan,
                }
            )

            for symbol in sorted(STRONG_PRODUCTS):
                pred_product = {key for key in pred_keys if key[0] == symbol}
                actual_product = {key for key in actual_keys if key[0] == symbol}
                actual_product_ts = {
                    (key[0], key[1]) for key in actual_keys if key[0] == symbol
                }
                pred_product_ts = {
                    (key[0], key[1]) for key in pred_keys if key[0] == symbol
                }
                tp_product = len(pred_product & actual_product)
                cv_rows.append(
                    {
                        "heldout_day": int(heldout),
                        "threshold_train_days": threshold,
                        "symbol": symbol,
                        "predicted_events": len(pred_product),
                        "actual_events": len(actual_product),
                        "true_positive_events": tp_product,
                        "wrong_side_same_timestamp": len(
                            [
                                key
                                for key in pred_product
                                if (key[0], key[1]) in actual_product_ts
                                and key not in actual_product
                            ]
                        ),
                        "precision": tp_product / len(pred_product)
                        if pred_product
                        else np.nan,
                        "recall": tp_product / len(actual_product)
                        if actual_product
                        else np.nan,
                        "timestamp_recall_any_side": len(
                            pred_product_ts & actual_product_ts
                        )
                        / len(actual_product_ts)
                        if actual_product_ts
                        else np.nan,
                    }
                )

    cv = pd.DataFrame(cv_rows)
    return recurrence, summary, cv


def summarize_running_extrema(events, price_lookup):
    rows = []
    for _, event in events.iterrows():
        day = int(event["day"])
        symbol = event["symbol"]
        timestamp = int(event["timestamp"])
        frame = price_lookup[(day, symbol)]
        history = frame[frame["timestamp"] <= timestamp]
        if len(history) == 0:
            continue

        event_mid = float(event["event_mid"])
        running_min = float(history["mid_price"].min())
        running_max = float(history["mid_price"].max())
        if event["side"] == "buy":
            relevant_distance = event_mid - running_min
        else:
            relevant_distance = running_max - event_mid

        rows.append(
            {
                "day": day,
                "symbol": symbol,
                "timestamp": timestamp,
                "side": event["side"],
                "event_mid": event_mid,
                "running_min": running_min,
                "running_max": running_max,
                "relevant_extrema_distance": relevant_distance,
            }
        )

    extrema = pd.DataFrame(rows)
    summary = (
        extrema.groupby(["symbol", "side"])
        .agg(
            events=("relevant_extrema_distance", "count"),
            mean_relevant_distance=("relevant_extrema_distance", "mean"),
            pct_at_extreme=("relevant_extrema_distance", lambda x: (x <= 0).mean()),
            pct_within_1=("relevant_extrema_distance", lambda x: (x <= 1).mean()),
            pct_within_2=("relevant_extrema_distance", lambda x: (x <= 2).mean()),
            pct_within_5=("relevant_extrema_distance", lambda x: (x <= 5).mean()),
            pct_within_10=("relevant_extrema_distance", lambda x: (x <= 10).mean()),
        )
        .reset_index()
        .sort_values(["symbol", "side"])
    )
    return extrema, summary


def write_report(
    events,
    early_summary,
    passive_summary,
    feature_summary,
    sequence_summary,
    recurrence_summary,
    schedule_cv,
    extrema_summary,
):
    out = OUT_DIR / "mark14_pre_event_execution_output.txt"
    strong_events = events[events["symbol"].isin(STRONG_PRODUCTS)]
    strong_early = early_summary[early_summary["symbol"].isin(STRONG_PRODUCTS)]
    strong_passive = passive_summary[passive_summary["symbol"].isin(STRONG_PRODUCTS)]
    strong_features = feature_summary[feature_summary["symbol"].isin(STRONG_PRODUCTS)]

    with out.open("w") as fh:
        print("Mark 14 pre-event execution analysis", file=fh)
        print(f"Forward horizon: t+{FORWARD_HORIZON}", file=fh)
        print(f"Offsets: {OFFSETS}", file=fh)
        print(f"Passive levels: {PASSIVE_LEVELS}", file=fh)
        print("", file=fh)

        print("Event counts by product/side:", file=fh)
        counts = (
            events.groupby(["symbol", "side"])
            .agg(
                events=("timestamp", "count"),
                days=("day", "nunique"),
                mean_hist_edge=("historical_edge", "mean"),
                mean_event_mid_edge=("event_mid_edge", "mean"),
                avg_qty=("qty", "mean"),
            )
            .reset_index()
            .sort_values(["symbol", "side"])
        )
        print(counts.to_string(index=False), file=fh)

        print("\nStrong-product upper bound: cross before Mark 14 if side were known", file=fh)
        print(strong_early.to_string(index=False), file=fh)

        print("\nStrong-product passive fill proxy", file=fh)
        print(strong_passive.to_string(index=False), file=fh)

        print("\nStrong-product pre-event features", file=fh)
        print(strong_features.to_string(index=False), file=fh)

        print("\nStrong-product next Mark 14 event sequencing", file=fh)
        print(
            sequence_summary[
                sequence_summary["symbol"].isin(STRONG_PRODUCTS)
            ].to_string(index=False),
            file=fh,
        )

        print("\nStrong-product repeated timestamp/side counts across days", file=fh)
        print(
            recurrence_summary[
                recurrence_summary["symbol"].isin(STRONG_PRODUCTS)
            ].to_string(index=False),
            file=fh,
        )

        print("\nLeave-one-day-out timestamp/side schedule replay", file=fh)
        cv_display = schedule_cv[
            schedule_cv.get("symbol", pd.Series(index=schedule_cv.index, dtype=object)).isna()
        ]
        print(cv_display.to_string(index=False), file=fh)

        print("\nLeave-one-day-out schedule replay by strong product", file=fh)
        cv_products = schedule_cv[
            schedule_cv.get("symbol", pd.Series(index=schedule_cv.index, dtype=object)).isin(
                STRONG_PRODUCTS
            )
        ].sort_values(["symbol", "heldout_day", "threshold_train_days"])
        print(cv_products.to_string(index=False), file=fh)

        print("\nRunning extrema distance for strong products", file=fh)
        print(
            extrema_summary[extrema_summary["symbol"].isin(STRONG_PRODUCTS)].to_string(
                index=False
            ),
            file=fh,
        )

        best_passive = strong_passive.sort_values(
            ["edge_per_event", "fill_rate"], ascending=[False, False]
        ).head(20)
        print("\nBest strong-product passive rows by edge_per_event:", file=fh)
        print(best_passive.to_string(index=False), file=fh)

    return out


def main():
    trades, prices = load_data()
    price_lookup = {
        (int(day), product): frame.sort_values("timestamp").reset_index(drop=True)
        for (day, product), frame in prices.groupby(["day", "product"])
    }

    events = build_events(trades, price_lookup)
    early, passive, features = analyze_offsets(events, price_lookup, trades)
    early_summary = summarize_early(early)
    passive_summary = summarize_passive(passive)
    feature_summary = summarize_features(features)
    sequence, sequence_summary = summarize_side_sequence(events)
    recurrence, recurrence_summary, schedule_cv = summarize_timestamp_recurrence(events)
    extrema, extrema_summary = summarize_running_extrema(events, price_lookup)

    events.to_csv(OUT_DIR / "mark14_pre_event_events.csv", index=False)
    early.to_csv(OUT_DIR / "mark14_pre_event_early_cross.csv", index=False)
    passive.to_csv(OUT_DIR / "mark14_pre_event_passive.csv", index=False)
    features.to_csv(OUT_DIR / "mark14_pre_event_features.csv", index=False)
    sequence.to_csv(OUT_DIR / "mark14_pre_event_sequence.csv", index=False)
    recurrence.to_csv(OUT_DIR / "mark14_pre_event_recurrence.csv", index=False)
    schedule_cv.to_csv(OUT_DIR / "mark14_pre_event_schedule_cv.csv", index=False)
    extrema.to_csv(OUT_DIR / "mark14_pre_event_extrema.csv", index=False)
    early_summary.to_csv(OUT_DIR / "mark14_pre_event_early_cross_summary.csv", index=False)
    passive_summary.to_csv(OUT_DIR / "mark14_pre_event_passive_summary.csv", index=False)
    feature_summary.to_csv(OUT_DIR / "mark14_pre_event_feature_summary.csv", index=False)
    sequence_summary.to_csv(
        OUT_DIR / "mark14_pre_event_sequence_summary.csv", index=False
    )
    recurrence_summary.to_csv(
        OUT_DIR / "mark14_pre_event_recurrence_summary.csv", index=False
    )
    extrema_summary.to_csv(OUT_DIR / "mark14_pre_event_extrema_summary.csv", index=False)

    report = write_report(
        events,
        early_summary,
        passive_summary,
        feature_summary,
        sequence_summary,
        recurrence_summary,
        schedule_cv,
        extrema_summary,
    )
    print(f"Wrote {report}")
    print(f"Events: {len(events)}")


if __name__ == "__main__":
    main()
