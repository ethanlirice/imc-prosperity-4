import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
STRATEGY = "strategies/round5/base-strategy-free-alpha-configurable.py"
BASE_TOTAL = 868478

MM_PRODUCTS = [
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "MICROCHIP_TRIANGLE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PANEL_2X4",
    "PEBBLES_S",
    "PEBBLES_XL",
    "ROBOT_DISHES",
    "ROBOT_IRONING",
    "ROBOT_LAUNDRY",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_SUEDE",
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_STRAWBERRY",
    "TRANSLATOR_ASTRO_BLACK",
    "TRANSLATOR_ECLIPSE_CHARCOAL",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
]

FREE_ALPHA_PRODUCTS = [
    "GALAXY_SOUNDS_DARK_MATTER",
    "GALAXY_SOUNDS_SOLAR_FLAMES",
    "GALAXY_SOUNDS_SOLAR_WINDS",
    "PANEL_2X2",
    "PEBBLES_L",
    "SLEEP_POD_COTTON",
    "SLEEP_POD_LAMB_WOOL",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_VANILLA",
    "TRANSLATOR_GRAPHITE_MIST",
    "UV_VISOR_MAGENTA",
    "UV_VISOR_YELLOW",
]

ADD_CANDIDATES = [
    # Higher-variance candidates from the broad free-alpha sweep. These are not
    # expected to all pass; this is an owner-map check.
    ("MICROCHIP_RECTANGLE", "80"),
    ("OXYGEN_SHAKE_MORNING_BREATH", "200"),
    ("TRANSLATOR_VOID_BLUE", "200"),
    ("SNACKPACK_CHOCOLATE", "80"),
    ("SLEEP_POD_POLYESTER", "200"),
    ("ROBOT_MOPPING", "200"),
    ("ROBOT_VACUUMING", "200"),
    ("PEBBLES_XL", "200"),
    ("GALAXY_SOUNDS_BLACK_HOLES", "200"),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "200"),
]

PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def run_case(case):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    for key, value in case["env"].items():
        env[key] = value
    cmd = [
        "prosperity4btx",
        STRATEGY,
        "5",
        "--merge-pnl",
        "--no-progress",
        "--no-out",
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        return {
            "case": case["case"],
            "kind": case["kind"],
            "product": case["product"],
            "status": "failed",
            "error": result.stdout[-1000:],
        }, []

    current_day = None
    summary = {}
    product_rows = []
    for line in result.stdout.splitlines():
        m = DAY_RE.match(line)
        if m:
            current_day = int(m.group(1))
            continue
        m = SUMMARY_RE.match(line)
        if m:
            summary[int(m.group(1))] = parse_int(m.group(2))
            continue
        m = PRODUCT_RE.match(line)
        if m and current_day is not None and m.group(1) != "Total":
            product_rows.append(
                {
                    "case": case["case"],
                    "kind": case["kind"],
                    "product_under_test": case["product"],
                    "day": current_day,
                    "product": m.group(1),
                    "pnl": parse_int(m.group(2)),
                }
            )

    total = sum(summary.values())
    row = {
        "case": case["case"],
        "kind": case["kind"],
        "product": case["product"],
        "day2": summary.get(2, 0),
        "day3": summary.get(3, 0),
        "day4": summary.get(4, 0),
        "total": total,
        "delta": total - BASE_TOTAL,
        "min_day": min(summary.values()) if summary else 0,
        "status": "ok",
        "error": "",
    }
    return row, product_rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_cases():
    cases = []
    for product in MM_PRODUCTS:
        cases.append(
            {
                "case": "mm_bid_off__" + product,
                "kind": "mm_bid_off",
                "product": product,
                "env": {"MM_BID_OFF_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "mm_ask_off__" + product,
                "kind": "mm_ask_off",
                "product": product,
                "env": {"MM_ASK_OFF_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "mm_drop__" + product,
                "kind": "mm_drop",
                "product": product,
                "env": {"DROP_MM_PRODUCTS": product},
            }
        )

    for product in FREE_ALPHA_PRODUCTS:
        cases.append(
            {
                "case": "free_drop__" + product,
                "kind": "free_drop",
                "product": product,
                "env": {"DROP_FREE_ALPHA_PRODUCTS": product},
            }
        )

    for product, edge in ADD_CANDIDATES:
        cases.append(
            {
                "case": "free_add__" + product,
                "kind": "free_add",
                "product": product,
                "env": {
                    "ADD_FREE_ALPHA_PRODUCTS": product,
                    "FREE_ALPHA_EDGE_OVERRIDES": product + ":" + edge,
                },
            }
        )
    return cases


def main():
    cases = build_cases()
    max_workers = int(os.environ.get("ABLATION_WORKERS", "5"))
    summary_rows = []
    product_rows = []
    print("running %d cases with %d workers" % (len(cases), max_workers))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_case, case) for case in cases]
        for idx, future in enumerate(as_completed(futures), 1):
            row, rows = future.result()
            summary_rows.append(row)
            product_rows.extend(rows)
            if idx % 10 == 0 or row.get("delta", 0) > 0:
                print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row.get("delta", ""), row.get("total", "")))

    summary_rows.sort(key=lambda row: (row["status"] != "ok", -int(row.get("delta", 0))))
    write_csv(
        os.path.join(OUT_DIR, "owner_side_ablation_summary.csv"),
        ["case", "kind", "product", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"],
        summary_rows,
    )
    write_csv(
        os.path.join(OUT_DIR, "owner_side_ablation_product_day.csv"),
        ["case", "kind", "product_under_test", "day", "product", "pnl"],
        product_rows,
    )
    best = summary_rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]))


if __name__ == "__main__":
    main()
