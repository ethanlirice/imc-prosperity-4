from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
PRODUCTS = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
PAR = 50000


def load_pebbles_books() -> dict[int, pd.DataFrame]:
    prices = pd.concat(
        [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))],
        ignore_index=True,
    )
    prices = prices[prices["product"].isin(PRODUCTS)]
    out = {}
    for day, d in prices.groupby("day"):
        rows = []
        for t, g in d.groupby("timestamp"):
            if set(g["product"]) != set(PRODUCTS):
                continue
            gg = g.set_index("product")
            row = {"timestamp": int(t)}
            for prefix, col in [
                ("bid", "bid_price_1"),
                ("ask", "ask_price_1"),
                ("mid", "mid_price"),
            ]:
                row[f"{prefix}_sum"] = float(sum(gg.loc[p, col] for p in PRODUCTS))
            rows.append(row)
        out[int(day)] = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return out


def sim_day(df: pd.DataFrame, buy_sum: float, exit_sum: float, qty: int, max_baskets: int, ttl: int) -> dict:
    inv = 0
    cash = 0.0
    entry_times: list[int] = []
    buy_count = 0
    sell_count = 0
    for r in df.itertuples(index=False):
        if inv > 0 and (r.bid_sum >= exit_sum or (ttl > 0 and entry_times and r.timestamp - entry_times[0] >= ttl)):
            q = inv
            cash += q * r.bid_sum
            sell_count += q
            inv = 0
            entry_times = []
        if inv < max_baskets and r.ask_sum <= buy_sum:
            q = min(qty, max_baskets - inv)
            cash -= q * r.ask_sum
            inv += q
            buy_count += q
            entry_times.extend([r.timestamp] * q)
    cash += inv * float(df.iloc[-1]["mid_sum"])
    return {"pnl": cash, "buy_baskets": buy_count, "sell_baskets": sell_count, "end_inv": inv}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = load_pebbles_books()
    rows = []
    for buy_sum in [49996, 49997, 49998, 49999, 50000]:
        for exit_sum in [49998, 49999, 50000]:
            for qty in [1, 2, 5, 10]:
                for max_baskets in [1, 2, 5, 10]:
                    for ttl in [0, 100, 200, 500, 1000, 2000, 5000]:
                        row = {
                            "buy_sum": buy_sum,
                            "exit_sum": exit_sum,
                            "qty": qty,
                            "max_baskets": max_baskets,
                            "ttl": ttl,
                        }
                        for day, df in books.items():
                            result = sim_day(df, buy_sum, exit_sum, qty, max_baskets, ttl)
                            for k, v in result.items():
                                row[f"d{day}_{k}"] = v
                        row["sum_pnl"] = sum(row.get(f"d{day}_pnl", 0.0) for day in books)
                        row["min_day_pnl"] = min(row.get(f"d{day}_pnl", 0.0) for day in books)
                        rows.append(row)
    out = pd.DataFrame(rows).sort_values(["min_day_pnl", "sum_pnl"], ascending=False)
    out.to_csv(OUT_DIR / "09_pebbles_executable_basket.csv", index=False)
    lines = [
        "# Round 5 PEBBLES Executable Basket Proxy",
        "",
        "Tests the direct identity `PEBBLES_XS + PEBBLES_S + PEBBLES_M + PEBBLES_L + PEBBLES_XL ~= 50000`.",
        "Rule: buy one full 5-leg basket when sum(best asks) <= `buy_sum`; exit all inventory when sum(best bids) >= `exit_sum`, or after TTL if TTL > 0. End inventory is marked to sum(mid).",
        "",
        "## Top Robust Parameter Sets",
        "",
        out.head(30).round(3).to_markdown(index=False),
        "",
    ]
    (OUT_DIR / "09_pebbles_executable_basket.md").write_text("\n".join(lines))
    print(out.head(30).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
