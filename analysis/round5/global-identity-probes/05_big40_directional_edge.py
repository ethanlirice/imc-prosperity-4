import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND5")

GROUPS = {
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
}

BIG_40_GROUPS = [
    "GALAXY_SOUNDS", "SLEEP_POD", "ROBOT", "UV_VISOR", "TRANSLATOR", "PANEL", "OXYGEN_SHAKE", "SNACKPACK"
]

def analyze_directional_edge(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    df_trades = pd.read_csv(DATA_DIR / f"trades_round_5_day_{day}.csv", sep=';')
    
    # 1. Inferred Trade Direction
    # Join trades with prices to get side
    prices_subset = df_prices[['timestamp', 'product', 'bid_price_1', 'ask_price_1', 'mid_price']]
    df_trades = df_trades.merge(prices_subset.rename(columns={'product': 'symbol'}), on=['timestamp', 'symbol'], how='left')
    
    # Infer side: 1 for Buy (at Ask), -1 for Sell (at Bid)
    df_trades['side'] = 0
    df_trades.loc[df_trades['price'] >= df_trades['ask_price_1'], 'side'] = 1
    df_trades.loc[df_trades['price'] <= df_trades['bid_price_1'], 'side'] = -1
    
    # 2. Big 40 Net Flow
    big_40_symbols = [p for g in BIG_40_GROUPS for p in GROUPS.get(g, []) if g in BIG_40_GROUPS]
    # Wait, GROUPS only had PANEL and PEBBLES in this script. Let's fix that.
    
    return df_trades

# Redefining GROUPS properly
FULL_GROUPS = {
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

def analyze_day(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    df_trades = pd.read_csv(DATA_DIR / f"trades_round_5_day_{day}.csv", sep=';')
    
    # 1. Inferred Trade Direction
    prices_subset = df_prices[['timestamp', 'product', 'bid_price_1', 'ask_price_1', 'mid_price']]
    df_trades = df_trades.merge(prices_subset.rename(columns={'product': 'symbol'}), on=['timestamp', 'symbol'], how='left')
    
    df_trades['side'] = 0
    df_trades.loc[df_trades['price'] >= df_trades['ask_price_1'], 'side'] = 1
    df_trades.loc[df_trades['price'] <= df_trades['bid_price_1'], 'side'] = -1
    
    # 2. Net Flow per timestamp (Big 40)
    big_40_symbols = [p for g in BIG_40_GROUPS for p in FULL_GROUPS[g]]
    flow = df_trades[df_trades['symbol'].isin(big_40_symbols)].groupby('timestamp')['side'].sum()
    
    # 3. Correlation with future returns of ALL groups
    indices = {}
    for name, products in FULL_GROUPS.items():
        mids = df_prices[df_prices['product'].isin(products)].pivot(index='timestamp', columns='product', values='mid_price')
        indices[name] = mids.mean(axis=1)
    
    df_indices = pd.DataFrame(indices)
    
    results = []
    for g in FULL_GROUPS.keys():
        for l in [100, 200, 500]:
            fwd_ret = (df_indices[g].shift(-l//100) / df_indices[g]) - 1
            # Filter for timestamps with significant flow
            heavy_flow = flow[flow.abs() >= 10]
            common_idx = heavy_flow.index.intersection(fwd_ret.dropna().index)
            
            if len(common_idx) == 0: continue
            
            pnl = heavy_flow.loc[common_idx] * fwd_ret.loc[common_idx]
            results.append({
                "group": g,
                "lag": l,
                "mean_pnl": pnl.mean(),
                "hit_rate": (pnl > 0).mean()
            })
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    res2 = analyze_day(2)
    res3 = analyze_day(3)
    res4 = analyze_day(4)
    
    final = pd.concat([res2, res3, res4]).groupby(['group', 'lag']).mean()
    print("\nDirectional Edge of Big 40 Trades (PnL per unit of flow):")
    print(final.sort_values('mean_pnl', ascending=False).head(20))
