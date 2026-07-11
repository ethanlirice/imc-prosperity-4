from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
MARK = "Mark 38"
HORIZONS = [10, 50, 200, 500]


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_prices():
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        if "day" not in df.columns:
            df["day"] = parse_day(path)
        frames.append(df)
    prices = pd.concat(frames, ignore_index=True)
    for col in ["bid_price_1", "ask_price_1", "mid_price", "timestamp"]:
        prices[col] = pd.to_numeric(prices[col], errors="coerce")
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    bid_vol_cols = [c for c in prices.columns if c.startswith("bid_volume_")]
    ask_vol_cols = [c for c in prices.columns if c.startswith("ask_volume_")]
    prices["bid_depth_3"] = prices[bid_vol_cols].fillna(0).sum(axis=1)
    prices["ask_depth_3"] = prices[ask_vol_cols].fillna(0).sum(axis=1)
    prices["total_depth_3"] = prices["bid_depth_3"] + prices["ask_depth_3"]
    return prices


def load_trades():
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        df["day"] = parse_day(path)
        frames.append(df)
    trades = pd.concat(frames, ignore_index=True)
    trades["timestamp"] = pd.to_numeric(trades["timestamp"], errors="coerce")
    trades["price"] = pd.to_numeric(trades["price"], errors="coerce")
    trades["quantity"] = pd.to_numeric(trades["quantity"], errors="coerce")
    return trades


def build_price_lookup(prices):
    lookup = {}
    for key, frame in prices.groupby(["day", "product"]):
        frame = frame.sort_values("timestamp").reset_index(drop=True)
        lookup[key] = {
            "ts": frame["timestamp"].to_numpy(),
            "mid": frame["mid_price"].to_numpy(),
            "frame": frame,
        }
    return lookup


def future_mid(price_lookup, day, product, timestamp, horizon):
    item = price_lookup.get((day, product))
    if item is None:
        return np.nan
    idx = np.searchsorted(item["ts"], timestamp + horizon, side="left")
    if idx >= len(item["ts"]):
        return np.nan
    return float(item["mid"][idx])


def exact_book(prices):
    cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "ask_price_1",
        "mid_price",
        "spread",
        "bid_depth_3",
        "ask_depth_3",
        "total_depth_3",
    ]
    return prices[cols].rename(columns={"product": "symbol"})


def build_events(trades, prices):
    mask = (trades["buyer"] == MARK) | (trades["seller"] == MARK)
    events = trades.loc[mask].copy()
    events["side"] = np.where(events["buyer"] == MARK, "buy", "sell")
    events["counterparty"] = np.where(
        events["buyer"] == MARK, events["seller"], events["buyer"]
    )
    events = events.merge(
        exact_book(prices), on=["day", "timestamp", "symbol"], how="left"
    )
    events["px_minus_mid"] = events["price"] - events["mid_price"]
    events["mark_price_adv_vs_mid"] = np.where(
        events["side"] == "buy",
        events["mid_price"] - events["price"],
        events["price"] - events["mid_price"],
    )
    events["px_vs_bid"] = events["price"] - events["bid_price_1"]
    events["px_vs_ask"] = events["price"] - events["ask_price_1"]
    events["at_or_through_best"] = np.where(
        events["side"] == "buy",
        events["price"] >= events["ask_price_1"],
        events["price"] <= events["bid_price_1"],
    )
    events["inside_spread"] = (
        (events["price"] > events["bid_price_1"])
        & (events["price"] < events["ask_price_1"])
    )

    lookup = build_price_lookup(prices)
    for h in HORIZONS:
        events["future_mid_t{}".format(h)] = [
            future_mid(lookup, row.day, row.symbol, row.timestamp, h)
            for row in events.itertuples(index=False)
        ]
        fcol = "future_mid_t{}".format(h)
        events["markout_trade_t{}".format(h)] = np.where(
            events["side"] == "buy",
            events[fcol] - events["price"],
            events["price"] - events[fcol],
        )
        events["markout_mid_t{}".format(h)] = np.where(
            events["side"] == "buy",
            events[fcol] - events["mid_price"],
            events["mid_price"] - events[fcol],
        )
    return events.sort_values(["day", "timestamp", "symbol", "side"]).reset_index(drop=True)


def summarize_markouts(events):
    agg = {
        "quantity": ["count", "sum", "mean", "median", "min", "max"],
        "price": ["mean"],
        "mid_price": ["mean"],
        "spread": ["mean", "median"],
        "mark_price_adv_vs_mid": ["mean", "median"],
        "at_or_through_best": ["mean"],
        "inside_spread": ["mean"],
        "total_depth_3": ["mean", "median"],
    }
    for h in HORIZONS:
        agg["markout_trade_t{}".format(h)] = ["mean", "median", "sum"]
        agg["markout_mid_t{}".format(h)] = ["mean", "median"]
    out = events.groupby(["symbol", "side", "day"]).agg(agg)
    out.columns = ["_".join(c).strip("_") for c in out.columns]
    return out.reset_index()


def product_side_summary(events):
    out = events.groupby(["symbol", "side"]).agg(
        trades=("quantity", "count"),
        qty_sum=("quantity", "sum"),
        qty_mean=("quantity", "mean"),
        qty_median=("quantity", "median"),
        qty_min=("quantity", "min"),
        qty_max=("quantity", "max"),
        px_adv_mid_mean=("mark_price_adv_vs_mid", "mean"),
        spread_mean=("spread", "mean"),
        at_or_through_best_pct=("at_or_through_best", "mean"),
        inside_spread_pct=("inside_spread", "mean"),
        t10_mean=("markout_trade_t10", "mean"),
        t50_mean=("markout_trade_t50", "mean"),
        t200_mean=("markout_trade_t200", "mean"),
        t500_mean=("markout_trade_t500", "mean"),
        t200_mid_mean=("markout_mid_t200", "mean"),
        t500_mid_mean=("markout_mid_t500", "mean"),
        t200_sum=("markout_trade_t200", "sum"),
    )
    return out.reset_index()


def timing_summary(events):
    rows = []
    for key, frame in events.sort_values("timestamp").groupby(["symbol", "side", "day"]):
        gaps = frame["timestamp"].diff().dropna()
        row = {
            "symbol": key[0],
            "side": key[1],
            "day": key[2],
            "events": len(frame),
            "first_ts": int(frame["timestamp"].min()),
            "last_ts": int(frame["timestamp"].max()),
            "repeat_ts_events": int(frame.duplicated("timestamp", keep=False).sum()),
            "unique_timestamps": int(frame["timestamp"].nunique()),
        }
        if len(gaps):
            row.update(
                {
                    "gap_mean": float(gaps.mean()),
                    "gap_median": float(gaps.median()),
                    "gap_min": float(gaps.min()),
                    "gap_p10": float(gaps.quantile(0.10)),
                    "gap_p90": float(gaps.quantile(0.90)),
                    "gap_max": float(gaps.max()),
                    "most_common_gap": int(gaps.value_counts().idxmax()),
                    "most_common_gap_count": int(gaps.value_counts().max()),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def repeat_timestamps(events):
    by_day = (
        events.groupby(["symbol", "side", "timestamp"])["day"]
        .agg(["nunique", lambda s: ",".join(str(int(x)) for x in sorted(set(s)))])
        .reset_index()
        .rename(columns={"nunique": "days_seen", "<lambda_0>": "days"})
    )
    by_day = by_day.sort_values(["days_seen", "symbol", "side", "timestamp"], ascending=[False, True, True, True])
    per_ts = (
        events.groupby(["symbol", "side", "day", "timestamp"])
        .agg(events=("quantity", "count"), qty_sum=("quantity", "sum"))
        .reset_index()
        .sort_values(["events", "qty_sum"], ascending=[False, False])
    )
    return by_day, per_ts


def counterparty_summary(events):
    out = events.groupby(["symbol", "side", "counterparty"]).agg(
        trades=("quantity", "count"),
        qty_sum=("quantity", "sum"),
        qty_mean=("quantity", "mean"),
        t200_mean=("markout_trade_t200", "mean"),
        t200_sum=("markout_trade_t200", "sum"),
        t500_mean=("markout_trade_t500", "mean"),
        first_ts=("timestamp", "min"),
        last_ts=("timestamp", "max"),
    )
    return out.reset_index().sort_values(["symbol", "side", "trades"], ascending=[True, True, False])


def regime_summary(events):
    rows = []
    for key, frame in events.groupby(["symbol", "side"]):
        spreads = frame["spread"]
        depth = frame["total_depth_3"]
        for name, mask in [
            ("spread_le_median", spreads <= spreads.median()),
            ("spread_gt_median", spreads > spreads.median()),
            ("depth_le_median", depth <= depth.median()),
            ("depth_gt_median", depth > depth.median()),
        ]:
            sub = frame.loc[mask]
            if len(sub) == 0:
                continue
            rows.append(
                {
                    "symbol": key[0],
                    "side": key[1],
                    "regime": name,
                    "trades": len(sub),
                    "spread_mean": sub["spread"].mean(),
                    "depth_mean": sub["total_depth_3"].mean(),
                    "px_adv_mid_mean": sub["mark_price_adv_vs_mid"].mean(),
                    "t200_mean": sub["markout_trade_t200"].mean(),
                    "t500_mean": sub["markout_trade_t500"].mean(),
                }
            )
    return pd.DataFrame(rows)


def interaction_windows(events, trades):
    others = trades.copy()
    rows = []
    for event in events.itertuples(index=False):
        same = others[
            (others["day"] == event.day)
            & (others["symbol"] == event.symbol)
            & (others["timestamp"] >= event.timestamp - 500)
            & (others["timestamp"] <= event.timestamp + 500)
        ]
        mark_cols = []
        for _, row in same.iterrows():
            for participant, side in [(row["buyer"], "buy"), (row["seller"], "sell")]:
                if participant == MARK:
                    continue
                if isinstance(participant, str) and participant:
                    mark_cols.append((participant, side))
        for participant, side in mark_cols:
            rows.append(
                {
                    "symbol": event.symbol,
                    "mark38_side": event.side,
                    "day": event.day,
                    "other_mark": participant,
                    "other_side": side,
                }
            )
    if not rows:
        return pd.DataFrame()
    raw = pd.DataFrame(rows)
    return (
        raw.groupby(["symbol", "mark38_side", "other_mark", "other_side"])
        .size()
        .reset_index(name="window_mentions")
        .sort_values(["symbol", "mark38_side", "window_mentions"], ascending=[True, True, False])
    )


def fmt(x, digits=3):
    if pd.isna(x):
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if abs(float(x) - int(float(x))) < 1e-9:
        return str(int(float(x)))
    return ("{:." + str(digits) + "f}").format(float(x))


def md_table(df, cols, max_rows=None, digits=3):
    if max_rows is not None:
        df = df.head(max_rows)
    rows = []
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(fmt(row[c], digits) for c in cols) + " |")
    return "\n".join(rows)


def write_report(events, ps, by_day, timing, repeats, repeated_events, cp, regimes, interactions):
    lines = []
    lines.append("# Mark 38 taxonomy")
    lines.append("")
    lines.append("Data: `data/ROUND4` days 1-3. Markouts are signed for Mark 38: buy = future mid - trade price, sell = trade price - future mid. Forward mid is the first price row at timestamp >= event timestamp + horizon.")
    lines.append("")
    lines.append("## Executive read")
    total = len(events)
    products = ", ".join(sorted(events["symbol"].unique()))
    main_events = events[events["symbol"].isin(["HYDROGEL_PACK", "VEV_4000"])]
    mark14_main = main_events[main_events["counterparty"] == "Mark 14"]
    lines.append("- Mark 38 appears only in `{}` with {} total prints: {} buys and {} sells.".format(
        products,
        total,
        int((events["side"] == "buy").sum()),
        int((events["side"] == "sell").sum()),
    ))
    lines.append("- {} / {} prints ({}%) are in HYDROGEL_PACK or VEV_4000; {} of those ({}%) are directly against Mark 14.".format(
        len(main_events),
        total,
        fmt(100.0 * len(main_events) / total, 1),
        len(mark14_main),
        fmt(100.0 * len(mark14_main) / max(1, len(main_events)), 1),
    ))
    hgp = ps[ps["symbol"] == "HYDROGEL_PACK"]
    v4000 = ps[ps["symbol"] == "VEV_4000"]
    if len(hgp):
        lines.append("- HYDROGEL_PACK t+200 mean markout by side is {}.".format(
            ", ".join("{} {}".format(r.side, fmt(r.t200_mean)) for r in hgp.itertuples(index=False))
        ))
    if len(v4000):
        lines.append("- VEV_4000 t+200 mean markout by side is {}.".format(
            ", ".join("{} {}".format(r.side, fmt(r.t200_mean)) for r in v4000.itertuples(index=False))
        ))
    main_mid = main_events.groupby(["symbol", "side"]).agg(t200_mid_mean=("markout_mid_t200", "mean")).reset_index()
    lines.append("- Current-mid t+200 markouts on the two real products are small: {}. The large negative trade-price edge is mostly spread paid at execution.".format(
        ", ".join("{} {} {}".format(r.symbol, r.side, fmt(r.t200_mid_mean)) for r in main_mid.itertuples(index=False))
    ))
    lines.append("- Interpretation: Mark 38 is a spread-paying liquidity taker/noise source, usually trading against Mark 14. Do not follow Mark 38 directionally.")
    lines.append("- Classification: liquidity taker / noise. Not a market maker, not informed in mid-price direction, and not adverse to passive contra quotes at the measured horizons.")
    lines.append("")

    lines.append("## Products, side bias, and markouts")
    show = ps.copy()
    show["at_or_through_best_pct"] *= 100.0
    show["inside_spread_pct"] *= 100.0
    lines.append(md_table(show, [
        "symbol", "side", "trades", "qty_sum", "qty_mean", "px_adv_mid_mean",
        "spread_mean", "at_or_through_best_pct", "inside_spread_pct",
        "t10_mean", "t50_mean", "t200_mean", "t500_mean", "t200_mid_mean",
        "t500_mid_mean", "t200_sum",
    ]))
    lines.append("")

    lines.append("## Product + side + day markouts")
    day_cols = ["symbol", "side", "day", "quantity_count", "quantity_sum", "quantity_mean", "spread_mean", "mark_price_adv_vs_mid_mean"]
    for h in HORIZONS:
        day_cols.append("markout_trade_t{}_mean".format(h))
    lines.append(md_table(by_day, day_cols))
    lines.append("")

    lines.append("## Timing gaps")
    lines.append(md_table(timing, [
        "symbol", "side", "day", "events", "first_ts", "last_ts", "unique_timestamps",
        "repeat_ts_events", "gap_median", "gap_p10", "gap_p90", "most_common_gap",
        "most_common_gap_count",
    ]))
    lines.append("")

    repeated_keys = repeats[repeats["days_seen"] > 1]
    lines.append("## Repeat timestamps")
    lines.append("- Timestamp-side keys recurring on multiple days: {}.".format(len(repeated_keys)))
    if len(repeated_keys):
        lines.append(md_table(repeated_keys, ["symbol", "side", "timestamp", "days_seen", "days"], max_rows=20))
    actual_bursts = repeated_events[repeated_events["events"] > 1]
    if len(actual_bursts):
        lines.append("- Largest same-day repeat bursts:")
        lines.append(md_table(actual_bursts, ["symbol", "side", "day", "timestamp", "events", "qty_sum"], max_rows=20))
    else:
        lines.append("- Same product/side/day repeated timestamp bursts: 0. Every Mark 38 product-side timestamp is a single print.")
    lines.append("")

    lines.append("## Counterparties")
    lines.append(md_table(cp, ["symbol", "side", "counterparty", "trades", "qty_sum", "qty_mean", "t200_mean", "t200_sum", "t500_mean", "first_ts", "last_ts"]))
    lines.append("")

    lines.append("## Spread and depth regimes")
    lines.append(md_table(regimes, ["symbol", "side", "regime", "trades", "spread_mean", "depth_mean", "px_adv_mid_mean", "t200_mean", "t500_mean"]))
    lines.append("")

    lines.append("## Nearby interaction windows")
    lines.append("Counts below are mentions of other participants in same product/day within +/-500 timestamp units of each Mark 38 event; they are not unique events.")
    lines.append(md_table(interactions, ["symbol", "mark38_side", "other_mark", "other_side", "window_mentions"], max_rows=40))
    lines.append("")

    lines.append("## Compare to v314159")
    lines.append("- v314159 already trades HYDROGEL_PACK with tight buy edge 4 and wide sell edge 12. Mark 38's HYDROGEL_PACK flow does not justify following buys/sells; it mainly says takers are paying the spread.")
    lines.append("- v314159's VEV_4000 deep-ITM module is built around structural fair and aggressive passive making. Mark 38's VEV_4000 prints support the value of being passive/contra at the touch, because Mark 38 loses about 10 points from trade price while current-mid t+200 is near flat.")
    lines.append("- Practical recommendation: ignore Mark 38 as a directional overlay. Do not suppress passive contra quotes because of Mark 38 alone. The only testable sleeve idea is a one-factor passive-tightening/capture experiment on HYDROGEL_PACK or VEV_4000, but only in the simulator and only if both `none` and `worse` improve.")
    lines.append("")

    lines.append("## Files created")
    for name in [
        "mark_38_analysis.py",
        "mark_38_events.csv",
        "mark_38_summary_by_product_side.csv",
        "mark_38_summary_by_product_side_day.csv",
        "mark_38_timing_gaps.csv",
        "mark_38_repeat_timestamps.csv",
        "mark_38_repeat_bursts.csv",
        "mark_38_counterparties.csv",
        "mark_38_regimes.csv",
        "mark_38_interactions.csv",
        "mark_38.md",
    ]:
        lines.append("- `{}`".format(name))
    lines.append("")
    (OUT_DIR / "mark_38.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    prices = load_prices()
    trades = load_trades()
    events = build_events(trades, prices)
    if len(events) == 0:
        raise RuntimeError("No Mark 38 events found")

    by_day = summarize_markouts(events)
    ps = product_side_summary(events)
    timing = timing_summary(events)
    repeats, repeated_events = repeat_timestamps(events)
    cp = counterparty_summary(events)
    regimes = regime_summary(events)
    interactions = interaction_windows(events, trades)

    events.to_csv(OUT_DIR / "mark_38_events.csv", index=False)
    ps.to_csv(OUT_DIR / "mark_38_summary_by_product_side.csv", index=False)
    by_day.to_csv(OUT_DIR / "mark_38_summary_by_product_side_day.csv", index=False)
    timing.to_csv(OUT_DIR / "mark_38_timing_gaps.csv", index=False)
    repeats.to_csv(OUT_DIR / "mark_38_repeat_timestamps.csv", index=False)
    repeated_events.to_csv(OUT_DIR / "mark_38_repeat_bursts.csv", index=False)
    cp.to_csv(OUT_DIR / "mark_38_counterparties.csv", index=False)
    regimes.to_csv(OUT_DIR / "mark_38_regimes.csv", index=False)
    interactions.to_csv(OUT_DIR / "mark_38_interactions.csv", index=False)
    write_report(events, ps, by_day, timing, repeats, repeated_events, cp, regimes, interactions)
    print("Wrote Mark 38 analysis files to {}".format(OUT_DIR))
    print(ps.to_string(index=False))


if __name__ == "__main__":
    main()
