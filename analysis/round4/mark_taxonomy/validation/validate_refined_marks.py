
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def validate_refined_marks():
    print("Loading data...")
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
    
    # Pre-map prices for faster lookup
    price_map = {}
    for (day, prod), df in prices.groupby(['day', 'product']):
        price_map[(day, prod)] = df.sort_values('timestamp')

    def get_future_metrics(day, prod, ts, trade_px, direction, horizon=200):
        df = price_map.get((day, prod))
        if df is None: return None
        
        target_ts = ts + horizon
        idx = np.searchsorted(df['timestamp'].values, target_ts)
        if idx >= len(df): return None
        
        future_mid = df.iloc[idx]['mid_price']
        
        curr_row = df[df['timestamp'] == ts]
        if curr_row.empty: return None
        
        curr_mid = curr_row['mid_price'].values[0]
        curr_bid = curr_row['bid_price_1'].values[0]
        curr_ask = curr_row['ask_price_1'].values[0]
        
        return {
            'mid_move': direction * (future_mid - curr_mid),
            'trade_edge': direction * (future_mid - trade_px),
            'px_vs_mid': direction * (curr_mid - trade_px), # positive if bought below mid or sold above mid
            'is_at_touch': (trade_px >= curr_ask if direction == 1 else trade_px <= curr_bid)
        }

    # 1. Mark 22 by strike
    print("\nValidating Mark 22 Strike-Specific Edge...")
    m22_trades = trades[(trades['seller'] == 'Mark 22') & (trades['symbol'].str.startswith('VEV_'))].copy()
    m22_results = []
    for _, row in m22_trades.iterrows():
        metrics = get_future_metrics(row['day'], row['symbol'], row['timestamp'], row['price'], -1) # M22 is seller, we are buyer
        if metrics:
            metrics['strike'] = row['symbol']
            m22_results.append(metrics)
    
    m22_df = pd.DataFrame(m22_results)
    if not m22_df.empty:
        summary = m22_df.groupby('strike').agg({
            'mid_move': 'mean',
            'trade_edge': 'mean',
            'px_vs_mid': 'mean',
            'trade_edge': ['mean', 'count']
        })
        print(summary)

    # 2. Mark 14 Spread Capture Analysis
    print("\nValidating Mark 14 Spread Capture...")
    m14_trades = trades[(trades['buyer'] == 'Mark 14') | (trades['seller'] == 'Mark 14')].copy()
    m14_results = []
    for _, row in m14_trades.iterrows():
        direction = 1 if row['buyer'] == 'Mark 14' else -1
        metrics = get_future_metrics(row['day'], row['symbol'], row['timestamp'], row['price'], direction)
        if metrics:
            metrics['product'] = row['symbol']
            m14_results.append(metrics)
            
    m14_df = pd.DataFrame(m14_results)
    if not m14_df.empty:
        m14_summary = m14_df.groupby('product').agg({
            'mid_move': 'mean',
            'trade_edge': 'mean',
            'px_vs_mid': 'mean',
            'is_at_touch': 'mean'
        })
        print(m14_summary)

if __name__ == "__main__":
    validate_refined_marks()
