"""Shared helpers for round5-hidden-paths analysis.

Bucket convention: matches v7 trader.
    bucket = int(timestamp * 5 // 1_000_000), clamped to [0, 4].

Bucket time boundaries (timestamps run 0..999_900 at step 100):
    bucket 0: [    0, 200_000)
    bucket 1: [200_000, 400_000)
    bucket 2: [400_000, 600_000)
    bucket 3: [600_000, 800_000)
    bucket 4: [800_000, 999_900]
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT, "raw-data", "ROUND5")
OUT_DIR = os.path.dirname(__file__)
DAYS = (2, 3, 4)
N_BUCKETS = 5
BUCKET_BOUNDARY = 200_000

PRODUCT_GROUPS = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ],
    "PEBBLES": [
        "PEBBLES_XS",
        "PEBBLES_S",
        "PEBBLES_M",
        "PEBBLES_L",
        "PEBBLES_XL",
    ],
    "ROBOT": [
        "ROBOT_VACUUMING",
        "ROBOT_MOPPING",
        "ROBOT_DISHES",
        "ROBOT_LAUNDRY",
        "ROBOT_IRONING",
    ],
    "UV_VISOR": [
        "UV_VISOR_YELLOW",
        "UV_VISOR_AMBER",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_MAGENTA",
    ],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ],
    "PANEL": [
        "PANEL_1X2",
        "PANEL_2X2",
        "PANEL_1X4",
        "PANEL_2X4",
        "PANEL_4X4",
    ],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
}

PRODUCT_TO_GROUP = {p: g for g, ps in PRODUCT_GROUPS.items() for p in ps}
ALL_PRODUCTS = sorted(PRODUCT_TO_GROUP.keys())

# Free alpha table from analysis/round5/free-alpha/20_free_alpha_probe.py.
# Tuple is (base, d1, d2, d3, d4); fair_path = [base, base+d1, base+d2, base+d3, base+d4].
FREE_ALPHA_TABLE = {
    "GALAXY_SOUNDS_BLACK_HOLES": (11193.8333, -68.0000, 241.3333, 36.3333, 1151.8333),
    "GALAXY_SOUNDS_DARK_MATTER": (10428.5000, -201.5000, -346.1667, -438.5000, 89.3333),
    "GALAXY_SOUNDS_PLANETARY_RINGS": (10888.3333, -155.1667, -291.6667, 25.3333, -120.0000),
    "GALAXY_SOUNDS_SOLAR_FLAMES": (10660.5000, 290.0000, 485.5000, 537.8333, 277.3333),
    "GALAXY_SOUNDS_SOLAR_WINDS": (10115.8333, -5.5000, 457.5000, 305.5000, 83.5000),
    "MICROCHIP_CIRCLE": (9140.8333, -154.1667, -31.8333, 6.8333, 127.3333),
    "MICROCHIP_OVAL": (8889.6667, -186.0000, -385.1667, -686.8333, -1488.5000),
    "MICROCHIP_RECTANGLE": (9080.6667, -268.1667, -85.0000, -334.0000, -403.5000),
    "MICROCHIP_SQUARE": (12789.5000, -77.3333, 270.1667, 1295.3333, 1205.3333),
    "MICROCHIP_TRIANGLE": (9911.5000, -84.5000, -30.3333, -405.6667, -693.3333),
    "OXYGEN_SHAKE_CHOCOLATE": (9599.6667, -51.3333, -327.3333, -100.1667, 240.6667),
    "OXYGEN_SHAKE_EVENING_BREATH": (9286.6667, 136.6667, 160.0000, 53.3333, -193.3333),
    "OXYGEN_SHAKE_GARLIC": (11250.3333, 80.8333, 134.1667, 837.6667, 1299.3333),
    "OXYGEN_SHAKE_MINT": (9939.6667, -60.8333, -251.0000, -304.6667, 52.1667),
    "OXYGEN_SHAKE_MORNING_BREATH": (10178.3333, 223.6667, 156.3333, -142.5000, -149.6667),
    "PANEL_1X2": (9092.6667, -391.0000, -339.5000, -409.1667, -99.0000),
    "PANEL_1X4": (9939.6667, -387.8333, -425.3333, -538.3333, -269.8333),
    "PANEL_2X2": (9762.1667, -231.1667, -417.1667, 114.6667, -192.0000),
    "PANEL_2X4": (10726.6667, -52.3333, 181.8333, 531.1667, 790.1667),
    "PANEL_4X4": (9977.8333, 402.5000, 233.3333, -322.3333, -291.6667),
    "PEBBLES_L": (10381.6667, -27.0000, 159.1667, -231.8333, -297.0000),
    "PEBBLES_M": (10028.6667, -336.0000, -28.8333, 421.5000, 229.8333),
    "PEBBLES_S": (9386.8333, -189.1667, -214.3333, -458.5000, -651.3333),
    "PEBBLES_XL": (11894.3333, 551.5000, 302.1667, 1300.0000, 2045.3333),
    "PEBBLES_XS": (8308.1667, 0.8333, -217.8333, -1030.6667, -1326.1667),
    "ROBOT_DISHES": (10015.6667, -126.0000, -235.1667, 41.0000, 405.5000),
    "ROBOT_IRONING": (9000.0000, 170.0000, 176.6667, -310.0000, -720.0000),
    "ROBOT_LAUNDRY": (9903.5000, -60.0000, -68.5000, 24.6667, -239.5000),
    "ROBOT_MOPPING": (10661.5000, 120.0000, -7.3333, 392.0000, 530.1667),
    "ROBOT_VACUUMING": (9550.5000, -255.3333, -440.0000, -322.8333, -570.5000),
    "SLEEP_POD_COTTON": (11105.1667, 265.3333, 277.3333, 463.3333, 471.5000),
    "SLEEP_POD_LAMB_WOOL": (10396.3333, 32.0000, 207.6667, 457.5000, 272.0000),
    "SLEEP_POD_NYLON": (9529.0000, -75.6667, 79.5000, 218.5000, 242.0000),
    "SLEEP_POD_POLYESTER": (11555.5000, -63.1667, 439.1667, 71.5000, 655.6667),
    "SLEEP_POD_SUEDE": (11074.5000, 190.5000, -64.0000, 370.0000, 603.0000),
    "SNACKPACK_CHOCOLATE": (9921.3333, -7.6667, 21.5000, 36.1667, -113.6667),
    "SNACKPACK_PISTACHIO": (9634.8333, -41.3333, -22.5000, -243.8333, -298.1667),
    "SNACKPACK_RASPBERRY": (10120.3333, 2.5000, -79.3333, 53.1667, 103.1667),
    "SNACKPACK_STRAWBERRY": (10413.8333, 89.3333, 260.1667, 178.1667, 297.0000),
    "SNACKPACK_VANILLA": (10023.0000, 23.1667, -26.1667, -74.0000, 109.3333),
    "TRANSLATOR_ASTRO_BLACK": (9774.5000, -53.0000, -237.3333, -417.5000, -352.6667),
    "TRANSLATOR_ECLIPSE_CHARCOAL": (9954.0000, 41.5000, 22.3333, -280.5000, -88.1667),
    "TRANSLATOR_GRAPHITE_MIST": (10130.3333, 327.6667, 311.0000, -148.8333, -70.0000),
    "TRANSLATOR_SPACE_GRAY": (9869.3333, -297.5000, -562.6667, -472.8333, -519.6667),
    "TRANSLATOR_VOID_BLUE": (10596.3333, 178.1667, 19.8333, 214.1667, 509.1667),
    "UV_VISOR_AMBER": (8627.3333, -410.3333, -487.1667, -629.5000, -954.5000),
    "UV_VISOR_MAGENTA": (10969.6667, -95.6667, 12.1667, -169.5000, 501.5000),
    "UV_VISOR_ORANGE": (10152.0000, 164.8333, 314.0000, 558.3333, -226.5000),
    "UV_VISOR_RED": (10624.5000, 323.1667, 487.6667, 637.8333, 574.0000),
    "UV_VISOR_YELLOW": (11211.6667, -56.0000, -301.1667, -491.1667, 16.0000),
}

# Products v7 / current root trader already owns through any sleeve.
# Used as a hint label in candidate ranking, NOT to filter.
V7_FREE_ALPHA_PRODUCTS = {
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "PANEL_2X2",
    "PEBBLES_L",
    "ROBOT_MOPPING",
    "ROBOT_VACUUMING",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SLEEP_POD_POLYESTER",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_YELLOW",
}
V7_MR_PRODUCTS = {
    "PEBBLES_XL",
    "PEBBLES_XS",
    "MICROCHIP_TRIANGLE",
    "ROBOT_LAUNDRY",
}
V7_RESIDUAL_PRODUCTS = {
    "SLEEP_POD_POLYESTER",  # already in free-alpha as well
}
V7_MM_BID_OFF = {
    "MICROCHIP_OVAL",
    "MICROCHIP_TRIANGLE",
    "ROBOT_IRONING",
    "TRANSLATOR_ASTRO_BLACK",
    "UV_VISOR_AMBER",
}
V7_MM_ASK_OFF = {
    "GALAXY_SOUNDS_BLACK_HOLES",
    "MICROCHIP_SQUARE",
    "OXYGEN_SHAKE_GARLIC",
    "PANEL_2X4",
    "PEBBLES_XL",
    "SLEEP_POD_SUEDE",
    "UV_VISOR_RED",
}


def load_prices(days=DAYS):
    """Load price snapshots for the requested days. Includes mid_price and
    L1/L2/L3 bid+ask sides plus a microprice (L1 weighted) and L1+L2+L3
    book-weighted mid.

    Returns a DataFrame with columns:
        day, timestamp, product, group, bucket, mid, micro_mid, weighted_mid,
        spread, total_depth.
    """
    frames = []
    for day in days:
        path = os.path.join(DATA_DIR, "prices_round_5_day_%d.csv" % day)
        df = pd.read_csv(path, sep=";")
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["group"] = df["product"].map(PRODUCT_TO_GROUP)
    df["bucket"] = np.minimum(N_BUCKETS - 1, df["timestamp"] * N_BUCKETS // 1_000_000).astype(int)

    # Microprice using L1 only (bid * ask_size + ask * bid_size) / total_size.
    bid1 = df["bid_price_1"].astype(float)
    ask1 = df["ask_price_1"].astype(float)
    bv1 = df["bid_volume_1"].fillna(0).astype(float)
    av1 = df["ask_volume_1"].fillna(0).astype(float)
    total1 = bv1 + av1
    micro = np.where(total1 > 0, (bid1 * av1 + ask1 * bv1) / np.where(total1 > 0, total1, 1.0), df["mid_price"])
    df["micro_mid"] = micro

    # Volume-weighted mid across all 3 levels.
    px_cols = [
        ("bid_price_1", "bid_volume_1"),
        ("bid_price_2", "bid_volume_2"),
        ("bid_price_3", "bid_volume_3"),
        ("ask_price_1", "ask_volume_1"),
        ("ask_price_2", "ask_volume_2"),
        ("ask_price_3", "ask_volume_3"),
    ]
    weighted_num = pd.Series(0.0, index=df.index)
    weighted_den = pd.Series(0.0, index=df.index)
    for px, vol in px_cols:
        p = df[px].fillna(0).astype(float)
        v = df[vol].fillna(0).astype(float)
        weighted_num = weighted_num + p * v
        weighted_den = weighted_den + v
    weighted_mid = np.where(weighted_den > 0, weighted_num / np.where(weighted_den > 0, weighted_den, 1.0), df["mid_price"])
    df["weighted_mid"] = weighted_mid

    df["spread"] = (ask1 - bid1).astype(float)
    df["total_depth"] = weighted_den

    df["mid"] = df["mid_price"].astype(float)
    cols = [
        "day",
        "timestamp",
        "product",
        "group",
        "bucket",
        "mid",
        "micro_mid",
        "weighted_mid",
        "spread",
        "total_depth",
    ]
    return df[cols].sort_values(["product", "day", "timestamp"]).reset_index(drop=True)


def free_alpha_path(product):
    """Return the 5-bucket fair path for `product` per the v7 free-alpha table.
    None if the product is not in the table.
    """
    vals = FREE_ALPHA_TABLE.get(product)
    if vals is None:
        return None
    base = vals[0]
    return [base + 0.0, base + vals[1], base + vals[2], base + vals[3], base + vals[4]]
