from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]
PRODUCTS = ["ROBOT_DISHES", "PEBBLES_L", "OXYGEN_SHAKE_MINT", "SNACKPACK_STRAWBERRY", "SNACKPACK_CHOCOLATE"]


def main():
    cases = [{"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}}]
    for product in PRODUCTS:
        cases.append({"case": "owned_mm_reduce__" + product, "kind": "owned_mm_reduce", "product": product, "param": "reduce", "env": {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product, "MM_REDUCE_ONLY_PRODUCTS": product}})
        cases.append({"case": "owned_mm_size1__" + product, "kind": "owned_mm_size1", "product": product, "param": "size1", "env": {"ADD_MM_PRODUCTS": product, "MM_WITH_OWNED_PRODUCTS": product, "MM_SIZE_BY_PRODUCT": "%s:1" % product}})
    rows = []
    product_rows = []
    for idx, case in enumerate(cases, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(cases), row["case"], row["delta"], row["total"]), flush=True)
        write_csv(OUT_DIR / "v11_mm_owned_summary.partial.csv", SUMMARY_FIELDS, rows)
        write_csv(OUT_DIR / "v11_mm_owned_product_day.partial.csv", PRODUCT_FIELDS, product_rows)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_owned_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_owned_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
