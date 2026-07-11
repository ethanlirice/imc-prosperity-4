from collections import Counter, deque
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")

DAYS = [2, 3, 4]
HORIZONS = [1, 5, 20, 100, 500]
PRICE_LEVELS = [1, 2, 3]
POPULAR_WINDOW = 1_000
POPULAR_MIN_HISTORY = 200

TICK = 1.0
MIN_DAY_EVENTS = 25
MIN_TOTAL_EVENTS = 100


def read_prices() -> pd.DataFrame:
    frames = []
    for day in DAYS:
        path = DATA_DIR / f"prices_round_5_day_{day}.csv"
        frame = pd.read_csv(path, sep=";")
        frames.append(frame)
    prices = pd.concat(frames, ignore_index=True)
    prices = prices.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    return prices


def product_group(product: str) -> str:
    parts = product.split("_")
    if product.startswith("GALAXY_SOUNDS_"):
        return "GALAXY_SOUNDS"
    if product.startswith("SLEEP_POD_"):
        return "SLEEP_POD"
    if product.startswith("OXYGEN_SHAKE_"):
        return "OXYGEN_SHAKE"
    if product.startswith("UV_VISOR_"):
        return "UV_VISOR"
    return parts[0]


def max_price_by_volume(prices: pd.DataFrame, price_cols: list[str], volume_cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
    volume = prices[volume_cols].fillna(-1).to_numpy(dtype=float)
    quote_price = prices[price_cols].to_numpy(dtype=float)
    max_idx = np.argmax(volume, axis=1)
    rows = np.arange(len(prices))
    return quote_price[rows, max_idx], max_idx + 1


def add_wall_features(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    bid_prices = [f"bid_price_{level}" for level in PRICE_LEVELS]
    bid_volumes = [f"bid_volume_{level}" for level in PRICE_LEVELS]
    ask_prices = [f"ask_price_{level}" for level in PRICE_LEVELS]
    ask_volumes = [f"ask_volume_{level}" for level in PRICE_LEVELS]

    prices["bid_wall_price"], prices["bid_wall_level"] = max_price_by_volume(prices, bid_prices, bid_volumes)
    prices["ask_wall_price"], prices["ask_wall_level"] = max_price_by_volume(prices, ask_prices, ask_volumes)
    prices["wall_mid"] = (prices["bid_wall_price"] + prices["ask_wall_price"]) / 2.0
    prices["wall_mid_dev"] = prices["wall_mid"] - prices["mid_price"]

    bid_depth = prices[bid_volumes].fillna(0).sum(axis=1)
    ask_depth = prices[ask_volumes].fillna(0).sum(axis=1)
    prices["bid_depth"] = bid_depth
    prices["ask_depth"] = ask_depth
    prices["book_depth"] = bid_depth + ask_depth
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]

    bid_vwap_num = sum(prices[f"bid_price_{level}"].fillna(0) * prices[f"bid_volume_{level}"].fillna(0) for level in PRICE_LEVELS)
    ask_vwap_num = sum(prices[f"ask_price_{level}"].fillna(0) * prices[f"ask_volume_{level}"].fillna(0) for level in PRICE_LEVELS)
    prices["depth_vwap_mid"] = ((bid_vwap_num / bid_depth) + (ask_vwap_num / ask_depth)) / 2.0
    prices["depth_vwap_dev"] = prices["depth_vwap_mid"] - prices["mid_price"]
    return prices


def rolling_popular_mid_for_group(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("timestamp").copy()
    bid_counter: Counter[int] = Counter()
    ask_counter: Counter[int] = Counter()
    bid_queue: deque[tuple[int, int, int]] = deque()
    ask_queue: deque[tuple[int, int, int]] = deque()
    pop_bid = np.full(len(group), np.nan)
    pop_ask = np.full(len(group), np.nan)

    bid_price_arr = group[[f"bid_price_{level}" for level in PRICE_LEVELS]].to_numpy(dtype=float)
    ask_price_arr = group[[f"ask_price_{level}" for level in PRICE_LEVELS]].to_numpy(dtype=float)
    bid_vol_arr = group[[f"bid_volume_{level}" for level in PRICE_LEVELS]].fillna(0).to_numpy(dtype=float)
    ask_vol_arr = group[[f"ask_volume_{level}" for level in PRICE_LEVELS]].fillna(0).to_numpy(dtype=float)

    def best_price(counter: Counter[int], side: str) -> float:
        if not counter:
            return np.nan
        if side == "bid":
            return float(max(counter.items(), key=lambda item: (item[1], item[0]))[0])
        return float(max(counter.items(), key=lambda item: (item[1], -item[0]))[0])

    for idx in range(len(group)):
        while bid_queue and bid_queue[0][0] <= idx - POPULAR_WINDOW:
            _, price, volume = bid_queue.popleft()
            bid_counter[price] -= volume
            if bid_counter[price] <= 0:
                del bid_counter[price]
        while ask_queue and ask_queue[0][0] <= idx - POPULAR_WINDOW:
            _, price, volume = ask_queue.popleft()
            ask_counter[price] -= volume
            if ask_counter[price] <= 0:
                del ask_counter[price]

        if idx >= POPULAR_MIN_HISTORY:
            pop_bid[idx] = best_price(bid_counter, "bid")
            pop_ask[idx] = best_price(ask_counter, "ask")

        for level_idx in range(len(PRICE_LEVELS)):
            bid_price = bid_price_arr[idx, level_idx]
            bid_volume = bid_vol_arr[idx, level_idx]
            if np.isfinite(bid_price) and bid_volume > 0:
                price = int(round(bid_price))
                volume = int(round(bid_volume))
                bid_counter[price] += volume
                bid_queue.append((idx, price, volume))

            ask_price = ask_price_arr[idx, level_idx]
            ask_volume = ask_vol_arr[idx, level_idx]
            if np.isfinite(ask_price) and ask_volume > 0:
                price = int(round(ask_price))
                volume = int(round(ask_volume))
                ask_counter[price] += volume
                ask_queue.append((idx, price, volume))

    group["popular_bid_price"] = pop_bid
    group["popular_ask_price"] = pop_ask
    group["popular_mid"] = (group["popular_bid_price"] + group["popular_ask_price"]) / 2.0
    group["popular_mid_dev"] = group["popular_mid"] - group["mid_price"]
    return group


def add_popular_features(prices: pd.DataFrame) -> pd.DataFrame:
    print("Computing trailing popular quote levels...")
    frames = []
    for _, group in prices.groupby(["product", "day"], sort=False):
        frames.append(rolling_popular_mid_for_group(group))
    return pd.concat(frames, ignore_index=True).sort_values(["product", "day", "timestamp"]).reset_index(drop=True)


def mode_with_share(values: pd.Series) -> tuple[float, float]:
    clean = values.dropna()
    if clean.empty:
        return np.nan, np.nan
    counts = clean.value_counts()
    return float(counts.index[0]), float(counts.iloc[0] / len(clean))


def top_sizes(values: pd.Series, n: int = 3) -> str:
    clean = values.dropna()
    if clean.empty:
        return ""
    counts = clean.value_counts().head(n)
    return ",".join(f"{int(size)}:{count / len(clean):.3f}" for size, count in counts.items())


def summarize_microstructure(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    volume_cols = [f"{side}_volume_{level}" for side in ["bid", "ask"] for level in PRICE_LEVELS]
    for (product, day), group in prices.groupby(["product", "day"], sort=True):
        flat_volume = pd.Series(group[volume_cols].to_numpy(dtype=float).ravel()).dropna()
        dominant_size, dominant_size_share = mode_with_share(flat_volume)
        top_bid_size, top_bid_size_share = mode_with_share(group["bid_volume_1"])
        top_ask_size, top_ask_size_share = mode_with_share(group["ask_volume_1"])
        max_any_prices = []
        for _, row in group.iterrows():
            candidates = []
            for side in ["bid", "ask"]:
                for level in PRICE_LEVELS:
                    price = row[f"{side}_price_{level}"]
                    volume = row[f"{side}_volume_{level}"]
                    if pd.notna(price) and pd.notna(volume):
                        candidates.append((float(volume), float(price)))
            if candidates:
                max_any_prices.append(max(candidates, key=lambda item: (item[0], -abs(item[1] - row["mid_price"])))[1])
        max_volume_price, max_volume_price_share = mode_with_share(pd.Series(max_any_prices))
        rows.append(
            {
                "product": product,
                "group": product_group(product),
                "day": int(day),
                "obs": int(len(group)),
                "avg_mid": group["mid_price"].mean(),
                "avg_spread": group["spread"].mean(),
                "avg_book_depth": group["book_depth"].mean(),
                "avg_bid_depth": group["bid_depth"].mean(),
                "avg_ask_depth": group["ask_depth"].mean(),
                "dominant_quote_size": dominant_size,
                "dominant_quote_size_share": dominant_size_share,
                "top_quote_sizes": top_sizes(flat_volume),
                "top_bid_size": top_bid_size,
                "top_bid_size_share": top_bid_size_share,
                "top_ask_size": top_ask_size,
                "top_ask_size_share": top_ask_size_share,
                "symmetric_top_size_share": (group["bid_volume_1"] == group["ask_volume_1"]).mean(),
                "bid_wall_level1_share": (group["bid_wall_level"] == 1).mean(),
                "ask_wall_level1_share": (group["ask_wall_level"] == 1).mean(),
                "bid_wall_price_mode": mode_with_share(group["bid_wall_price"])[0],
                "ask_wall_price_mode": mode_with_share(group["ask_wall_price"])[0],
                "max_volume_price_mode": max_volume_price,
                "max_volume_price_share": max_volume_price_share,
                "wall_dev_mean": group["wall_mid_dev"].mean(),
                "wall_dev_abs_mean": group["wall_mid_dev"].abs().mean(),
                "wall_dev_nonzero_share": (group["wall_mid_dev"].abs() >= TICK).mean(),
                "popular_dev_abs_mean": group["popular_mid_dev"].abs().mean(),
                "popular_dev_nonzero_share": (group["popular_mid_dev"].abs() >= TICK).mean(),
                "depth_vwap_dev_abs_mean": group["depth_vwap_dev"].abs().mean(),
            }
        )
    return pd.DataFrame(rows)


def markout_rows(prices: pd.DataFrame) -> pd.DataFrame:
    fair_defs = [
        ("wall_mid", "wall_mid"),
        ("popular_mid", "popular_mid"),
        ("depth_vwap_mid", "depth_vwap_mid"),
    ]
    rows = []
    for (product, day), group in prices.groupby(["product", "day"], sort=True):
        group = group.sort_values("timestamp")
        mid = group["mid_price"].to_numpy(dtype=float)
        spread = group["spread"].to_numpy(dtype=float)
        bid = group["bid_price_1"].to_numpy(dtype=float)
        ask = group["ask_price_1"].to_numpy(dtype=float)
        for fair_name, fair_col in fair_defs:
            fair = group[fair_col].to_numpy(dtype=float)
            signal = fair - mid
            for horizon in HORIZONS:
                future_mid = np.full(len(group), np.nan)
                future_mid[:-horizon] = mid[horizon:]
                future_return = future_mid - mid
                valid = np.isfinite(signal) & np.isfinite(future_return) & (np.abs(signal) >= TICK)
                if valid.any():
                    signed_markout = np.sign(signal[valid]) * future_return[valid]
                    sig_valid = signal[valid]
                    ret_valid = future_return[valid]
                    corr = np.corrcoef(sig_valid, ret_valid)[0, 1] if np.std(sig_valid) > 0 and np.std(ret_valid) > 0 else np.nan
                    beta = np.dot(sig_valid, ret_valid) / np.dot(sig_valid, sig_valid) if np.dot(sig_valid, sig_valid) > 0 else np.nan
                    signed_std = signed_markout.std(ddof=1) if len(signed_markout) > 1 else np.nan
                    signed_t = signed_markout.mean() / (signed_std / np.sqrt(len(signed_markout))) if signed_std and signed_std > 0 else np.nan
                else:
                    signed_markout = np.array([])
                    corr = np.nan
                    beta = np.nan
                    signed_t = np.nan

                cross_buy = signal > spread / 2.0
                cross_sell = signal < -spread / 2.0
                cross_valid = np.isfinite(future_mid) & (cross_buy | cross_sell)
                cross_edge = np.where(cross_buy, future_mid - ask, np.where(cross_sell, bid - future_mid, np.nan))
                cross_edge_valid = cross_edge[cross_valid]

                passive_valid = valid
                passive_edge = np.where(signal > 0, future_mid - bid, np.where(signal < 0, ask - future_mid, np.nan))
                passive_edge_valid = passive_edge[passive_valid]

                rows.append(
                    {
                        "product": product,
                        "group": product_group(product),
                        "day": int(day),
                        "fair": fair_name,
                        "horizon": int(horizon),
                        "active_events": int(valid.sum()),
                        "mean_abs_signal": float(np.nanmean(np.abs(signal[valid]))) if valid.any() else np.nan,
                        "signal_return_corr": corr,
                        "signal_return_beta": beta,
                        "signed_mid_markout_mean": float(signed_markout.mean()) if len(signed_markout) else np.nan,
                        "signed_mid_markout_t": signed_t,
                        "signed_mid_markout_win_rate": float((signed_markout > 0).mean()) if len(signed_markout) else np.nan,
                        "cross_events": int(cross_valid.sum()),
                        "cross_edge_mean": float(np.nanmean(cross_edge_valid)) if len(cross_edge_valid) else np.nan,
                        "cross_edge_total": float(np.nansum(cross_edge_valid)) if len(cross_edge_valid) else 0.0,
                        "cross_win_rate": float((cross_edge_valid > 0).mean()) if len(cross_edge_valid) else np.nan,
                        "passive_events": int(passive_valid.sum()),
                        "passive_edge_mean": float(np.nanmean(passive_edge_valid)) if len(passive_edge_valid) else np.nan,
                        "passive_edge_total": float(np.nansum(passive_edge_valid)) if len(passive_edge_valid) else 0.0,
                        "passive_win_rate": float((passive_edge_valid > 0).mean()) if len(passive_edge_valid) else np.nan,
                        "avg_half_spread_active": float(np.nanmean(spread[valid] / 2.0)) if valid.any() else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def aggregate_validation(markouts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["product", "group", "fair", "horizon"]
    for key, group in markouts.groupby(keys, sort=True):
        active_days = group[group["active_events"] >= MIN_DAY_EVENTS]
        cross_days = group[group["cross_events"] >= MIN_DAY_EVENTS]
        passive_days = group[group["passive_events"] >= MIN_DAY_EVENTS]
        total_active = int(group["active_events"].sum())
        total_cross = int(group["cross_events"].sum())
        total_passive = int(group["passive_events"].sum())

        def weighted_mean(col: str, weight_col: str) -> float:
            valid = group[col].notna() & (group[weight_col] > 0)
            if not valid.any():
                return np.nan
            return float(np.average(group.loc[valid, col], weights=group.loc[valid, weight_col]))

        rows.append(
            {
                "product": key[0],
                "group": key[1],
                "fair": key[2],
                "horizon": key[3],
                "active_events": total_active,
                "active_days": int((group["active_events"] >= MIN_DAY_EVENTS).sum()),
                "positive_markout_days": int((active_days["signed_mid_markout_mean"] > 0).sum()),
                "min_day_signed_mid_markout": float(active_days["signed_mid_markout_mean"].min()) if len(active_days) else np.nan,
                "signed_mid_markout_mean": weighted_mean("signed_mid_markout_mean", "active_events"),
                "signed_mid_markout_win_rate": weighted_mean("signed_mid_markout_win_rate", "active_events"),
                "signal_return_corr": weighted_mean("signal_return_corr", "active_events"),
                "cross_events": total_cross,
                "cross_days": int((group["cross_events"] >= MIN_DAY_EVENTS).sum()),
                "positive_cross_days": int((cross_days["cross_edge_mean"] > 0).sum()),
                "min_day_cross_edge": float(cross_days["cross_edge_mean"].min()) if len(cross_days) else np.nan,
                "cross_edge_mean": weighted_mean("cross_edge_mean", "cross_events"),
                "cross_win_rate": weighted_mean("cross_win_rate", "cross_events"),
                "passive_events": total_passive,
                "passive_days": int((group["passive_events"] >= MIN_DAY_EVENTS).sum()),
                "positive_passive_days": int((passive_days["passive_edge_mean"] > 0).sum()),
                "min_day_passive_edge": float(passive_days["passive_edge_mean"].min()) if len(passive_days) else np.nan,
                "passive_edge_mean": weighted_mean("passive_edge_mean", "passive_events"),
                "passive_win_rate": weighted_mean("passive_win_rate", "passive_events"),
                "avg_half_spread_active": weighted_mean("avg_half_spread_active", "active_events"),
            }
        )
    validation = pd.DataFrame(rows)
    validation["robust_markout"] = (
        (validation["active_events"] >= MIN_TOTAL_EVENTS)
        & (validation["active_days"] == 3)
        & (validation["positive_markout_days"] == 3)
        & (validation["min_day_signed_mid_markout"] > 0)
    )
    validation["robust_cross"] = (
        (validation["cross_events"] >= MIN_TOTAL_EVENTS)
        & (validation["cross_days"] == 3)
        & (validation["positive_cross_days"] == 3)
        & (validation["min_day_cross_edge"] > 0)
    )
    validation["robust_passive"] = (
        (validation["passive_events"] >= MIN_TOTAL_EVENTS)
        & (validation["passive_days"] == 3)
        & (validation["positive_passive_days"] == 3)
        & (validation["min_day_passive_edge"] > 0)
    )
    validation["robust_candidate"] = validation["robust_markout"] & (validation["robust_cross"] | validation["robust_passive"])
    return validation.sort_values(
        ["robust_candidate", "signed_mid_markout_mean", "cross_edge_mean", "passive_edge_mean"],
        ascending=[False, False, False, False],
    )


def aggregate_by_fair(markouts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (fair, horizon), group in markouts.groupby(["fair", "horizon"], sort=True):
        active = group[group["active_events"] > 0]
        cross = group[group["cross_events"] > 0]
        passive = group[group["passive_events"] > 0]

        def wavg(frame: pd.DataFrame, col: str, weight_col: str) -> float:
            valid = frame[col].notna() & (frame[weight_col] > 0)
            if not valid.any():
                return np.nan
            return float(np.average(frame.loc[valid, col], weights=frame.loc[valid, weight_col]))

        rows.append(
            {
                "fair": fair,
                "horizon": int(horizon),
                "active_events": int(active["active_events"].sum()),
                "signed_mid_markout_mean": wavg(active, "signed_mid_markout_mean", "active_events"),
                "signed_mid_markout_win_rate": wavg(active, "signed_mid_markout_win_rate", "active_events"),
                "positive_markout_day_products": int((active["signed_mid_markout_mean"] > 0).sum()),
                "tested_day_products": int(len(active)),
                "cross_events": int(cross["cross_events"].sum()),
                "cross_edge_mean": wavg(cross, "cross_edge_mean", "cross_events"),
                "cross_win_rate": wavg(cross, "cross_win_rate", "cross_events"),
                "passive_events": int(passive["passive_events"].sum()),
                "passive_edge_mean": wavg(passive, "passive_edge_mean", "passive_events"),
                "passive_win_rate": wavg(passive, "passive_win_rate", "passive_events"),
            }
        )
    return pd.DataFrame(rows).sort_values(["fair", "horizon"])


def fmt(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.{digits}f}"


def write_report(
    product_summary: pd.DataFrame,
    markouts: pd.DataFrame,
    validation: pd.DataFrame,
    fair_summary: pd.DataFrame,
) -> None:
    report_path = OUT_DIR / "16_wall_mid_mm.md"
    robust = validation[validation["robust_candidate"]].copy()
    robust = robust.sort_values(["signed_mid_markout_mean", "cross_edge_mean", "passive_edge_mean"], ascending=False)
    wall_best = validation[(validation["fair"] == "wall_mid") & (validation["robust_candidate"])].head(15)
    rejects = validation[~validation["robust_candidate"]].copy()
    one_day = rejects[
        (rejects["active_days"] == 3)
        & (rejects["positive_markout_days"].between(1, 2))
        & (rejects["active_events"] >= MIN_TOTAL_EVENTS)
    ].sort_values("signed_mid_markout_mean", ascending=False).head(12)
    strongest_rejects = rejects.sort_values("signed_mid_markout_mean", ascending=False).head(12)
    micro_top = (
        product_summary.groupby(["product", "group"], as_index=False)
        .agg(
            avg_spread=("avg_spread", "mean"),
            avg_book_depth=("avg_book_depth", "mean"),
            wall_dev_abs_mean=("wall_dev_abs_mean", "mean"),
            wall_dev_nonzero_share=("wall_dev_nonzero_share", "mean"),
            bid_wall_level1_share=("bid_wall_level1_share", "mean"),
            ask_wall_level1_share=("ask_wall_level1_share", "mean"),
            dominant_quote_size=("dominant_quote_size", lambda x: x.mode().iloc[0]),
            dominant_quote_size_share=("dominant_quote_size_share", "mean"),
        )
        .sort_values(["wall_dev_abs_mean", "wall_dev_nonzero_share"], ascending=False)
        .head(15)
    )
    fair_lines = []
    for _, row in fair_summary.iterrows():
        fair_lines.append(
            f"| {row['fair']} | {int(row['horizon'])} | {int(row['active_events'])} | "
            f"{fmt(row['signed_mid_markout_mean'])} | {fmt(row['signed_mid_markout_win_rate'], 4)} | "
            f"{int(row['cross_events'])} | {fmt(row['cross_edge_mean'])} | "
            f"{int(row['passive_events'])} | {fmt(row['passive_edge_mean'])} |"
        )

    candidate_lines = []
    for _, row in robust.head(20).iterrows():
        candidate_lines.append(
            f"| {row['product']} | {row['fair']} | {int(row['horizon'])} | "
            f"{int(row['active_events'])} | {fmt(row['signed_mid_markout_mean'])} | "
            f"{fmt(row['min_day_signed_mid_markout'])} | {int(row['cross_events'])} | "
            f"{fmt(row['cross_edge_mean'])} | {int(row['passive_events'])} | {fmt(row['passive_edge_mean'])} |"
        )

    wall_lines = []
    for _, row in wall_best.iterrows():
        wall_lines.append(
            f"| {row['product']} | {int(row['horizon'])} | {int(row['active_events'])} | "
            f"{fmt(row['signed_mid_markout_mean'])} | {fmt(row['min_day_signed_mid_markout'])} | "
            f"{fmt(row['cross_edge_mean'])} | {fmt(row['passive_edge_mean'])} |"
        )

    micro_lines = []
    for _, row in micro_top.iterrows():
        micro_lines.append(
            f"| {row['product']} | {fmt(row['avg_spread'])} | {fmt(row['avg_book_depth'])} | "
            f"{fmt(row['wall_dev_abs_mean'])} | {fmt(row['wall_dev_nonzero_share'], 4)} | "
            f"{fmt(row['bid_wall_level1_share'], 4)} | {fmt(row['ask_wall_level1_share'], 4)} | "
            f"{int(row['dominant_quote_size'])} | {fmt(row['dominant_quote_size_share'], 4)} |"
        )

    one_day_lines = []
    for _, row in one_day.iterrows():
        one_day_lines.append(
            f"| {row['product']} | {row['fair']} | {int(row['horizon'])} | "
            f"{int(row['positive_markout_days'])}/3 | {fmt(row['signed_mid_markout_mean'])} | "
            f"{fmt(row['min_day_signed_mid_markout'])} | {fmt(row['cross_edge_mean'])} | {fmt(row['passive_edge_mean'])} |"
        )

    strongest_reject_lines = []
    for _, row in strongest_rejects.iterrows():
        strongest_reject_lines.append(
            f"| {row['product']} | {row['fair']} | {int(row['horizon'])} | "
            f"{int(row['positive_markout_days'])}/3 | {int(row['active_events'])} | "
            f"{fmt(row['signed_mid_markout_mean'])} | {fmt(row['min_day_signed_mid_markout'])} | "
            f"{'yes' if row['robust_cross'] else 'no'} | {'yes' if row['robust_passive'] else 'no'} |"
        )

    wall_all = fair_summary[fair_summary["fair"] == "wall_mid"]
    popular_all = fair_summary[fair_summary["fair"] == "popular_mid"]
    best_wall = wall_all.sort_values("signed_mid_markout_mean", ascending=False).iloc[0]
    best_popular = popular_all.sort_values("signed_mid_markout_mean", ascending=False).iloc[0]

    text = f"""# Round 5 wall-mid / permanent-MM fair research

Scope: Round 5 price books only, days 2, 3, and 4, all 50 products. The tested fairs are:

- `wall_mid`: midpoint of the largest displayed bid-side wall price and largest displayed ask-side wall price in the current book.
- `popular_mid`: midpoint of the trailing {POPULAR_WINDOW}-row quote-volume modes on bid and ask, using only prior rows after {POPULAR_MIN_HISTORY} rows of warmup.
- `depth_vwap_mid`: depth-weighted quote midpoint across the three displayed levels, included as a control.

For markouts, positive means `fair - mid` correctly predicted the future mid move. For crossing, buys cross the ask when `fair > ask_1` and sells cross the bid when `fair < bid_1`; edge is future mid less the paid spread. Passive edge assumes a fill at the current best bid/ask, so it is useful as a quoting-value diagnostic, not a fill-rate backtest.

## Headline

`wall_mid` has a sparse but broad all-day structural signal. Its best aggregate horizon is {int(best_wall['horizon'])}: {int(best_wall['active_events'])} active observations, signed mid markout {fmt(best_wall['signed_mid_markout_mean'])}, hit rate {fmt(best_wall['signed_mid_markout_win_rate'], 4)}, cross edge {fmt(best_wall['cross_edge_mean'])} over {int(best_wall['cross_events'])} crossing events, and passive edge {fmt(best_wall['passive_edge_mean'])}.

The trailing `popular_mid` idea is not a short-horizon crossing fair: aggregate crossing edge is negative through horizon 100. It does produce strong product-specific horizon-{int(best_popular['horizon'])} anchors, with aggregate signed mid markout {fmt(best_popular['signed_mid_markout_mean'])} and cross edge {fmt(best_popular['cross_edge_mean'])}, so the usable interpretation is slow popular-price anchoring rather than immediate wall-following.

## Aggregate fair results

| fair | horizon | active_events | signed_mid_markout | hit_rate | cross_events | cross_edge | passive_events | passive_edge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(fair_lines)}

## Top robust candidates

Criteria: at least {MIN_TOTAL_EVENTS} active events, at least {MIN_DAY_EVENTS} events on each of the three days, positive signed markout on every day, and either positive crossing edge on every day or positive passive edge on every day.

| product | fair | horizon | active_events | signed_mid_markout | min_day_markout | cross_events | cross_edge | passive_events | passive_edge |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(candidate_lines) if candidate_lines else '| none |  |  |  |  |  |  |  |  |  |'}

## MM-style wall candidates only

| product | horizon | active_events | signed_mid_markout | min_day_markout | cross_edge | passive_edge |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(wall_lines) if wall_lines else '| none |  |  |  |  |  |  |'}

## Strongest wall/dislocation microstructure

These are the products where the largest displayed wall most often moves the fair away from ordinary book mid.

| product | avg_spread | avg_book_depth | abs_wall_dev | nonzero_wall_dev_share | bid_wall_L1_share | ask_wall_L1_share | dominant_size | dominant_size_share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(micro_lines)}

## Explicit rejections

These had apparent aggregate signal but failed the three-day validation or the after-spread strategy requirement.

| product | fair | horizon | positive_days | signed_mid_markout | min_day_markout | cross_edge | passive_edge |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(one_day_lines) if one_day_lines else '| none |  |  |  |  |  |  |  |'}

Strongest non-candidates by aggregate markout:

| product | fair | horizon | positive_days | active_events | signed_mid_markout | min_day_markout | robust_cross | robust_passive |
|---|---|---:|---:|---:|---:|---:|---|---|
{chr(10).join(strongest_reject_lines)}

## Files

- `16_wall_mid_product_summary.csv`: quote-size modes, top-of-book wall levels, max-volume price modes, spread/depth, and fair deviations by product/day.
- `16_wall_mid_markouts.csv`: product/day/fair/horizon predictive markouts and crossing/passive edge.
- `16_wall_mid_validation.csv`: three-day validation table used for candidate/rejection decisions.
- `16_wall_mid_fair_summary.csv`: aggregate fair/horizon results.
"""
    report_path.write_text(text)


def main() -> None:
    print("Loading Round 5 prices...")
    prices = read_prices()
    prices = add_wall_features(prices)
    prices = add_popular_features(prices)

    print("Summarizing book walls and quote sizes...")
    product_summary = summarize_microstructure(prices)
    product_summary.to_csv(OUT_DIR / "16_wall_mid_product_summary.csv", index=False)

    print("Computing markouts and strategy diagnostics...")
    markouts = markout_rows(prices)
    markouts.to_csv(OUT_DIR / "16_wall_mid_markouts.csv", index=False)

    validation = aggregate_validation(markouts)
    validation.to_csv(OUT_DIR / "16_wall_mid_validation.csv", index=False)

    fair_summary = aggregate_by_fair(markouts)
    fair_summary.to_csv(OUT_DIR / "16_wall_mid_fair_summary.csv", index=False)

    write_report(product_summary, markouts, validation, fair_summary)
    print("Wrote 16_wall_mid_mm.md and 16_wall_mid_*.csv outputs.")


if __name__ == "__main__":
    main()
