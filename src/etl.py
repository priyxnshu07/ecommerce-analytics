"""Build clean, analysis-ready tables from the raw Olist CSVs.

    python -m src.etl

Reads data/raw/*.csv (see scripts/download_data.py), cleans them in DuckDB
with SQL, and writes two Parquet tables to data/processed/:

    orders.parquet       one row per order: customer, dates, revenue,
                         delivery performance, review score, order sequence
    order_items.parquet  one row per item: product category, seller, price

Every cleaning decision is listed in CLEANING_DECISIONS and in the README.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# Complete months only: 2016 is sparse (Nov 2016 has no orders) and
# Sep-Oct 2018 hold a handful of trailing orders.
WINDOW_START = "2017-01-01"
WINDOW_END = "2018-09-01"  # exclusive

# Two categories have no English name in the official translation table.
MISSING_TRANSLATIONS = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_preparers",
}

CLEANING_DECISIONS = [
    "Analysis window = Jan 2017 to Aug 2018 (complete months); orders outside it are kept but flagged.",
    "Revenue (GMV) = sum of item prices; freight reported separately; payments not used because they include installment interest.",
    "Orders with no items (mostly canceled/unavailable) carry zero revenue and are excluded from revenue analysis.",
    "Orders with several reviews keep the most recent one.",
    "Products with no category are labelled 'unknown'; two untranslated categories are translated manually.",
    "Delivery metrics only for delivered orders that have a delivery date (8 delivered orders lack one).",
    "Customers are identified by customer_unique_id; customer_id is a per-order key in this dataset.",
]


def csv(name: str) -> str:
    return f"read_csv_auto('{(RAW / name).as_posix()}', header = true)"


def build(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE OR REPLACE TABLE raw_orders AS SELECT * FROM {csv('olist_orders_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_items AS SELECT * FROM {csv('olist_order_items_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_payments AS SELECT * FROM {csv('olist_order_payments_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_reviews AS SELECT * FROM {csv('olist_order_reviews_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_customers AS SELECT * FROM {csv('olist_customers_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_products AS SELECT * FROM {csv('olist_products_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_sellers AS SELECT * FROM {csv('olist_sellers_dataset.csv')}")
    con.execute(f"CREATE OR REPLACE TABLE raw_translation AS SELECT * FROM {csv('product_category_name_translation.csv')}")

    extra = " UNION ALL ".join(f"SELECT '{pt}' AS pt, '{en}' AS en" for pt, en in MISSING_TRANSLATIONS.items())
    con.execute(f"""
        CREATE OR REPLACE TABLE categories AS
        SELECT product_category_name AS pt, product_category_name_english AS en FROM raw_translation
        UNION ALL {extra}
    """)

    con.execute("""
        CREATE OR REPLACE TABLE order_items AS
        SELECT
            i.order_id,
            i.order_item_id,
            i.product_id,
            i.seller_id,
            s.seller_state,
            COALESCE(c.en, 'unknown')            AS category,
            i.price,
            i.freight_value
        FROM raw_items i
        JOIN raw_products p USING (product_id)
        LEFT JOIN categories c ON c.pt = p.product_category_name
        JOIN raw_sellers s USING (seller_id)
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE orders AS
        WITH items AS (
            SELECT order_id,
                   COUNT(*)            AS items,
                   SUM(price)          AS gmv,
                   SUM(freight_value)  AS freight
            FROM raw_items GROUP BY order_id
        ),
        payments AS (
            SELECT order_id,
                   SUM(payment_value)                      AS payment_value,
                   ARG_MAX(payment_type, payment_value)    AS payment_type,
                   MAX(payment_installments)               AS installments
            FROM raw_payments GROUP BY order_id
        ),
        latest_review AS (
            SELECT order_id, review_score
            FROM raw_reviews
            QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1
        ),
        base AS (
            SELECT
                o.order_id,
                c.customer_unique_id,
                c.customer_state,
                c.customer_city,
                o.order_status,
                o.order_purchase_timestamp                           AS purchase_ts,
                DATE_TRUNC('month', o.order_purchase_timestamp)::DATE AS purchase_month,
                o.order_delivered_customer_date                      AS delivered_ts,
                o.order_estimated_delivery_date::DATE                AS estimated_date,
                COALESCE(i.items, 0)                                 AS items,
                COALESCE(i.gmv, 0)                                   AS gmv,
                COALESCE(i.freight, 0)                               AS freight,
                p.payment_value,
                p.payment_type,
                p.installments,
                r.review_score
            FROM raw_orders o
            JOIN raw_customers c USING (customer_id)
            LEFT JOIN items i USING (order_id)
            LEFT JOIN payments p USING (order_id)
            LEFT JOIN latest_review r USING (order_id)
        )
        SELECT
            *,
            order_status = 'delivered' AND delivered_ts IS NOT NULL                    AS has_delivery,
            CASE WHEN delivered_ts IS NOT NULL AND order_status = 'delivered'
                 THEN DATE_DIFF('hour', purchase_ts, delivered_ts) / 24.0 END          AS delivery_days,
            CASE WHEN delivered_ts IS NOT NULL AND order_status = 'delivered'
                 THEN DATE_DIFF('day', estimated_date, delivered_ts::DATE) END         AS delay_days,
            CASE WHEN delivered_ts IS NOT NULL AND order_status = 'delivered'
                 THEN delivered_ts::DATE > estimated_date END                          AS is_late,
            ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_ts)   AS customer_order_number,
            purchase_ts >= DATE '{WINDOW_START}' AND purchase_ts < DATE '{WINDOW_END}' AS in_window
        FROM base
    """)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    build(con)
    for table in ("orders", "order_items"):
        target = OUT / f"{table}.parquet"
        con.execute(f"COPY {table} TO '{target.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"wrote {target.relative_to(ROOT)}: {rows:,} rows, {target.stat().st_size / 1e6:.1f} MB")
    print("\nCleaning decisions:")
    for d in CLEANING_DECISIONS:
        print(f"  - {d}")


if __name__ == "__main__":
    main()
