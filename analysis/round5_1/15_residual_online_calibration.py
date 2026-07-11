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

CANDIDATES = [
    ("SLEEP_POD", "SLEEP_POD_POLYESTER"),
    ("GALAXY_SOUNDS", "GALAXY_SOUNDS_SOLAR_FLAMES"),
    ("MICROCHIP", "MICROCHIP_RECTANGLE"),
    ("ROBOT", "ROBOT_IRONING"),
    ("TRANSLATOR", "TRANSLATOR_VOID_BLUE"),
    ("UV_VISOR", "UV_VISOR_MAGENTA"),
    ("OXYGEN_SHAKE", "OXYGEN_SHAKE_MINT"),
    ("PANEL", "PANEL_2X2"),
    ("SNACKPACK", "SNACKPACK_STRAWBERRY"),
    ("PEBBLES", "PEBBLES_S"),
    ("PEBBLES", "PEBBLES_XL"),
]

THRESHOLDS = [1.5, 2.0, 2.5, 3.0]
HORIZONS = [50, 100, 200, 500]
QTY = 10


def read_prices():
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True).sort_values(["day", "timestamp", "product"])


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


def past_rolling_mean(arr, window):
    out = np.full(len(arr), np.nan)
    csum = np.cumsum(np.insert(arr, 0, 0.0))
    for i in range(1, len(arr)):
        start = max(0, i - window)
        count = i - start
        out[i] = (csum[i] - csum[start]) / count if count else np.nan
    return out


def centered_signal(resid, mode):
    if mode == "raw":
        return resid.copy()
    if mode == "open100":
        out = resid.copy()
        if len(out) > 100:
            out = out - np.mean(out[:100])
            out[:100] = np.nan
        return out
    if mode == "open500":
        out = resid.copy()
        if len(out) > 500:
            out = out - np.mean(out[:500])
            out[:500] = np.nan
        return out
    if mode == "rolling200":
        return resid - past_rolling_mean(resid, 200)
    if mode == "rolling500":
        return resid - past_rolling_mean(resid, 500)
    raise ValueError(mode)


def simulate(sig, bid, ask, sigma, threshold, horizon):
    pnl = 0.0
    trades = 0
    wins = 0
    hold_sum = 0
    i = 0
    while i < len(sig) - 1:
        value = sig[i]
        if not np.isfinite(value) or abs(value / sigma) < threshold:
            i += 1
            continue
        direction = -1 if value > 0 else 1
        exit_i = min(i + horizon, len(sig) - 1)
        entry = ask[i] if direction > 0 else bid[i]
        exit_price = bid[exit_i] if direction > 0 else ask[exit_i]
        edge = (exit_price - entry) * direction
        pnl += edge * QTY
        trades += 1
        wins += int(edge > 0)
        hold_sum += exit_i - i
        i = exit_i + 1
    return {
        "pnl": pnl,
        "trades": trades,
        "wins": wins,
        "avg_hold": hold_sum / trades if trades else 0.0,
    }


def run(prices):
    rows = []
    for group, target in CANDIDATES:
        print(f"Calibrating {target}...")
        products = GROUPS[group]
        components = [product for product in products if product != target]
        pivots = make_pivots(prices, products)
        mids = pivots["mid_price"]
        bids = pivots["bid_price_1"]
        asks = pivots["ask_price_1"]
        base = mids[[target] + components].dropna()
        days = sorted(base.index.get_level_values("day").unique())
        for test_day in days:
            train = base[base.index.get_level_values("day") != test_day]
            test = base[base.index.get_level_values("day") == test_day]
            coef = fit_ols(train[target].to_numpy(dtype=float), train[components].to_numpy(dtype=float))
            train_resid = train[target].to_numpy(dtype=float) - predict_ols(
                coef, train[components].to_numpy(dtype=float)
            )
            sigma = float(np.std(train_resid))
            if sigma <= 1e-12:
                continue
            y = test[target].to_numpy(dtype=float)
            resid = y - predict_ols(coef, test[components].to_numpy(dtype=float))
            idx = test.index
            bid = bids.loc[idx, target].to_numpy(dtype=float)
            ask = asks.loc[idx, target].to_numpy(dtype=float)
            for mode in ["raw", "open100", "open500", "rolling200", "rolling500"]:
                sig = centered_signal(resid, mode)
                for threshold in THRESHOLDS:
                    for horizon in HORIZONS:
                        result = simulate(sig, bid, ask, sigma, threshold, horizon)
                        rows.append(
                            {
                                "group": group,
                                "target": target,
                                "test_day": int(test_day),
                                "center_mode": mode,
                                "threshold": threshold,
                                "horizon": horizon,
                                "pnl": result["pnl"],
                                "trades": result["trades"],
                                "wins": result["wins"],
                                "avg_hold": result["avg_hold"],
                                "sigma_train": sigma,
                            }
                        )
    return pd.DataFrame(rows)


def summarize(rows):
    out = []
    keys = ["group", "target", "center_mode", "threshold", "horizon"]
    for key, frame in rows.groupby(keys):
        trades = int(frame["trades"].sum())
        wins = int(frame["wins"].sum())
        out.append(
            {
                "group": key[0],
                "target": key[1],
                "center_mode": key[2],
                "threshold": key[3],
                "horizon": key[4],
                "days": int(frame["test_day"].nunique()),
                "total_pnl": float(frame["pnl"].sum()),
                "min_day_pnl": float(frame["pnl"].min()),
                "positive_days": int((frame["pnl"] > 0).sum()),
                "total_trades": trades,
                "win_pct": wins / trades if trades else 0.0,
                "avg_pnl_per_trade": float(frame["pnl"].sum() / trades) if trades else 0.0,
                "avg_hold": float(np.average(frame["avg_hold"], weights=np.maximum(frame["trades"], 1))),
            }
        )
    return pd.DataFrame(out).sort_values(
        ["center_mode", "positive_days", "total_pnl"], ascending=[True, False, False]
    )


def md_table(frame, columns, n=30):
    if frame.empty:
        return "No rows passed the filter."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_outputs(rows, summary):
    rows.to_csv(OUT_DIR / "15_residual_online_calibration_by_day.csv", index=False)
    summary.to_csv(OUT_DIR / "15_residual_online_calibration_summary.csv", index=False)

    robust = summary[
        (summary["days"] == 3)
        & (summary["positive_days"] == 3)
        & (summary["total_trades"] >= 10)
        & (summary["min_day_pnl"] > 0)
    ]
    non_raw = robust[robust["center_mode"] != "raw"].sort_values(
        ["total_pnl", "min_day_pnl"], ascending=False
    )
    raw = robust[robust["center_mode"] == "raw"].sort_values(
        ["total_pnl", "min_day_pnl"], ascending=False
    )
    best_mode = (
        robust.sort_values(["target", "total_pnl"], ascending=[True, False])
        .groupby(["group", "target"], as_index=False)
        .head(2)
        .sort_values("total_pnl", ascending=False)
    )

    lines = [
        "# Round 5 Residual Online Calibration Check",
        "",
        "Tests whether leave-one-day-out residual signals survive day-level intercept uncertainty. `raw` uses the held-out residual directly; `open100` and `open500` subtract only that day's first 100/500 residual observations; rolling modes subtract a past-only rolling mean.",
        "",
        "## Non-Raw Robust Candidates",
        "",
        md_table(
            non_raw,
            [
                "group",
                "target",
                "center_mode",
                "threshold",
                "horizon",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
            ],
        ),
        "",
        "## Raw Robust Candidates",
        "",
        md_table(
            raw,
            [
                "group",
                "target",
                "center_mode",
                "threshold",
                "horizon",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
            ],
        ),
        "",
        "## Best Modes By Candidate",
        "",
        md_table(
            best_mode,
            [
                "group",
                "target",
                "center_mode",
                "threshold",
                "horizon",
                "total_pnl",
                "min_day_pnl",
                "positive_days",
                "total_trades",
                "avg_pnl_per_trade",
            ],
            n=40,
        ),
    ]
    (OUT_DIR / "15_residual_online_calibration.md").write_text("\n".join(lines))
    print("Wrote notebooks/round5/15_residual_online_calibration.md")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    rows = run(prices)
    summary = summarize(rows)
    write_outputs(rows, summary)


if __name__ == "__main__":
    main()
