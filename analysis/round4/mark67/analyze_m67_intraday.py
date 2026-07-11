
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))
PRICES_FILES = sorted(DATA_DIR.glob("prices_round_4_day_*.csv"))

def analyze_m67_intraday():
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list).sort_values(['day', 'timestamp']).reset_index(drop=True)
    m67 = trades[trades['buyer'] == 'Mark 67']

    prices_list = []
    for f in PRICES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        prices_list.append(df)
    prices = pd.concat(prices_list)
    vfe_prices = prices[prices['product'] == 'VELVETFRUIT_EXTRACT']

    print("Mark 67 Intraday Distribution (by day):")
    for day in m67['day'].unique():
        day_m67 = m67[m67['day'] == day]
        print(f"Day {day}: {len(day_m67)} trades")
        # Bin by 50,000 units
        bins = pd.cut(day_m67['timestamp'], bins=range(0, 1000001, 50000))
        print(bins.value_counts().sort_index())

    # Look for "Trigger" in price path
    print("\nPrice Path before M67 trade:")
    all_paths = []
    for _, row in m67.iterrows():
        day_prices = vfe_prices[vfe_prices['day'] == row['day']]
        path = day_prices[(day_prices['timestamp'] <= row['timestamp']) & 
                          (day_prices['timestamp'] >= row['timestamp'] - 500)]
        if len(path) == 6: # Ensure we have all 6 points (0, 100, 200, 300, 400, 500)
            mid_at_trade = path.iloc[-1]['mid_price']
            relative_path = path['mid_price'].values - mid_at_trade
            all_paths.append(relative_path)
    
    if all_paths:
        avg_path = np.mean(all_paths, axis=0)
        print("Average relative price path (500 units before to 0):")
        print(avg_path)
        
    # Is there a "Velocity" trigger?
    print("\nMid-price velocity (diff) before M67:")
    velocities = []
    for _, row in m67.iterrows():
        day_prices = vfe_prices[vfe_prices['day'] == row['day']]
        prev = day_prices[day_prices['timestamp'] == row['timestamp'] - 100]
        if not prev.empty:
            velocities.append(row['price'] - prev['mid_price'].values[0])
    
    vel_df = pd.Series(velocities)
    print(vel_df.describe())

if __name__ == "__main__":
    analyze_m67_intraday()
