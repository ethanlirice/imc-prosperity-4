"""
Mark 14 × HYDROGEL_PACK — price improvement vs touch / mid / spread.

Also documents how strategies/round4/v314159.py uses (or does not use) Mark IDs.

Run from repo root:
  python notebooks/mark14/explore_mark14_price_improvement.py

Outputs:
  notebooks/mark14/mark14_hgp_price_improvement_output.txt
  notebooks/mark14/mark14_hgp_price_improvement.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from explore_mark14_hgp import compute_enriched_mark14_hgp

OUT_DIR = Path(__file__).resolve().parent
V314159 = Path(__file__).resolve().parents[2] / "strategies" / "round4" / "v314159.py"


def fmt(x, nd=4):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "nan"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def add_price_improvement_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    bid = out["bid_price_1"].to_numpy(dtype=float)
    ask = out["ask_price_1"].to_numpy(dtype=float)
    mid = out["mid_price"].to_numpy(dtype=float)
    px = out["price"].to_numpy(dtype=float)
    spr = out["spread"].to_numpy(dtype=float)
    is_buy = out["side"].to_numpy() == "buy"

    # NBBO-style: savings vs crossing the wide side (aggressive alternative).
    save_vs_touch = np.where(is_buy, ask - px, px - bid)
    # Signed distance from mid (half-spread capture proxy).
    mid_capture = np.where(is_buy, mid - px, px - mid)
    # Fraction of quoted spread "kept" vs paying the opposite touch.
    frac_of_spread = np.where(spr > 0, save_vs_touch / spr, np.nan)

    # One tick "better" than bid+1 (buy) / ask-1 (sell) posting — mechanical comparison.
    vs_improve_1 = np.where(is_buy, (bid + 1.0) - px, px - (ask - 1.0))

    out["save_vs_touch_aggressive"] = save_vs_touch
    out["mid_capture_signed"] = mid_capture
    out["save_vs_touch_as_frac_of_spread"] = frac_of_spread
    out["vs_improve_1_quote"] = vs_improve_1
    return out


def summarize(df: pd.DataFrame, lines: list) -> None:
    n = len(df)
    lines.append(f"Sample: n={n}, qty sum={int(df['quantity'].sum())}")
    lines.append("")
    lines.append("### vs aggressive touch (buy: ask−price; sell: price−bid)")
    for side in ["buy", "sell"]:
        sl = df[df["side"] == side]
        w = sl["quantity"].to_numpy()
        x = sl["save_vs_touch_aggressive"].to_numpy()
        lines.append(
            f"  {side}: mean={fmt(np.average(x, weights=w))}, "
            f"p50={fmt(np.quantile(x, 0.5))}, p10={fmt(np.quantile(x, 0.1))}, p90={fmt(np.quantile(x, 0.9))}"
        )
    lines.append(
        f"  pooled qty-weighted mean save_vs_touch: "
        f"{fmt(np.average(df['save_vs_touch_aggressive'], weights=df['quantity']))}"
    )
    lines.append("")
    lines.append("### Mid capture (buy: mid−price; sell: price−mid)")
    for side in ["buy", "sell"]:
        sl = df[df["side"] == side]
        w = sl["quantity"].to_numpy()
        x = sl["mid_capture_signed"].to_numpy()
        lines.append(
            f"  {side}: qty-weighted mean={fmt(np.average(x, weights=w))}"
        )
    lines.append("")
    lines.append("### Share of quoted spread captured (save/spread)")
    x = df["save_vs_touch_as_frac_of_spread"].to_numpy()
    w = df["quantity"].to_numpy()
    lines.append(f"  qty-weighted mean frac: {fmt(np.average(x, weights=w))}")
    lines.append(f"  frac == 1.0 (within 1e-9): {np.average(np.isclose(x, 1.0), weights=w):.4f}")
    inside = df["price_location"] == "inside"
    lines.append(f"  rows strictly inside spread: {inside.sum()} ({inside.mean():.4f})")
    lines.append("")
    lines.append("### vs bid+1 / ask−1 one-tick improved passive quote")
    for side in ["buy", "sell"]:
        sl = df[df["side"] == side]
        w = sl["quantity"].to_numpy()
        v = sl["vs_improve_1_quote"].to_numpy()
        lines.append(
            f"  {side}: qty-weighted mean (positive ⇒ better than that 1-tick quote): "
            f"{fmt(np.average(v, weights=w))}"
        )
    lines.append("")
    lines.append("Interpretation sketch:")
    lines.append(
        "- save_vs_touch ≈ spread on bid/ask prints: Mark 14 avoids paying the spread vs an "
        "immediate aggressive cross on the other side."
    )
    lines.append(
        "- mid_capture ≈ half-spread per side at touch: consistent with passive liquidity provision "
        "being lifted by the counterparty."
    )
    lines.append(
        "- 'Mark14-only price improvement' in CSV replay is mostly structural (at-touch), not "
        "oracle timing; executable replication after observing the ID is a separate question (see DATA.md)."
    )


def write_v314159_survey(lines: list) -> None:
    lines.append("")
    lines.append("=" * 72)
    lines.append("## v314159.py — how Mark-related logic is implemented")
    lines.append("")
    src = V314159.read_text(encoding="utf-8")
    lines.append(f"Source file: {V314159}")
    lines.append("")
    lines.append("**Mark 14:** not used. No `Mark 14` string and no branch on Mark 14 in `market_trades`.")
    lines.append("")
    lines.append(
        "**Mark 67 / Mark 49:** applied only on **VELVETFRUIT_EXTRACT** (`UNDERLYING`). "
        "`update_signal_state` scans `state.market_trades.get(UNDERLYING)` for "
        "`t.buyer == \"Mark 67\"` or `t.seller == \"Mark 49\"`, updates `last_signal_ts`, "
        "and `trade_ou_split(..., suppress_sell=signal_active)` suppresses **VFE sells** for "
        "`SIGNAL_WINDOW` after the last qualifying print."
    )
    lines.append("")
    lines.append(
        "**Mark 22:** not read from trades. The strategy uses a **static** set "
        "`MARK22_VULNERABLE_STRIKES = {\"VEV_5200\", \"VEV_5500\"}` in `trade_option()` to "
        "**lower the option buy edge** (vs sell edge) on those symbols only — documentation ties "
        "this to Mark 22's selling pressure in data, but runtime code does not identify Mark 22."
    )
    lines.append("")
    lines.append(
        "**HYDROGEL_PACK:** `trade_ou_split` with OU mean `HYDROGEL_MU`, micro-buy edge "
        "`MICRO_HGP_BUY_EDGE = 4`, passive edges `PASSIVE_HGP_BID_EDGE` / `PASSIVE_HGP_ASK_EDGE`. "
        "**No counterparty / Mark logic** on hydrogel."
    )
    lines.append("")
    if "Mark 14" in src:
        lines.append("(Unexpected: file contains substring 'Mark 14' — verify manually.)")
    else:
        lines.append("Verified: source text has no substring `Mark 14`.")
    lines.append("")


def main() -> None:
    df = compute_enriched_mark14_hgp()
    df = add_price_improvement_columns(df)

    lines = []
    lines.append("Mark 14 × HYDROGEL_PACK — price improvement (Round 4 days 1–3)")
    lines.append("")
    summarize(df, lines)
    write_v314159_survey(lines)

    out_txt = OUT_DIR / "mark14_hgp_price_improvement_output.txt"
    out_txt.write_text("\n".join(lines) + "\n")

    csv_path = OUT_DIR / "mark14_hgp_price_improvement.csv"
    df.to_csv(csv_path, index=False)

    print(f"Wrote {out_txt}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
