# Round 4 Manual — "Vanilla Just Isn't Exotic Enough"

## Spec (from `wiki/round4manual.md`)

- Underlying `AETHER_CRYSTAL`. S₀ = 50. σ = 2.51 (251% ann). r = q = 0.
- Discrete GBM, 4 steps/day, 252 trading days/yr. Δt = 1/1008.
- Two horizons: 2w (= 10 trading days = 40 steps), 3w (= 15 days = 60 steps).
- Score = mean PnL across **100** simulated paths. Hold-to-expiry, no inter-day rebalance.
- Contract size 3000 = flat PnL multiplier on per-contract PnL.

## Pricing summary (closed-form vs MC, N=200k antithetic, seed 20260427)

| Contract | Type | Fair (CF) | Fair (MC) | Listed mid | Side | Edge / contract |
|---|---|---:|---:|---:|---|---:|
| AC | spot | 50.000 | 49.99 | 50.000 | **SKIP** | 0 |
| AC_50_P | 3w put K=50 | 12.027 | 12.03 | 12.025 | skip | ~0 |
| AC_45_P | 3w put K=45 | 9.089  | 9.09  | 9.075  | skip | ~0 |
| AC_40_P | 3w put K=40 | 6.510  | 6.51  | 6.525  | skip | ~0 |
| AC_35_P | 3w put K=35 | 4.336  | 4.34  | 4.34   | skip | ~0 |
| AC_50_C | 3w call K=50 | 12.027 | 12.02 | 12.025 | (used as hedge) | -0.023 |
| AC_60_C | 3w call K=60 | 8.792  | 8.78  | 8.825 | **SELL @ 8.80** | +0.018 |
| AC_50_P_2 | 2w put K=50 | 9.871  | 9.88  | 9.725 | **BUY @ 9.75** | +0.129 |
| AC_50_C_2 | 2w call K=50 | 9.871  | 9.88  | 9.725 | **BUY @ 9.75** | +0.132 |
| AC_50_CO | chooser K=50 (decide t1=2w, exp=3w) | 21.898 | 21.89 | 22.25 | **SELL @ 22.20** | +0.314 |
| AC_40_BP | binary put K=40, payout 10 | 4.768 | 4.77 | 5.05 | **SELL @ 5.00** | +0.232 |
| AC_45_KO | down-and-out put K=45, B=35 (discrete) | 0.123 (cont) / 0.208 (discrete) | 0.208 | 0.1625 | **BUY @ 0.175** | +0.033 |

Note: KO continuous-monitor RR = 0.123, but the spec mandates discrete monitoring at the 4-step grid. Discrete-monitor MC fair = 0.208 — the listed price (0.15/0.175) is between, so using continuous would mis-sign or undersize the trade.

## Key identities used

1. **Chooser at K = S₀, r = 0:** "ITM at t1" rule = "max-value" rule by put-call parity (C − P = S − K). Standard chooser identity:
   - Chooser(0) = Put(K, T) + Call(K, t₁) = 12.027 + 9.871 = **21.898**
   - Listed bid 22.20 ⇒ rich vs replication by 0.302.
   - **Replication-arb:** sell CO + buy 3w-call + buy 2w-put = **$0.40 per contract risk-free** = $60,000 across 50 contracts at full size. Pathwise identity, not just expected.

2. **Binary put with put-spread approximation:** bin(K=40, pay=10) ≈ P(45) − P(35).
   - P45 − P35 fair = 9.089 − 4.336 = 4.753, vs binary fair 4.768 (within MC noise).
   - Selling BP and buying spread (long P45, short P35) doesn't lock a clean arb (digital-vs-spread residual at edges), but partially hedges the directional shock at the K=40 boundary. MC shows it tightens portfolio SD without much expected loss.

3. **Knock-out put has no clean vanilla replication** with the listed instruments (would need a down-and-in put). KO is left unhedged but at full size because edge/SD per contract is small and discrete-monitor fair is firm.

## Portfolio comparison (E[score] vs SD across 100-sim marks; 5000 bootstrap reps)

| Portfolio | E[score] | SD | P5 | P95 | P(>0) |
|---|---:|---:|---:|---:|---:|
| **ARB-LOCKED chooser + BP put-spread hedge** | **169,506** | **329,434** | **-353,765** | **707,437** | **69.8%** |
| ARB-LOCKED chooser + greedy others | 169,271 | 350,761 | -422,213 | 739,088 | 69.7% |
| ARB-LOCKED + half-size KO | 139,119 | 318,950 | -397,323 | 663,820 | 67.4% |
| ARB-LOCKED, no extra 2w-call | 154,703 | 408,458 | -544,946 | 799,955 | 67.0% |
| GREEDY (each favorable side at cap) | 180,451 | 590,417 | -840,028 | 1,077,804 | 64.1% |
| GREEDY without KO | 128,986 | 550,484 | -820,022 | 953,950 | 61.2% |
| GREEDY without BP | 132,659 | 595,878 | -922,873 | 1,038,174 | 61.7% |
| GREEDY without KO and BP | 84,470 | 568,037 | -905,840 | 940,474 | 58.8% |

The **arb-locked + BP-hedge** portfolio has the highest mean−¼·SD score and the highest P(score > 0) at 69.8%. Naked greedy gives ~6% more expected but 80% more SD; risk-adjusted, it loses.

## Final orders (submit to Manual Challenge Overview)

| # | Side | Qty | Contract | Price | Expected $ | Role |
|---|------|-----|----------|------:|-----------:|------|
| 1 | SELL | 50  | AC_50_CO  | 22.20 | +$47,164 | Sell rich chooser |
| 2 | BUY  | 50  | AC_50_C   | 12.05 | -$4,897  | Hedge leg of chooser arb |
| 3 | BUY  | 50  | AC_50_P_2 | 9.75  | +$19,309 | Hedge leg of chooser arb (also +edge alone) |
| 4 | BUY  | 50  | AC_50_C_2 | 9.75  | +$19,789 | Cheap 2w call (separate edge) |
| 5 | SELL | 50  | AC_40_BP  | 5.00  | +$34,800 | Sell rich binary put |
| 6 | BUY  | 50  | AC_45_P   | 9.10  | -$1,105  | Long leg of BP put-spread hedge |
| 7 | SELL | 50  | AC_35_P   | 4.33  | -$1,551  | Short leg of BP put-spread hedge |
| 8 | BUY  | 500 | AC_45_KO  | 0.175 | +$49,539 | Buy cheap discrete-monitor KO put |
| 9 | SELL | 50  | AC_60_C   | 8.80  | +$2,733  | Sell marginal-rich OTM call |

**Total expected score ≈ +$169,506** with SD ≈ $329k. P(score > 0) ≈ 70%.

Skip AC (spot — zero E[PnL], pure variance) and AC_50_P / AC_40_P / AC_50_C standalone (all near fair within MC noise).

## Why this is the strongest practical edge

1. **The chooser arb is exact at t=0**, not just expected: sell CO + buy {3w-call, 2w-put} replicates the chooser perfectly (put-call parity at K = S₀, r = 0). The locked spread between listed 22.20 and replication 21.80 = $0.40 × 50 × 3000 = $60,000 risk-free. Most participants will sell the chooser naked and accept higher SD.
2. **Discrete-monitor KO insight:** continuous-monitor RR (≈0.12) is the textbook number; the simulator monitors discretely at the 4-step grid (explicit in spec). Discrete fair (≈0.21) is **70% higher**. Anyone using closed-form RR will under-buy or skip — we buy the entire 500-cap.
3. **Binary put put-spread hedge:** lays off the discontinuous payoff at K=40 against the listed P45/P35 spread. Cuts portfolio SD by 6% with negligible expected cost.
4. **Symmetric 2w-straddle layer:** long P_2 + long C_2 (each cheap by 0.12 vs BS) earns +$38k jointly; the half that overlaps with the chooser hedge is "free" alpha.
5. **No naive trade on at-fair vanillas:** the 50/45/40/35 puts and 50-call are all within 1¢ of MC fair — no edge, no trade except as hedge legs.

## Files

- `optimize.py` — runs all pricing + portfolio comparison; outputs `optimize_output.json`.
- `optimize_output.json` — machine-readable result for downstream submission scripts.
