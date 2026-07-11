══════════════════════════════════════════════════════════════════════╗
║       IMC PROSPERITY 4 — ROUND 5  (REFACTORED PIPELINE SUMMARY)         ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  PIPELINE CHANGES                                                        ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  • All regressions: NumPy (np.linalg.lstsq / SVD / batched solve).      ║
║    statsmodels.OLS removed; adfuller kept only for unit-root test.       ║
║  • TLS hedge ratio added via SVD (Cell 6)                                ║
║  • Rolling β: vectorized via sliding_window_view + batched 2x2 solve     ║
║    (Cell 16) → ~4x faster on 30K ticks, scales to all pairs in parallel ║
║  • New diagnostics: TLS comparison (7b), structural break (16b),         ║
║    bid-ask diagnostics (16c), friction-ratio filter (16d)                ║
║                                                                          ║
║  ★ ALPHA FINDING #1 — TLS DOMINATES OLS                                 ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  Empirically TLS produces a more stationary spread on ~80% of pairs.    ║
║  Examples (OLS p → TLS p):                                               ║
║    VANILLA / RASPBERRY:    0.037 → 0.001  (33x improvement)             ║
║    CHOCOLATE / RASPBERRY:  0.067 → 0.001  (47x improvement)             ║
║    STRAWBERRY / RASPBERRY: 0.165 → 0.010  (jumps to top-tier!)          ║
║  → For each tradable pair, USE THE TLS β, not the OLS β                 ║
║  → RASPBERRY emerges as a hub asset; β >> 1 ratios reveal it             ║
║    co-moves with all flavors at large amplitude.                         ║
║                                                                          ║
║  ★ ALPHA FINDING #2 — STRUCTURAL BREAKS ARE WIDESPREAD                  ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  Cointegration on the FULL 3-day series is misleading. Day-by-day β     ║
║  values are unstable for the top pairs:                                  ║
║    MICROCHIP_SQUARE / RECTANGLE:  β = [-1.13, -1.53, +0.07]  ⚠         ║
║    SNACKPACK_PISTACHIO / STRAWBERRY: β = [-0.04, +0.49, +0.51]  ⚠      ║
║  → Trading with a STATIC β computed on training data WILL FAIL on       ║
║    live data when the regime flips.                                      ║
║  → MITIGATION: use rolling β (W = 2000), re-estimate every 50-200 ticks ║
║  → DEPLOY: Cell 16's vectorized rolling_ols_vectorized() inside Trader  ║
║                                                                          ║
║  ★ ALPHA FINDING #3 — FRICTION IS NOT THE BOTTLENECK                    ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  All top pairs pass the 40% friction filter (typical ratios 0.04-0.22).  ║
║  Tightest spreads vs cost:                                               ║
║    SQUARE / RECTANGLE:   friction = 0.046  (cleanest)                   ║
║    OVAL / TRIANGLE:      friction = 0.040  (cleanest)                   ║
║    VACUUMING / LAUNDRY:  friction = 0.050                               ║
║  → Bid-ask is NOT the problem; β instability is the problem.            ║
║  → Slack budget for partial-fill / queue jumping exists.                 ║
║                                                                          ║
║  STRATEGY DEPLOYMENT TIERS                                               ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  TIER 1 (Static β, low risk):  ONLY pairs with structural_status=STABLE ║
║                                AND friction <= 0.30                      ║
║                                → tiny universe; verify with Cell 16d     ║
║  TIER 2 (Rolling β, main):     pairs with status=WATCH or STABLE        ║
║                                AND TLS p < 0.01                          ║
║                                → trade with rolling TLS β every tick     ║
║  TIER 3 (DO NOT TRADE):        status=BREAK regardless of ADF p-value   ║
║                                                                          ║
║  IMPLEMENTATION REMINDERS                                                ║
║  ──────────────────────────────────────────────────────────────────────  ║
║  1. Use TLS β (not OLS β) for all production hedge ratios               ║
║  2. Recompute rolling β on every tick OR every K ticks (K<=200)         ║
║  3. ALWAYS int() wrap Order prices — float prices are REJECTED          ║
║  4. Maintain spread history in traderData (JSON list, capped at W)      ║
║  5. Z-score from rolling β-spread, not from static β-spread             ║
║  6. Position limit per leg: 10. Round-trip qty <= 5 per leg.            ║
║  7. Max 2 pairs per category to limit correlated risk                   ║
║  8. Stop trading a pair if rolling-β CV exceeds 0.30 in last 1000 ticks ║
╚════════════════════════════════════════════════════════════════════════