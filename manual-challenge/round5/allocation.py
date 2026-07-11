from dataclasses import dataclass
import random
from statistics import mean, median
from typing import Dict, Iterable, List, Tuple


BUDGET = 1_000_000
MAX_GROSS_PERCENT = 100.0


@dataclass(frozen=True)
class ProductSignal:
    product: str
    direction: str
    base_return: float
    confidence: str
    rationale: str


SIGNALS: List[ProductSignal] = [
    ProductSignal("Obsidian cutlery", "Buy", 0.20, "medium", "manufacturing halt implies scarcity; headline also showcases extreme product quality"),
    ProductSignal("Pyroflex cells", "Sell", -0.22, "medium", "abrupt end of tax cut effectively doubles the levy and should slow purchases"),
    ProductSignal("Thermalite core", "Buy", 0.35, "high", "quarterly forecast shows active projects surging from 1.42m to 3.89m"),
    ProductSignal("Lava cake", "Sell", -0.65, "high", "actual lava traces, sales halt, lawsuits, and vendor returns are a direct crash catalyst"),
    ProductSignal("Magma ink", "Buy", 0.16, "medium", "front-page hot-drop queue creates near-term demand for ink reservoir product"),
    ProductSignal("Scoria paste", "Buy", 0.22, "medium", "stockpiling call plus central maintenance role makes it a household/macro proxy"),
    ProductSignal("Ashes of the Phoenix", "Sell", -0.32, "high", "origin scandal shocks public, partially offset by immortal-bird reassurance"),
    ProductSignal("Volcanic incense", "Buy", 0.15, "medium", "already extended rally with accelerated buying around public appearances"),
    ProductSignal("Sulfur reactor", "Buy", 0.33, "high", "index committee confirmation implies forced/index-tracker demand"),
]


SCENARIOS: Dict[str, Dict[str, float]] = {
    "conservative": {
        "Obsidian cutlery": 0.12,
        "Pyroflex cells": -0.12,
        "Thermalite core": 0.25,
        "Lava cake": -0.45,
        "Magma ink": 0.08,
        "Scoria paste": 0.12,
        "Ashes of the Phoenix": -0.22,
        "Volcanic incense": 0.07,
        "Sulfur reactor": 0.23,
    },
    "base": {signal.product: signal.base_return for signal in SIGNALS},
    "crowd_amplified": {
        "Obsidian cutlery": 0.25,
        "Pyroflex cells": -0.25,
        "Thermalite core": 0.42,
        "Lava cake": -0.75,
        "Magma ink": 0.22,
        "Scoria paste": 0.30,
        "Ashes of the Phoenix": -0.40,
        "Volcanic incense": 0.20,
        "Sulfur reactor": 0.40,
    },
    "aggressive": {
        "Obsidian cutlery": 0.32,
        "Pyroflex cells": -0.32,
        "Thermalite core": 0.55,
        "Lava cake": -0.85,
        "Magma ink": 0.28,
        "Scoria paste": 0.38,
        "Ashes of the Phoenix": -0.55,
        "Volcanic incense": 0.28,
        "Sulfur reactor": 0.50,
    },
}


SCENARIO_WEIGHTS = {
    "conservative": 0.25,
    "base": 0.45,
    "crowd_amplified": 0.20,
    "aggressive": 0.10,
}


def optimize_for_returns(returns: Dict[str, float]) -> Dict[str, float]:
    magnitudes = {product: abs(ret) for product, ret in returns.items()}
    unconstrained = {product: 50.0 * mag for product, mag in magnitudes.items()}
    if sum(unconstrained.values()) <= MAX_GROSS_PERCENT:
        abs_alloc = unconstrained
    else:
        low = 0.0
        high = max(unconstrained.values())
        for _ in range(100):
            mid = (low + high) / 2.0
            total = sum(max(0.0, value - mid) for value in unconstrained.values())
            if total > MAX_GROSS_PERCENT:
                low = mid
            else:
                high = mid
        tau = high
        abs_alloc = {product: max(0.0, value - tau) for product, value in unconstrained.items()}
    return {product: abs_alloc[product] if ret >= 0 else -abs_alloc[product] for product, ret in returns.items()}


def evaluate(allocation: Dict[str, float], returns: Dict[str, float]) -> Tuple[float, float, float, float]:
    gross = sum(BUDGET * returns[product] * allocation[product] / 100.0 for product in returns)
    fee = sum(BUDGET * (abs(allocation[product]) / 100.0) ** 2 for product in returns)
    net = gross - fee
    gross_percent = sum(abs(value) for value in allocation.values())
    return gross, fee, net, gross_percent


def weighted_returns() -> Dict[str, float]:
    products = [signal.product for signal in SIGNALS]
    out: Dict[str, float] = {}
    for product in products:
        out[product] = sum(SCENARIO_WEIGHTS[name] * scenario[product] for name, scenario in SCENARIOS.items())
    return out


def round_to_integer_percent(allocation: Dict[str, float]) -> Dict[str, int]:
    rounded = {product: int(round(value)) for product, value in allocation.items()}
    while sum(abs(value) for value in rounded.values()) > 100:
        candidates = sorted(
            rounded,
            key=lambda p: (abs(rounded[p]), abs(allocation[p]) - abs(rounded[p])),
            reverse=True,
        )
        product = candidates[0]
        rounded[product] -= 1 if rounded[product] > 0 else -1
    return rounded


def print_allocation(title: str, allocation: Dict[str, float], returns: Dict[str, float]) -> None:
    gross, fee, net, gross_percent = evaluate(allocation, returns)
    print(f"\n{title}")
    print("-" * len(title))
    print(f"Expected gross PnL: {gross:,.0f}")
    print(f"Expected fee:       {fee:,.0f}")
    print(f"Expected net PnL:   {net:,.0f}")
    print(f"Gross allocation:   {gross_percent:.2f}%")
    for product, pct in sorted(allocation.items(), key=lambda kv: -abs(kv[1])):
        if abs(pct) < 0.005:
            continue
        side = "Buy" if pct > 0 else "Sell"
        print(f"{product:<22} {side:<4} {abs(pct):>6.2f}%  expected_return={returns[product]:>7.2%}")


def main() -> None:
    for name, returns in SCENARIOS.items():
        print_allocation(f"Scenario optimum: {name}", optimize_for_returns(returns), returns)

    final_returns = weighted_returns()
    final_allocation = optimize_for_returns(final_returns)
    rounded = round_to_integer_percent(final_allocation)
    print_allocation("Weighted robust optimum", final_allocation, final_returns)
    print_allocation("Rounded submission", {k: float(v) for k, v in rounded.items()}, final_returns)
    monte_carlo_report({
        "conservative_optimum": round_to_integer_percent(optimize_for_returns(SCENARIOS["conservative"])),
        "base_optimum": round_to_integer_percent(optimize_for_returns(SCENARIOS["base"])),
        "aggressive_optimum": round_to_integer_percent(optimize_for_returns(SCENARIOS["aggressive"])),
        "rounded_submission": rounded,
    })


def sample_returns() -> Dict[str, float]:
    returns: Dict[str, float] = {}
    for signal in SIGNALS:
        values = [scenario[signal.product] for scenario in SCENARIOS.values()]
        scenario_draw = random.choices(
            list(SCENARIOS.keys()),
            weights=[SCENARIO_WEIGHTS[name] for name in SCENARIOS],
            k=1,
        )[0]
        center = SCENARIOS[scenario_draw][signal.product]
        spread = max(0.03, (max(values) - min(values)) / 3.0)
        draw = random.gauss(center, spread)
        if signal.direction == "Buy":
            returns[signal.product] = max(-0.10, draw)
        else:
            returns[signal.product] = min(0.10, draw)
    return returns


def percentile(values: List[float], q: float) -> float:
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, int(round(q * (len(sorted_values) - 1)))))
    return sorted_values[index]


def monte_carlo_report(candidates: Dict[str, Dict[str, int]], runs: int = 20000) -> None:
    print("\nMonte Carlo robustness check")
    print("----------------------------")
    results: Dict[str, List[float]] = {name: [] for name in candidates}
    wins: Dict[str, int] = {name: 0 for name in candidates}
    for _ in range(runs):
        returns = sample_returns()
        values = {
            name: evaluate({k: float(v) for k, v in allocation.items()}, returns)[2]
            for name, allocation in candidates.items()
        }
        best = max(values, key=values.get)
        wins[best] += 1
        for name, value in values.items():
            results[name].append(value)
    for name, values in results.items():
        print(
            f"{name:<22} "
            f"mean={mean(values):>10,.0f} "
            f"median={median(values):>10,.0f} "
            f"p05={percentile(values, 0.05):>10,.0f} "
            f"p95={percentile(values, 0.95):>10,.0f} "
            f"win_rate={wins[name] / runs:>6.1%}"
        )


if __name__ == "__main__":
    main()
