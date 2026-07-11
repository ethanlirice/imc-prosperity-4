
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def validate_m01():
    print("Loading data for Mark 01 analysis...")
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
    
    m01_trades = trades[(trades['buyer'] == 'Mark 01') | (trades['seller'] == 'Mark 01')]
    
    price_map = {}
    for (day, prod), df in prices.groupby(['day', 'product']):
        price_map[(day, prod)] = df.sort_values('timestamp')

    results = []
    for _, row in m01_trades.iterrows():
        df = price_map.get((row['day'], row['symbol']))
        if df is None: continue
        
        target_ts = row['timestamp'] + 200
        idx = np.searchsorted(df['timestamp'].values, target_ts)
        if idx >= len(df): continue
        
        future_mid = df.iloc[idx]['mid_price']
        curr_row = df[df['timestamp'] == row['timestamp']]
        if curr_row.empty: continue
        curr_mid = curr_row['mid_price'].values[0]
        
        direction = 1 if row['buyer'] == 'Mark 01' else -1
        results.append({
            'product': row['symbol'],
            'mid_move': direction * (future_mid - curr_mid),
            'trade_edge': direction * (future_mid - row['price']),
            'px_vs_mid': direction * (curr_mid - row['price'])
        })

    m01_df = pd.DataFrame(results)
    if not m01_df.empty:
        summary = m01_df.groupby('product').agg({
            'mid_move': 'mean',
            'trade_edge': 'mean',
            'px_vs_mid': 'mean',
            'trade_edge': ['mean', 'count']
        })
        print("\nMark 01 Performance Summary (Horizon 200):")
        print(summary)

if __name__ == "__main__":
    validate_m01()
