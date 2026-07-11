
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/ROUND4")
TRADES_FILES = sorted(DATA_DIR.glob("trades_round_4_day_*.csv"))

def analyze_m67_sequences():
    trades_list = []
    for f in TRADES_FILES:
        df = pd.read_csv(f, sep=";")
        df['day'] = int(f.stem.split("_")[-1])
        trades_list.append(df)
    trades = pd.concat(trades_list).sort_values(['day', 'timestamp']).reset_index(drop=True)
    
    m67_indices = trades[trades['buyer'] == 'Mark 67'].index
    
    sequences = []
    for idx in m67_indices:
        if idx < 10: continue
        # Look at 10 trades before
        pre = trades.iloc[idx-10:idx]
        seq = []
        for _, r in pre.iterrows():
            trader = r['buyer'] if r['buyer'] != 'Mark 67' else 'M67-Internal?' # Should be buyer side if we are looking for buying pressure
            # If buyer is None, it's a seller-initiated trade?
            # Actually buyer/seller fields in the CSV are the IDs.
            # Let's just record the buyer/seller pair
            seq.append(f"{r['buyer']}->{r['seller']}:{r['symbol']}")
        sequences.append(" | ".join(seq))
    
    seq_df = pd.Series(sequences)
    print("Top 10 Sequences of 10 trades before M67:")
    print(seq_df.value_counts().head(10))
    
    # Let's try a shorter sequence, say 3 trades
    sequences_3 = []
    for idx in m67_indices:
        if idx < 3: continue
        pre = trades.iloc[idx-3:idx]
        seq = []
        for _, r in pre.iterrows():
            seq.append(f"{r['buyer']}:{r['symbol']}")
        sequences_3.append(" | ".join(seq))
    
    seq3_df = pd.Series(sequences_3)
    print("\nTop 10 Sequences of 3 trades before M67:")
    print(seq3_df.value_counts().head(10))

    # Check for timestamp patterns (modulo)
    print("\nTimestamp Modulo Analysis:")
    m67_trades = trades[trades['buyer'] == 'Mark 67']
    for m in [100, 500, 1000, 5000, 10000]:
        print(f"Mod {m}:")
        print((m67_trades['timestamp'] % m).value_counts().head(5))

if __name__ == "__main__":
    analyze_m67_sequences()
