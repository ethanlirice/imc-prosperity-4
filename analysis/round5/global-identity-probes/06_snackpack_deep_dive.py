import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND5")
SNACKPACK = ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"]

def analyze_snackpack(day):
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    mids = df_prices[df_prices['product'].isin(SNACKPACK)].pivot(index='timestamp', columns='product', values='mid_price').dropna()
    
    # 1. Simple Sum
    simple_sum = mids.sum(axis=1)
    print(f"Simple Sum Std Dev (Day {day}): {simple_sum.std():.4f}")
    
    # 2. Regression 1-vs-Others
    target = "SNACKPACK_STRAWBERRY"
    others = [p for p in SNACKPACK if p != target]
    
    y = mids[target]
    X = mids[others]
    X = np.column_stack([np.ones(len(X)), X])
    
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ coef
    print(f"Regression Residual Std Dev (Day {day}): {resid.std():.4f}")
    
    # 3. Check for -1 Coefficients (Inverse products)
    print(f"Coefficients for {target}:")
    print(dict(zip(["Intercept"] + others, coef.round(4))))

if __name__ == "__main__":
    analyze_snackpack(2)
    analyze_snackpack(3)
    analyze_snackpack(4)
