
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

HORIZONS = [100, 200, 500, 1000, 2000, 5000]

def validate_signal_decay():
    print("Loading data for signal decay analysis...")
    trades_list = []
    for f in TRADES_FILES:
        print(f"Reading {f}...")
        try:
            df = pd.read_csv(f, sep=";")
            df['day'] = int(f.stem.split("_")[-1])
            trades_list.append(df)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
    trades = pd.concat(trades_list)
    
    prices_list = []
    for f in PRICES_FILES:
        try:
            df = pd.read_csv(f, sep=";")
            df['day'] = int(f.stem.split("_")[-1])
            prices_list.append(df)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
    prices = pd.concat(prices_list)
    
    # Focus on VFE
    vfe_trades = trades[trades['symbol'] == 'VELVETFRUIT_EXTRACT']
    vfe_prices = prices[prices['product'] == 'VELVETFRUIT_EXTRACT'].sort_values(['day', 'timestamp'])
    
    price_map = {day: df for day, df in vfe_prices.groupby('day')}

    results = []
    for trader in ['Mark 67', 'Mark 49']:
        trader_trades = vfe_trades[(vfe_trades['buyer'] == trader) | (vfe_trades['seller'] == trader)]
        
        for horizon in HORIZONS:
            moves = []
            for _, row in trader_trades.iterrows():
                day_df = price_map.get(row['day'])
                if day_df is None: continue
                
                target_ts = row['timestamp'] + horizon
                idx = np.searchsorted(day_df['timestamp'].values, target_ts)
                if idx >= len(day_df): continue
                
                future_mid = day_df.iloc[idx]['mid_price']
                curr_mid_vals = day_df[day_df['timestamp'] == row['timestamp']]['mid_price'].values
                if len(curr_mid_vals) == 0: continue
                
                side = 1 if row['buyer'] == trader else -1
                moves.append(side * (future_mid - curr_mid_vals[0]))
            
            if moves:
                results.append({
                    'trader': trader,
                    'horizon': horizon,
                    'mean_move': np.mean(moves),
                    'std_move': np.std(moves),
                    'pos_ratio': np.mean(np.array(moves) > 0)
                })

    df_results = pd.DataFrame(results)
    print("\nSignal Decay Analysis (Mean Signed Mid Move):")
    pivot = df_results.pivot(index='horizon', columns='trader', values='mean_move')
    print(pivot)
    
    print("\nPositive Ratio (Consistency):")
    pivot_pos = df_results.pivot(index='horizon', columns='trader', values='pos_ratio')
    print(pivot_pos)

if __name__ == "__main__":
    validate_signal_decay()
