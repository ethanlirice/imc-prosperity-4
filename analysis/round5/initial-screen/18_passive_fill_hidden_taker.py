from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")

HORIZONS = [1, 5, 20, 100, 500]
QUOTE_MODES = ["best_touch", "one_tick_inside", "book_mid", "wall_mid", "residual_fair"]
QTY_CAP = 10

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
PRODUCTS = [product for products in GROUPS.values() for product in products]


def read_prices() -> pd.DataFrame:
    frames = [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))]
    prices = pd.concat(frames, ignore_index=True)
    prices["group"] = prices["product"].map(PRODUCT_TO_GROUP)
    prices = prices[prices["day"].isin([2, 3, 4]) & prices["product"].isin(PRODUCTS)].copy()
    for col in [
        "bid_volume_1",
        "bid_volume_2",
        "bid_volume_3",
        "ask_volume_1",
        "ask_volume_2",
        "ask_volume_3",
    ]:
        prices[col] = prices[col].fillna(0).abs()
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    prices["book_mid_floor"] = np.floor(prices["mid_price"]).astype(float)
    prices["book_mid_ceil"] = np.ceil(prices["mid_price"]).astype(float)
    prices["wall_bid_price"] = wall_price(prices, "bid")
    prices["wall_ask_price"] = wall_price(prices, "ask")
    prices["wall_mid"] = (prices["wall_bid_price"] + prices["wall_ask_price"]) / 2.0
    prices["wall_mid_floor"] = np.floor(prices["wall_mid"]).astype(float)
    prices["wall_mid_ceil"] = np.ceil(prices["wall_mid"]).astype(float)
    return prices.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)


def read_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_5_day_*.csv")):
        day = int(path.stem.split("_")[-1])
        frame = pd.read_csv(path, sep=";").rename(columns={"symbol": "product"})
        frame["day"] = day
        frame["group"] = frame["product"].map(PRODUCT_TO_GROUP)
        frames.append(frame)
    trades = pd.concat(frames, ignore_index=True)
    return trades[trades["day"].isin([2, 3, 4]) & trades["product"].isin(PRODUCTS)].copy()


def wall_price(prices: pd.DataFrame, side: str) -> pd.Series:
    price_cols = [f"{side}_price_{level}" for level in [1, 2, 3]]
    volume_cols = [f"{side}_volume_{level}" for level in [1, 2, 3]]
    vols = prices[volume_cols].to_numpy(dtype=float)
    pxs = prices[price_cols].to_numpy(dtype=float)
    idx = np.nanargmax(np.where(np.isfinite(vols), vols, -1.0), axis=1)
    return pd.Series(pxs[np.arange(len(prices)), idx], index=prices.index)


def fit_ols(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return np.linalg.lstsq(design, y, rcond=None)[0]


def predict_ols(coef: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    return design @ coef


def add_residual_fair(prices: pd.DataFrame) -> pd.DataFrame:
    out = prices.copy()
    fair_parts = []
    key_cols = ["day", "timestamp"]
    for group, products in GROUPS.items():
        pivot = (
            out[out["product"].isin(products)]
            .pivot(index=key_cols, columns="product", values="mid_price")
            .sort_index()
        )
        days = sorted(pivot.index.get_level_values("day").unique())
        for target in products:
            components = [product for product in products if product != target]
            base = pivot[[target] + components].dropna()
            for test_day in days:
                train = base[base.index.get_level_values("day") != test_day]
                test = base[base.index.get_level_values("day") == test_day]
                coef = fit_ols(train[target].to_numpy(dtype=float), train[components].to_numpy(dtype=float))
                fair = predict_ols(coef, test[components].to_numpy(dtype=float))
                fair_parts.append(
                    pd.DataFrame(
                        {
                            "day": test.index.get_level_values("day"),
                            "timestamp": test.index.get_level_values("timestamp"),
                            "product": target,
                            "residual_fair": fair,
                        }
                    )
                )
    fair_frame = pd.concat(fair_parts, ignore_index=True)
    out = out.merge(fair_frame, on=["day", "timestamp", "product"], how="left")
    out["residual_fair_floor"] = np.floor(out["residual_fair"]).astype(float)
    out["residual_fair_ceil"] = np.ceil(out["residual_fair"]).astype(float)
    out["residual_fair_offset"] = out["residual_fair"] - out["mid_price"]
    return out


def future_min(values: np.ndarray, horizon: int) -> np.ndarray:
    arr = pd.Series(values).shift(-1)
    return arr.iloc[::-1].rolling(horizon, min_periods=1).min().iloc[::-1].to_numpy(dtype=float)


def future_max(values: np.ndarray, horizon: int) -> np.ndarray:
    arr = pd.Series(values).shift(-1)
    return arr.iloc[::-1].rolling(horizon, min_periods=1).max().iloc[::-1].to_numpy(dtype=float)


def future_shift(values: np.ndarray, horizon: int) -> np.ndarray:
    return pd.Series(values).shift(-horizon).to_numpy(dtype=float)


def clip_buy_quote(q: np.ndarray, bid: np.ndarray, ask: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(q, bid), ask - 1)


def clip_sell_quote(q: np.ndarray, bid: np.ndarray, ask: np.ndarray) -> np.ndarray:
    return np.maximum(np.minimum(q, ask), bid + 1)


def quote_prices(frame: pd.DataFrame, mode: str, side: str) -> np.ndarray:
    bid = frame["bid_price_1"].to_numpy(dtype=float)
    ask = frame["ask_price_1"].to_numpy(dtype=float)
    if mode == "best_touch":
        q = bid if side == "buy" else ask
    elif mode == "one_tick_inside":
        raw = bid + 1 if side == "buy" else ask - 1
        q = clip_buy_quote(raw, bid, ask) if side == "buy" else clip_sell_quote(raw, bid, ask)
    elif mode == "book_mid":
        raw = frame["book_mid_floor"].to_numpy(dtype=float) if side == "buy" else frame["book_mid_ceil"].to_numpy(dtype=float)
        q = clip_buy_quote(raw, bid, ask) if side == "buy" else clip_sell_quote(raw, bid, ask)
    elif mode == "wall_mid":
        raw = frame["wall_mid_floor"].to_numpy(dtype=float) if side == "buy" else frame["wall_mid_ceil"].to_numpy(dtype=float)
        q = clip_buy_quote(raw, bid, ask) if side == "buy" else clip_sell_quote(raw, bid, ask)
    elif mode == "residual_fair":
        raw = (
            frame["residual_fair_floor"].to_numpy(dtype=float)
            if side == "buy"
            else frame["residual_fair_ceil"].to_numpy(dtype=float)
        )
        q = clip_buy_quote(raw, bid, ask) if side == "buy" else clip_sell_quote(raw, bid, ask)
    else:
        raise ValueError(mode)
    passive = q < ask if side == "buy" else q > bid
    return np.where(passive, q, np.nan)


def aggregate_quote_path(
    frame: pd.DataFrame,
    trades: pd.DataFrame,
    product: str,
    day: int,
) -> list[dict[str, float | int | str]]:
    rows = []
    n = len(frame)
    trade_min = np.full(n, np.nan)
    trade_max = np.full(n, np.nan)
    if not trades.empty:
        ts_to_idx = {int(ts): idx for idx, ts in enumerate(frame["timestamp"].to_numpy(dtype=int))}
        for timestamp, group in trades.groupby("timestamp"):
            idx = ts_to_idx.get(int(timestamp))
            if idx is not None:
                trade_min[idx] = float(group["price"].min())
                trade_max[idx] = float(group["price"].max())

    mid = frame["mid_price"].to_numpy(dtype=float)
    bid = frame["bid_price_1"].to_numpy(dtype=float)
    ask = frame["ask_price_1"].to_numpy(dtype=float)
    group_name = PRODUCT_TO_GROUP[product]

    future_cache = {}
    for horizon in HORIZONS:
        future_cache[horizon] = {
            "mid": future_shift(mid, horizon),
            "bid": future_shift(bid, horizon),
            "ask": future_shift(ask, horizon),
            "trade_min": future_min(trade_min, horizon),
            "trade_max": future_max(trade_max, horizon),
            "book_min_ask": future_min(ask, horizon),
            "book_max_bid": future_max(bid, horizon),
        }

    for mode in QUOTE_MODES:
        for side in ["buy", "sell"]:
            q = quote_prices(frame, mode, side)
            valid_quote = np.isfinite(q)
            if not valid_quote.any():
                continue
            spread_capture = np.where(side == "buy", mid - q, q - mid)
            for horizon in HORIZONS:
                fut = future_cache[horizon]
                future_mid = fut["mid"]
                future_bid = fut["bid"]
                future_ask = fut["ask"]
                valid = valid_quote & np.isfinite(future_mid)
                if side == "buy":
                    trade_fill = fut["trade_min"] <= q
                    book_fill = fut["book_min_ask"] <= q
                    edge = future_mid - q
                    adverse = future_mid - mid
                    cross_liq_edge = future_bid - q
                else:
                    trade_fill = fut["trade_max"] >= q
                    book_fill = fut["book_max_bid"] >= q
                    edge = q - future_mid
                    adverse = mid - future_mid
                    cross_liq_edge = q - future_ask
                trade_fill = valid & np.asarray(trade_fill, dtype=bool)
                book_fill = valid & np.asarray(book_fill, dtype=bool)
                book_or_trade = trade_fill | book_fill
                filled_edge = edge[trade_fill]
                filled_cross = cross_liq_edge[trade_fill]
                rows.append(
                    {
                        "group": group_name,
                        "product": product,
                        "day": int(day),
                        "quote_mode": mode,
                        "side": side,
                        "horizon": int(horizon),
                        "quote_ticks": int(valid.sum()),
                        "trade_fill_count": int(trade_fill.sum()),
                        "book_or_trade_fill_count": int(book_or_trade.sum()),
                        "trade_fill_rate": float(trade_fill.sum() / valid.sum()) if valid.sum() else np.nan,
                        "book_or_trade_fill_rate": float(book_or_trade.sum() / valid.sum()) if valid.sum() else np.nan,
                        "mean_quote_offset_mid": float(np.nanmean(np.where(valid, q - mid, np.nan))),
                        "mean_spread_capture_if_filled": float(np.nanmean(spread_capture[trade_fill]))
                        if trade_fill.any()
                        else np.nan,
                        "mean_adverse_selection_if_filled": float(np.nanmean(adverse[trade_fill]))
                        if trade_fill.any()
                        else np.nan,
                        "mean_edge_if_filled": float(np.nanmean(filled_edge)) if len(filled_edge) else np.nan,
                        "mean_cross_liq_edge_if_filled": float(np.nanmean(filled_cross)) if len(filled_cross) else np.nan,
                        "ev_per_quote": float(np.nansum(np.where(trade_fill, edge, 0.0)) / valid.sum())
                        if valid.sum()
                        else np.nan,
                        "cross_liq_ev_per_quote": float(
                            np.nansum(np.where(trade_fill, cross_liq_edge, 0.0)) / valid.sum()
                        )
                        if valid.sum()
                        else np.nan,
                    }
                )
    return rows


def quote_ev(prices: pd.DataFrame, trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (product, day), frame in prices.groupby(["product", "day"], sort=False):
        print(f"Quote EV {product} day {day}...")
        product_trades = trades[(trades["product"].eq(product)) & (trades["day"].eq(day))]
        rows.extend(aggregate_quote_path(frame.sort_values("timestamp"), product_trades, product, int(day)))
    by_day = pd.DataFrame(rows)
    weighted = []
    group_cols = ["group", "product", "quote_mode", "side", "horizon"]
    for key, frame in by_day.groupby(group_cols, sort=False):
        quote_ticks = frame["quote_ticks"].sum()
        trade_fill_count = frame["trade_fill_count"].sum()
        book_fill_count = frame["book_or_trade_fill_count"].sum()
        weighted.append(
            {
                **dict(zip(group_cols, key)),
                "days": int(frame["day"].nunique()),
                "quote_ticks": int(quote_ticks),
                "trade_fill_count": int(trade_fill_count),
                "book_or_trade_fill_count": int(book_fill_count),
                "trade_fill_rate": float(trade_fill_count / quote_ticks) if quote_ticks else np.nan,
                "book_or_trade_fill_rate": float(book_fill_count / quote_ticks) if quote_ticks else np.nan,
                "mean_edge_if_filled": weighted_mean(frame, "mean_edge_if_filled", "trade_fill_count"),
                "mean_cross_liq_edge_if_filled": weighted_mean(
                    frame, "mean_cross_liq_edge_if_filled", "trade_fill_count"
                ),
                "mean_spread_capture_if_filled": weighted_mean(
                    frame, "mean_spread_capture_if_filled", "trade_fill_count"
                ),
                "mean_adverse_selection_if_filled": weighted_mean(
                    frame, "mean_adverse_selection_if_filled", "trade_fill_count"
                ),
                "ev_per_quote": weighted_mean(frame, "ev_per_quote", "quote_ticks"),
                "cross_liq_ev_per_quote": weighted_mean(frame, "cross_liq_ev_per_quote", "quote_ticks"),
                "positive_edge_days": int((frame["mean_edge_if_filled"] > 0).sum()),
                "positive_cross_liq_days": int((frame["mean_cross_liq_edge_if_filled"] > 0).sum()),
                "min_day_edge_if_filled": float(frame["mean_edge_if_filled"].min()),
                "min_day_cross_liq_edge_if_filled": float(frame["mean_cross_liq_edge_if_filled"].min()),
                "min_day_ev_per_quote": float(frame["ev_per_quote"].min()),
                "cap10_edge_per_full_inventory": float(QTY_CAP * weighted_mean(frame, "mean_edge_if_filled", "trade_fill_count")),
                "cap10_cross_liq_edge_per_full_inventory": float(
                    QTY_CAP * weighted_mean(frame, "mean_cross_liq_edge_if_filled", "trade_fill_count")
                ),
            }
        )
    summary = pd.DataFrame(weighted)
    return by_day, summary


def weighted_mean(frame: pd.DataFrame, value_col: str, weight_col: str) -> float:
    valid = frame[value_col].notna() & frame[weight_col].gt(0)
    if not valid.any():
        return np.nan
    return float(np.average(frame.loc[valid, value_col], weights=frame.loc[valid, weight_col]))


def enrich_trades(prices: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "day",
        "timestamp",
        "product",
        "group",
        "bid_price_1",
        "ask_price_1",
        "mid_price",
        "spread",
        "wall_mid",
        "wall_mid_floor",
        "wall_mid_ceil",
        "book_mid_floor",
        "book_mid_ceil",
        "residual_fair",
        "residual_fair_floor",
        "residual_fair_ceil",
    ]
    out = trades.merge(prices[cols], on=["day", "timestamp", "product", "group"], how="left")
    out["side"] = np.select(
        [out["price"] >= out["ask_price_1"], out["price"] <= out["bid_price_1"]],
        ["buy_at_ask", "sell_at_bid"],
        default="inside_spread",
    )
    out["price_minus_bid"] = out["price"] - out["bid_price_1"]
    out["ask_minus_price"] = out["ask_price_1"] - out["price"]
    out["price_minus_mid"] = out["price"] - out["mid_price"]
    out["price_minus_wall_mid"] = out["price"] - out["wall_mid"]
    out["price_minus_residual_fair"] = out["price"] - out["residual_fair"]
    out["matches_best_touch"] = (out["price"].eq(out["bid_price_1"])) | (out["price"].eq(out["ask_price_1"]))
    out["matches_inside_1"] = (out["price"].eq(out["bid_price_1"] + 1)) | (out["price"].eq(out["ask_price_1"] - 1))
    out["matches_book_mid"] = (out["price"].eq(out["book_mid_floor"])) | (out["price"].eq(out["book_mid_ceil"]))
    out["matches_wall_mid"] = (out["price"].eq(out["wall_mid_floor"])) | (out["price"].eq(out["wall_mid_ceil"]))
    out["matches_residual_fair"] = (out["price"].eq(out["residual_fair_floor"])) | (
        out["price"].eq(out["residual_fair_ceil"])
    )
    return out


def price_offset_tables(enriched: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (group, product), frame in enriched.groupby(["group", "product"], sort=False):
        rows.append(
            {
                "group": group,
                "product": product,
                "trades": int(len(frame)),
                "qty": int(frame["quantity"].sum()),
                "avg_qty": float(frame["quantity"].mean()),
                "top_qty": int(frame["quantity"].value_counts().index[0]),
                "top_qty_share": float(frame["quantity"].value_counts(normalize=True).iloc[0]),
                "best_touch_match_rate": float(frame["matches_best_touch"].mean()),
                "inside_1_match_rate": float(frame["matches_inside_1"].mean()),
                "book_mid_match_rate": float(frame["matches_book_mid"].mean()),
                "wall_mid_match_rate": float(frame["matches_wall_mid"].mean()),
                "residual_fair_match_rate": float(frame["matches_residual_fair"].mean()),
                "mean_price_minus_mid": float(frame["price_minus_mid"].mean()),
                "mean_price_minus_wall_mid": float(frame["price_minus_wall_mid"].mean()),
                "mean_abs_price_minus_residual_fair": float(frame["price_minus_residual_fair"].abs().mean()),
                "inside_spread_rate": float((frame["side"] == "inside_spread").mean()),
            }
        )
    by_product = pd.DataFrame(rows)

    offset_rows = []
    for col in ["price_minus_bid", "ask_minus_price", "price_minus_mid", "price_minus_wall_mid"]:
        counts = (
            enriched.dropna(subset=[col])
            .groupby(["group", col])
            .agg(trades=("price", "size"), qty=("quantity", "sum"))
            .reset_index()
            .rename(columns={col: "offset"})
        )
        counts["offset_type"] = col
        offset_rows.append(counts)
    offsets = pd.concat(offset_rows, ignore_index=True)
    return by_product, offsets.sort_values(["offset_type", "group", "trades"], ascending=[True, True, False])


def synchronized_baskets(enriched: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = (
        enriched.groupby(["day", "timestamp", "group"])
        .agg(
            trades=("product", "size"),
            products=("product", "nunique"),
            qty=("quantity", "sum"),
            quantity_set=("quantity", lambda s: ",".join(map(str, sorted(set(map(int, s)))))),
            side_set=("side", lambda s: ",".join(sorted(set(map(str, s))))),
            best_touch_match_rate=("matches_best_touch", "mean"),
            inside_1_match_rate=("matches_inside_1", "mean"),
            wall_mid_match_rate=("matches_wall_mid", "mean"),
            residual_fair_match_rate=("matches_residual_fair", "mean"),
            mean_price_minus_wall_mid=("price_minus_wall_mid", "mean"),
            mean_abs_price_minus_residual_fair=("price_minus_residual_fair", lambda s: float(np.abs(s).mean())),
        )
        .reset_index()
    )
    events["full_group"] = events["products"].eq(5)
    events["same_qty"] = ~events["quantity_set"].str.contains(",", regex=False)
    full = events[events["full_group"]].copy()
    summary = (
        full.groupby("group")
        .agg(
            full_group_events=("timestamp", "size"),
            same_qty_events=("same_qty", "sum"),
            avg_qty=("qty", "mean"),
            best_touch_match_rate=("best_touch_match_rate", "mean"),
            inside_1_match_rate=("inside_1_match_rate", "mean"),
            wall_mid_match_rate=("wall_mid_match_rate", "mean"),
            residual_fair_match_rate=("residual_fair_match_rate", "mean"),
            mean_abs_price_minus_residual_fair=("mean_abs_price_minus_residual_fair", "mean"),
        )
        .reset_index()
        .sort_values(["full_group_events", "same_qty_events"], ascending=False)
    )
    return events.sort_values(["products", "trades"], ascending=False), summary


def hidden_taker_signatures(
    trade_offsets: pd.DataFrame,
    sync_summary: pd.DataFrame,
    quote_summary: pd.DataFrame,
) -> pd.DataFrame:
    quote_slice = quote_summary[quote_summary["horizon"].eq(20)].copy()
    quote_best = (
        quote_slice.sort_values(["product", "trade_fill_rate"], ascending=[True, False])
        .groupby(["group", "product"], as_index=False)
        .head(1)
        .rename(
            columns={
                "quote_mode": "best_fill_quote_mode_h20",
                "side": "best_fill_side_h20",
                "trade_fill_rate": "best_trade_fill_rate_h20",
                "mean_edge_if_filled": "best_mean_edge_if_filled_h20",
                "mean_cross_liq_edge_if_filled": "best_cross_liq_edge_if_filled_h20",
            }
        )
    )
    out = trade_offsets.merge(
        quote_best[
            [
                "group",
                "product",
                "best_fill_quote_mode_h20",
                "best_fill_side_h20",
                "best_trade_fill_rate_h20",
                "best_mean_edge_if_filled_h20",
                "best_cross_liq_edge_if_filled_h20",
            ]
        ],
        on=["group", "product"],
        how="left",
    )
    group_sync = sync_summary[["group", "full_group_events", "same_qty_events"]]
    out = out.merge(group_sync, on="group", how="left")
    match_cols = [
        "best_touch_match_rate",
        "inside_1_match_rate",
        "book_mid_match_rate",
        "wall_mid_match_rate",
        "residual_fair_match_rate",
    ]
    out["max_quote_match_rate"] = out[match_cols].max(axis=1)
    out["hidden_taker_score"] = (
        2.0 * out["top_qty_share"]
        + 1.5 * out["max_quote_match_rate"]
        + 0.5 * out["inside_spread_rate"]
        + 0.002 * out["full_group_events"].fillna(0)
        + 0.003 * out["same_qty_events"].fillna(0)
    )
    return out.sort_values("hidden_taker_score", ascending=False)


def top_candidates(summary: pd.DataFrame) -> pd.DataFrame:
    stable = summary[
        (summary["days"] == 3)
        & (summary["trade_fill_count"] >= 20)
        & (summary["positive_edge_days"] == 3)
        & (summary["mean_edge_if_filled"] > 0)
    ].copy()
    stable["score"] = (
        stable["mean_edge_if_filled"]
        + 10.0 * stable["ev_per_quote"]
        + 0.5 * stable["mean_cross_liq_edge_if_filled"].fillna(-100)
    )
    return stable.sort_values(["score", "trade_fill_count"], ascending=False)


def group_quote_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    frame = summary[summary["horizon"].isin([20, 100, 500])].copy()
    out = (
        frame.groupby(["group", "quote_mode", "horizon"])
        .agg(
            products=("product", "nunique"),
            quote_ticks=("quote_ticks", "sum"),
            trade_fill_count=("trade_fill_count", "sum"),
            trade_fill_rate=("trade_fill_rate", "mean"),
            mean_edge_if_filled=("mean_edge_if_filled", "mean"),
            mean_cross_liq_edge_if_filled=("mean_cross_liq_edge_if_filled", "mean"),
            ev_per_quote=("ev_per_quote", "mean"),
            positive_product_sides=("positive_edge_days", lambda s: int((s == 3).sum())),
        )
        .reset_index()
        .sort_values(["horizon", "ev_per_quote"], ascending=[True, False])
    )
    return out


def top_product_anchor_comparison(summary: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    top_products = list(dict.fromkeys(candidates.head(10)["product"].tolist()))
    cross = summary[summary["trade_fill_count"] >= 20].sort_values(
        "mean_cross_liq_edge_if_filled", ascending=False
    )
    for product in cross.head(5)["product"].tolist():
        if product not in top_products:
            top_products.append(product)
    frame = summary[
        summary["product"].isin(top_products[:8])
        & summary["quote_mode"].isin(["book_mid", "wall_mid", "residual_fair"])
    ].copy()
    out = (
        frame.groupby(["group", "product", "quote_mode", "horizon"])
        .agg(
            sides=("side", "nunique"),
            quote_ticks=("quote_ticks", "sum"),
            trade_fill_count=("trade_fill_count", "sum"),
            trade_fill_rate=("trade_fill_rate", "mean"),
            mean_edge_if_filled=("mean_edge_if_filled", "mean"),
            mean_cross_liq_edge_if_filled=("mean_cross_liq_edge_if_filled", "mean"),
            ev_per_quote=("ev_per_quote", "mean"),
            positive_side_days=("positive_edge_days", "sum"),
            positive_cross_side_days=("positive_cross_liq_days", "sum"),
        )
        .reset_index()
        .sort_values(["product", "horizon", "ev_per_quote"], ascending=[True, True, False])
    )
    return out


def md_table(frame: pd.DataFrame, columns: list[str], n: int = 15) -> str:
    if frame.empty:
        return "No rows."
    return frame.head(n)[columns].round(6).to_markdown(index=False)


def write_report(
    by_day: pd.DataFrame,
    summary: pd.DataFrame,
    candidates: pd.DataFrame,
    trade_offsets: pd.DataFrame,
    hidden: pd.DataFrame,
    sync_summary: pd.DataFrame,
    group_compare: pd.DataFrame,
    product_anchor_compare: pd.DataFrame,
) -> None:
    top = candidates.head(12)
    cross_ok = candidates[candidates["mean_cross_liq_edge_if_filled"] > 0].head(12)
    stable_cross = summary[
        (summary["trade_fill_count"] >= 20)
        & (summary["positive_cross_liq_days"] == 3)
        & (summary["mean_cross_liq_edge_if_filled"] > 0)
    ]
    best_avg_cross = summary[summary["trade_fill_count"] >= 20].sort_values(
        "mean_cross_liq_edge_if_filled", ascending=False
    ).head(1)
    anchor_compare = group_compare[
        group_compare["quote_mode"].isin(["book_mid", "wall_mid", "residual_fair"]) & group_compare["horizon"].eq(100)
    ].sort_values("ev_per_quote", ascending=False)
    product_anchor_slice = product_anchor_compare[
        product_anchor_compare["horizon"].isin([1, 20, 100])
    ].sort_values(["product", "horizon", "ev_per_quote"], ascending=[True, True, False])
    high_fill_negative = summary[
        (summary["horizon"].eq(20))
        & (summary["trade_fill_count"] >= 100)
        & (summary["trade_fill_rate"] >= 0.02)
        & (summary["mean_edge_if_filled"] < 0)
    ].sort_values("mean_edge_if_filled")

    best = top.iloc[0] if not top.empty else None
    best_cross = cross_ok.iloc[0] if not cross_ok.empty else None
    avg_cross = best_avg_cross.iloc[0] if not best_avg_cross.empty else None
    best_hidden = hidden.iloc[0] if not hidden.empty else None
    full_events = int(sync_summary["full_group_events"].sum()) if not sync_summary.empty else 0
    same_qty_events = int(sync_summary["same_qty_events"].sum()) if not sync_summary.empty else 0
    stable_cross_n = int(len(stable_cross))
    overall_touch_match = float(trade_offsets["best_touch_match_rate"].mean()) if not trade_offsets.empty else np.nan

    lines = [
        "# Round 5 Passive Fill / Hidden Taker Research",
        "",
        "Scope: Round 5 prices and public trades for days 2, 3, and 4 across all 50 products. Quotes are evaluated at `best_touch`, `one_tick_inside`, `book_mid`, `wall_mid`, and leave-one-day-out `residual_fair`. Conservative fills require a future public trade through the submitted quote; `book_or_trade` fill columns also count future top-of-book movement through the quote.",
        "",
        "PnL decomposition: for a buy fill, `edge = future_mid - quote`; for a sell fill, `edge = quote - future_mid`. `spread_capture` is quote-vs-current-mid and `adverse_selection` is current-mid-vs-future-mid. `cross_liq_edge` marks forced liquidation at the future opposite touch, which is the relevant zero-edge / 10-cap stress check.",
        "",
        "## Headline Findings",
        "",
    ]
    if best is not None:
        lines.append(
            f"- Best conservative filled-edge row is **{best['product']} {best['side']} {best['quote_mode']} h{int(best['horizon'])}**: fill_rate {best['trade_fill_rate']:.6f}, mean_edge_if_filled {best['mean_edge_if_filled']:.6f}, EV/quote {best['ev_per_quote']:.6f}, positive days {int(best['positive_edge_days'])}/3, fills {int(best['trade_fill_count'])}."
        )
        lines.append(
            f"- The same row fails 10-cap forced liquidation: cross_liq_edge {best['mean_cross_liq_edge_if_filled']:.6f}, or {best['cap10_cross_liq_edge_per_full_inventory']:.6f} for a full 10-lot inventory."
        )
    if stable_cross_n == 0:
        lines.append("- No quote row with at least 20 conservative fills has positive forced cross-liquidation edge on all three days.")
    if avg_cross is not None:
        lines.append(
            f"- Best average forced-liquidation row is **{avg_cross['product']} {avg_cross['side']} {avg_cross['quote_mode']} h{int(avg_cross['horizon'])}**: cross_liq_edge {avg_cross['mean_cross_liq_edge_if_filled']:.6f}, fill_rate {avg_cross['trade_fill_rate']:.6f}, but only {int(avg_cross['positive_cross_liq_days'])}/3 positive days."
        )
    if best_cross is not None:
        lines.append(
            f"- Best candidate that still survives forced opposite-touch liquidation is **{best_cross['product']} {best_cross['side']} {best_cross['quote_mode']} h{int(best_cross['horizon'])}**: cross_liq_edge {best_cross['mean_cross_liq_edge_if_filled']:.6f}, cap-10 cross-liq edge {best_cross['cap10_cross_liq_edge_per_full_inventory']:.6f}, fill_rate {best_cross['trade_fill_rate']:.6f}."
        )
    if best_hidden is not None:
        lines.append(
            f"- Hidden-taker pattern is broad rather than product-specific: average best-touch match rate is {overall_touch_match:.6f}; the top repeated size is usually {int(best_hidden['top_qty'])} with share {best_hidden['top_qty_share']:.6f}. Wall-mid and residual-fair matches are sparse."
        )
    lines.extend(
        [
            f"- Synchronized basket prints are common but not directly monetizable by passive quotes alone: {full_events} full-group same-timestamp events, including {same_qty_events} same-quantity events.",
            "- Explicit rejection: positive midpoint markouts are not enough under the 10-position cap. Rows with positive `mean_edge_if_filled` but negative `mean_cross_liq_edge_if_filled` can accumulate inventory whose forced flattening gives back the apparent spread capture.",
            "",
            "## Top Passive Quote Candidates",
            "",
            md_table(
                top,
                [
                    "group",
                    "product",
                    "quote_mode",
                    "side",
                    "horizon",
                    "trade_fill_rate",
                    "mean_edge_if_filled",
                    "mean_cross_liq_edge_if_filled",
                    "ev_per_quote",
                    "positive_edge_days",
                    "trade_fill_count",
                ],
                n=20,
            ),
            "",
            "## Candidates Surviving Forced Cross Liquidation",
            "",
            md_table(
                cross_ok,
                [
                    "group",
                    "product",
                    "quote_mode",
                    "side",
                    "horizon",
                    "trade_fill_rate",
                    "mean_edge_if_filled",
                    "mean_cross_liq_edge_if_filled",
                    "cap10_cross_liq_edge_per_full_inventory",
                    "trade_fill_count",
                ],
                n=20,
            ),
            "",
            "## Anchor Comparison Around Book Mid / Wall Mid / Residual Fair",
            "",
            md_table(
                anchor_compare,
                [
                    "group",
                    "quote_mode",
                    "horizon",
                    "trade_fill_rate",
                    "mean_edge_if_filled",
                    "mean_cross_liq_edge_if_filled",
                    "ev_per_quote",
                    "positive_product_sides",
                ],
                n=30,
            ),
            "",
            "## Top Product Anchor Comparison",
            "",
            md_table(
                product_anchor_slice,
                [
                    "group",
                    "product",
                    "quote_mode",
                    "horizon",
                    "trade_fill_rate",
                    "mean_edge_if_filled",
                    "mean_cross_liq_edge_if_filled",
                    "ev_per_quote",
                    "positive_side_days",
                    "positive_cross_side_days",
                ],
                n=45,
            ),
            "",
            "## Hidden-Taker Signature Watchlist",
            "",
            md_table(
                hidden,
                [
                    "group",
                    "product",
                    "trades",
                    "top_qty",
                    "top_qty_share",
                    "best_touch_match_rate",
                    "inside_1_match_rate",
                    "wall_mid_match_rate",
                    "residual_fair_match_rate",
                    "hidden_taker_score",
                ],
                n=20,
            ),
            "",
            "## Synchronized Basket Fills",
            "",
            md_table(
                sync_summary,
                [
                    "group",
                    "full_group_events",
                    "same_qty_events",
                    "avg_qty",
                    "best_touch_match_rate",
                    "inside_1_match_rate",
                    "wall_mid_match_rate",
                    "residual_fair_match_rate",
                ],
                n=15,
            ),
            "",
            "## Explicit Rejections",
            "",
            "High fill-rate rows with negative filled edge at h20 are adverse-selection traps:",
            "",
            md_table(
                high_fill_negative,
                [
                    "group",
                    "product",
                    "quote_mode",
                    "side",
                    "trade_fill_rate",
                    "mean_edge_if_filled",
                    "mean_cross_liq_edge_if_filled",
                    "trade_fill_count",
                ],
                n=20,
            ),
            "",
            "CSV outputs: `18_quote_ev_by_day.csv`, `18_quote_ev_summary.csv`, `18_top_quote_candidates.csv`, `18_trade_price_offsets.csv`, `18_trade_offset_histogram.csv`, `18_sync_basket_events.csv`, `18_sync_basket_summary.csv`, `18_hidden_taker_signatures.csv`, `18_group_quote_anchor_comparison.csv`, and `18_top_product_anchor_comparison.csv`.",
        ]
    )
    (OUT_DIR / "18_passive_fill_hidden_taker.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = add_residual_fair(read_prices())
    trades = read_trades()

    by_day, summary = quote_ev(prices, trades)
    enriched = enrich_trades(prices, trades)
    trade_offsets, offset_hist = price_offset_tables(enriched)
    sync_events, sync_summary = synchronized_baskets(enriched)
    hidden = hidden_taker_signatures(trade_offsets, sync_summary, summary)
    candidates = top_candidates(summary)
    group_compare = group_quote_comparison(summary)
    product_anchor_compare = top_product_anchor_comparison(summary, candidates)

    by_day.to_csv(OUT_DIR / "18_quote_ev_by_day.csv", index=False)
    summary.to_csv(OUT_DIR / "18_quote_ev_summary.csv", index=False)
    candidates.to_csv(OUT_DIR / "18_top_quote_candidates.csv", index=False)
    trade_offsets.to_csv(OUT_DIR / "18_trade_price_offsets.csv", index=False)
    offset_hist.to_csv(OUT_DIR / "18_trade_offset_histogram.csv", index=False)
    sync_events.to_csv(OUT_DIR / "18_sync_basket_events.csv", index=False)
    sync_summary.to_csv(OUT_DIR / "18_sync_basket_summary.csv", index=False)
    hidden.to_csv(OUT_DIR / "18_hidden_taker_signatures.csv", index=False)
    group_compare.to_csv(OUT_DIR / "18_group_quote_anchor_comparison.csv", index=False)
    product_anchor_compare.to_csv(OUT_DIR / "18_top_product_anchor_comparison.csv", index=False)
    write_report(
        by_day,
        summary,
        candidates,
        trade_offsets,
        hidden,
        sync_summary,
        group_compare,
        product_anchor_compare,
    )

    print("Wrote notebooks/round5/18_passive_fill_hidden_taker.md")
    print(candidates.head(10).round(6).to_string(index=False))


if __name__ == "__main__":
    main()
