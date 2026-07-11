import itertools
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")


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


def read_prices() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv")):
        frames.append(pd.read_csv(path, sep=";"))
    prices = pd.concat(frames, ignore_index=True)
    prices["spread"] = prices["ask_price_1"] - prices["bid_price_1"]
    depth_cols = [
        "bid_volume_1",
        "bid_volume_2",
        "bid_volume_3",
        "ask_volume_1",
        "ask_volume_2",
        "ask_volume_3",
    ]
    prices[depth_cols] = prices[depth_cols].fillna(0)
    prices["top3_depth"] = (
        prices["bid_volume_1"].abs()
        + prices["bid_volume_2"].abs()
        + prices["bid_volume_3"].abs()
        + prices["ask_volume_1"].abs()
        + prices["ask_volume_2"].abs()
        + prices["ask_volume_3"].abs()
    )
    return prices


def mean_abs_pair_corr(frame: pd.DataFrame, products: list[str], use_returns: bool) -> float:
    pivot = frame.pivot(index="timestamp", columns="product", values="mid_price")
    pivot = pivot.reindex(columns=products)
    values = pivot.diff().dropna() if use_returns else pivot.dropna()
    corrs = []
    for a, b in itertools.combinations(products, 2):
        if a not in values or b not in values:
            continue
        x = values[a].to_numpy(dtype=float)
        y = values[b].to_numpy(dtype=float)
        if len(x) < 20 or np.std(x) <= 1e-12 or np.std(y) <= 1e-12:
            continue
        corrs.append(abs(float(np.corrcoef(x, y)[0, 1])))
    return float(np.mean(corrs)) if corrs else 0.0


def day_group_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, day_df in prices.groupby("day"):
        for group, products in GROUPS.items():
            g = day_df[day_df["product"].isin(products)].copy()
            if g.empty:
                continue
            lively = []
            ret_vols = []
            product_ranges = []
            for product, p_df in g.groupby("product"):
                mids = p_df.sort_values("timestamp")["mid_price"].to_numpy(dtype=float)
                if len(mids) < 2:
                    continue
                rets = np.diff(mids)
                lively.append(float(np.mean(np.abs(rets) > 1e-12)))
                ret_vols.append(float(np.std(rets)))
                product_ranges.append(float(np.max(mids) - np.min(mids)))

            intra_ret_corr = mean_abs_pair_corr(g, products, use_returns=True)
            intra_mid_corr = mean_abs_pair_corr(g, products, use_returns=False)
            median_spread = float(g["spread"].median())
            median_depth = float(g["top3_depth"].median())
            ret_vol = float(np.mean(ret_vols)) if ret_vols else 0.0
            # Higher is better: enough movement to pay the spread.
            vol_to_spread = ret_vol / median_spread if median_spread > 0 else 0.0
            lively_pct = float(np.mean(lively)) if lively else 0.0
            score = intra_ret_corr * vol_to_spread * median_depth * lively_pct
            rows.append(
                {
                    "day": int(day),
                    "group": group,
                    "intra_group_corr": intra_ret_corr,
                    "intra_mid_corr": intra_mid_corr,
                    "spread_to_vol": vol_to_spread,
                    "median_spread": median_spread,
                    "ret_vol": ret_vol,
                    "depth": median_depth,
                    "lively_ticks_pct": lively_pct,
                    "mid_range": float(np.mean(product_ranges)) if product_ranges else 0.0,
                    "tradeability_score": score,
                }
            )
    out = pd.DataFrame(rows)
    out["day_rank"] = out.groupby("day")["tradeability_score"].rank(
        method="first", ascending=False
    )
    return out


def stable_ranking(day_metrics: pd.DataFrame) -> pd.DataFrame:
    wide_score = day_metrics.pivot(index="group", columns="day", values="tradeability_score")
    wide_rank = day_metrics.pivot(index="group", columns="day", values="day_rank")
    metric_cols = [
        "intra_group_corr",
        "intra_mid_corr",
        "spread_to_vol",
        "median_spread",
        "ret_vol",
        "depth",
        "lively_ticks_pct",
        "mid_range",
    ]
    avg = day_metrics.groupby("group")[metric_cols].mean()
    out = avg.copy()
    for day in sorted(day_metrics["day"].unique()):
        out[f"score_d{day}"] = wide_score[day]
        out[f"rank_d{day}"] = wide_rank[day]
    score_cols = [c for c in out.columns if c.startswith("score_d")]
    rank_cols = [c for c in out.columns if c.startswith("rank_d")]
    out["score_mean"] = out[score_cols].mean(axis=1)
    out["score_min"] = out[score_cols].min(axis=1)
    out["score_cv"] = out[score_cols].std(axis=1) / out["score_mean"].replace(0, np.nan)
    out["rank_worst"] = out[rank_cols].max(axis=1)
    out["rank_mean"] = out[rank_cols].mean(axis=1)
    # Stability rewards high minimum day score and penalizes rank instability.
    out["stable_tradeability_score"] = out["score_min"] / out["rank_worst"]
    return out.reset_index().sort_values(
        ["stable_tradeability_score", "score_mean"], ascending=False
    )


def write_markdown(ranking: pd.DataFrame, day_metrics: pd.DataFrame) -> None:
    top_groups = ranking.head(4)["group"].tolist()
    lines = [
        "# Round 5 Phase 1 - Group Tradeability",
        "",
        "Composite score uses `intra_group_corr * spread_to_vol * depth * lively_ticks_pct`.",
        "`spread_to_vol` is implemented as return-volatility divided by median spread, so higher means the group moves enough to pay crossing costs.",
        "Validation requirement: ranking should be stable across days 2, 3, and 4; unstable high-score groups are treated as lower confidence.",
        "",
        "## Ranked Groups",
        "",
        ranking[
            [
                "group",
                "stable_tradeability_score",
                "score_mean",
                "score_min",
                "rank_mean",
                "rank_worst",
                "intra_group_corr",
                "spread_to_vol",
                "depth",
                "lively_ticks_pct",
            ]
        ]
        .round(6)
        .to_markdown(index=False),
        "",
        "## Selected For Phase 2/3",
        "",
    ]
    for group in top_groups:
        row = ranking[ranking["group"] == group].iloc[0]
        lines.append(
            f"- **{group}**: stable score {row['stable_tradeability_score']:.6f}, "
            f"mean rank {row['rank_mean']:.2f}, worst rank {row['rank_worst']:.0f}; "
            f"corr {row['intra_group_corr']:.4f}, vol/spread {row['spread_to_vol']:.4f}, "
            f"depth {row['depth']:.1f}, lively {row['lively_ticks_pct']:.3f}."
        )
    lines.extend(["", "## Excluded Groups", ""])
    for _, row in ranking.iloc[4:].iterrows():
        reason = []
        if row["rank_worst"] > 6:
            reason.append(f"weak worst-day rank {row['rank_worst']:.0f}")
        if row["score_min"] < ranking["score_min"].median():
            reason.append("low minimum day score")
        if row["intra_group_corr"] < ranking["intra_group_corr"].median():
            reason.append("below-median return co-movement")
        if row["spread_to_vol"] < ranking["spread_to_vol"].median():
            reason.append("movement is thin versus spread")
        if not reason:
            reason.append("lower stable score than selected groups")
        lines.append(f"- **{row['group']}**: rejected for {', '.join(reason)}.")
    lines.extend(
        [
            "",
            "## Per-Day Scores",
            "",
            day_metrics.sort_values(["day", "day_rank"])[
                [
                    "day",
                    "group",
                    "day_rank",
                    "tradeability_score",
                    "intra_group_corr",
                    "spread_to_vol",
                    "depth",
                    "lively_ticks_pct",
                ]
            ]
            .round(6)
            .to_markdown(index=False),
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "01_group_tradeability.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = read_prices()
    day_metrics = day_group_metrics(prices)
    ranking = stable_ranking(day_metrics)
    day_metrics.to_csv(OUT_DIR / "01_group_tradeability_by_day.csv", index=False)
    ranking.to_csv(OUT_DIR / "01_group_tradeability_ranking.csv", index=False)
    write_markdown(ranking, day_metrics)
    print(
        ranking[
            [
                "group",
                "stable_tradeability_score",
                "score_mean",
                "score_min",
                "rank_mean",
                "rank_worst",
                "intra_group_corr",
                "spread_to_vol",
                "depth",
                "lively_ticks_pct",
            ]
        ]
        .round(6)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
