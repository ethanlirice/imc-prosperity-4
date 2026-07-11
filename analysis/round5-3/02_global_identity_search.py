import pandas as pd
import numpy as np
from pathlib import Path

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

def analyze_identities(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    
    # Pivot all products
    mids = df_prices.pivot(index='timestamp', columns='product', values='mid_price').dropna()
    
    # 1. Group Sums
    group_sums = {}
    for name, products in GROUPS.items():
        group_sums[name] = mids[products].sum(axis=1)
    
    df_sums = pd.DataFrame(group_sums)
    
    print("\nGroup Sum Stability (Std Dev):")
    print(df_sums.std())
    
    print("\nGroup Sum Mean:")
    print(df_sums.mean())
    
    # 2. Cross-Group Sums
    # Is there a relationship between different groups?
    # e.g., Group A + Group B = Constant?
    # We check correlations of group sums
    print("\nGroup Sum Correlation Matrix:")
    print(df_sums.corr())

    # 3. Global Sum
    global_sum = mids.sum(axis=1)
    print(f"\nGlobal Sum (All 50) Mean: {global_sum.mean():.4f}, Std: {global_sum.std():.4f}")

if __name__ == "__main__":
    analyze_identities(2)
