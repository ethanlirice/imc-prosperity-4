import csv
import os
import re
import subprocess


STRATEGY = "strategies/round5/v8-reanchor-configurable.py"
OUT_SUMMARY = "analysis/round5-hidden-paths/reanchor_integration_summary.csv"
OUT_PRODUCT_DAY = "analysis/round5-hidden-paths/reanchor_integration_product_day.csv"
BASELINE = 1234316

PRODUCTS = [
    "ROBOT_DISHES",
    "PEBBLES_S",
    "UV_VISOR_ORANGE",
    "SLEEP_POD_NYLON",
    "OXYGEN_SHAKE_MINT",
    "SNACKPACK_STRAWBERRY",
    "PANEL_4X4",
    "SNACKPACK_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "PANEL_1X2",
]

CASES = [("single__" + product, product) for product in PRODUCTS]
CASES.extend(
    [
        ("top2", "ROBOT_DISHES,PEBBLES_S"),
        ("top3", "ROBOT_DISHES,PEBBLES_S,UV_VISOR_ORANGE"),
        ("top4", "ROBOT_DISHES,PEBBLES_S,UV_VISOR_ORANGE,SLEEP_POD_NYLON"),
        ("all10", ",".join(PRODUCTS)),
    ]
)


def parse_output(text):
    current_day = None
    day_totals = {}
    product_day = []
    product_re = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
    day_re = re.compile(r"round 5 day (\d+)")
    summary_re = re.compile(r"Round 5 day (\d+):\s+(-?[\d,]+)")
    total_re = re.compile(r"Total profit:\s+(-?[\d,]+)")
    total = None
    in_summary = False
    for line in text.splitlines():
        if line.startswith("Profit summary"):
            in_summary = True
            continue
        m = day_re.search(line)
        if m and not in_summary:
            current_day = int(m.group(1))
            continue
        m = product_re.match(line.strip())
        if m and current_day is not None and not in_summary:
            product_day.append(
                {
                    "day": current_day,
                    "product": m.group(1),
                    "pnl": int(m.group(2).replace(",", "")),
                }
            )
            continue
        m = summary_re.search(line)
        if m:
            day_totals[int(m.group(1))] = int(m.group(2).replace(",", ""))
            continue
        m = total_re.search(line)
        if m:
            total = int(m.group(1).replace(",", ""))
    return total, day_totals, product_day


def run_case(name, products):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["RA_PRODUCTS"] = products
    proc = subprocess.run(
        [
            "prosperity4btx",
            STRATEGY,
            "5",
            "--merge-pnl",
            "--no-progress",
            "--no-out",
        ],
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    total, day_totals, product_day = parse_output(proc.stdout)
    if total is None:
        raise RuntimeError("Could not parse total for " + name)
    return {
        "case": name,
        "products": products,
        "total": total,
        "delta": total - BASELINE,
        "day2": day_totals.get(2, 0),
        "day3": day_totals.get(3, 0),
        "day4": day_totals.get(4, 0),
    }, product_day


def main():
    rows = []
    pd_rows = []
    for name, products in CASES:
        print("running", name, products, flush=True)
        row, product_day = run_case(name, products)
        rows.append(row)
        for item in product_day:
            item["case"] = name
            item["products"] = products
            pd_rows.append(item)
        with open(OUT_SUMMARY, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["case", "products", "total", "delta", "day2", "day3", "day4"])
            writer.writeheader()
            writer.writerows(rows)
        with open(OUT_PRODUCT_DAY, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["case", "products", "day", "product", "pnl"])
            writer.writeheader()
            writer.writerows(pd_rows)
        print(row, flush=True)


if __name__ == "__main__":
    main()
