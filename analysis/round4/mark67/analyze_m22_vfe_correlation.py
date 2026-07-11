
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def analyze_m22_vfe_correlation():
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
    
    m22_options = trades[(trades['seller'] == 'Mark 22') & (trades['symbol'].str.startswith('VEV_'))]
    baskets = m22_options.groupby(['day', 'timestamp']).size().reset_index(name='basket_size')
    
    vfe['mid_diff'] = vfe.groupby('day')['mid_price'].diff()
    
    # For each M22 basket, check the VFE mid_diff at that same timestamp
    basket_impact = []
    for _, b in baskets.iterrows():
        vfe_tick = vfe[(vfe['day'] == b['day']) & (vfe['timestamp'] == b['timestamp'])]
        if not vfe_tick.empty:
            basket_impact.append({
                'day': b['day'],
                'timestamp': b['timestamp'],
                'basket_size': b['basket_size'],
                'vfe_diff': vfe_tick.iloc[0]['mid_diff']
            })
            
    impact_df = pd.DataFrame(basket_impact)
    print("VFE Mid-Price Diff at M22 Option Basket Timestamps:")
    print(impact_df['vfe_diff'].describe())
    
    print("\nBaskets coinciding with a sharp drop (<= -1.5):")
    sharp_basket = impact_df[impact_df['vfe_diff'] <= -1.5]
    print(len(sharp_basket), "out of", len(impact_df), f"({len(sharp_basket)/len(impact_df):.2%})")
    
    # Now, how many of THESE sharp baskets are followed by Mark 67?
    m67 = trades[trades['buyer'] == 'Mark 67']
    coincidence = 0
    for _, b in sharp_basket.iterrows():
        matches = m67[(m67['day'] == b['day']) & (m67['timestamp'] == b['timestamp'])]
        if not matches.empty:
            coincidence += 1
    print(f"Sharp baskets coinciding with M67 trade: {coincidence} ({coincidence/len(sharp_basket):.2%})")

if __name__ == "__main__":
    analyze_m22_vfe_correlation()
