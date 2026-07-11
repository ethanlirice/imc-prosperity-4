from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/ROUND5")
OUT_DIR = Path("notebooks/round5")
PRODUCTS = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
PAR = 50000.0


def load_books() -> pd.DataFrame:
    prices = pd.concat(
        [pd.read_csv(path, sep=";") for path in sorted(DATA_DIR.glob("prices_round_5_day_*.csv"))],
        ignore_index=True,
    )
    return prices[prices["product"].isin(PRODUCTS)].copy()


def build_feature_frame(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, dday in prices.groupby("day"):
        piv = dday.pivot(index="timestamp", columns="product", values="mid_price").sort_index()
        sum_mid = piv[PRODUCTS].sum(axis=1)
        residual = sum_mid - PAR
        for product, g in dday.groupby("product"):
            g = g.sort_values("timestamp").copy()
            g["sum_mid"] = g["timestamp"].map(sum_mid)
            g["basket_resid"] = g["timestamp"].map(residual)
            g["synthetic_fair"] = g["mid_price"] - g["basket_resid"]
            g["edge_to_ask"] = g["synthetic_fair"] - g["ask_price_1"]
            g["edge_to_bid"] = g["bid_price_1"] - g["synthetic_fair"]
            for h in [1, 2, 5, 10, 20, 50, 100, 200]:
                future_mid = g["mid_price"].shift(-h)
                g[f"buy_mo_{h}"] = future_mid - g["ask_price_1"]
                g[f"sell_mo_{h}"] = g["bid_price_1"] - future_mid
                g[f"passive_buy_mo_{h}"] = future_mid - (g["bid_price_1"] + 1)
                g[f"passive_sell_mo_{h}"] = (g["ask_price_1"] - 1) - future_mid
            rows.append(g)
    return pd.concat(rows, ignore_index=True)


def summarize_events(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mode, edge_col, mo_prefix in [
        ("active_buy", "edge_to_ask", "buy_mo"),
        ("active_sell", "edge_to_bid", "sell_mo"),
        ("passive_buy", "edge_to_ask", "passive_buy_mo"),
        ("passive_sell", "edge_to_bid", "passive_sell_mo"),
    ]:
        for threshold in [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]:
            sub = frame[frame[edge_col] >= threshold].copy()
            for h in [1, 2, 5, 10, 20, 50, 100, 200]:
                mo_col = f"{mo_prefix}_{h}"
                vals = sub[mo_col].dropna()
                if vals.empty:
                    rows.append(
                        {
                            "mode": mode,
                            "threshold": threshold,
                            "horizon": h,
                            "n": 0,
                            "mean_mo": np.nan,
                            "good_pct": np.nan,
                            "qty_proxy_edge": 0.0,
                        }
                    )
                else:
                    rows.append(
                        {
                            "mode": mode,
                            "threshold": threshold,
                            "horizon": h,
                            "n": int(len(vals)),
                            "mean_mo": float(vals.mean()),
                            "good_pct": float((vals > 0).mean()),
                            "qty_proxy_edge": float(vals.sum()),
                        }
                    )
    return pd.DataFrame(rows)


def summarize_by_product(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, g in frame.groupby("product"):
        for side, edge_col, mo_col in [
            ("buy", "edge_to_ask", "buy_mo_20"),
            ("sell", "edge_to_bid", "sell_mo_20"),
            ("passive_buy", "edge_to_ask", "passive_buy_mo_20"),
            ("passive_sell", "edge_to_bid", "passive_sell_mo_20"),
        ]:
            for threshold in [0, 2, 4, 6, 8]:
                sub = g[g[edge_col] >= threshold]
                vals = sub[mo_col].dropna()
                rows.append(
                    {
                        "product": product,
                        "side": side,
                        "threshold": threshold,
                        "n": int(len(vals)),
                        "mean_mo20": float(vals.mean()) if len(vals) else np.nan,
                        "good_pct20": float((vals > 0).mean()) if len(vals) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = build_feature_frame(load_books())
    summary = summarize_events(frame)
    by_product = summarize_by_product(frame)
    frame[
        [
            "day",
            "timestamp",
            "product",
            "mid_price",
            "synthetic_fair",
            "basket_resid",
            "edge_to_ask",
            "edge_to_bid",
        ]
    ].to_csv(OUT_DIR / "10_pebbles_leg_fair_events.csv", index=False)
    summary.to_csv(OUT_DIR / "10_pebbles_leg_fair_summary.csv", index=False)
    by_product.to_csv(OUT_DIR / "10_pebbles_leg_fair_by_product.csv", index=False)

    interesting = summary[
        (summary["horizon"].isin([10, 20, 50]))
        & (summary["threshold"].isin([0, 2, 4, 6, 8]))
        & (summary["n"] > 0)
    ].sort_values(["mode", "threshold", "horizon"])
    lines = [
        "# Round 5 PEBBLES Leg Fair Proxy",
        "",
        "Uses the identity `sum(PEBBLES mids) ~= 50000`. For each leg, synthetic fair is `mid_i - (sum_mid - 50000)`.",
        "`edge_to_ask = synthetic_fair - best_ask`; `edge_to_bid = best_bid - synthetic_fair`.",
        "",
        "## Event Summary",
        "",
        interesting.round(6).to_markdown(index=False),
        "",
        "## By Product, Horizon 20",
        "",
        by_product.round(6).to_markdown(index=False),
        "",
    ]
    (OUT_DIR / "10_pebbles_leg_fair_proxy.md").write_text("\n".join(lines))
    print(interesting.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
