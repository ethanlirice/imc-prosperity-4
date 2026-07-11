import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(__file__)
STRATEGY = "strategies/round5/base-strategy-free-alpha-side-gated-mr-configurable.py"
BASE_TOTAL = 1196202

PAIR_KEYS = [
    "MICROCHIP_RECTANGLE__MICROCHIP_SQUARE",
    "SNACKPACK_RASPBERRY__SNACKPACK_VANILLA",
    "GALAXY_SOUNDS_SOLAR_FLAMES__GALAXY_SOUNDS_SOLAR_WINDS",
    "SLEEP_POD_LAMB_WOOL__SLEEP_POD_NYLON",
]

WINDOWS = [200, 500, 1000]
ENTRY_ZS = [1.5, 2.0, 2.5, 3.0]
HOLDS = [200, 500]

PRODUCT_RE = re.compile(r"^([A-Z0-9_]+):\s+(-?[\d,]+)$")
DAY_RE = re.compile(r"^Backtesting .* on round 5 day (\d+)$")
SUMMARY_RE = re.compile(r"^Round 5 day (\d+):\s+(-?[\d,]+)$")


def parse_int(text):
    return int(text.replace(",", ""))


def run_case(case):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["MR_PRODUCTS"] = "ALL"
    env["PAIR_SPREADS"] = case["pair_key"]
    env["PAIR_WINDOW"] = str(case["window"])
    env["PAIR_ENTRY_Z"] = str(case["entry_z"])
    env["PAIR_HOLD"] = str(case["hold"])
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
        row = dict(case)
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
                    "day": current_day,
                    "product": match.group(1),
                    "pnl": parse_int(match.group(2)),
                }
            )

    total = sum(summary.values())
    row = dict(case)
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
    cases = []
    for pair_key in PAIR_KEYS:
        for window in WINDOWS:
            for entry_z in ENTRY_ZS:
                for hold in HOLDS:
                    cases.append(
                        {
                            "case": "%s__w%s__z%s__h%s" % (pair_key, window, entry_z, hold),
                            "pair_key": pair_key,
                            "window": window,
                            "entry_z": entry_z,
                            "hold": hold,
                        }
                    )
    return cases


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cases = build_cases()
    max_workers = int(os.environ.get("PAIR_WORKERS", "5"))
    summary_rows = []
    product_rows = []
    print("running %d pair-spread cases with %d workers" % (len(cases), max_workers))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_case, case) for case in cases]
        for idx, future in enumerate(as_completed(futures), 1):
            row, rows = future.result()
            summary_rows.append(row)
            product_rows.extend(rows)
            if idx % 10 == 0 or int(row.get("delta", -10**9)) > 0:
                print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row.get("delta", ""), row.get("total", "")))

    summary_rows.sort(key=lambda row: (row["status"] != "ok", -int(row.get("delta", -10**9))))
    write_csv(
        os.path.join(OUT_DIR, "pair_spread_integration_summary.csv"),
        ["case", "pair_key", "window", "entry_z", "hold", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"],
        summary_rows,
    )
    write_csv(
        os.path.join(OUT_DIR, "pair_spread_integration_product_day.csv"),
        ["case", "day", "product", "pnl"],
        product_rows,
    )
    best = summary_rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]))


if __name__ == "__main__":
    main()
