import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5/tls-pair-spreads")
OUT_SUMMARY = OUT_DIR / "rolling_tls_target_summary.csv"
OUT_DAY = OUT_DIR / "rolling_tls_target_day.csv"

ALL_GROUPS = {
    "GALAXY_SOUNDS": ["GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_SOLAR_FLAMES"],
    "SLEEP_POD": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UV_VISOR": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    "TRANSLATOR": ["TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN_SHAKE": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"],
    "SNACKPACK": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"],
}
GROUPS = {name: ALL_GROUPS[name] for name in ["SNACKPACK", "MICROCHIP", "ROBOT", "SLEEP_POD", "GALAXY_SOUNDS"]}

WINDOWS = [500, 1000, 2000]
ENTRY_ZS = [2.5, 3.0]
EXIT_Z = 0.25
HOLD = 500
LIMIT = 10


def read_prices():
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    raw = pd.concat(frames, ignore_index=True)
    keep = ["day", "timestamp", "product", "bid_price_1", "ask_price_1", "mid_price"]
    return raw[keep].rename(columns={"bid_price_1": "bid", "ask_price_1": "ask", "mid_price": "mid"})


def tls_beta(x, y):
    xc = x - x.mean()
    yc = y - y.mean()
    sxx = float(np.dot(xc, xc) / len(xc))
    syy = float(np.dot(yc, yc) / len(yc))
    sxy = float(np.dot(xc, yc) / len(xc))
    if abs(sxy) < 1e-9:
        return float("nan")
    root = math.sqrt((syy - sxx) * (syy - sxx) + 4.0 * sxy * sxy)
    return float((syy - sxx + root) / (2.0 * sxy))


def ols_beta(x, y):
    xc = x - x.mean()
    yc = y - y.mean()
    denom = float(np.dot(xc, xc))
    if denom < 1e-9:
        return float("nan")
    return float(np.dot(xc, yc) / denom)


def simulate(day_frame, target, anchor, window, entry_z, method):
    y = day_frame[target].to_numpy(dtype=float)
    x = day_frame[anchor].to_numpy(dtype=float)
    bid = day_frame[target + "_bid"].to_numpy(dtype=float)
    ask = day_frame[target + "_ask"].to_numpy(dtype=float)
    n = float(window)
    sx = np.r_[0.0, np.cumsum(x)]
    sy = np.r_[0.0, np.cumsum(y)]
    sx2 = np.r_[0.0, np.cumsum(x * x)]
    sy2 = np.r_[0.0, np.cumsum(y * y)]
    sxy = np.r_[0.0, np.cumsum(x * y)]
    pos = 0
    cash = 0.0
    entry_i = 0
    trades = 0
    for i in range(window, len(y)):
        sum_x = sx[i] - sx[i - window]
        sum_y = sy[i] - sy[i - window]
        mean_x = sum_x / n
        mean_y = sum_y / n
        var_x = (sx2[i] - sx2[i - window]) / n - mean_x * mean_x
        var_y = (sy2[i] - sy2[i - window]) / n - mean_y * mean_y
        cov_xy = (sxy[i] - sxy[i - window]) / n - mean_x * mean_y
        if method == "tls":
            if abs(cov_xy) < 1e-9:
                continue
            root = math.sqrt((var_y - var_x) * (var_y - var_x) + 4.0 * cov_xy * cov_xy)
            beta = (var_y - var_x + root) / (2.0 * cov_xy)
        else:
            if var_x < 1e-9:
                continue
            beta = cov_xy / var_x
        if not np.isfinite(beta):
            continue
        alpha = mean_y - beta * mean_x
        # E[(y-a-bx)^2] over the rolling window.
        sigma2 = var_y + beta * beta * var_x - 2.0 * beta * cov_xy
        sigma = math.sqrt(max(0.0, sigma2))
        if sigma <= 1e-9:
            continue
        fair = alpha + beta * x[i]
        resid = y[i] - fair
        z = resid / sigma
        if pos == 0:
            if z <= -entry_z and np.isfinite(ask[i]):
                qty = LIMIT
                cash -= ask[i] * qty
                pos += qty
                entry_i = i
                trades += 1
            elif z >= entry_z and np.isfinite(bid[i]):
                qty = LIMIT
                cash += bid[i] * qty
                pos -= qty
                entry_i = i
                trades += 1
        else:
            zero_cross = (pos > 0 and z >= -EXIT_Z) or (pos < 0 and z <= EXIT_Z)
            timed_out = i - entry_i >= HOLD
            if zero_cross or timed_out:
                if pos > 0 and np.isfinite(bid[i]):
                    cash += bid[i] * pos
                    pos = 0
                elif pos < 0 and np.isfinite(ask[i]):
                    cash -= ask[i] * abs(pos)
                    pos = 0
    if pos > 0:
        cash += y[-1] * pos
    elif pos < 0:
        cash -= y[-1] * abs(pos)
    return float(cash), int(trades)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = read_prices()
    day_rows = []
    summary_rows = []
    for group, products in GROUPS.items():
        sub = raw[raw["product"].isin(products)].copy()
        wide_mid = sub.pivot(index=["day", "timestamp"], columns="product", values="mid")
        wide_bid = sub.pivot(index=["day", "timestamp"], columns="product", values="bid").add_suffix("_bid")
        wide_ask = sub.pivot(index=["day", "timestamp"], columns="product", values="ask").add_suffix("_ask")
        wide = wide_mid.join(wide_bid).join(wide_ask).dropna(how="any").reset_index()
        for target in products:
            for anchor in products:
                if target == anchor:
                    continue
                for window in WINDOWS:
                    for entry_z in ENTRY_ZS:
                        for method in ["ols", "tls"]:
                            case = "%s__%s__%s__w%s__z%s" % (method, target, anchor, window, entry_z)
                            total = 0.0
                            total_trades = 0
                            p_by_day = {}
                            for day in sorted(wide["day"].unique()):
                                frame = wide[wide["day"] == day].sort_values("timestamp")
                                pnl, trades = simulate(frame, target, anchor, window, entry_z, method)
                                p_by_day[int(day)] = pnl
                                total += pnl
                                total_trades += trades
                                day_rows.append({"case": case, "group": group, "method": method, "target": target, "anchor": anchor, "window": window, "entry_z": entry_z, "day": int(day), "pnl": round(pnl, 2), "trades": trades})
                            vals = [p_by_day.get(2, 0.0), p_by_day.get(3, 0.0), p_by_day.get(4, 0.0)]
                            summary_rows.append({
                                "case": case,
                                "group": group,
                                "method": method,
                                "target": target,
                                "anchor": anchor,
                                "window": window,
                                "entry_z": entry_z,
                                "total": round(total, 2),
                                "day2": round(vals[0], 2),
                                "day3": round(vals[1], 2),
                                "day4": round(vals[2], 2),
                                "worst_day": round(min(vals), 2),
                                "positive_days": sum(1 for v in vals if v > 0),
                                "trades": total_trades,
                            })
    summary_rows.sort(key=lambda r: (r["positive_days"], r["worst_day"], r["total"]), reverse=True)
    with open(OUT_SUMMARY, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    with open(OUT_DAY, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(day_rows[0].keys()))
        writer.writeheader()
        writer.writerows(day_rows)
    for row in summary_rows[:30]:
        print(row)


if __name__ == "__main__":
    main()
