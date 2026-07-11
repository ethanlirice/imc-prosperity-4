from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
PRIOR_DIRS = [OUT_DIR, Path("notebooks/round5 2")]
QTY = 10

KEYS = ["group", "target", "threshold", "horizon", "exit_rule"]

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


def read_prices():
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def read_prior_csv(filename):
    for directory in PRIOR_DIRS:
        path = directory / filename
        if path.exists():
            return pd.read_csv(path)
    searched = ", ".join(str(directory / filename) for directory in PRIOR_DIRS)
    raise FileNotFoundError(f"Could not find {filename}; searched {searched}")


def make_pivots(prices, products):
    group_prices = prices[prices["product"].isin(products)]
    return {
        col: group_prices.pivot(index=["day", "timestamp"], columns="product", values=col).sort_index()
        for col in ["mid_price", "bid_price_1", "ask_price_1"]
    }


def fit_ols(y, x):
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef, x):
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def candidate_id(frame):
    return (
        frame["group"].astype(str)
        + "|"
        + frame["target"].astype(str)
        + "|thr="
        + frame["threshold"].map(lambda x: f"{x:g}")
        + "|h="
        + frame["horizon"].astype(str)
        + "|"
        + frame["exit_rule"].astype(str)
    )


def summarize_isolated(day_rows):
    rows = []
    for key, frame in day_rows.groupby(KEYS):
        trades = int(frame["trades"].sum())
        wins = int(frame["wins"].sum())
        total_pnl = float(frame["pnl"].sum())
        rows.append(
            {
                "group": key[0],
                "target": key[1],
                "threshold": key[2],
                "horizon": key[3],
                "exit_rule": key[4],
                "train_days": int(frame["test_day"].nunique()),
                "train_total_pnl": total_pnl,
                "train_min_day_pnl": float(frame["pnl"].min()),
                "train_positive_days": int((frame["pnl"] > 0).sum()),
                "train_total_trades": trades,
                "train_win_pct": wins / trades if trades else 0.0,
                "train_avg_pnl_per_trade": total_pnl / trades if trades else 0.0,
            }
        )
    out = pd.DataFrame(rows)
    out["candidate_id"] = candidate_id(out)
    return out.sort_values(
        ["train_positive_days", "train_min_day_pnl", "train_total_pnl", "train_avg_pnl_per_trade"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def robust_train_pool(train_summary):
    return train_summary[
        (train_summary["train_days"] >= 2)
        & (train_summary["train_positive_days"] == train_summary["train_days"])
        & (train_summary["train_min_day_pnl"] > 0)
        & (train_summary["train_total_trades"] >= 5)
    ].copy()


def robust_static_pool(summary):
    pool = summary[
        (summary["days"] == 3)
        & (summary["positive_days"] == 3)
        & (summary["min_day_pnl"] > 0)
        & (summary["total_trades"] >= 10)
    ].copy()
    pool = pool.rename(
        columns={
            "total_pnl": "all_days_total_pnl",
            "min_day_pnl": "all_days_min_day_pnl",
            "positive_days": "all_days_positive_days",
            "total_trades": "all_days_total_trades",
        }
    )
    pool["candidate_id"] = candidate_id(pool)
    return pool.sort_values(
        ["all_days_min_day_pnl", "all_days_total_pnl", "avg_pnl_per_trade"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def select_named_sets(train_pool, static_pool):
    sets = {}
    ranked = train_pool.sort_values(
        ["train_min_day_pnl", "train_total_pnl", "train_avg_pnl_per_trade"],
        ascending=[False, False, False],
    )
    sets["lodo_top_per_group"] = (
        ranked.sort_values(["group", "train_min_day_pnl", "train_total_pnl"], ascending=[True, False, False])
        .groupby("group", as_index=False)
        .head(1)
    )
    sets["lodo_top3_overall"] = ranked.head(3)
    sets["lodo_fast_horizon_le_100"] = ranked[ranked["horizon"] <= 100]
    sets["lodo_long_horizon_500"] = ranked[ranked["horizon"] == 500]

    static_ranked = static_pool.sort_values(
        ["all_days_min_day_pnl", "all_days_total_pnl", "avg_pnl_per_trade"],
        ascending=[False, False, False],
    )
    sets["static12_top_per_group"] = (
        static_ranked.sort_values(
            ["group", "all_days_min_day_pnl", "all_days_total_pnl"], ascending=[True, False, False]
        )
        .groupby("group", as_index=False)
        .head(1)
    )
    sets["static12_top3_overall"] = static_ranked.head(3)
    sets["static12_fast_horizon_le_100"] = static_ranked[static_ranked["horizon"] <= 100]
    sets["static12_long_horizon_500"] = static_ranked[static_ranked["horizon"] == 500]
    return {name: frame.copy().reset_index(drop=True) for name, frame in sets.items()}


class ResidualCache:
    def __init__(self, prices):
        self.prices = prices
        self.pivots = {}
        self.cache = {}

    def get(self, group, target, test_day):
        key = (group, target, int(test_day))
        if key in self.cache:
            return self.cache[key]

        products = GROUPS[group]
        if group not in self.pivots:
            self.pivots[group] = make_pivots(self.prices, products)
        mids = self.pivots[group]["mid_price"]
        bids = self.pivots[group]["bid_price_1"]
        asks = self.pivots[group]["ask_price_1"]

        components = [product for product in products if product != target]
        base = mids[[target] + components].dropna()
        train = base[base.index.get_level_values("day") != test_day]
        test = base[base.index.get_level_values("day") == test_day]
        if len(train) < 100 or len(test) < 100:
            raise ValueError(f"Insufficient rows for {group} {target} day {test_day}")

        coef = fit_ols(train[target].to_numpy(dtype=float), train[components].to_numpy(dtype=float))
        train_resid = train[target].to_numpy(dtype=float) - predict_ols(
            coef, train[components].to_numpy(dtype=float)
        )
        sigma = float(np.std(train_resid))
        resid = test[target].to_numpy(dtype=float) - predict_ols(
            coef, test[components].to_numpy(dtype=float)
        )
        idx = test.index
        out = {
            "timestamps": idx.get_level_values("timestamp").to_numpy(dtype=int),
            "resid": resid,
            "z": resid / sigma if sigma > 1e-12 else np.zeros(len(resid)),
            "bid": bids.loc[idx, target].to_numpy(dtype=float),
            "ask": asks.loc[idx, target].to_numpy(dtype=float),
            "sigma_train": sigma,
        }
        self.cache[key] = out
        return out


def signal_priority(row, abs_z):
    return (
        int(row.get("train_positive_days", 0)),
        float(row.get("train_min_day_pnl", 0.0)),
        float(row.get("train_total_pnl", 0.0)),
        float(row.get("train_avg_pnl_per_trade", 0.0)),
        float(abs_z),
        -float(row["horizon"]),
        str(row["candidate_id"]),
    )


def find_exit_i(data, entry_i, horizon, exit_rule):
    exit_i = min(entry_i + int(horizon), len(data["resid"]) - 1)
    if exit_rule == "zero_cross":
        start_sign = np.sign(data["resid"][entry_i])
        for j in range(entry_i + 1, exit_i + 1):
            if data["resid"][j] == 0 or np.sign(data["resid"][j]) != start_sign:
                return j
    return exit_i


def simulate_set(resid_cache, specs, test_day, set_name):
    specs = specs.copy().reset_index(drop=True)
    if specs.empty:
        return empty_day_result(set_name, test_day), []

    specs["candidate_id"] = candidate_id(specs)
    target_data = {
        (row.group, row.target): resid_cache.get(row.group, row.target, test_day)
        for row in specs[["group", "target"]].drop_duplicates().itertuples(index=False)
    }
    first = next(iter(target_data.values()))
    n = len(first["timestamps"])

    positions = {}
    trades = []
    signals_seen = 0
    blocked_active = 0
    rejected_conflict = 0
    accepted = 0
    max_concurrent = 0

    for i in range(n):
        for target, position in list(positions.items()):
            if position["exit_i"] <= i:
                data = position["data"]
                exit_price = data["bid"][i] if position["direction"] > 0 else data["ask"][i]
                edge = (exit_price - position["entry_price"]) * position["direction"]
                pnl = edge * QTY
                trades.append(
                    {
                        "candidate_set": set_name,
                        "test_day": int(test_day),
                        "group": position["group"],
                        "target": target,
                        "candidate_id": position["candidate_id"],
                        "threshold": position["threshold"],
                        "horizon": position["horizon"],
                        "exit_rule": position["exit_rule"],
                        "direction": position["direction"],
                        "entry_timestamp": int(position["entry_timestamp"]),
                        "exit_timestamp": int(first["timestamps"][i]),
                        "entry_z": position["entry_z"],
                        "entry_abs_z": abs(position["entry_z"]),
                        "entry_price": position["entry_price"],
                        "exit_price": exit_price,
                        "hold": int(i - position["entry_i"]),
                        "pnl": pnl,
                    }
                )
                del positions[target]

        if i >= n - 1:
            continue

        signals = []
        for row in specs.itertuples(index=False):
            data = target_data[(row.group, row.target)]
            z = float(data["z"][i])
            if abs(z) < float(row.threshold):
                continue
            signals_seen += 1
            signals.append((signal_priority(row._asdict(), abs(z)), row, data, z))

        for _, row, data, z in sorted(signals, key=lambda item: item[0], reverse=True):
            if row.target in positions:
                blocked_active += 1
                continue
            direction = -1 if data["resid"][i] > 0 else 1
            exit_i = find_exit_i(data, i, row.horizon, row.exit_rule)
            if exit_i <= i:
                rejected_conflict += 1
                continue
            entry_price = data["ask"][i] if direction > 0 else data["bid"][i]
            positions[row.target] = {
                "group": row.group,
                "candidate_id": row.candidate_id,
                "threshold": row.threshold,
                "horizon": int(row.horizon),
                "exit_rule": row.exit_rule,
                "direction": direction,
                "entry_i": i,
                "exit_i": exit_i,
                "entry_timestamp": first["timestamps"][i],
                "entry_z": z,
                "entry_price": entry_price,
                "data": data,
            }
            accepted += 1
        max_concurrent = max(max_concurrent, len(positions))

    day_pnl = float(sum(trade["pnl"] for trade in trades))
    wins = int(sum(trade["pnl"] > 0 for trade in trades))
    losses = int(sum(trade["pnl"] < 0 for trade in trades))
    result = {
        "candidate_set": set_name,
        "test_day": int(test_day),
        "n_candidates": int(len(specs)),
        "n_products": int(specs["target"].nunique()),
        "pnl": day_pnl,
        "trades": int(len(trades)),
        "wins": wins,
        "losses": losses,
        "win_pct": wins / len(trades) if trades else 0.0,
        "avg_pnl_per_trade": day_pnl / len(trades) if trades else 0.0,
        "avg_hold": float(np.mean([trade["hold"] for trade in trades])) if trades else 0.0,
        "signals_seen": int(signals_seen),
        "signals_accepted": int(accepted),
        "signals_blocked_active": int(blocked_active),
        "signals_rejected_conflict": int(rejected_conflict),
        "conflict_rate": (blocked_active + rejected_conflict) / signals_seen if signals_seen else 0.0,
        "max_concurrent_positions": int(max_concurrent),
    }
    return result, trades


def empty_day_result(set_name, test_day):
    return {
        "candidate_set": set_name,
        "test_day": int(test_day),
        "n_candidates": 0,
        "n_products": 0,
        "pnl": 0.0,
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_pct": 0.0,
        "avg_pnl_per_trade": 0.0,
        "avg_hold": 0.0,
        "signals_seen": 0,
        "signals_accepted": 0,
        "signals_blocked_active": 0,
        "signals_rejected_conflict": 0,
        "conflict_rate": 0.0,
        "max_concurrent_positions": 0,
    }


def summarize_portfolios(day_rows):
    rows = []
    for set_name, frame in day_rows.groupby("candidate_set"):
        trades = int(frame["trades"].sum())
        wins = int(frame["wins"].sum())
        total_pnl = float(frame["pnl"].sum())
        rows.append(
            {
                "candidate_set": set_name,
                "days": int(frame["test_day"].nunique()),
                "total_pnl": total_pnl,
                "min_day_pnl": float(frame["pnl"].min()),
                "max_day_pnl": float(frame["pnl"].max()),
                "mean_day_pnl": float(frame["pnl"].mean()),
                "positive_days": int((frame["pnl"] > 0).sum()),
                "total_trades": trades,
                "win_pct": wins / trades if trades else 0.0,
                "avg_pnl_per_trade": total_pnl / trades if trades else 0.0,
                "avg_candidates": float(frame["n_candidates"].mean()),
                "avg_products": float(frame["n_products"].mean()),
                "signals_seen": int(frame["signals_seen"].sum()),
                "signals_accepted": int(frame["signals_accepted"].sum()),
                "signals_blocked_active": int(frame["signals_blocked_active"].sum()),
                "signals_rejected_conflict": int(frame["signals_rejected_conflict"].sum()),
                "conflict_rate": (
                    (frame["signals_blocked_active"].sum() + frame["signals_rejected_conflict"].sum())
                    / frame["signals_seen"].sum()
                    if frame["signals_seen"].sum()
                    else 0.0
                ),
                "max_concurrent_positions": int(frame["max_concurrent_positions"].max()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["positive_days", "min_day_pnl", "total_pnl"], ascending=[False, False, False]
    )


def md_table(frame, columns, n=20):
    if frame.empty:
        return "No rows."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_report(summary, day_rows, candidates):
    lodo_summary = summary[summary["candidate_set"].str.startswith("lodo_")]
    static_summary = summary[summary["candidate_set"].str.startswith("static12_")]
    best = lodo_summary.iloc[0] if not lodo_summary.empty else summary.iloc[0]
    best_static = static_summary.iloc[0] if not static_summary.empty else None
    best_candidates = candidates[candidates["candidate_set"] == best["candidate_set"]].copy()
    lines = [
        "# Round 5 Residual Portfolio Conflict Simulation",
        "",
        "Portfolio-level simulation for the residual-shock candidates from `12_residual_trade_sim`. Entries cross the target leg at top of book with quantity 10. Each residual fit is leave-one-day-out: coefficients and residual sigma are trained on the two non-test days, then applied to the held-out day.",
        "",
        "At each timestamp, all selected candidate signals are scored by training-day isolated robustness: positive training days, minimum training-day PnL, total training PnL, average PnL per trade, then current absolute z-score. The resolver accepts signals in that order while enforcing at most one active position per product; lower-priority signals for active products are skipped.",
        "",
        "Candidate-set names beginning with `lodo_` are selected separately for each test day from the two non-test days only. `static12_` sets are diagnostic baselines selected from the full prior `12_*` robust table, while still using leave-one-day-out coefficients and day-specific training priority during execution.",
        "",
        "## Portfolio Summary",
        "",
        md_table(
            summary,
            [
                "candidate_set",
                "total_pnl",
                "min_day_pnl",
                "positive_days",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
                "avg_candidates",
                "signals_accepted",
                "signals_blocked_active",
                "conflict_rate",
            ],
        ),
        "",
        "## Day By Day",
        "",
        md_table(
            day_rows.sort_values(["candidate_set", "test_day"]),
            [
                "candidate_set",
                "test_day",
                "n_candidates",
                "n_products",
                "pnl",
                "trades",
                "win_pct",
                "signals_seen",
                "signals_accepted",
                "signals_blocked_active",
                "max_concurrent_positions",
            ],
            n=80,
        ),
        "",
        "## Best Robust Candidate Set",
        "",
        f"Best strict no-test-selection set by positive held-out days, then minimum day PnL, then total PnL: `{best['candidate_set']}` with total PnL {best['total_pnl']:.0f}, minimum day PnL {best['min_day_pnl']:.0f}, and {int(best['positive_days'])}/{int(best['days'])} positive days.",
        "",
        (
            f"Best diagnostic all-day `static12_` baseline: `{best_static['candidate_set']}` with total PnL {best_static['total_pnl']:.0f}, minimum day PnL {best_static['min_day_pnl']:.0f}, and {int(best_static['positive_days'])}/{int(best_static['days'])} positive days. Treat this as an upper-bound comparison because membership comes from the full prior `12_*` robust table."
            if best_static is not None
            else "No diagnostic `static12_` baseline was available."
        ),
        "",
        "### Best Set Membership",
        "",
        md_table(
            best_candidates.sort_values(["test_day", "train_min_day_pnl", "train_total_pnl"], ascending=[True, False, False]),
            [
                "candidate_set",
                "test_day",
                "group",
                "target",
                "threshold",
                "horizon",
                "exit_rule",
                "train_min_day_pnl",
                "train_total_pnl",
                "train_total_trades",
            ],
            n=80,
        ),
    ]
    path = OUT_DIR / "14_residual_portfolio_conflicts.md"
    path.write_text("\n".join(lines))
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    prior_day_rows = read_prior_csv("12_residual_trade_sim_by_day.csv")
    prior_summary = read_prior_csv("12_residual_trade_sim_summary.csv")
    static_pool = robust_static_pool(prior_summary)
    resid_cache = ResidualCache(prices)

    days = sorted(prior_day_rows["test_day"].unique())
    portfolio_rows = []
    trade_rows = []
    candidate_rows = []

    for test_day in days:
        train_summary = summarize_isolated(prior_day_rows[prior_day_rows["test_day"] != test_day])
        train_pool = robust_train_pool(train_summary)
        sets = select_named_sets(train_pool, static_pool)
        priority = train_summary[KEYS + ["candidate_id", "train_positive_days", "train_min_day_pnl", "train_total_pnl", "train_total_trades", "train_win_pct", "train_avg_pnl_per_trade"]]

        for set_name, specs in sets.items():
            specs = specs.merge(priority, on=KEYS + ["candidate_id"], how="left", suffixes=("", "_priority"))
            for col in ["train_positive_days", "train_min_day_pnl", "train_total_pnl", "train_total_trades", "train_win_pct", "train_avg_pnl_per_trade"]:
                priority_col = f"{col}_priority"
                if priority_col in specs.columns:
                    specs[col] = specs[priority_col].combine_first(specs.get(col))
                    specs = specs.drop(columns=[priority_col])
            specs["test_day"] = int(test_day)
            specs["candidate_set"] = set_name
            candidate_rows.extend(specs.to_dict("records"))

            print(f"Simulating {set_name} day {test_day}: {len(specs)} candidates")
            day_result, trades = simulate_set(resid_cache, specs, test_day, set_name)
            portfolio_rows.append(day_result)
            trade_rows.extend(trades)

    by_day = pd.DataFrame(portfolio_rows).sort_values(["candidate_set", "test_day"])
    summary = summarize_portfolios(by_day)
    candidates = pd.DataFrame(candidate_rows)
    trades = pd.DataFrame(trade_rows)

    summary_path = OUT_DIR / "14_residual_portfolio_conflicts_summary.csv"
    by_day_path = OUT_DIR / "14_residual_portfolio_conflicts_by_day.csv"
    candidates_path = OUT_DIR / "14_residual_portfolio_conflicts_candidates.csv"
    trades_path = OUT_DIR / "14_residual_portfolio_conflicts_trades.csv"

    summary.to_csv(summary_path, index=False)
    by_day.to_csv(by_day_path, index=False)
    candidates.to_csv(candidates_path, index=False)
    trades.to_csv(trades_path, index=False)
    report_path = write_report(summary, by_day, candidates)

    print(f"Wrote {summary_path}")
    print(f"Wrote {by_day_path}")
    print(f"Wrote {candidates_path}")
    print(f"Wrote {trades_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
