#!/usr/bin/env python3
"""
Round 5 tree + GRU research model.

This is not submission code. It uses all 50 products' book/mid/group features
per timestamp to identify which features and products help predict executable
future edges. Outputs are rankings and validation metrics, not trades.

Validation splits:
- train day 2 -> validate day 3
- train day 3 -> validate day 4
- train days 2+3 -> validate day 4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
except Exception as exc:  # pragma: no cover - research dependency
    torch = None
    nn = None
    DataLoader = None
    Dataset = object
    TORCH_IMPORT_ERROR = exc
else:
    TORCH_IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5" / "neural-signals"
HORIZONS = [10, 50, 100, 200, 500, 1000]
GROUPS = {
    "GALAXY": ["GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_SOLAR_FLAMES"],
    "SLEEP": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UV": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    "TRANSLATOR": ["TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"],
    "SNACKPACK": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"],
}
PRODUCTS = [p for ps in GROUPS.values() for p in ps]
PRODUCT_TO_GROUP = {p: g for g, ps in GROUPS.items() for p in ps}
BASE_FEATURES = ["mid_centered", "ret1", "ret10", "ret50", "spread", "imbalance1", "imbalance3", "micro_minus_mid", "group_residual_z", "group_mid_rank"]


def load_long() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        frames.append(pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=";"))
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    for c in ["bid_volume_2", "bid_volume_3", "ask_volume_2", "ask_volume_3"]:
        df[c] = df[c].fillna(0)
    df["group"] = df["product"].map(PRODUCT_TO_GROUP)
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["depth_bid3"] = df["bid_volume_1"] + df["bid_volume_2"] + df["bid_volume_3"]
    df["depth_ask3"] = df["ask_volume_1"] + df["ask_volume_2"] + df["ask_volume_3"]
    df["imbalance1"] = (df["bid_volume_1"] - df["ask_volume_1"]) / (df["bid_volume_1"] + df["ask_volume_1"]).replace(0, np.nan)
    df["imbalance3"] = (df["depth_bid3"] - df["depth_ask3"]) / (df["depth_bid3"] + df["depth_ask3"]).replace(0, np.nan)
    df["microprice"] = (df["ask_price_1"] * df["bid_volume_1"] + df["bid_price_1"] * df["ask_volume_1"]) / (df["bid_volume_1"] + df["ask_volume_1"]).replace(0, np.nan)
    df["micro_minus_mid"] = df["microprice"] - df["mid_price"]
    gp = df.groupby(["product", "day"], sort=False)
    df["ret1"] = gp["mid_price"].diff()
    df["ret10"] = gp["mid_price"].diff(10)
    df["ret50"] = gp["mid_price"].diff(50)
    df["mid_centered"] = df["mid_price"] - gp["mid_price"].transform(lambda s: s.expanding().mean())
    for h in HORIZONS:
        df[f"long_edge_{h}"] = gp["bid_price_1"].shift(-h) - df["ask_price_1"]
        df[f"short_edge_{h}"] = df["bid_price_1"] - gp["ask_price_1"].shift(-h)
    keys = ["day", "timestamp", "group"]
    gr = df.groupby(keys, sort=False)
    sum_mid = gr["mid_price"].transform("sum")
    count_mid = gr["mid_price"].transform("count").clip(lower=2)
    resid = df["mid_price"] - (sum_mid - df["mid_price"]) / (count_mid - 1)
    resid_mean = resid.groupby([df[k] for k in keys]).transform("mean")
    resid_std = resid.groupby([df[k] for k in keys]).transform("std").replace(0, np.nan)
    df["group_residual_z"] = ((resid - resid_mean) / resid_std).fillna(0.0)
    df["group_mid_rank"] = gr["mid_price"].rank(method="first") - 1
    return df.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def make_wide(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    idx = ["day", "timestamp"]
    feature_frames = []
    feature_cols = []
    for feature in BASE_FEATURES:
        wide = df.pivot(index=idx, columns="product", values=feature).sort_index()
        wide.columns = [f"{p}__{feature}" for p in wide.columns]
        feature_frames.append(wide)
        feature_cols.extend(wide.columns.tolist())
    x = pd.concat(feature_frames, axis=1).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    target_frames = []
    target_cols = []
    for h in HORIZONS:
        for side in ["long", "short"]:
            wide = df.pivot(index=idx, columns="product", values=f"{side}_edge_{h}").sort_index()
            wide.columns = [f"{p}__{side}__h{h}" for p in wide.columns]
            target_frames.append(wide)
            target_cols.extend(wide.columns.tolist())
    y = pd.concat(target_frames, axis=1).replace([np.inf, -np.inf], np.nan)
    valid = ~y.isna().any(axis=1)
    return x.loc[valid], y.loc[valid], feature_cols, target_cols


def edge_metrics(pred: np.ndarray, actual: np.ndarray, target_cols: list[str], split_name: str) -> pd.DataFrame:
    rows = []
    for i, col in enumerate(target_cols):
        p = pred[:, i]
        a = actual[:, i]
        finite = np.isfinite(p) & np.isfinite(a)
        if finite.sum() < 100:
            continue
        p = p[finite]
        a = a[finite]
        top_n = max(20, int(0.05 * len(p)))
        idx = np.argsort(p)[-top_n:]
        corr = np.corrcoef(p, a)[0, 1] if np.std(p) > 0 and np.std(a) > 0 else np.nan
        product, side, h = col.split("__")
        rows.append({
            "split": split_name,
            "product": product,
            "group": PRODUCT_TO_GROUP[product],
            "side": side,
            "horizon": int(h[1:]),
            "corr": float(corr) if np.isfinite(corr) else np.nan,
            "top5_pred_mean_edge": float(a[idx].mean()),
            "top5_win": float((a[idx] > 0).mean()),
            "top5_count": int(top_n),
            "all_mean_edge": float(a.mean()),
        })
    return pd.DataFrame(rows)


def run_trees(x: pd.DataFrame, y: pd.DataFrame, feature_cols: list[str], target_cols: list[str]) -> None:
    splits = [
        ("d2_to_d3", [2], [3]),
        ("d3_to_d4", [3], [4]),
        ("d23_to_d4", [2, 3], [4]),
    ]
    all_metrics = []
    all_importance = []
    day_values = x.index.get_level_values("day")
    for split_name, train_days, valid_days in splits:
        train_mask = day_values.isin(train_days)
        valid_mask = day_values.isin(valid_days)
        model = ExtraTreesRegressor(
            n_estimators=32,
            max_features=0.45,
            min_samples_leaf=40,
            random_state=20260429,
            n_jobs=-1,
        )
        model.fit(x.loc[train_mask].to_numpy(dtype=np.float32), y.loc[train_mask].to_numpy(dtype=np.float32))
        pred = model.predict(x.loc[valid_mask].to_numpy(dtype=np.float32))
        all_metrics.append(edge_metrics(pred, y.loc[valid_mask].to_numpy(), target_cols, split_name))
        imp = pd.DataFrame({"split": split_name, "feature_col": feature_cols, "importance": model.feature_importances_})
        imp["source_product"] = imp["feature_col"].str.split("__").str[0]
        imp["feature"] = imp["feature_col"].str.split("__").str[1]
        all_importance.append(imp)
    metrics = pd.concat(all_metrics, ignore_index=True)
    metrics["rank_score"] = metrics["top5_mean_stable_proxy"] = metrics["top5_pred_mean_edge"] * metrics["top5_win"].clip(lower=0.01)
    metrics = metrics.sort_values(["rank_score", "top5_pred_mean_edge"], ascending=[False, False])
    metrics.to_csv(OUT_DIR / "44_tree_target_metrics.csv", index=False)
    stable = metrics.groupby(["product", "side", "horizon"], as_index=False).agg(
        group=("group", "first"),
        splits=("split", "nunique"),
        min_top5_edge=("top5_pred_mean_edge", "min"),
        mean_top5_edge=("top5_pred_mean_edge", "mean"),
        min_top5_win=("top5_win", "min"),
        mean_corr=("corr", "mean"),
    )
    stable = stable[(stable["splits"] == 3) & (stable["min_top5_edge"] > 0)].copy()
    stable["rank_score"] = stable["min_top5_edge"] * stable["min_top5_win"].clip(lower=0.01)
    stable.sort_values(["rank_score", "mean_top5_edge"], ascending=[False, False]).to_csv(OUT_DIR / "44_tree_stable_targets.csv", index=False)
    importance = pd.concat(all_importance, ignore_index=True)
    importance.sort_values(["split", "importance"], ascending=[True, False]).to_csv(OUT_DIR / "44_tree_feature_importance_by_split.csv", index=False)
    feature_summary = importance.groupby(["source_product", "feature"], as_index=False).agg(mean_importance=("importance", "mean"), min_importance=("importance", "min"))
    feature_summary.sort_values(["mean_importance", "min_importance"], ascending=[False, False]).to_csv(OUT_DIR / "44_tree_feature_importance_summary.csv", index=False)


class SeqDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, days: np.ndarray, lookback: int, allowed_days: set[int]):
        self.x = x
        self.y = y
        self.lookback = lookback
        self.indices = []
        for i in range(lookback - 1, len(x)):
            if int(days[i]) in allowed_days and np.all(days[i - lookback + 1:i + 1] == days[i]):
                self.indices.append(i)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, j: int):
        i = self.indices[j]
        return (
            torch.tensor(self.x[i - self.lookback + 1:i + 1], dtype=torch.float32),
            torch.tensor(self.y[i], dtype=torch.float32),
        )


class EdgeGRU(nn.Module):
    def __init__(self, n_features: int, n_targets: int):
        super().__init__()
        self.gru = nn.GRU(n_features, 64, batch_first=True)
        self.head = nn.Sequential(nn.LayerNorm(64), nn.Linear(64, 128), nn.ReLU(), nn.Linear(128, n_targets))

    def forward(self, x):
        out, _ = self.gru(x)
        return self.head(out[:, -1, :])


def run_gru(x: pd.DataFrame, y: pd.DataFrame, feature_cols: list[str], target_cols: list[str], epochs: int) -> None:
    if torch is None:
        raise SystemExit(f"PyTorch unavailable: {TORCH_IMPORT_ERROR}")
    day_values = x.index.get_level_values("day").to_numpy()
    train_mask = np.isin(day_values, [2, 3])
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    x_np = scaler_x.fit_transform(x.loc[train_mask]).astype(np.float32)
    x_all = scaler_x.transform(x).astype(np.float32)
    y_np = scaler_y.fit_transform(y.loc[train_mask]).astype(np.float32)
    y_all = scaler_y.transform(y).astype(np.float32)
    train_ds = SeqDataset(x_all, y_all, day_values, lookback=20, allowed_days={2, 3})
    valid_ds = SeqDataset(x_all, y_all, day_values, lookback=20, allowed_days={4})
    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=1024, shuffle=False)
    device = "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu"
    model = EdgeGRU(x.shape[1], y.shape[1]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    loss_fn = nn.SmoothL1Loss()
    for epoch in range(epochs):
        model.train()
        total = 0.0
        count = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += float(loss.item()) * len(xb)
            count += len(xb)
        print(f"gru epoch {epoch + 1}/{epochs} loss {total / max(1, count):.6f}")
    model.eval()
    preds = []
    acts = []
    with torch.no_grad():
        for xb, yb in valid_loader:
            pred = model(xb.to(device)).cpu().numpy()
            preds.append(pred)
            acts.append(yb.numpy())
    pred_scaled = np.vstack(preds)
    act_scaled = np.vstack(acts)
    pred = scaler_y.inverse_transform(pred_scaled)
    actual = scaler_y.inverse_transform(act_scaled)
    metrics = edge_metrics(pred, actual, target_cols, "gru_d23_to_d4")
    metrics["rank_score"] = metrics["top5_pred_mean_edge"] * metrics["top5_win"].clip(lower=0.01)
    metrics.sort_values(["rank_score", "top5_pred_mean_edge"], ascending=[False, False]).to_csv(OUT_DIR / "44_gru_target_metrics.csv", index=False)
    w = model.gru.weight_ih_l0.detach().abs().sum(dim=0).cpu().numpy()
    imp = pd.DataFrame({"feature_col": feature_cols, "importance": w})
    imp["source_product"] = imp["feature_col"].str.split("__").str[0]
    imp["feature"] = imp["feature_col"].str.split("__").str[1]
    imp.sort_values("importance", ascending=False).to_csv(OUT_DIR / "44_gru_feature_importance.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-gru", action="store_true")
    parser.add_argument("--gru-epochs", type=int, default=6)
    parser.add_argument("--target-step", type=int, default=3)
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    long_df = load_long()
    x, y, feature_cols, target_cols = make_wide(long_df)
    if args.target_step > 1:
        keep = np.arange(len(target_cols)) % args.target_step == 0
        y = y.iloc[:, keep]
        target_cols = [c for c, k in zip(target_cols, keep) if k]
    run_trees(x, y, feature_cols, target_cols)
    if not args.skip_gru:
        run_gru(x, y, feature_cols, target_cols, epochs=args.gru_epochs)
    print("wrote tree/gru research outputs")


if __name__ == "__main__":
    main()
