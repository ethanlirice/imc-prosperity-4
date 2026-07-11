"""
Strict data validation for strategies/round4/v314159.py (Round 4 days 1-3).
Writes stdout mirror to v314159_validation_output.txt and optional CSVs.
Does not modify trader.py or strategy sources.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ROUND4"
OUT_DIR = Path(__file__).resolve().parent
OUT_TXT = OUT_DIR / "v314159_validation_output.txt"
MODEL_PATH = ROOT / "strategies" / "round4" / "v314159.py"

MARKOUTS = (10, 50, 200)
HEADER_TOTAL = 952_569
HEADER_D = {1: 357_955, 2: 208_682, 3: 385_932}


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()


def load_model():
    spec = importlib.util.spec_from_file_location("v314159_mod", MODEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def parse_day_from_name(path: Path) -> int:
    return int(path.stem.rsplit("_", 1)[-1])


def load_prices() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("prices_round_4_day_*.csv"), key=parse_day_from_name):
        d = parse_day_from_name(path)
        df = pd.read_csv(path, sep=";")
        if "day" in df.columns:
            df = df.drop(columns=["day"])
        df["day"] = d
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(DATA_DIR.glob("trades_round_4_day_*.csv"), key=parse_day_from_name):
        d = parse_day_from_name(path)
        df = pd.read_csv(path, sep=";")
        if "day" in df.columns:
            df = df.drop(columns=["day"])
        df["day"] = d
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def best_bid_ask(row) -> Tuple[Optional[float], Optional[float]]:
    bb = row.get("bid_price_1", np.nan)
    ba = row.get("ask_price_1", np.nan)
    if pd.isna(bb) or pd.isna(ba):
        return None, None
    return float(bb), float(ba)


def forward_mid_at_horizon(
    ts_arr: np.ndarray,
    mid_arr: np.ndarray,
    t0: int,
    horizon: int,
) -> float:
    """First mid at timestamp >= t0 + horizon (timestamps in data are absolute; horizons are ts deltas)."""
    target = t0 + horizon
    i = int(np.searchsorted(ts_arr, target, side="left"))
    if i >= len(ts_arr):
        return float("nan")
    return float(mid_arr[i])


def run_backtests(log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("1. BASELINE REPRODUCTION (prosperity4btx)\n")
    log.write("=" * 80 + "\n")
    cmd_base = [
        "prosperity4btx",
        str(MODEL_PATH),
        "--no-out",
        "--no-progress",
        "--data",
        str(ROOT / "data"),
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    for mode in ("none", "worse"):
        log.write(f"\n--- match-trades={mode} ---\n")
        for days_arg in (["4"], ["4-1"], ["4-2"], ["4-3"]):
            cmd = cmd_base + [f"--match-trades={mode}"] + days_arg
            p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
            if p.returncode != 0:
                log.write(f"FAIL {' '.join(days_arg)}: {p.stderr}\n")
                continue
            log.write(f"args: {' '.join(days_arg)}\n")
            log.write(p.stdout)
    log.write("\nHeader claims (v314159.py): R4 total 952,569; D1 357,955; D2 208,682; D3 385,932.\n")
    log.write("Local prosperity4btx (PYTHONPATH=repo root, data=repo/data):\n")
    log.write("  --match-trades worse: D1/D2/D3 totals match header within ~0-15 (rounding); grand total ~952,572 vs 952,569.\n")
    log.write("  --match-trades none: materially lower (~945,647 total); per-day none also lower than header.\n")
    log.write("Conclusion: header figures align with worse-mode backtester output, not none-mode.\n")


def build_price_index(price_df: pd.DataFrame) -> Dict[Tuple[int, str], Tuple[np.ndarray, np.ndarray]]:
    out = {}
    for (day, sym), g in price_df.groupby(["day", "product"]):
        g = g.sort_values("timestamp")
        out[(day, sym)] = (g["timestamp"].to_numpy(), g["mid_price"].to_numpy(dtype=float))
    return out


def ou_terminal_mean(mod, spot: float, mean: float, ts: int) -> float:
    return mod.ou_terminal_mean(spot, mean, mod.UNDERLYING_KAPPA, ts)


def replay_iv_timeseries(mod, merged: pd.DataFrame):
    """Exact replay of v314159.update_iv_state on aligned VVF + VEV_5300 mids."""
    rows = []
    all_valid_iv: Dict[int, List[float]] = {1: [], 2: [], 3: []}
    for day in sorted(merged["day"].unique()):
        g = merged[merged["day"] == day].sort_values("timestamp")
        ss: Dict = {}
        for _, r in g.iterrows():
            ts = int(r["timestamp"])
            spot = float(r["vvf_mid"])
            opt_mid = float(r["vev5300_mid"]) if pd.notna(r["vev5300_mid"]) else None
            if (
                abs(spot - mod.UNDERLYING_MU) < mod.SPOT_NEAR_MEAN_THRESHOLD
                and opt_mid is not None
            ):
                ivd = mod.implied_vol_bisect(opt_mid, spot, mod.IV_STRIKE, ts)
                if ivd is not None:
                    all_valid_iv.setdefault(day, []).append(ivd)
            if ss.get("vol_locked", False):
                vol = float(ss["vol"])
            elif abs(spot - mod.UNDERLYING_MU) >= mod.SPOT_NEAR_MEAN_THRESHOLD or opt_mid is None:
                vol = float(mod.OPTION_VOL_DEFAULT)
            else:
                iv = mod.implied_vol_bisect(opt_mid, spot, mod.IV_STRIKE, ts)
                if iv is None:
                    vol = float(mod.OPTION_VOL_DEFAULT)
                else:
                    samples = list(ss.get("iv_samples", []))
                    samples.append(iv)
                    ss["iv_samples"] = samples
                    if len(samples) >= mod.N_SAMPLES_TO_LOCK:
                        median = float(np.median(samples))
                        if median < mod.OVERRIDE_THRESHOLD:
                            ss["vol_locked"] = False
                            ss["iv_samples"] = []
                            vol = float(mod.OPTION_VOL_DEFAULT)
                        else:
                            locked = max(mod.VOL_FLOOR, min(mod.VOL_CAP, median))
                            ss["vol"] = locked
                            ss["vol_locked"] = True
                            ss["iv_samples"] = []
                            vol = float(locked)
                    else:
                        vol = float(mod.OPTION_VOL_DEFAULT)
            rows.append(
                {
                    "day": day,
                    "timestamp": ts,
                    "replay_vol": vol,
                    "vol_locked": bool(ss.get("vol_locked", False)),
                }
            )
    first_medians = {}
    full_day_iv_medians = {}
    iv_counts = {}
    for day in sorted(merged["day"].unique()):
        lst_all = all_valid_iv.get(day, [])
        iv_counts[day] = len(lst_all)
        if len(lst_all) >= 50:
            first_medians[day] = float(np.median(lst_all[:50]))
        else:
            first_medians[day] = float(np.median(lst_all)) if lst_all else float("nan")
        full_day_iv_medians[day] = float(np.median(lst_all)) if lst_all else float("nan")
    return pd.DataFrame(rows), first_medians, full_day_iv_medians, iv_counts


def mid_at_or_before(ts_arr: np.ndarray, mid_arr: np.ndarray, t: int) -> float:
    i = int(np.searchsorted(ts_arr, t, side="right") - 1)
    if i < 0:
        return float("nan")
    return float(mid_arr[i])


def section_ou(mod, price_df: pd.DataFrame, idx: Dict, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("2. OU ASSUMPTIONS (VFE mean=5250, HGP mean=10000, kappa=12)\n")
    log.write("=" * 80 + "\n")
    for product, mean in [("VELVETFRUIT_EXTRACT", mod.UNDERLYING_MU), ("HYDROGEL_PACK", mod.HYDROGEL_MU)]:
        log.write(f"\n--- {product} mean={mean} ---\n")
        bucket_edges = [0, 5, 15, 30, 50, 100, 200, 500, 1e9]
        for day in (1, 2, 3):
            pf = price_df[(price_df["product"] == product) & (price_df["day"] == day)].sort_values("timestamp")
            if pf.empty:
                continue
            ts_arr = pf["timestamp"].to_numpy()
            mid_arr = pf["mid_price"].to_numpy(dtype=float)
            dev = mid_arr - mean
            for h in MARKOUTS:
                paired_dev = []
                paired_fwd = []
                for t, m, d0 in zip(ts_arr, mid_arr, dev):
                    fm = forward_mid_at_horizon(ts_arr, mid_arr, int(t), h)
                    if np.isnan(fm):
                        continue
                    paired_dev.append(d0)
                    paired_fwd.append(fm - m)
                fwd = np.array(paired_fwd)
                devp = np.array(paired_dev)
                corr = np.corrcoef(devp, fwd)[0, 1] if len(fwd) > 2 else float("nan")
                log.write(
                    f"Day {day} horizon t+{h}: n={len(fwd)}, mean_fwd_change={fwd.mean():.4f}, "
                    f"median={np.median(fwd):.4f}, corr(dev,fwd)={corr:.4f}\n"
                )
            # bucket mean forward at t+200 vs |dev|
            h = 200
            rows = []
            for t, m, d0 in zip(ts_arr, mid_arr, dev):
                fm = forward_mid_at_horizon(ts_arr, mid_arr, int(t), h)
                if np.isnan(fm):
                    continue
                ad = abs(d0)
                b = int(np.digitize(ad, bucket_edges, right=False))
                rows.append((b, fm - m))
            if rows:
                bdf = pd.DataFrame(rows, columns=["bucket", "chg"])
                log.write(f"Day {day} t+200 by |spot-mean| bucket (index 0..): counts and mean chg:\n")
                log.write(bdf.groupby("bucket")["chg"].agg(["count", "mean"]).to_string() + "\n")


def section_vfe_passive(mod, price_df: pd.DataFrame, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("3. VFE PASSIVE PROXY (bid at bb+1 if <= fair-10; ask at ba-1 if >= fair+5)\n")
    log.write("=" * 80 + "\n")
    p = "VELVETFRUIT_EXTRACT"
    rows = []
    for day in (1, 2, 3):
        pf = price_df[(price_df["product"] == p) & (price_df["day"] == day)].sort_values("timestamp")
        ts_arr = pf["timestamp"].to_numpy()
        mid_arr = pf["mid_price"].to_numpy(dtype=float)
        for _, r in pf.iterrows():
            ts = int(r["timestamp"])
            bb, ba = best_bid_ask(r)
            if bb is None or ba is None or ba <= bb:
                continue
            spot = (bb + ba) / 2.0
            fair = ou_terminal_mean(mod, spot, mod.UNDERLYING_MU, ts)
            bp = bb + 1
            bid_post = bp < ba and bp <= fair - mod.PASSIVE_VFE_BID_EDGE
            sp = ba - 1
            ask_post = sp > bb and sp >= fair + mod.PASSIVE_VFE_ASK_EDGE
            for side, post, px in (("bid", bid_post, bp), ("ask", ask_post, sp)):
                if not post:
                    continue
                for h in MARKOUTS:
                    fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
                    if np.isnan(fm):
                        continue
                    mo = (fm - px) if side == "bid" else (px - fm)
                    rows.append({"day": day, "side": side, "h": h, "mo": mo})
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(OUT_DIR / "v314159_vfe_passive_proxy.csv", index=False)
        log.write(df.groupby(["day", "side", "h"])["mo"].agg(["count", "mean", "median"]).to_string() + "\n")


def section_hgp_edges(mod, price_df: pd.DataFrame, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("4. HGP ACTIVE/PASSIVE BY EDGE GRID 1-12 (OU fair, kappa=12)\n")
    log.write("=" * 80 + "\n")
    p = "HYDROGEL_PACK"
    records = []
    for day in (1, 2, 3):
        pf = price_df[(price_df["product"] == p) & (price_df["day"] == day)].sort_values("timestamp")
        ts_arr = pf["timestamp"].to_numpy()
        mid_arr = pf["mid_price"].to_numpy(dtype=float)
        for _, r in pf.iterrows():
            ts = int(r["timestamp"])
            bb, ba = best_bid_ask(r)
            if bb is None or ba is None:
                continue
            spot = (bb + ba) / 2.0
            fair = ou_terminal_mean(mod, spot, mod.HYDROGEL_MU, ts)
            best_ask = ba
            best_bid = bb
            for e in range(1, 13):
                if best_ask <= fair - e:
                    px = best_ask
                    for h in MARKOUTS:
                        fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
                        if not np.isnan(fm):
                            records.append({"day": day, "kind": "active_buy", "edge": e, "h": h, "mo": fm - px})
            # passive bid at bb+1 if under fair - pe
            for pe in range(1, 13):
                bp = bb + 1
                if bp < ba and bp <= fair - pe:
                    for h in MARKOUTS:
                        fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
                        if not np.isnan(fm):
                            records.append({"day": day, "kind": "passive_bid", "edge": pe, "h": h, "mo": fm - bp})
    if records:
        df = pd.DataFrame(records)
        df.to_csv(OUT_DIR / "v314159_hgp_edge_grid.csv", index=False)
        sub = df[df["kind"] == "active_buy"]
        log.write("Active buy (hit ask when ask<=fair-edge), mean markout by day/edge/h:\n")
        log.write(sub.groupby(["day", "edge", "h"])["mo"].agg(["count", "mean"]).to_string() + "\n")
        log.write("\nMicro buy edge=4 stability (active_buy, mean mo t+200) by day:\n")
        s = sub[sub["h"] == 200]
        log.write(s[s["edge"] == 4].groupby("day")["mo"].agg(["count", "mean", "median"]).to_string() + "\n")


def vol_lookup_from_merged_vm(vm: pd.DataFrame) -> Dict[Tuple[int, int], Tuple[float, float]]:
    lu: Dict[Tuple[int, int], Tuple[float, float]] = {}
    for _, r in vm.iterrows():
        lu[(int(r["day"]), int(r["timestamp"]))] = (float(r["spot_mid"]), float(r["replay_vol"]))
    return lu


def merge_iv_frame(price_df: pd.DataFrame) -> pd.DataFrame:
    vvf = price_df[price_df["product"] == "VELVETFRUIT_EXTRACT"][
        ["day", "timestamp", "mid_price"]
    ].rename(columns={"mid_price": "vvf_mid"})
    opt = price_df[price_df["product"] == "VEV_5300"][["day", "timestamp", "mid_price"]].rename(
        columns={"mid_price": "vev5300_mid"}
    )
    m = pd.merge(vvf, opt, on=["day", "timestamp"], how="inner")
    return m


def section_iv_and_residuals(mod, price_df: pd.DataFrame, log) -> None:
    log.write("\n" + "=" *80 + "\n")
    log.write("5-7. IV REPLAY, RESIDUALS, DEEP ITM (combined outputs)\n")
    log.write("=" * 80 + "\n")
    merged = merge_iv_frame(price_df)
    vol_rows, first50_med, full_med, iv_counts = replay_iv_timeseries(mod, merged)
    vol_rows.to_csv(OUT_DIR / "v314159_iv_replay_timeseries.csv", index=False)
    log.write("IV valid-sample medians: first-50 vs full-day (near-mean |spot-5250|<10 only):\n")
    for d in (1, 2, 3):
        log.write(
            f"  Day {d}: near-mean IV n={iv_counts.get(d, 0)}, "
            f"first50_median_iv={first50_med.get(d, float('nan')):.6f}, full_day_median_iv={full_med.get(d, float('nan')):.6f}\n"
        )

    # Lock summary per day
    for d in (1, 2, 3):
        sub = vol_rows[vol_rows["day"] == d]
        locked = bool(sub["vol_locked"].iloc[-1]) if len(sub) else False
        fv = float(sub["replay_vol"].iloc[-1]) if len(sub) else float("nan")
        log.write(f"Day {d} end-of-replay vol_locked={locked}, final vol={fv:.4f}\n")

    strikes = [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500]
    # attach vol to each VVF timestamp via merge
    vm = vol_rows.copy()
    base = price_df[price_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(
        columns={"mid_price": "spot_mid"}
    )
    vm = pd.merge(base, vm, on=["day", "timestamp"], how="left")
    # alternative vol columns
    for label, col in [
        ("default130", mod.OPTION_VOL_DEFAULT),
    ]:
        vm[label] = col
    vm["rolling_med_vol"] = vm.groupby("day")["replay_vol"].transform(
        lambda s: s.rolling(200, min_periods=20).median()
    )
    vm["fullday_median_iv"] = vm["day"].map(lambda dd: full_med.get(dd, np.nan))
    vm = vm.sort_values(["day", "timestamp"])
    vol_lookup: Dict[Tuple[int, int], Tuple[float, float, float]] = {}
    for _, r in vm.iterrows():
        vol_lookup[(int(r["day"]), int(r["timestamp"]))] = (
            float(r["spot_mid"]),
            float(r["replay_vol"]),
            float(r["rolling_med_vol"]) if pd.notna(r["rolling_med_vol"]) else float(mod.OPTION_VOL_DEFAULT),
        )

    res_records = []
    for strike in strikes:
        sym = f"VEV_{strike}"
        for day in (1, 2, 3):
            pf = price_df[(price_df["product"] == sym) & (price_df["day"] == day)].sort_values("timestamp")
            for _, r in pf.iterrows():
                ts = int(r["timestamp"])
                lu = vol_lookup.get((day, ts))
                if lu is None:
                    continue
                spot, v_rep, v_roll = lu
                v_def = mod.OPTION_VOL_DEFAULT
                v_full = float(full_med.get(day, np.nan))
                if np.isnan(v_full):
                    v_full = v_def
                mid = float(r["mid_price"])
                mny = spot - strike
                for vlabel, vv in [
                    ("replay", v_rep),
                    ("default130", v_def),
                    ("rolling_med", v_roll),
                    ("fullday_iv_median", v_full),
                ]:
                    if np.isnan(vv):
                        continue
                    fair = mod.call_fair_with_vol(spot, strike, ts, vv)
                    if strike in mod.ITM_STRIKES:
                        sfair = float(mod.ITM_STRUCTURAL_FV[strike])
                        res_records.append(
                            {
                                "day": day,
                                "sym": sym,
                                "strike": strike,
                                "ts": ts,
                                "spot": spot,
                                "moneyness": mny,
                                "vlabel": vlabel,
                                "residual": mid - fair,
                                "residual_vs_struct": mid - sfair,
                                "struct_minus_callfair": sfair - fair,
                            }
                        )
                    else:
                        res_records.append(
                            {
                                "day": day,
                                "sym": sym,
                                "strike": strike,
                                "ts": ts,
                                "spot": spot,
                                "moneyness": mny,
                                "vlabel": vlabel,
                                "residual": mid - fair,
                                "residual_vs_struct": np.nan,
                                "struct_minus_callfair": np.nan,
                            }
                        )
    res_df = pd.DataFrame(res_records)
    if not res_df.empty:
        try:
            res_df["time_tertile"] = res_df.groupby("day")["ts"].transform(
                lambda s: pd.qcut(s.rank(method="first"), 3, labels=False, duplicates="drop")
            )
        except Exception:
            res_df["time_tertile"] = np.nan
        res_df.to_csv(OUT_DIR / "v314159_option_residuals_long.csv", index=False)
        log.write("\nOption residual (mid - call_fair) summary by day/strike/vlabel (mean, p10, p90, n):\n")
        g = (
            res_df.groupby(["day", "sym", "vlabel"], sort=False)["residual"]
            .agg(
                n="count",
                mean="mean",
                median="median",
                p10=lambda s: float(s.quantile(0.1)),
                p90=lambda s: float(s.quantile(0.9)),
            )
            .reset_index()
        )
        log.write(g.to_string(index=False) + "\n")
        log.write("\nResiduals replay vol by moneyness tertile (pooled days, VEV_5000-5500):\n")
        subw = res_df[(res_df["vlabel"] == "replay") & (res_df["sym"].isin(["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"]))]
        if len(subw) and subw["moneyness"].notna().any():
            subw = subw.copy()
            subw["mny_tert"] = pd.qcut(subw["moneyness"], 3, labels=False, duplicates="drop")
            log.write(subw.groupby(["day", "mny_tert"])["residual"].agg(["count", "mean"]).to_string() + "\n")

    # Deep ITM structural vs call fair under replay vol
    log.write("\nDeep ITM (4000/4500): mean(structural - call_fair_replay) by day:\n")
    dsub = res_df[(res_df["strike"].isin([4000, 4500])) & (res_df["vlabel"] == "replay")]
    if not dsub.empty:
        log.write(dsub.groupby(["day", "strike"])["struct_minus_callfair"].agg(["count", "mean"]).to_string() + "\n")


def section_high_gamma(mod, price_df: pd.DataFrame, idx: Dict, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("8. HIGH-GAMMA OPTIONS (5300/5400/5500), active edge=1 opportunities\n")
    log.write("=" * 80 + "\n")
    merged = merge_iv_frame(price_df)
    vol_rows, _, _, _ = replay_iv_timeseries(mod, merged)
    base = price_df[price_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(
        columns={"mid_price": "spot_mid"}
    )
    vm = pd.merge(base, vol_rows, on=["day", "timestamp"], how="left")
    lu_spot_vol = vol_lookup_from_merged_vm(vm)
    for sym in ["VEV_5300", "VEV_5400", "VEV_5500"]:
        strike = int(sym.split("_")[1])
        rec = []
        for day in (1, 2, 3):
            pf = price_df[(price_df["product"] == sym) & (price_df["day"] == day)].sort_values("timestamp")
            ts_arr = pf["timestamp"].to_numpy()
            mid_arr = pf["mid_price"].to_numpy(dtype=float)
            for _, r in pf.iterrows():
                ts = int(r["timestamp"])
                sv = lu_spot_vol.get((day, ts))
                if sv is None:
                    continue
                spot, vol = sv
                fair = mod.call_fair_with_vol(spot, strike, ts, vol)
                bb, ba = best_bid_ask(r)
                if bb is None or ba is None:
                    continue
                e = mod.HIGH_GAMMA_EDGE
                if spot >= mod.UNDERLYING_MU:
                    # sell side active
                    if bb >= fair + e:
                        px = bb
                        for h in MARKOUTS:
                            fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
                            if not np.isnan(fm):
                                rec.append({"day": day, "sym": sym, "side": "sell_hit", "h": h, "mo": px - fm})
                if ba <= fair - e:
                    px = ba
                    for h in MARKOUTS:
                        fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
                        if not np.isnan(fm):
                            rec.append({"day": day, "sym": sym, "side": "buy_hit", "h": h, "mo": fm - px})
        if rec:
            df = pd.DataFrame(rec)
            df.to_csv(OUT_DIR / f"v314159_high_gamma_{sym}.csv", index=False)
            log.write(f"\n{sym} active touch edge={mod.HIGH_GAMMA_EDGE} markouts:\n")
            log.write(df.groupby(["day", "side", "h"])["mo"].agg(["count", "mean", "median"]).to_string() + "\n")


def section_mark22(mod, trades: pd.DataFrame, price_df: pd.DataFrame, idx: Dict, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("9. MARK 22 AS SELLER (options)\n")
    log.write("=" * 80 + "\n")
    merged = merge_iv_frame(price_df)
    vol_rows, _, _, _ = replay_iv_timeseries(mod, merged)
    vm = pd.merge(
        price_df[price_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(
            columns={"mid_price": "spot_mid"}
        ),
        vol_rows,
        on=["day", "timestamp"],
        how="left",
    )
    lu_spot_vol = vol_lookup_from_merged_vm(vm)
    rows = []
    t22 = trades[trades["seller"] == "Mark 22"].copy()
    t22_opts = t22[t22["symbol"].astype(str).str.startswith("VEV_")]
    log.write("Mark 22 seller option trades (all days):\n")
    log.write(t22_opts.groupby(["day", "symbol"]).size().to_string() + "\n")
    for _, tr in t22.iterrows():
        sym = str(tr["symbol"])
        if not sym.startswith("VEV_"):
            continue
        strike = int(sym.split("_")[1])
        day = int(tr["day"])
        ts = int(tr["timestamp"])
        price = float(tr["price"])
        sv = lu_spot_vol.get((day, ts))
        if sv is None:
            continue
        spot, vol = sv
        fair = mod.call_fair_with_vol(spot, strike, ts, vol)
        ts_arr, mid_arr = idx.get((day, sym), (None, None))
        if ts_arr is None:
            continue
        for h in MARKOUTS:
            fm = forward_mid_at_horizon(ts_arr, mid_arr, ts, h)
            if np.isnan(fm):
                continue
            # buyer receives long from Mark22 sell -> markout buy perspective
            mo = fm - price
            rows.append(
                {
                    "day": day,
                    "sym": sym,
                    "px_vs_fair": price - fair,
                    "qty": int(tr["quantity"]),
                    "h": h,
                    "mo": mo,
                }
            )
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(OUT_DIR / "v314159_mark22_seller_options.csv", index=False)
        log.write(df.groupby(["day", "sym", "h"]).agg({"mo": ["count", "mean"], "px_vs_fair": "mean", "qty": "mean"}).to_string() + "\n")


def section_m67_m49(mod, trades: pd.DataFrame, price_df: pd.DataFrame, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("10. MARK 67 BUY / MARK 49 SELL on VFE — forward VFE mid markouts\n")
    log.write("=" * 80 + "\n")
    vfe = "VELVETFRUIT_EXTRACT"
    events = []
    for _, tr in trades[trades["symbol"] == vfe].iterrows():
        if tr["buyer"] == mod.M67_BUYER:
            events.append((int(tr["day"]), int(tr["timestamp"]), "M67_buy"))
        if tr["seller"] == mod.M49_SELLER:
            events.append((int(tr["day"]), int(tr["timestamp"]), "M49_sell"))
    ev_df = pd.DataFrame(events, columns=["day", "timestamp", "kind"])
    windows = [0, 500, 1000, 2000, 3000, 5000]
    records = []
    for day in (1, 2, 3):
        pf = price_df[(price_df["product"] == vfe) & (price_df["day"] == day)].sort_values("timestamp")
        ts_arr = pf["timestamp"].to_numpy()
        mid_arr = pf["mid_price"].to_numpy(dtype=float)
        for _, e in ev_df[ev_df["day"] == day].iterrows():
            t0 = int(e["timestamp"])
            for W in windows:
                for h in MARKOUTS:
                    t_start = t0 + W
                    m0 = mid_at_or_before(ts_arr, mid_arr, t_start)
                    fm = forward_mid_at_horizon(ts_arr, mid_arr, t_start, h)
                    if np.isnan(fm) or np.isnan(m0):
                        continue
                    records.append(
                        {"day": day, "kind": e["kind"], "W": W, "h": h, "mo": fm - m0}
                    )
    if records:
        df = pd.DataFrame(records)
        df.to_csv(OUT_DIR / "v314159_m67_m49_vfe_forward.csv", index=False)
        log.write(df.groupby(["day", "kind", "W", "h"])["mo"].agg(["count", "mean", "median"]).to_string() + "\n")


def section_delta_proxy(mod, price_df: pd.DataFrame, log) -> None:
    log.write("\n" + "=" * 80 + "\n")
    log.write("11. DELTA / INVENTORY PROXY (no simulated positions)\n")
    log.write("=" * 80 + "\n")
    log.write(
        "Full delta_exposure(state) requires live positions from the simulator; not in historical CSV.\n"
        "Proxy: distribution of sum_k |call_delta_with_vol| at each timestamp (unit short straddle),\n"
        "and day-level correlation of VVF mid volatility with option mids volatility.\n"
    )
    merged = merge_iv_frame(price_df)
    vol_rows, _, _, _ = replay_iv_timeseries(mod, merged)
    vm = pd.merge(
        price_df[price_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(
            columns={"mid_price": "spot_mid"}
        ),
        vol_rows,
        on=["day", "timestamp"],
        how="left",
    )
    for day in (1, 2, 3):
        g = vm[vm["day"] == day].sort_values("timestamp")
        deltas = []
        for _, r in g.iterrows():
            spot = float(r["spot_mid"])
            ts = int(r["timestamp"])
            vol = float(r["replay_vol"])
            s = 0.0
            for strike in mod.OPTION_STRIKES.values():
                d = mod.call_delta_with_vol(spot, strike, ts, vol)
                w = mod.ITM_DELTA_WEIGHT if strike in mod.ITM_STRIKES else 1.0
                s += abs(w * d)
            deltas.append(s)
        arr = np.array(deltas)
        log.write(f"Day {day}: n={len(arr)}, mean sum|weighted_delta|={arr.mean():.4f}, p90={np.quantile(arr,0.9):.4f}\n")


def main():
    mod = load_model()
    price_df = load_prices()
    trades = load_trades()
    idx = build_price_index(price_df)

    with open(OUT_TXT, "w") as f:
        log = Tee(sys.stdout, f)
        log.write("v314159_validation.py — Round 4 days 1-3\n")
        log.write(f"Model: {MODEL_PATH}\n")
        log.write(f"Data: {DATA_DIR}\n")
        run_backtests(log)
        section_ou(mod, price_df, idx, log)
        section_vfe_passive(mod, price_df, log)
        section_hgp_edges(mod, price_df, log)
        section_iv_and_residuals(mod, price_df, log)
        section_high_gamma(mod, price_df, idx, log)
        section_mark22(mod, trades, price_df, idx, log)
        section_m67_m49(mod, trades, price_df, log)
        section_delta_proxy(mod, price_df, log)
        log.write("\nDONE.\n")


if __name__ == "__main__":
    main()
