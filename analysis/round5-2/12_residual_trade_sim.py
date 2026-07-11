from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")

GROUPS = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": [
        "ROBOT_VACUUMING",
        "ROBOT_MOPPING",
        "ROBOT_DISHES",
        "ROBOT_LAUNDRY",
        "ROBOT_IRONING",
    ],
    "UV_VISOR": [
        "UV_VISOR_YELLOW",
        "UV_VISOR_AMBER",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_MAGENTA",
    ],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
}

THRESHOLDS = [1.5, 2.0, 2.5, 3.0]
HORIZONS = [20, 50, 100, 200, 500]
QTY = 10


def read_prices():
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_pivots(prices, products):
    pivots = {}
    for col in ["mid_price", "bid_price_1", "ask_price_1"]:
        pivots[col] = (
            prices[prices["product"].isin(products)]
            .pivot(index=["day", "timestamp"], columns="product", values=col)
            .sort_index()
        )
    return pivots


def fit_ols(y, x):
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef, x):
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def simulate_day(y, bid, ask, resid, sigma, threshold, horizon, exit_on_zero):
    pnl = 0.0
    trades = 0
    wins = 0
    hold_sum = 0
    max_hold = 0
    i = 0
    while i < len(y) - 1:
        z = resid[i] / sigma if sigma > 1e-12 else 0.0
        if abs(z) < threshold:
            i += 1
            continue
        direction = -1 if resid[i] > 0 else 1
        entry_price = ask[i] if direction > 0 else bid[i]
        exit_i = min(i + horizon, len(y) - 1)
        if exit_on_zero:
            for j in range(i + 1, exit_i + 1):
                if resid[j] == 0 or np.sign(resid[j]) != np.sign(resid[i]):
                    exit_i = j
                    break
        exit_price = bid[exit_i] if direction > 0 else ask[exit_i]
        edge = (exit_price - entry_price) * direction
        pnl += edge * QTY
        trades += 1
        wins += int(edge > 0)
        hold = exit_i - i
        hold_sum += hold
        max_hold = max(max_hold, hold)
        i = exit_i + 1
    return {
        "pnl": pnl,
        "trades": trades,
        "wins": wins,
        "avg_hold": hold_sum / trades if trades else 0.0,
        "max_hold": max_hold,
    }


def run_sim(prices):
    rows = []
    for group, products in GROUPS.items():
        print(f"Simulating {group} residual trades...")
        pivots = make_pivots(prices, products)
        mids = pivots["mid_price"]
        bids = pivots["bid_price_1"]
        asks = pivots["ask_price_1"]
        days = sorted(mids.index.get_level_values("day").unique())
        for target in products:
            components = [product for product in products if product != target]
            base = mids[[target] + components].dropna()
            for test_day in days:
                train = base[base.index.get_level_values("day") != test_day]
                test = base[base.index.get_level_values("day") == test_day]
                if len(train) < 100 or len(test) < 100:
                    continue
                coef = fit_ols(train[target].to_numpy(dtype=float), train[components].to_numpy(dtype=float))
                train_resid = train[target].to_numpy(dtype=float) - predict_ols(
                    coef, train[components].to_numpy(dtype=float)
                )
                sigma = float(np.std(train_resid))
                if sigma <= 1e-12:
                    continue
                y = test[target].to_numpy(dtype=float)
                x = test[components].to_numpy(dtype=float)
                resid = y - predict_ols(coef, x)
                idx = test.index
                bid = bids.loc[idx, target].to_numpy(dtype=float)
                ask = asks.loc[idx, target].to_numpy(dtype=float)
                for threshold in THRESHOLDS:
                    for horizon in HORIZONS:
                        for exit_on_zero in [False, True]:
                            result = simulate_day(y, bid, ask, resid, sigma, threshold, horizon, exit_on_zero)
                            rows.append(
                                {
                                    "group": group,
                                    "target": target,
                                    "test_day": int(test_day),
                                    "threshold": threshold,
                                    "horizon": horizon,
                                    "exit_rule": "zero_cross" if exit_on_zero else "fixed_horizon",
                                    "pnl": result["pnl"],
                                    "trades": result["trades"],
                                    "wins": result["wins"],
                                    "avg_hold": result["avg_hold"],
                                    "max_hold": result["max_hold"],
                                    "sigma_train": sigma,
                                }
                            )
    return pd.DataFrame(rows)


def summarize(day_rows):
    rows = []
    keys = ["group", "target", "threshold", "horizon", "exit_rule"]
    for key, frame in day_rows.groupby(keys):
        total_trades = int(frame["trades"].sum())
        total_wins = int(frame["wins"].sum())
        rows.append(
            {
                "group": key[0],
                "target": key[1],
                "threshold": key[2],
                "horizon": key[3],
                "exit_rule": key[4],
                "days": int(frame["test_day"].nunique()),
                "total_pnl": float(frame["pnl"].sum()),
                "min_day_pnl": float(frame["pnl"].min()),
                "positive_days": int((frame["pnl"] > 0).sum()),
                "total_trades": total_trades,
                "win_pct": total_wins / total_trades if total_trades else 0.0,
                "avg_pnl_per_trade": float(frame["pnl"].sum() / total_trades) if total_trades else 0.0,
                "avg_hold": float(np.average(frame["avg_hold"], weights=np.maximum(frame["trades"], 1))),
                "max_hold": int(frame["max_hold"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["positive_days", "total_pnl", "min_day_pnl"], ascending=[False, False, False]
    )


def md_table(frame, columns, n=30):
    if frame.empty:
        return "No rows passed the filter."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_outputs(day_rows, summary):
    day_csv = OUT_DIR / "12_residual_trade_sim_by_day.csv"
    sum_csv = OUT_DIR / "12_residual_trade_sim_summary.csv"
    report = OUT_DIR / "12_residual_trade_sim.md"
    day_rows.to_csv(day_csv, index=False)
    summary.to_csv(sum_csv, index=False)

    robust = summary[
        (summary["days"] == 3)
        & (summary["positive_days"] == 3)
        & (summary["total_trades"] >= 10)
        & (summary["min_day_pnl"] > 0)
    ].sort_values(["total_pnl", "avg_pnl_per_trade"], ascending=False)
    fast = robust[robust["horizon"] <= 100].sort_values(
        ["total_pnl", "avg_pnl_per_trade"], ascending=False
    )
    by_group = (
        robust.sort_values(["group", "total_pnl"], ascending=[True, False])
        .groupby("group", as_index=False)
        .head(3)
        .sort_values("total_pnl", ascending=False)
    )

    lines = [
        "# Round 5 Residual Trade Simulation",
        "",
        "Leave-one-day-out test: fit each 1-vs-4 OLS residual on two sample days, trade the held-out day only, cross the target leg at top of book, use quantity 10, and allow only one open trade per product at a time. This tests whether residual shock markouts survive position occupancy and spread cost.",
        "",
        "## Robust Candidates",
        "",
        md_table(
            robust,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
                "avg_hold",
            ],
        ),
        "",
        "## Fast Robust Candidates",
        "",
        md_table(
            fast,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
                "avg_hold",
            ],
        ),
        "",
        "## Best By Group",
        "",
        md_table(
            by_group,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "total_pnl",
                "min_day_pnl",
                "positive_days",
                "total_trades",
                "avg_pnl_per_trade",
            ],
            n=40,
        ),
        "",
        "## Top Day Rows",
        "",
        md_table(
            day_rows.sort_values("pnl", ascending=False),
            [
                "group",
                "target",
                "test_day",
                "threshold",
                "horizon",
                "exit_rule",
                "pnl",
                "trades",
                "wins",
                "avg_hold",
            ],
            n=40,
        ),
    ]
    report.write_text("\n".join(lines))
    print(f"Wrote {day_csv}")
    print(f"Wrote {sum_csv}")
    print(f"Wrote {report}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    day_rows = run_sim(prices)
    summary = summarize(day_rows)
    write_outputs(day_rows, summary)


if __name__ == "__main__":
    main()
