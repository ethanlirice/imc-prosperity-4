import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
from statsmodels.tsa.stattools import adfuller

DATA_DIR = Path("data/ROUND5")

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

def analyze_pca(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    
    indices = {}
    for name, products in GROUPS.items():
        mids = df_prices[df_prices['product'].isin(products)].pivot(index='timestamp', columns='product', values='mid_price')
        indices[name] = mids.mean(axis=1)
    
    df_indices = pd.DataFrame(indices).dropna()
    returns = df_indices.pct_change().dropna()
    
    # PCA
    pca = PCA()
    pca.fit(returns)
    explained_variance = pca.explained_variance_ratio_
    
    # Check for stationary linear combinations (Cointegration proxy)
    # We look for the last principal component (least variance)
    last_pc = pca.components_[-1]
    stationary_series = (returns * last_pc).sum(axis=1)
    adf_res = adfuller(stationary_series)
    
    return explained_variance, last_pc, adf_res[0], adf_res[1]

if __name__ == "__main__":
    days = [2, 3, 4]
    all_variance = []
    all_adf_stat = []
    all_p_val = []
    
    for d in days:
        v, pc, adf, p = analyze_pca(d)
        all_variance.append(v)
        all_adf_stat.append(adf)
        all_p_val.append(p)
        if d == 2:
            print(f"Last PC weights (Day 2): {dict(zip(GROUPS.keys(), pc.round(4)))}")

    print("\nExplained Variance Ratio (Average):")
    avg_variance = np.mean(all_variance, axis=0)
    for i, v in enumerate(avg_variance):
        print(f"PC{i+1}: {v:.4f}")
        
    print(f"\nAverage ADF Statistic: {np.mean(all_adf_stat):.4f}")
    print(f"Average P-value: {np.mean(all_p_val):.4f}")
