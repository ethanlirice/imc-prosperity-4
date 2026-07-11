"""
Round 4 — Mark 14 on HYDROGEL_PACK exploratory analysis.

Answers (with numbers): timing regularity, volume patterns, direction vs book state,
and a passive/MM vs taker vs large-flow classification consistent with hint framing.

Run from repo root:
  python notebooks/mark14/explore_mark14_hgp.py

Outputs:
  notebooks/mark14/mark14_hgp_exploration_output.txt
  notebooks/mark14/mark14_hgp_events_enriched.csv

Also imports:
  compute_enriched_mark14_hgp() — used by explore_mark14_price_improvement.py
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
TRADER = "Mark 14"
PRODUCT = "HYDROGEL_PACK"
HGP_MU = 10000.0


def parse_day(path: Path) -> int:
    return int(path.stem.rsplit("_", 1)[-1])


def load_prices_hgp() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        df = df[df["product"] == PRODUCT].copy()
        frames.append(df)
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    prices["best_bid_depth"] = prices["bid_volume_1"].fillna(0)
    prices["best_ask_depth"] = prices["ask_volume_1"].fillna(0).abs()
    bid_cols = [c for c in prices.columns if c.startswith("bid_volume_")]
    ask_cols = [c for c in prices.columns if c.startswith("ask_volume_")]
    # CSV magnitudes are unsigned counts on each side; use abs for asks in case of datamodel-style negatives.
    prices["bid_depth_3"] = prices[bid_cols].fillna(0).sum(axis=1)
    prices["ask_depth_3"] = prices[ask_cols].fillna(0).abs().sum(axis=1)
    prices["depth_sum_3"] = prices["bid_depth_3"] + prices["ask_depth_3"]
    prices["imbalance_3"] = np.where(
        prices["depth_sum_3"] > 0,
        (prices["bid_depth_3"] - prices["ask_depth_3"]) / prices["depth_sum_3"],
        np.nan,
    )
    return prices


def load_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        df = pd.read_csv(path, sep=";")
        df["day"] = parse_day(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def build_price_lookup(prices: pd.DataFrame) -> dict:
    return {
        int(key): frame.sort_values("timestamp").reset_index(drop=True)
        for key, frame in prices.groupby("day", sort=True)
    }


def mid_at_or_before(lookup: pd.DataFrame, ts: int) -> float:
    times = lookup["timestamp"].to_numpy()
    idx = np.searchsorted(times, ts, side="right") - 1
    if idx < 0:
        return float("nan")
    return float(lookup["mid_price"].iloc[idx])


def forward_mid(lookup: pd.DataFrame, ts: int, horizon: int) -> float:
    times = lookup["timestamp"].to_numpy()
    idx = np.searchsorted(times, ts + horizon, side="left")
    if idx >= len(lookup):
        return float("nan")
    return float(lookup["mid_price"].iloc[idx])


def lagged_mid_delta(lookup: pd.DataFrame, ts: int, lag: int) -> float:
    cur = mid_at_or_before(lookup, ts)
    past = mid_at_or_before(lookup, ts - lag)
    if math.isnan(cur) or math.isnan(past):
        return float("nan")
    return cur - past


def classify_price_location(row) -> str:
    price = float(row.price)
    bid = float(row.bid_price_1)
    ask = float(row.ask_price_1)
    if price == bid:
        return "at_bid"
    if price == ask:
        return "at_ask"
    if bid < price < ask:
        return "inside"
    if price < bid:
        return "below_bid"
    if price > ask:
        return "above_ask"
    return "unknown"


def safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return float("nan")
    x = a[m]
    y = b[m]
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def summarize_gaps(gaps: pd.Series) -> dict:
    g = gaps.dropna().to_numpy()
    if len(g) == 0:
        return {"n": 0}
    return {
        "n": int(len(g)),
        "mean": float(np.mean(g)),
        "std": float(np.std(g, ddof=1)) if len(g) > 1 else 0.0,
        "cv": float(np.std(g, ddof=1) / np.mean(g)) if len(g) > 1 and np.mean(g) > 0 else float("nan"),
        "p10": float(np.quantile(g, 0.1)),
        "p50": float(np.quantile(g, 0.5)),
        "p90": float(np.quantile(g, 0.9)),
        "min": float(np.min(g)),
        "max": float(np.max(g)),
    }


def gap_autocorr(gaps: np.ndarray, lag: int = 1) -> float:
    if len(gaps) <= lag + 2:
        return float("nan")
    a = gaps[:-lag]
    b = gaps[lag:]
    return safe_corr(a, b)


def modulo_peak_ratio(ts: np.ndarray, mod: int) -> float:
    """Share of mass in top-5 residue buckets vs uniform baseline 5/mod."""
    if len(ts) == 0:
        return float("nan")
    rem = ts % mod
    vc = pd.Series(rem).value_counts()
    top5 = vc.nlargest(5).sum()
    return float(top5 / len(ts))


def compute_enriched_mark14_hgp() -> pd.DataFrame:
    """Join Mark 14 HGP trades to same-timestamp book + forward markouts."""
    prices = load_prices_hgp()
    trades = load_trades()
    lookup_by_day = build_price_lookup(prices)

    hgp = trades[trades["symbol"] == PRODUCT].copy()
    mark = hgp[(hgp["buyer"] == TRADER) | (hgp["seller"] == TRADER)].copy()
    mark["side"] = np.where(mark["buyer"] == TRADER, "buy", "sell")
    mark["counterparty"] = np.where(mark["buyer"] == TRADER, mark["seller"], mark["buyer"])

    merge_cols = [
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
        "imbalance_3",
    ]
    mark = mark.merge(prices[["day", "timestamp"] + merge_cols], on=["day", "timestamp"], how="left")

    rows = []
    for r in mark.itertuples(index=False):
        lu = lookup_by_day[int(r.day)]
        ts = int(r.timestamp)
        rows.append(
            {
                "day": int(r.day),
                "timestamp": ts,
                "side": r.side,
                "quantity": int(r.quantity),
                "price": float(r.price),
                "counterparty": r.counterparty,
                "bid_price_1": float(r.bid_price_1),
                "ask_price_1": float(r.ask_price_1),
                "spread": float(r.spread),
                "mid_price": float(r.mid_price),
                "imbalance_3": float(r.imbalance_3) if pd.notna(r.imbalance_3) else float("nan"),
                "ret_lag100": lagged_mid_delta(lu, ts, 100),
                "ret_lag500": lagged_mid_delta(lu, ts, 500),
                "ret_lag2000": lagged_mid_delta(lu, ts, 2000),
                "fwd200": forward_mid(lu, ts, 200) - float(r.price)
                if r.side == "buy"
                else float(r.price) - forward_mid(lu, ts, 200),
                "mid_minus_mu": float(r.mid_price) - HGP_MU,
            }
        )
    enriched = pd.DataFrame(rows)
    enriched["price_location"] = mark.apply(classify_price_location, axis=1)
    return enriched


def main() -> None:
    enriched = compute_enriched_mark14_hgp()

    lines = []
    lines.append("Mark 14 × HYDROGEL_PACK — exploration (Round 4 days 1–3)")
    lines.append(f"Events: n={len(enriched)}, total qty={int(enriched['quantity'].sum())}")
    lines.append("")

    # --- Timing / intervals ---
    lines.append("## 1) Does Mark 14 appear at predictable intervals?")
    lines.append("")
    for day, frame in enriched.groupby("day"):
        frame = frame.sort_values("timestamp")
        gaps = frame["timestamp"].diff().dropna()
        st = summarize_gaps(gaps)
        garr = gaps.to_numpy()
        ac1 = gap_autocorr(garr, 1)
        lines.append(f"Day {day}: inter-arrival gaps (timestamp units) — n={st.get('n', 0)}, mean={st.get('mean', float('nan')):.2f}, std={st.get('std', 0):.2f}, cv={st.get('cv', float('nan')):.3f}, p10/p50/p90={st.get('p10', float('nan')):.0f}/{st.get('p50', float('nan')):.0f}/{st.get('p90', float('nan')):.0f}, lag-1 gap autocorr={ac1:.4f}")
    # pooled within-day gaps only (already per-day diff); concatenate
    pooled = []
    for _, frame in enriched.groupby("day"):
        pooled.extend(frame.sort_values("timestamp")["timestamp"].diff().dropna().tolist())
    pooled = np.array(pooled, dtype=float)
    lines.append(f"Pooled across days (within-day gaps): mean={np.mean(pooled):.2f}, cv={np.std(pooled, ddof=1)/np.mean(pooled):.3f}, lag1 autocorr={gap_autocorr(pooled,1):.4f}")
    ts_all = enriched["timestamp"].to_numpy()
    for mod in (1000, 5000, 10000):
        r = modulo_peak_ratio(ts_all, mod)
        baseline = min(5.0 / mod, 1.0)
        lines.append(
            f"Timestamp residue mod {mod}: top-5 bucket mass share={r:.4f} "
            f"(≈{baseline:.5f} if uniform over {mod} buckets — **high** share ⇒ residues concentrate)"
        )
    lines.append(
        "Interpretation: gap lag-1 autocorr near 0 ⇒ little AR(1) structure in inter-arrival times; "
        "CV≈1 ⇒ gaps are heavy-tailed vs a fixed clock. Modulo concentration is separate: check top buckets."
    )
    lines.append("")

    # --- Volume ---
    lines.append("## 2) Does volume follow a pattern?")
    lines.append("")
    vc = enriched["quantity"].value_counts().sort_index()
    lines.append("Quantity histogram (qty -> count):")
    for q, c in vc.head(12).items():
        lines.append(f"  {int(q)}: {int(c)}")
    qmean = enriched.groupby(["day", "side"])["quantity"].mean().reset_index()
    lines.append("Mean qty by day × side:")
    for _, row in qmean.iterrows():
        lines.append(f"  day {int(row.day)} {row.side}: {row.quantity:.3f}")
    # Sequence: corr(gap, next qty) per day
    lines.append("Correlation between preceding gap and event qty (by day):")
    for day, frame in enriched.groupby("day"):
        frame = frame.sort_values("timestamp")
        gaps = frame["timestamp"].diff().dropna().to_numpy()
        qty = frame["quantity"].to_numpy()[1:]
        if len(gaps) == len(qty) and len(gaps) > 2:
            lines.append(f"  day {day}: corr(gap, qty)={safe_corr(gaps, qty):.4f}")
    lines.append("Side alternation (consecutive events, by day):")
    for day, frame in enriched.groupby("day"):
        frame = frame.sort_values("timestamp")
        sides = (frame["side"] == "buy").to_numpy()
        if len(sides) > 1:
            flips = np.mean(sides[1:] != sides[:-1])
            lines.append(f"  day {day}: P(side flips vs previous)={flips:.3f}")
    lines.append("")

    # --- Direction vs market conditions ---
    lines.append("## 3) Does direction correlate with specific market conditions?")
    lines.append("")
    buys = enriched[enriched["side"] == "buy"]
    sells = enriched[enriched["side"] == "sell"]
    lines.append(f"Buy share: {len(buys)/len(enriched):.3f} (n buy={len(buys)}, n sell={len(sells)})")
    for name, col in [
        ("spread", "spread"),
        ("imbalance_3", "imbalance_3"),
        ("mid_minus_mu", "mid_minus_mu"),
        ("ret_lag100", "ret_lag100"),
        ("ret_lag500", "ret_lag500"),
    ]:
        bx = buys[col].to_numpy(dtype=float)
        sx = sells[col].to_numpy(dtype=float)
        mb = np.nanmean(bx)
        ms = np.nanmean(sx)
        pooled = np.nanstd(np.concatenate([bx, sx]))
        sep = (mb - ms) / (pooled + 1e-9) if np.isfinite(pooled) and pooled > 0 else float("nan")
        lines.append(
            f"{name}: buy mean={mb:.4f}, sell mean={ms:.4f}, "
            f"(mean_buy−mean_sell)/std_pooled={sep:.4f}"
        )
    # Point-biserial: side buy=1 vs conditions
    side_numeric = (enriched["side"] == "buy").astype(float).to_numpy()
    for col in ["spread", "imbalance_3", "mid_minus_mu", "ret_lag500"]:
        lines.append(f"corr(side_is_buy, {col})={safe_corr(side_numeric, enriched[col].to_numpy(dtype=float)):.4f}")
    lines.append("")

    # --- Classification ---
    lines.append("## 4) Classification (hint lenses)")
    lines.append("")
    loc_tab = enriched["price_location"].value_counts(normalize=True).sort_values(ascending=False)
    lines.append("Price location mix (passive if at bid for buys / at ask for sells):")
    for k, v in loc_tab.items():
        lines.append(f"  {k}: {v:.3f}")
    passive_buy = (enriched["side"] == "buy") & (enriched["price_location"] == "at_bid")
    passive_sell = (enriched["side"] == "sell") & (enriched["price_location"] == "at_ask")
    lines.append(f"Passive-style fraction of all rows: buy@bid {passive_buy.mean():.3f}, sell@ask {passive_sell.mean():.3f}")
    buys_only = enriched[enriched["side"] == "buy"]
    sells_only = enriched[enriched["side"] == "sell"]
    lines.append(
        f"Conditional execution: P(at_bid | buy)={(buys_only['price_location']=='at_bid').mean():.4f}, "
        f"P(at_ask | sell)={(sells_only['price_location']=='at_ask').mean():.4f}"
    )
    dup_check = enriched.groupby(["day", "timestamp"]).size()
    dup_groups = int((dup_check > 1).sum())
    lines.append(f"Duplicate (day,timestamp) groups with >1 Mark14 HGP row: {dup_groups}")
    lines.append(f"Max simultaneous Mark14 HGP prints at same ts: {dup_check.max()}")
    lines.append("")
    lines.append("Narrative fit:")
    lines.append("- Market-maker (rhythmic two-sided liquidity): partially — buys cluster at bid, sells at ask; check two-sided frequency.")
    lines.append("- Liquidity taker: low if most prints are at bid/ask with passive classification above.")
    lines.append("- Large imprecise flow: inspect qty tail vs book depth.")
    lines.append("")
    cp_top = (
        enriched.groupby("counterparty")
        .agg(n=("timestamp", "count"), qty=("quantity", "sum"))
        .reset_index()
        .sort_values("n", ascending=False)
        .head(10)
    )
    lines.append("Top counterparties on HGP (who lifts Mark 14's passive quotes):")
    for _, row in cp_top.iterrows():
        lines.append(f"  {row.counterparty}: n={int(row.n)}, qty={int(row.qty)}")
    lines.append("")
    lines.append(f"Mean |imbalance_3| at events: {np.nanmean(np.abs(enriched['imbalance_3'].to_numpy())):.4f}")
    lines.append(f"Mean fwd200 trade-edge (historical, same sign convention as DATA.md): {np.nanmean(enriched['fwd200'].to_numpy()):.4f}")
    lines.append("")
    lines.append("## 5) Summary classification (this slice of evidence)")
    lines.append("")
    lines.append(
        "- Timing: near-zero lag-1 gap autocorrelation ⇒ not a simple periodic metronome; "
        "large CV ⇒ heavy-tailed spacing."
    )
    lines.append(
        "- Execution style: ~100% at bid (buys) / ask (sells) ⇒ passive quote interaction, not visible-book lifting."
    )
    lines.append(
        "- Counterparty: single counterparty identity across all HGP prints here (see table) ⇒ consistent other side."
    )

    out_txt = OUT_DIR / "mark14_hgp_exploration_output.txt"
    out_txt.write_text("\n".join(lines) + "\n")
    csv_path = OUT_DIR / "mark14_hgp_events_enriched.csv"
    enriched.to_csv(csv_path, index=False)
    print(f"Wrote {out_txt}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
