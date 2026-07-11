#!/usr/bin/env python3
"""
Round 5 second-generation NN/stochastic research lab.

Goals:
- Use a real GRU/RNN research model over product-local sequences plus
  cross-product context for all 50 products.
- Target executable edges, not mid-price prediction.
- Validate with day splits: d2->d3, d3->d4, d23->d4.
- Emit product/side/horizon candidate rankings and feature saliency.
- Add stochastic diagnostics: OU half-life, local drift/vol, crossing cost,
  and a rough hitting-probability proxy.
- Add synthetic injection checks so scanners/models can prove they rediscover
  planted lead-lag / suffix / time-bucket mechanics before we trust them.

This is research-only. Nothing here is valid submission code.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, Dataset
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"PyTorch required for this research script: {exc}")


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "raw-data" / "ROUND5"
OUT_DIR = ROOT / "analysis" / "round5-nn-research"

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
PRODUCT_TO_ID = {p: i for i, p in enumerate(PRODUCTS)}
PRODUCT_TO_GROUP = {p: g for g, ps in GROUPS.items() for p in ps}
GROUP_TO_ID = {g: i for i, g in enumerate(GROUPS)}
HORIZONS = [10, 50, 100, 200, 500, 1000]
SIDES = ["long", "short"]
TARGET_COLS = [f"{side}_h{h}" for h in HORIZONS for side in SIDES]
OWN_FEATURES = [
    "mid_centered", "ret1", "ret5", "ret10", "ret20", "ret50", "ret100",
    "spread", "imbalance1", "imbalance3", "micro_minus_mid",
    "group_residual_z", "group_mid_rank", "group_micro_rank", "vol50",
    "ou_z100", "dist_min100", "dist_max100", "suffix100", "suffix1000",
]
CTX_FEATURES = [
    "group_ret10_mean", "group_ret50_mean", "group_imbalance_mean",
    "group_micro_mean", "market_ret10_mean", "market_imbalance_mean",
]


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        frames.append(pd.read_csv(DATA_DIR / f"prices_round_5_day_{day}.csv", sep=";"))
    df = pd.concat(frames, ignore_index=True)
    df = df[df["product"].isin(PRODUCTS)].copy()
    df = df.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    df["product_id"] = df["product"].map(PRODUCT_TO_ID).astype(int)
    df["group"] = df["product"].map(PRODUCT_TO_GROUP)
    df["group_id"] = df["group"].map(GROUP_TO_ID).astype(int)
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["bid_price_2", "bid_price_3", "ask_price_2", "ask_price_3", "bid_volume_2", "bid_volume_3", "ask_volume_2", "ask_volume_3"]:
        out[c] = out[c].fillna(0)
    out["spread"] = out["ask_price_1"] - out["bid_price_1"]
    out["depth_bid3"] = out["bid_volume_1"] + out["bid_volume_2"] + out["bid_volume_3"]
    out["depth_ask3"] = out["ask_volume_1"] + out["ask_volume_2"] + out["ask_volume_3"]
    out["imbalance1"] = (out["bid_volume_1"] - out["ask_volume_1"]) / (out["bid_volume_1"] + out["ask_volume_1"]).replace(0, np.nan)
    out["imbalance3"] = (out["depth_bid3"] - out["depth_ask3"]) / (out["depth_bid3"] + out["depth_ask3"]).replace(0, np.nan)
    out["microprice"] = (out["ask_price_1"] * out["bid_volume_1"] + out["bid_price_1"] * out["ask_volume_1"]) / (out["bid_volume_1"] + out["ask_volume_1"]).replace(0, np.nan)
    out["micro_minus_mid"] = out["microprice"] - out["mid_price"]
    gp = out.groupby(["product", "day"], sort=False)
    out["ret1"] = gp["mid_price"].diff()
    for lag in [5, 10, 20, 50, 100]:
        out[f"ret{lag}"] = gp["mid_price"].diff(lag)
    out["mid_centered"] = out["mid_price"] - gp["mid_price"].transform(lambda s: s.expanding().mean())
    out["vol50"] = gp["ret1"].transform(lambda s: s.rolling(50, min_periods=10).std())
    roll_mean = gp["mid_price"].transform(lambda s: s.rolling(100, min_periods=20).mean())
    roll_std = gp["mid_price"].transform(lambda s: s.rolling(100, min_periods=20).std())
    out["ou_z100"] = (out["mid_price"] - roll_mean) / roll_std.replace(0, np.nan)
    out["dist_min100"] = out["mid_price"] - gp["mid_price"].transform(lambda s: s.rolling(100, min_periods=20).min())
    out["dist_max100"] = gp["mid_price"].transform(lambda s: s.rolling(100, min_periods=20).max()) - out["mid_price"]
    out["suffix100"] = (out["bid_price_1"] % 100) / 100.0
    out["suffix1000"] = (out["bid_price_1"] % 1000) / 1000.0

    keys = ["day", "timestamp", "group"]
    gr = out.groupby(keys, sort=False)
    count = gr["mid_price"].transform("count").clip(lower=2)
    sum_mid = gr["mid_price"].transform("sum")
    ex_self = (sum_mid - out["mid_price"]) / (count - 1)
    residual = out["mid_price"] - ex_self
    r_mean = gr["mid_price"].transform("mean")
    r_std = residual.groupby([out[k] for k in keys]).transform("std").replace(0, np.nan)
    out["group_residual_z"] = ((residual - (out["mid_price"] - r_mean)) / r_std).fillna(0.0)
    out["group_mid_rank"] = gr["mid_price"].rank(method="first") - 1
    out["group_micro_rank"] = gr["micro_minus_mid"].rank(method="first") - 1
    out["group_ret10_mean"] = gr["ret10"].transform("mean")
    out["group_ret50_mean"] = gr["ret50"].transform("mean")
    out["group_imbalance_mean"] = gr["imbalance3"].transform("mean")
    out["group_micro_mean"] = gr["micro_minus_mid"].transform("mean")
    cs = out.groupby(["day", "timestamp"], sort=False)
    out["market_ret10_mean"] = cs["ret10"].transform("mean")
    out["market_imbalance_mean"] = cs["imbalance3"].transform("mean")

    for h in HORIZONS:
        out[f"long_h{h}"] = gp["bid_price_1"].shift(-h) - out["ask_price_1"]
        out[f"short_h{h}"] = out["bid_price_1"] - gp["ask_price_1"].shift(-h)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


class SequenceEdgeDataset(Dataset):
    def __init__(self, df: pd.DataFrame, own_scaler: tuple[np.ndarray, np.ndarray], ctx_scaler: tuple[np.ndarray, np.ndarray],
                 lookback: int, days: set[int], stride: int, max_samples: int | None = None):
        self.df = df
        self.lookback = lookback
        self.own_mean, self.own_std = own_scaler
        self.ctx_mean, self.ctx_std = ctx_scaler
        self.indices = []
        day_arr = df["day"].to_numpy(dtype=int)
        prod_arr = df["product_id"].to_numpy(dtype=int)
        valid_days = np.isin(day_arr, list(days))
        # Rows are product/day sorted. Keep full in-day sequences only.
        for i in range(lookback - 1, len(df), stride):
            if not valid_days[i]:
                continue
            j = i - lookback + 1
            if j < 0:
                continue
            if day_arr[j] == day_arr[i] and prod_arr[j] == prod_arr[i]:
                self.indices.append(i)
        if max_samples and len(self.indices) > max_samples:
            rng = np.random.default_rng(20260429 + sum(days) + stride)
            self.indices = sorted(rng.choice(self.indices, size=max_samples, replace=False).tolist())
        self.own = df[OWN_FEATURES].to_numpy(dtype=np.float32)
        self.ctx = df[CTX_FEATURES].to_numpy(dtype=np.float32)
        self.y = df[TARGET_COLS].to_numpy(dtype=np.float32)
        self.prod = df["product_id"].to_numpy(dtype=np.int64)
        self.group = df["group_id"].to_numpy(dtype=np.int64)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int):
        i = self.indices[idx]
        j = i - self.lookback + 1
        own = (self.own[j:i + 1] - self.own_mean) / self.own_std
        ctx = (self.ctx[i] - self.ctx_mean) / self.ctx_std
        y = self.y[i]
        return (
            torch.tensor(own, dtype=torch.float32),
            torch.tensor(ctx, dtype=torch.float32),
            torch.tensor(self.prod[i], dtype=torch.long),
            torch.tensor(self.group[i], dtype=torch.long),
            torch.tensor(y, dtype=torch.float32),
            torch.tensor(i, dtype=torch.long),
        )


class ProductGRUEdgeNet(nn.Module):
    def __init__(self, n_own: int, n_ctx: int, n_targets: int):
        super().__init__()
        self.product_emb = nn.Embedding(len(PRODUCTS), 16)
        self.group_emb = nn.Embedding(len(GROUPS), 8)
        self.gru = nn.GRU(n_own, 72, num_layers=2, batch_first=True, dropout=0.08)
        self.head = nn.Sequential(
            nn.LayerNorm(72 + n_ctx + 16 + 8),
            nn.Linear(72 + n_ctx + 16 + 8, 160),
            nn.SiLU(),
            nn.Dropout(0.08),
            nn.Linear(160, 96),
            nn.SiLU(),
            nn.Linear(96, n_targets),
        )

    def forward(self, own, ctx, product, group):
        seq, _ = self.gru(own)
        h = seq[:, -1]
        z = torch.cat([h, ctx, self.product_emb(product), self.group_emb(group)], dim=1)
        return self.head(z)


def fit_scalers(df: pd.DataFrame, train_days: set[int]) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], np.ndarray, np.ndarray]:
    train = df[df["day"].isin(train_days)]
    own = train[OWN_FEATURES].to_numpy(dtype=np.float32)
    ctx = train[CTX_FEATURES].to_numpy(dtype=np.float32)
    y = train[TARGET_COLS].to_numpy(dtype=np.float32)
    own_mean = np.nanmean(own, axis=0).astype(np.float32)
    own_std = np.nanstd(own, axis=0).astype(np.float32)
    ctx_mean = np.nanmean(ctx, axis=0).astype(np.float32)
    ctx_std = np.nanstd(ctx, axis=0).astype(np.float32)
    y_mean = np.nanmean(y, axis=0).astype(np.float32)
    y_std = np.nanstd(y, axis=0).astype(np.float32)
    return (own_mean, np.maximum(own_std, 1e-6)), (ctx_mean, np.maximum(ctx_std, 1e-6)), y_mean, np.maximum(y_std, 1e-6)


def train_split(df: pd.DataFrame, split_name: str, train_days: set[int], valid_days: set[int], epochs: int, lookback: int, stride: int, max_train: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    own_scaler, ctx_scaler, y_mean, y_std = fit_scalers(df, train_days)
    train_ds = SequenceEdgeDataset(df, own_scaler, ctx_scaler, lookback, train_days, stride=stride, max_samples=max_train)
    valid_ds = SequenceEdgeDataset(df, own_scaler, ctx_scaler, lookback, valid_days, stride=max(1, stride // 2), max_samples=None)
    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=1024, shuffle=False)
    device = "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu"
    model = ProductGRUEdgeNet(len(OWN_FEATURES), len(CTX_FEATURES), len(TARGET_COLS)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1.5e-3, weight_decay=1e-4)
    y_mean_t = torch.tensor(y_mean, dtype=torch.float32, device=device)
    y_std_t = torch.tensor(y_std, dtype=torch.float32, device=device)
    for epoch in range(epochs):
        model.train()
        total = 0.0
        count = 0
        for own, ctx, product, group, y, _ in train_loader:
            own = own.to(device)
            ctx = ctx.to(device)
            product = product.to(device)
            group = group.to(device)
            y = y.to(device)
            y_scaled = (y - y_mean_t) / y_std_t
            weights = 1.0 + torch.clamp(torch.abs(y_scaled).mean(dim=1, keepdim=True), max=4.0)
            pred = model(own, ctx, product, group)
            loss = (F.smooth_l1_loss(pred, y_scaled, reduction="none").mean(dim=1, keepdim=True) * weights).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            opt.step()
            total += float(loss.item()) * len(y)
            count += len(y)
        print(f"{split_name} epoch {epoch + 1}/{epochs} loss {total / max(1, count):.6f}")
    model.eval()
    preds = []
    actuals = []
    idxs = []
    with torch.no_grad():
        for own, ctx, product, group, y, idx in valid_loader:
            pred = model(own.to(device), ctx.to(device), product.to(device), group.to(device)).cpu().numpy()
            preds.append(pred * y_std + y_mean)
            actuals.append(y.numpy())
            idxs.append(idx.numpy())
    pred = np.vstack(preds)
    actual = np.vstack(actuals)
    idx = np.concatenate(idxs)
    metrics = summarize_predictions(df.iloc[idx].reset_index(drop=True), pred, actual, split_name)
    saliency = input_saliency(model, valid_loader, device, y_std, split_name)
    return metrics, saliency


def summarize_predictions(meta: pd.DataFrame, pred: np.ndarray, actual: np.ndarray, split_name: str) -> pd.DataFrame:
    rows = []
    for j, target in enumerate(TARGET_COLS):
        side, h = target.split("_h")
        for product, idx in meta.groupby("product").groups.items():
            loc = np.array(list(idx))
            p = pred[loc, j]
            a = actual[loc, j]
            if len(a) < 50:
                continue
            top_n = max(20, int(0.05 * len(a)))
            top = np.argsort(p)[-top_n:]
            corr = np.corrcoef(p, a)[0, 1] if np.std(p) > 1e-9 and np.std(a) > 1e-9 else np.nan
            rows.append({
                "split": split_name,
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "side": side,
                "horizon": int(h),
                "corr": float(corr) if np.isfinite(corr) else np.nan,
                "top5_count": int(top_n),
                "top5_edge": float(np.mean(a[top])),
                "top5_win": float(np.mean(a[top] > 0)),
                "top5_pred": float(np.mean(p[top])),
                "all_edge": float(np.mean(a)),
            })
    out = pd.DataFrame(rows)
    out["rank_score"] = out["top5_edge"] * out["top5_win"].clip(lower=0.01)
    return out.sort_values(["rank_score", "top5_edge"], ascending=[False, False]).reset_index(drop=True)


def input_saliency(model: nn.Module, loader: DataLoader, device: str, y_std: np.ndarray, split_name: str) -> pd.DataFrame:
    # Gradient saliency on one validation batch. This is approximate but good enough for research triage.
    own, ctx, product, group, _, _ = next(iter(loader))
    own = own.to(device).requires_grad_(True)
    ctx = ctx.to(device).requires_grad_(True)
    pred = model(own, ctx, product.to(device), group.to(device))
    score = pred.abs().mean()
    model.zero_grad(set_to_none=True)
    score.backward()
    own_imp = own.grad.detach().abs().mean(dim=(0, 1)).cpu().numpy()
    ctx_imp = ctx.grad.detach().abs().mean(dim=0).cpu().numpy()
    rows = [{"split": split_name, "feature_scope": "own_sequence", "feature": f, "importance": float(v)} for f, v in zip(OWN_FEATURES, own_imp)]
    rows += [{"split": split_name, "feature_scope": "context", "feature": f, "importance": float(v)} for f, v in zip(CTX_FEATURES, ctx_imp)]
    return pd.DataFrame(rows).sort_values("importance", ascending=False)


def run_rnn(df: pd.DataFrame, epochs: int, lookback: int, stride: int, max_train: int) -> None:
    splits = [
        ("d2_to_d3", {2}, {3}),
        ("d3_to_d4", {3}, {4}),
        ("d23_to_d4", {2, 3}, {4}),
    ]
    all_metrics = []
    all_saliency = []
    for name, train_days, valid_days in splits:
        metrics, saliency = train_split(df, name, train_days, valid_days, epochs, lookback, stride, max_train)
        all_metrics.append(metrics)
        all_saliency.append(saliency)
    metrics = pd.concat(all_metrics, ignore_index=True)
    metrics.to_csv(OUT_DIR / "45_rnn_target_metrics.csv", index=False)
    stable = metrics.groupby(["product", "side", "horizon"], as_index=False).agg(
        group=("group", "first"),
        splits=("split", "nunique"),
        min_top5_edge=("top5_edge", "min"),
        mean_top5_edge=("top5_edge", "mean"),
        min_top5_win=("top5_win", "min"),
        mean_corr=("corr", "mean"),
    )
    stable = stable[(stable["splits"] == 3) & (stable["min_top5_edge"] > 0)].copy()
    stable["rank_score"] = stable["min_top5_edge"] * stable["min_top5_win"].clip(lower=0.01)
    stable.sort_values(["rank_score", "mean_top5_edge"], ascending=[False, False]).to_csv(OUT_DIR / "45_rnn_stable_targets.csv", index=False)
    pd.concat(all_saliency, ignore_index=True).to_csv(OUT_DIR / "45_rnn_saliency.csv", index=False)


def stochastic_diagnostics(df: pd.DataFrame) -> None:
    rows = []
    for product, p in df.groupby("product", sort=True):
        for day, d in p.groupby("day", sort=True):
            x = d["mid_price"].to_numpy(dtype=float)
            if len(x) < 200:
                continue
            dx = np.diff(x)
            lag = x[:-1]
            a = np.vstack([np.ones_like(lag), lag]).T
            coef, *_ = np.linalg.lstsq(a, dx, rcond=None)
            c, b = coef
            phi = 1.0 + b
            half_life = np.nan
            if 0 < phi < 1:
                half_life = float(-math.log(2) / math.log(phi))
            mu = float(-c / b) if abs(b) > 1e-9 else float(np.mean(x))
            resid = dx - (c + b * lag)
            sigma = float(np.std(resid))
            spread = float(np.median(d["spread"]))
            drift50 = float(np.mean(x[50:] - x[:-50])) if len(x) > 50 else np.nan
            vol50 = float(np.std(x[50:] - x[:-50])) if len(x) > 50 else np.nan
            z = abs(float(x[-1] - mu)) / (sigma * math.sqrt(max(1.0, half_life if np.isfinite(half_life) else 1.0)) + 1e-9)
            hit_proxy = 0.5 * math.erfc((spread / 2) / (sigma * math.sqrt(50) + 1e-9))
            rows.append({
                "product": product,
                "group": PRODUCT_TO_GROUP[product],
                "day": day,
                "ou_mu": mu,
                "ou_phi": float(phi),
                "ou_half_life": half_life,
                "ou_sigma": sigma,
                "median_spread": spread,
                "drift50": drift50,
                "vol50": vol50,
                "last_ou_z": z,
                "hit_proxy_h50_vs_halfspread": hit_proxy,
                "spread_to_sigma": spread / (sigma + 1e-9),
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "45_stochastic_ou_diagnostics.csv", index=False)
    summary = out.groupby(["product", "group"], as_index=False).agg(
        median_half_life=("ou_half_life", "median"),
        max_half_life=("ou_half_life", "max"),
        median_sigma=("ou_sigma", "median"),
        median_spread=("median_spread", "median"),
        median_spread_to_sigma=("spread_to_sigma", "median"),
        median_hit_proxy=("hit_proxy_h50_vs_halfspread", "median"),
    )
    summary.sort_values(["median_hit_proxy", "median_spread_to_sigma"], ascending=[False, True]).to_csv(OUT_DIR / "45_stochastic_ou_summary.csv", index=False)


def synthetic_injection_check() -> None:
    rng = np.random.default_rng(20260429)
    n_days = 3
    n = 10000
    products = ["SYN_A_LEADER", "SYN_B_LAGGER", "SYN_C_SUFFIX", "SYN_D_TIME"]
    rows = []
    truth = [
        {"mechanic": "lead_lag", "source": "SYN_A_LEADER", "target": "SYN_B_LAGGER", "expected_side": "long", "horizon": 100},
        {"mechanic": "suffix", "source": "SYN_C_SUFFIX", "target": "SYN_C_SUFFIX", "expected_side": "long", "horizon": 100},
        {"mechanic": "time_bucket", "source": "SYN_D_TIME", "target": "SYN_D_TIME", "expected_side": "short", "horizon": 100},
    ]
    for day in range(2, 2 + n_days):
        base = rng.normal(0, 1, size=n).cumsum() * 0.5 + 10000
        leader = base + rng.normal(0, 3, size=n)
        lagger = base.copy() + rng.normal(0, 3, size=n)
        # Planted lead-lag: a leader 50-tick move causes delayed lagger
        # appreciation after the signal, not before it.
        leader_ret50 = np.r_[np.zeros(50), leader[50:] - leader[:-50]]
        event_idx = np.flatnonzero(leader_ret50 > 8)
        lead_impulse = np.zeros(n)
        for t in event_idx[::25]:
            lead_impulse[min(n, t + 20):min(n, t + 150)] += 0.45
        lagger += np.cumsum(lead_impulse)
        suffix = base + rng.normal(0, 4, size=n)
        timep = base + rng.normal(0, 4, size=n)
        for t in range(n):
            if int(suffix[t]) % 100 == 42:
                suffix[min(n - 1, t + 50):min(n, t + 120)] += 20
            if t % 500 in range(80, 120):
                timep[t:min(n, t + 100)] -= 0.25
        paths = [leader, lagger, suffix, timep]
        for product, path in zip(products, paths):
            for t, mid in enumerate(path):
                spread = 4
                rows.append({
                    "day": day,
                    "timestamp": t,
                    "product": product,
                    "bid_price_1": int(math.floor(mid - spread / 2)),
                    "ask_price_1": int(math.ceil(mid + spread / 2)),
                    "mid_price": float(mid),
                })
    df = pd.DataFrame(rows).sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    gp = df.groupby(["product", "day"], sort=False)
    for h in [50, 100, 200]:
        df[f"long_h{h}"] = gp["bid_price_1"].shift(-h) - df["ask_price_1"]
        df[f"short_h{h}"] = df["bid_price_1"] - gp["ask_price_1"].shift(-h)
    out_rows = []
    # Detect planted suffix.
    p = df[df["product"] == "SYN_C_SUFFIX"]
    for residue in range(100):
        event = (p["bid_price_1"] % 100) == residue
        vals = p.loc[event, "long_h100"].dropna()
        if len(vals) > 50:
            out_rows.append({"scan": "suffix", "key": residue, "side": "long", "horizon": 100, "count": len(vals), "edge": float(vals.mean()), "win": float((vals > 0).mean())})
    # Detect planted time bucket.
    p = df[df["product"] == "SYN_D_TIME"]
    for residue in range(500):
        event = (p["timestamp"] % 500) == residue
        vals = p.loc[event, "short_h100"].dropna()
        if len(vals) > 20:
            out_rows.append({"scan": "time_bucket", "key": residue, "side": "short", "horizon": 100, "count": len(vals), "edge": float(vals.mean()), "win": float((vals > 0).mean())})
    # Detect planted lead-lag.
    lead = df[df["product"] == "SYN_A_LEADER"].reset_index(drop=True)
    lag = df[df["product"] == "SYN_B_LAGGER"].reset_index(drop=True)
    move = lead.groupby("day")["mid_price"].diff(50)
    event = move > 8
    vals = lag.loc[event.fillna(False), "long_h100"].dropna()
    out_rows.append({"scan": "lead_lag", "key": "leader_ret50_gt_8", "side": "long", "horizon": 100, "count": len(vals), "edge": float(vals.mean()), "win": float((vals > 0).mean())})
    found = pd.DataFrame(out_rows).sort_values(["edge", "win"], ascending=[False, False])
    found.to_csv(OUT_DIR / "45_synthetic_injection_recovery.csv", index=False)
    pd.DataFrame(truth).to_csv(OUT_DIR / "45_synthetic_injection_truth.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lookback", type=int, default=64)
    parser.add_argument("--stride", type=int, default=5)
    parser.add_argument("--max-train", type=int, default=120000)
    parser.add_argument("--skip-rnn", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_features(load_prices())
    stochastic_diagnostics(df)
    synthetic_injection_check()
    if not args.skip_rnn:
        run_rnn(df, args.epochs, args.lookback, args.stride, args.max_train)
    print("wrote 45_rnn/stochastic/synthetic outputs")


if __name__ == "__main__":
    main()
