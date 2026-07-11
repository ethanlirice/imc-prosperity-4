import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5-mean-reversion"
LIMIT = 10
TOP_N_PER_FAMILY = 20

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
PRODUCT_TO_GROUP = {product: group for group, products in GROUPS.items() for product in products}


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    if not frames:
        raise FileNotFoundError(DATA_DIR)
    return pd.concat(frames, ignore_index=True)


def active_fill(row: pd.Series, side: int, qty: int) -> tuple[float, int]:
    remaining = qty
    spent = 0.0
    filled = 0
    if side > 0:
        for level in (1, 2, 3):
            price = row.get(f"ask_price_{level}")
            volume = row.get(f"ask_volume_{level}")
            if not np.isfinite(price) or not np.isfinite(volume) or volume <= 0:
                continue
            take = min(remaining, int(volume))
            spent += float(price) * take
            filled += take
            remaining -= take
            if remaining <= 0:
                break
    else:
        for level in (1, 2, 3):
            price = row.get(f"bid_price_{level}")
            volume = row.get(f"bid_volume_{level}")
            if not np.isfinite(price) or not np.isfinite(volume) or volume <= 0:
                continue
            take = min(remaining, int(volume))
            spent += float(price) * take
            filled += take
            remaining -= take
            if remaining <= 0:
                break
    if filled <= 0:
        return 0.0, 0
    return spent / filled, filled


def product_z(sub: pd.DataFrame, window: int) -> pd.Series:
    mid = sub["mid_price"].astype(float)
    min_periods = max(20, window // 5)
    mean = mid.rolling(window, min_periods=min_periods).mean().shift(1)
    std = mid.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
    return (mid - mean) / std.replace(0, np.nan)


def group_fairs(wide_mid: pd.DataFrame, products: list[str], mode: str, day: int) -> pd.DataFrame:
    sub = wide_mid.loc[day, products].reset_index(drop=True)
    fairs = pd.DataFrame(index=sub.index, columns=products, dtype=float)
    if mode == "group_equal":
        for product in products:
            peers = [p for p in products if p != product]
            fairs[product] = sub[peers].mean(axis=1)
    elif mode == "group_vol":
        ret_vol = sub.diff().std(ddof=0).replace(0, np.nan)
        for product in products:
            peers = [p for p in products if p != product]
            inv = 1.0 / ret_vol[peers]
            inv = inv.replace([np.inf, -np.inf], np.nan).fillna(0.0)
            weights = inv / inv.sum() if float(inv.sum()) > 0.0 else pd.Series(1.0 / len(peers), index=peers)
            fairs[product] = sub[peers].mul(weights, axis=1).sum(axis=1)
    elif mode == "group_regression_open500":
        for product in products:
            peers = [p for p in products if p != product]
            train = sub[[product] + peers].iloc[:500].dropna()
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


def group_z(prices: pd.DataFrame, wide_mid: pd.DataFrame, product: str, kind: str, day: int, window: int) -> pd.Series:
    group = PRODUCT_TO_GROUP[product]
    products = GROUPS[group]
    fair = group_fairs(wide_mid, products, kind, day)[product]
    mid = wide_mid.loc[day, product].reset_index(drop=True).astype(float)
    raw_dev = mid - fair.reset_index(drop=True).astype(float)
    min_periods = max(20, window // 5)
    mean = raw_dev.rolling(window, min_periods=min_periods).mean().shift(1)
    std = raw_dev.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
    z = (raw_dev - mean) / std.replace(0, np.nan)
    if kind == "group_regression_open500":
        z.iloc[:500] = np.nan
    return z


def simulate_candidate(prices: pd.DataFrame, wide_mid: pd.DataFrame, cand: dict) -> list[dict]:
    product = cand["product"]
    kind = cand["kind"]
    window = int(cand["window"])
    threshold = float(cand["threshold"])
    horizon = int(cand["horizon"])
    rows = []
    for day, sub in prices[prices["product"] == product].groupby("day", sort=True):
        sub = sub.sort_values("timestamp").reset_index(drop=True)
        if kind == "product_rolling":
            z = product_z(sub, window)
        else:
            z = group_z(prices, wide_mid, product, kind, int(day), window)
        position = 0
        entry_i = None
        entry_z = 0.0
        cash = 0.0
        trades = 0
        wins = 0
        round_trip_pnls = []
        entry_cash = 0.0
        for i, row in sub.iterrows():
            zi = float(z.iloc[i]) if i < len(z) and np.isfinite(z.iloc[i]) else float("nan")
            if position == 0:
                if not np.isfinite(zi) or abs(zi) < threshold:
                    continue
                side = 1 if zi <= -threshold else -1
                price, qty = active_fill(row, side, LIMIT)
                if qty <= 0:
                    continue
                position = qty if side > 0 else -qty
                cash -= price * position
                entry_cash = cash
                entry_i = i
                entry_z = zi
                trades += 1
            else:
                timed_out = entry_i is not None and i - entry_i >= horizon
                zero_cross = (position > 0 and zi >= 0.0) or (position < 0 and zi <= 0.0)
                if not timed_out and not zero_cross:
                    continue
                side = -1 if position > 0 else 1
                price, qty = active_fill(row, side, abs(position))
                if qty <= 0:
                    continue
                exit_qty = min(qty, abs(position))
                exit_pos = exit_qty if side > 0 else -exit_qty
                cash -= price * exit_pos
                position += exit_pos
                if position == 0:
                    pnl = cash - entry_cash
                    round_trip_pnls.append(pnl)
                    if pnl > 0:
                        wins += 1
                    entry_i = None
        if position != 0:
            row = sub.iloc[-1]
            side = -1 if position > 0 else 1
            price, qty = active_fill(row, side, abs(position))
            if qty > 0:
                exit_qty = min(qty, abs(position))
                exit_pos = exit_qty if side > 0 else -exit_qty
                cash -= price * exit_pos
                position += exit_pos
            if position != 0:
                cash += position * float(row["mid_price"])
                position = 0
            pnl = cash - entry_cash
            round_trip_pnls.append(pnl)
            if pnl > 0:
                wins += 1
        rows.append(
            {
                "product": product,
                "kind": kind,
                "window": window,
                "threshold": threshold,
                "horizon": horizon,
                "day": int(day),
                "pnl": float(cash),
                "trades": int(trades),
                "wins": int(wins),
                "win_pct": wins / trades if trades else float("nan"),
                "avg_round_trip_pnl": float(np.mean(round_trip_pnls)) if round_trip_pnls else float("nan"),
                "entry_z_abs": abs(entry_z) if entry_i is not None else float("nan"),
            }
        )
    return rows


def candidate_pool() -> pd.DataFrame:
    product = pd.read_csv(OUT_DIR / "mr_product_scan.csv")
    group = pd.read_csv(OUT_DIR / "mr_group_scan.csv")
    product = product[(product["signal_n"] >= 100) & (product["positive_days_active"] == 3)].copy()
    group = group[(group["signal_n"] >= 100) & (group["positive_days_active"] == 3)].copy()
    product["family"] = "product"
    group["family"] = "group"
    keep_cols = ["family", "group", "product", "kind", "window", "threshold", "horizon", "signal_n", "min_day_active_edge", "active_edge"]
    if "group" not in product.columns:
        product["group"] = product["product"].map(PRODUCT_TO_GROUP)
    pool = pd.concat([product[keep_cols], group[keep_cols]], ignore_index=True)
    pool = pool.sort_values(["min_day_active_edge", "active_edge", "signal_n"], ascending=[False, False, False])
    selected = []
    seen = set()
    for _, row in pool.iterrows():
        key = (row["family"], row["group"])
        count = sum(1 for item in selected if (item["family"], item["group"]) == key)
        if count >= TOP_N_PER_FAMILY:
            continue
        cand_key = (row["product"], row["kind"], int(row["window"]), float(row["threshold"]), int(row["horizon"]))
        if cand_key in seen:
            continue
        seen.add(cand_key)
        selected.append(row.to_dict())
        if len(selected) >= 160:
            break
    return pd.DataFrame(selected)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    wide_mid = prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()
    pool = candidate_pool()
    pool.to_csv(OUT_DIR / "mr_executable_candidate_pool.csv", index=False)
    day_rows = []
    for cand in pool.to_dict("records"):
        day_rows.extend(simulate_candidate(prices, wide_mid, cand))
    day = pd.DataFrame(day_rows)
    day.to_csv(OUT_DIR / "mr_executable_day.csv", index=False)
    summary_rows = []
    for keys, sub in day.groupby(["product", "kind", "window", "threshold", "horizon"], dropna=False):
        product, kind, window, threshold, horizon = keys
        summary_rows.append(
            {
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "kind": kind,
                "window": int(window),
                "threshold": float(threshold),
                "horizon": int(horizon),
                "total_pnl": float(sub["pnl"].sum()),
                "min_day_pnl": float(sub["pnl"].min()),
                "day2": float(sub[sub["day"] == 2]["pnl"].sum()),
                "day3": float(sub[sub["day"] == 3]["pnl"].sum()),
                "day4": float(sub[sub["day"] == 4]["pnl"].sum()),
                "trades": int(sub["trades"].sum()),
                "positive_days": int((sub["pnl"] > 0).sum()),
                "avg_win_pct": float(sub["win_pct"].dropna().mean()) if len(sub["win_pct"].dropna()) else float("nan"),
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values(["min_day_pnl", "total_pnl"], ascending=[False, False])
    summary.to_csv(OUT_DIR / "mr_executable_summary.csv", index=False)
    print("candidates", len(pool), "day_rows", len(day), "summary_rows", len(summary))
    print(summary.head(30).to_string(index=False))


if __name__ == "__main__":
    main()
