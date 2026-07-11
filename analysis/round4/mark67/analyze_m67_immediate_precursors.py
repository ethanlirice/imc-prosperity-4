
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def analyze_m67_immediate_precursors():
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list).sort_values(['day', 'timestamp']).reset_index(drop=True)
    
    m67_trades = trades[trades['buyer'] == 'Mark 67']
    
    precursor_100 = []
    precursor_0 = []
    
    for _, m in m67_trades.iterrows():
        # What happened at T-100?
        t_100 = trades[(trades['day'] == m['day']) & (trades['timestamp'] == m['timestamp'] - 100)]
        if not t_100.empty:
            p_seq = " | ".join([f"{r['buyer']}:{r['symbol']}" for _, r in t_100.iterrows()])
            precursor_100.append(p_seq)
        else:
            precursor_100.append("EMPTY")
            
        # What happened at the same T? (before M67 in the list?)
        t_0 = trades[(trades['day'] == m['day']) & (trades['timestamp'] == m['timestamp'])]
        # Find M67's position in this list
        m_idx_in_t0 = t_0[t_0['buyer'] == 'Mark 67'].index[0]
        before_in_t0 = t_0.loc[:m_idx_in_t0-1]
        if not before_in_t0.empty:
            p_seq = " | ".join([f"{r['buyer']}:{r['symbol']}" for _, r in before_in_t0.iterrows()])
            precursor_0.append(p_seq)
        else:
            precursor_0.append("EMPTY")

    print("Top Precursors at T-100:")
    print(pd.Series(precursor_100).value_counts().head(10))
    
    print("\nTop Precursors at SAME T (before M67):")
    print(pd.Series(precursor_0).value_counts().head(10))

if __name__ == "__main__":
    analyze_m67_immediate_precursors()
