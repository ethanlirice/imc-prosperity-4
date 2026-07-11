from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT = Path(__file__).resolve().parent / "executable_mark14_edge_output.txt"

TRADER = "Mark 14"
HORIZON = 200


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

    return pd.concat(trades, ignore_index=True), pd.concat(prices, ignore_index=True)


def first_row_after(frame, timestamp):
    rows = frame[frame["timestamp"] > timestamp]
    if len(rows) == 0:
        return None
    return rows.iloc[0]


def last_mid_within(frame, timestamp, horizon):
    rows = frame[
        (frame["timestamp"] > timestamp)
        & (frame["timestamp"] <= timestamp + horizon)
    ]
    if len(rows) == 0:
        return None
    return float(rows.iloc[-1]["mid_price"])


def main():
    trades, prices = load_data()
    price_lookup = {
        (day, product): frame.sort_values("timestamp").reset_index(drop=True)
        for (day, product), frame in prices.groupby(["day", "product"])
    }

    rows = []
    for _, trade in trades.iterrows():
        if trade["buyer"] != TRADER and trade["seller"] != TRADER:
            continue

        side = "buy" if trade["buyer"] == TRADER else "sell"
        day = int(trade["day"])
        symbol = trade["symbol"]
        frame = price_lookup[(day, symbol)]
        entry_row = first_row_after(frame, int(trade["timestamp"]))
        if entry_row is None:
            continue

        entry_ts = int(entry_row["timestamp"])
        if side == "buy":
            entry_px = entry_row["ask_price_1"]
            if pd.isna(entry_px):
                continue
            trade_edge_px = float(trade["price"])
            slippage = float(entry_px) - trade_edge_px
            future_original = last_mid_within(frame, int(trade["timestamp"]), HORIZON)
            future_entry = last_mid_within(frame, entry_ts, HORIZON)
            if future_original is None or future_entry is None:
                continue
            historical_edge = future_original - trade_edge_px
            executable_edge = future_entry - float(entry_px)
        else:
            entry_px = entry_row["bid_price_1"]
            if pd.isna(entry_px):
                continue
            trade_edge_px = float(trade["price"])
            slippage = trade_edge_px - float(entry_px)
            future_original = last_mid_within(frame, int(trade["timestamp"]), HORIZON)
            future_entry = last_mid_within(frame, entry_ts, HORIZON)
            if future_original is None or future_entry is None:
                continue
            historical_edge = trade_edge_px - future_original
            executable_edge = float(entry_px) - future_entry

        rows.append(
            {
                "day": day,
                "symbol": symbol,
                "timestamp": int(trade["timestamp"]),
                "entry_ts": entry_ts,
                "side": side,
                "qty": int(trade["quantity"]),
                "mark_price": trade_edge_px,
                "entry_px": float(entry_px),
                "historical_edge": historical_edge,
                "executable_edge": executable_edge,
                "slippage": slippage,
                "qty_executable_edge": executable_edge * int(trade["quantity"]),
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(Path(__file__).resolve().parent / "executable_mark14_edge.csv", index=False)

    with OUT.open("w") as fh:
        print("Mark 14 executable next-tick copy edge", file=fh)
        print(f"Rows: {len(result)}", file=fh)
        print("\nBy product:", file=fh)
        by_product = (
            result.groupby("symbol")
            .agg(
                trades=("executable_edge", "count"),
                hist_good_pct=("historical_edge", lambda x: (x > 0).mean()),
                exec_good_pct=("executable_edge", lambda x: (x > 0).mean()),
                hist_mean_edge=("historical_edge", "mean"),
                exec_mean_edge=("executable_edge", "mean"),
                mean_slippage=("slippage", "mean"),
                exec_unit_edge=("executable_edge", "sum"),
                exec_qty_edge=("qty_executable_edge", "sum"),
            )
            .sort_values("exec_unit_edge", ascending=False)
        )
        print(by_product.to_string(), file=fh)

        print("\nBy product/side:", file=fh)
        by_side = (
            result.groupby(["symbol", "side"])
            .agg(
                trades=("executable_edge", "count"),
                exec_good_pct=("executable_edge", lambda x: (x > 0).mean()),
                exec_mean_edge=("executable_edge", "mean"),
                mean_slippage=("slippage", "mean"),
                exec_unit_edge=("executable_edge", "sum"),
                exec_qty_edge=("qty_executable_edge", "sum"),
            )
            .sort_values("exec_unit_edge", ascending=False)
        )
        print(by_side.to_string(), file=fh)

    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
