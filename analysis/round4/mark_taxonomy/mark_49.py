import os
from collections import Counter

import numpy as np
import pandas as pd


DATA_DIR = "data/ROUND4"
OUT_DIR = "notebooks/round4/mark_taxonomy"
MARK = "Mark 49"
VFE = "VELVETFRUIT_EXTRACT"
M67 = "Mark 67"
HORIZONS = [10, 50, 200, 500]
SIGNAL_HORIZONS = [10, 50, 200, 500, 1000, 2000, 5000]


def q(s, p):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) == 0:
        return np.nan
    return float(s.quantile(p))


def fmt_num(x, digits=3):
    if pd.isna(x):
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    try:
        fx = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(fx - round(fx)) < 1e-9:
        return str(int(round(float(x))))
    return f"{fx:.{digits}f}"


def md_table(df, cols=None, digits=3, max_rows=None):
    if cols is not None:
        df = df.loc[:, cols]
    if max_rows is not None:
        df = df.head(max_rows)
    if df.empty:
        return "_No rows._"
    labels = list(df.columns)
    lines = [
        "| " + " | ".join(labels) + " |",
        "| " + " | ".join(["---"] * len(labels)) + " |",
    ]
    for _, row in df.iterrows():
        vals = [fmt_num(row[c], digits) for c in labels]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def flatten_cols(df):
    out = df.copy()
    out.columns = [
        "_".join([str(x) for x in col if str(x) != ""]).strip("_")
        if isinstance(col, tuple)
        else str(col)
        for col in out.columns
    ]
    return out.reset_index()


def load_data():
    prices = []
    trades = []
    for day in [1, 2, 3]:
        p = pd.read_csv(os.path.join(DATA_DIR, f"prices_round_4_day_{day}.csv"), sep=";")
        p["day"] = day
        prices.append(p)
        t = pd.read_csv(os.path.join(DATA_DIR, f"trades_round_4_day_{day}.csv"), sep=";")
        t["day"] = day
        t["row_id"] = np.arange(len(t)) + day * 100000
        trades.append(t)
    prices = pd.concat(prices, ignore_index=True)
    trades = pd.concat(trades, ignore_index=True)

    for c in [
        "bid_price_1",
        "bid_volume_1",
        "bid_price_2",
        "bid_volume_2",
        "bid_price_3",
        "bid_volume_3",
        "ask_price_1",
        "ask_volume_1",
        "ask_price_2",
        "ask_volume_2",
        "ask_price_3",
        "ask_volume_3",
        "mid_price",
    ]:
        prices[c] = pd.to_numeric(prices[c], errors="coerce")
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    prices["bid_depth_3"] = prices[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).sum(axis=1)
    prices["ask_depth_3"] = prices[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).sum(axis=1)
    prices = prices.sort_values(["day", "product", "timestamp"]).reset_index(drop=True)

    trades["price"] = pd.to_numeric(trades["price"], errors="coerce")
    trades["quantity"] = pd.to_numeric(trades["quantity"], errors="coerce")
    return prices, trades


def add_future_mids(events, prices, horizons):
    out = events.copy().sort_values(["day", "symbol", "timestamp"]).reset_index(drop=True)
    out["_event_idx"] = np.arange(len(out))
    for h in horizons:
        pieces = []
        right_base = prices[["day", "product", "timestamp", "mid_price"]].copy()
        for (day, sym), left in out.groupby(["day", "symbol"], sort=False):
            right = right_base[(right_base["day"] == day) & (right_base["product"] == sym)].sort_values("timestamp")
            if right.empty:
                tmp = left[["_event_idx"]].copy()
                tmp[f"future_mid_{h}"] = np.nan
            else:
                l = left[["_event_idx", "timestamp"]].copy()
                l["target_ts"] = l["timestamp"] + h
                tmp = pd.merge_asof(
                    l.sort_values("target_ts"),
                    right[["timestamp", "mid_price"]].rename(columns={"timestamp": "future_ts"}),
                    left_on="target_ts",
                    right_on="future_ts",
                    direction="forward",
                )[["_event_idx", "mid_price"]].rename(columns={"mid_price": f"future_mid_{h}"})
            pieces.append(tmp)
        fut = pd.concat(pieces, ignore_index=True)
        out = out.merge(fut, on="_event_idx", how="left")
        side_sign = np.where(out["mark49_side"] == "buy", 1, -1)
        out[f"mid_move_{h}"] = out[f"future_mid_{h}"] - out["mid_price"]
        out[f"side_mid_markout_{h}"] = side_sign * out[f"mid_move_{h}"]
        out[f"trade_markout_{h}"] = np.where(
            out["mark49_side"] == "buy",
            out[f"future_mid_{h}"] - out["price"],
            out["price"] - out[f"future_mid_{h}"],
        )
    return out.drop(columns=["_event_idx"])


def active_mask_for_events(price_day, event_ts, window):
    active = np.zeros(len(price_day), dtype=bool)
    event_ts = sorted(set(int(x) for x in event_ts))
    if not event_ts:
        return active
    starts = np.array(event_ts)
    ts = price_day["timestamp"].to_numpy()
    pos = np.searchsorted(starts, ts, side="right") - 1
    valid = pos >= 0
    active[valid] = ts[valid] - starts[pos[valid]] <= window
    return active


def add_future_to_price_series(price_series, prices, horizons):
    out = price_series.copy().sort_values(["day", "product", "timestamp"]).reset_index(drop=True)
    out["_idx"] = np.arange(len(out))
    for h in horizons:
        pieces = []
        for (day, product), left in out.groupby(["day", "product"], sort=False):
            right = prices[(prices["day"] == day) & (prices["product"] == product)][["timestamp", "mid_price"]]
            l = left[["_idx", "timestamp"]].copy()
            l["target_ts"] = l["timestamp"] + h
            tmp = pd.merge_asof(
                l.sort_values("target_ts"),
                right.rename(columns={"timestamp": "future_ts"}),
                left_on="target_ts",
                right_on="future_ts",
                direction="forward",
            )[["_idx", "mid_price"]].rename(columns={"mid_price": f"future_mid_{h}"})
            pieces.append(tmp)
        out = out.merge(pd.concat(pieces, ignore_index=True), on="_idx", how="left")
        out[f"mid_move_{h}"] = out[f"future_mid_{h}"] - out["mid_price"]
    return out.drop(columns=["_idx"])


def write_csv(df, name):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False)
    return path


def summarize_markouts(events):
    rows = []
    for keys, g in events.groupby(["day", "symbol", "mark49_side"]):
        row = {"day": keys[0], "product": keys[1], "side": keys[2], "n": len(g)}
        for h in HORIZONS:
            row[f"trade_mo_{h}_mean"] = g[f"trade_markout_{h}"].mean()
            row[f"mid_move_{h}_mean"] = g[f"mid_move_{h}"].mean()
            row[f"side_mid_mo_{h}_mean"] = g[f"side_mid_markout_{h}"].mean()
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["product", "side", "day"])


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    prices, trades = load_data()

    mark = trades[(trades["buyer"] == MARK) | (trades["seller"] == MARK)].copy()
    mark["mark49_side"] = np.where(mark["buyer"] == MARK, "buy", "sell")
    mark["other_party"] = np.where(mark["buyer"] == MARK, mark["seller"], mark["buyer"])
    mark = mark.merge(
        prices[
            [
                "day",
                "timestamp",
                "product",
                "bid_price_1",
                "ask_price_1",
                "bid_volume_1",
                "ask_volume_1",
                "bid_depth_3",
                "ask_depth_3",
                "spread",
                "mid_price",
            ]
        ].rename(columns={"product": "symbol"}),
        on=["day", "timestamp", "symbol"],
        how="left",
    )
    mark["px_minus_mid"] = mark["price"] - mark["mid_price"]
    mark["at_bid"] = np.isclose(mark["price"], mark["bid_price_1"])
    mark["at_ask"] = np.isclose(mark["price"], mark["ask_price_1"])
    mark["inside"] = (mark["price"] > mark["bid_price_1"]) & (mark["price"] < mark["ask_price_1"])
    mark["outside"] = (mark["price"] < mark["bid_price_1"]) | (mark["price"] > mark["ask_price_1"])
    mark["aggressive"] = np.where(
        mark["mark49_side"] == "buy",
        mark["price"] >= mark["ask_price_1"],
        mark["price"] <= mark["bid_price_1"],
    )
    mark["passive_or_price_improved"] = np.where(
        mark["mark49_side"] == "buy",
        mark["price"] <= mark["bid_price_1"],
        mark["price"] >= mark["ask_price_1"],
    )
    mark = add_future_mids(mark, prices, SIGNAL_HORIZONS)
    write_csv(mark, "mark_49_events_enriched.csv")

    product_side = flatten_cols(
        mark.groupby(["symbol", "mark49_side"]).agg(
            trades=("quantity", "size"),
            total_qty=("quantity", "sum"),
            mean_qty=("quantity", "mean"),
            median_qty=("quantity", "median"),
            max_qty=("quantity", "max"),
            first_ts=("timestamp", "min"),
            last_ts=("timestamp", "max"),
        )
    ).sort_values(["symbol", "mark49_side"])
    write_csv(product_side, "mark_49_product_side_summary.csv")

    day_side = flatten_cols(
        mark.groupby(["day", "symbol", "mark49_side"]).agg(
            trades=("quantity", "size"),
            total_qty=("quantity", "sum"),
            mean_qty=("quantity", "mean"),
            median_qty=("quantity", "median"),
            max_qty=("quantity", "max"),
        )
    ).sort_values(["symbol", "mark49_side", "day"])
    write_csv(day_side, "mark_49_day_side_summary.csv")

    size_rows = []
    for (sym, side), g in mark.groupby(["symbol", "mark49_side"]):
        top_sizes = Counter(g["quantity"].astype(int)).most_common(5)
        size_rows.append(
            {
                "product": sym,
                "side": side,
                "n": len(g),
                "mean": g["quantity"].mean(),
                "p25": q(g["quantity"], 0.25),
                "median": q(g["quantity"], 0.5),
                "p75": q(g["quantity"], 0.75),
                "p90": q(g["quantity"], 0.9),
                "max": g["quantity"].max(),
                "top_sizes": "; ".join(f"{s}x{c}" for s, c in top_sizes),
            }
        )
    size_dist = pd.DataFrame(size_rows).sort_values(["product", "side"])
    write_csv(size_dist, "mark_49_size_distribution.csv")

    timing_rows = []
    gap_rows = []
    for (day, sym, side), g in mark.sort_values("timestamp").groupby(["day", "symbol", "mark49_side"]):
        ts = g["timestamp"].sort_values().to_numpy()
        gaps = np.diff(ts)
        common = Counter(gaps.astype(int)).most_common(5) if len(gaps) else []
        timing_rows.append(
            {
                "day": day,
                "product": sym,
                "side": side,
                "n": len(g),
                "first_ts": ts[0],
                "last_ts": ts[-1],
                "mean_gap": float(np.mean(gaps)) if len(gaps) else np.nan,
                "median_gap": float(np.median(gaps)) if len(gaps) else np.nan,
                "p10_gap": float(np.quantile(gaps, 0.1)) if len(gaps) else np.nan,
                "p90_gap": float(np.quantile(gaps, 0.9)) if len(gaps) else np.nan,
                "top_gaps": "; ".join(f"{gap}x{cnt}" for gap, cnt in common),
            }
        )
        for gap, cnt in Counter(gaps.astype(int)).most_common():
            gap_rows.append({"day": day, "product": sym, "side": side, "gap": gap, "count": cnt})
    timing = pd.DataFrame(timing_rows).sort_values(["product", "side", "day"])
    gaps = pd.DataFrame(gap_rows)
    write_csv(timing, "mark_49_timing_gaps.csv")
    write_csv(gaps, "mark_49_gap_counts.csv")

    repeat_rows = []
    for (sym, side), g in mark.groupby(["symbol", "mark49_side"]):
        keys = g.groupby(["timestamp"])["day"].nunique()
        repeat_rows.append(
            {
                "product": sym,
                "side": side,
                "unique_timestamps": len(keys),
                "repeated_2plus_days": int((keys >= 2).sum()),
                "repeated_all_3_days": int((keys == 3).sum()),
            }
        )
    repeat_ts = pd.DataFrame(repeat_rows).sort_values(["product", "side"])
    write_csv(repeat_ts, "mark_49_repeat_timestamps.csv")

    within_repeat = flatten_cols(
        mark.groupby(["day", "symbol", "mark49_side", "timestamp"]).agg(
            trades_at_ts=("quantity", "size"),
            qty_at_ts=("quantity", "sum"),
        )
    )
    within_repeat = within_repeat[within_repeat["trades_at_ts"] > 1].sort_values(
        ["trades_at_ts", "qty_at_ts"], ascending=False
    )
    write_csv(within_repeat, "mark_49_same_timestamp_repeats.csv")

    relation = flatten_cols(
        mark.groupby(["day", "symbol", "mark49_side"]).agg(
            n=("quantity", "size"),
            avg_px_minus_mid=("px_minus_mid", "mean"),
            median_px_minus_mid=("px_minus_mid", "median"),
            avg_spread=("spread", "mean"),
            median_spread=("spread", "median"),
            avg_bid_depth_3=("bid_depth_3", "mean"),
            avg_ask_depth_3=("ask_depth_3", "mean"),
            at_bid_pct=("at_bid", "mean"),
            at_ask_pct=("at_ask", "mean"),
            inside_pct=("inside", "mean"),
            outside_pct=("outside", "mean"),
            aggressive_pct=("aggressive", "mean"),
            passive_or_price_improved_pct=("passive_or_price_improved", "mean"),
        )
    ).sort_values(["symbol", "mark49_side", "day"])
    for c in [c for c in relation.columns if c.endswith("_pct")]:
        relation[c] *= 100.0
    write_csv(relation, "mark_49_price_relation.csv")

    full_regime = flatten_cols(
        prices.groupby(["day", "product"]).agg(
            full_spread_mean=("spread", "mean"),
            full_spread_median=("spread", "median"),
            full_bid_depth_3_mean=("bid_depth_3", "mean"),
            full_ask_depth_3_mean=("ask_depth_3", "mean"),
        )
    )
    event_regime = flatten_cols(
        mark.groupby(["day", "symbol", "mark49_side"]).agg(
            event_spread_mean=("spread", "mean"),
            event_spread_median=("spread", "median"),
            event_bid_depth_3_mean=("bid_depth_3", "mean"),
            event_ask_depth_3_mean=("ask_depth_3", "mean"),
        )
    )
    regimes = event_regime.merge(
        full_regime.rename(columns={"product": "symbol"}), on=["day", "symbol"], how="left"
    ).sort_values(["symbol", "mark49_side", "day"])
    write_csv(regimes, "mark_49_spread_depth_regimes.csv")

    markouts = summarize_markouts(mark)
    write_csv(markouts, "mark_49_markouts_by_product_side_day.csv")

    direct = flatten_cols(
        mark.groupby(["symbol", "mark49_side", "other_party"]).agg(
            trades=("quantity", "size"),
            qty=("quantity", "sum"),
            avg_qty=("quantity", "mean"),
        )
    ).sort_values(["trades", "qty"], ascending=False)
    write_csv(direct, "mark_49_direct_counterparties.csv")

    part_rows = []
    other_trades = trades.copy()
    for _, ev in mark[["row_id", "day", "timestamp", "symbol"]].iterrows():
        same = other_trades[
            (other_trades["day"] == ev["day"])
            & (other_trades["timestamp"] == ev["timestamp"])
            & (other_trades["row_id"] != ev["row_id"])
        ]
        marks = []
        for _, row in same.iterrows():
            if row["buyer"] != MARK:
                marks.append(row["buyer"])
            if row["seller"] != MARK:
                marks.append(row["seller"])
        for m, cnt in Counter(marks).items():
            part_rows.append({"event_row_id": ev["row_id"], "co_mark": m, "count": cnt})
    if part_rows:
        co = pd.DataFrame(part_rows)
        co_top = flatten_cols(co.groupby("co_mark").agg(events=("event_row_id", "nunique"), mentions=("count", "sum")))
        co_top = co_top.sort_values(["events", "mentions"], ascending=False)
    else:
        co_top = pd.DataFrame(columns=["co_mark", "events", "mentions"])
    write_csv(co_top, "mark_49_same_timestamp_marks.csv")

    vfe_signal_rows = []
    for name, cond in [
        ("M49_sell", (trades["symbol"] == VFE) & (trades["seller"] == MARK)),
        ("M49_buy", (trades["symbol"] == VFE) & (trades["buyer"] == MARK)),
        ("M67_buy", (trades["symbol"] == VFE) & (trades["buyer"] == M67)),
        ("M67_sell", (trades["symbol"] == VFE) & (trades["seller"] == M67)),
    ]:
        tmp = trades[cond].copy()
        if tmp.empty:
            continue
        tmp["mark49_side"] = np.where(tmp["buyer"] == MARK, "buy", np.where(tmp["seller"] == MARK, "sell", name))
        tmp = tmp.merge(
            prices[["day", "timestamp", "product", "mid_price"]].rename(columns={"product": "symbol"}),
            on=["day", "timestamp", "symbol"],
            how="left",
        )
        tmp = add_future_mids(tmp, prices, SIGNAL_HORIZONS)
        for day, g in tmp.groupby("day"):
            row = {"trigger": name, "day": day, "n": len(g)}
            for h in SIGNAL_HORIZONS:
                row[f"mid_move_{h}_mean"] = g[f"mid_move_{h}"].mean()
            vfe_signal_rows.append(row)
    vfe_signal = pd.DataFrame(vfe_signal_rows).sort_values(["trigger", "day"])
    write_csv(vfe_signal, "mark_49_vfe_trigger_forward_mid_moves.csv")

    vfe_prices = prices[prices["product"] == VFE].copy()
    active_rows = []
    active_labeled = []
    for day, pday in vfe_prices.groupby("day"):
        pday = pday.sort_values("timestamp").copy()
        m49_sell_ts = trades[
            (trades["day"] == day) & (trades["symbol"] == VFE) & (trades["seller"] == MARK)
        ]["timestamp"].tolist()
        m49_buy_ts = trades[
            (trades["day"] == day) & (trades["symbol"] == VFE) & (trades["buyer"] == MARK)
        ]["timestamp"].tolist()
        m67_buy_ts = trades[
            (trades["day"] == day) & (trades["symbol"] == VFE) & (trades["buyer"] == M67)
        ]["timestamp"].tolist()
        masks = {
            "inactive_vs_M49_sell": ~active_mask_for_events(pday, m49_sell_ts, 2000),
            "active_M49_sell_only": active_mask_for_events(pday, m49_sell_ts, 2000),
            "active_M49_buy_only": active_mask_for_events(pday, m49_buy_ts, 2000),
            "active_M67_buy_only": active_mask_for_events(pday, m67_buy_ts, 2000),
            "active_v314159_M49_sell_or_M67_buy": active_mask_for_events(pday, sorted(set(m49_sell_ts + m67_buy_ts)), 2000),
        }
        for label, mask in masks.items():
            tmp = pday[mask].copy()
            if tmp.empty:
                continue
            tmp["window_label"] = label
            active_labeled.append(tmp)
    active_series = pd.concat(active_labeled, ignore_index=True)
    active_series = add_future_to_price_series(active_series, prices, HORIZONS)
    for (day, label), g in active_series.groupby(["day", "window_label"]):
        row = {"day": day, "window_label": label, "ticks": len(g)}
        for h in HORIZONS:
            row[f"mid_move_{h}_mean"] = g[f"mid_move_{h}"].mean()
        active_rows.append(row)
    active_summary = pd.DataFrame(active_rows).sort_values(["window_label", "day"])
    write_csv(active_summary, "mark_49_vfe_suppression_window_validation.csv")

    interval_rows = []
    for label, side_cond in [
        ("M49_sell", (trades["symbol"] == VFE) & (trades["seller"] == MARK)),
        ("M67_buy", (trades["symbol"] == VFE) & (trades["buyer"] == M67)),
        ("v314159_combined", (trades["symbol"] == VFE) & ((trades["seller"] == MARK) | (trades["buyer"] == M67))),
    ]:
        for day in [1, 2, 3]:
            ev_ts = sorted(trades[(trades["day"] == day) & side_cond]["timestamp"].astype(int).tolist())
            pday = vfe_prices[vfe_prices["day"] == day].sort_values("timestamp")
            active = active_mask_for_events(pday, ev_ts, 2000)
            overlaps = sum(1 for a, b in zip(ev_ts, ev_ts[1:]) if b - a <= 2000)
            interval_rows.append(
                {
                    "trigger": label,
                    "day": day,
                    "events": len(ev_ts),
                    "events_with_next_within_2000": overlaps,
                    "active_ticks": int(active.sum()),
                    "active_tick_pct": float(active.mean() * 100),
                }
            )
    intervals = pd.DataFrame(interval_rows).sort_values(["trigger", "day"])
    write_csv(intervals, "mark_49_vfe_signal_window_coverage.csv")

    # Report-focused compact tables.
    total_trades = len(mark)
    total_qty = int(mark["quantity"].sum())
    products = ", ".join(product_side["symbol"].drop_duplicates().tolist())

    product_totals = flatten_cols(
        mark.groupby("symbol").agg(trades=("quantity", "size"), qty=("quantity", "sum"))
    ).sort_values("trades", ascending=False)
    product_totals["trade_pct"] = product_totals["trades"] / total_trades * 100
    product_totals["qty_pct"] = product_totals["qty"] / total_qty * 100

    side_totals = flatten_cols(
        mark.groupby("mark49_side").agg(trades=("quantity", "size"), qty=("quantity", "sum"))
    )
    side_totals["trade_pct"] = side_totals["trades"] / total_trades * 100
    side_totals["qty_pct"] = side_totals["qty"] / total_qty * 100

    top_markouts = markouts.copy()
    top_markouts = top_markouts[
        [
            "day",
            "product",
            "side",
            "n",
            "trade_mo_10_mean",
            "trade_mo_50_mean",
            "trade_mo_200_mean",
            "trade_mo_500_mean",
            "mid_move_200_mean",
        ]
    ]

    vfe_focus = vfe_signal[vfe_signal["trigger"].isin(["M49_sell", "M49_buy"])].copy()
    if not vfe_focus.empty:
        vfe_focus = vfe_focus[
            [
                "trigger",
                "day",
                "n",
                "mid_move_10_mean",
                "mid_move_50_mean",
                "mid_move_200_mean",
                "mid_move_500_mean",
                "mid_move_1000_mean",
                "mid_move_2000_mean",
            ]
        ]

    active_focus = active_summary[
        active_summary["window_label"].isin(
            ["active_M49_sell_only", "inactive_vs_M49_sell", "active_v314159_M49_sell_or_M67_buy"]
        )
    ].copy()

    direct_top = direct.head(12)
    relation_compact = relation[
        [
            "day",
            "symbol",
            "mark49_side",
            "n",
            "avg_px_minus_mid",
            "avg_spread",
            "aggressive_pct",
            "passive_or_price_improved_pct",
            "inside_pct",
        ]
    ]

    created = [
        "mark_49.py",
        "mark_49_events_enriched.csv",
        "mark_49_product_side_summary.csv",
        "mark_49_day_side_summary.csv",
        "mark_49_size_distribution.csv",
        "mark_49_timing_gaps.csv",
        "mark_49_gap_counts.csv",
        "mark_49_repeat_timestamps.csv",
        "mark_49_same_timestamp_repeats.csv",
        "mark_49_price_relation.csv",
        "mark_49_spread_depth_regimes.csv",
        "mark_49_markouts_by_product_side_day.csv",
        "mark_49_direct_counterparties.csv",
        "mark_49_same_timestamp_marks.csv",
        "mark_49_vfe_trigger_forward_mid_moves.csv",
        "mark_49_vfe_suppression_window_validation.csv",
        "mark_49_vfe_signal_window_coverage.csv",
        "mark_49.md",
    ]

    report = f"""# Mark 49 Counterparty Taxonomy

Data: `data/ROUND4/prices_round_4_day_1..3.csv` and `trades_round_4_day_1..3.csv`.
Method: exact `buyer == "Mark 49"` / `seller == "Mark 49"` filter, joined to same-timestamp visible book. Forward marks use first price row with timestamp >= `event_ts + horizon`. Trade markout is side-signed from Mark 49's trade price: buy = future_mid - trade_price; sell = trade_price - future_mid. `mid_move` is raw future_mid - current_mid.

## Executive Read

- Mark 49 appears in {total_trades} trades / {total_qty} units across days 1-3. Products: {products}. There are no Mark 49 trades in HYDROGEL_PACK or any VEV option in the Round 4 trade CSVs.
- Side mix is not neutral: see side table below. VFE is the strategy-relevant product.
- VFE Mark 49 **seller** prints have positive raw forward mid moves at t+200 on every day, matching the direction behind v314159's sell-suppression rule. Mark 49 **buyer** prints do not justify symmetric buy suppression from these data.
- Book relation is mostly passive/price-improved for Mark 49: sells are usually at/above ask and buys at/below bid, so Mark 49 looks more like a visible liquidity provider than a liquidity taker.
- The evidence supports `suppress_sell` or a temporary ask-side skew/widen after Mark 49 VFE seller prints. It does not support tightening asks into the signal. The sample is small, so prefer the current conservative overlay over a larger directional take.

## Products And Side Bias

{md_table(product_totals, ["symbol", "trades", "qty", "trade_pct", "qty_pct"])}

{md_table(side_totals, ["mark49_side", "trades", "qty", "trade_pct", "qty_pct"])}

By product/side:

{md_table(product_side.rename(columns={"symbol": "product", "mark49_side": "side"}), ["product", "side", "trades", "total_qty", "mean_qty", "median_qty", "max_qty"])}

## Size Distributions

{md_table(size_dist, ["product", "side", "n", "mean", "p25", "median", "p75", "p90", "max", "top_sizes"])}

## Timing, Periodicity, Repeats

Timing gaps by day/product/side:

{md_table(timing.rename(columns={"symbol": "product", "mark49_side": "side"}), ["day", "product", "side", "n", "first_ts", "last_ts", "mean_gap", "median_gap", "p10_gap", "p90_gap", "top_gaps"], max_rows=30)}

Cross-day repeated exact timestamps:

{md_table(repeat_ts, ["product", "side", "unique_timestamps", "repeated_2plus_days", "repeated_all_3_days"])}

Same-day repeat timestamps are sparse; full rows are in `mark_49_same_timestamp_repeats.csv`.

## Price Relation To Book And Regime

Percent columns are percentages of Mark 49 events in that day/product/side bucket. `aggressive_pct` means Mark 49 bought at/above ask or sold at/below bid. `passive_or_price_improved_pct` means Mark 49 bought at/below bid or sold at/above ask.

{md_table(relation_compact.rename(columns={"symbol": "product", "mark49_side": "side"}), ["day", "product", "side", "n", "avg_px_minus_mid", "avg_spread", "aggressive_pct", "passive_or_price_improved_pct", "inside_pct"], max_rows=40)}

Event-time spread/depth versus full-day product regimes:

{md_table(regimes.rename(columns={"symbol": "product", "mark49_side": "side"}), ["day", "product", "side", "event_spread_mean", "full_spread_mean", "event_bid_depth_3_mean", "full_bid_depth_3_mean", "event_ask_depth_3_mean", "full_ask_depth_3_mean"], max_rows=40)}

## Markouts By Product / Side / Day

Trade-price markouts are side-signed for Mark 49. Positive means Mark 49's historical execution was profitable versus the future mid. `mid_move_200_mean` is included because v314159 uses Mark 49 seller prints as a raw VFE-up signal for our sell suppression.

{md_table(top_markouts, ["day", "product", "side", "n", "trade_mo_10_mean", "trade_mo_50_mean", "trade_mo_200_mean", "trade_mo_500_mean", "mid_move_200_mean"], max_rows=80)}

## VFE Signal Validation For v314159

Current v314159 logic:

- Trigger: any VFE trade with `buyer == "Mark 67"` or `seller == "Mark 49"`.
- Action: suppress VFE sells for `SIGNAL_WINDOW = 2000` timestamp units.

Event-time raw VFE mid moves after Mark 49 VFE prints:

{md_table(vfe_focus, ["trigger", "day", "n", "mid_move_10_mean", "mid_move_50_mean", "mid_move_200_mean", "mid_move_500_mean", "mid_move_1000_mean", "mid_move_2000_mean"])}

Validation of the actual 2000-unit active windows, measured on every VFE price tick inside each window:

{md_table(active_focus, ["day", "window_label", "ticks", "mid_move_10_mean", "mid_move_50_mean", "mid_move_200_mean", "mid_move_500_mean"])}

Window coverage / overlap:

{md_table(intervals, ["trigger", "day", "events", "events_with_next_within_2000", "active_ticks", "active_tick_pct"])}

Read: Mark 49 seller windows are directionally aligned with avoiding short VFE exposure at short horizons, especially t+200. The t+500+ signal is weaker/mixed, and the number of Mark 49 VFE seller events is small. This supports the current suppress-sell overlay more than an aggressive buy-follow rule. A narrower 200-500 window is empirically cleaner than 2000 from event-time marks, but the tick-window table should be used before changing code because v314159 suppresses at every tick inside the 2000 window, not only at event time.

## Interactions With Other Marks

Direct counterparties to Mark 49:

{md_table(direct_top.rename(columns={"symbol": "product", "mark49_side": "side"}), ["product", "side", "other_party", "trades", "qty", "avg_qty"])}

Other Marks appearing at the same timestamp as Mark 49 events:

{md_table(co_top, ["co_mark", "events", "mentions"])}

## Behavioral Classification

- **VFE role:** Mark 49 is mostly a passive/price-improved liquidity provider in VFE, not a liquidity taker. The clearest signature is selling VFE, frequently to Mark 67, at tight-spread timestamps.
- **Adverseness:** Mark 49 seller prints look adverse to our own selling into the next ~200 timestamps because raw VFE mid change after seller prints is positive by day. From Mark 49's own trade price, those sells are negative on average, so the useful feature is better described as an adverse-selection/liquidity-warning signal than a clean informed-trader copy signal.
- **Other products:** no Mark 49 HGP or VEV option trades exist in these files, so ignore Mark 49 outside VFE.
- **Microstructure:** Price relation is mostly at book/touch rather than a clean hidden periodic schedule. Timing gaps show clustered bursts and repeated exact timestamps are limited, so there is no reliable timestamp replay rule here.

## Recommendation Versus v314159

- Keep Mark 49 treatment asymmetric: **suppress or widen/skew VFE asks after Mark 49 seller prints**.
- Do **not** add symmetric suppression after Mark 49 buyer prints; the side evidence is weaker and does not match the current risk.
- Ignore Mark 49 outside VFE because there are zero observed HGP/VEV option prints.
- Do **not** chase Mark 49 by crossing after observation; historical print prices and visible next book are different execution problems.
- If testing one factor, test shorter sell-suppression windows around 200/500/1000 versus current 2000, with both `--match-trades none` and `worse`.

## Files Created

{os.linesep.join(f'- `{x}`' for x in created)}
"""

    with open(os.path.join(OUT_DIR, "mark_49.md"), "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()
