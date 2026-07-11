import math
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
RANKING_PATH = OUT_DIR / "01_group_tradeability_ranking.csv"


GROUPS = {
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
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
}


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)


def acf1(resid: np.ndarray) -> float:
    if len(resid) < 3:
        return float("nan")
    a = resid[:-1]
    b = resid[1:]
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def half_life(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0 or phi >= 1:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def adf_t_stat(resid: np.ndarray) -> float:
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
        inv = np.linalg.inv(x.T @ x)
        se = math.sqrt(max(0.0, sigma2 * inv[1, 1]))
        return float(coef[1] / se) if se > 1e-12 else float("nan")
    except np.linalg.LinAlgError:
        return float("nan")


def fit_basket(pivot: pd.DataFrame, target: str, components: list[str]) -> dict:
    frame = pivot[[target] + components].dropna()
    if len(frame) < 50:
        return {}
    y = frame[target].to_numpy(dtype=float)
    x = frame[components].to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    coef = np.linalg.lstsq(x, y, rcond=None)[0]
    pred = x @ coef
    resid = y - pred
    phi = acf1(resid)
    return {
        "alpha": float(coef[0]),
        **{f"beta_{component}": float(beta) for component, beta in zip(components, coef[1:])},
        "r2": float(1.0 - np.var(resid) / np.var(y)) if np.var(y) > 1e-12 else float("nan"),
        "resid_sd": float(np.std(resid)),
        "resid_acf1": phi,
        "half_life": half_life(phi),
        "adf_t": adf_t_stat(resid),
        "n": int(len(resid)),
    }


def fit_index(pivot: pd.DataFrame, target: str, components: list[str]) -> dict:
    frame = pivot[[target] + components].dropna()
    if len(frame) < 50:
        return {}
    y = frame[target].to_numpy(dtype=float)
    idx = frame[components].mean(axis=1).to_numpy(dtype=float)
    var = float(np.var(idx))
    beta = 0.0 if var <= 1e-12 else float(np.mean((idx - idx.mean()) * (y - y.mean())) / var)
    alpha = float(y.mean() - beta * idx.mean())
    resid = y - alpha - beta * idx
    phi = acf1(resid)
    corr = float(np.corrcoef(y, idx)[0, 1]) if np.std(y) > 0 and np.std(idx) > 0 else float("nan")
    return {
        "index_alpha": alpha,
        "index_beta": beta,
        "index_corr": corr,
        "index_resid_sd": float(np.std(resid)),
        "index_adf_t": adf_t_stat(resid),
        "index_half_life": half_life(phi),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    selected = pd.read_csv(RANKING_PATH).head(4)["group"].tolist()
    prices = read_prices()
    rows = []
    for group in selected:
        products = GROUPS[group]
        g = prices[prices["product"].isin(products)]
        full_pivot = g.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        for target in products:
            components = [p for p in products if p != target]
            full = fit_basket(full_pivot, target, components)
            idx = fit_index(full_pivot, target, components)
            if not full:
                continue
            row = {"group": group, "target": target, "components": ",".join(components), **full, **idx}
            adf_days = 0
            max_hl = 0.0
            min_r2 = 1.0
            for day, day_g in g.groupby("day"):
                day_pivot = day_g.pivot(index="timestamp", columns="product", values="mid_price")
                dm = fit_basket(day_pivot, target, components)
                for key, value in dm.items():
                    row[f"d{int(day)}_{key}"] = value
                adf_days += int(dm.get("adf_t", 0.0) < -2.8)
                max_hl = max(max_hl, dm.get("half_life", float("inf")))
                min_r2 = min(min_r2, dm.get("r2", float("nan")))
            row["adf_days_lt_-2_8"] = adf_days
            row["half_life_max_day"] = max_hl
            row["min_day_r2"] = min_r2
            row["candidate"] = (
                row["adf_t"] < -2.8
                and adf_days >= 2
                and row["half_life"] <= 300
                and row["half_life_max_day"] <= 300
                and row["min_day_r2"] >= 0.25
            )
            rows.append(row)
    out = pd.DataFrame(rows).sort_values(
        ["candidate", "adf_days_lt_-2_8", "adf_t", "half_life_max_day", "r2"],
        ascending=[False, False, True, True, False],
    )
    out.to_csv(OUT_DIR / "03_basket_synthetic.csv", index=False)
    lines = [
        "# Round 5 Phase 2.2 - Basket Synthetic",
        "",
        "For each selected group, each product is regressed on the other four products.",
        "Candidate gate: combined residual ADF t < -2.8, at least 2 daily ADF passes, max daily half-life <= 300 ticks, and min daily R2 >= 0.25.",
        "",
        "## Candidate Baskets",
        "",
    ]
    cand = out[out["candidate"]]
    if cand.empty:
        lines.append("No 1-against-4 basket passed the full candidate gate.")
    else:
        lines.append(
            cand[["group", "target", "r2", "resid_sd", "adf_t", "adf_days_lt_-2_8", "half_life", "half_life_max_day", "min_day_r2", "index_corr"]]
            .round(6)
            .to_markdown(index=False)
        )
    lines.extend(["", "## Top Raw Baskets", ""])
    lines.append(
        out.head(25)[["group", "target", "candidate", "r2", "resid_sd", "adf_t", "adf_days_lt_-2_8", "half_life", "half_life_max_day", "min_day_r2", "index_corr", "index_adf_t", "index_half_life"]]
        .round(6)
        .to_markdown(index=False)
    )
    (OUT_DIR / "03_basket_synthetic.md").write_text("\n".join(lines))
    print(
        out.head(25)[["group", "target", "candidate", "r2", "resid_sd", "adf_t", "adf_days_lt_-2_8", "half_life", "half_life_max_day", "min_day_r2", "index_corr", "index_adf_t", "index_half_life"]]
        .round(6)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
