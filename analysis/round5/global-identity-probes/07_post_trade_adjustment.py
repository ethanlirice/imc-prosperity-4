import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND5")
BIG_40_GROUPS = ["GALAXY_SOUNDS", "SLEEP_POD", "ROBOT", "UV_VISOR", "TRANSLATOR", "PANEL", "OXYGEN_SHAKE", "SNACKPACK"]

def analyze_post_trade_adjustment(day):
    print(f"Analyzing Day {day}...")
    df_prices = pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=';')
    df_trades = pd.read_csv(DATA_DIR / f"trades_round_5_day_{day}.csv", sep=';')
    
    # 1. Big 40 trades
    # For simplicity, just one product
    product = "UV_VISOR_MAGENTA"
    p_trades = df_trades[df_trades['symbol'] == product]
    p_prices = df_prices[df_prices['product'] == product].set_index('timestamp')
    
    # Infer side
    p_trades = p_trades.merge(p_prices[['bid_price_1', 'ask_price_1', 'mid_price']], left_on='timestamp', right_index=True, how='left')
    p_trades['side'] = 0
    p_trades.loc[p_trades['price'] >= p_trades['ask_price_1'], 'side'] = 1
    p_trades.loc[p_trades['price'] <= p_trades['bid_price_1'], 'side'] = -1
    
    # Markouts
    res = []
    for lag in [0, 100, 200]: # 100 is next tick
        fwd_mid = p_prices['mid_price'].shift(-lag//100)
        p_trades[f'markout_{lag}'] = p_trades['side'] * (fwd_mid.loc[p_trades['timestamp']].values - p_trades['mid_price'])
        res.append({
            "lag": lag,
            "mean_markout": p_trades[f'markout_{lag}'].mean()
        })
        
    return pd.DataFrame(res)

if __name__ == "__main__":
    print(analyze_post_trade_adjustment(2))
    print(analyze_post_trade_adjustment(3))
    print(analyze_post_trade_adjustment(4))
