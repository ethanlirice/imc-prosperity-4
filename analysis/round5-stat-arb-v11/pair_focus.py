import math
from pathlib import Path
import numpy as np
import pandas as pd

DATA_DIR = Path("raw-data/ROUND5")

def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)

def ols_y_on_x(y, x):
    x_mean, y_mean = np.mean(x), np.mean(y)
    beta = np.mean((x - x_mean) * (y - y_mean)) / np.var(x)
    alpha = y_mean - beta * x_mean
    return alpha, beta

def main():
    prices = read_prices()
    g = prices[prices["product"].isin(["MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE"])]
    pivot = g.pivot(index=["day", "timestamp"], columns="product", values="mid_price").dropna()
    
    y = pivot["MICROCHIP_RECTANGLE"].values
    x = pivot["MICROCHIP_SQUARE"].values
    
    alpha, beta = ols_y_on_x(y, x)
    resid = y - (alpha + beta * x)
    resid_sd = np.std(resid)
    
    print(f"RECTANGLE = {alpha:.4f} + {beta:.4f} * SQUARE")
    print(f"Resid SD: {resid_sd:.4f}")
    
    # Check per day
    for day in [2, 3, 4]:
        d = pivot.xs(day, level="day")
        da, db = ols_y_on_x(d["MICROCHIP_RECTANGLE"].values, d["MICROCHIP_SQUARE"].values)
        print(f"Day {day}: alpha={da:.4f}, beta={db:.4f}")

if __name__ == "__main__":
    main()
