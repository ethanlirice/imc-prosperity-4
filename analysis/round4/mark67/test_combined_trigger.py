
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def test_combined_trigger():
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
    vfe['spread'] = vfe['ask_price_1'] - vfe['bid_price_1']
    vfe['ask_vol'] = vfe['ask_volume_1'].abs()
    vfe['forward_200'] = vfe.groupby('day')['mid_price'].shift(-2) - vfe['mid_price']
    
    # Combined Trigger
    trigger = (vfe['mid_diff'] <= -1.5) & (vfe['spread'] <= 2.0) & (vfe['ask_vol'] <= 15)
    
    triggered_events = vfe[trigger].copy()
    print(f"Total triggered events: {len(triggered_events)}")
    
    coincidence = 0
    for _, event in triggered_events.iterrows():
        matches = m67[(m67['day'] == event['day']) & (m67['timestamp'] == event['timestamp'])]
        if not matches.empty:
            coincidence += 1
            
    print(f"Triggered events coinciding with M67: {coincidence} ({coincidence/len(triggered_events):.2%})")
    print(f"M67 trades covered: {coincidence} ({coincidence/len(m67):.2%})")
    
    print("\nForward PnL (t+200) for Triggered events:")
    print(triggered_events['forward_200'].describe())
    
    # What if we vary the thresholds?
    print("\nSweep on Ask Volume Threshold:")
    for v in [5, 10, 15, 20]:
        t = (vfe['mid_diff'] <= -1.5) & (vfe['spread'] <= 2.0) & (vfe['ask_vol'] <= v)
        events = vfe[t]
        print(f"Vol <= {v}: count={len(events)}, mean_pnl={events['forward_200'].mean():.4f}, m67_hit={sum(events.index.isin(vfe[vfe.index.isin(m67.index)].index))}")
        # Note: the index check in the last line might be wrong due to merges, let's just use a loop for now or a merge check.

if __name__ == "__main__":
    test_combined_trigger()
