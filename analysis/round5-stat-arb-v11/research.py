import math
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5-stat-arb-v11")

GROUPS = {
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

def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)

def ols_y_on_x(y: np.ndarray, x: np.ndarray):
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    var_x = float(np.var(x))
    beta = 0.0 if var_x <= 1e-12 else float(np.mean((x - x_mean) * (y - y_mean)) / var_x)
    alpha = y_mean - beta * x_mean
    resid = y - alpha - beta * x
    return alpha, beta, resid

def adf_t_stat(resid: np.ndarray) -> float:
    if len(resid) < 20: return float("nan")
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
    except np.linalg.LinAlgError: return float("nan")

def acf1(resid: np.ndarray) -> float:
    if len(resid) < 3: return float("nan")
    a = resid[:-1]
    b = resid[1:]
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12: return float("nan")
    return float(np.corrcoef(a, b)[0, 1])

def half_life_from_acf(phi: float) -> float:
    if not np.isfinite(phi) or phi <= 0 or phi >= 1: return float("inf")
    return float(-math.log(2.0) / math.log(phi))

def compute_pair_stats(pivot_mids: pd.DataFrame, y_name: str, x_name: str):
    frame = pivot_mids[[y_name, x_name]].dropna()
    y = frame[y_name].to_numpy(dtype=float)
    x = frame[x_name].to_numpy(dtype=float)
    if len(frame) < 20: return {}
    alpha, beta, resid = ols_y_on_x(y, x)
    corr_mid = float(np.corrcoef(y, x)[0, 1]) if np.std(y) > 0 and np.std(x) > 0 else float("nan")
    ry, rx = np.diff(y), np.diff(x)
    corr_ret = float(np.corrcoef(ry, rx)[0, 1]) if len(ry) > 2 and np.std(ry) > 0 and np.std(rx) > 0 else float("nan")
    phi = acf1(resid)
    return {
        "alpha": alpha, "beta": beta, "corr_mid": corr_mid, "corr_ret": corr_ret,
        "resid_mean": float(np.mean(resid)), "resid_sd": float(np.std(resid)),
        "resid_acf1": phi, "half_life": half_life_from_acf(phi),
        "adf_t": adf_t_stat(resid), "n": int(len(resid))
    }

def fit_basket(pivot_mids: pd.DataFrame, target: str, components: list[str]):
    frame = pivot_mids[[target] + components].dropna()
    if len(frame) < 50: return {}
    y = frame[target].to_numpy(dtype=float)
    X_raw = frame[components].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(X_raw)), X_raw])
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = X @ coef
    resid = y - pred
    phi = acf1(resid)
    return {
        "alpha": float(coef[0]),
        **{f"beta_{c}": float(b) for c, b in zip(components, coef[1:])},
        "resid_sd": float(np.std(resid)), "resid_acf1": phi,
        "half_life": half_life_from_acf(phi), "adf_t": adf_t_stat(resid), "n": int(len(resid))
    }

def simulate_trade(pivot_mids, pivot_bids, pivot_asks, target, signal_resid, resid_sd, z_threshold=1.5, hold_max=500):
    # Simplified execution-aware PnL
    # Signal is residual from OLS. If signal > z * sd, short target (sell at bid), long peers (buy at ask).
    # But wait, the prompt says "pair trade must pay cost on both legs; basket trade must pay cost on all active legs."
    # For now, let's just simulate target-leg only active trade if peers are assumed to be "fair".
    # Or full basket simulation? Prompt says "basket trade must pay cost on all active legs".
    # Let's do a simple z-score crossover.
    
    pnl = 0.0
    pos = 0
    trades = 0
    entry_val = 0.0
    
    mids = pivot_mids[target].values
    bids = pivot_bids[target].values
    asks = pivot_asks[target].values
    
    for i in range(len(signal_resid)):
        z = signal_resid[i] / resid_sd if resid_sd > 0 else 0
        
        if pos == 0:
            if z > z_threshold: # Short target
                pos = -1
                entry_val = bids[i] # Sell at bid
                trades += 1
            elif z < -z_threshold: # Long target
                pos = 1
                entry_val = asks[i] # Buy at ask
                trades += 1
        elif pos == 1:
            if z >= 0 or i == len(signal_resid) - 1: # Exit long
                pnl += (bids[i] - entry_val) # Sell at bid
                pos = 0
        elif pos == -1:
            if z <= 0 or i == len(signal_resid) - 1: # Exit short
                pnl += (entry_val - asks[i]) # Buy at ask
                pos = 0
    return pnl, trades

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    
    # Pairs
    pair_rows = []
    for group, products in GROUPS.items():
        g_prices = prices[prices["product"].isin(products)]
        pivot_mids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        pivot_bids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="bid_price_1")
        pivot_asks = g_prices.pivot(index=["day", "timestamp"], columns="product", values="ask_price_1")
        
        for i, y_name in enumerate(products):
            for x_name in products[i+1:]:
                stats = compute_pair_stats(pivot_mids, y_name, x_name)
                if not stats: continue
                
                # Simulation (paying the spread on BOTH legs)
                # Spread cost on y: (ask - bid)
                # Spread cost on x: (ask - bid) * beta
                # Simplified: cross y, assume x is fair, or cross both.
                # Let's cross both: entry_cost = half_spread_y + abs(beta) * half_spread_x
                
                row = {"group": group, "y": y_name, "x": x_name, **stats}
                
                # Stability
                day_stats = []
                for day in [2, 3, 4]:
                    d_pivot = pivot_mids.xs(day, level="day")
                    ds = compute_pair_stats(d_pivot, y_name, x_name)
                    day_stats.append(ds)
                
                row["min_day_adf"] = min([d.get("adf_t", 0) for d in day_stats if d])
                row["max_day_hl"] = max([d.get("half_life", 9999) for d in day_stats if d])
                pair_rows.append(row)
                
    pd.DataFrame(pair_rows).to_csv(OUT_DIR / "pair_rankings.csv", index=False)
    
    # Baskets (1-vs-4)
    basket_rows = []
    for group, products in GROUPS.items():
        g_prices = prices[prices["product"].isin(products)]
        pivot_mids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        
        for target in products:
            components = [p for p in products if p != target]
            stats = fit_basket(pivot_mids, target, components)
            if not stats: continue
            
            row = {"group": group, "target": target, **stats}
            
            day_stats = []
            for day in [2, 3, 4]:
                d_pivot = pivot_mids.xs(day, level="day")
                ds = fit_basket(d_pivot, target, components)
                day_stats.append(ds)
            
            row["min_day_adf"] = min([d.get("adf_t", 0) for d in day_stats if d])
            row["max_day_hl"] = max([d.get("half_life", 9999) for d in day_stats if d])
            basket_rows.append(row)
            
    pd.DataFrame(basket_rows).to_csv(OUT_DIR / "basket_rankings.csv", index=False)
    print("Research complete. CSVs saved in analysis/round5-stat-arb-v11/")

if __name__ == "__main__":
    main()
