"""
Empirical taxonomy for Round 4 counterparty Mark 22.

Inputs:
  data/ROUND4/prices_round_4_day_*.csv
  data/ROUND4/trades_round_4_day_*.csv
  strategies/round4/v314159.py for current option fair/vol replay

Outputs are confined to notebooks/round4/mark_taxonomy/mark_22.*.
"""
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "strategies" / "round4" / "v314159.py"
MARK = "Mark 22"
HORIZONS = (10, 50, 200, 500)
OPTION_PRODUCTS = (
    "VEV_4000", "VEV_4500", "VEV_5000", "VEV_5100", "VEV_5200",
    "VEV_5300", "VEV_5400", "VEV_5500", "VEV_6000", "VEV_6500",
)
STRIKES = {p: int(p.split("_")[1]) for p in OPTION_PRODUCTS}


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_model():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("v314159_mark22", MODEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_prices():
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        if "day" in df.columns:
            df = df.drop(columns=["day"])
        df["day"] = parse_day(path)
        frames.append(df)
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    prices["top_depth"] = prices["bid_volume_1"].fillna(0) + prices["ask_volume_1"].fillna(0).abs()
    prices["total_depth"] = 0
    for i in (1, 2, 3):
        prices["total_depth"] += prices[f"bid_volume_{i}"].fillna(0)
        prices["total_depth"] += prices[f"ask_volume_{i}"].fillna(0).abs()
    return prices


def load_trades():
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        df["day"] = parse_day(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def build_price_index(prices):
    idx = {}
    for key, g in prices.sort_values("timestamp").groupby(["day", "product"]):
        idx[key] = (
            g["timestamp"].to_numpy(dtype=np.int64),
            g["mid_price"].to_numpy(dtype=float),
        )
    return idx


def forward_mid(price_index, day, product, timestamp, horizon):
    ts, mids = price_index[(day, product)]
    i = int(np.searchsorted(ts, int(timestamp) + int(horizon), side="left"))
    if i >= len(ts):
        return np.nan
    return float(mids[i])


def replay_iv(model, prices):
    vvf = prices.loc[prices["product"] == "VELVETFRUIT_EXTRACT", ["day", "timestamp", "mid_price"]]
    vvf = vvf.rename(columns={"mid_price": "vvf_mid"})
    src = prices.loc[prices["product"] == model.IV_SOURCE, ["day", "timestamp", "mid_price"]]
    src = src.rename(columns={"mid_price": "iv_source_mid"})
    merged = vvf.merge(src, on=["day", "timestamp"], how="left")
    rows = []
    for day, g in merged.sort_values("timestamp").groupby("day"):
        ss = {}
        for r in g.itertuples(index=False):
            spot = float(r.vvf_mid)
            opt_mid = float(r.iv_source_mid)
            if ss.get("vol_locked", False):
                vol = float(ss["vol"])
            elif abs(spot - model.UNDERLYING_MU) >= model.SPOT_NEAR_MEAN_THRESHOLD:
                vol = float(model.OPTION_VOL_DEFAULT)
            else:
                iv = model.implied_vol_bisect(opt_mid, spot, model.IV_STRIKE, int(r.timestamp))
                if iv is None:
                    vol = float(model.OPTION_VOL_DEFAULT)
                else:
                    samples = list(ss.get("iv_samples", []))
                    samples.append(iv)
                    ss["iv_samples"] = samples
                    if len(samples) >= model.N_SAMPLES_TO_LOCK:
                        median = float(np.median(samples))
                        if median < model.OVERRIDE_THRESHOLD:
                            ss["vol_locked"] = False
                            ss["iv_samples"] = []
                            vol = float(model.OPTION_VOL_DEFAULT)
                        else:
                            locked = max(model.VOL_FLOOR, min(model.VOL_CAP, median))
                            ss["vol"] = locked
                            ss["vol_locked"] = True
                            ss["iv_samples"] = []
                            vol = float(locked)
                    else:
                        vol = float(model.OPTION_VOL_DEFAULT)
            rows.append(
                {
                    "day": int(day),
                    "timestamp": int(r.timestamp),
                    "vvf_mid": spot,
                    "replay_vol": vol,
                    "vol_locked": bool(ss.get("vol_locked", False)),
                }
            )
    return pd.DataFrame(rows)


def side_and_counterparty(row):
    if row["buyer"] == MARK:
        return "buy", row["seller"]
    return "sell", row["buyer"]


def role(row):
    p = row["price"]
    bb = row["bid_price_1"]
    ba = row["ask_price_1"]
    if pd.isna(bb) or pd.isna(ba):
        return "no_book"
    eps = 1e-9
    if row["mark22_side"] == "buy":
        if p >= ba - eps:
            return "taker_buy_at_ask"
        if p <= bb + eps:
            return "passive_buy_at_bid"
    else:
        if p <= bb + eps:
            return "taker_sell_at_bid"
        if p >= ba - eps:
            return "passive_sell_at_ask"
    if bb < p < ba:
        return "inside_spread"
    return "outside_top"


def fair_for_row(model, row):
    product = row["symbol"]
    if product not in STRIKES:
        return np.nan
    strike = STRIKES[product]
    if strike in model.ITM_STRIKES:
        return float(model.ITM_STRUCTURAL_FV[strike])
    return float(model.call_fair_with_vol(row["vvf_mid"], strike, int(row["timestamp"]), row["replay_vol"]))


def percentile_rank(values, x):
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0 or pd.isna(x):
        return np.nan
    return 100.0 * float(np.searchsorted(np.sort(arr), x, side="right")) / float(len(arr))


def add_event_percentiles(events, prices):
    lookup = {}
    for key, g in prices.groupby(["day", "product"]):
        lookup[key] = {
            "spread": g["spread"].to_numpy(dtype=float),
            "top_depth": g["top_depth"].to_numpy(dtype=float),
            "total_depth": g["total_depth"].to_numpy(dtype=float),
        }
    spread_pct = []
    top_depth_pct = []
    total_depth_pct = []
    for r in events.itertuples(index=False):
        dist = lookup[(r.day, r.symbol)]
        spread_pct.append(percentile_rank(dist["spread"], r.spread))
        top_depth_pct.append(percentile_rank(dist["top_depth"], r.top_depth))
        total_depth_pct.append(percentile_rank(dist["total_depth"], r.total_depth))
    events["spread_pctile_in_product_day"] = spread_pct
    events["top_depth_pctile_in_product_day"] = top_depth_pct
    events["total_depth_pctile_in_product_day"] = total_depth_pct
    return events


def q(series, pct):
    s = series.dropna()
    if len(s) == 0:
        return np.nan
    return float(s.quantile(pct))


def summarize_product_side(events):
    rows = []
    for (product, side), g in events.groupby(["symbol", "mark22_side"]):
        sizes = g["quantity"].value_counts().sort_index()
        common = "; ".join(f"{int(k)}x{int(v)}" for k, v in sizes.sort_values(ascending=False).head(5).items())
        rows.append(
            {
                "product": product,
                "side": side,
                "trades": len(g),
                "total_qty": int(g["quantity"].sum()),
                "avg_qty": g["quantity"].mean(),
                "median_qty": g["quantity"].median(),
                "p90_qty": q(g["quantity"], 0.9),
                "min_qty": int(g["quantity"].min()),
                "max_qty": int(g["quantity"].max()),
                "common_qty_counts": common,
                "avg_price_vs_mid": g["price_vs_mid"].mean(),
                "avg_price_vs_fair": g["price_vs_v314159_fair"].mean(),
                "median_spread": g["spread"].median(),
                "avg_spread_pctile": g["spread_pctile_in_product_day"].mean(),
                "avg_top_depth": g["top_depth"].mean(),
                "avg_top_depth_pctile": g["top_depth_pctile_in_product_day"].mean(),
                "dominant_role": g["role"].value_counts().idxmax(),
                "dominant_role_share": g["role"].value_counts(normalize=True).max(),
            }
        )
    return pd.DataFrame(rows).sort_values(["product", "side"])


def summarize_markouts(events):
    rows = []
    for (day, product, side), g in events.groupby(["day", "symbol", "mark22_side"]):
        base = {
            "day": int(day),
            "product": product,
            "side": side,
            "trades": len(g),
            "total_qty": int(g["quantity"].sum()),
        }
        for h in HORIZONS:
            mo = g[f"mark22_mo_t{h}"]
            cmo = g[f"contra_mo_t{h}"]
            base[f"m22_mean_t{h}"] = mo.mean()
            base[f"m22_qty_wmean_t{h}"] = np.average(mo.dropna(), weights=g.loc[mo.notna(), "quantity"]) if mo.notna().any() else np.nan
            base[f"contra_mean_t{h}"] = cmo.mean()
            base[f"contra_qty_wmean_t{h}"] = np.average(cmo.dropna(), weights=g.loc[cmo.notna(), "quantity"]) if cmo.notna().any() else np.nan
            base[f"contra_win_rate_t{h}"] = float((cmo > 0).mean())
        rows.append(base)
    return pd.DataFrame(rows).sort_values(["product", "day", "side"])


def summarize_timing(events):
    rows = []
    for day, g in events.groupby("day"):
        unique_ts = np.array(sorted(g["timestamp"].unique()))
        gaps = np.diff(unique_ts)
        gap_counts = pd.Series(gaps).value_counts().sort_values(ascending=False).head(12)
        timestamp_counts = g.groupby("timestamp").size()
        rows.append(
            {
                "scope": "all_products",
                "day": int(day),
                "product": "ALL",
                "side": "ALL",
                "trade_rows": len(g),
                "unique_timestamps": len(unique_ts),
                "first_ts": int(unique_ts[0]),
                "last_ts": int(unique_ts[-1]),
                "median_gap": float(np.median(gaps)) if len(gaps) else np.nan,
                "mean_gap": float(np.mean(gaps)) if len(gaps) else np.nan,
                "top_gap_counts": "; ".join(f"{int(k)}x{int(v)}" for k, v in gap_counts.items()),
                "max_rows_same_ts": int(timestamp_counts.max()),
                "median_rows_same_ts": float(timestamp_counts.median()),
            }
        )
    for (day, product, side), g in events.groupby(["day", "symbol", "mark22_side"]):
        unique_ts = np.array(sorted(g["timestamp"].unique()))
        gaps = np.diff(unique_ts)
        gap_counts = pd.Series(gaps).value_counts().sort_values(ascending=False).head(8)
        rows.append(
            {
                "scope": "product_side",
                "day": int(day),
                "product": product,
                "side": side,
                "trade_rows": len(g),
                "unique_timestamps": len(unique_ts),
                "first_ts": int(unique_ts[0]),
                "last_ts": int(unique_ts[-1]),
                "median_gap": float(np.median(gaps)) if len(gaps) else np.nan,
                "mean_gap": float(np.mean(gaps)) if len(gaps) else np.nan,
                "top_gap_counts": "; ".join(f"{int(k)}x{int(v)}" for k, v in gap_counts.items()),
                "max_rows_same_ts": int(g.groupby("timestamp").size().max()),
                "median_rows_same_ts": float(g.groupby("timestamp").size().median()),
            }
        )
    return pd.DataFrame(rows)


def summarize_interactions(events, trades):
    direct = (
        events.groupby(["counterparty", "symbol", "mark22_side"])
        .agg(trades=("timestamp", "size"), qty=("quantity", "sum"))
        .reset_index()
        .sort_values(["trades", "qty"], ascending=False)
    )
    rows = []
    mark_cols = ["buyer", "seller"]
    for (day, ts), ev in events.groupby(["day", "timestamp"]):
        same_ts = trades[(trades["day"] == day) & (trades["timestamp"] == ts)]
        marks = set()
        non_m22_rows = 0
        for r in same_ts.itertuples(index=False):
            row_marks = set()
            for c in mark_cols:
                value = getattr(r, c)
                if isinstance(value, str) and value.startswith("Mark"):
                    row_marks.add(value)
            if MARK not in row_marks:
                non_m22_rows += 1
            marks.update(row_marks)
        marks.discard(MARK)
        rows.append(
            {
                "day": int(day),
                "timestamp": int(ts),
                "mark22_rows": len(ev),
                "all_trade_rows_same_ts": len(same_ts),
                "non_mark22_trade_rows_same_ts": non_m22_rows,
                "other_marks_same_ts": ",".join(sorted(marks)),
            }
        )
    same_ts = pd.DataFrame(rows)
    mark_cooccur = []
    for marks in same_ts["other_marks_same_ts"]:
        if marks:
            mark_cooccur.extend(marks.split(","))
    cooccur = pd.Series(mark_cooccur).value_counts().rename_axis("other_mark").reset_index(name="timestamp_count")
    return direct, same_ts, cooccur


def repeat_timestamp_summary(events):
    ts_by_day = events[["day", "timestamp"]].drop_duplicates()
    repeated_ts = ts_by_day.groupby("timestamp")["day"].nunique().value_counts().sort_index()
    key_cols = ["timestamp", "symbol", "mark22_side"]
    repeated_key = events[key_cols + ["day"]].drop_duplicates().groupby(key_cols)["day"].nunique()
    basket = (
        events.assign(item=events["mark22_side"] + ":" + events["symbol"])
        .groupby(["day", "timestamp"])["item"]
        .apply(lambda s: ",".join(sorted(s)))
        .reset_index(name="basket")
    )
    basket_repeats = basket.groupby("basket")["day"].nunique().sort_values(ascending=False)
    return {
        "unique_day_timestamps": len(ts_by_day),
        "calendar_timestamps_seen_1_2_3_days": repeated_ts.to_dict(),
        "timestamp_product_side_keys": int(len(repeated_key)),
        "timestamp_product_side_repeated_2plus_days": int((repeated_key >= 2).sum()),
        "timestamp_product_side_repeated_3_days": int((repeated_key == 3).sum()),
        "top_repeated_baskets": basket_repeats.head(10).to_dict(),
    }


def md_table(df, columns, max_rows=None, float_digits=3):
    if max_rows is not None:
        df = df.head(max_rows)
    if len(df) == 0:
        return "_No rows._\n"
    work = df.loc[:, columns].copy()
    for col in work.columns:
        if pd.api.types.is_float_dtype(work[col]):
            work[col] = work[col].map(lambda x: "" if pd.isna(x) else f"{x:.{float_digits}f}")
    return work.to_markdown(index=False) + "\n"


def build_report(events, product_side, markouts, timing, direct, same_ts, cooccur, repeats):
    lines = []
    lines.append("# Mark 22 Counterparty Taxonomy\n")
    lines.append("Data: `data/ROUND4` days 1-3. Markout sign convention: `mark22_mo` is favorable to Mark 22; `contra_mo` is favorable to the counterparty. Forward mid is first book mid at timestamp >= event timestamp + horizon. Because book timestamps are 100 units apart, t+10 and t+50 both resolve to the next book update for these events.\n")

    total_trades = len(events)
    total_qty = int(events["quantity"].sum())
    option_events = events[events["symbol"].isin(OPTION_PRODUCTS)]
    non_option_events = events[~events["symbol"].isin(OPTION_PRODUCTS)]
    side_counts = events.groupby("mark22_side").agg(trades=("timestamp", "size"), qty=("quantity", "sum")).reset_index()
    lines.append("## Executive Read\n")
    lines.append(f"- Mark 22 appears in {total_trades} trade rows, {total_qty} total contracts: {len(option_events)} option rows / {int(option_events['quantity'].sum())} contracts and {len(non_option_events)} VFE/HGP rows / {int(non_option_events['quantity'].sum())} contracts.\n")
    lines.append("- Behavior is dominated by scheduled, multi-strike option selling. The dominant option role is selling at the displayed bid, so the historical option print stream looks like liquidity-taking sell flow rather than passive market making.\n")
    lines.append("- Raw seller-to-buyer option markouts are positive on VEV_5200/5300/5400/5500 at t+200. VEV_5200 is the largest non-dead strike signal; VEV_5400/5500 are consistent but mostly half-tick to one-tick effects in tight high-gamma books.\n")
    lines.append("- Recommendation versus v314159: keep Mark22 buy-edge reduction on VEV_5200/VEV_5500; treat VEV_5400 and VEV_5300 as test-only because they are already in the high-gamma tight-edge path and the baseline notes VEV_5400 hurt in sim; ignore 6000/6500 due zero/one-tick dead-market mechanics; no sell suppression is supported by this taxonomy.\n")

    lines.append("## Side Bias\n")
    lines.append(md_table(side_counts, ["mark22_side", "trades", "qty"]))

    lines.append("## Product And Side Inventory\n")
    display = product_side.copy()
    lines.append(md_table(
        display,
        [
            "product", "side", "trades", "total_qty", "avg_qty", "median_qty", "p90_qty",
            "avg_price_vs_mid", "avg_price_vs_fair", "median_spread", "dominant_role", "dominant_role_share",
        ],
        float_digits=3,
    ))

    lines.append("## Markouts By Product, Side, Day\n")
    mo_cols = [
        "day", "product", "side", "trades", "total_qty",
        "contra_mean_t10", "contra_mean_t50", "contra_mean_t200", "contra_mean_t500",
        "contra_win_rate_t200",
    ]
    lines.append("Positive values below favor the counterparty trading against Mark 22.\n")
    lines.append(md_table(markouts, mo_cols, float_digits=3))

    sell_options = markouts[(markouts["side"] == "sell") & (markouts["product"].isin(OPTION_PRODUCTS))]
    agg_rows = []
    for product, g in events[(events["mark22_side"] == "sell") & (events["symbol"].isin(OPTION_PRODUCTS))].groupby("symbol"):
        row = {"product": product, "trades": len(g), "qty": int(g["quantity"].sum())}
        for h in HORIZONS:
            row[f"buyer_mean_t{h}"] = g[f"contra_mo_t{h}"].mean()
            row[f"buyer_qwmean_t{h}"] = np.average(g[f"contra_mo_t{h}"].dropna(), weights=g.loc[g[f"contra_mo_t{h}"].notna(), "quantity"])
            row[f"buyer_win_t{h}"] = float((g[f"contra_mo_t{h}"] > 0).mean())
        agg_rows.append(row)
    seller_agg = pd.DataFrame(agg_rows).sort_values("product")
    lines.append("## Option-Selling Focus\n")
    lines.append("Aggregate buyer markout when Mark 22 sells:\n")
    lines.append(md_table(
        seller_agg,
        [
            "product", "trades", "qty",
            "buyer_mean_t10", "buyer_mean_t50", "buyer_mean_t200", "buyer_mean_t500",
            "buyer_win_t200",
        ],
        float_digits=3,
    ))
    lines.append("Day slices for v314159-relevant strikes:\n")
    focus = sell_options[sell_options["product"].isin(["VEV_5200", "VEV_5400", "VEV_5500"])]
    lines.append(md_table(focus, mo_cols, float_digits=3))

    lines.append("## Book Relation And Regimes\n")
    role_counts = events.groupby(["mark22_side", "role"]).size().reset_index(name="trades")
    lines.append(md_table(role_counts, ["mark22_side", "role", "trades"]))
    regime = product_side[[
        "product", "side", "trades", "median_spread", "avg_spread_pctile",
        "avg_top_depth", "avg_top_depth_pctile", "dominant_role",
    ]]
    lines.append("Average percentile columns compare Mark 22 event books to the same product/day full-book distribution.\n")
    lines.append(md_table(regime, list(regime.columns), float_digits=2))

    lines.append("## Timing And Periodicity\n")
    all_timing = timing[timing["scope"] == "all_products"]
    lines.append(md_table(
        all_timing,
        [
            "day", "trade_rows", "unique_timestamps", "first_ts", "last_ts",
            "median_gap", "mean_gap", "top_gap_counts", "max_rows_same_ts", "median_rows_same_ts",
        ],
        float_digits=1,
    ))
    lines.append(f"- Unique day/timestamps: {repeats['unique_day_timestamps']}; calendar timestamps by number of days observed: {repeats['calendar_timestamps_seen_1_2_3_days']}.\n")
    lines.append(f"- Timestamp+product+side keys: {repeats['timestamp_product_side_keys']}; repeated on 2+ days: {repeats['timestamp_product_side_repeated_2plus_days']}; repeated on all 3 days: {repeats['timestamp_product_side_repeated_3_days']}.\n")
    top_baskets = pd.DataFrame(
        [{"basket": k, "days_seen": v} for k, v in repeats["top_repeated_baskets"].items()]
    )
    lines.append("Most repeated timestamp basket signatures:\n")
    lines.append(md_table(top_baskets, ["basket", "days_seen"], max_rows=8))

    lines.append("## Interactions With Other Marks\n")
    direct_top = direct.head(20)
    lines.append("Direct counterparties in Mark 22 rows:\n")
    lines.append(md_table(direct_top, ["counterparty", "symbol", "mark22_side", "trades", "qty"]))
    lines.append("Other Mark IDs appearing at the same timestamp as at least one Mark 22 trade:\n")
    lines.append(md_table(cooccur, ["other_mark", "timestamp_count"], max_rows=12))
    lines.append(f"- Same-timestamp rows: {len(same_ts)} Mark22 timestamps; median all trade rows at those timestamps = {same_ts['all_trade_rows_same_ts'].median():.1f}; median non-Mark22 rows = {same_ts['non_mark22_trade_rows_same_ts'].median():.1f}.\n")

    lines.append("## Classification\n")
    lines.append("- Market-maker: weak fit. Mark 22 does not trade both sides broadly; side is dominated by sells, and prints are concentrated in option baskets.\n")
    lines.append("- Liquidity-taker: strong fit for the observed print mechanics; most Mark 22 sells occur at the displayed bid.\n")
    lines.append("- Informed/adverse: mixed by strike. Counterparties buying from Mark 22 have positive t+200/t+500 markouts in the listed vulnerable strikes, especially 5200/5500, but the signal is not clean enough to blanket-follow all strikes.\n")
    lines.append("- Noise/dead-market flow: 6000/6500 prints mostly occur at zero against one-tick books; they should not drive strategy changes.\n")

    lines.append("## v314159 Comparison\n")
    lines.append("- Current overlay: `MARK22_VULNERABLE_STRIKES = {VEV_5200, VEV_5500}`, buy edge reduction 1.5 with floor 0.5.\n")
    lines.append("- Keep/skew: VEV_5200 remains the clearest Mark22-specific buy-tighten target by raw markout magnitude. VEV_5500 remains acceptable because it is already validated in v314159 despite the raw edge being mostly half a tick.\n")
    lines.append("- VEV_5300/5400: raw buyer markouts after Mark 22 sells are positive and stable, but both strikes already use `HIGH_GAMMA_EDGE = 1`; classify additional Mark22 reduction as `test-only`, not a direct promote. This especially applies to VEV_5400 because the baseline comment records an about 10k R4 loss when included in the mask.\n")
    lines.append("- Widen/suppress: no evidence here supports suppressing our option buys after Mark 22 sells; if anything, the counterparty side is the favorable historical side on selected strikes. No evidence supports making our sell side more aggressive due solely to Mark 22.\n")

    lines.append("## Generated Files\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.py`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.events.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.product_side.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.markouts_by_day.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.timing.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.direct_counterparties.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.same_timestamp.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.cooccurring_marks.csv`\n")
    lines.append("- `notebooks/round4/mark_taxonomy/mark_22.md`\n")
    return "".join(lines)


def main():
    model = load_model()
    prices = load_prices()
    trades = load_trades()
    price_index = build_price_index(prices)
    iv = replay_iv(model, prices)

    m22 = trades[(trades["buyer"] == MARK) | (trades["seller"] == MARK)].copy()
    sides = m22.apply(side_and_counterparty, axis=1, result_type="expand")
    m22["mark22_side"] = sides[0]
    m22["counterparty"] = sides[1]

    book_cols = [
        "day", "timestamp", "product", "bid_price_1", "bid_volume_1",
        "ask_price_1", "ask_volume_1", "mid_price", "spread", "top_depth", "total_depth",
    ]
    events = m22.merge(
        prices[book_cols],
        left_on=["day", "timestamp", "symbol"],
        right_on=["day", "timestamp", "product"],
        how="left",
    ).drop(columns=["product"])
    events = events.merge(iv, on=["day", "timestamp"], how="left")
    events["role"] = events.apply(role, axis=1)
    events["price_vs_mid"] = events["price"] - events["mid_price"]
    events["price_vs_bid"] = events["price"] - events["bid_price_1"]
    events["price_vs_ask"] = events["price"] - events["ask_price_1"]
    events["price_vs_v314159_fair"] = events.apply(lambda r: r["price"] - fair_for_row(model, r), axis=1)

    for h in HORIZONS:
        fut = [
            forward_mid(price_index, r.day, r.symbol, r.timestamp, h)
            for r in events.itertuples(index=False)
        ]
        events[f"future_mid_t{h}"] = fut
        buy_mo = events[f"future_mid_t{h}"] - events["price"]
        sell_mo = events["price"] - events[f"future_mid_t{h}"]
        events[f"mark22_mo_t{h}"] = np.where(events["mark22_side"] == "buy", buy_mo, sell_mo)
        events[f"contra_mo_t{h}"] = -events[f"mark22_mo_t{h}"]

    events = add_event_percentiles(events, prices)
    product_side = summarize_product_side(events)
    markouts = summarize_markouts(events)
    timing = summarize_timing(events)
    direct, same_ts, cooccur = summarize_interactions(events, trades)
    repeats = repeat_timestamp_summary(events)

    events.to_csv(OUT_DIR / "mark_22.events.csv", index=False)
    product_side.to_csv(OUT_DIR / "mark_22.product_side.csv", index=False)
    markouts.to_csv(OUT_DIR / "mark_22.markouts_by_day.csv", index=False)
    timing.to_csv(OUT_DIR / "mark_22.timing.csv", index=False)
    direct.to_csv(OUT_DIR / "mark_22.direct_counterparties.csv", index=False)
    same_ts.to_csv(OUT_DIR / "mark_22.same_timestamp.csv", index=False)
    cooccur.to_csv(OUT_DIR / "mark_22.cooccurring_marks.csv", index=False)

    report = build_report(events, product_side, markouts, timing, direct, same_ts, cooccur, repeats)
    (OUT_DIR / "mark_22.md").write_text(report)


if __name__ == "__main__":
    main()
