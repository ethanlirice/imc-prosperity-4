import math
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5/stat-arb-v11")

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

def fit_basket(pivot_mids: pd.DataFrame, target: str, components: list[str]):
    frame = pivot_mids[[target] + components].dropna()
    if len(frame) < 50: return None
    y = frame[target].to_numpy(dtype=float)
    X_raw = frame[components].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(X_raw)), X_raw])
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = X @ coef
    resid = y - pred
    return {
        "alpha": float(coef[0]),
        "betas": [float(b) for b in coef[1:]],
        "resid": resid,
        "resid_sd": float(np.std(resid))
    }

def simulate_active_basket(pivot_mids, pivot_bids, pivot_asks, target, components, alpha, betas, resid, resid_sd, z_threshold=1.5):
    # Cross only the target leg. Assume components are "fairly priced" at their mids.
    pnl = 0.0
    pos = 0
    trades = 0
    entry_val = 0.0
    
    mids = pivot_mids[target].values
    bids = pivot_bids[target].values
    asks = pivot_asks[target].values
    
    # Components mids for fair value calculation
    comp_mids = [pivot_mids[c].values for c in components]
    
    for i in range(len(resid)):
        # Calculate fair value from current components mids
        fair = alpha
        for j, c_mid in enumerate(comp_mids):
            fair += betas[j] * c_mid[i]
        
        z = (mids[i] - fair) / resid_sd if resid_sd > 0 else 0
        
        if pos == 0:
            if z > z_threshold: # Target is overvalued -> Short target
                pos = -1
                entry_val = bids[i] # Sell at bid
                trades += 1
            elif z < -z_threshold: # Target is undervalued -> Long target
                pos = 1
                entry_val = asks[i] # Buy at ask
                trades += 1
        elif pos == 1:
            if mids[i] >= fair: # Exit long
                pnl += (bids[i] - entry_val) # Sell at bid
                pos = 0
        elif pos == -1:
            if mids[i] <= fair: # Exit short
                pnl += (entry_val - asks[i]) # Buy at ask
                pos = 0
    return pnl, trades

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    
    results = []
    for group, products in GROUPS.items():
        g_prices = prices[prices["product"].isin(products)]
        pivot_mids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        pivot_bids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="bid_price_1")
        pivot_asks = g_prices.pivot(index=["day", "timestamp"], columns="product", values="ask_price_1")
        
        # Drop rows with missing values to keep things simple
        valid_idx = pivot_mids.dropna().index
        pivot_mids = pivot_mids.loc[valid_idx]
        pivot_bids = pivot_bids.loc[valid_idx]
        pivot_asks = pivot_asks.loc[valid_idx]
        
        for target in products:
            components = [p for p in products if p != target]
            basket = fit_basket(pivot_mids, target, components)
            if not basket: continue
            
            # Global sim
            pnl, trades = simulate_active_basket(
                pivot_mids, pivot_bids, pivot_asks, target, components,
                basket["alpha"], basket["betas"], basket["resid"], basket["resid_sd"]
            )
            
            # Per day sim
            day_pnls = {}
            for day in [2, 3, 4]:
                d_mids = pivot_mids.xs(day, level="day")
                d_bids = pivot_bids.xs(day, level="day")
                d_asks = pivot_asks.xs(day, level="day")
                
                # Fit on global coefficients for consistency
                # (Ideally we'd fit on past days only, but let's see global first)
                d_resid = d_mids[target].values - (basket["alpha"] + np.dot(d_mids[components].values, basket["betas"]))
                dpnl, dtrades = simulate_active_basket(
                    d_mids, d_bids, d_asks, target, components,
                    basket["alpha"], basket["betas"], d_resid, basket["resid_sd"]
                )
                day_pnls[day] = dpnl
            
            results.append({
                "group": group, "target": target,
                "total_pnl": pnl, "trades": trades,
                "d2_pnl": day_pnls[2], "d3_pnl": day_pnls[3], "d4_pnl": day_pnls[4],
                "min_day_pnl": min(day_pnls.values()),
                "resid_sd": basket["resid_sd"]
            })
            
    df = pd.DataFrame(results).sort_values("total_pnl", ascending=False)
    df.to_csv(OUT_DIR / "active_basket_sim.csv", index=False)
    print(df.head(20).to_string(index=False))

if __name__ == "__main__":
    main()
