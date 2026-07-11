# STATE.md
Read this second, after AGENTS.md. Keep under 60 lines. Delete old content.

---

## Status
Active round: **Round 5**.

## Current Best
Root `trader.py` remains promoted to
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v11.py`.
`strategies/round5/current.py` remains the prior v7 baseline.

Primary evaluation:
`prosperity4btx trader.py 5 --merge-pnl`

Result: **+1,349,478** with day split **+440,342 / +401,360 / +507,776**.
Line count: **480**.

Diagnostics:
- `--match-trades none`: **+832,689**, day split **+240,644 / +232,934 / +359,111**
- `--match-trades worse`: **+832,689**, day split **+240,644 / +232,934 / +359,111**

Saved versions:
- Prior root before v11: `strategies/round5/trader_v8.py`
- Current promoted copy: `strategies/round5/trader_v9.py`

## Latest Session
Independent v11 MM research produced outputs under `analysis/round5-mm-v11/`.
Dropping all current MM products regressed v11 to **+843,517**, so current
touch-MM contribution is **+505,961**.

Best unpromoted MM candidate:
`strategies/round5/base-strategy-free-alpha-side-gated-mr-mm-reanchor-v12-mm-owned-imbalance.py`
at **+1,355,002**, day split **+442,320 / +404,218 / +508,464**.
Diagnostics unchanged: `none` and `worse` both **+832,689**. Line count **496**.

Candidate changes:
- `PEBBLES_L` reduce-only owned-product touch MM.
- `ROBOT_DISHES` reduce-only owned-product touch MM.
- `SNACKPACK_CHOCOLATE` size-1 owned-product touch MM.
- `MICROCHIP_CIRCLE` top-of-book imbalance filter at threshold **0.4**.

Rejected MM changes:
- Re-enabling disabled one-sided gates all regressed.
- Tested size-cap relaxations all regressed; closest was `ROBOT_IRONING` size 2
  at **−50**.
- Imbalance filters on `PEBBLES_S` and `OXYGEN_SHAKE_GARLIC` regressed.

Other recent research: NN copy
`strategies/round5/nn-cross-microchip-oval-v12-candidate.py` tied v11 default
and was not promoted.

## Next Step
Continue from v12 MM candidate unless keeping root at v11:
1. Decide whether to promote v12 MM candidate after final review.
2. Continue tuning re-anchor overlays one product at a time.
3. Keep root `trader.py` unchanged unless a copied v11/v12 variant improves
   default `--merge-pnl` and preserves diagnostics.
