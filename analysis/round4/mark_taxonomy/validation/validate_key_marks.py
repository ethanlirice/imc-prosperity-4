
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def validate_directional_marks():
    print("Validating Mark 67 and Mark 49 directional follow-through...")
    
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list)
    
    prices_list = []
    for f in PRICES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        prices_list.append(df)
    prices = pd.concat(prices_list)
    
    # Focus on VFE
    vfe_prices = prices[prices['product'] == 'VELVETFRUIT_EXTRACT'].copy()
    vfe_prices = vfe_prices.sort_values(['day', 'timestamp'])
    
    def get_mid_move(day, ts, horizon):
        day_prices = vfe_prices[vfe_prices['day'] == day]
        target_ts = ts + horizon
        # Find first price at or after target_ts
        idx = np.searchsorted(day_prices['timestamp'].values, target_ts)
        if idx < len(day_prices):
            future_mid = day_prices.iloc[idx]['mid_price']
            current_mid = day_prices[day_prices['timestamp'] == ts]['mid_price'].values
            if len(current_mid) > 0:
                return future_mid - current_mid[0]
        return np.nan

    results = []
    for trader in ['Mark 67', 'Mark 49']:
        trader_trades = trades[(trades['buyer'] == trader) | (trades['seller'] == trader)].copy()
        trader_trades = trader_trades[trader_trades['symbol'] == 'VELVETFRUIT_EXTRACT']
        
        moves = []
        for _, row in trader_trades.iterrows():
            side = 1 if row['buyer'] == trader else -1
            move = get_mid_move(row['day'], row['timestamp'], 200)
            if not np.isnan(move):
                moves.append(side * move)
        
        if moves:
            results.append({
                'trader': trader,
                'n': len(moves),
                'mean': np.mean(moves),
                'median': np.median(moves),
                'std': np.std(moves),
                'min': np.min(moves),
                'max': np.max(moves),
                'pos_ratio': np.mean(np.array(moves) > 0)
            })
            
    res_df = pd.DataFrame(results)
    print("\nDirectional Validation (Horizon 200):")
    print(res_df)
    
    # Check Mark 22
    print("\nValidating Mark 22 Option Pressure...")
    m22_trades = trades[(trades['seller'] == 'Mark 22') & (trades['symbol'].str.startswith('VEV_'))].copy()
    m22_moves = []
    for _, row in m22_trades.iterrows():
        # When M22 sells, we want to see if mid moves UP (recovery from pressure)
        # Side is -1 (M22 is seller), so mid_move * -1 = future_mid - current_mid
        
        day_prices = prices[(prices['day'] == row['day']) & (prices['product'] == row['symbol'])]
        target_ts = row['timestamp'] + 200
        idx = np.searchsorted(day_prices['timestamp'].values, target_ts)
        if idx < len(day_prices):
            future_mid = day_prices.iloc[idx]['mid_price']
            current_mid_val = day_prices[day_prices['timestamp'] == row['timestamp']]['mid_price'].values
            if len(current_mid_val) > 0:
                m22_moves.append(future_mid - current_mid_val[0])
                
    if m22_moves:
        print(f"Mark 22 Option Sell Markouts (n={len(m22_moves)}):")
        print(f"Mean: {np.mean(m22_moves):.4f}")
        print(f"Median: {np.median(m22_moves):.4f}")
        print(f"Positive Ratio (Mid Up): {np.mean(np.array(m22_moves) > 0):.4f}")

if __name__ == "__main__":
    validate_directional_marks()
