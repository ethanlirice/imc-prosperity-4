# Round 1 — Trading Groundwork

## Setting
You have reached Intara. Goal: earn net profit of 200,000 XIRECs or more before the beginning of the third trading day. Trading days last 72 hours.

## Algorithmic Challenge — "First Intarian Goods"

Products:
- ASH_COATED_OSMIUM (position limit: 80) — "rumored to be a bit more volatile, although one may speculate that its apparent unpredictability may follow a hidden pattern"
- INTARIAN_PEPPER_ROOT (position limit: 80) — "value is quite steady... a hardy, slow-growing root" (analogue of EMERALDS in tutorial)

## Manual Challenge — "An Intarian Welcome"

Two sealed-bid auctions, single limit order each (price, quantity). You submit last; no other orders arrive after.

Clearing rule:
1. Exchange selects single clearing price that maximizes total traded volume.
2. Ties broken by choosing the higher price.
3. All bids ≥ clearing price and asks ≤ clearing price execute at the clearing price.
4. Allocation: price priority, then time priority. We are last in line at any price level we join.

Guaranteed buyback after auction:
- DRYLAND_FLAX: 30 per unit (no fees)
- EMBER_MUSHROOM: 20 per unit (fee: 0.10 per unit traded)

These products do NOT trade in continuous trading — only auction + buyback.

Submission: enter orders in Manual Challenge Overview, can resubmit until round ends, last submitted orders execute.
