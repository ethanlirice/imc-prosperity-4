from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
LAGS = [1, 2, 5, 10, 20, 50, 100, 200]
MIN_ABS_CORR = 0.10


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)


def corr_matrix(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0 = x - x.mean(axis=0, keepdims=True)
    y0 = y - y.mean(axis=0, keepdims=True)
    denom = np.sqrt((x0 * x0).sum(axis=0))[:, None] * np.sqrt((y0 * y0).sum(axis=0))[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (x0.T @ y0) / denom
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def beta_matrix(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0 = x - x.mean(axis=0, keepdims=True)
    y0 = y - y.mean(axis=0, keepdims=True)
    var = (x0 * x0).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (x0.T @ y0) / var[:, None]
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def scan_day(day: int, day_df: pd.DataFrame) -> pd.DataFrame:
    pivot = day_df.pivot(index="timestamp", columns="product", values="mid_price").sort_index()
    products = list(pivot.columns)
    returns = pivot.diff().dropna().to_numpy(dtype=float)
    lag0 = corr_matrix(returns, returns)
    rows = []
    for lag in LAGS:
        x = returns[:-lag]
        y = returns[lag:]
        c = corr_matrix(x, y)
        b = beta_matrix(x, y)
        for i, leader in enumerate(products):
            for j, follower in enumerate(products):
                if i == j:
                    continue
                corr = float(c[i, j])
                lag0_corr = float(lag0[i, j])
                rows.append(
                    {
                        "day": day,
                        "lag": lag,
                        "leader": leader,
                        "follower": follower,
                        "corr": corr,
                        "abs_corr": abs(corr),
                        "lag0_corr": lag0_corr,
                        "beats_lag0": abs(corr) > abs(lag0_corr),
                        "beta": float(b[i, j]),
                        "r2": corr * corr,
                    }
                )
    return pd.DataFrame(rows)


def event_markout(prices: pd.DataFrame, leader: str, follower: str, lag: int, beta: float) -> dict:
    vals = []
    counts = []
    for _, day_df in prices.groupby("day"):
        pivot = day_df.pivot(index="timestamp", columns="product", values="mid_price").sort_index()
        if leader not in pivot or follower not in pivot:
            continue
        leader_ret = pivot[leader].diff().to_numpy(dtype=float)
        follower_mid = pivot[follower].to_numpy(dtype=float)
        sigma = np.nanstd(leader_ret)
        if not np.isfinite(sigma) or sigma <= 1e-12:
            continue
        for t in range(1, len(leader_ret) - lag):
            move = leader_ret[t]
            if not np.isfinite(move) or abs(move) <= 1.5 * sigma:
                continue
            direction = np.sign(beta * move)
            vals.append(float(direction * (follower_mid[t + lag] - follower_mid[t])))
        counts.append(len(vals))
    arr = np.array(vals, dtype=float)
    if len(arr) == 0:
        return {"event_n": 0, "event_mean_fwd": 0.0, "event_good_pct": 0.0}
    return {
        "event_n": int(len(arr)),
        "event_mean_fwd": float(arr.mean()),
        "event_good_pct": float((arr > 0).mean()),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    day_rows = []
    for day, day_df in prices.groupby("day"):
        day_rows.append(scan_day(int(day), day_df))
    tensor = pd.concat(day_rows, ignore_index=True)
    tensor.to_csv(OUT_DIR / "04_lead_lag_tensor.csv", index=False)

    grouped = tensor.groupby(["lag", "leader", "follower"])
    rows = []
    for key, g in grouped:
        lag, leader, follower = key
        sig = g[(g["abs_corr"] >= MIN_ABS_CORR) & (g["beats_lag0"])]
        if len(sig) < 2:
            continue
        signs = np.sign(sig["corr"].to_numpy())
        same_sign = np.all(signs == signs[0])
        if not same_sign:
            continue
        beta = float(sig["beta"].mean())
        row = {
            "lag": lag,
            "leader": leader,
            "follower": follower,
            "days_passing": int(len(sig)),
            "mean_corr": float(sig["corr"].mean()),
            "min_abs_corr": float(sig["abs_corr"].min()),
            "mean_beta": beta,
            "mean_r2": float(sig["r2"].mean()),
            "max_abs_lag0_corr": float(g["lag0_corr"].abs().max()),
        }
        row.update(event_markout(prices, leader, follower, int(lag), beta))
        rows.append(row)
    survivors = pd.DataFrame(rows)
    if not survivors.empty:
        survivors = survivors.sort_values(
            ["event_mean_fwd", "mean_r2", "min_abs_corr"], ascending=False
        )
    survivors.to_csv(OUT_DIR / "04_lead_lag_survivors.csv", index=False)

    lines = [
        "# Round 5 Phase 3 - Lead-Lag Scan",
        "",
        "Scans all ordered product pairs at lags 1, 2, 5, 10, 20, 50, 100, 200.",
        "Survivor gate: |corr| >= 0.10, beats lag-0 correlation, same sign, and passes on at least 2 of 3 sample days.",
        "",
    ]
    if survivors.empty:
        lines.append("No lead-lag pair passed the survivor gate.")
    else:
        lines.append(
            survivors.head(50)[
                [
                    "lag",
                    "leader",
                    "follower",
                    "days_passing",
                    "mean_corr",
                    "min_abs_corr",
                    "mean_beta",
                    "mean_r2",
                    "event_n",
                    "event_mean_fwd",
                    "event_good_pct",
                ]
            ]
            .round(6)
            .to_markdown(index=False)
        )
    (OUT_DIR / "04_lead_lag_scan.md").write_text("\n".join(lines))
    if survivors.empty:
        print("No lead-lag pair passed the survivor gate.")
    else:
        print(
            survivors.head(50)[
                [
                    "lag",
                    "leader",
                    "follower",
                    "days_passing",
                    "mean_corr",
                    "min_abs_corr",
                    "mean_beta",
                    "mean_r2",
                    "event_n",
                    "event_mean_fwd",
                    "event_good_pct",
                ]
            ]
            .round(6)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
