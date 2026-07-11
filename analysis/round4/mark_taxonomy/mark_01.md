# Mark 01 Counterparty Taxonomy

Data: `data/ROUND4` days 1-3. Script: `notebooks/round4/mark_taxonomy/mark_01_analysis.py`.

Signed markout convention: Mark 01 buy = `future_mid - trade_price`; Mark 01 sell = `trade_price - future_mid`. Future mid is first price row with `timestamp >= trade_timestamp + horizon`. `signed_mid_change` removes the instantaneous half-spread component by using current mid instead of trade price.

## Headline

Mark 01 looks like a passive market-maker / liquidity provider, not an informed liquidity taker.

- 1,843 Mark 01 trade rows.
- Products: `VELVETFRUIT_EXTRACT`, `VEV_5200`, `VEV_5300`, `VEV_5400`, `VEV_5500`, `VEV_6000`, `VEV_6500`.
- No Mark 01 trades in `HYDROGEL_PACK`, `VEV_4000`, `VEV_4500`, `VEV_5000`, or `VEV_5100`.
- VFE is balanced two-sided quoting against Mark 55: 260 buys at bid, 244 sells at ask.
- Options are one-sided passive bids against Mark 22: all Mark 01 option trades are buys at the best bid.
- Historical trade-price markouts are positive, but option forward mid movement is flat to slightly adverse. The option edge is almost entirely bid/ask capture.

## Product And Side Summary

| product | side | trades | qty | avg qty | book relation | spread pctile | signed mid edge | t+200 trade MO | t+200 mid move |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| VELVETFRUIT_EXTRACT | buy | 260 | 1417 | 5.45 | at bid | 0.847 | +2.602 | +2.804 | +0.202 |
| VELVETFRUIT_EXTRACT | sell | 244 | 1375 | 5.64 | at ask | 0.876 | +2.686 | +2.830 | +0.143 |
| VEV_5200 | buy | 11 | 34 | 3.09 | at bid | 0.462 | +1.000 | +1.091 | +0.091 |
| VEV_5300 | buy | 132 | 439 | 3.33 | at bid | 0.803 | +0.909 | +0.742 | -0.167 |
| VEV_5400 | buy | 263 | 911 | 3.46 | at bid | 0.769 | +0.595 | +0.568 | -0.027 |
| VEV_5500 | buy | 299 | 1042 | 3.48 | at bid | 0.903 | +0.527 | +0.513 | -0.013 |
| VEV_6000 | buy | 317 | 1105 | 3.49 | at bid | 1.000 | +0.500 | +0.500 | +0.000 |
| VEV_6500 | buy | 317 | 1105 | 3.49 | at bid | 1.000 | +0.500 | +0.500 | +0.000 |

Market share of all trades is high where Mark 01 is active: VFE 36.5%, VEV_5300 80.5%, VEV_5400 95.3%, VEV_5500 97.7%, VEV_6000/6500 100.0%.

## Day Markouts

Mean signed trade-price markout by product, side, and day:

| day | product | side | n | t+10 | t+50 | t+200 | t+500 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | VELVETFRUIT_EXTRACT | buy | 76 | +3.086 | +3.086 | +3.092 | +3.243 |
| 1 | VELVETFRUIT_EXTRACT | sell | 81 | +2.963 | +2.963 | +3.037 | +2.796 |
| 1 | VEV_5300 | buy | 32 | +0.828 | +0.828 | +0.766 | +0.719 |
| 1 | VEV_5400 | buy | 76 | +0.572 | +0.572 | +0.586 | +0.625 |
| 1 | VEV_5500 | buy | 89 | +0.511 | +0.511 | +0.534 | +0.517 |
| 1 | VEV_6000 | buy | 98 | +0.500 | +0.500 | +0.500 | +0.500 |
| 1 | VEV_6500 | buy | 98 | +0.500 | +0.500 | +0.500 | +0.500 |
| 2 | VELVETFRUIT_EXTRACT | buy | 91 | +2.610 | +2.610 | +2.478 | +2.505 |
| 2 | VELVETFRUIT_EXTRACT | sell | 92 | +2.902 | +2.902 | +2.908 | +2.745 |
| 2 | VEV_5300 | buy | 31 | +0.839 | +0.839 | +0.726 | +0.935 |
| 2 | VEV_5400 | buy | 78 | +0.596 | +0.596 | +0.583 | +0.603 |
| 2 | VEV_5500 | buy | 91 | +0.522 | +0.522 | +0.495 | +0.505 |
| 2 | VEV_6000 | buy | 95 | +0.500 | +0.500 | +0.500 | +0.500 |
| 2 | VEV_6500 | buy | 95 | +0.500 | +0.500 | +0.500 | +0.500 |
| 3 | VELVETFRUIT_EXTRACT | buy | 93 | +2.849 | +2.849 | +2.887 | +2.984 |
| 3 | VELVETFRUIT_EXTRACT | sell | 71 | +2.817 | +2.817 | +2.493 | +2.493 |
| 3 | VEV_5200 | buy | 11 | +1.000 | +1.000 | +1.091 | +0.818 |
| 3 | VEV_5300 | buy | 69 | +0.754 | +0.754 | +0.739 | +0.703 |
| 3 | VEV_5400 | buy | 109 | +0.537 | +0.537 | +0.546 | +0.537 |
| 3 | VEV_5500 | buy | 119 | +0.504 | +0.504 | +0.513 | +0.500 |
| 3 | VEV_6000 | buy | 124 | +0.500 | +0.500 | +0.500 | +0.500 |
| 3 | VEV_6500 | buy | 124 | +0.500 | +0.500 | +0.500 | +0.500 |

Quantity-weighted t+200 trade markouts are nearly identical: VFE buy +2.783, VFE sell +2.837, VEV_5200 +1.206, VEV_5300 +0.747, VEV_5400 +0.575, VEV_5500 +0.509, VEV_6000 +0.500, VEV_6500 +0.500.

The quantity-weighted t+200 mid movement is small: VFE buy +0.193, VFE sell +0.164, VEV_5200 +0.206, VEV_5300 -0.162, VEV_5400 -0.023, VEV_5500 -0.017, VEV_6000/6500 0.000.

## Counterparties And Interactions

Direct counterparties are deterministic by sleeve:

| counterparty | products | Mark 01 side | trades | qty | t+200 trade MO |
|---|---|---:|---:|---:|---:|
| Mark 55 | VELVETFRUIT_EXTRACT | buy | 260 | 1417 | +2.804 |
| Mark 55 | VELVETFRUIT_EXTRACT | sell | 244 | 1375 | +2.830 |
| Mark 22 | VEV_5200/5300/5400/5500/6000/6500 | buy | 1339 | 4636 | positive, mostly half-spread |

At Mark 01 timestamps, other non-Mark-01 trades occur 145 times. Other Marks seen at the same timestamp: Mark 14 total 128, Mark 22 total 100, Mark 38 total 48, Mark 55 total 8, Mark 67 total 4, Mark 49 total 2. This looks like shared event timing rather than Mark 01 reacting to a specific other Mark, because Mark 01's direct counterparty remains Mark 55 on VFE and Mark 22 on options.

## Timing, Repeats, And Bursts

- No duplicate same product/side timestamps within a day: every product-side-day row has `duplicate_timestamp_rows = 0`.
- Mark 01 has 817 unique day/timestamp values for 1,843 event rows, so multi-product option baskets are common.
- 317 timestamps have 2+ Mark 01 rows; those account for 1,343 of 1,843 rows.
- 114 timestamps have 5+ rows; 8 timestamps have 6 rows. These are mostly simultaneous option-bid fills across `VEV_5300` through `VEV_6500`, with `VEV_5200` included on some day 3 bursts.
- Exact product/side/timestamp recurrence across days is weak: 22 keys appear on exactly 2 days, 0 keys appear on all 3 days.
- Median gaps are not fixed-period: VFE buy day medians 5,650-7,500; VFE sell 6,300-9,250; VEV_5400 5,600-10,700; VEV_5500 5,200-10,600; VEV_6000/6500 5,100-8,850. Common small gaps of 100-500 exist, but no stable clock signal repeats across all days.

## Spread And Depth Regimes

Mark 01 generally trades when spreads are wide relative to that product/day:

- VFE buys at average spread 5.20, spread percentile 0.847, touch depth 32.6.
- VFE sells at average spread 5.37, spread percentile 0.876, touch depth 36.8.
- VEV_5300 buys at average spread 1.82, spread percentile 0.803.
- VEV_5400 buys at average spread 1.19, spread percentile 0.769.
- VEV_5500 buys at average spread 1.05, spread percentile 0.903.
- VEV_6000/6500 always show spread 1.0 with Mark 01 buying at 0 against a 0/1 market.

This is consistent with resting at the bid/ask in favorable spread regimes, not crossing the book.

## Interpretation

Mark 01 is liquidity-providing:

- VFE: buys at bid and sells at ask against Mark 55 with balanced counts. Both sides have positive trade-price markouts because Mark 01 captures roughly half-spread plus tiny favorable mean reversion.
- Options: buys at bid from Mark 22. Positive trade-price markout is mostly mechanical half-spread; the forward mid after Mark 01 buys is flat or adverse for VEV_5300/5400/5500.
- No evidence Mark 01 is informed. No product has large positive signed mid movement after Mark 01 trades.
- No evidence Mark 01 is toxic to fade from visible trade ID alone. The edge is at Mark 01's passive fill price, not at a next-tick crossing price.

## v314159 Implications

No immediate Mark 01 overlay should be added.

- Do not copy Mark 01 after seeing the print: Mark 01's edge is the passive trade price, and options have near-zero/negative post-trade mid movement.
- Do not suppress VFE quoting because of Mark 01. Mark 01's VFE flow supports the existing passive VFE sleeve: wide-spread, two-sided, positive trade-price markouts on both sides.
- Do not add `VEV_5400` to the Mark 22 vulnerable mask based on Mark 01 alone. Mark 01 buys many `VEV_5400` prints from Mark 22, but t+200 signed mid movement is -0.027 unweighted and -0.023 quantity-weighted. The positive +0.568 trade markout is spread capture.
- Do not widen because Mark 01 appears adverse. It is not adverse in mid-move terms; it is a passive competitor.
- Do not tighten solely to compete with Mark 01. The observed fills are at the best bid/ask in wide-spread regimes, not inside-spread urgency.
- Ignore Mark 01 as a direct ID signal for v314159 unless future simulation tests a very narrow passive-only option bid filter. Data here does not justify changing the current baseline.

## Files Created

- `notebooks/round4/mark_taxonomy/mark_01_analysis.py`
- `notebooks/round4/mark_taxonomy/mark_01_events.csv`
- `notebooks/round4/mark_taxonomy/mark_01_product_side_summary.csv`
- `notebooks/round4/mark_taxonomy/mark_01_product_side_day_markouts.csv`
- `notebooks/round4/mark_taxonomy/mark_01_quantity_weighted_markouts.csv`
- `notebooks/round4/mark_taxonomy/mark_01_counterparties.csv`
- `notebooks/round4/mark_taxonomy/mark_01_price_relation.csv`
- `notebooks/round4/mark_taxonomy/mark_01_timing.csv`
- `notebooks/round4/mark_taxonomy/mark_01_common_gaps.csv`
- `notebooks/round4/mark_taxonomy/mark_01_repeat_timestamps.csv`
- `notebooks/round4/mark_taxonomy/mark_01_timestamp_bursts.csv`
- `notebooks/round4/mark_taxonomy/mark_01_same_timestamp_other_trades.csv`
- `notebooks/round4/mark_taxonomy/mark_01_same_timestamp_other_marks.csv`
- `notebooks/round4/mark_taxonomy/mark_01_size_distribution.csv`
- `notebooks/round4/mark_taxonomy/mark_01_market_share.csv`
