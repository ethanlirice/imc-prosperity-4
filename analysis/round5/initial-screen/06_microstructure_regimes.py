from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")

HORIZONS = [1, 5, 20]
RESID_THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
PASSIVE_FILL_WINDOW = 5

GROUPS = {
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
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
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
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
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

PRODUCT_TO_GROUP = {product: group for group, products in GROUPS.items() for product in products}


def read_prices() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv")):
        frames.append(pd.read_csv(path, sep=";"))
    prices = pd.concat(frames, ignore_index=True)
    prices["group"] = prices["product"].map(PRODUCT_TO_GROUP)
    return prices.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)


def read_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_5_day_*.csv")):
        day = int(path.stem.split("_")[-1])
        frame = pd.read_csv(path, sep=";")
        frame["day"] = day
        frame = frame.rename(columns={"symbol": "product"})
        frame["group"] = frame["product"].map(PRODUCT_TO_GROUP)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def add_book_fields(prices: pd.DataFrame) -> pd.DataFrame:
    out = prices.copy()
    for col in [
        "bid_volume_1",
        "bid_volume_2",
        "bid_volume_3",
        "ask_volume_1",
        "ask_volume_2",
        "ask_volume_3",
    ]:
        out[col] = out[col].fillna(0).abs()

    out["spread"] = out["ask_price_1"] - out["bid_price_1"]
    out["half_spread"] = out["spread"] / 2.0
    out["top_depth"] = out["bid_volume_1"] + out["ask_volume_1"]
    out["top3_depth"] = (
        out["bid_volume_1"]
        + out["bid_volume_2"]
        + out["bid_volume_3"]
        + out["ask_volume_1"]
        + out["ask_volume_2"]
        + out["ask_volume_3"]
    )
    out["top_depth_share"] = out["top_depth"] / out["top3_depth"].replace(0, np.nan)
    out["imbalance_1"] = (
        (out["bid_volume_1"] - out["ask_volume_1"]) / out["top_depth"].replace(0, np.nan)
    ).fillna(0.0)
    out["bid_gap_12"] = out["bid_price_1"] - out["bid_price_2"]
    out["bid_gap_23"] = out["bid_price_2"] - out["bid_price_3"]
    out["ask_gap_12"] = out["ask_price_2"] - out["ask_price_1"]
    out["ask_gap_23"] = out["ask_price_3"] - out["ask_price_2"]
    out["book_gap_mean"] = out[["bid_gap_12", "bid_gap_23", "ask_gap_12", "ask_gap_23"]].mean(axis=1)

    grouped = out.groupby(["product", "day"], sort=False)
    out["mid_ret_1"] = grouped["mid_price"].diff()
    for horizon in HORIZONS:
        out[f"future_mid_{horizon}"] = grouped["mid_price"].shift(-horizon)
        out[f"fwd_mid_chg_{horizon}"] = out[f"future_mid_{horizon}"] - out["mid_price"]
    out["time_bin"] = (out["timestamp"] // 100000).astype(int)
    return out


def add_passive_fill_proxy(prices: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    trade_grid = (
        trades.groupby(["product", "day", "timestamp"], as_index=False)
        .agg(trade_min_price=("price", "min"), trade_max_price=("price", "max"), trade_qty=("quantity", "sum"))
    )
    out = prices.merge(trade_grid, on=["product", "day", "timestamp"], how="left")
    grouped = out.groupby(["product", "day"], sort=False)
    future_min = []
    future_max = []
    for step in range(1, PASSIVE_FILL_WINDOW + 1):
        future_min.append(grouped["trade_min_price"].shift(-step))
        future_max.append(grouped["trade_max_price"].shift(-step))
    out[f"next{PASSIVE_FILL_WINDOW}_trade_min"] = pd.concat(future_min, axis=1).min(axis=1)
    out[f"next{PASSIVE_FILL_WINDOW}_trade_max"] = pd.concat(future_max, axis=1).max(axis=1)
    out["passive_buy_fill_next5"] = out[f"next{PASSIVE_FILL_WINDOW}_trade_min"] <= out["bid_price_1"]
    out["passive_sell_fill_next5"] = out[f"next{PASSIVE_FILL_WINDOW}_trade_max"] >= out["ask_price_1"]
    out["passive_buy_fill_next5"] = out["passive_buy_fill_next5"].fillna(False)
    out["passive_sell_fill_next5"] = out["passive_sell_fill_next5"].fillna(False)
    return out


def classify_trades(prices: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    quote_cols = [
        "product",
        "day",
        "timestamp",
        "bid_price_1",
        "ask_price_1",
        "bid_volume_1",
        "ask_volume_1",
        "mid_price",
        *[f"future_mid_{h}" for h in HORIZONS],
    ]
    out = trades.merge(prices[quote_cols], on=["product", "day", "timestamp"], how="left")
    out["at_bid"] = out["price"] <= out["bid_price_1"]
    out["at_ask"] = out["price"] >= out["ask_price_1"]
    out["inside_spread"] = (out["price"] > out["bid_price_1"]) & (out["price"] < out["ask_price_1"])
    out["outside_book"] = (out["price"] < out["bid_price_1"]) | (out["price"] > out["ask_price_1"])
    out["initiator_side"] = np.select([out["at_ask"], out["at_bid"]], [1.0, -1.0], default=0.0)
    out["touch_qty_to_depth"] = np.where(
        out["at_ask"],
        out["quantity"] / out["ask_volume_1"].replace(0, np.nan),
        np.where(out["at_bid"], out["quantity"] / out["bid_volume_1"].replace(0, np.nan), np.nan),
    )
    for horizon in HORIZONS:
        out[f"trade_markout_{horizon}"] = out["initiator_side"] * (out[f"future_mid_{horizon}"] - out["price"])
    return out


def mean_safe(values: pd.Series | np.ndarray) -> float:
    arr = pd.Series(values).dropna().to_numpy(dtype=float)
    return float(arr.mean()) if len(arr) else float("nan")


def corr_safe(x: pd.Series, y: pd.Series) -> float:
    frame = pd.concat([x, y], axis=1).dropna()
    if len(frame) < 20:
        return float("nan")
    a = frame.iloc[:, 0].to_numpy(dtype=float)
    b = frame.iloc[:, 1].to_numpy(dtype=float)
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def product_day_metrics(prices: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    trade_touch = trades.groupby(["product", "day"]).agg(
        trade_count=("price", "size"),
        trade_qty=("quantity", "sum"),
        at_bid_count=("at_bid", "sum"),
        at_ask_count=("at_ask", "sum"),
        inside_count=("inside_spread", "sum"),
        outside_count=("outside_book", "sum"),
        touch_qty_to_depth_median=("touch_qty_to_depth", "median"),
        trade_markout_1_mean=("trade_markout_1", "mean"),
        trade_markout_5_mean=("trade_markout_5", "mean"),
        trade_markout_20_mean=("trade_markout_20", "mean"),
    )
    rows = []
    for (product, day), frame in prices.groupby(["product", "day"], sort=False):
        group = PRODUCT_TO_GROUP[product]
        active_ratio = mean_safe(frame["fwd_mid_chg_5"].abs() / frame["half_spread"].replace(0, np.nan))

        extreme_cut = frame["imbalance_1"].abs().quantile(0.8)
        extreme = frame[(frame["imbalance_1"].abs() >= extreme_cut) & (frame["imbalance_1"].abs() > 0.0)]
        direction = np.sign(extreme["imbalance_1"])
        imb_mid_edge = mean_safe(direction * extreme["fwd_mid_chg_1"])
        imb_active_edge = mean_safe(
            np.where(direction > 0, extreme["future_mid_1"] - extreme["ask_price_1"], extreme["bid_price_1"] - extreme["future_mid_1"])
        )
        imb_passive_edge = mean_safe(
            np.where(direction > 0, extreme["future_mid_1"] - extreme["bid_price_1"], extreme["ask_price_1"] - extreme["future_mid_1"])
        )
        imb_fill_proxy = mean_safe(
            np.where(direction > 0, extreme["passive_buy_fill_next5"], extreme["passive_sell_fill_next5"])
        )

        row = {
            "product": product,
            "group": group,
            "day": int(day),
            "ticks": int(len(frame)),
            "spread_median": float(frame["spread"].median()),
            "spread_p90": float(frame["spread"].quantile(0.9)),
            "top_depth_median": float(frame["top_depth"].median()),
            "top3_depth_median": float(frame["top3_depth"].median()),
            "top_depth_share_median": float(frame["top_depth_share"].median()),
            "imbalance_abs_mean": float(frame["imbalance_1"].abs().mean()),
            "imbalance_corr_h1": corr_safe(frame["imbalance_1"], frame["fwd_mid_chg_1"]),
            "imbalance_extreme_n": int(len(extreme)),
            "imbalance_extreme_mid_edge_h1": imb_mid_edge,
            "imbalance_extreme_active_edge_h1": imb_active_edge,
            "imbalance_extreme_passive_edge_h1": imb_passive_edge,
            "imbalance_extreme_passive_fill_next5": imb_fill_proxy,
            "book_gap_mean_median": float(frame["book_gap_mean"].median()),
            "mid_ret_abs_mean": float(frame["mid_ret_1"].abs().mean()),
            "mid_ret_sd": float(frame["mid_ret_1"].std()),
            "move_tick_pct": float((frame["mid_ret_1"].abs() > 1e-12).mean()),
            "fwd_abs_move_h5_to_halfspread": active_ratio,
            "passive_buy_fill_next5_pct": float(frame["passive_buy_fill_next5"].mean()),
            "passive_sell_fill_next5_pct": float(frame["passive_sell_fill_next5"].mean()),
        }
        if (product, day) in trade_touch.index:
            row.update(trade_touch.loc[(product, day)].to_dict())
        else:
            row.update(
                {
                    "trade_count": 0,
                    "trade_qty": 0,
                    "at_bid_count": 0,
                    "at_ask_count": 0,
                    "inside_count": 0,
                    "outside_count": 0,
                    "touch_qty_to_depth_median": float("nan"),
                    "trade_markout_1_mean": float("nan"),
                    "trade_markout_5_mean": float("nan"),
                    "trade_markout_20_mean": float("nan"),
                }
            )
        rows.append(row)
    out = pd.DataFrame(rows)
    out["trade_ticks_pct"] = out["trade_count"] / out["ticks"]
    out["at_touch_share"] = (out["at_bid_count"] + out["at_ask_count"]) / out["trade_count"].replace(0, np.nan)
    out["inside_share"] = out["inside_count"] / out["trade_count"].replace(0, np.nan)
    out["outside_share"] = out["outside_count"] / out["trade_count"].replace(0, np.nan)
    return out


def aggregate_product_metrics(product_day: pd.DataFrame) -> pd.DataFrame:
    numeric = product_day.select_dtypes(include=[np.number]).columns.difference(["day"])
    out = product_day.groupby(["product", "group"], as_index=False)[list(numeric)].mean()
    return out.sort_values(["group", "product"])


def aggregate_group_metrics(product_day: pd.DataFrame) -> pd.DataFrame:
    numeric = product_day.select_dtypes(include=[np.number]).columns.difference(["day"])
    out = product_day.groupby("group", as_index=False)[list(numeric)].mean()
    out["min_product_trade_ticks_pct"] = product_day.groupby("group")["trade_ticks_pct"].min().to_numpy()
    out["max_product_spread_median"] = product_day.groupby("group")["spread_median"].max().to_numpy()
    return out.sort_values("group")


def residual_z_table(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    key_cols = ["day", "timestamp"]
    for group, products in GROUPS.items():
        pivot = (
            prices[prices["product"].isin(products)]
            .pivot(index=key_cols, columns="product", values="mid_price")
            .sort_index()
        )
        for target in products:
            components = [product for product in products if product != target]
            frame = pivot[[target] + components].dropna()
            y = frame[target].to_numpy(dtype=float)
            x = frame[components].to_numpy(dtype=float)
            x = np.column_stack([np.ones(len(x)), x])
            coef = np.linalg.lstsq(x, y, rcond=None)[0]
            resid = y - x @ coef
            resid_sd = float(np.std(resid))
            if resid_sd <= 1e-12:
                continue
            part = pd.DataFrame(index=frame.index)
            part["product"] = target
            part["group"] = group
            part["resid"] = resid
            part["resid_z"] = resid / resid_sd
            rows.append(part.reset_index())
    return pd.concat(rows, ignore_index=True)


def residual_threshold_metrics(prices: pd.DataFrame, residuals: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "product",
        "group",
        "day",
        "timestamp",
        "bid_price_1",
        "ask_price_1",
        "mid_price",
        "passive_buy_fill_next5",
        "passive_sell_fill_next5",
        *[f"future_mid_{h}" for h in HORIZONS],
    ]
    frame = residuals.merge(prices[cols], on=["product", "group", "day", "timestamp"], how="left")
    rows = []
    for (group, product), product_frame in frame.groupby(["group", "product"], sort=False):
        for threshold in RESID_THRESHOLDS:
            signal = product_frame[product_frame["resid_z"].abs() >= threshold].copy()
            if signal.empty:
                continue
            direction = -np.sign(signal["resid_z"])  # Positive residual means sell target; negative means buy.
            signal["passive_fill_next5"] = np.where(
                direction > 0,
                signal["passive_buy_fill_next5"],
                signal["passive_sell_fill_next5"],
            )
            row = {
                "group": group,
                "product": product,
                "threshold_abs_z": threshold,
                "signal_n": int(len(signal)),
                "signal_pct": float(len(signal) / len(product_frame)),
                "buy_signal_share": float((direction > 0).mean()),
                "passive_fill_next5_pct": float(signal["passive_fill_next5"].mean()),
            }
            for horizon in HORIZONS:
                fut = signal[f"future_mid_{horizon}"]
                active_edge = np.where(
                    direction > 0,
                    fut - signal["ask_price_1"],
                    signal["bid_price_1"] - fut,
                )
                passive_edge = np.where(
                    direction > 0,
                    fut - signal["bid_price_1"],
                    signal["ask_price_1"] - fut,
                )
                mid_edge = direction * (fut - signal["mid_price"])
                signal[f"active_edge_{horizon}"] = active_edge
                row[f"mid_edge_h{horizon}"] = float(np.nanmean(mid_edge))
                row[f"active_edge_h{horizon}"] = float(np.nanmean(active_edge))
                row[f"passive_edge_h{horizon}"] = float(np.nanmean(passive_edge))
                day_edges = signal.groupby("day")[f"active_edge_{horizon}"].mean()
                row[f"active_edge_h{horizon}_positive_days"] = int((day_edges > 0).sum())
                row[f"active_edge_h{horizon}_min_day"] = float(day_edges.min())
            rows.append(row)
    out = pd.DataFrame(rows)
    return out.sort_values(
        ["active_edge_h1", "active_edge_h5", "passive_fill_next5_pct"],
        ascending=[False, False, False],
    )


def time_regime_metrics(prices: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    trade_counts = trades.copy()
    trade_counts["time_bin"] = (trade_counts["timestamp"] // 100000).astype(int)
    trade_counts = trade_counts.groupby(["group", "day", "time_bin"], as_index=False).agg(
        trade_count=("price", "size"), trade_qty=("quantity", "sum")
    )
    rows = []
    for (group, day, time_bin), frame in prices.groupby(["group", "day", "time_bin"], sort=False):
        rows.append(
            {
                "group": group,
                "day": int(day),
                "time_bin": int(time_bin),
                "ticks": int(len(frame)),
                "spread_median": float(frame["spread"].median()),
                "top_depth_median": float(frame["top_depth"].median()),
                "imbalance_abs_mean": float(frame["imbalance_1"].abs().mean()),
                "mid_ret_abs_mean": float(frame["mid_ret_1"].abs().mean()),
                "passive_fill_next5_pct": float(
                    (frame["passive_buy_fill_next5"] | frame["passive_sell_fill_next5"]).mean()
                ),
            }
        )
    out = pd.DataFrame(rows)
    out = out.merge(trade_counts, on=["group", "day", "time_bin"], how="left")
    out[["trade_count", "trade_qty"]] = out[["trade_count", "trade_qty"]].fillna(0)
    out["trade_ticks_pct"] = out["trade_count"] / out["ticks"]
    return out.sort_values(["group", "day", "time_bin"])


def trade_markout_summary(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.groupby(["product", "group"], as_index=False).agg(
        trade_count=("price", "size"),
        trade_qty=("quantity", "sum"),
        at_bid_share=("at_bid", "mean"),
        at_ask_share=("at_ask", "mean"),
        inside_share=("inside_spread", "mean"),
        outside_share=("outside_book", "mean"),
        touch_qty_to_depth_median=("touch_qty_to_depth", "median"),
        trade_markout_1_mean=("trade_markout_1", "mean"),
        trade_markout_5_mean=("trade_markout_5", "mean"),
        trade_markout_20_mean=("trade_markout_20", "mean"),
    )
    return out.sort_values(["group", "product"])


def md_table(frame: pd.DataFrame, columns: list[str], n: int | None = None, digits: int = 4) -> str:
    view = frame[columns].copy()
    if n is not None:
        view = view.head(n)
    return view.round(digits).to_markdown(index=False)


def write_report(
    product: pd.DataFrame,
    group: pd.DataFrame,
    residuals: pd.DataFrame,
    time_regimes: pd.DataFrame,
    trades: pd.DataFrame,
) -> None:
    crossing = residuals[residuals["signal_n"] >= 100].sort_values("active_edge_h1", ascending=False)
    passive = residuals[residuals["signal_n"] >= 100].sort_values(
        ["passive_fill_next5_pct", "passive_edge_h1"], ascending=False
    )
    imbalance = product[product["imbalance_extreme_n"] >= 200].sort_values(
        "imbalance_extreme_active_edge_h1", ascending=False
    )
    active_trade = trades[trades["trade_count"] >= 100].sort_values("trade_markout_5_mean", ascending=False)

    group_rank = group.sort_values(
        ["fwd_abs_move_h5_to_halfspread", "trade_ticks_pct", "passive_buy_fill_next5_pct"],
        ascending=False,
    )
    time_lively = time_regimes.sort_values(["mid_ret_abs_mean", "trade_ticks_pct"], ascending=False)
    time_passive = time_regimes.sort_values(["passive_fill_next5_pct", "trade_ticks_pct"], ascending=False)
    stable_active = crossing[crossing["active_edge_h1_positive_days"] == 3].head(5)
    top_active = crossing.head(1)
    top_imbalance = imbalance.head(1)
    top_passive_bin = time_passive.head(1)

    lines = [
        "# Round 5 Lens 2 - Microstructure Regimes",
        "",
        "Scope: all 50 Round 5 products on days 2, 3, and 4.",
        "Execution proxies use visible top-of-book only. `active_edge` crosses the current bid/ask; `passive_edge` assumes a fill at current bid/ask and is therefore an upper bound, paired with a next-5-tick touch-fill proxy.",
        "",
        "## Actionable Findings",
        "",
    ]
    if not stable_active.empty:
        row = stable_active.iloc[0]
        lines.append(
            f"- **Best day-stable active residual signal:** {row['product']} at `|z| >= {row['threshold_abs_z']:.1f}` "
            f"has {row['signal_n']:.0f} signal ticks, h1 active edge {row['active_edge_h1']:.3f}, "
            f"positive on all 3 days, and worst daily h1 active edge {row['active_edge_h1_min_day']:.3f}. "
            f"Next-5-tick passive touch-fill proxy is {row['passive_fill_next5_pct']:.3%}."
        )
    if not top_active.empty:
        row = top_active.iloc[0]
        lines.append(
            f"- **Largest active residual average:** {row['product']} at `|z| >= {row['threshold_abs_z']:.1f}` "
            f"has h1 active edge {row['active_edge_h1']:.3f} and h5 active edge {row['active_edge_h5']:.3f}, "
            f"but only {row['active_edge_h1_positive_days']:.0f}/3 h1-positive days."
        )
    if not top_imbalance.empty:
        row = top_imbalance.iloc[0]
        lines.append(
            f"- **Top-level imbalance alone is weak:** best product average is {row['product']} with "
            f"h1 active edge {row['imbalance_extreme_active_edge_h1']:.3f} over about "
            f"{row['imbalance_extreme_n']:.0f} extreme ticks/day, but passive touch-fill proxy is only "
            f"{row['imbalance_extreme_passive_fill_next5']:.3%}."
        )
    if not top_passive_bin.empty:
        row = top_passive_bin.iloc[0]
        lines.append(
            f"- **Most fillable regime:** {row['group']} day {row['day']:.0f} time bin {row['time_bin']:.0f} "
            f"has next-5-tick passive touch-fill {row['passive_fill_next5_pct']:.3%}, "
            f"trade-tick rate {row['trade_ticks_pct']:.3%}, and median spread {row['spread_median']:.1f}."
        )
    lines.extend(
        [
            "",
        "## Group Execution Surface",
        "",
        md_table(
            group_rank,
            [
                "group",
                "spread_median",
                "top_depth_median",
                "top3_depth_median",
                "trade_ticks_pct",
                "passive_buy_fill_next5_pct",
                "passive_sell_fill_next5_pct",
                "fwd_abs_move_h5_to_halfspread",
                "imbalance_extreme_active_edge_h1",
            ],
            digits=5,
        ),
        "",
        "## Residual-Z Executable Thresholds",
        "",
        "Best active crossing candidates among product/group basket residual signals with at least 100 signal ticks:",
        "",
        md_table(
            crossing,
            [
                "group",
                "product",
                "threshold_abs_z",
                "signal_n",
                "signal_pct",
                "mid_edge_h1",
                "active_edge_h1",
                "active_edge_h1_positive_days",
                "active_edge_h1_min_day",
                "passive_edge_h1",
                "passive_fill_next5_pct",
            ],
            n=20,
            digits=5,
        ),
        "",
        "Best passive upper-bound candidates among the same residual signals:",
        "",
        md_table(
            passive,
            [
                "group",
                "product",
                "threshold_abs_z",
                "signal_n",
                "signal_pct",
                "passive_edge_h1",
                "passive_fill_next5_pct",
                "active_edge_h1",
                "active_edge_h1_positive_days",
            ],
            n=20,
            digits=5,
        ),
        "",
        "## Top-Level Imbalance",
        "",
        "Extreme imbalance is each product/day's top 20% by absolute top-level imbalance. Active edge crosses in the imbalance direction at h=1.",
        "",
        md_table(
            imbalance,
            [
                "group",
                "product",
                "spread_median",
                "imbalance_abs_mean",
                "imbalance_corr_h1",
                "imbalance_extreme_mid_edge_h1",
                "imbalance_extreme_active_edge_h1",
                "imbalance_extreme_passive_edge_h1",
                "imbalance_extreme_passive_fill_next5",
            ],
            n=20,
            digits=5,
        ),
        "",
        "## Trade Occurrence And Fill Quality",
        "",
        md_table(
            active_trade,
            [
                "group",
                "product",
                "trade_count",
                "at_bid_share",
                "at_ask_share",
                "inside_share",
                "outside_share",
                "touch_qty_to_depth_median",
                "trade_markout_1_mean",
                "trade_markout_5_mean",
                "trade_markout_20_mean",
            ],
            n=25,
            digits=5,
        ),
        "",
        "## Day And Time Regimes",
        "",
        "Most volatile group/day/time bins:",
        "",
        md_table(
            time_lively,
            [
                "group",
                "day",
                "time_bin",
                "spread_median",
                "top_depth_median",
                "mid_ret_abs_mean",
                "trade_ticks_pct",
                "passive_fill_next5_pct",
            ],
            n=20,
            digits=5,
        ),
        "",
        "Highest next-5-tick passive touch-fill bins:",
        "",
        md_table(
            time_passive,
            [
                "group",
                "day",
                "time_bin",
                "spread_median",
                "top_depth_median",
                "mid_ret_abs_mean",
                "trade_ticks_pct",
                "passive_fill_next5_pct",
            ],
            n=20,
            digits=5,
        ),
        "",
        "## Interpretation",
        "",
        "- Residual mean reversion is statistically visible, but active crossing must beat a median half-spread of roughly 5-8 ticks depending on group. The residual-z scan is the decisive executable filter.",
        "- Passive residual signals show positive upper-bound markouts because they collect spread, but next-5-tick touch-fill probabilities are generally low enough that queue/fill uncertainty dominates. Treat passive results as quote-skew candidates, not guaranteed trades.",
        "- Top-level imbalance has a few small positive active averages after spread, but the signal is thin and low-fill; use it only as a secondary skew/gating variable.",
        "- Historical trade prints are mostly touch prints with small quantity relative to visible top depth; observed active print markouts are a fill-quality diagnostic, not a copy signal because trade files have no named counterparties.",
        ]
    )
    (OUT_DIR / "06_microstructure_regimes.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = add_book_fields(read_prices())
    trades_raw = read_trades()
    prices = add_passive_fill_proxy(prices, trades_raw)
    trades = classify_trades(prices, trades_raw)

    product_day = product_day_metrics(prices, trades)
    product = aggregate_product_metrics(product_day)
    group = aggregate_group_metrics(product_day)
    residuals = residual_threshold_metrics(prices, residual_z_table(prices))
    time_regimes = time_regime_metrics(prices, trades)
    trade_summary = trade_markout_summary(trades)

    product_day.to_csv(OUT_DIR / "06_product_day_microstructure.csv", index=False)
    product.to_csv(OUT_DIR / "06_product_microstructure.csv", index=False)
    group.to_csv(OUT_DIR / "06_group_microstructure.csv", index=False)
    residuals.to_csv(OUT_DIR / "06_residual_thresholds.csv", index=False)
    time_regimes.to_csv(OUT_DIR / "06_time_regimes.csv", index=False)
    trade_summary.to_csv(OUT_DIR / "06_trade_markouts.csv", index=False)
    write_report(product, group, residuals, time_regimes, trade_summary)

    print("Wrote notebooks/round5/06_microstructure_regimes.md")
    print("Top active residual thresholds:")
    print(
        residuals[residuals["signal_n"] >= 100]
        .head(12)[
            [
                "group",
                "product",
                "threshold_abs_z",
                "signal_n",
                "active_edge_h1",
                "active_edge_h1_positive_days",
                "passive_edge_h1",
                "passive_fill_next5_pct",
            ]
        ]
        .round(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
