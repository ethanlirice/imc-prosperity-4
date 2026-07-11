import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND5")
PEBBLES = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]

def analyze_pebbles(day):
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    mids = df_prices[df_prices['product'].isin(PEBBLES)].pivot(index='timestamp', columns='product', values='mid_price').dropna()
    
    print(f"Pebbles Individual Std Dev (Day {day}):")
    print(mids.std())
    
    # Calculate Synthetic Mid Error
    # Error_j = Mid_j - (50000 - Sum(Other_Mids))
    # This is exactly Sum(Mids) - 50000
    error = mids.sum(axis=1) - 50000
    
    print(f"\nTotal Sum Error Std Dev: {error.std():.4f}")
    
    # Check if any leg leads the error
    for leg in PEBBLES:
        corr = mids[leg].pct_change().corr(error.shift(1))
        print(f"Corr({leg} return, error lag 1): {corr:.4f}")

if __name__ == "__main__":
    analyze_pebbles(2)
    analyze_pebbles(3)
    analyze_pebbles(4)
