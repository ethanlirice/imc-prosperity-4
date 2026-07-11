"""Round 4 manual challenge - "Vanilla Just Isn't Exotic Enough".

Full analytical + Monte Carlo pricing for every listed contract under the
spec in `wiki/round4manual.md`:
  S0 = 50, sigma = 2.51 ann, r = q = 0
  GBM, 4 steps/day, 252 days/yr, 5 days/week
  Score = mean PnL across 100 sims, hold-to-expiry, no rebalance
  Contract size 3000 (flat PnL multiplier)

Outputs:
  - per-contract closed-form / MC fair value
  - bid/ask edge per contract
  - 100-sim mark variance (since the *mark itself* is a random 100-path
    average; this drives the realized score noise)
  - portfolio expected score and SD across many (100-sim) marks
  - greedy max-edge portfolio + LP-equivalent (bang-bang) at volume caps
"""

import json
import math
import os
import sys
import time

import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Spec constants
# ---------------------------------------------------------------------------
S0 = 50.0
SIGMA = 2.51
R = 0.0
TRADING_DAYS_PER_YEAR = 252
STEPS_PER_DAY = 4
STEPS_PER_YEAR = TRADING_DAYS_PER_YEAR * STEPS_PER_DAY
CONTRACT_SIZE = 3000

T_2W = (10) / TRADING_DAYS_PER_YEAR        # 10 trading days
T_3W = (15) / TRADING_DAYS_PER_YEAR        # 15 trading days
N_2W = 10 * STEPS_PER_DAY                  # 40 steps
N_3W = 15 * STEPS_PER_DAY                  # 60 steps
N_T1 = 10 * STEPS_PER_DAY                  # chooser decision after 14 calendar / 10 trading? See doc.

# Chooser doc: "After 14 Solvenarian Days" => decision at index N_DECIDE_CHOOSER
# But Solvenarian "days" earlier said weeks-to-years uses 5 trading days/week,
# so 14 Solvenarian days = 14 trading days = 56 steps? Let me re-read.
# "2 weeks" = 10 trading days = 40 steps. "After 14 Solvenarian Days" — but
# the spec says "After 2 weeks" (= 10 trading days) elsewhere. The detail
# says T+14 / T+21. Convention used in chooser identity: t1 = 2 weeks, T = 3 weeks.
# Stick with 2-week decision = 40 steps, 3-week expiry = 60 steps.
N_DECIDE = N_2W  # 40
N_EXPIRY_3W = N_3W  # 60
N_EXPIRY_2W = N_2W  # 40

# ---------------------------------------------------------------------------
# Listed contracts
# ---------------------------------------------------------------------------
# (name, type, params dict, bid, ask, max_volume)
CONTRACTS = [
    # spot
    {"name": "AC",         "type": "spot",  "bid": 49.975, "ask": 50.025, "max": 200},
    # 3-week vanilla puts
    {"name": "AC_50_P",    "type": "put",   "K": 50, "T_steps": N_3W, "bid": 12.00, "ask": 12.05, "max": 50},
    {"name": "AC_45_P",    "type": "put",   "K": 45, "T_steps": N_3W, "bid":  9.05, "ask":  9.10, "max": 50},
    {"name": "AC_40_P",    "type": "put",   "K": 40, "T_steps": N_3W, "bid":  6.50, "ask":  6.55, "max": 50},
    {"name": "AC_35_P",    "type": "put",   "K": 35, "T_steps": N_3W, "bid":  4.33, "ask":  4.35, "max": 50},
    # 3-week vanilla calls
    {"name": "AC_50_C",    "type": "call",  "K": 50, "T_steps": N_3W, "bid": 12.00, "ask": 12.05, "max": 50},
    {"name": "AC_60_C",    "type": "call",  "K": 60, "T_steps": N_3W, "bid":  8.80, "ask":  8.85, "max": 50},
    # 2-week vanilla
    {"name": "AC_50_P_2",  "type": "put",   "K": 50, "T_steps": N_2W, "bid":  9.70, "ask":  9.75, "max": 50},
    {"name": "AC_50_C_2",  "type": "call",  "K": 50, "T_steps": N_2W, "bid":  9.70, "ask":  9.75, "max": 50},
    # exotics
    {"name": "AC_50_CO",   "type": "chooser","K": 50, "T_steps": N_3W, "T_decide": N_DECIDE, "bid": 22.20, "ask": 22.30, "max": 50},
    {"name": "AC_40_BP",   "type": "binput","K": 40, "T_steps": N_3W, "payout": 10.0, "bid":  5.00, "ask":  5.10, "max": 50},
    {"name": "AC_45_KO",   "type": "doput", "K": 45, "B": 35, "T_steps": N_3W, "bid":  0.15, "ask": 0.175, "max": 500},
]

# ---------------------------------------------------------------------------
# Closed-form (Black-Scholes, r = q = 0)
# ---------------------------------------------------------------------------
def _phi(x):  # standard normal CDF
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def bs_call(S, K, T, sigma):
    if T <= 0:
        return max(S - K, 0.0)
    sT = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sT * sT) / sT
    d2 = d1 - sT
    return S * _phi(d1) - K * _phi(d2)

def bs_put(S, K, T, sigma):
    if T <= 0:
        return max(K - S, 0.0)
    return bs_call(S, K, T, sigma) - (S - K)  # put-call parity at r=0

def bs_binary_put(S, K, T, sigma, payout=1.0):
    """Cash-or-nothing binary put: pays `payout` if S_T < K."""
    if T <= 0:
        return payout if S < K else 0.0
    sT = sigma * math.sqrt(T)
    d2 = (math.log(S / K) - 0.5 * sT * sT) / sT
    return payout * _phi(-d2)

def reiner_rubinstein_doput(S, K, B, T, sigma, r=0.0, q=0.0):
    """Down-and-out put (continuous monitoring), Reiner-Rubinstein 1991.
    Assumes B < S (otherwise immediately knocked out)."""
    if S <= B:
        return 0.0
    if T <= 0:
        return max(K - S, 0.0) if S > B else 0.0
    sT = sigma * math.sqrt(T)
    mu = (r - q - 0.5 * sigma * sigma) / (sigma * sigma)
    lam = math.sqrt(mu * mu + 2.0 * r / (sigma * sigma)) if sigma > 0 else 0.0

    # Standard formulas; B<K case (knock-out below strike) differs from B>=K.
    x1 = math.log(S / K) / sT + (1 + mu) * sT
    x2 = math.log(S / B) / sT + (1 + mu) * sT
    y1 = math.log(B * B / (S * K)) / sT + (1 + mu) * sT
    y2 = math.log(B / S) / sT + (1 + mu) * sT

    A = -S * math.exp(-q * T) * _phi(-x1) + K * math.exp(-r * T) * _phi(-x1 + sT)
    B_ = -S * math.exp(-q * T) * _phi(-x2) + K * math.exp(-r * T) * _phi(-x2 + sT)
    C = -S * math.exp(-q * T) * (B / S) ** (2 * (mu + 1)) * _phi(y1) + \
        K * math.exp(-r * T) * (B / S) ** (2 * mu) * _phi(y1 - sT)
    D = -S * math.exp(-q * T) * (B / S) ** (2 * (mu + 1)) * _phi(y2) + \
        K * math.exp(-r * T) * (B / S) ** (2 * mu) * _phi(y2 - sT)

    # Down-and-out put with B < K: P_DO = A - B + C - D  (Haug, 2007 table)
    if B < K:
        return A - B_ + C - D
    # B >= K: P_DO = 0 (knock-out at-or-above strike makes no sense)
    return 0.0

# ---------------------------------------------------------------------------
# Monte Carlo paths (single shared simulation, used for every contract)
# ---------------------------------------------------------------------------
def gbm_paths(n_paths, n_steps, S0, sigma, dt, antithetic=True, seed=0):
    rng = np.random.default_rng(seed)
    if antithetic:
        half = n_paths // 2
        z = rng.standard_normal((half, n_steps))
        z = np.concatenate([z, -z], axis=0)
        if z.shape[0] < n_paths:
            extra = rng.standard_normal((n_paths - z.shape[0], n_steps))
            z = np.concatenate([z, extra], axis=0)
    else:
        z = rng.standard_normal((n_paths, n_steps))
    drift = -0.5 * sigma * sigma * dt
    diffusion = sigma * math.sqrt(dt)
    log_increments = drift + diffusion * z
    log_paths = np.cumsum(log_increments, axis=1)
    paths = S0 * np.exp(log_paths)
    paths = np.concatenate([np.full((n_paths, 1), S0), paths], axis=1)
    return paths  # shape (n_paths, n_steps+1)

# ---------------------------------------------------------------------------
# MC payoffs given a path matrix
# ---------------------------------------------------------------------------
def payoff_call(paths, K, T_steps):
    return np.maximum(paths[:, T_steps] - K, 0.0)

def payoff_put(paths, K, T_steps):
    return np.maximum(K - paths[:, T_steps], 0.0)

def payoff_binput(paths, K, T_steps, payout):
    return payout * (paths[:, T_steps] < K).astype(np.float64)

def payoff_doput(paths, K, B, T_steps):
    """Discrete-monitored down-and-out put.
    Knocked out if min along the path (steps 1..T_steps inclusive) <= B.
    `paths[:,0] = S0` is excluded from monitoring."""
    sub = paths[:, 1:T_steps + 1]
    knocked = (sub <= B).any(axis=1)
    payoff = np.maximum(K - paths[:, T_steps], 0.0)
    payoff[knocked] = 0.0
    return payoff

def payoff_chooser(paths, K, T_decide, T_expiry):
    """At t1 = T_decide, holder chooses call or put. Doc says "side that is
    in the money". With r=0 and K=S0, intrinsic > 0 side equals higher-value
    side (put-call parity), so this is the standard chooser. Implementation
    picks the side with higher conditional value as of t1 (using BS on the
    remaining time)."""
    S_t1 = paths[:, T_decide]
    S_T  = paths[:, T_expiry]
    remaining_years = (T_expiry - T_decide) / STEPS_PER_YEAR
    sT = SIGMA * math.sqrt(remaining_years)
    # value of call and put at t1, given S_t1 and remaining time
    # (vectorized BS, r=q=0)
    eps = 1e-12
    log_ratio = np.log(S_t1 / K + eps)
    d1 = (log_ratio + 0.5 * sT * sT) / sT
    d2 = d1 - sT
    cdf = lambda x: 0.5 * (1.0 + np_erf(x / math.sqrt(2.0)))
    call_val = S_t1 * cdf(d1) - K * cdf(d2)
    put_val = call_val - (S_t1 - K)  # parity
    pick_call = call_val >= put_val
    payoff_call_T = np.maximum(S_T - K, 0.0)
    payoff_put_T = np.maximum(K - S_T, 0.0)
    return np.where(pick_call, payoff_call_T, payoff_put_T)

def np_erf(x):
    # vectorized erf via Abramowitz approximation; numpy has math.erf only scalar in older.
    from scipy.special import erf  # type: ignore
    return erf(x)

# fall back to numpy/math if scipy missing
try:
    from scipy.special import erf as _erf  # noqa
    np_erf = _erf  # type: ignore
except Exception:
    _erf_vec = np.vectorize(math.erf)
    np_erf = _erf_vec  # type: ignore

# ---------------------------------------------------------------------------
# Pricing each contract
# ---------------------------------------------------------------------------
def closed_form_price(c):
    if c["type"] == "spot":
        return S0
    T_years = c["T_steps"] / STEPS_PER_YEAR
    if c["type"] == "call":
        return bs_call(S0, c["K"], T_years, SIGMA)
    if c["type"] == "put":
        return bs_put(S0, c["K"], T_years, SIGMA)
    if c["type"] == "binput":
        return bs_binary_put(S0, c["K"], T_years, SIGMA, payout=c["payout"])
    if c["type"] == "doput":
        # continuous-monitored Reiner-Rubinstein closed form
        return reiner_rubinstein_doput(S0, c["K"], c["B"], T_years, SIGMA)
    if c["type"] == "chooser":
        # standard chooser identity at K=S0, r=0:
        # Chooser = Put(S0, K, T_expiry) + Call(S0, K, T_decide)
        T_dec_y = c["T_decide"] / STEPS_PER_YEAR
        T_exp_y = c["T_steps"] / STEPS_PER_YEAR
        return bs_put(S0, c["K"], T_exp_y, SIGMA) + bs_call(S0, c["K"], T_dec_y, SIGMA)
    raise ValueError(c["type"])

def mc_payoffs(c, paths):
    if c["type"] == "spot":
        return paths[:, -1]  # ending spot; PnL = S_T - S_0
    if c["type"] == "call":
        return payoff_call(paths, c["K"], c["T_steps"])
    if c["type"] == "put":
        return payoff_put(paths, c["K"], c["T_steps"])
    if c["type"] == "binput":
        return payoff_binput(paths, c["K"], c["T_steps"], c["payout"])
    if c["type"] == "doput":
        return payoff_doput(paths, c["K"], c["B"], c["T_steps"])
    if c["type"] == "chooser":
        return payoff_chooser(paths, c["K"], c["T_decide"], c["T_steps"])
    raise ValueError(c["type"])

# ---------------------------------------------------------------------------
# Build everything
# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    dt = 1.0 / STEPS_PER_YEAR

    # large-N MC for high-precision fair values + payoff variances
    N_PATHS = 200_000
    paths = gbm_paths(N_PATHS, N_3W, S0, SIGMA, dt, antithetic=True, seed=20260427)

    # Also estimate the "100-sim mark" distribution by bootstrapping subsamples
    # of size 100 from these paths. This approximates the variance of the
    # mark itself (the score is the mean of 100 paths chosen by the
    # simulator, not the true expectation).
    N_BOOT = 5000

    rng_boot = np.random.default_rng(42)

    rows = []
    payoff_matrix = []  # for portfolio variance: (n_paths, n_contracts) of payoffs
    contract_names = []

    for c in CONTRACTS:
        cf = closed_form_price(c)
        payoffs = mc_payoffs(c, paths)
        mc_mean = float(payoffs.mean())
        mc_se = float(payoffs.std(ddof=1) / math.sqrt(len(payoffs)))
        payoff_var = float(payoffs.var(ddof=1))
        # 100-sim mark: average of 100 random paths
        idx = rng_boot.integers(0, N_PATHS, size=(N_BOOT, 100))
        marks_100 = payoffs[idx].mean(axis=1)
        mark_mean = float(marks_100.mean())
        mark_sd = float(marks_100.std(ddof=1))

        bid = c["bid"]; ask = c["ask"]
        mid = 0.5 * (bid + ask)
        edge_buy = mc_mean - ask    # PnL per contract if we buy at ask, marked to fair
        edge_sell = bid - mc_mean

        # Optimal action: side with higher edge if positive
        if edge_buy > edge_sell and edge_buy > 0:
            side = "BUY"
            edge_per = edge_buy
            qty = c["max"]
        elif edge_sell > 0:
            side = "SELL"
            edge_per = edge_sell
            qty = c["max"]
        else:
            side = "SKIP"
            edge_per = 0.0
            qty = 0

        rows.append({
            "name": c["name"],
            "type": c["type"],
            "K": c.get("K"),
            "B": c.get("B"),
            "T_steps": c.get("T_steps"),
            "bid": bid, "ask": ask, "mid": mid,
            "closed_form": cf,
            "mc_mean": mc_mean, "mc_se": mc_se,
            "payoff_sd": math.sqrt(payoff_var),
            "mark_100_mean": mark_mean,
            "mark_100_sd": mark_sd,
            "edge_buy_at_ask": edge_buy,
            "edge_sell_at_bid": edge_sell,
            "action": side,
            "qty": qty,
            "edge_per_contract": edge_per,
        })
        payoff_matrix.append(payoffs)
        contract_names.append(c["name"])

    payoff_matrix = np.stack(payoff_matrix, axis=1)  # (N_PATHS, n_contracts)
    name_to_idx = {n: i for i, n in enumerate(contract_names)}

    def evaluate(positions, label):
        """positions: dict name -> (sign in {-1,+1}, qty, trade_price)"""
        pnl_vec = np.zeros(N_PATHS)
        exp_pnl = 0.0
        for nm, (sign, qty, px) in positions.items():
            i = name_to_idx[nm]
            payoffs = payoff_matrix[:, i]
            pnl_vec += sign * (payoffs - px) * qty * CONTRACT_SIZE
            exp_pnl += sign * (payoffs.mean() - px) * qty * CONTRACT_SIZE
        idx = rng_boot.integers(0, N_PATHS, size=(N_BOOT, 100))
        sc = pnl_vec[idx].mean(axis=1)
        return {
            "label": label,
            "positions": positions,
            "exp_pnl_path": exp_pnl,
            "sd_path": float(pnl_vec.std(ddof=1)),
            "score_mean": float(sc.mean()),
            "score_sd": float(sc.std(ddof=1)),
            "score_p5": float(np.percentile(sc, 5)),
            "score_p95": float(np.percentile(sc, 95)),
            "p_score_pos": float((sc > 0).mean()),
        }

    # build candidate portfolios
    # Helper: greedy positions = each contract that has positive edge, at cap.
    greedy_pos = {}
    for r in rows:
        if r["action"] == "BUY":
            greedy_pos[r["name"]] = (+1, r["qty"], r["ask"])
        elif r["action"] == "SELL":
            greedy_pos[r["name"]] = (-1, r["qty"], r["bid"])

    # Arb-locked chooser hedge: sell CO + buy 3w-call + buy 2w-put
    # (an exact replication at t=0 with locked $0.40 per contract).
    arb_lock = dict(greedy_pos)
    arb_lock["AC_50_C"] = (+1, 50, 12.05)  # buy 3w call at ask
    arb_lock["AC_50_P_2"] = (+1, 50, 9.75)  # already in greedy (same)

    # Variant: same as arb_lock but DROP the long 2w-call (only put for hedge)
    # — this keeps chooser-arb pure (sell CO + 3w-C + 2w-P) without straddle.
    arb_pure = dict(arb_lock)
    arb_pure.pop("AC_50_C_2", None)

    # Variant: arb_lock + ALSO buy 3w put (to convert chooser arb into the
    # symmetric form) — but 3w put is at fair, no edge. Skipped.

    # Variant: skip KO (largest single-position variance contributor)
    no_ko = dict(greedy_pos); no_ko.pop("AC_45_KO", None)

    # Variant: skip BP (binary-jump risk)
    no_bp = dict(greedy_pos); no_bp.pop("AC_40_BP", None)

    # Variant: skip both KO and BP (cleanest)
    clean = dict(greedy_pos); clean.pop("AC_45_KO", None); clean.pop("AC_40_BP", None)

    # Binary-put put-spread replication: bin(K=40, pay=10) ≈ P(45) - P(35).
    # Sell BP, buy P45, sell P35 to lock most of the directional exposure.
    bp_replication = dict(arb_lock)
    bp_replication["AC_45_P"] = (+1, 50, 9.10)   # buy P45 at ask
    bp_replication["AC_35_P"] = (-1, 50, 4.33)   # sell P35 at bid

    # KO-replication: down-and-out put = vanilla put - down-and-in put.
    # No DI put listed; cannot perfectly replicate. Skip.

    # Half-sized KO (acknowledge the discrete-monitor MC has model risk).
    half_ko = dict(arb_lock); half_ko["AC_45_KO"] = (+1, 250, 0.175)

    portfolios = [
        evaluate(greedy_pos, "GREEDY (each favorable side at cap)"),
        evaluate(arb_lock,   "ARB-LOCKED chooser + greedy others"),
        evaluate(arb_pure,   "ARB-LOCKED chooser, no extra 2w-call"),
        evaluate(bp_replication, "ARB-LOCKED chooser + BP put-spread hedge"),
        evaluate(half_ko,    "ARB-LOCKED chooser + half-size KO"),
        evaluate(no_ko,      "GREEDY without KO"),
        evaluate(no_bp,      "GREEDY without BP"),
        evaluate(clean,      "GREEDY without KO and BP"),
    ]

    # Pick best by Sharpe of score (E/SD) with a positivity prior
    def rank_score(p):
        # maximize E - 0.25 * SD (mean-CVaR-ish; matches IMC manual scoring style)
        return p["score_mean"] - 0.25 * p["score_sd"]

    portfolios_sorted = sorted(portfolios, key=rank_score, reverse=True)
    best = portfolios_sorted[0]
    actions = []
    for nm, (sign, qty, px) in best["positions"].items():
        i = name_to_idx[nm]
        payoffs = payoff_matrix[:, i]
        actions.append({
            "name": nm,
            "side": "BUY" if sign > 0 else "SELL",
            "qty": qty,
            "trade_price": px,
            "fair": float(payoffs.mean()),
            "edge_per_contract": float(sign * (payoffs.mean() - px)),
            "expected_pnl_$": float(sign * (payoffs.mean() - px) * qty * CONTRACT_SIZE),
        })

    portfolio_mean = best["exp_pnl_path"]
    portfolio_sd_per_path = best["sd_path"]
    score_mean = best["score_mean"]
    score_sd = best["score_sd"]
    score_5pct = best["score_p5"]
    score_95pct = best["score_p95"]
    score_realizations = None  # for legacy print path

    elapsed = time.time() - t0

    # ---------------- print + save ----------------
    print(f"=== Round 4 manual: optimal portfolio ===  (compute {elapsed:.2f}s)")
    print(f"S0={S0}  sigma={SIGMA}  T2w={T_2W:.4f}yr ({N_2W} steps)  "
          f"T3w={T_3W:.4f}yr ({N_3W} steps)  N_paths={N_PATHS}")
    print()
    print(f"{'name':12s} {'type':7s} {'cf':>8s} {'mc':>8s} {'se':>6s} "
          f"{'bid':>8s} {'ask':>8s} {'edge_buy':>9s} {'edge_sell':>9s} {'action':>6s} {'qty':>4s} {'$/contract':>10s}")
    for r in rows:
        cf = r["closed_form"]
        mc = r["mc_mean"]
        se = r["mc_se"]
        eb = r["edge_buy_at_ask"]
        es = r["edge_sell_at_bid"]
        print(f"{r['name']:12s} {r['type']:7s} {cf:8.4f} {mc:8.4f} {se:6.4f} "
              f"{r['bid']:8.4f} {r['ask']:8.4f} {eb:9.4f} {es:9.4f} {r['action']:>6s} {r['qty']:4d} "
              f"{r['edge_per_contract']*CONTRACT_SIZE:10.0f}")
    print()
    print("Candidate portfolios (sorted by score_mean - 0.25*score_sd):")
    print(f"  {'label':60s} {'E[score]':>12s} {'SD':>12s} {'p5':>12s} {'p95':>12s} {'P(>0)':>7s}")
    for p in portfolios_sorted:
        print(f"  {p['label']:60s} {p['score_mean']:>12,.0f} {p['score_sd']:>12,.0f} "
              f"{p['score_p5']:>12,.0f} {p['score_p95']:>12,.0f} {p['p_score_pos']:>7.1%}")
    print()
    print(f"BEST = {best['label']}")
    print(f"  E[score]             = {score_mean:>15,.0f}")
    print(f"  SD of score          = {score_sd:>15,.0f}")
    print(f"  5th pctile score     = {score_5pct:>15,.0f}")
    print(f"  95th pctile score    = {score_95pct:>15,.0f}")
    print(f"  P(score > 0)         = {best['p_score_pos']:.3%}")
    print(f"  E[PnL] per path      = {portfolio_mean:>15,.0f}")
    print(f"  SD per single path   = {portfolio_sd_per_path:>15,.0f}")
    print()
    print("Per-contract greedy orders to submit:")
    for a in actions:
        if a["side"] == "SKIP":
            continue
        print(f"  {a['side']:>4s} {a['qty']:>3d}  {a['name']:12s}  "
              f"@ {a['trade_price']:>8.4f}  (fair={a['fair']:>7.4f}, "
              f"edge=${a['expected_pnl_$']:>10,.0f})")

    out = {
        "spec": {
            "S0": S0, "sigma": SIGMA, "r": R,
            "T_2W_steps": N_2W, "T_3W_steps": N_3W,
            "contract_size": CONTRACT_SIZE, "n_paths_mc": N_PATHS,
            "score_paths_per_realization": 100,
        },
        "contracts": rows,
        "actions": actions,
        "portfolio": {
            "expected_score": score_mean,
            "score_sd_100sims": score_sd,
            "p5": score_5pct, "p95": score_95pct,
            "sd_per_path": portfolio_sd_per_path,
            "mean_per_path": portfolio_mean,
            "p_score_positive": best["p_score_pos"],
        },
    }
    with open(os.path.join(OUT_DIR, "optimize_output.json"), "w") as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nSaved {os.path.join(OUT_DIR, 'optimize_output.json')}")

if __name__ == "__main__":
    main()
