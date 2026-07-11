import math
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

HORIZONS = [1, 2, 5, 10, 20, 50, 100, 200, 500]
THRESHOLDS = [1.5, 2.0, 2.5, 3.0]


def read_prices():
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv")):
        frame = pd.read_csv(path, sep=";")
        frames.append(frame)
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_group_frame(prices, products):
    value_cols = ["mid_price", "bid_price_1", "ask_price_1"]
    pieces = {}
    for col in value_cols:
        pieces[col] = (
            prices[prices["product"].isin(products)]
            .pivot(index=["day", "timestamp"], columns="product", values=col)
            .sort_index()
        )
    return pieces


def fit_ols(y, x):
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef, x):
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def adf_t_stat(resid):
    if len(resid) < 20:
        return float("nan")
    lagged = resid[:-1]
    delta = np.diff(resid)
    x = np.column_stack([np.ones_like(lagged), lagged])
    try:
        coef = np.linalg.lstsq(x, delta, rcond=None)[0]
        err = delta - x @ coef
        dof = max(1, len(delta) - x.shape[1])
        sigma2 = float(err @ err / dof)
        inv = np.linalg.inv(x.T @ x)
        se = math.sqrt(max(0.0, sigma2 * inv[1, 1]))
        return float(coef[1] / se) if se > 1e-12 else float("nan")
    except np.linalg.LinAlgError:
        return float("nan")


def safe_mean(values):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    return float(arr.mean()) if len(arr) else float("nan")


def summarize_events(events):
    if not events:
        return pd.DataFrame()
    raw = pd.DataFrame(events)
    rows = []
    keys = ["fit_mode", "group", "target", "threshold", "horizon"]
    for key, frame in raw.groupby(keys):
        day_mean = frame.groupby("day")["roundtrip_edge"].mean()
        day_mid = frame.groupby("day")["mid_edge"].mean()
        rows.append(
            {
                "fit_mode": key[0],
                "group": key[1],
                "target": key[2],
                "threshold": key[3],
                "horizon": key[4],
                "n": int(len(frame)),
                "days": int(frame["day"].nunique()),
                "buy_share": float((frame["direction"] > 0).mean()),
                "mid_edge": safe_mean(frame["mid_edge"]),
                "entry_active_edge": safe_mean(frame["entry_active_edge"]),
                "roundtrip_edge": safe_mean(frame["roundtrip_edge"]),
                "roundtrip_good_pct": float((frame["roundtrip_edge"] > 0).mean()),
                "positive_roundtrip_days": int((day_mean > 0).sum()),
                "min_day_roundtrip_edge": float(day_mean.min()),
                "min_day_mid_edge": float(day_mid.min()),
                "signal_abs_resid_mean": safe_mean(frame["abs_resid"]),
                "resid_sigma": safe_mean(frame["resid_sigma"]),
                "adf_t": safe_mean(frame["adf_t"]),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(
        ["positive_roundtrip_days", "roundtrip_edge", "n"],
        ascending=[False, False, False],
    )


def scan(prices):
    events = []
    for group, products in GROUPS.items():
        print(f"Scanning {group} residual execution...")
        frames = make_group_frame(prices, products)
        mids = frames["mid_price"]
        bids = frames["bid_price_1"]
        asks = frames["ask_price_1"]
        for target in products:
            components = [product for product in products if product != target]
            base = mids[[target] + components].dropna()
            if base.empty:
                continue
            y_all = base[target].to_numpy(dtype=float)
            x_all = base[components].to_numpy(dtype=float)
            pooled_coef = fit_ols(y_all, x_all)
            fit_specs = [("pooled_all_days", pooled_coef)]
            for heldout_day in sorted(base.index.get_level_values("day").unique()):
                train = base[base.index.get_level_values("day") != heldout_day]
                if len(train) < 50:
                    continue
                fit_specs.append(
                    (
                        f"leaveout_test_day_{int(heldout_day)}",
                        fit_ols(train[target].to_numpy(dtype=float), train[components].to_numpy(dtype=float)),
                    )
                )

            for fit_mode, coef in fit_specs:
                pred_all = predict_ols(coef, x_all)
                resid_all = y_all - pred_all
                sigma = float(np.std(resid_all))
                if sigma <= 1e-12:
                    continue
                adf_t = adf_t_stat(resid_all)
                for day in sorted(base.index.get_level_values("day").unique()):
                    if fit_mode.startswith("leaveout_test_day_"):
                        test_day = int(fit_mode.rsplit("_", 1)[-1])
                        if int(day) != test_day:
                            continue
                    day_base = base[base.index.get_level_values("day") == day]
                    idx = day_base.index
                    y = day_base[target].to_numpy(dtype=float)
                    x = day_base[components].to_numpy(dtype=float)
                    resid = y - predict_ols(coef, x)
                    z = resid / sigma
                    day_bid = bids.loc[idx, target].to_numpy(dtype=float)
                    day_ask = asks.loc[idx, target].to_numpy(dtype=float)
                    for threshold in THRESHOLDS:
                        signal_idx = np.flatnonzero(np.abs(z) >= threshold)
                        if len(signal_idx) == 0:
                            continue
                        for horizon in HORIZONS:
                            usable = signal_idx[signal_idx + horizon < len(y)]
                            if len(usable) == 0:
                                continue
                            direction = -np.sign(resid[usable])
                            future_mid = y[usable + horizon]
                            future_bid = day_bid[usable + horizon]
                            future_ask = day_ask[usable + horizon]
                            entry_ask = day_ask[usable]
                            entry_bid = day_bid[usable]
                            mid_edge = direction * (future_mid - y[usable])
                            entry_active_edge = np.where(
                                direction > 0,
                                future_mid - entry_ask,
                                entry_bid - future_mid,
                            )
                            roundtrip_edge = np.where(
                                direction > 0,
                                future_bid - entry_ask,
                                entry_bid - future_ask,
                            )
                            for j, pos in enumerate(usable):
                                events.append(
                                    {
                                        "fit_mode": fit_mode,
                                        "group": group,
                                        "target": target,
                                        "day": int(day),
                                        "threshold": threshold,
                                        "horizon": horizon,
                                        "direction": float(direction[j]),
                                        "mid_edge": float(mid_edge[j]),
                                        "entry_active_edge": float(entry_active_edge[j]),
                                        "roundtrip_edge": float(roundtrip_edge[j]),
                                        "abs_resid": float(abs(resid[pos])),
                                        "resid_sigma": sigma,
                                        "adf_t": adf_t,
                                    }
                                )
    return summarize_events(events)


def md_table(frame, columns, n=25):
    if frame.empty:
        return "No rows passed the filter."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_report(summary):
    out_csv = OUT_DIR / "11_residual_shock_execution.csv"
    out_md = OUT_DIR / "11_residual_shock_execution.md"
    summary.to_csv(out_csv, index=False)

    stable = summary[
        (summary["n"] >= 100)
        & (summary["days"] == 3)
        & (summary["positive_roundtrip_days"] == 3)
    ].sort_values(["roundtrip_edge", "n"], ascending=False)
    loo = summary[
        (summary["fit_mode"].str.startswith("leaveout_test_day_"))
        & (summary["n"] >= 30)
        & (summary["roundtrip_edge"] > 0)
    ].sort_values(["roundtrip_edge", "n"], ascending=False)
    fast = stable[stable["horizon"] <= 50].sort_values(["roundtrip_edge", "n"], ascending=False)
    pooled_top = summary[
        (summary["fit_mode"] == "pooled_all_days")
        & (summary["n"] >= 100)
    ].sort_values(["roundtrip_edge", "n"], ascending=False)

    lines = [
        "# Round 5 Residual Shock Execution Check",
        "",
        "Validates OLS 1-vs-4 residual shocks using active entry and active exit costs. `roundtrip_edge` assumes buying at current ask and selling at future bid, or selling at current bid and buying back at future ask. Leave-one-day-out rows fit on two sample days and test only on the held-out day.",
        "",
        "## Stable Pooled Candidates",
        "",
        md_table(
            stable,
            [
                "fit_mode",
                "group",
                "target",
                "threshold",
                "horizon",
                "n",
                "buy_share",
                "mid_edge",
                "entry_active_edge",
                "roundtrip_edge",
                "roundtrip_good_pct",
                "min_day_roundtrip_edge",
                "resid_sigma",
                "adf_t",
            ],
        ),
        "",
        "## Fast Stable Candidates",
        "",
        md_table(
            fast,
            [
                "fit_mode",
                "group",
                "target",
                "threshold",
                "horizon",
                "n",
                "mid_edge",
                "entry_active_edge",
                "roundtrip_edge",
                "roundtrip_good_pct",
                "min_day_roundtrip_edge",
            ],
        ),
        "",
        "## Leave-One-Day-Out Positive Tests",
        "",
        md_table(
            loo,
            [
                "fit_mode",
                "group",
                "target",
                "threshold",
                "horizon",
                "n",
                "mid_edge",
                "entry_active_edge",
                "roundtrip_edge",
                "roundtrip_good_pct",
                "min_day_roundtrip_edge",
            ],
            n=40,
        ),
        "",
        "## Pooled Top By Roundtrip Edge",
        "",
        md_table(
            pooled_top,
            [
                "fit_mode",
                "group",
                "target",
                "threshold",
                "horizon",
                "n",
                "days",
                "positive_roundtrip_days",
                "mid_edge",
                "entry_active_edge",
                "roundtrip_edge",
                "roundtrip_good_pct",
                "min_day_roundtrip_edge",
            ],
            n=40,
        ),
    ]
    out_md.write_text("\n".join(lines))
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    summary = scan(prices)
    write_report(summary)


if __name__ == "__main__":
    main()
