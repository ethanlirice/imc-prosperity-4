import math
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")
OUT_DIR = Path("analysis/round5/stat-arb-v11")

GROUPS = {
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
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
    return coef

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    
    results = []
    for group, products in GROUPS.items():
        g_prices = prices[prices["product"].isin(products)]
        pivot_mids = g_prices.pivot(index=["day", "timestamp"], columns="product", values="mid_price")
        
        for target in products:
            components = [p for p in products if p != target]
            
            day_coefs = {}
            for day in [2, 3, 4]:
                d_mids = pivot_mids.xs(day, level="day").dropna()
                coef = fit_basket(d_mids, target, components)
                if coef is not None:
                    day_coefs[day] = coef
            
            if len(day_coefs) < 3: continue
            
            # Compute variance of coefficients
            coef_matrix = np.array([day_coefs[d] for d in [2, 3, 4]])
            coef_std = np.std(coef_matrix, axis=0)
            coef_mean = np.mean(coef_matrix, axis=0)
            coef_cv = np.abs(coef_std / coef_mean)
            
            results.append({
                "group": group, "target": target,
                "intercept_cv": coef_cv[0],
                "beta_max_cv": np.max(coef_cv[1:]),
                "beta_mean_cv": np.mean(coef_cv[1:])
            })
            
    df = pd.DataFrame(results).sort_values("beta_mean_cv")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
