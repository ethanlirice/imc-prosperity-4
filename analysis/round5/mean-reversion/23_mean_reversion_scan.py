import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5-mean-reversion"

WINDOWS = [50, 100, 200, 500, 1000]
HORIZONS = [10, 25, 50, 100, 200, 500]
THRESHOLDS = [1.0, 1.5, 2.0, 2.5, 3.0]
REGRESSION_OPEN_N = 500
MIN_SIGNALS = 20

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
    "ROBOT": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UV_VISOR": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
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


def acf1(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < 3:
        return float("nan")
    a = arr[:-1]
    b = arr[1:]
    sa = float(np.std(a))
    sb = float(np.std(b))
    if sa <= 1e-12 or sb <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def half_life_from_acf(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0.0 or phi >= 1.0:
        return float("inf")
    return float(-math.log(2.0) / math.log(phi))


def summarize(rows: list[dict], keys: list[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    day_df = pd.DataFrame(rows)
    groups = []
    for values, sub in day_df.groupby(keys, dropna=False):
        if not isinstance(values, tuple):
            values = (values,)
        row = dict(zip(keys, values))
        total_signal_n = int(sub["signal_n"].sum())
        weighted_cols = [
            "mid_edge",
            "active_edge",
            "hit_rate_mid",
            "hit_rate_active",
            "avg_abs_z",
            "acf_ret_1",
            "acf_dev_1",
            "half_life_dev",
            "signal_pct",
        ]
        row["signal_n"] = total_signal_n
        row["positive_days_active"] = int((sub["active_edge"] > 0).sum())
        row["positive_days_mid"] = int((sub["mid_edge"] > 0).sum())
        row["min_day_active_edge"] = float(sub["active_edge"].min())
        row["min_day_mid_edge"] = float(sub["mid_edge"].min())
        row["worst_day_signal_n"] = int(sub["signal_n"].min())
        row["days_with_signals"] = int((sub["signal_n"] > 0).sum())
        for col in weighted_cols:
            valid = sub[np.isfinite(sub[col]) & (sub["signal_n"] > 0)]
            if len(valid) == 0:
                row[col] = float("nan")
            else:
                row[col] = float(np.average(valid[col], weights=valid["signal_n"]))
        groups.append(row)
    return pd.DataFrame(groups).sort_values(
        ["positive_days_active", "min_day_active_edge", "active_edge", "signal_n"],
        ascending=[False, False, False, False],
    )


def signal_metrics(
    product: str,
    day: int,
    kind: str,
    window: int,
    threshold: float,
    horizon: int,
    mid: pd.Series,
    bid: pd.Series,
    ask: pd.Series,
    dev: pd.Series,
    z: pd.Series,
) -> dict:
    signal = z.abs() >= threshold
    future = mid.shift(-horizon)
    direction = -np.sign(z)
    mid_edge = direction * (future - mid)
    active_buy_edge = future - ask
    active_sell_edge = bid - future
    active_edge = pd.Series(np.where(direction > 0, active_buy_edge, active_sell_edge), index=mid.index)
    valid = signal & future.notna() & bid.notna() & ask.notna() & np.isfinite(z)
    sig_n = int(valid.sum())
    total_n = int((future.notna() & bid.notna() & ask.notna()).sum())
    if sig_n == 0:
        avg_mid = float("nan")
        avg_active = float("nan")
        hit_mid = float("nan")
        hit_active = float("nan")
        avg_abs_z = float("nan")
    else:
        avg_mid = float(mid_edge[valid].mean())
        avg_active = float(active_edge[valid].mean())
        hit_mid = float((mid_edge[valid] > 0).mean())
        hit_active = float((active_edge[valid] > 0).mean())
        avg_abs_z = float(z[valid].abs().mean())
    ret = mid.diff()
    phi = acf1(dev.dropna().to_numpy(dtype=float))
    return {
        "product": product,
        "day": day,
        "kind": kind,
        "window": window,
        "threshold": threshold,
        "horizon": horizon,
        "signal_n": sig_n,
        "total_n": total_n,
        "signal_pct": sig_n / total_n if total_n else float("nan"),
        "avg_abs_z": avg_abs_z,
        "mid_edge": avg_mid,
        "active_edge": avg_active,
        "hit_rate_mid": hit_mid,
        "hit_rate_active": hit_active,
        "acf_ret_1": acf1(ret.to_numpy(dtype=float)),
        "acf_dev_1": phi,
        "half_life_dev": half_life_from_acf(phi),
    }


def rolling_product_scan(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    day_rows = []
    for (day, product), sub in prices.groupby(["day", "product"], sort=True):
        sub = sub.sort_values("timestamp")
        mid = sub["mid_price"].astype(float).reset_index(drop=True)
        bid = sub["bid_price_1"].astype(float).reset_index(drop=True)
        ask = sub["ask_price_1"].astype(float).reset_index(drop=True)
        for window in WINDOWS:
            min_periods = max(20, window // 5)
            mean = mid.rolling(window, min_periods=min_periods).mean().shift(1)
            std = mid.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
            dev = mid - mean
            z = dev / std.replace(0, np.nan)
            for threshold in THRESHOLDS:
                for horizon in HORIZONS:
                    row = signal_metrics(product, int(day), "product_rolling", window, threshold, horizon, mid, bid, ask, dev, z)
                    day_rows.append(row)
    day_df = pd.DataFrame(day_rows)
    scan_df = summarize(day_rows, ["product", "kind", "window", "threshold", "horizon"])
    return scan_df, day_df


def group_fairs(wide_mid: pd.DataFrame, group: str, products: list[str], mode: str, day: int) -> pd.DataFrame:
    sub = wide_mid.loc[day, products].reset_index(drop=True)
    fairs = pd.DataFrame(index=sub.index, columns=products, dtype=float)
    if mode == "equal":
        for product in products:
            peers = [p for p in products if p != product]
            fairs[product] = sub[peers].mean(axis=1)
    elif mode == "vol":
        ret_vol = sub.diff().std(ddof=0).replace(0, np.nan)
        for product in products:
            peers = [p for p in products if p != product]
            inv = 1.0 / ret_vol[peers]
            inv = inv.replace([np.inf, -np.inf], np.nan).fillna(0.0)
            if float(inv.sum()) <= 0.0:
                weights = pd.Series(1.0 / len(peers), index=peers)
            else:
                weights = inv / inv.sum()
            fairs[product] = sub[peers].mul(weights, axis=1).sum(axis=1)
    elif mode == "regression_open500":
        for product in products:
            peers = [p for p in products if p != product]
            train = sub[[product] + peers].iloc[:REGRESSION_OPEN_N].dropna()
            if len(train) < len(peers) + 20:
                fairs[product] = np.nan
                continue
            x = np.column_stack([np.ones(len(train)), train[peers].to_numpy(dtype=float)])
            y = train[product].to_numpy(dtype=float)
            coef, *_ = np.linalg.lstsq(x, y, rcond=None)
            all_x = np.column_stack([np.ones(len(sub)), sub[peers].to_numpy(dtype=float)])
            fairs[product] = all_x @ coef
    else:
        raise ValueError(mode)
    return fairs


def group_index_scan(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mid_wide = prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()
    bid_wide = prices.pivot(index=["day", "timestamp"], columns="product", values="bid_price_1").sort_index()
    ask_wide = prices.pivot(index=["day", "timestamp"], columns="product", values="ask_price_1").sort_index()
    day_rows = []
    for group, products in GROUPS.items():
        for day in sorted(prices["day"].unique()):
            fairs_by_mode = {mode: group_fairs(mid_wide, group, products, mode, int(day)) for mode in ["equal", "vol", "regression_open500"]}
            for mode, fairs in fairs_by_mode.items():
                for product in products:
                    mid = mid_wide.loc[day, product].reset_index(drop=True).astype(float)
                    bid = bid_wide.loc[day, product].reset_index(drop=True).astype(float)
                    ask = ask_wide.loc[day, product].reset_index(drop=True).astype(float)
                    fair = fairs[product].reset_index(drop=True).astype(float)
                    raw_dev = mid - fair
                    for window in WINDOWS:
                        min_periods = max(20, window // 5)
                        mean = raw_dev.rolling(window, min_periods=min_periods).mean().shift(1)
                        std = raw_dev.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
                        dev = raw_dev - mean
                        z = dev / std.replace(0, np.nan)
                        if mode == "regression_open500":
                            z.iloc[:REGRESSION_OPEN_N] = np.nan
                        for threshold in THRESHOLDS:
                            for horizon in HORIZONS:
                                row = signal_metrics(product, int(day), f"group_{mode}", window, threshold, horizon, mid, bid, ask, dev, z)
                                row["group"] = group
                                day_rows.append(row)
    day_df = pd.DataFrame(day_rows)
    scan_df = summarize(day_rows, ["group", "product", "kind", "window", "threshold", "horizon"])
    return scan_df, day_df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    if not frames:
        raise FileNotFoundError(DATA_DIR)
    prices = pd.concat(frames, ignore_index=True)
    product_scan, product_day = rolling_product_scan(prices)
    group_scan, group_day = group_index_scan(prices)
    product_scan.to_csv(OUT_DIR / "mr_product_scan.csv", index=False)
    product_day.to_csv(OUT_DIR / "mr_product_day.csv", index=False)
    group_scan.to_csv(OUT_DIR / "mr_group_scan.csv", index=False)
    group_day.to_csv(OUT_DIR / "mr_group_day.csv", index=False)
    robust_products = product_scan[(product_scan["signal_n"] >= MIN_SIGNALS) & (product_scan["positive_days_active"] == 3)]
    robust_groups = group_scan[(group_scan["signal_n"] >= MIN_SIGNALS) & (group_scan["positive_days_active"] == 3)]
    print("product_rows", len(product_scan), "product_day_rows", len(product_day))
    print("group_rows", len(group_scan), "group_day_rows", len(group_day))
    if len(robust_products):
        print("top_product_active")
        print(robust_products.head(15).to_string(index=False))
    else:
        print("top_product_active none")
    if len(robust_groups):
        print("top_group_active")
        print(robust_groups.head(15).to_string(index=False))
    else:
        print("top_group_active none")


if __name__ == "__main__":
    main()
