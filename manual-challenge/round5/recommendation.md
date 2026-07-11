# Round 5 Manual Trading Recommendation

## Final submission

| Product | Side | Percentage |
|---|---:|---:|
| Lava cake | Sell | 29% |
| Thermalite core | Buy | 14% |
| Ashes of the Phoenix | Sell | 13% |
| Sulfur reactor | Buy | 13% |
| Scoria paste | Buy | 8% |
| Obsidian cutlery | Buy | 7% |
| Pyroflex cells | Sell | 7% |
| Magma ink | Buy | 5% |
| Volcanic incense | Buy | 4% |
| **Total gross allocation** |  | **100%** |

## Rationale

- **Lava cake: strongest short** — actual lava traces, immediate sales halt, lawsuits, and vendor returns.
- **Thermalite core: strongest long** — forecasted active projects rise from 1.42m to 3.89m with sustained usage.
- **Sulfur reactor: strong long** — index inclusion implies forced buying from index-tracking funds.
- **Ashes of the Phoenix: strong short** — public origin scandal; the company's reassurance is weak and bizarre.
- **Scoria paste: medium long** — stockpiling recommendation plus broad maintenance/infrastructure use.
- **Pyroflex cells: medium short** — tax cut ending effectively doubles the levy and slows consumer upgrades.
- **Obsidian cutlery: medium long** — production halt implies scarcity, but contamination/manufacturing spillover adds uncertainty.
- **Magma ink: smaller long** — front-page hot-drop demand, but it is tied to a limited-edition pen release rather than broad recurring demand.
- **Volcanic incense: smaller long** — already rallying with concentrated buying, but celebrity/influencer-driven and more likely to be crowded/fragile.

## Method

The allocation follows the same framework used by top Prosperity manual teams for news-trading rounds:

1. Convert article evidence into expected percentage returns.
2. Include conservative, base, crowd-amplified, and aggressive scenarios.
3. Maximize expected PnL net of quadratic fees: `budget * (percentage / 100)^2` per product.
4. Stress test candidate allocations across Monte Carlo perturbations of the return assumptions.
5. Round to integer percentages for manual entry.

The script backing this recommendation is `manual-challenge/round5/allocation.py`.
