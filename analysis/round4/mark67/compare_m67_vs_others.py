
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def compare_m67_vs_others():
    prices_list = []
    for f in PRICES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        prices_list.append(df)
    prices = pd.concat(prices_list)
    vfe = prices[prices['product'] == 'VELVETFRUIT_EXTRACT'].sort_values(['day', 'timestamp'])
    
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list)
    m67 = trades[trades['buyer'] == 'Mark 67']
    
    vfe['mid_diff'] = vfe.groupby('day')['mid_price'].diff()
    vfe['forward_200'] = vfe.groupby('day')['mid_price'].shift(-2) - vfe['mid_price']
    
    threshold = -1.5
    vfe['is_m67'] = False
    for _, row in m67.iterrows():
        vfe.loc[(vfe['day'] == row['day']) & (vfe['timestamp'] == row['timestamp']), 'is_m67'] = True
        
    sharp_drops = vfe[vfe['mid_diff'] <= threshold]
    
    print("Sharp Drop Comparison (t+200 Forward PnL):")
    print("\nWith Mark 67:")
    print(sharp_drops[sharp_drops['is_m67'] == True]['forward_200'].describe())
    
    print("\nWithout Mark 67:")
    print(sharp_drops[sharp_drops['is_m67'] == False]['forward_200'].describe())

if __name__ == "__main__":
    compare_m67_vs_others()
