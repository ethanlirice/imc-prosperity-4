from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
QTY = 10
DAYS = [2, 3, 4]

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

CENTER_MODES = ["raw", "open100", "rolling500", "expanding"]
THRESHOLDS = [1.5, 2.0, 2.5, 3.0]
HORIZONS = [100, 200, 500]
EXIT_RULES = ["fixed", "zero_cross"]
SLOPE_MODES = ["any", "reverting"]
VOL_MODES = ["any", "low_vol", "high_vol"]

V3_SPECS = [
    {
        "target": "GALAXY_SOUNDS_SOLAR_FLAMES",
        "components": [
            "GALAXY_SOUNDS_DARK_MATTER",
            "GALAXY_SOUNDS_BLACK_HOLES",
            "GALAXY_SOUNDS_PLANETARY_RINGS",
            "GALAXY_SOUNDS_SOLAR_WINDS",
        ],
        "intercept": 14350.29332353689,
        "betas": [-0.06049803953960144, 0.02252832693672156, 0.02250904659478898, -0.30080885256248274],
        "sigma": 423.1705719697622,
        "entry_z": 2.0,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "MICROCHIP_RECTANGLE",
        "components": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE"],
        "intercept": 12595.888646662721,
        "betas": [0.10560729802045757, 0.25219468928333105, -0.2712089572427367, -0.3316449079702204],
        "sigma": 329.6256830600202,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "OXYGEN_SHAKE_MINT",
        "components": [
            "OXYGEN_SHAKE_MORNING_BREATH",
            "OXYGEN_SHAKE_EVENING_BREATH",
            "OXYGEN_SHAKE_CHOCOLATE",
            "OXYGEN_SHAKE_GARLIC",
        ],
        "intercept": 18937.692978063147,
        "betas": [-0.1295323083444758, -0.5603953797416523, 0.08014956879485062, -0.28291729214856054],
        "sigma": 442.06984309591326,
        "entry_z": 3.0,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "PANEL_2X2",
        "components": ["PANEL_1X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
        "intercept": 21783.253229735506,
        "betas": [-0.34317424505888905, 0.18104373486721692, -0.41149800200502956, -0.628654226694312],
        "sigma": 369.54249653714464,
        "entry_z": 2.5,
        "hold": 100,
        "exit": "fixed",
    },
    {
        "target": "PEBBLES_S",
        "components": ["PEBBLES_XS", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
        "intercept": 49997.436755970608,
        "betas": [-0.999926006686, -0.999951654763, -0.999926981924, -0.999945873064],
        "sigma": 2.798296213303394,
        "entry_z": 1.5,
        "hold": 200,
        "exit": "fixed",
    },
    {
        "target": "ROBOT_IRONING",
        "components": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY"],
        "intercept": 18545.65891347723,
        "betas": [0.12133139173436146, -0.6035255172035513, -0.4402725717106749, 0.015651900384425228],
        "sigma": 369.0771501834655,
        "entry_z": 2.5,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "SLEEP_POD_POLYESTER",
        "components": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
        "intercept": 84.64084048818248,
        "betas": [0.5185851713630322, -0.1455033575710156, 0.06990506069066837, 0.5837152771996909],
        "sigma": 327.3066485115772,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "SNACKPACK_STRAWBERRY",
        "components": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_RASPBERRY"],
        "intercept": 67692.39480337707,
        "betas": [-1.819519057618865, -1.6199756067024471, -1.0092655194895161, -1.3032960304327985],
        "sigma": 163.08409144921757,
        "entry_z": 2.0,
        "hold": 500,
        "exit": "zero",
    },
    {
        "target": "TRANSLATOR_VOID_BLUE",
        "components": [
            "TRANSLATOR_SPACE_GRAY",
            "TRANSLATOR_ASTRO_BLACK",
            "TRANSLATOR_ECLIPSE_CHARCOAL",
            "TRANSLATOR_GRAPHITE_MIST",
        ],
        "intercept": 15353.237252967916,
        "betas": [-0.40582283392210716, -0.6238663498409187, 0.5065746200270247, 0.021493389661280775],
        "sigma": 329.1562069293615,
        "entry_z": 2.5,
        "hold": 500,
        "exit": "fixed",
    },
    {
        "target": "UV_VISOR_MAGENTA",
        "components": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED"],
        "intercept": 19824.977653006463,
        "betas": [0.031230275469664674, -0.6565830090431027, -0.06530299043059871, -0.2874209095667269],
        "sigma": 264.0833293041973,
        "entry_z": 1.5,
        "hold": 500,
        "exit": "fixed",
    },
]


@dataclass(frozen=True)
class Candidate:
    lens: str
    group: str
    target: str
    label: str
    components: tuple[str, ...] = ()
    coeff: tuple[int, ...] = ()
    pca_k: int = 0

    @property
    def candidate_id(self) -> str:
        if self.lens == "integer_combo":
            spec = ",".join(str(v) for v in self.coeff)
        elif self.lens.startswith("pca"):
            spec = f"k={self.pca_k}"
        else:
            spec = ",".join(self.components)
        return f"{self.lens}|{self.group}|{self.target}|{spec}"


def read_prices() -> pd.DataFrame:
    frames = []
    for day in DAYS:
        path = DATA_DIR / f"prices_round_5_day_{day}.csv"
        frame = pd.read_csv(path, sep=";")
        frames.append(frame)
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_group_data(prices: pd.DataFrame) -> dict[str, dict[str, object]]:
    groups: dict[str, dict[str, object]] = {}
    for group, products in GROUPS.items():
        group_prices = prices[prices["product"].isin(products)]
        pivots = {
            col: group_prices.pivot(index=["day", "timestamp"], columns="product", values=col).sort_index()
            for col in ["mid_price", "bid_price_1", "ask_price_1"]
        }
        days = pivots["mid_price"].index.get_level_values("day").to_numpy()
        groups[group] = {
            "products": products,
            "days": days,
            "mid": pivots["mid_price"][products].to_numpy(dtype=float),
            "bid": pivots["bid_price_1"][products].to_numpy(dtype=float),
            "ask": pivots["ask_price_1"][products].to_numpy(dtype=float),
            "product_index": {product: idx for idx, product in enumerate(products)},
        }
    return groups


def fit_ols(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def past_rolling_mean(arr: np.ndarray, window: int) -> np.ndarray:
    out = np.full(len(arr), np.nan)
    csum = np.cumsum(np.insert(arr, 0, 0.0))
    for i in range(1, len(arr)):
        start = max(0, i - window)
        count = i - start
        out[i] = (csum[i] - csum[start]) / count if count else np.nan
    return out


def past_rolling_std(arr: np.ndarray, window: int) -> np.ndarray:
    out = np.full(len(arr), np.nan)
    csum = np.cumsum(np.insert(arr, 0, 0.0))
    csum2 = np.cumsum(np.insert(arr * arr, 0, 0.0))
    for i in range(2, len(arr)):
        start = max(0, i - window)
        count = i - start
        if count < 2:
            continue
        mean = (csum[i] - csum[start]) / count
        mean2 = (csum2[i] - csum2[start]) / count
        out[i] = math.sqrt(max(0.0, mean2 - mean * mean))
    return out


def centered_by_day(resid: np.ndarray, days: np.ndarray, mode: str) -> np.ndarray:
    out = np.full(len(resid), np.nan)
    for day in np.unique(days):
        idx = np.flatnonzero(days == day)
        r = resid[idx]
        if mode == "raw":
            out[idx] = r
        elif mode == "open100":
            if len(r) > 100:
                out[idx[100:]] = r[100:] - float(np.mean(r[:100]))
        elif mode == "rolling200":
            out[idx] = r - past_rolling_mean(r, 200)
        elif mode == "rolling500":
            out[idx] = r - past_rolling_mean(r, 500)
        elif mode == "expanding":
            out[idx] = r - past_rolling_mean(r, len(r))
        else:
            raise ValueError(mode)
    return out


def lag_diff(arr: np.ndarray, lag: int) -> np.ndarray:
    out = np.full(len(arr), np.nan)
    out[lag:] = arr[lag:] - arr[:-lag]
    return out


def acf1(arr: np.ndarray) -> float:
    arr = arr[np.isfinite(arr)]
    if len(arr) < 3:
        return float("nan")
    a = arr[:-1]
    b = arr[1:]
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def half_life(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0.0 or phi >= 1.0:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def mean_reversion_probe(sig: np.ndarray, horizon: int = 100, threshold: float = 2.0) -> tuple[int, float, float]:
    finite = np.isfinite(sig)
    sigma = float(np.std(sig[finite])) if np.any(finite) else 0.0
    if sigma <= 1e-12:
        return 0, 0.0, 0.0
    z = sig / sigma
    idx = np.flatnonzero(np.isfinite(z) & (np.abs(z) >= threshold))
    idx = idx[idx + horizon < len(sig)]
    if len(idx) == 0:
        return 0, 0.0, 0.0
    improve = np.sign(sig[idx]) * (sig[idx] - sig[idx + horizon])
    return int(len(idx)), float(np.mean(improve)), float(np.mean(improve > 0.0))


def relation_label(products: list[str], coeff: tuple[int, ...]) -> str:
    parts = []
    for product, value in zip(products, coeff):
        if value == 0:
            continue
        parts.append(f"{value:+d}*{product}")
    return " ".join(parts).lstrip("+")


def generate_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for group, products in GROUPS.items():
        for target in products:
            others = [p for p in products if p != target]
            for component in others:
                candidates.append(
                    Candidate(
                        lens="pair_ols",
                        group=group,
                        target=target,
                        components=(component,),
                        label=f"{target} ~ {component}",
                    )
                )
            candidates.append(
                Candidate(
                    lens="basket_1v4",
                    group=group,
                    target=target,
                    components=tuple(others),
                    label=f"{target} ~ other 4",
                )
            )
            for k in [1, 2]:
                candidates.append(
                    Candidate(
                        lens=f"pca{k}_residual",
                        group=group,
                        target=target,
                        pca_k=k,
                        label=f"{target} minus PCA{k} reconstruction",
                    )
                )

            target_idx = products.index(target)
            for a, b in itertools.combinations([i for i in range(len(products)) if i != target_idx], 2):
                for sa, sb in itertools.product([-1, 1], repeat=2):
                    coeff = [0] * len(products)
                    coeff[target_idx] = 1
                    coeff[a] = sa
                    coeff[b] = sb
                    coeff_tuple = tuple(coeff)
                    candidates.append(
                        Candidate(
                            lens="integer_combo",
                            group=group,
                            target=target,
                            coeff=coeff_tuple,
                            label=relation_label(products, coeff_tuple),
                        )
                    )
            for signs in itertools.product([-1, 1], repeat=4):
                coeff = [0] * len(products)
                coeff[target_idx] = 1
                for idx, sign in zip([i for i in range(len(products)) if i != target_idx], signs):
                    coeff[idx] = sign
                coeff_tuple = tuple(coeff)
                candidates.append(
                    Candidate(
                        lens="integer_combo",
                        group=group,
                        target=target,
                        coeff=coeff_tuple,
                        label=relation_label(products, coeff_tuple),
                    )
                )
    return candidates


def fit_candidate_residual(
    candidate: Candidate,
    group_data: dict[str, object],
    train_day: np.ndarray,
    test_day: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    products = group_data["products"]
    days = group_data["days"]
    values = group_data["mid"]
    product_index = group_data["product_index"]
    train_mask = np.isin(days, train_day)
    test_mask = days == test_day
    train_values = values[train_mask]
    test_values = values[test_mask]
    if candidate.lens in {"pair_ols", "basket_1v4"}:
        target_idx = product_index[candidate.target]
        component_idx = [product_index[component] for component in candidate.components]
        y_train = train_values[:, target_idx]
        x_train = train_values[:, component_idx]
        y_test = test_values[:, target_idx]
        x_test = test_values[:, component_idx]
        coef = fit_ols(y_train, x_train)
        train_resid = y_train - predict_ols(coef, x_train)
        test_resid = y_test - predict_ols(coef, x_test)
    elif candidate.lens.startswith("pca"):
        k = candidate.pca_k
        mean = train_values.mean(axis=0)
        centered_train = train_values - mean
        _, _, vt = np.linalg.svd(centered_train, full_matrices=False)
        pcs = vt[:k]
        recon_train = (centered_train @ pcs.T) @ pcs
        recon_test = ((test_values - mean) @ pcs.T) @ pcs
        target_idx = product_index[candidate.target]
        train_resid = centered_train[:, target_idx] - recon_train[:, target_idx]
        test_resid = (test_values - mean)[:, target_idx] - recon_test[:, target_idx]
    elif candidate.lens == "integer_combo":
        coeff = np.array(candidate.coeff, dtype=float)
        train_resid = train_values @ coeff
        test_resid = test_values @ coeff
    else:
        raise ValueError(candidate.lens)
    train_resid = train_resid - float(np.mean(train_resid))
    test_resid = test_resid - float(np.mean(train_resid))
    return train_resid, days[train_mask], test_resid, test_mask


def simulate(
    sig: np.ndarray,
    bid: np.ndarray,
    ask: np.ndarray,
    sigma: float,
    threshold: float,
    horizon: int,
    exit_rule: str,
    slope_mode: str,
    vol_mode: str,
    low_vol_cut: float,
    slope: np.ndarray | None = None,
    vol: np.ndarray | None = None,
) -> dict[str, float | int]:
    if sigma <= 1e-12:
        return {"pnl": 0.0, "trades": 0, "wins": 0, "avg_hold": 0.0, "max_hold": 0}
    z = sig / sigma
    if slope is None:
        slope = lag_diff(sig, 5)
    if vol is None:
        vol = past_rolling_std(sig, 200)
    mask = np.isfinite(z) & (np.abs(z) >= threshold)
    if slope_mode == "reverting":
        mask &= np.isfinite(slope) & (sig * slope < 0.0)
    elif slope_mode == "extending":
        mask &= np.isfinite(slope) & (sig * slope > 0.0)
    elif slope_mode != "any":
        raise ValueError(slope_mode)
    if vol_mode == "low_vol":
        mask &= np.isfinite(vol) & (vol <= low_vol_cut)
    elif vol_mode == "high_vol":
        mask &= np.isfinite(vol) & (vol > low_vol_cut)
    elif vol_mode != "any":
        raise ValueError(vol_mode)

    pnl = 0.0
    trades = 0
    wins = 0
    hold_sum = 0
    max_hold = 0
    i = 0
    trigger_idx = np.flatnonzero(mask)
    for entry_i in trigger_idx:
        if entry_i < i or entry_i >= len(sig) - 1:
            continue
        direction = -1 if sig[entry_i] > 0.0 else 1
        exit_i = min(entry_i + horizon, len(sig) - 1)
        if exit_rule == "zero_cross":
            sign0 = np.sign(sig[entry_i])
            path = sig[entry_i + 1 : exit_i + 1]
            crosses = np.flatnonzero(np.isfinite(path) & ((path == 0.0) | (np.sign(path) != sign0)))
            if len(crosses):
                exit_i = entry_i + 1 + int(crosses[0])
        elif exit_rule != "fixed":
            raise ValueError(exit_rule)
        entry_price = ask[entry_i] if direction > 0 else bid[entry_i]
        exit_price = bid[exit_i] if direction > 0 else ask[exit_i]
        edge = (exit_price - entry_price) * direction
        pnl += edge * QTY
        trades += 1
        wins += int(edge > 0.0)
        hold = exit_i - entry_i
        hold_sum += hold
        max_hold = max(max_hold, hold)
        i = exit_i + 1
    return {
        "pnl": float(pnl),
        "trades": int(trades),
        "wins": int(wins),
        "avg_hold": float(hold_sum / trades) if trades else 0.0,
        "max_hold": int(max_hold),
    }


def screen_candidates(
    candidates: list[Candidate],
    group_data_by_name: dict[str, dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for n, candidate in enumerate(candidates, start=1):
        if n % 250 == 0:
            print(f"Screened {n}/{len(candidates)} candidates...")
        group_data = group_data_by_name[candidate.group]
        product_idx = group_data["product_index"][candidate.target]
        bids = group_data["bid"]
        asks = group_data["ask"]
        for test_day in DAYS:
            train_days = np.array([day for day in DAYS if day != test_day])
            train_resid, train_day_values, test_resid, test_mask = fit_candidate_residual(
                candidate, group_data, train_days, test_day
            )
            train_sig = centered_by_day(train_resid, train_day_values, "raw")
            test_sig = test_resid.copy()
            sigma = float(np.nanstd(train_sig))
            bid = bids[test_mask, product_idx]
            ask = asks[test_mask, product_idx]
            result = simulate(
                test_sig,
                bid,
                ask,
                sigma,
                threshold=2.0,
                horizon=200,
                exit_rule="fixed",
                slope_mode="any",
                vol_mode="any",
                low_vol_cut=float("inf"),
            )
            trigger_n, mr_points, good_pct = mean_reversion_probe(test_sig, horizon=100, threshold=2.0)
            phi = acf1(test_sig)
            rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "lens": candidate.lens,
                    "group": candidate.group,
                    "target": candidate.target,
                    "label": candidate.label,
                    "test_day": test_day,
                    "train_sigma": sigma,
                    "test_sd": float(np.nanstd(test_sig)),
                    "test_acf1": phi,
                    "test_half_life": half_life(phi),
                    "mr_trigger_n": trigger_n,
                    "mr_points_h100": mr_points,
                    "mr_good_pct_h100": good_pct,
                    **result,
                }
            )
    day_rows = pd.DataFrame(rows)
    summary = summarize(day_rows, ["candidate_id", "lens", "group", "target", "label"], pnl_col="pnl")
    summary = summary.sort_values(
        ["positive_days", "min_day_pnl", "total_pnl", "avg_pnl_per_trade"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    return day_rows, summary


def summarize(rows: pd.DataFrame, keys: list[str], pnl_col: str = "pnl") -> pd.DataFrame:
    out = []
    for key, frame in rows.groupby(keys, dropna=False):
        trades = int(frame["trades"].sum())
        wins = int(frame["wins"].sum())
        total_pnl = float(frame[pnl_col].sum())
        row = {name: value for name, value in zip(keys, key if isinstance(key, tuple) else (key,))}
        row.update(
            {
                "days": int(frame["test_day"].nunique()),
                "total_pnl": total_pnl,
                "min_day_pnl": float(frame[pnl_col].min()),
                "max_day_pnl": float(frame[pnl_col].max()),
                "positive_days": int((frame[pnl_col] > 0.0).sum()),
                "total_trades": trades,
                "win_pct": wins / trades if trades else 0.0,
                "avg_pnl_per_trade": total_pnl / trades if trades else 0.0,
                "avg_hold": float(np.average(frame["avg_hold"], weights=np.maximum(frame["trades"], 1))),
                "max_hold": int(frame["max_hold"].max()) if "max_hold" in frame else 0,
            }
        )
        if "mr_points_h100" in frame:
            row["mean_mr_points_h100"] = float(frame["mr_points_h100"].mean())
            row["mean_mr_good_pct_h100"] = float(frame["mr_good_pct_h100"].mean())
        out.append(row)
    return pd.DataFrame(out)


def select_sweep_candidates(screen_summary: pd.DataFrame, all_candidates: list[Candidate]) -> list[Candidate]:
    lookup = {candidate.candidate_id: candidate for candidate in all_candidates}
    ranked = screen_summary[screen_summary["days"] == 3].copy()
    ranked = ranked.sort_values(
        ["lens", "group", "target", "positive_days", "min_day_pnl", "total_pnl"],
        ascending=[True, True, True, False, False, False],
    )
    selected = (
        ranked.groupby(["lens", "group", "target"], as_index=False, dropna=False)
        .head(1)
        .sort_values(
            ["positive_days", "min_day_pnl", "total_pnl", "avg_pnl_per_trade"],
            ascending=[False, False, False, False],
        )
    )
    selected_ids = selected.head(120)["candidate_id"].tolist()
    return [lookup[candidate_id] for candidate_id in selected_ids]


def run_parameter_sweep(
    candidates: list[Candidate],
    group_data_by_name: dict[str, dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for n, candidate in enumerate(candidates, start=1):
        print(f"Sweeping {n}/{len(candidates)} {candidate.candidate_id}")
        group_data = group_data_by_name[candidate.group]
        product_idx = group_data["product_index"][candidate.target]
        bids = group_data["bid"]
        asks = group_data["ask"]
        for test_day in DAYS:
            train_days = np.array([day for day in DAYS if day != test_day])
            train_resid, train_day_values, test_resid, test_mask = fit_candidate_residual(
                candidate, group_data, train_days, test_day
            )
            bid = bids[test_mask, product_idx]
            ask = asks[test_mask, product_idx]
            train_raw = centered_by_day(train_resid, train_day_values, "raw")
            raw_vol = past_rolling_std(train_raw[np.isfinite(train_raw)], 200)
            low_vol_cut = float(np.nanmedian(raw_vol)) if np.any(np.isfinite(raw_vol)) else float("inf")
            for center_mode in CENTER_MODES:
                train_sig = centered_by_day(train_resid, train_day_values, center_mode)
                sigma = float(np.nanstd(train_sig))
                if sigma <= 1e-12:
                    continue
                test_sig = centered_by_day(test_resid, np.full(len(test_resid), test_day), center_mode)
                slope = lag_diff(test_sig, 5)
                vol = past_rolling_std(test_sig, 200)
                for threshold in THRESHOLDS:
                    for horizon in HORIZONS:
                        for exit_rule in EXIT_RULES:
                            for slope_mode in SLOPE_MODES:
                                for vol_mode in VOL_MODES:
                                    result = simulate(
                                        test_sig,
                                        bid,
                                        ask,
                                        sigma,
                                        threshold,
                                        horizon,
                                        exit_rule,
                                        slope_mode,
                                        vol_mode,
                                        low_vol_cut,
                                        slope,
                                        vol,
                                    )
                                    rows.append(
                                        {
                                            "candidate_id": candidate.candidate_id,
                                            "lens": candidate.lens,
                                            "group": candidate.group,
                                            "target": candidate.target,
                                            "label": candidate.label,
                                            "test_day": test_day,
                                            "center_mode": center_mode,
                                            "threshold": threshold,
                                            "horizon": horizon,
                                            "exit_rule": exit_rule,
                                            "slope_mode": slope_mode,
                                            "vol_mode": vol_mode,
                                            "sigma_train": sigma,
                                            **result,
                                        }
                                    )
    day_rows = pd.DataFrame(rows)
    keys = [
        "candidate_id",
        "lens",
        "group",
        "target",
        "label",
        "center_mode",
        "threshold",
        "horizon",
        "exit_rule",
        "slope_mode",
        "vol_mode",
    ]
    summary = summarize(day_rows, keys)
    summary = summary.sort_values(
        ["positive_days", "min_day_pnl", "total_pnl", "avg_pnl_per_trade"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
    return day_rows, summary


def run_v3_baseline(group_data_by_name: dict[str, dict[str, object]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    product_to_group = {product: group for group, products in GROUPS.items() for product in products}
    for spec in V3_SPECS:
        target = spec["target"]
        group = product_to_group[target]
        group_data = group_data_by_name[group]
        values = group_data["mid"]
        bids = group_data["bid"]
        asks = group_data["ask"]
        days = group_data["days"]
        product_index = group_data["product_index"]
        target_idx = product_index[target]
        for day in DAYS:
            test_mask = days == day
            test_values = values[test_mask]
            fair = np.full(len(test_values), float(spec["intercept"]))
            for component, beta in zip(spec["components"], spec["betas"]):
                fair += float(beta) * test_values[:, product_index[component]]
            sig = test_values[:, target_idx] - fair
            bid = bids[test_mask, target_idx]
            ask = asks[test_mask, target_idx]
            result = simulate(
                sig,
                bid,
                ask,
                float(spec["sigma"]),
                float(spec["entry_z"]),
                int(spec["hold"]),
                "zero_cross" if spec["exit"] == "zero" else "fixed",
                "any",
                "any",
                float("inf"),
            )
            rows.append(
                {
                    "candidate_id": f"v3|{group}|{target}",
                    "lens": "v3_current",
                    "group": group,
                    "target": target,
                    "label": f"current v3 {target}",
                    "test_day": day,
                    "center_mode": "static",
                    "threshold": float(spec["entry_z"]),
                    "horizon": int(spec["hold"]),
                    "exit_rule": "zero_cross" if spec["exit"] == "zero" else "fixed",
                    "slope_mode": "any",
                    "vol_mode": "any",
                    "sigma_train": float(spec["sigma"]),
                    **result,
                }
            )
    day_rows = pd.DataFrame(rows)
    keys = [
        "candidate_id",
        "lens",
        "group",
        "target",
        "label",
        "center_mode",
        "threshold",
        "horizon",
        "exit_rule",
        "slope_mode",
        "vol_mode",
    ]
    return day_rows, summarize(day_rows, keys).sort_values("total_pnl", ascending=False).reset_index(drop=True)


def plateau_rows(summary: pd.DataFrame) -> pd.DataFrame:
    robust = summary[
        (summary["days"] == 3)
        & (summary["positive_days"] == 3)
        & (summary["min_day_pnl"] > 0.0)
        & (summary["total_trades"] >= 10)
    ].copy()
    rows = []
    for key, frame in robust.groupby(["candidate_id", "lens", "group", "target", "label"]):
        best = frame.sort_values(["min_day_pnl", "total_pnl"], ascending=False).iloc[0]
        rows.append(
            {
                "candidate_id": key[0],
                "lens": key[1],
                "group": key[2],
                "target": key[3],
                "label": key[4],
                "robust_param_count": int(len(frame)),
                "best_total_pnl": float(best["total_pnl"]),
                "best_min_day_pnl": float(best["min_day_pnl"]),
                "best_trades": int(best["total_trades"]),
                "best_center_mode": best["center_mode"],
                "best_threshold": float(best["threshold"]),
                "best_horizon": int(best["horizon"]),
                "best_exit_rule": best["exit_rule"],
                "best_slope_mode": best["slope_mode"],
                "best_vol_mode": best["vol_mode"],
                "thresholds_passing": ",".join(str(v) for v in sorted(frame["threshold"].unique())),
                "horizons_passing": ",".join(str(int(v)) for v in sorted(frame["horizon"].unique())),
                "centers_passing": ",".join(sorted(frame["center_mode"].unique())),
                "slope_modes_passing": ",".join(sorted(frame["slope_mode"].unique())),
                "vol_modes_passing": ",".join(sorted(frame["vol_mode"].unique())),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["robust_param_count", "best_min_day_pnl", "best_total_pnl"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def rejection_rows(screen_summary: pd.DataFrame, sweep_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lens, frame in screen_summary.groupby("lens"):
        robust = frame[
            (frame["days"] == 3)
            & (frame["positive_days"] == 3)
            & (frame["min_day_pnl"] > 0.0)
            & (frame["total_trades"] >= 10)
        ]
        best = frame.sort_values(["positive_days", "min_day_pnl", "total_pnl"], ascending=False).iloc[0]
        rows.append(
            {
                "scope": "screen",
                "lens": lens,
                "candidates": int(frame["candidate_id"].nunique()),
                "robust_candidates": int(robust["candidate_id"].nunique()),
                "best_candidate_id": best["candidate_id"],
                "best_total_pnl": float(best["total_pnl"]),
                "best_min_day_pnl": float(best["min_day_pnl"]),
                "best_positive_days": int(best["positive_days"]),
                "verdict": "kept for sweep" if len(robust) else "rejected: no stable baseline edge",
            }
        )
    for lens, frame in sweep_summary.groupby("lens"):
        robust = frame[
            (frame["days"] == 3)
            & (frame["positive_days"] == 3)
            & (frame["min_day_pnl"] > 0.0)
            & (frame["total_trades"] >= 10)
        ]
        best = frame.sort_values(["positive_days", "min_day_pnl", "total_pnl"], ascending=False).iloc[0]
        rows.append(
            {
                "scope": "sweep",
                "lens": lens,
                "candidates": int(frame["candidate_id"].nunique()),
                "robust_candidates": int(robust["candidate_id"].nunique()),
                "best_candidate_id": best["candidate_id"],
                "best_total_pnl": float(best["total_pnl"]),
                "best_min_day_pnl": float(best["min_day_pnl"]),
                "best_positive_days": int(best["positive_days"]),
                "verdict": "candidate-specific" if len(robust) else "rejected: no parameter plateau",
            }
        )
    return pd.DataFrame(rows)


def md_table(frame: pd.DataFrame, columns: list[str], n: int = 20) -> str:
    if frame.empty:
        return "No rows passed the filter."
    return frame.head(n)[columns].round(4).to_markdown(index=False)


def write_report(
    screen_summary: pd.DataFrame,
    sweep_summary: pd.DataFrame,
    plateaus: pd.DataFrame,
    rejections: pd.DataFrame,
    v3_summary: pd.DataFrame,
) -> None:
    robust = sweep_summary[
        (sweep_summary["days"] == 3)
        & (sweep_summary["positive_days"] == 3)
        & (sweep_summary["min_day_pnl"] > 0.0)
        & (sweep_summary["total_trades"] >= 10)
    ].sort_values(["min_day_pnl", "total_pnl"], ascending=False)
    top_total = robust.sort_values(["total_pnl", "min_day_pnl"], ascending=False)
    lens_counts = (
        robust.groupby("lens")["candidate_id"].nunique().reset_index(name="robust_candidate_count")
        if not robust.empty
        else pd.DataFrame(columns=["lens", "robust_candidate_count"])
    )
    v3_total = float(v3_summary["total_pnl"].sum())
    v3_min_sum = float(v3_summary["min_day_pnl"].sum())
    lines = [
        "# Round 5 Stat-Arb Mean-Reversion Deep Scan",
        "",
        "Validation is leave-one-day-out: fit on two of days 2, 3, 4 and test the held-out day, then require all three held-out days to be stable. Execution proxy trades only the target leg, crosses top of book on entry/exit, uses quantity 10, and allows one open position per candidate.",
        "",
        f"Broad screen covered {screen_summary['candidate_id'].nunique()} candidate residual definitions. Parameter sweep covered {sweep_summary['candidate_id'].nunique()} best-per-group/product/lens definitions across centers, z thresholds, horizons, exits, velocity gates, and volatility regimes.",
        "",
        f"Current v3 isolated-spec proxy total PnL is {v3_total:.0f} across {int(v3_summary['total_trades'].sum())} trades. Sum of isolated min-day PnL is {v3_min_sum:.0f}; this is not a portfolio conflict simulation, but it matches the same target-only crossing-cost proxy used below.",
        "",
        "## Top Robust Candidates By Worst Day",
        "",
        md_table(
            robust,
            [
                "lens",
                "group",
                "target",
                "center_mode",
                "threshold",
                "horizon",
                "exit_rule",
                "slope_mode",
                "vol_mode",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
                "avg_pnl_per_trade",
            ],
            n=25,
        ),
        "",
        "## Top Robust Candidates By Total PnL",
        "",
        md_table(
            top_total,
            [
                "lens",
                "group",
                "target",
                "center_mode",
                "threshold",
                "horizon",
                "exit_rule",
                "slope_mode",
                "vol_mode",
                "total_pnl",
                "min_day_pnl",
                "total_trades",
                "win_pct",
            ],
            n=25,
        ),
        "",
        "## Parameter Plateaus",
        "",
        md_table(
            plateaus,
            [
                "lens",
                "group",
                "target",
                "robust_param_count",
                "best_total_pnl",
                "best_min_day_pnl",
                "best_trades",
                "best_center_mode",
                "best_threshold",
                "best_horizon",
                "thresholds_passing",
                "horizons_passing",
            ],
            n=25,
        ),
        "",
        "## Robust Candidate Counts By Lens",
        "",
        md_table(lens_counts.sort_values("robust_candidate_count", ascending=False), ["lens", "robust_candidate_count"], n=20),
        "",
        "## Rejected Ideas",
        "",
        md_table(
            rejections,
            [
                "scope",
                "lens",
                "candidates",
                "robust_candidates",
                "best_total_pnl",
                "best_min_day_pnl",
                "best_positive_days",
                "verdict",
            ],
            n=20,
        ),
        "",
        "## Notes",
        "",
        "- The strongest rows are still target-only proxies; no hedge-leg fills are assumed. A deployable change should check portfolio conflicts before replacing v3 specs.",
        "- `open100`, rolling, and expanding centers are included to avoid relying on held-out day intercepts. Robust rows that only pass under `raw` should be treated as lower quality.",
        "- Velocity gates distinguish entries while residuals are already reverting versus still extending. Volatility regimes split on train-only rolling residual volatility median.",
    ]
    (OUT_DIR / "17_stat_arb_mr_deep.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    group_data = make_group_data(prices)
    candidates = generate_candidates()
    print(f"Generated {len(candidates)} candidate residual definitions.")

    screen_day, screen_summary = screen_candidates(candidates, group_data)
    screen_day.to_csv(OUT_DIR / "17_stat_arb_mr_deep_screen_by_day.csv", index=False)
    screen_summary.to_csv(OUT_DIR / "17_stat_arb_mr_deep_screen_summary.csv", index=False)

    sweep_candidates = select_sweep_candidates(screen_summary, candidates)
    sweep_day, sweep_summary = run_parameter_sweep(sweep_candidates, group_data)
    sweep_day.to_csv(OUT_DIR / "17_stat_arb_mr_deep_by_day.csv", index=False)
    sweep_summary.to_csv(OUT_DIR / "17_stat_arb_mr_deep_summary.csv", index=False)

    v3_day, v3_summary = run_v3_baseline(group_data)
    v3_day.to_csv(OUT_DIR / "17_stat_arb_mr_deep_v3_by_day.csv", index=False)
    v3_summary.to_csv(OUT_DIR / "17_stat_arb_mr_deep_v3_summary.csv", index=False)

    plateaus = plateau_rows(sweep_summary)
    plateaus.to_csv(OUT_DIR / "17_stat_arb_mr_deep_plateaus.csv", index=False)
    rejections = rejection_rows(screen_summary, sweep_summary)
    rejections.to_csv(OUT_DIR / "17_stat_arb_mr_deep_rejections.csv", index=False)
    write_report(screen_summary, sweep_summary, plateaus, rejections, v3_summary)
    print("Wrote 17_stat_arb_mr_deep outputs.")


if __name__ == "__main__":
    main()
