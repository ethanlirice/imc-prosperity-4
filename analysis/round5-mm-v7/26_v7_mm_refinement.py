import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
STRATEGY = "strategies/round5/v7-mm-configurable.py"
BASE_TOTAL = 1196202

MM_PRODUCTS = [
    "GALAXY_SOUNDS_BLACK_HOLES",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "MICROCHIP_CIRCLE",
    "MICROCHIP_OVAL",
    "MICROCHIP_SQUARE",
    "OXYGEN_SHAKE_CHOCOLATE",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "OXYGEN_SHAKE_GARLIC",
    "OXYGEN_SHAKE_MORNING_BREATH",
    "PANEL_1X4",
    "PANEL_2X4",
    "PEBBLES_S",
    "ROBOT_DISHES",
    "ROBOT_IRONING",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_SUEDE",
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_STRAWBERRY",
    "TRANSLATOR_ASTRO_BLACK",
    "UV_VISOR_AMBER",
    "UV_VISOR_ORANGE",
    "UV_VISOR_RED",
]

MR_PRODUCTS = ["PEBBLES_XL", "PEBBLES_XS", "MICROCHIP_TRIANGLE", "ROBOT_LAUNDRY"]
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
    cmd = ["prosperity4btx", STRATEGY, "5", "--merge-pnl", "--no-progress", "--no-out"]
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
        row = {k: case.get(k, "") for k in ("case", "kind", "product", "param")}
        row.update({"status": "failed", "error": result.stdout[-1000:]})
        return row, []

    current_day = None
    summary = {}
    product_rows = []
    for line in result.stdout.splitlines():
        match = DAY_RE.match(line)
        if match:
            current_day = int(match.group(1))
            continue
        match = SUMMARY_RE.match(line)
        if match:
            summary[int(match.group(1))] = parse_int(match.group(2))
            continue
        match = PRODUCT_RE.match(line)
        if match and current_day is not None and match.group(1) != "Total":
            product_rows.append(
                {
                    "case": case["case"],
                    "kind": case["kind"],
                    "product_under_test": case.get("product", ""),
                    "param": case.get("param", ""),
                    "day": current_day,
                    "product": match.group(1),
                    "pnl": parse_int(match.group(2)),
                }
            )

    total = sum(summary.values())
    row = {k: case.get(k, "") for k in ("case", "kind", "product", "param")}
    row.update(
        {
            "day2": summary.get(2, 0),
            "day3": summary.get(3, 0),
            "day4": summary.get(4, 0),
            "total": total,
            "delta": total - BASE_TOTAL,
            "min_day": min(summary.values()) if summary else 0,
            "status": "ok",
            "error": "",
        }
    )
    return row, product_rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_cases():
    cases = [
        {"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}},
    ]
    for size in (1, 2, 3, 4, 5, 7):
        cases.append({"case": "global_size_%s" % size, "kind": "global_size", "product": "", "param": str(size), "env": {"MM_SIZE": str(size)}})

    for product in MM_PRODUCTS:
        for size in (1, 2, 5):
            cases.append(
                {
                    "case": "size_%s__%s" % (size, product),
                    "kind": "product_size",
                    "product": product,
                    "param": str(size),
                    "env": {"MM_SIZE_BY_PRODUCT": product + ":" + str(size)},
                }
            )
        cases.append(
            {
                "case": "flat_only__" + product,
                "kind": "flat_only",
                "product": product,
                "param": "",
                "env": {"MM_FLAT_ONLY_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "reduce_only__" + product,
                "kind": "reduce_only",
                "product": product,
                "param": "",
                "env": {"MM_REDUCE_ONLY_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "drop_mm__" + product,
                "kind": "drop_mm",
                "product": product,
                "param": "",
                "env": {"DROP_MM_PRODUCTS": product},
            }
        )

    for threshold in (1, 3, 5, 8):
        cases.append(
            {
                "case": "global_inv_reduce_%s" % threshold,
                "kind": "global_inv_reduce",
                "product": "",
                "param": str(threshold),
                "env": {"MM_INVENTORY_REDUCE_THRESHOLD": str(threshold)},
            }
        )

    for product in MR_PRODUCTS:
        cases.append(
            {
                "case": "add_mr_mm__" + product,
                "kind": "add_mr_mm",
                "product": product,
                "param": "normal",
                "env": {"ADD_MM_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "add_mr_mm_flat__" + product,
                "kind": "add_mr_mm_flat",
                "product": product,
                "param": "flat",
                "env": {"ADD_MM_PRODUCTS": product, "MM_FLAT_ONLY_PRODUCTS": product},
            }
        )
        cases.append(
            {
                "case": "add_mr_mm_reduce__" + product,
                "kind": "add_mr_mm_reduce",
                "product": product,
                "param": "reduce",
                "env": {"ADD_MM_PRODUCTS": product, "MM_REDUCE_ONLY_PRODUCTS": product},
            }
        )
    return cases


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cases = build_cases()
    max_workers = int(os.environ.get("MM_V7_WORKERS", "5"))
    summary_rows = []
    product_rows = []
    summary_fields = ["case", "kind", "product", "param", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
    product_fields = ["case", "kind", "product_under_test", "param", "day", "product", "pnl"]
    print("running %d v7 MM cases with %d workers" % (len(cases), max_workers), flush=True)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_case, case) for case in cases]
        for idx, future in enumerate(as_completed(futures), 1):
            row, rows = future.result()
            summary_rows.append(row)
            product_rows.extend(rows)
            if idx % 10 == 0 or int(row.get("delta", -10**9)) > 0:
                print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row.get("delta", ""), row.get("total", "")), flush=True)
            if idx % 5 == 0 or idx == len(cases):
                checkpoint = sorted(summary_rows, key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
                write_csv(os.path.join(OUT_DIR, "v7_mm_refinement_summary.partial.csv"), summary_fields, checkpoint)
                write_csv(os.path.join(OUT_DIR, "v7_mm_refinement_product_day.partial.csv"), product_fields, product_rows)

    summary_rows.sort(key=lambda row: (row["status"] != "ok", -int(row.get("delta", -10**9))))
    write_csv(
        os.path.join(OUT_DIR, "v7_mm_refinement_summary.csv"),
        summary_fields,
        summary_rows,
    )
    write_csv(
        os.path.join(OUT_DIR, "v7_mm_refinement_product_day.csv"),
        product_fields,
        product_rows,
    )
    best = summary_rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
