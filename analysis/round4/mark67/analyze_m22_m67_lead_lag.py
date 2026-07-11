
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def analyze_m22_m67_lead_lag():
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list).sort_values(['day', 'timestamp']).reset_index(drop=True)
    
    m22_options = trades[(trades['seller'] == 'Mark 22') & (trades['symbol'].str.startswith('VEV_'))].copy()
    m67_trades = trades[trades['buyer'] == 'Mark 67'].copy()
    
    # Identify M22 baskets (trades at the same timestamp and day)
    baskets = m22_options.groupby(['day', 'timestamp']).size().reset_index(name='basket_size')
    
    print(f"Total M22 option baskets: {len(baskets)}")
    
    # For each basket, find the NEXT M67 trade
    lead_times = []
    for _, b in baskets.iterrows():
        next_m67 = m67_trades[(m67_trades['day'] == b['day']) & (m67_trades['timestamp'] >= b['timestamp'])].head(1)
        if not next_m67.empty:
            lead_times.append({
                'basket_ts': b['timestamp'],
                'm67_ts': next_m67.iloc[0]['timestamp'],
                'dt': next_m67.iloc[0]['timestamp'] - b['timestamp'],
                'basket_size': b['basket_size']
            })
            
    lead_df = pd.DataFrame(lead_times)
    print("\nTime from M22 Basket to NEXT M67 Trade:")
    print(lead_df['dt'].describe())
    
    print("\nTop lead times (dt):")
    print(lead_df['dt'].value_counts().head(15))
    
    # Conversely, for each M67 trade, find the PREVIOUS M22 basket
    pre_baskets = []
    for _, m in m67_trades.iterrows():
        prev_b = baskets[(baskets['day'] == m['day']) & (baskets['timestamp'] <= m['timestamp'])].tail(1)
        if not prev_b.empty:
            pre_baskets.append({
                'm67_ts': m['timestamp'],
                'basket_ts': prev_b.iloc[0]['timestamp'],
                'dt': m['timestamp'] - prev_b.iloc[0]['timestamp'],
                'basket_size': prev_b.iloc[0]['basket_size']
            })
            
    pre_df = pd.DataFrame(pre_baskets)
    print("\nTime from PREVIOUS M22 Basket to M67 Trade:")
    print(pre_df['dt'].describe())
    
    print("\nTop lag times (dt):")
    print(pre_df['dt'].value_counts().head(15))

if __name__ == "__main__":
    analyze_m22_m67_lead_lag()
