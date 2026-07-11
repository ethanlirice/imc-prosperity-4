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

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    
    group_sums = []
    for group, products in GROUPS.items():
        g_prices = prices[prices["product"].isin(products)]
        pivot = g_prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        pivot = pivot.dropna()
        if pivot.empty: continue
        
        group_sum = pivot[products].sum(axis=1)
        group_sums.append({
            "group": group,
            "mean_sum": group_sum.mean(),
            "std_sum": group_sum.std(),
            "min_sum": group_sum.min(),
            "max_sum": group_sum.max(),
            "cv_sum": group_sum.std() / group_sum.mean() if group_sum.mean() != 0 else 0
        })
        
    pd.DataFrame(group_sums).to_csv(OUT_DIR / "group_sums.csv", index=False)
    print(pd.DataFrame(group_sums).to_string(index=False))

if __name__ == "__main__":
    main()
