import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND5")
PEBBLES = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]

def simulate_quoting(day):
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    mids = df_prices[df_prices['product'].isin(PEBBLES)].pivot(index='timestamp', columns='product', values='mid_price').dropna()
    
    # Global identity sum
    total_sum = mids.sum(axis=1)
    error = total_sum - 50000
    
    # We want to know: if we trade based on error, what is the markout?
    # Horizon: 1, 5, 10 ticks
    results = []
    for horizon in [1, 5, 10]:
        for product in PEBBLES:
            fwd_ret = mids[product].shift(-horizon) - mids[product]
            # If error > 0, we expect price to fall (sell)
            # If error < 0, we expect price to rise (buy)
            pnl = -np.sign(error) * fwd_ret
            
            results.append({
                "product": product,
                "horizon": horizon,
                "mean_pnl": pnl.mean(),
                "hit_rate": (pnl > 0).mean()
            })
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    res2 = simulate_quoting(2)
    res3 = simulate_quoting(3)
    res4 = simulate_quoting(4)
    
    final = pd.concat([res2, res3, res4]).groupby(['product', 'horizon']).mean()
    print("Markout PnL per trade (ignoring spread):")
    print(final.sort_values('mean_pnl', ascending=False))
