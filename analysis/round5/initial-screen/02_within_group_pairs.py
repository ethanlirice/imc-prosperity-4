import math
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
RANKING_PATH = OUT_DIR / "01_group_tradeability_ranking.csv"


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


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)


def ols_y_on_x(y: np.ndarray, x: np.ndarray) -> tuple[float, float, np.ndarray]:
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    var_x = float(np.var(x))
    beta = 0.0 if var_x <= 1e-12 else float(np.mean((x - x_mean) * (y - y_mean)) / var_x)
    alpha = y_mean - beta * x_mean
    resid = y - alpha - beta * x
    return alpha, beta, resid


def adf_t_stat(resid: np.ndarray) -> float:
    # Lightweight ADF(0): delta e_t = a + lambda * e_{t-1} + noise.
    if len(resid) < 20:
        return float("nan")
    lag = resid[:-1]
    de = np.diff(resid)
    x = np.column_stack([np.ones_like(lag), lag])
    try:
        coef = np.linalg.lstsq(x, de, rcond=None)[0]
        err = de - x @ coef
        dof = max(1, len(de) - x.shape[1])
        sigma2 = float(err @ err / dof)
        xtx_inv = np.linalg.inv(x.T @ x)
        se = math.sqrt(max(0.0, sigma2 * xtx_inv[1, 1]))
        return float(coef[1] / se) if se > 1e-12 else float("nan")
    except np.linalg.LinAlgError:
        return float("nan")


def acf1(resid: np.ndarray) -> float:
    if len(resid) < 3:
        return float("nan")
    a = resid[:-1]
    b = resid[1:]
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def half_life_from_acf(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0 or phi >= 1:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def pair_metrics(pivot: pd.DataFrame, y_name: str, x_name: str) -> dict[str, float]:
    frame = pivot[[y_name, x_name]].dropna()
    y = frame[y_name].to_numpy(dtype=float)
    x = frame[x_name].to_numpy(dtype=float)
    if len(frame) < 20:
        return {}
    alpha, beta, resid = ols_y_on_x(y, x)
    corr_mid = float(np.corrcoef(y, x)[0, 1]) if np.std(y) > 0 and np.std(x) > 0 else float("nan")
    ry = np.diff(y)
    rx = np.diff(x)
    corr_ret = (
        float(np.corrcoef(ry, rx)[0, 1])
        if len(ry) > 2 and np.std(ry) > 0 and np.std(rx) > 0
        else float("nan")
    )
    phi = acf1(resid)
    return {
        "alpha": alpha,
        "beta": beta,
        "corr_mid": corr_mid,
        "corr_ret": corr_ret,
        "resid_mean": float(np.mean(resid)),
        "resid_sd": float(np.std(resid)),
        "resid_acf1": phi,
        "half_life": half_life_from_acf(phi),
        "adf_t": adf_t_stat(resid),
        "n": int(len(resid)),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ranking = pd.read_csv(RANKING_PATH)
    selected_groups = ranking.head(4)["group"].tolist()
    prices = read_prices()
    rows = []
    for group in selected_groups:
        products = GROUPS[group]
        g = prices[prices["product"].isin(products)]
        full_pivot = g.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        for i, y_name in enumerate(products):
            for x_name in products[i + 1 :]:
                full = pair_metrics(full_pivot, y_name, x_name)
                if not full:
                    continue
                row = {"group": group, "y": y_name, "x": x_name, **{f"all_{k}": v for k, v in full.items()}}
                day_adfs = []
                day_hl = []
                day_beta = []
                day_corr = []
                for day, day_g in g.groupby("day"):
                    day_pivot = day_g.pivot(index="timestamp", columns="product", values="mid_price")
                    dm = pair_metrics(day_pivot, y_name, x_name)
                    for key, value in dm.items():
                        row[f"d{int(day)}_{key}"] = value
                    day_adfs.append(dm.get("adf_t", float("nan")))
                    day_hl.append(dm.get("half_life", float("inf")))
                    day_beta.append(dm.get("beta", float("nan")))
                    day_corr.append(dm.get("corr_mid", float("nan")))
                beta_arr = np.array([v for v in day_beta if np.isfinite(v)])
                row["adf_days_lt_-2_8"] = int(sum(np.isfinite(v) and v < -2.8 for v in day_adfs))
                row["half_life_max_day"] = float(np.nanmax(day_hl))
                row["half_life_mean_day"] = float(np.nanmean(day_hl))
                row["beta_cv_day"] = (
                    float(np.std(beta_arr) / abs(np.mean(beta_arr)))
                    if len(beta_arr) >= 2 and abs(np.mean(beta_arr)) > 1e-12
                    else float("nan")
                )
                row["min_day_corr_mid"] = float(np.nanmin(day_corr))
                row["candidate"] = (
                    row["all_adf_t"] < -2.8
                    and row["adf_days_lt_-2_8"] >= 2
                    and row["half_life_max_day"] <= 300
                    and row["all_resid_sd"] > 0
                )
                rows.append(row)
    out = pd.DataFrame(rows).sort_values(
        ["candidate", "adf_days_lt_-2_8", "all_adf_t", "half_life_mean_day"],
        ascending=[False, False, True, True],
    )
    out.to_csv(OUT_DIR / "02_within_group_pairs.csv", index=False)
    lines = [
        "# Round 5 Phase 2.1 - Within-Group Pairs",
        "",
        "Selected groups come from `01_group_tradeability_ranking.csv` top 4.",
        "ADF is a lightweight ADF(0) t-statistic on OLS residuals; threshold used here is t < -2.8 on combined data and at least 2 of 3 days.",
        "Half-life is estimated from residual lag-1 ACF; candidates require max daily half-life <= 300 ticks.",
        "",
        "## Candidate Pairs",
        "",
    ]
    cand = out[out["candidate"]]
    if cand.empty:
        lines.append("No pair passed the full candidate gate.")
    else:
        lines.append(
            cand[
                [
                    "group",
                    "y",
                    "x",
                    "all_beta",
                    "all_corr_mid",
                    "all_corr_ret",
                    "all_resid_sd",
                    "all_adf_t",
                    "adf_days_lt_-2_8",
                    "half_life_mean_day",
                    "half_life_max_day",
                    "beta_cv_day",
                ]
            ]
            .round(6)
            .to_markdown(index=False)
        )
    lines.extend(["", "## Top Raw Pair Metrics", ""])
    lines.append(
        out.head(30)[
            [
                "group",
                "y",
                "x",
                "candidate",
                "all_beta",
                "all_corr_mid",
                "all_corr_ret",
                "all_resid_sd",
                "all_adf_t",
                "adf_days_lt_-2_8",
                "half_life_mean_day",
                "half_life_max_day",
                "beta_cv_day",
            ]
        ]
        .round(6)
        .to_markdown(index=False)
    )
    (OUT_DIR / "02_within_group_pairs.md").write_text("\n".join(lines))
    print(
        out.head(30)[
            [
                "group",
                "y",
                "x",
                "candidate",
                "all_beta",
                "all_corr_mid",
                "all_corr_ret",
                "all_resid_sd",
                "all_adf_t",
                "adf_days_lt_-2_8",
                "half_life_mean_day",
                "half_life_max_day",
                "beta_cv_day",
            ]
        ]
        .round(6)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
