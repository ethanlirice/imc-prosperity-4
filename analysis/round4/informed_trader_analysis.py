from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
OUT_FILE = OUT_DIR / "informed_trader_analysis_output.txt"

FORWARD_HORIZON = 200
MIN_TRADES_FOR_SUMMARY = 5
MIN_TRADES_FOR_CANDIDATE = 10
GOOD_PCT_THRESHOLD = 0.65
EXTREMA_TOLERANCE = 5


def parse_day(path):
    return int(path.stem.rsplit("_", 1)[-1])


def load_trades():
    days = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        if "day" in df.columns:
            df = df.drop(columns=["day"])
        df["day"] = day
        days.append(df)
        print(f"Day {day}: {len(df)} trades, columns: {df.columns.tolist()}")
    if not days:
        raise FileNotFoundError(f"No trades files found in {DATA_DIR}")
    return pd.concat(days, ignore_index=True)


def load_prices():
    days = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day):
        day = parse_day(path)
        df = pd.read_csv(path, sep=";")
        if "day" in df.columns:
            df = df.drop(columns=["day"])
        df["day"] = day
        days.append(df)
    if not days:
        raise FileNotFoundError(f"No price files found in {DATA_DIR}")
    return pd.concat(days, ignore_index=True)


def print_step_1(trades):
    print("\nAll trader IDs present:")
    ids = sorted(set(trades["buyer"].dropna()) | set(trades["seller"].dropna()))
    for trader in ids:
        if str(trader) != "":
            print(trader)

    print("\nBuyer counts:")
    print(trades["buyer"].value_counts().to_string())
    print("\nSeller counts:")
    print(trades["seller"].value_counts().to_string())

    print("\nAll products:")
    for product in sorted(trades["symbol"].unique()):
        print(product)


def build_good_trade_results(trades, price_df):
    results = []
    price_lookup = {
        (day, symbol): frame.sort_values("timestamp")
        for (day, symbol), frame in price_df.groupby(["day", "product"])
    }

    for _, trade in trades.iterrows():
        day = trade["day"]
        ts = trade["timestamp"]
        symbol = trade["symbol"]
        price = trade["price"]
        qty = trade["quantity"]

        frame = price_lookup.get((day, symbol))
        if frame is None:
            continue

        future = frame[
            (frame["timestamp"] > ts)
            & (frame["timestamp"] <= ts + FORWARD_HORIZON)
        ]["mid_price"]
        if len(future) == 0:
            continue

        future_mid = future.iloc[-1]

        for side, trader in (("buy", trade["buyer"]), ("sell", trade["seller"])):
            if pd.isna(trader) or trader == "":
                continue
            if side == "buy":
                good = 1 if future_mid > price else 0
                signed_edge = future_mid - price
            else:
                good = 1 if future_mid < price else 0
                signed_edge = price - future_mid
            results.append(
                {
                    "trader": trader,
                    "symbol": symbol,
                    "day": day,
                    "timestamp": ts,
                    "side": side,
                    "price": price,
                    "future_mid": future_mid,
                    "good": good,
                    "qty": qty,
                    "signed_edge": signed_edge,
                }
            )

    return pd.DataFrame(results)


def print_step_2(result_df):
    summary = (
        result_df.groupby(["trader", "symbol"])
        .agg(
            trades=("good", "count"),
            good_pct=("good", "mean"),
            avg_qty=("qty", "mean"),
            mean_edge=("signed_edge", "mean"),
            total_edge=("signed_edge", "sum"),
        )
        .reset_index()
    )
    summary = summary[summary["trades"] >= MIN_TRADES_FOR_SUMMARY]
    summary = summary.sort_values(
        ["good_pct", "trades", "mean_edge"], ascending=[False, False, False]
    )

    print("\nTop traders by good trade %:")
    print(summary.to_string(index=False))

    candidates = summary[
        (summary["trades"] >= MIN_TRADES_FOR_CANDIDATE)
        & (summary["good_pct"] > GOOD_PCT_THRESHOLD)
    ].copy()
    print(
        "\nCandidates with good_pct > "
        f"{GOOD_PCT_THRESHOLD:.2f} and trades >= {MIN_TRADES_FOR_CANDIDATE}:"
    )
    if len(candidates) == 0:
        print("NONE")
    else:
        print(candidates.to_string(index=False))

    return summary, candidates


def print_step_3(trades, price_df):
    extrema_hits = []

    for symbol in trades["symbol"].unique():
        sym_prices = price_df[price_df["product"] == symbol].copy()
        sym_trades = trades[trades["symbol"] == symbol].copy()

        print(f"\n=== {symbol} ===")

        for day in sorted(sym_trades["day"].unique()):
            day_price_rows = sym_prices[sym_prices["day"] == day]
            day_prices = day_price_rows["mid_price"]
            day_trades = sym_trades[sym_trades["day"] == day]

            if len(day_prices) == 0:
                continue

            daily_min = day_prices.min()
            daily_max = day_prices.max()

            buys_at_min = day_trades[
                (day_trades["price"] <= daily_min + EXTREMA_TOLERANCE)
                & (~day_trades["buyer"].isna())
                & (day_trades["buyer"] != "")
            ]

            sells_at_max = day_trades[
                (day_trades["price"] >= daily_max - EXTREMA_TOLERANCE)
                & (~day_trades["seller"].isna())
                & (day_trades["seller"] != "")
            ]

            if len(buys_at_min) > 0:
                print(f"Day {day} | Min={daily_min:.1f} | Buyers at min:")
                print(
                    buys_at_min[["timestamp", "buyer", "price", "quantity"]]
                    .to_string(index=False)
                )
                for _, row in buys_at_min.iterrows():
                    extrema_hits.append(
                        {
                            "symbol": symbol,
                            "day": day,
                            "side": "buy_at_min",
                            "trader": row["buyer"],
                            "price": row["price"],
                            "quantity": row["quantity"],
                        }
                    )

            if len(sells_at_max) > 0:
                print(f"Day {day} | Max={daily_max:.1f} | Sellers at max:")
                print(
                    sells_at_max[["timestamp", "seller", "price", "quantity"]]
                    .to_string(index=False)
                )
                for _, row in sells_at_max.iterrows():
                    extrema_hits.append(
                        {
                            "symbol": symbol,
                            "day": day,
                            "side": "sell_at_max",
                            "trader": row["seller"],
                            "price": row["price"],
                            "quantity": row["quantity"],
                        }
                    )

    extrema_df = pd.DataFrame(extrema_hits)
    print("\nExtrema hit summary:")
    if len(extrema_df) == 0:
        print("NONE")
    else:
        summary = (
            extrema_df.groupby(["trader", "symbol", "side"])
            .agg(hits=("day", "count"), days=("day", lambda x: ",".join(map(str, sorted(set(x))))), avg_qty=("quantity", "mean"))
            .reset_index()
            .sort_values(["hits", "trader", "symbol"], ascending=[False, True, True])
        )
        print(summary.to_string(index=False))

    return extrema_df


def choose_candidate(candidates, extrema_df):
    if len(candidates) == 0:
        return None
    if len(extrema_df) == 0:
        ranked = candidates.sort_values(
            ["good_pct", "trades", "mean_edge"], ascending=[False, False, False]
        )
        return ranked.iloc[0]["trader"]

    extrema_counts = (
        extrema_df.groupby("trader").size().rename("extrema_hits").reset_index()
    )
    ranked = candidates.merge(extrema_counts, on="trader", how="left").fillna(
        {"extrema_hits": 0}
    )
    ranked = ranked.sort_values(
        ["extrema_hits", "good_pct", "trades", "mean_edge"],
        ascending=[False, False, False, False],
    )
    return ranked.iloc[0]["trader"]


def print_step_4(result_df, candidate):
    if candidate is None:
        print("\nNo candidate selected from Steps 2 and 3.")
        return pd.DataFrame()

    candidate_trades = result_df[result_df["trader"] == candidate].copy()

    print(f"\nCandidate: {candidate}")
    print(f"Total trades: {len(candidate_trades)}")
    print(f"Good trade %: {candidate_trades['good'].mean():.3f}")
    print(f"Products traded: {candidate_trades['symbol'].unique()}")
    print(f"Average qty: {candidate_trades['qty'].mean():.1f}")
    print("\nBy product:")
    by_product = (
        candidate_trades.groupby("symbol")
        .agg(
            trades=("good", "count"),
            good_pct=("good", "mean"),
            avg_qty=("qty", "mean"),
            mean_edge=("signed_edge", "mean"),
            total_edge=("signed_edge", "sum"),
        )
        .sort_values(["good_pct", "trades"], ascending=[False, False])
    )
    print(by_product.to_string())

    print("\nQuantity signature by product:")
    qty_sig = (
        candidate_trades.groupby(["symbol", "qty"])
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["symbol", "count"], ascending=[True, False])
    )
    print(qty_sig.to_string(index=False))

    for symbol in candidate_trades["symbol"].unique():
        sym = candidate_trades[candidate_trades["symbol"] == symbol]
        print(f"\n{symbol}: {len(sym)} trades, good_pct={sym['good'].mean():.3f}")
        print(
            sym[["day", "timestamp", "side", "price", "future_mid", "qty", "signed_edge"]]
            .to_string(index=False)
        )

    return candidate_trades


def print_step_5(candidate_trades):
    if len(candidate_trades) == 0:
        print("\nNo theoretical PnL calculated because no candidate was confirmed.")
        return None

    pnl_per_trade = candidate_trades["signed_edge"].to_numpy()

    print(f"\nMean PnL per trade if copied: {np.mean(pnl_per_trade):.2f}")
    print(f"Total trades available: {len(pnl_per_trade)}")
    print(f"Theoretical total PnL: {sum(pnl_per_trade):.0f}")
    print(f"Theoretical PnL/day: {sum(pnl_per_trade) / 3:.0f}")

    return {
        "mean_pnl_per_trade": float(np.mean(pnl_per_trade)),
        "total_trades": int(len(pnl_per_trade)),
        "theoretical_total_pnl": float(sum(pnl_per_trade)),
        "theoretical_pnl_per_day": float(sum(pnl_per_trade) / 3),
    }


def main():
    with OUT_FILE.open("w") as fh:
        import sys

        original_stdout = sys.stdout
        sys.stdout = fh
        try:
            trades = load_trades()
            print_step_1(trades)

            if (
                "buyer" not in trades.columns
                or "seller" not in trades.columns
                or trades["buyer"].fillna("").eq("").all()
                or trades["seller"].fillna("").eq("").all()
            ):
                print("\nSTOP: buyer/seller columns are empty or missing.")
                return

            price_df = load_prices()
            result_df = build_good_trade_results(trades, price_df)
            result_df.to_csv(OUT_DIR / "informed_trader_trade_scores.csv", index=False)

            summary, candidates = print_step_2(result_df)
            summary.to_csv(OUT_DIR / "informed_trader_good_pct_summary.csv", index=False)

            extrema_df = print_step_3(trades, price_df)
            extrema_df.to_csv(OUT_DIR / "informed_trader_extrema_hits.csv", index=False)

            candidate = choose_candidate(candidates, extrema_df)
            candidate_trades = print_step_4(result_df, candidate)
            candidate_trades.to_csv(
                OUT_DIR / "informed_trader_candidate_trades.csv", index=False
            )

            pnl = print_step_5(candidate_trades)
            if candidate is None:
                confirmed = "NO"
            else:
                by_product = candidate_trades.groupby("symbol")["good"].mean()
                confirmed = (
                    "YES"
                    if (by_product > 0.60).any()
                    and candidate_trades.groupby("symbol")["day"].nunique().max() >= 2
                    else "NO"
                )
            print(f"\nConfirmed: {confirmed}")
            if pnl is not None:
                print(
                    "Implementation threshold cleared: "
                    f"{'YES' if pnl['theoretical_pnl_per_day'] > 10000 else 'NO'}"
                )
        finally:
            sys.stdout = original_stdout

    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
