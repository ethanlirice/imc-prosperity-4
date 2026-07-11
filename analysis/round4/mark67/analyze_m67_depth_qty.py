
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def analyze_m67_depth_qty():
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list)
    m67 = trades[trades['buyer'] == 'Mark 67'].copy()
    
    prices_list = []
    for f in PRICES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        prices_list.append(df)
    prices = pd.concat(prices_list)
    vfe = prices[prices['product'] == 'VELVETFRUIT_EXTRACT']
    
    print("Mark 67 Quantity Distribution:")
    print(m67['quantity'].value_counts().sort_index())
    
    # Merge with prices to get book state
    m67_book = pd.merge(m67, vfe, left_on=['day', 'timestamp'], right_on=['day', 'timestamp'])
    
    print("\nBook State at Mark 67 Trade:")
    print("Mean Ask Volume 1:", m67_book['ask_volume_1'].abs().mean())
    print("Mean Bid Volume 1:", m67_book['bid_volume_1'].mean())
    print("Mean Spread:", (m67_book['ask_price_1'] - m67_book['bid_price_1']).mean())
    
    # Compare with ALL sharp drops
    vfe['mid_diff'] = vfe.groupby('day')['mid_price'].diff()
    sharp_drops = vfe[vfe['mid_diff'] <= -1.5].copy()
    
    print("\nBook State at ALL Sharp Drops (diff <= -1.5):")
    print("Mean Ask Volume 1:", sharp_drops['ask_volume_1'].abs().mean())
    print("Mean Bid Volume 1:", sharp_drops['bid_volume_1'].mean())
    print("Mean Spread:", (sharp_drops['ask_price_1'] - sharp_drops['bid_price_1']).mean())

if __name__ == "__main__":
    analyze_m67_depth_qty()
