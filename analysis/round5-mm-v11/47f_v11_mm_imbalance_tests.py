from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]
CASES = [{"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}}]
for product in ["MICROCHIP_SQUARE", "OXYGEN_SHAKE_GARLIC", "PEBBLES_S", "MICROCHIP_CIRCLE"]:
    for threshold in ["0.2", "0.4"]:
        CASES.append(
            {
                "case": "imb_%s__%s" % (threshold.replace(".", "p"), product),
                "kind": "imbalance",
                "product": product,
                "param": threshold,
                "env": {"MM_IMB_FILTER_PRODUCTS": product, "MM_IMB_THRESHOLD_BY_PRODUCT": "%s:%s" % (product, threshold)},
            }
        )


def main():
    rows = []
    product_rows = []
    for idx, case in enumerate(CASES, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(CASES), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_imbalance_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_imbalance_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_imbalance_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_imbalance_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
