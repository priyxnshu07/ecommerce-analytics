"""Data-quality checks on the processed tables (run: pytest).

These encode the cleaning rules as assertions, so a change to the pipeline
that breaks one fails loudly instead of quietly skewing the analysis.
"""
from pathlib import Path

import duckdb
import pytest

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.execute(f"CREATE VIEW orders AS SELECT * FROM '{(PROCESSED / 'orders.parquet').as_posix()}'")
    c.execute(f"CREATE VIEW order_items AS SELECT * FROM '{(PROCESSED / 'order_items.parquet').as_posix()}'")
    return c


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_one_row_per_order(con):
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM orders") == 0


def test_one_row_per_order_item(con):
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT (order_id, order_item_id)) FROM order_items") == 0


def test_revenue_reconciles_between_tables(con):
    # Order-level GMV must equal the sum of item prices, to the cent.
    diff = one(con, "SELECT ROUND((SELECT SUM(gmv) FROM orders) - (SELECT SUM(price) FROM order_items), 2)")
    assert diff == 0


def test_item_counts_reconcile(con):
    assert one(con, "SELECT SUM(items) FROM orders") == one(con, "SELECT COUNT(*) FROM order_items")


def test_no_negative_money(con):
    assert one(con, "SELECT COUNT(*) FROM orders WHERE gmv < 0 OR freight < 0") == 0
    assert one(con, "SELECT COUNT(*) FROM order_items WHERE price <= 0 OR freight_value < 0") == 0


def test_review_scores_are_valid(con):
    assert one(con, "SELECT COUNT(*) FROM orders WHERE review_score NOT BETWEEN 1 AND 5") == 0


def test_delivery_metrics_only_for_delivered_orders(con):
    assert one(con, "SELECT COUNT(*) FROM orders WHERE delivery_days IS NOT NULL AND NOT has_delivery") == 0
    assert one(con, "SELECT COUNT(*) FROM orders WHERE delivery_days < 0") == 0


def test_late_flag_matches_delay(con):
    assert one(con, "SELECT COUNT(*) FROM orders WHERE is_late <> (delay_days > 0)") == 0


def test_every_item_has_a_category(con):
    assert one(con, "SELECT COUNT(*) FROM order_items WHERE category IS NULL") == 0


def test_each_customer_has_exactly_one_first_order(con):
    assert one(con, """
        SELECT COUNT(*) FROM (
            SELECT customer_unique_id FROM orders
            GROUP BY 1 HAVING COUNT(*) FILTER (WHERE customer_order_number = 1) <> 1
        )""") == 0


def test_analysis_window_is_20_complete_months(con):
    months = con.execute(
        "SELECT MIN(purchase_month), MAX(purchase_month), COUNT(DISTINCT purchase_month) FROM orders WHERE in_window"
    ).fetchone()
    assert str(months[0]) == "2017-01-01"
    assert str(months[1]) == "2018-08-01"
    assert months[2] == 20
