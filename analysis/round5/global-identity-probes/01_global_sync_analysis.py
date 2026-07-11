import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data/ROUND5")

GROUPS = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_SOLAR_FLAMES"
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"
    ],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": [
        "ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"
    ],
    "UV_VISOR": [
        "UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"
    ],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"
    ],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"
    ],
}

BIG_40_GROUPS = [
    "GALAXY_SOUNDS", "SLEEP_POD", "ROBOT", "UV_VISOR", "TRANSLATOR", "PANEL", "OXYGEN_SHAKE", "SNACKPACK"
]

def analyze_sync(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    df_trades = pd.read_csv(DATA_DIR / f"trades_round_5_day_{day}.csv", sep=';')
    
    # 1. Group Mid Indices
    indices = {}
    for name, products in GROUPS.items():
        mids = df_prices[df_prices['product'].isin(products)].pivot(index='timestamp', columns='product', values='mid_price')
        indices[name] = mids.mean(axis=1)
    
    df_indices = pd.DataFrame(indices)
    returns = df_indices.pct_change().dropna()
    
    # 2. Lead-Lag Matrix
    lags = [100, 200, 500]
    res = []
    for lag in lags:
        # returns is pct_change, we need to shift by number of rows if index is regular
        # or use shift(lag) if lag is index-based. returns index is 100-spaced.
        shift_rows = lag // 100
        corr = returns.corrwith(returns.shift(shift_rows))
        for g, c in corr.items():
            res.append({"group": g, "lag": lag, "corr": c})
    
    # 3. Big 40 Impact
    trade_counts = df_trades.groupby(['timestamp']).size()
    
    # Large trade events (top 5% by volume/count)
    event_times = trade_counts[trade_counts >= trade_counts.quantile(0.95)].index
    
    # Measure index returns post-event
    impacts = []
    for g in GROUPS.keys():
        for l in [100, 200, 500]:
            # Forward return from event time
            common_times = df_indices.index.intersection(event_times)
            if len(common_times) == 0: continue
            
            # Use reindex to safely get future prices
            future_times = common_times + l
            current_prices = df_indices.loc[common_times, g].values
            future_prices = df_indices[g].reindex(future_times).values
            
            fwd_ret = (future_prices / current_prices) - 1
            impacts.append({
                "group": g,
                "lag": l,
                "mean_impact": np.nanmean(fwd_ret),
                "hit_rate": np.nanmean(fwd_ret > 0)
            })
            
    return pd.DataFrame(res), pd.DataFrame(impacts)

if __name__ == "__main__":
    days = [2, 3, 4]
    # Inspect spacing
    df_sample = pd.read_csv(DATA_DIR / f"prices_round_5_day_2.csv", sep=';')
    print(f"Timestamp spacing sample: {df_sample['timestamp'].unique()[:5]}")
    all_res = []
    all_impacts = []
    for d in days:
        r, i = analyze_sync(d)
        all_res.append(r)
        all_impacts.append(i)
        
    final_res = pd.concat(all_res).groupby(['group', 'lag']).mean()
    final_impacts = pd.concat(all_impacts).groupby(['group', 'lag']).mean()
    
    print("\nIntra-Index Lead-Lag (Auto-correlation):")
    print(final_res.sort_values('corr', ascending=False).head(20))
    
    print("\nBig 40 Event Impact on Indices:")
    print(final_impacts.sort_values('mean_impact', key=abs, ascending=False).head(20))
