from _common import OUT_DIR, run_case, write_csv

SUMMARY_FIELDS = ["case", "kind", "product", "param", "match_mode", "day2", "day3", "day4", "total", "delta", "min_day", "status", "error"]
PRODUCT_FIELDS = ["case", "kind", "product_under_test", "param", "match_mode", "day", "product", "pnl"]

CASES = [
    {"case": "baseline", "kind": "baseline", "product": "", "param": "", "env": {}},
    {
        "case": "bundle_pebbles_l_reduce_snack_choc_size1",
        "kind": "bundle",
        "product": "PEBBLES_L,SNACKPACK_CHOCOLATE",
        "param": "",
        "env": {
            "ADD_MM_PRODUCTS": "PEBBLES_L,SNACKPACK_CHOCOLATE",
            "MM_WITH_OWNED_PRODUCTS": "PEBBLES_L,SNACKPACK_CHOCOLATE",
            "MM_REDUCE_ONLY_PRODUCTS": "PEBBLES_L",
            "MM_SIZE_BY_PRODUCT": "SNACKPACK_CHOCOLATE:1",
        },
    },
    {
        "case": "bundle_pebbles_l_reduce_robot_dishes_reduce",
        "kind": "bundle",
        "product": "PEBBLES_L,ROBOT_DISHES",
        "param": "",
        "env": {
            "ADD_MM_PRODUCTS": "PEBBLES_L,ROBOT_DISHES",
            "MM_WITH_OWNED_PRODUCTS": "PEBBLES_L,ROBOT_DISHES",
            "MM_REDUCE_ONLY_PRODUCTS": "PEBBLES_L,ROBOT_DISHES",
        },
    },
    {
        "case": "bundle_snack_choc_size1_robot_dishes_reduce",
        "kind": "bundle",
        "product": "SNACKPACK_CHOCOLATE,ROBOT_DISHES",
        "param": "",
        "env": {
            "ADD_MM_PRODUCTS": "SNACKPACK_CHOCOLATE,ROBOT_DISHES",
            "MM_WITH_OWNED_PRODUCTS": "SNACKPACK_CHOCOLATE,ROBOT_DISHES",
            "MM_REDUCE_ONLY_PRODUCTS": "ROBOT_DISHES",
            "MM_SIZE_BY_PRODUCT": "SNACKPACK_CHOCOLATE:1",
        },
    },
    {
        "case": "bundle_all_three",
        "kind": "bundle",
        "product": "PEBBLES_L,SNACKPACK_CHOCOLATE,ROBOT_DISHES",
        "param": "",
        "env": {
            "ADD_MM_PRODUCTS": "PEBBLES_L,SNACKPACK_CHOCOLATE,ROBOT_DISHES",
            "MM_WITH_OWNED_PRODUCTS": "PEBBLES_L,SNACKPACK_CHOCOLATE,ROBOT_DISHES",
            "MM_REDUCE_ONLY_PRODUCTS": "PEBBLES_L,ROBOT_DISHES",
            "MM_SIZE_BY_PRODUCT": "SNACKPACK_CHOCOLATE:1",
        },
    },
]


def main():
    rows = []
    product_rows = []
    for idx, case in enumerate(CASES, 1):
        row, products = run_case(case)
        rows.append(row)
        product_rows.extend(products)
        print("%d/%d %s delta=%s total=%s" % (idx, len(CASES), row["case"], row["delta"], row["total"]), flush=True)
    rows.sort(key=lambda item: (item["status"] != "ok", -int(item.get("delta", -10**9))))
    write_csv(OUT_DIR / "v11_mm_bundle_summary.csv", SUMMARY_FIELDS, rows)
    write_csv(OUT_DIR / "v11_mm_bundle_product_day.csv", PRODUCT_FIELDS, product_rows)
    best = rows[0]
    print("best %s total=%s delta=%s days=%s/%s/%s" % (best["case"], best["total"], best["delta"], best["day2"], best["day3"], best["day4"]), flush=True)


if __name__ == "__main__":
    main()
