
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

HORIZONS = [100, 200, 500, 1000, 2000, 5000]

def validate_m22_recovery():
    print("Loading data for Mark 22 recovery analysis...")
    trades_list = []
    for f in TRADES_FILES:
        try:
            df = pd.read_csv(f, sep=";")
            df['day'] = int(f.stem.split("_")[-1])
            trades_list.append(df)
        except: pass
    trades = pd.concat(trades_list)
    
    prices_list = []
    for f in PRICES_FILES:
        try:
            df = pd.read_csv(f, sep=";")
            df['day'] = int(f.stem.split("_")[-1])
            prices_list.append(df)
        except: pass
    prices = pd.concat(prices_list)
    
    m22_sells = trades[(trades['seller'] == 'Mark 22') & (trades['symbol'].str.startswith('VEV_'))]
    
    price_map = {}
    for (day, prod), df in prices.groupby(['day', 'product']):
        price_map[(day, prod)] = df.sort_values('timestamp')

    results = []
    for horizon in HORIZONS:
        moves = []
        for _, row in m22_sells.iterrows():
            day_df = price_map.get((row['day'], row['symbol']))
            if day_df is None: continue
            
            target_ts = row['timestamp'] + horizon
            idx = np.searchsorted(day_df['timestamp'].values, target_ts)
            if idx >= len(day_df): continue
            
            future_mid = day_df.iloc[idx]['mid_price']
            curr_mid_vals = day_df[day_df['timestamp'] == row['timestamp']]['mid_price'].values
            if len(curr_mid_vals) == 0: continue
            
            # We want to see if mid moves UP after Mark 22 sells
            moves.append(future_mid - curr_mid_vals[0])
        
        if moves:
            results.append({
                'horizon': horizon,
                'mean_move': np.mean(moves),
                'pos_ratio': np.mean(np.array(moves) > 0),
                'flat_ratio': np.mean(np.array(moves) == 0)
            })

    df_results = pd.DataFrame(results)
    print("\nMark 22 Option Sell Recovery Analysis (Future Mid - Event Mid):")
    print(df_results)

if __name__ == "__main__":
    validate_m22_recovery()
