
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def analyze_mark67_behavior():
    print("Loading data...")
    trades = pd.concat([pd.read_csv(f, sep=";") for f in TRADES_FILES])
    trades['day'] = trades['timestamp'] # Placeholder to ensure we can join
    # Re-loading with day column correctly
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
    
    m67 = trades[trades['buyer'] == 'Mark 67'].copy()
    m67 = m67.sort_values(['day', 'timestamp'])
    
    print(f"Total Mark 67 trades: {len(m67)}")
    
    # 1. Periodicity Analysis
    print("\n1. Timing Periodicity Analysis:")
    m67['gap'] = m67.groupby('day')['timestamp'].diff()
    print("Gap statistics (timestamps):")
    print(m67['gap'].describe())
    
    common_gaps = m67['gap'].value_counts().head(10)
    print("\nMost common gaps:")
    print(common_gaps)
    
    # 2. Relationship with other traders
    # Who trades in the 1000 units BEFORE Mark 67?
    print("\n2. Pre-event Counterparty Analysis (Who trades before M67?):")
    pre_m67_activity = []
    for _, row in m67.iterrows():
        window = trades[(trades['day'] == row['day']) & 
                        (trades['timestamp'] < row['timestamp']) & 
                        (trades['timestamp'] >= row['timestamp'] - 500)]
        for _, w_row in window.iterrows():
            pre_m67_activity.append({
                'm67_ts': row['timestamp'],
                'pre_trader': w_row['buyer'] if w_row['buyer'] != 'Mark 67' else w_row['seller'],
                'pre_product': w_row['symbol'],
                'pre_side': 'buy' if w_row['buyer'] != 'Mark 67' else 'sell',
                'dt': row['timestamp'] - w_row['timestamp']
            })
    
    pre_df = pd.DataFrame(pre_m67_activity)
    if not pre_df.empty:
        counts = pre_df.groupby(['pre_trader', 'pre_product', 'pre_side']).size().sort_values(ascending=False).head(15)
        print("Top 15 activities in the 500 units leading to M67 trade:")
        print(counts)

    # 3. Price Context
    # Is he buying at a local dip or a local peak?
    print("\n3. Price Context Analysis:")
    vfe_prices = prices[prices['product'] == 'VELVETFRUIT_EXTRACT']
    
    price_relations = []
    for _, row in m67.iterrows():
        day_prices = vfe_prices[vfe_prices['day'] == row['day']]
        # Look back 1000 units
        lookback = day_prices[(day_prices['timestamp'] < row['timestamp']) & 
                              (day_prices['timestamp'] >= row['timestamp'] - 1000)]
        if not lookback.empty:
            mean_prev = lookback['mid_price'].mean()
            price_relations.append({
                'ts': row['timestamp'],
                'price': row['price'],
                'mid_at_trade': day_prices[day_prices['timestamp'] == row['timestamp']]['mid_price'].values[0] if not day_prices[day_prices['timestamp'] == row['timestamp']].empty else np.nan,
                'mean_1000': mean_prev,
                'rel_to_mean': row['price'] - mean_prev
            })
    
    pr_df = pd.DataFrame(price_relations)
    if not pr_df.empty:
        print("Price relative to 1000-unit trailing mean:")
        print(pr_df['rel_to_mean'].describe())

if __name__ == "__main__":
    analyze_mark67_behavior()
