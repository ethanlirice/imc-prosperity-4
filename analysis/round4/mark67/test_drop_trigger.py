
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def test_drop_trigger():
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
    
    # Identify all sharp drops
    threshold = -1.5
    sharp_drops = vfe[vfe['mid_diff'] <= threshold]
    
    print(f"Total sharp drops (diff <= {threshold}): {len(sharp_drops)}")
    
    # How many of these sharp drops coincide with a Mark 67 trade at the same timestamp?
    coincidence = 0
    for _, drop in sharp_drops.iterrows():
        matches = m67[(m67['day'] == drop['day']) & (m67['timestamp'] == drop['timestamp'])]
        if not matches.empty:
            coincidence += 1
            
    print(f"Sharp drops coinciding with M67 trade: {coincidence} ({coincidence/len(sharp_drops):.2%})")
    print(f"Total M67 trades covered: {coincidence} ({coincidence/len(m67):.2%})")
    
    # What if we look at the forward PnL of these sharp drops (regardless of M67)?
    vfe['forward_200'] = vfe.groupby('day')['mid_price'].shift(-2) - vfe['mid_price']
    print("\nForward PnL (t+200) for ALL sharp drops:")
    print(vfe[vfe['mid_diff'] <= threshold]['forward_200'].describe())

if __name__ == "__main__":
    test_drop_trigger()
