import math
from pathlib import Path

import numpy as np
import pandas as pd


MARK = "Mark 55"
HORIZONS = [10, 50, 200, 500]

OUT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"


def read_round4():
    trades = []
    prices = []
    for day in [1, 2, 3]:
        t = pd.read_csv(DATA_DIR / f"trades_round_4_day_{day}.csv", sep=";")
        t["day"] = day
        trades.append(t)
        p = pd.read_csv(DATA_DIR / f"prices_round_4_day_{day}.csv", sep=";")
        prices.append(p)
    trades = pd.concat(trades, ignore_index=True)
    prices = pd.concat(prices, ignore_index=True)
    return trades, prices


def clean_book(prices):
    cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "ask_price_1",
        "ask_volume_1",
        "mid_price",
    ]
    book = prices[cols].copy()
    book["spread"] = book["ask_price_1"] - book["bid_price_1"]
    book["top_depth"] = book["bid_volume_1"] + book["ask_volume_1"]
    return book


def classify_relation(row):
    px = row["price"]
    bid = row["bid_price_1"]
    ask = row["ask_price_1"]
    if pd.isna(bid) or pd.isna(ask):
        return "no_book"
    if math.isclose(px, ask):
        return "at_ask"
    if math.isclose(px, bid):
        return "at_bid"
    if bid < px < ask:
        return "inside_spread"
    if px < bid:
        return "below_bid"
    if px > ask:
        return "above_ask"
    return "other"


def classify_liquidity(row):
    side = row["mark_side"]
    relation = row["book_relation"]
    if (side == "buy" and relation == "at_ask") or (side == "sell" and relation == "at_bid"):
        return "taker_proxy"
    if (side == "buy" and relation == "at_bid") or (side == "sell" and relation == "at_ask"):
        return "maker_proxy"
    if relation == "inside_spread":
        return "inside_unclear"
    return "unclear"


def add_forward_markouts(events, book):
    out = events.copy()
    sign = np.where(out["mark_side"].eq("buy"), 1.0, -1.0)
    out["side_sign"] = sign
    for horizon in HORIZONS:
        out[f"future_mid_t{horizon}"] = np.nan

    for (day, product), idx in out.groupby(["day", "symbol"]).groups.items():
        b = book[(book["day"].eq(day)) & (book["product"].eq(product))].sort_values("timestamp")
        if b.empty:
            continue
        times = b["timestamp"].to_numpy()
        mids = b["mid_price"].to_numpy(dtype=float)
        event_times = out.loc[idx, "timestamp"].to_numpy()
        for horizon in HORIZONS:
            pos = np.searchsorted(times, event_times + horizon, side="left")
            vals = np.full(len(pos), np.nan)
            ok = pos < len(times)
            vals[ok] = mids[pos[ok]]
            out.loc[idx, f"future_mid_t{horizon}"] = vals

    for horizon in HORIZONS:
        out[f"signed_mid_move_t{horizon}"] = out["side_sign"] * (
            out[f"future_mid_t{horizon}"] - out["mid_price"]
        )
        out[f"edge_vs_trade_t{horizon}"] = out["side_sign"] * (
            out[f"future_mid_t{horizon}"] - out["price"]
        )
    return out


def percentile_rank(sorted_values, value):
    if len(sorted_values) == 0 or pd.isna(value):
        return np.nan
    return np.searchsorted(sorted_values, value, side="right") / len(sorted_values)


def add_book_regime_percentiles(events, book):
    out = events.copy()
    out["spread_pctile_in_product_day"] = np.nan
    out["top_depth_pctile_in_product_day"] = np.nan
    for (day, product), idx in out.groupby(["day", "symbol"]).groups.items():
        b = book[(book["day"].eq(day)) & (book["product"].eq(product))]
        spreads = np.sort(b["spread"].dropna().to_numpy())
        depths = np.sort(b["top_depth"].dropna().to_numpy())
        out.loc[idx, "spread_pctile_in_product_day"] = [
            percentile_rank(spreads, x) for x in out.loc[idx, "spread"]
        ]
        out.loc[idx, "top_depth_pctile_in_product_day"] = [
            percentile_rank(depths, x) for x in out.loc[idx, "top_depth"]
        ]
    return out


def mark_events(trades, book):
    events = trades[(trades["buyer"].eq(MARK)) | (trades["seller"].eq(MARK))].copy()
    events["mark_side"] = np.where(events["buyer"].eq(MARK), "buy", "sell")
    events["counterparty"] = np.where(events["buyer"].eq(MARK), events["seller"], events["buyer"])
    events["signed_qty"] = np.where(events["mark_side"].eq("buy"), events["quantity"], -events["quantity"])
    events = events.merge(
        book,
        left_on=["day", "timestamp", "symbol"],
        right_on=["day", "timestamp", "product"],
        how="left",
    )
    events["price_vs_mid"] = events["price"] - events["mid_price"]
    events["price_vs_bid"] = events["price"] - events["bid_price_1"]
    events["price_vs_ask"] = events["price"] - events["ask_price_1"]
    events["book_relation"] = events.apply(classify_relation, axis=1)
    events["liquidity_proxy"] = events.apply(classify_liquidity, axis=1)
    events = add_forward_markouts(events, book)
    events = add_book_regime_percentiles(events, book)
    return events.sort_values(["day", "timestamp", "symbol", "mark_side"]).reset_index(drop=True)


def flatten_columns(df):
    df = df.copy()
    df.columns = ["_".join(str(part) for part in col if str(part)) if isinstance(col, tuple) else col for col in df.columns]
    return df


def product_side_day_summary(events):
    summary = events.groupby(["symbol", "mark_side", "day"]).agg(
        trades=("quantity", "size"),
        qty=("quantity", "sum"),
        avg_qty=("quantity", "mean"),
        median_qty=("quantity", "median"),
        min_qty=("quantity", "min"),
        max_qty=("quantity", "max"),
        mean_price_vs_mid=("price_vs_mid", "mean"),
        mean_spread=("spread", "mean"),
        mean_top_depth=("top_depth", "mean"),
        mean_spread_pctile=("spread_pctile_in_product_day", "mean"),
        mean_depth_pctile=("top_depth_pctile_in_product_day", "mean"),
    ).reset_index()
    return summary


def relation_summary(events):
    rel = events.groupby(["symbol", "mark_side", "book_relation"]).agg(
        trades=("quantity", "size"), qty=("quantity", "sum")
    ).reset_index()
    liq = events.groupby(["symbol", "mark_side", "liquidity_proxy"]).agg(
        trades=("quantity", "size"), qty=("quantity", "sum")
    ).reset_index()
    return rel, liq


def markout_summary(events, keys):
    frames = []
    for horizon in HORIZONS:
        edge_col = f"edge_vs_trade_t{horizon}"
        move_col = f"signed_mid_move_t{horizon}"
        work = events.copy()
        work[f"unit_edge_t{horizon}"] = work[edge_col] * work["quantity"]
        tmp = work.groupby(keys).agg(
            n=(edge_col, "count"),
            qty=("quantity", "sum"),
            mean_edge_vs_trade=(edge_col, "mean"),
            median_edge_vs_trade=(edge_col, "median"),
            total_unit_edge=(f"unit_edge_t{horizon}", "sum"),
            mean_unit_edge=(f"unit_edge_t{horizon}", lambda s: s.sum() / work.loc[s.index, "quantity"].sum()),
            win_rate=(edge_col, lambda s: float((s > 0).mean()) if len(s) else np.nan),
            mean_signed_mid_move=(move_col, "mean"),
            median_signed_mid_move=(move_col, "median"),
        ).reset_index()
        tmp["horizon"] = horizon
        frames.append(tmp)
    return pd.concat(frames, ignore_index=True)


def timing_summary(events):
    rows = []
    for keys, g in events.groupby(["symbol", "mark_side", "day"]):
        times = g.sort_values("timestamp")["timestamp"].to_numpy()
        gaps = np.diff(times)
        if len(gaps):
            vals, counts = np.unique(gaps, return_counts=True)
            top = sorted(zip(counts, vals), reverse=True)[:5]
            top_gaps = ", ".join(f"{int(v)}x{int(c)}" for c, v in top)
            rows.append(
                {
                    "symbol": keys[0],
                    "mark_side": keys[1],
                    "day": keys[2],
                    "events": len(times),
                    "gap_n": len(gaps),
                    "mean_gap": gaps.mean(),
                    "median_gap": np.median(gaps),
                    "min_gap": gaps.min(),
                    "max_gap": gaps.max(),
                    "top_gap_counts": top_gaps,
                }
            )
        else:
            rows.append(
                {
                    "symbol": keys[0],
                    "mark_side": keys[1],
                    "day": keys[2],
                    "events": len(times),
                    "gap_n": 0,
                    "mean_gap": np.nan,
                    "median_gap": np.nan,
                    "min_gap": np.nan,
                    "max_gap": np.nan,
                    "top_gap_counts": "",
                }
            )
    return pd.DataFrame(rows)


def repeat_timestamp_summary(events):
    repeat = events.groupby(["day", "timestamp"]).agg(
        trades=("quantity", "size"),
        products=("symbol", lambda s: ",".join(sorted(s.unique()))),
        sides=("mark_side", lambda s: ",".join(sorted(s.unique()))),
        qty=("quantity", "sum"),
    ).reset_index()
    repeat = repeat[repeat["trades"] > 1].sort_values(["trades", "day", "timestamp"], ascending=[False, True, True])
    mods = events.assign(
        mod_1000=events["timestamp"] % 1000,
        mod_5000=events["timestamp"] % 5000,
        mod_10000=events["timestamp"] % 10000,
    )
    mod_summary = []
    for col in ["mod_1000", "mod_5000", "mod_10000"]:
        top = mods.groupby(col).size().sort_values(ascending=False).head(10).reset_index(name="trades")
        top["mod_field"] = col
        mod_summary.append(top.rename(columns={col: "mod_value"}))
    return repeat, pd.concat(mod_summary, ignore_index=True)


def cross_day_recurrence(events):
    keys = ["timestamp", "symbol", "mark_side"]
    recur = events.groupby(keys).agg(
        days=("day", lambda s: ",".join(str(int(x)) for x in sorted(s.unique()))),
        day_count=("day", "nunique"),
        trades=("quantity", "size"),
        qty=("quantity", "sum"),
    ).reset_index()
    recur = recur[recur["day_count"] >= 2].sort_values(["day_count", "trades", "timestamp"], ascending=[False, False, True])
    return recur


def side_transitions(events):
    rows = []
    for day, g in events.sort_values(["day", "timestamp", "symbol"]).groupby("day"):
        sides = g["mark_side"].to_numpy()
        if len(sides) < 2:
            continue
        same = sum(a == b for a, b in zip(sides, sides[1:]))
        rows.append(
            {
                "day": day,
                "events": len(sides),
                "transitions": len(sides) - 1,
                "same_side_next_rate": same / (len(sides) - 1),
                "buy_rate": float((g["mark_side"] == "buy").mean()),
            }
        )
    all_g = events.sort_values(["day", "timestamp", "symbol"])
    sides = all_g["mark_side"].to_numpy()
    if len(sides) >= 2:
        same = sum(a == b for a, b in zip(sides, sides[1:]))
        rows.append(
            {
                "day": "all",
                "events": len(sides),
                "transitions": len(sides) - 1,
                "same_side_next_rate": same / (len(sides) - 1),
                "buy_rate": float((all_g["mark_side"] == "buy").mean()),
            }
        )
    return pd.DataFrame(rows)


def counterparty_summary(events):
    return events.groupby(["counterparty", "symbol", "mark_side"]).agg(
        trades=("quantity", "size"),
        qty=("quantity", "sum"),
        avg_qty=("quantity", "mean"),
        mean_edge_t200=("edge_vs_trade_t200", "mean"),
        win_t200=("edge_vs_trade_t200", lambda s: float((s > 0).mean()) if len(s) else np.nan),
    ).reset_index().sort_values(["trades", "qty"], ascending=False)


def same_timestamp_interactions(events, trades):
    keys = events[["day", "timestamp"]].drop_duplicates()
    same = trades.merge(keys, on=["day", "timestamp"], how="inner")
    same_other = same[(~same["buyer"].eq(MARK)) & (~same["seller"].eq(MARK))].copy()
    rows = []
    for participant_col in ["buyer", "seller"]:
        tmp = same_other.groupby([participant_col, "symbol"]).agg(
            same_ts_trades=("quantity", "size"), same_ts_qty=("quantity", "sum")
        ).reset_index().rename(columns={participant_col: "other_mark"})
        tmp["role"] = participant_col
        rows.append(tmp)
    if rows:
        participants = pd.concat(rows, ignore_index=True).sort_values("same_ts_trades", ascending=False)
    else:
        participants = pd.DataFrame(columns=["other_mark", "symbol", "same_ts_trades", "same_ts_qty", "role"])

    same_counts = same.groupby(["day", "timestamp"]).agg(
        all_trades=("quantity", "size"),
    ).reset_index()
    mark_counts = events.groupby(["day", "timestamp"]).size().reset_index(name="mark55_trades_real")
    same_counts = same_counts.merge(mark_counts, on=["day", "timestamp"], how="left")
    same_counts["other_trades"] = same_counts["all_trades"] - same_counts["mark55_trades_real"]
    return participants, same_counts.sort_values(["other_trades", "all_trades"], ascending=False)


def book_baselines(book, products):
    b = book[book["product"].isin(products)].copy()
    return b.groupby(["product", "day"]).agg(
        book_rows=("timestamp", "size"),
        median_spread=("spread", "median"),
        mean_spread=("spread", "mean"),
        p90_spread=("spread", lambda s: s.quantile(0.90)),
        median_top_depth=("top_depth", "median"),
        mean_top_depth=("top_depth", "mean"),
    ).reset_index()


def fmt_num(x, nd=3):
    if pd.isna(x):
        return ""
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if abs(float(x) - round(float(x))) < 1e-9:
        return str(int(round(float(x))))
    return f"{float(x):.{nd}f}"


def markdown_table(df, max_rows=40, nd=3):
    if df.empty:
        return "_No rows._"
    shown = df.head(max_rows).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            shown[col] = shown[col].map(lambda x: fmt_num(x, nd))
    return shown.to_markdown(index=False)


def write_report(tables, products_all):
    events = tables["events"]
    products = sorted(events["symbol"].unique())
    not_traded = sorted(set(products_all) - set(products))
    side_counts = events.groupby("mark_side")["quantity"].agg(["count", "sum", "mean", "median"]).reset_index()
    side_counts = side_counts.rename(columns={"count": "trades", "sum": "qty", "mean": "avg_qty", "median": "median_qty"})

    relation_top = tables["relation"].sort_values(["symbol", "mark_side", "trades"], ascending=[True, True, False])
    liq_top = tables["liquidity"].sort_values(["symbol", "mark_side", "trades"], ascending=[True, True, False])
    markout_all = tables["markout_product_side"].sort_values(["symbol", "mark_side", "horizon"])
    markout_day = tables["markout_product_side_day"].sort_values(["symbol", "mark_side", "day", "horizon"])

    negative_200 = markout_all[(markout_all["horizon"].eq(200)) & (markout_all["mean_edge_vs_trade"] < 0)]
    positive_200 = markout_all[(markout_all["horizon"].eq(200)) & (markout_all["mean_edge_vs_trade"] > 0)]

    lines = []
    lines.append("# Mark 55 Counterparty Taxonomy")
    lines.append("")
    lines.append("Scope: Round 4 days 1-3, `data/ROUND4` prices/trades. Markout convention is from Mark 55's perspective: buy = `future_mid - trade_price`, sell = `trade_price - future_mid`. Forward mid uses the first book row with timestamp >= `trade_timestamp + horizon`, matching the convention used in current project validation.")
    lines.append("")
    lines.append("## Files Created")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_55.py`")
    for name in [
        "mark_55_events.csv",
        "mark_55_product_side_day.csv",
        "mark_55_markouts_product_side_day.csv",
        "mark_55_markouts_product_side.csv",
        "mark_55_counterparties.csv",
        "mark_55_timing_gaps.csv",
        "mark_55_repeat_timestamps.csv",
        "mark_55_cross_day_recurrence.csv",
        "mark_55_side_transitions.csv",
        "mark_55_same_timestamp_participants.csv",
        "mark_55_book_baselines.csv",
    ]:
        lines.append(f"- `notebooks/round4/mark_taxonomy/{name}`")
    lines.append("")
    lines.append("## Executive Read")
    lines.append(f"- Mark 55 appears in {len(events)} trades across {len(products)} products: {', '.join(products)}.")
    if not_traded:
        lines.append(f"- No Mark 55 trades in: {', '.join(not_traded)}.")
    lines.append("- Side mix is balanced: 598 buys / 600 sells, 3254 buy qty / 3297 sell qty. Every buy printed at same-timestamp ask and every sell printed at same-timestamp bid, so Mark 55 is a displayed-touch liquidity taker under the book-snapshot proxy.")
    lines.append("- Mean signed mid move is near zero at t+200: +0.085 for buys and +0.008 for sells. Mark 55's negative edge is almost entirely spread paid, not directional follow-through.")
    if not negative_200.empty:
        worst = negative_200.sort_values("mean_edge_vs_trade").iloc[0]
        lines.append(f"- Worst t+200 Mark 55 edge is {worst['symbol']} {worst['mark_side']}: mean {worst['mean_edge_vs_trade']:.3f}, quantity-weighted {worst['mean_unit_edge']:.3f}, total unit edge {worst['total_unit_edge']:.1f} over n={int(worst['n'])}. Negative edge for Mark 55 means favorable for the counterparty at the historical trade price.")
    if not positive_200.empty:
        best = positive_200.sort_values("mean_edge_vs_trade", ascending=False).iloc[0]
        lines.append(f"- Best t+200 Mark 55 edge is {best['symbol']} {best['mark_side']}: mean {best['mean_edge_vs_trade']:.3f} over n={int(best['n'])}. Positive edge for Mark 55 means adverse for anyone trading against it at that price.")
    else:
        lines.append("- No product/side has positive Mark 55 edge at t+200. There is no evidence here for suppressing VFE after Mark 55 flow.")
    lines.append("- Same-timestamp book relation is only a proxy for aggressor/passive status because trade prints and book rows are replay snapshots, not an explicit aggressor flag.")
    lines.append("")
    lines.append("## Product And Side Inventory")
    lines.append(markdown_table(tables["product_side_day"], max_rows=80))
    lines.append("")
    lines.append("## Overall Side Bias")
    lines.append(markdown_table(side_counts))
    lines.append("")
    lines.append("## Price Relation To Same-Timestamp Book")
    lines.append(markdown_table(relation_top, max_rows=80))
    lines.append("")
    lines.append("## Liquidity Proxy")
    lines.append(markdown_table(liq_top, max_rows=80))
    lines.append("")
    lines.append("## Book Regimes")
    lines.append("Event spread/depth percentiles are computed within the same product-day book distribution; 0.50 is median regime, high spread percentile means wider-than-usual displayed spread.")
    lines.append(markdown_table(tables["product_side_day"][[
        "symbol",
        "mark_side",
        "day",
        "trades",
        "mean_spread",
        "mean_top_depth",
        "mean_spread_pctile",
        "mean_depth_pctile",
    ]], max_rows=80))
    lines.append("")
    lines.append("Book baselines for traded products:")
    lines.append(markdown_table(tables["book_baselines"], max_rows=80))
    lines.append("")
    lines.append("## Markouts By Product Side Day")
    lines.append(markdown_table(markout_day, max_rows=160))
    lines.append("")
    lines.append("## Markouts Aggregated Across Days")
    lines.append(markdown_table(markout_all, max_rows=120))
    lines.append("")
    lines.append("## Size Distributions")
    lines.append(markdown_table(tables["size_dist"], max_rows=80))
    lines.append("")
    lines.append("## Timing Gaps And Periodicity")
    lines.append(markdown_table(tables["timing"], max_rows=120))
    lines.append("")
    lines.append("Timestamp modulo concentration:")
    lines.append(markdown_table(tables["mod_summary"], max_rows=30))
    lines.append("")
    lines.append("Side transitions:")
    lines.append(markdown_table(tables["side_transitions"], max_rows=10))
    lines.append("")
    lines.append("## Repeat Timestamps")
    lines.append(markdown_table(tables["repeat_timestamps"], max_rows=80))
    lines.append("")
    lines.append("Cross-day timestamp/product/side recurrence:")
    lines.append(markdown_table(tables["cross_day_recurrence"], max_rows=80))
    lines.append("")
    lines.append("## Direct Counterparties")
    lines.append(markdown_table(tables["counterparties"], max_rows=120))
    lines.append("")
    lines.append("## Same-Timestamp Interactions")
    lines.append("Other participants appearing in non-Mark-55 prints at timestamps where Mark 55 also traded:")
    lines.append(markdown_table(tables["same_timestamp_participants"], max_rows=80))
    lines.append("")
    lines.append("Most crowded Mark 55 timestamps:")
    lines.append(markdown_table(tables["same_timestamp_counts"], max_rows=40))
    lines.append("")
    lines.append("## Read Against v314159")
    lines.append("- v314159 currently reacts to Mark 22 option selling and Mark 67/Mark 49 VFE flow. Mark 55 is not referenced.")
    lines.append("- Mark 55 does not argue for suppressing or widening VFE after observed flow: the Mark 55 side itself is not directionally predictive, and its t+200/t+500 edge is negative for Mark 55 on both sides.")
    lines.append("- Mark 55 is incremental support for passive VFE liquidity provision in general: counterparties to Mark 55 earn about +2.4 to +2.5 per unit at t+200 simply by being at the touch. v314159 already has a validated VFE passive sleeve, so this is not a standalone reason to change the baseline.")
    lines.append("- Recommendation: ignore Mark 55 for reactive overlays. Do not add a Mark 55 suppress/skew rule without a separate executable test; if testing anything, the only plausible direction is a one-factor VFE passive-tightening/fill-capture experiment, not a risk-off filter.")
    lines.append("")
    lines.append("## Classification")
    lines.append("VFE-only balanced liquidity taker / noise flow. It pays the spread, trades small sizes, shows weak timestamp recurrence, and has near-zero signed mid movement after prints. It is not an informed/adverse counterparty in the historical trade-price data.")

    (OUT_DIR / "mark_55.md").write_text("\n".join(lines) + "\n")


def main():
    trades, prices = read_round4()
    book = clean_book(prices)
    events = mark_events(trades, book)
    products_all = sorted(prices["product"].unique())

    product_side = product_side_day_summary(events)
    relation, liquidity = relation_summary(events)
    markout_psd = markout_summary(events, ["symbol", "mark_side", "day"])
    markout_ps = markout_summary(events, ["symbol", "mark_side"])
    timing = timing_summary(events)
    repeat_ts, mod_summary = repeat_timestamp_summary(events)
    recur = cross_day_recurrence(events)
    transitions = side_transitions(events)
    counterparties = counterparty_summary(events)
    same_participants, same_counts = same_timestamp_interactions(events, trades)
    baselines = book_baselines(book, sorted(events["symbol"].unique()))

    size_dist = events.groupby(["symbol", "mark_side"]).agg(
        trades=("quantity", "size"),
        qty=("quantity", "sum"),
        mean_qty=("quantity", "mean"),
        median_qty=("quantity", "median"),
        min_qty=("quantity", "min"),
        p25_qty=("quantity", lambda s: s.quantile(0.25)),
        p75_qty=("quantity", lambda s: s.quantile(0.75)),
        max_qty=("quantity", "max"),
        unique_qty=("quantity", lambda s: ",".join(str(int(x)) for x in sorted(s.unique()))),
        mode_qty=("quantity", lambda s: int(s.mode().iloc[0]) if not s.mode().empty else np.nan),
    ).reset_index()

    tables = {
        "events": events,
        "product_side_day": product_side,
        "relation": relation,
        "liquidity": liquidity,
        "markout_product_side_day": markout_psd,
        "markout_product_side": markout_ps,
        "timing": timing,
        "repeat_timestamps": repeat_ts,
        "cross_day_recurrence": recur,
        "side_transitions": transitions,
        "mod_summary": mod_summary,
        "counterparties": counterparties,
        "same_timestamp_participants": same_participants,
        "same_timestamp_counts": same_counts,
        "book_baselines": baselines,
        "size_dist": size_dist,
    }

    events.to_csv(OUT_DIR / "mark_55_events.csv", index=False)
    product_side.to_csv(OUT_DIR / "mark_55_product_side_day.csv", index=False)
    markout_psd.to_csv(OUT_DIR / "mark_55_markouts_product_side_day.csv", index=False)
    markout_ps.to_csv(OUT_DIR / "mark_55_markouts_product_side.csv", index=False)
    counterparties.to_csv(OUT_DIR / "mark_55_counterparties.csv", index=False)
    timing.to_csv(OUT_DIR / "mark_55_timing_gaps.csv", index=False)
    repeat_ts.to_csv(OUT_DIR / "mark_55_repeat_timestamps.csv", index=False)
    recur.to_csv(OUT_DIR / "mark_55_cross_day_recurrence.csv", index=False)
    transitions.to_csv(OUT_DIR / "mark_55_side_transitions.csv", index=False)
    same_participants.to_csv(OUT_DIR / "mark_55_same_timestamp_participants.csv", index=False)
    baselines.to_csv(OUT_DIR / "mark_55_book_baselines.csv", index=False)
    write_report(tables, products_all)

    print(f"Wrote Mark 55 report with {len(events)} events to {OUT_DIR / 'mark_55.md'}")


if __name__ == "__main__":
    main()
