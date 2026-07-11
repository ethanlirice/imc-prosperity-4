"""
Phase 1: walk-forward pair scan across all 10 Round 5 groups.

For each group, compute every C(5,2) = 10 pairwise spread (10 groups x 10 = 100
pairs total). Train spread mean/std on day N, test on day N+1. A pair survives
when out-of-sample mean Sharpe across the two folds > 1.0.

Output: analysis/round5/three-layer-prototype/01_pair_walkforward.{csv,md}
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5/three-layer-prototype")

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

# Walk-forward strategy parameters. Match competitor description: simple
# z-score on the spread, mean reversion entry at |z|=1.5, exit at |z|<=0.5.
ENTRY_Z = 1.5
EXIT_Z = 0.5
ROLL_WINDOW = 500  # ticks; matches Layer 3 spec in TRADING brief


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(p, sep=";") for p in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)


def adf_t_stat(resid: np.ndarray) -> float:
    if len(resid) < 20:
        return float("nan")
    lag = resid[:-1]
    de = np.diff(resid)
    x = np.column_stack([np.ones_like(lag), lag])
    try:
        coef, *_ = np.linalg.lstsq(x, de, rcond=None)
        err = de - x @ coef
        dof = max(1, len(de) - x.shape[1])
        sigma2 = float(err @ err / dof)
        xtx_inv = np.linalg.inv(x.T @ x)
        se = math.sqrt(max(0.0, sigma2 * xtx_inv[1, 1]))
        return float(coef[1] / se) if se > 1e-12 else float("nan")
    except np.linalg.LinAlgError:
        return float("nan")


def half_life(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0 or phi >= 1:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def acf1(arr: np.ndarray) -> float:
    if len(arr) < 3:
        return float("nan")
    a = arr[:-1]
    b = arr[1:]
    sa = np.std(a)
    sb = np.std(b)
    if sa <= 1e-12 or sb <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def simulate_spread_mr(
    spread_test: np.ndarray,
    train_mean: float,
    train_sd: float,
    entry_z: float = ENTRY_Z,
    exit_z: float = EXIT_Z,
) -> dict:
    """One-unit spread strategy: long when z<=-entry, short when z>=entry,
    flat when |z|<=exit. PnL accrues from spread change while in position."""
    if train_sd <= 1e-9 or len(spread_test) < 5:
        return {"pnl": 0.0, "sharpe": float("nan"), "trades": 0, "win_pct": float("nan")}
    z = (spread_test - train_mean) / train_sd
    pos = np.zeros(len(spread_test))
    state = 0
    for i, zi in enumerate(z):
        if state == 0:
            if zi <= -entry_z:
                state = 1
            elif zi >= entry_z:
                state = -1
        else:
            if abs(zi) <= exit_z:
                state = 0
        pos[i] = state
    # PnL[t] = pos[t-1] * (spread[t] - spread[t-1])
    diffs = np.diff(spread_test)
    pos_lag = pos[:-1]
    bar = pos_lag * diffs
    pnl = float(bar.sum())
    if len(bar) < 2 or np.std(bar) <= 1e-12:
        sharpe = float("nan")
    else:
        sharpe = float(bar.mean() / bar.std() * math.sqrt(len(bar)))
    # count round-trip trades (entries)
    trades = int(np.sum((pos[1:] != 0) & (pos[:-1] == 0)))
    wins = int(np.sum(bar > 0))
    win_pct = wins / max(1, np.sum(bar != 0))
    return {"pnl": pnl, "sharpe": sharpe, "trades": trades, "win_pct": float(win_pct)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    rows = []
    for group, products in GROUPS.items():
        sub = prices[prices["product"].isin(products)]
        # pivot per (day, timestamp) -> product mid
        wide = sub.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        wide = wide.dropna(how="any").reset_index()
        for i, a in enumerate(products):
            for b in products[i + 1 :]:
                pair_df = wide[["day", "timestamp", a, b]].dropna()
                if len(pair_df) < 1000:
                    continue
                spread_full = (pair_df[a] - pair_df[b]).to_numpy(dtype=float)
                mean_corr = float(np.corrcoef(pair_df[a], pair_df[b])[0, 1])
                # daily aggregates
                day_groups = {int(d): pair_df[pair_df["day"] == d] for d in pair_df["day"].unique()}
                day_ids = sorted(day_groups.keys())
                if len(day_ids) < 2:
                    continue
                folds = []
                for j in range(len(day_ids) - 1):
                    train_d, test_d = day_ids[j], day_ids[j + 1]
                    train = day_groups[train_d]
                    test = day_groups[test_d]
                    spread_train = (train[a] - train[b]).to_numpy(dtype=float)
                    spread_test = (test[a] - test[b]).to_numpy(dtype=float)
                    mu = float(np.mean(spread_train))
                    sd = float(np.std(spread_train))
                    sim = simulate_spread_mr(spread_test, mu, sd)
                    sim.update(
                        {
                            "train_day": train_d,
                            "test_day": test_d,
                            "train_mean": mu,
                            "train_sd": sd,
                        }
                    )
                    folds.append(sim)
                # ADF and half-life on combined
                resid_full = spread_full - np.mean(spread_full)
                phi = acf1(resid_full)
                hl = half_life(phi)
                adf = adf_t_stat(resid_full)
                pnl_tot = float(sum(f["pnl"] for f in folds))
                sharpes = [f["sharpe"] for f in folds if np.isfinite(f["sharpe"])]
                mean_sharpe = float(np.mean(sharpes)) if sharpes else float("nan")
                min_sharpe = float(np.min(sharpes)) if sharpes else float("nan")
                trades_tot = int(sum(f["trades"] for f in folds))
                row = {
                    "group": group,
                    "a": a,
                    "b": b,
                    "n_full": int(len(pair_df)),
                    "corr_mid_full": mean_corr,
                    "spread_mean_full": float(np.mean(spread_full)),
                    "spread_sd_full": float(np.std(spread_full)),
                    "adf_t_full": adf,
                    "half_life_full": hl,
                    "wf_pnl_total": pnl_tot,
                    "wf_sharpe_mean": mean_sharpe,
                    "wf_sharpe_min": min_sharpe,
                    "wf_trades": trades_tot,
                }
                for fold in folds:
                    tag = f"d{fold['train_day']}to{fold['test_day']}"
                    row[f"{tag}_pnl"] = fold["pnl"]
                    row[f"{tag}_sharpe"] = fold["sharpe"]
                    row[f"{tag}_trades"] = fold["trades"]
                    row[f"{tag}_win_pct"] = fold["win_pct"]
                row["pass_walkforward"] = bool(
                    np.isfinite(min_sharpe) and min_sharpe > 1.0 and trades_tot >= 4
                )
                rows.append(row)
    out = pd.DataFrame(rows).sort_values(
        ["pass_walkforward", "wf_sharpe_min", "wf_sharpe_mean"], ascending=[False, False, False]
    )
    out.to_csv(OUT_DIR / "01_pair_walkforward.csv", index=False)

    keep_cols = [
        "group",
        "a",
        "b",
        "corr_mid_full",
        "spread_sd_full",
        "adf_t_full",
        "half_life_full",
        "wf_pnl_total",
        "wf_sharpe_mean",
        "wf_sharpe_min",
        "wf_trades",
        "pass_walkforward",
    ]
    survivors = out[out["pass_walkforward"]]
    md = ["# Phase 1: walk-forward pair scan", "",
          f"Entry |z| >= {ENTRY_Z}, exit |z| <= {EXIT_Z}, train mean/std per day, evaluate on next day.",
          f"Pass gate: min walk-forward Sharpe > 1.0 AND >=4 trades.",
          "",
          f"## Survivors ({len(survivors)})", ""]
    if survivors.empty:
        md.append("No pair passed.")
    else:
        md.append(survivors[keep_cols].round(4).to_markdown(index=False))
    md.extend(["", "## Top 30 by min walk-forward Sharpe", ""])
    md.append(out.head(30)[keep_cols].round(4).to_markdown(index=False))
    (OUT_DIR / "01_pair_walkforward.md").write_text("\n".join(md))
    print(out.head(20)[keep_cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
