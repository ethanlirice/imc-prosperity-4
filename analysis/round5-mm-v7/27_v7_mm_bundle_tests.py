import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
STRATEGY = "strategies/round5/v7-mm-configurable.py"
BASE_TOTAL = 1196202
PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def size_map(pairs):
    return ",".join("%s:%s" % (product, size) for product, size in pairs)


CASES = [
    {"case": "top2_size1", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1)])}},
    {"case": "top2_plus_laundry", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1)]), "ADD_MM_PRODUCTS": "ROBOT_LAUNDRY"}},
    {"case": "top3_sizes", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1)])}},
    {"case": "top3_sizes_plus_laundry", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1)]), "ADD_MM_PRODUCTS": "ROBOT_LAUNDRY"}},
    {"case": "top5_sizes", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1), ("OXYGEN_SHAKE_GARLIC", 1), ("MICROCHIP_CIRCLE", 1)])}},
    {"case": "top5_sizes_plus_laundry", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1), ("OXYGEN_SHAKE_GARLIC", 1), ("MICROCHIP_CIRCLE", 1)]), "ADD_MM_PRODUCTS": "ROBOT_LAUNDRY"}},
    {"case": "top8_sizes", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1), ("OXYGEN_SHAKE_GARLIC", 1), ("MICROCHIP_CIRCLE", 1), ("PANEL_2X4", 1), ("SNACKPACK_STRAWBERRY", 2), ("ROBOT_IRONING", 1)])}},
    {"case": "top8_sizes_plus_laundry", "env": {"MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1), ("OXYGEN_SHAKE_GARLIC", 1), ("MICROCHIP_CIRCLE", 1), ("PANEL_2X4", 1), ("SNACKPACK_STRAWBERRY", 2), ("ROBOT_IRONING", 1)]), "ADD_MM_PRODUCTS": "ROBOT_LAUNDRY"}},
    {"case": "global4_plus_top2", "env": {"MM_SIZE": "4", "MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1)])}},
    {"case": "global4_plus_top5_laundry", "env": {"MM_SIZE": "4", "MM_SIZE_BY_PRODUCT": size_map([("GALAXY_SOUNDS_PLANETARY_RINGS", 1), ("UV_VISOR_ORANGE", 1), ("OXYGEN_SHAKE_MORNING_BREATH", 1), ("OXYGEN_SHAKE_GARLIC", 1), ("MICROCHIP_CIRCLE", 1)]), "ADD_MM_PRODUCTS": "ROBOT_LAUNDRY"}},
]


def run_case(case):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env.update(case["env"])
    cmd = ["prosperity4btx", STRATEGY, "5", "--merge-pnl", "--no-progress", "--no-out"]
    result = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        return {"case": case["case"], "status": "failed", "error": result.stdout[-1000:]}, []
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
            product_rows.append({"case": case["case"], "day": current_day, "product": match.group(1), "pnl": parse_int(match.group(2))})
    total = sum(summary.values())
    return {
        "case": case["case"],
        "day2": summary.get(2, 0),
        "day3": summary.get(3, 0),
        "day4": summary.get(4, 0),
        "total": total,
        "delta": total - BASE_TOTAL,
        "status": "ok",
        "error": "",
    }, product_rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = []
    product_rows = []
    max_workers = int(os.environ.get("MM_BUNDLE_WORKERS", "5"))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_case, case) for case in CASES]
        for future in as_completed(futures):
            row, products = future.result()
            rows.append(row)
            product_rows.extend(products)
            print("%s delta=%s total=%s" % (row["case"], row.get("delta", ""), row.get("total", "")), flush=True)
    rows.sort(key=lambda row: (row["status"] != "ok", -int(row.get("delta", -10**9))))
    write_csv(os.path.join(OUT_DIR, "v7_mm_bundle_summary.csv"), ["case", "day2", "day3", "day4", "total", "delta", "status", "error"], rows)
    write_csv(os.path.join(OUT_DIR, "v7_mm_bundle_product_day.csv"), ["case", "day", "product", "pnl"], product_rows)
    print("best %s delta=%s total=%s" % (rows[0]["case"], rows[0]["delta"], rows[0]["total"]), flush=True)


if __name__ == "__main__":
    main()
