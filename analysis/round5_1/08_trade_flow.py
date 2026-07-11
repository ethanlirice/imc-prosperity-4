from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
OUT_PATH = OUT_DIR / "08_trade_flow.md"
HORIZONS = [100, 200, 1000, 5000]


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


PRODUCT_GROUP = {product: group for group, products in GROUPS.items() for product in products}


def day_from_path(path: Path) -> int:
    return int(path.stem.split("_")[-1])


def read_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_5_day_*.csv")):
        frame = pd.read_csv(path, sep=";").rename(columns={"symbol": "product"})
        frame["day"] = day_from_path(path)
        frames.append(frame)
    trades = pd.concat(frames, ignore_index=True)
    trades["group"] = trades["product"].map(PRODUCT_GROUP)
    return trades


def read_prices() -> pd.DataFrame:
    prices = pd.concat(
        [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))],
        ignore_index=True,
    )
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    return prices


def enrich_trades(trades: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    book_cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "ask_price_1",
        "ask_volume_1",
        "mid_price",
        "spread",
    ]
    out = trades.merge(prices[book_cols], on=["day", "timestamp", "product"], how="left")
    out["book_joined"] = out["mid_price"].notna()
    out["side"] = np.select(
        [
            out["price"] >= out["ask_price_1"],
            out["price"] <= out["bid_price_1"],
        ],
        ["buy_at_ask", "sell_at_bid"],
        default="inside_or_unknown",
    )
    out["signed_mid_edge"] = np.where(
        out["side"].eq("buy_at_ask"),
        out["price"] - out["mid_price"],
        np.where(out["side"].eq("sell_at_bid"), out["mid_price"] - out["price"], np.nan),
    )
    for horizon in HORIZONS:
        future = prices[["day", "timestamp", "product", "mid_price"]].copy()
        future["timestamp"] -= horizon
        future = future.rename(columns={"mid_price": f"future_mid_{horizon}"})
        out = out.merge(future, on=["day", "timestamp", "product"], how="left")
        sign = np.where(out["side"].eq("buy_at_ask"), 1.0, np.where(out["side"].eq("sell_at_bid"), -1.0, np.nan))
        out[f"mid_markout_{horizon}"] = sign * (out[f"future_mid_{horizon}"] - out["mid_price"])
        out[f"price_edge_{horizon}"] = np.where(
            out["side"].eq("buy_at_ask"),
            out[f"future_mid_{horizon}"] - out["price"],
            np.where(out["side"].eq("sell_at_bid"), out["price"] - out[f"future_mid_{horizon}"], np.nan),
        )
    return out


def participant_summary(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ["buyer", "seller"]:
        non_null = trades[col].notna() & trades[col].astype(str).str.strip().ne("")
        rows.append(
            {
                "field": col,
                "rows": len(trades),
                "non_blank": int(non_null.sum()),
                "unique_non_blank": int(trades.loc[non_null, col].nunique()),
            }
        )
    return pd.DataFrame(rows)


def coverage_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    return (
        enriched.groupby("day")
        .agg(
            trades=("price", "size"),
            products=("product", "nunique"),
            timestamps=("timestamp", "nunique"),
            first_ts=("timestamp", "min"),
            last_ts=("timestamp", "max"),
            book_join_rate=("book_joined", "mean"),
            quantity=("quantity", "sum"),
        )
        .reset_index()
    )


def touch_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    return (
        enriched.groupby("side")
        .agg(
            n=("price", "size"),
            qty=("quantity", "sum"),
            avg_qty=("quantity", "mean"),
            median_half_spread=("signed_mid_edge", "median"),
            mean_mid_markout_200=("mid_markout_200", "mean"),
            mean_price_edge_200=("price_edge_200", "mean"),
        )
        .reset_index()
        .sort_values("n", ascending=False)
    )


def group_cadence(enriched: pd.DataFrame) -> pd.DataFrame:
    product_rows = []
    for (day, product), frame in enriched.sort_values("timestamp").groupby(["day", "product"]):
        timestamps = frame["timestamp"].to_numpy()
        gaps = np.diff(timestamps)
        product_rows.append(
            {
                "day": int(day),
                "product": product,
                "group": PRODUCT_GROUP[product],
                "n": len(frame),
                "unique_ts": int(frame["timestamp"].nunique()),
                "same_product_same_ts_extra": int(len(frame) - frame["timestamp"].nunique()),
                "median_gap": float(np.median(gaps)) if len(gaps) else np.nan,
                "p10_gap": float(np.percentile(gaps, 10)) if len(gaps) else np.nan,
                "p90_gap": float(np.percentile(gaps, 90)) if len(gaps) else np.nan,
            }
        )
    product_cadence = pd.DataFrame(product_rows)
    return (
        product_cadence.groupby("group")
        .agg(
            trades=("n", "sum"),
            avg_trades_per_product_day=("n", "mean"),
            median_product_gap=("median_gap", "median"),
            p10_product_gap=("p10_gap", "median"),
            p90_product_gap=("p90_gap", "median"),
            same_product_same_ts_extra=("same_product_same_ts_extra", "sum"),
        )
        .reset_index()
        .sort_values(["trades", "group"], ascending=[False, True])
    )


def basket_events(enriched: pd.DataFrame) -> pd.DataFrame:
    events = (
        enriched.groupby(["day", "timestamp", "group"])
        .agg(
            trades=("product", "size"),
            products=("product", "nunique"),
            buy_trades=("side", lambda s: int((s == "buy_at_ask").sum())),
            sell_trades=("side", lambda s: int((s == "sell_at_bid").sum())),
            qty=("quantity", "sum"),
            size_set=("quantity", lambda s: ",".join(map(str, sorted(set(s))))),
            mean_mid_markout_200=("mid_markout_200", "mean"),
            mean_mid_markout_1000=("mid_markout_1000", "mean"),
        )
        .reset_index()
    )
    events["side_type"] = np.select(
        [events["sell_trades"].eq(0), events["buy_trades"].eq(0)],
        ["all_buy", "all_sell"],
        default="mixed",
    )
    return events


def basket_summary(events: pd.DataFrame) -> pd.DataFrame:
    full = events[events["products"].eq(5)]
    return (
        full.groupby("group")
        .agg(
            full_group_events=("timestamp", "size"),
            all_buy_events=("side_type", lambda s: int((s == "all_buy").sum())),
            all_sell_events=("side_type", lambda s: int((s == "all_sell").sum())),
            mixed_events=("side_type", lambda s: int((s == "mixed").sum())),
            days=("day", "nunique"),
            avg_event_qty=("qty", "mean"),
            median_event_qty=("qty", "median"),
            mean_mid_markout_200=("mean_mid_markout_200", "mean"),
            mean_mid_markout_1000=("mean_mid_markout_1000", "mean"),
        )
        .reset_index()
        .sort_values(["full_group_events", "group"], ascending=[False, True])
    )


def timestamp_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    timestamp_events = (
        enriched.groupby(["day", "timestamp"])
        .agg(
            trades=("product", "size"),
            products=("product", "nunique"),
            groups=("group", "nunique"),
            buy_trades=("side", lambda s: int((s == "buy_at_ask").sum())),
            sell_trades=("side", lambda s: int((s == "sell_at_bid").sum())),
            qty=("quantity", "sum"),
        )
        .reset_index()
    )
    timestamp_events["side_mix"] = (
        timestamp_events["buy_trades"].astype(str) + " buy / " + timestamp_events["sell_trades"].astype(str) + " sell"
    )
    return (
        timestamp_events.groupby(["products", "groups", "side_mix"])
        .agg(timestamps=("timestamp", "size"), avg_qty=("qty", "mean"))
        .reset_index()
        .sort_values(["products", "timestamps"], ascending=[False, False])
        .head(12)
    )


def size_summary(events: pd.DataFrame) -> pd.DataFrame:
    full = events[events["products"].eq(5)]
    return (
        full.groupby(["group", "size_set"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values("group")
    )


def open_close_summary(enriched: pd.DataFrame, window: int = 100_000) -> pd.DataFrame:
    temp = enriched.copy()
    temp["open_window"] = temp["timestamp"] < window
    temp["close_window"] = temp["timestamp"] >= 1_000_000 - window
    out = (
        temp.groupby("group")
        .agg(
            n=("price", "size"),
            open_n=("open_window", "sum"),
            close_n=("close_window", "sum"),
        )
        .reset_index()
    )
    out["open_share"] = out["open_n"] / out["n"]
    out["close_share"] = out["close_n"] / out["n"]
    return out.sort_values(["open_share", "close_share"], ascending=False)


def group_markouts(enriched: pd.DataFrame, horizon: int) -> pd.DataFrame:
    return (
        enriched.groupby(["group", "side"])
        .agg(
            n=("price", "size"),
            mean_mid_markout=(f"mid_markout_{horizon}", "mean"),
            mean_price_edge=(f"price_edge_{horizon}", "mean"),
            good_pct=(f"mid_markout_{horizon}", lambda s: float((s > 0).mean())),
        )
        .reset_index()
        .sort_values("mean_mid_markout", ascending=False)
    )


def persistent_product_markouts(enriched: pd.DataFrame, horizon: int, positive: bool) -> pd.DataFrame:
    daily = (
        enriched.groupby(["product", "side", "day"])
        .agg(
            n=("price", "size"),
            mean_mid_markout=(f"mid_markout_{horizon}", "mean"),
            mean_price_edge=(f"price_edge_{horizon}", "mean"),
            good_pct=(f"mid_markout_{horizon}", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )
    pivot = daily.pivot_table(index=["product", "side"], columns="day", values="mean_mid_markout")
    summary = daily.groupby(["product", "side"]).agg(
        n=("n", "sum"),
        mean_mid_markout=("mean_mid_markout", "mean"),
        mean_price_edge=("mean_price_edge", "mean"),
        avg_good_pct=("good_pct", "mean"),
    )
    for day in [2, 3, 4]:
        summary[f"d{day}_mid_markout"] = pivot[day]
    summary = summary.reset_index()
    day_cols = ["d2_mid_markout", "d3_mid_markout", "d4_mid_markout"]
    if positive:
        filtered = summary[(summary["n"] >= 150) & (summary[day_cols] > 0).all(axis=1)]
        return filtered.sort_values("mean_mid_markout", ascending=False).head(12)
    filtered = summary[(summary["n"] >= 150) & (summary[day_cols] < 0).all(axis=1)]
    return filtered.sort_values("mean_mid_markout", ascending=True).head(12)


def repeated_timestamp_by_group(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group, frame in enriched.groupby("group"):
        sets = {int(day): set(day_frame["timestamp"]) for day, day_frame in frame.groupby("day")}
        all_days = set.intersection(*sets.values()) if len(sets) == 3 else set()
        rows.append(
            {
                "group": group,
                "d2_timestamps": len(sets.get(2, set())),
                "d3_timestamps": len(sets.get(3, set())),
                "d4_timestamps": len(sets.get(4, set())),
                "exact_timestamps_repeated_all_3_days": len(all_days),
            }
        )
    return pd.DataFrame(rows).sort_values("group")


def fmt_table(frame: pd.DataFrame, digits: int = 4) -> str:
    return frame.round(digits).to_markdown(index=False)


def write_report() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trades = read_trades()
    prices = read_prices()
    enriched = enrich_trades(trades, prices)
    events = basket_events(enriched)
    full_events = events[events["products"].eq(5)]

    total_trades = len(enriched)
    full_event_trades = int(full_events["trades"].sum())
    all_buy_events = int((full_events["side_type"] == "all_buy").sum())
    all_sell_events = int((full_events["side_type"] == "all_sell").sum())
    mixed_events = int((full_events["side_type"] == "mixed").sum())

    lines = [
        "# Round 5 Lens 4 - Trade Flow, Participants, Timing",
        "",
        "Data: `data/ROUND5/trades_round_5_day_*.csv` joined to same-day `prices_round_5_day_*.csv` on `(day, timestamp, product)`.",
        "Side is inferred from book touch: prints at or above best ask are buyer-initiated; prints at or below best bid are seller-initiated.",
        "",
        "## Actionable Findings",
        "",
        f"- **No named counterparty signal exists in Round 5 trade CSVs.** Buyer/seller non-blank count is 0 out of {total_trades:,} rows, so there is no direct `Mark`/`Olivia` participant to copy or fade.",
        f"- **Every trade is part of a synchronized 5-product group basket.** Full group basket events account for {full_event_trades:,} / {total_trades:,} rows; events are {all_buy_events:,} all-buy and {all_sell_events:,} all-sell with {mixed_events:,} mixed-side events. Treat public flow as group-level inventory pressure, not single-name informed flow.",
        "- **All prints occur exactly at best bid or best ask and all rows join to the book.** Crossing immediately after these prints is not supported by t+200 evidence: both inferred sides still have negative average trade-price edge after spread at t+200.",
        "- **PEBBLES trade flow does not improve the confirmed PEBBLES basket-arb thesis.** PEBBLES group basket markouts are near flat at t+200 (`buy_at_ask` +0.023, `sell_at_bid` +0.071 mid points) and t+1000 (`buy_at_ask` -0.022, `sell_at_bid` +0.038), so use basket residuals rather than public-trade side as the main trigger.",
        "- **Opening/closing flow is not a special regime.** First/last 100k timestamps are close to calendar share: most groups are about 10.2% open and 10.9% close; PEBBLES is 10.4% / 11.2%. No open/close-only rule is justified from flow counts.",
        "- **Weak hidden-flow watchlist, not promotion:** persistent t+1000 mid-direction examples exist, but spread-adjusted edge is inconsistent. `PEBBLES_M buy_at_ask` has +7.396 average t+1000 mid markout across all 3 days, while `PEBBLES_XL buy_at_ask` has -5.244 across all 3 days; these are better used as quote-suppression/context filters than crossing signals.",
        "",
        "## Coverage",
        "",
        fmt_table(coverage_summary(enriched), 6),
        "",
        "## Counterparty Availability",
        "",
        fmt_table(participant_summary(trades), 6),
        "",
        "No non-blank buyer or seller names appear in any Round 5 trade row.",
        "",
        "## Book Join And Touch Relation",
        "",
        fmt_table(touch_summary(enriched), 6),
        "",
        "Interpretation: every joined print is a touch print. `mean_price_edge_200` is negative for both inferred sides, so blindly crossing in the same direction after observing a trade does not pay the spread at t+200.",
        "",
        "## Group Cadence",
        "",
        fmt_table(group_cadence(enriched), 4),
        "",
        "There are no duplicate timestamps within the same product/day; repeated timestamps are cross-product basket events.",
        "",
        "## Synchronized Basket Events",
        "",
        fmt_table(basket_summary(events), 4),
        "",
        "## Cross-Group Timestamp Repetition",
        "",
        fmt_table(timestamp_summary(enriched), 4),
        "",
        "The common 40-product events are the eight non-PEBBLES/non-MICROCHIP groups firing together. PEBBLES and MICROCHIP have separate schedules and sometimes align with the larger synchronized block.",
        "",
        "## Basket Size Pattern",
        "",
        fmt_table(size_summary(events), 0),
        "",
        "PEBBLES baskets use per-product sizes 2-5; MICROCHIP uses 1-3; the other eight groups use 1-4. Within each group basket, all five products share the same size.",
        "",
        "## Opening And Closing Rhythm",
        "",
        "Window: first and last 100,000 timestamps.",
        "",
        fmt_table(open_close_summary(enriched), 4),
        "",
        "## Forward Markouts By Group",
        "",
        "Buyer/seller side is inferred from touch. `mean_mid_markout` ignores spread; `mean_price_edge` includes the historical trade price.",
        "",
        "### Horizon 200",
        "",
        fmt_table(group_markouts(enriched, 200), 4),
        "",
        "### Horizon 1000",
        "",
        fmt_table(group_markouts(enriched, 1000), 4),
        "",
        "## Persistent Product-Side Mid Markouts",
        "",
        "These require at least 150 trades and the same markout sign on days 2, 3, and 4. They are directional mid moves after public prints, not guaranteed executable crossing edges.",
        "",
        "### Positive t+1000 Examples",
        "",
        fmt_table(persistent_product_markouts(enriched, 1000, positive=True), 4),
        "",
        "### Negative t+1000 Examples",
        "",
        fmt_table(persistent_product_markouts(enriched, 1000, positive=False), 4),
        "",
        "## Olivia / Mark-Like Signal Check",
        "",
        fmt_table(repeated_timestamp_by_group(enriched), 0),
        "",
        "No exact trade timestamp repeats across all 3 days for any group. Combined with blank participant IDs, this rejects a direct Olivia/Mark-style participant replay signal for Round 5. The only repeatable signature is structural: complete same-side group baskets at the touch.",
        "",
    ]
    OUT_PATH.write_text("\n".join(lines))
    print(f"Wrote {OUT_PATH}")
    print("\n".join(lines[:22]))


if __name__ == "__main__":
    write_report()
