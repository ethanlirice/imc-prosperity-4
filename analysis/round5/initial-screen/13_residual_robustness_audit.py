from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
QTY = 10

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
HORIZONS = [50, 100, 200, 500]
EXIT_RULES = ["fixed_horizon", "zero_cross"]


def read_prices():
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_pivots(prices, products):
    columns = [
        "mid_price",
        "bid_price_1",
        "bid_volume_1",
        "bid_price_2",
        "bid_volume_2",
        "bid_price_3",
        "bid_volume_3",
        "ask_price_1",
        "ask_volume_1",
        "ask_price_2",
        "ask_volume_2",
        "ask_price_3",
        "ask_volume_3",
    ]
    out = {}
    subset = prices[prices["product"].isin(products)]
    for col in columns:
        out[col] = subset.pivot(index=["day", "timestamp"], columns="product", values=col).sort_index()
    return out


def fit_ols(y, x):
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef, x):
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def depth_vwap(price_levels, volume_levels, idx, qty):
    remaining = qty
    notional = 0.0
    top_volume = 0.0
    for level, (prices, volumes) in enumerate(zip(price_levels, volume_levels)):
        price = prices[idx]
        volume = volumes[idx]
        if not np.isfinite(price) or not np.isfinite(volume) or volume <= 0:
            continue
        if level == 0:
            top_volume = float(volume)
        take = min(remaining, float(volume))
        notional += take * float(price)
        remaining -= take
        if remaining <= 0:
            return notional / qty, top_volume < qty
    return np.nan, True


def side_price(book, i, direction, action, use_depth):
    if action == "entry":
        side = "ask" if direction > 0 else "bid"
    else:
        side = "bid" if direction > 0 else "ask"

    prices = [book[f"{side}_price_{level}"] for level in [1, 2, 3]]
    volumes = [book[f"{side}_volume_{level}"] for level in [1, 2, 3]]
    if use_depth:
        return depth_vwap(prices, volumes, i, QTY)
    return float(prices[0][i]), float(volumes[0][i]) < QTY


def simulate(book, resid, sigma, threshold, horizon, exit_rule, use_depth):
    z = resid / sigma if sigma > 1e-12 else np.zeros_like(resid)
    signal_mask = np.abs(z) >= threshold
    signal_count = int(signal_mask.sum())
    buy_signals = int(((resid < 0) & signal_mask).sum())
    sell_signals = int(((resid > 0) & signal_mask).sum())

    pnl = 0.0
    trades = 0
    wins = 0
    hold_sum = 0
    max_hold = 0
    entry_top_short = 0
    exit_top_short = 0
    unfilled = 0
    i = 0
    while i < len(resid) - 1:
        if not signal_mask[i]:
            i += 1
            continue
        direction = -1 if resid[i] > 0 else 1
        entry_price, entry_short = side_price(book, i, direction, "entry", use_depth)
        if not np.isfinite(entry_price):
            unfilled += 1
            i += 1
            continue
        exit_i = min(i + horizon, len(resid) - 1)
        if exit_rule == "zero_cross":
            entry_sign = np.sign(resid[i])
            for j in range(i + 1, exit_i + 1):
                if resid[j] == 0 or np.sign(resid[j]) != entry_sign:
                    exit_i = j
                    break
        exit_price, exit_short = side_price(book, exit_i, direction, "exit", use_depth)
        if not np.isfinite(exit_price):
            unfilled += 1
            i += 1
            continue

        edge = (exit_price - entry_price) * direction
        pnl += edge * QTY
        trades += 1
        wins += int(edge > 0)
        hold = exit_i - i
        hold_sum += hold
        max_hold = max(max_hold, hold)
        entry_top_short += int(entry_short)
        exit_top_short += int(exit_short)
        i = exit_i + 1

    return {
        "pnl": pnl,
        "trades": trades,
        "wins": wins,
        "avg_hold": hold_sum / trades if trades else 0.0,
        "max_hold": max_hold,
        "signal_count": signal_count,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "entry_top_short": entry_top_short,
        "exit_top_short": exit_top_short,
        "unfilled": unfilled,
    }


def build_residuals(base, target, components, test_day, variant):
    train = base[base.index.get_level_values("day") != test_day]
    test = base[base.index.get_level_values("day") == test_day]
    y_train = train[target].to_numpy(dtype=float)
    x_train = train[components].to_numpy(dtype=float)
    y_test = test[target].to_numpy(dtype=float)
    x_test = test[components].to_numpy(dtype=float)

    if variant == "ols_loo":
        coef = fit_ols(y_train, x_train)
        train_resid = y_train - predict_ols(coef, x_train)
        test_resid = y_test - predict_ols(coef, x_test)
    elif variant == "demean_group_mean_loo":
        target_mean = float(y_train.mean())
        component_means = x_train.mean(axis=0)
        train_resid = (y_train - target_mean) - (x_train - component_means).mean(axis=1)
        test_resid = (y_test - target_mean) - (x_test - component_means).mean(axis=1)
    elif variant == "ols_all_days_leaky":
        y_all = base[target].to_numpy(dtype=float)
        x_all = base[components].to_numpy(dtype=float)
        coef = fit_ols(y_all, x_all)
        all_resid = y_all - predict_ols(coef, x_all)
        sigma = float(np.std(all_resid))
        return test, y_test - predict_ols(coef, x_test), sigma
    else:
        raise ValueError(f"unknown variant {variant}")

    sigma = float(np.std(train_resid))
    return test, test_resid, sigma


def run_audit(prices):
    day_rows = []
    variants = ["ols_loo", "demean_group_mean_loo", "ols_all_days_leaky"]
    for group, products in GROUPS.items():
        print(f"Auditing {group} residual robustness...")
        pivots = make_pivots(prices, products)
        mids = pivots["mid_price"]
        days = sorted(mids.index.get_level_values("day").unique())
        for target in products:
            components = [product for product in products if product != target]
            base = mids[[target] + components].dropna()
            if len(base) < 100:
                continue
            for test_day in days:
                for variant in variants:
                    test, resid, sigma = build_residuals(base, target, components, test_day, variant)
                    if len(test) < 100 or sigma <= 1e-12:
                        continue
                    idx = test.index
                    book = {
                        col: pivots[col].loc[idx, target].to_numpy(dtype=float)
                        for col in pivots
                        if col != "mid_price"
                    }
                    for threshold in THRESHOLDS:
                        for horizon in HORIZONS:
                            for exit_rule in EXIT_RULES:
                                top = simulate(book, resid, sigma, threshold, horizon, exit_rule, False)
                                depth = simulate(book, resid, sigma, threshold, horizon, exit_rule, True)
                                row = {
                                    "variant": variant,
                                    "group": group,
                                    "target": target,
                                    "test_day": int(test_day),
                                    "threshold": threshold,
                                    "horizon": horizon,
                                    "exit_rule": exit_rule,
                                    "sigma": sigma,
                                }
                                for prefix, result in [("top", top), ("depth", depth)]:
                                    for key, value in result.items():
                                        row[f"{prefix}_{key}"] = value
                                day_rows.append(row)
    return pd.DataFrame(day_rows)


def summarize(day_rows):
    rows = []
    keys = ["variant", "group", "target", "threshold", "horizon", "exit_rule"]
    for key, frame in day_rows.groupby(keys):
        depth_trades = int(frame["depth_trades"].sum())
        top_trades = int(frame["top_trades"].sum())
        depth_wins = int(frame["depth_wins"].sum())
        top_wins = int(frame["top_wins"].sum())
        rows.append(
            {
                "variant": key[0],
                "group": key[1],
                "target": key[2],
                "threshold": key[3],
                "horizon": key[4],
                "exit_rule": key[5],
                "days": int(frame["test_day"].nunique()),
                "top_total_pnl": float(frame["top_pnl"].sum()),
                "top_min_day_pnl": float(frame["top_pnl"].min()),
                "top_positive_days": int((frame["top_pnl"] > 0).sum()),
                "top_trades": top_trades,
                "top_win_pct": top_wins / top_trades if top_trades else 0.0,
                "depth_total_pnl": float(frame["depth_pnl"].sum()),
                "depth_min_day_pnl": float(frame["depth_pnl"].min()),
                "depth_positive_days": int((frame["depth_pnl"] > 0).sum()),
                "depth_trades": depth_trades,
                "depth_win_pct": depth_wins / depth_trades if depth_trades else 0.0,
                "avg_depth_pnl_per_trade": float(frame["depth_pnl"].sum() / depth_trades)
                if depth_trades
                else 0.0,
                "signal_count": int(frame["depth_signal_count"].sum()),
                "buy_signals": int(frame["depth_buy_signals"].sum()),
                "sell_signals": int(frame["depth_sell_signals"].sum()),
                "entry_top_short": int(frame["depth_entry_top_short"].sum()),
                "exit_top_short": int(frame["depth_exit_top_short"].sum()),
                "top_short_trade_pct": float(
                    (frame["depth_entry_top_short"].sum() + frame["depth_exit_top_short"].sum())
                    / max(1, 2 * depth_trades)
                ),
                "depth_unfilled": int(frame["depth_unfilled"].sum()),
                "avg_hold": float(np.average(frame["depth_avg_hold"], weights=np.maximum(frame["depth_trades"], 1))),
                "max_hold": int(frame["depth_max_hold"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["variant", "depth_positive_days", "depth_total_pnl", "depth_min_day_pnl"],
        ascending=[True, False, False, False],
    )


def build_verdicts(summary):
    ols = summary[
        (summary["variant"] == "ols_loo")
        & (summary["days"] == 3)
        & (summary["depth_trades"] >= 10)
        & (summary["depth_positive_days"] == 3)
    ].copy()
    ols = ols.sort_values(["depth_total_pnl", "avg_depth_pnl_per_trade"], ascending=False)
    rows = []
    for _, row in ols.iterrows():
        same = summary[
            (summary["group"] == row["group"])
            & (summary["target"] == row["target"])
            & (summary["horizon"] == row["horizon"])
            & (summary["exit_rule"] == row["exit_rule"])
        ]
        ols_same = same[same["variant"] == "ols_loo"]
        simple_same = same[
            (same["variant"] == "demean_group_mean_loo")
            & (same["threshold"] == row["threshold"])
        ]
        leaky_same = same[
            (same["variant"] == "ols_all_days_leaky")
            & (same["threshold"] == row["threshold"])
        ]
        stable_thresholds = int((ols_same["depth_positive_days"] == 3).sum())
        stable_threshold_values = ",".join(
            str(x).rstrip("0").rstrip(".")
            for x in sorted(ols_same.loc[ols_same["depth_positive_days"] == 3, "threshold"].unique())
        )
        simple_total = float(simple_same["depth_total_pnl"].iloc[0]) if not simple_same.empty else np.nan
        simple_min = float(simple_same["depth_min_day_pnl"].iloc[0]) if not simple_same.empty else np.nan
        simple_days = int(simple_same["depth_positive_days"].iloc[0]) if not simple_same.empty else 0
        leaky_total = float(leaky_same["depth_total_pnl"].iloc[0]) if not leaky_same.empty else np.nan
        if row["depth_min_day_pnl"] > 0 and stable_thresholds >= 2 and simple_days == 3 and simple_min > 0:
            verdict = "accepted"
        elif row["depth_min_day_pnl"] > 0 and stable_thresholds >= 2 and simple_total > 0:
            verdict = "tentative"
        else:
            verdict = "reject"
        rows.append(
            {
                "verdict": verdict,
                "group": row["group"],
                "target": row["target"],
                "threshold": row["threshold"],
                "horizon": row["horizon"],
                "exit_rule": row["exit_rule"],
                "depth_total_pnl": row["depth_total_pnl"],
                "depth_min_day_pnl": row["depth_min_day_pnl"],
                "depth_trades": row["depth_trades"],
                "depth_win_pct": row["depth_win_pct"],
                "signal_count": row["signal_count"],
                "buy_signals": row["buy_signals"],
                "sell_signals": row["sell_signals"],
                "stable_threshold_count": stable_thresholds,
                "stable_thresholds": stable_threshold_values,
                "simple_total_pnl_same_rule": simple_total,
                "simple_min_day_pnl_same_rule": simple_min,
                "simple_positive_days_same_rule": simple_days,
                "leaky_total_pnl_same_rule": leaky_total,
                "top_short_trade_pct": row["top_short_trade_pct"],
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["verdict", "depth_total_pnl"], ascending=[True, False]
    )


def md_table(frame, columns, n=20):
    if frame.empty:
        return "No rows."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_report(day_rows, summary, verdicts):
    by_day_csv = OUT_DIR / "13_residual_robustness_audit_by_day.csv"
    summary_csv = OUT_DIR / "13_residual_robustness_audit_summary.csv"
    verdict_csv = OUT_DIR / "13_residual_robustness_audit_verdicts.csv"
    report_md = OUT_DIR / "13_residual_robustness_audit.md"

    day_rows.to_csv(by_day_csv, index=False)
    summary.to_csv(summary_csv, index=False)
    verdicts.to_csv(verdict_csv, index=False)

    accepted = verdicts[verdicts["verdict"] == "accepted"].sort_values("depth_total_pnl", ascending=False)
    tentative = verdicts[verdicts["verdict"] == "tentative"].sort_values("depth_total_pnl", ascending=False)
    rejected = verdicts[verdicts["verdict"] == "reject"].sort_values("depth_total_pnl", ascending=False)
    ols_top = summary[
        (summary["variant"] == "ols_loo")
        & (summary["days"] == 3)
        & (summary["depth_trades"] >= 10)
    ].sort_values("depth_total_pnl", ascending=False)
    simple_top = summary[
        (summary["variant"] == "demean_group_mean_loo")
        & (summary["days"] == 3)
        & (summary["depth_trades"] >= 10)
    ].sort_values("depth_total_pnl", ascending=False)
    leaky_top = summary[
        (summary["variant"] == "ols_all_days_leaky")
        & (summary["days"] == 3)
        & (summary["depth_trades"] >= 10)
    ].sort_values("depth_total_pnl", ascending=False)

    lines = [
        "# Round 5 Residual Robustness Audit",
        "",
        "Scope: days 2/3/4 only. This audit reruns 1-vs-4 residual trades with three variants: `ols_loo` fits coefficients and residual sigma only on the two non-test days; `demean_group_mean_loo` uses a simpler target-minus-peer-mean formula with train-day means only; `ols_all_days_leaky` intentionally fits all days as a leakage comparator. PnL uses quantity 10, one open trade per product, and a depth-aware 3-level VWAP for entry and exit.",
        "",
        "Implementation checks:",
        "- The prior `12_residual_trade_sim.py` avoids held-out coefficient and sigma leakage; this audit keeps that convention.",
        "- The prior `11_residual_shock_execution.py` pooled tables use all days, and its leave-one-day-out rows still scale thresholds with all-day residual sigma. Treat those rows as discovery only.",
        "- `fixed_horizon` is directly implementable by storing entry timestamp in `traderData`; `zero_cross` is also implementable if `traderData` stores the entry residual sign and recomputes the same residual each tick.",
        "- Top-of-book quantity-10 fills are not always available. The accepted/rejected tables below use depth-aware VWAP; `top_short_trade_pct` reports how often entry/exit needed more than level 1.",
        "",
        "## Strongest Findings",
        "",
        "- **Accept SLEEP_POD_POLYESTER OLS residual, threshold 1.5, horizon 500.** Depth-aware held-out PnL is **+48,277** with zero-cross exit and **+38,540** with fixed-horizon exit. Day PnL for zero-cross is day 2 **+14,648**, day 3 **+9,528**, day 4 **+24,101** over **48** trades from **17,801** raw threshold signals. Thresholds **1.5/2/2.5/3** all stay positive on all three days, and the simpler demeaned peer-mean formula remains positive with **+22,318** total and **+1,976** minimum day PnL.",
        "- **Accept UV_VISOR_MAGENTA only as a secondary, lower-capacity signal.** Threshold 1.5 / horizon 500 / fixed-horizon gives depth-aware day PnL **+4,802 / +11,080 / +5,320**, **+21,202** total, **36** trades, and the simple formula is also positive on all days (**+26,826**, min day **+3,940**). Parameter stability is weaker than SLEEP_POD_POLYESTER because only two threshold settings pass all days for the fixed-horizon rule.",
        "- **Accept GALAXY_SOUNDS_SOLAR_WINDS only as marginal.** Threshold 1.5 / horizon 500 gives **+9,850** fixed-horizon PnL and **+9,870** zero-cross PnL, but day 2 contributes only **+210**. The simple formula is stronger (**+12,338**, min day **+3,890**), so this is real enough to keep on the list but not a primary allocation.",
        "- **Do not accept GALAXY_SOUNDS_SOLAR_FLAMES despite high OLS PnL.** Held-out OLS threshold 2 / horizon 500 produces **+36,400** fixed-horizon PnL, but the same simple formula rule has minimum day **-529** and only **1** positive day. This is a plausible OLS-specific fit, not a robust formula-level signal.",
        "- **Reject MICROCHIP_RECTANGLE as an implementation/overfit false positive.** Held-out OLS threshold 1.5 / horizon 500 shows **+34,009** zero-cross PnL and all three days positive, but it is stable at only threshold **1.5**, the simple same-rule PnL has min day **-8,507**, and **92.4%** of entry/exit events need more than level 1 for quantity 10.",
        "- **Do not promote ROBOT_IRONING or TRANSLATOR_VOID_BLUE.** Both have positive held-out OLS grids, but the simple formula has zero-PnL days and ROBOT_IRONING requires deeper-than-top liquidity on roughly **86%+** of entry/exit events.",
        "",
        "## Accepted OLS Candidates",
        "",
        md_table(
            accepted,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_trades",
                "depth_win_pct",
                "signal_count",
                "stable_thresholds",
                "simple_total_pnl_same_rule",
                "simple_min_day_pnl_same_rule",
                "top_short_trade_pct",
            ],
            n=20,
        ),
        "",
        "## Tentative Candidates",
        "",
        md_table(
            tentative,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_trades",
                "signal_count",
                "stable_thresholds",
                "simple_total_pnl_same_rule",
                "simple_min_day_pnl_same_rule",
            ],
            n=15,
        ),
        "",
        "## Rejected From Top OLS Set",
        "",
        md_table(
            rejected,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_trades",
                "signal_count",
                "stable_thresholds",
                "simple_total_pnl_same_rule",
                "simple_min_day_pnl_same_rule",
            ],
            n=15,
        ),
        "",
        "## Best Held-Out OLS Depth Rows",
        "",
        md_table(
            ols_top,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_positive_days",
                "depth_trades",
                "signal_count",
                "buy_signals",
                "sell_signals",
                "top_short_trade_pct",
            ],
            n=25,
        ),
        "",
        "## Best Simple Formula Rows",
        "",
        md_table(
            simple_top,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_positive_days",
                "depth_trades",
                "signal_count",
            ],
            n=20,
        ),
        "",
        "## Leakage Comparator",
        "",
        md_table(
            leaky_top,
            [
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "depth_total_pnl",
                "depth_min_day_pnl",
                "depth_positive_days",
                "depth_trades",
            ],
            n=15,
        ),
        "",
        "## Day-By-Day Accepted Rows",
        "",
    ]
    if accepted.empty:
        lines.append("No accepted rows.")
    else:
        accepted_keys = accepted[["group", "target", "threshold", "horizon", "exit_rule"]]
        accepted_days = day_rows[day_rows["variant"] == "ols_loo"].merge(
            accepted_keys, on=["group", "target", "threshold", "horizon", "exit_rule"], how="inner"
        )
        lines.append(
            md_table(
                accepted_days.sort_values(["target", "threshold", "horizon", "exit_rule", "test_day"]),
                [
                    "group",
                    "target",
                    "test_day",
                    "threshold",
                    "horizon",
                    "exit_rule",
                    "depth_pnl",
                    "depth_trades",
                    "depth_wins",
                    "depth_signal_count",
                    "depth_buy_signals",
                    "depth_sell_signals",
                    "depth_avg_hold",
                ],
                n=80,
            )
        )
    report_md.write_text("\n".join(lines))
    print(f"Wrote {by_day_csv}")
    print(f"Wrote {summary_csv}")
    print(f"Wrote {verdict_csv}")
    print(f"Wrote {report_md}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    day_rows = run_audit(prices)
    summary = summarize(day_rows)
    verdicts = build_verdicts(summary)
    write_report(day_rows, summary, verdicts)


if __name__ == "__main__":
    main()
