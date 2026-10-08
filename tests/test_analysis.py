"""Sanity checks on the analysis queries (run: pytest).

Each query must run and return rows, and shares that should add up to 100%
must do so, which catches double counting from a bad join.
"""
from pathlib import Path

import pytest

from src.analysis import SQL_DIR, connect, run_query


@pytest.fixture(scope="module")
def con():
    return connect()


def q(con, name):
    return run_query(con, SQL_DIR / f"{name}.sql")


@pytest.mark.parametrize("path", sorted(SQL_DIR.glob("*.sql")), ids=lambda p: p.stem)
def test_every_query_runs_and_returns_rows(con, path: Path):
    assert len(run_query(con, path)) > 0


def test_monthly_revenue_covers_the_20_month_window(con):
    df = q(con, "01_monthly_revenue")
    assert len(df) == 20


def test_delivery_buckets_cover_all_delivered_orders(con):
    df = q(con, "02_delivery_vs_reviews")
    assert df["pct_of_orders"].sum() == pytest.approx(100, abs=0.2)
    # Only the buckets after the promised date may be flagged late.
    assert set(df.loc[df["is_late"], "delivery_bucket"].str[0]) == {"4", "5", "6", "7"}


def test_category_and_seller_shares_add_up(con):
    assert q(con, "04_category_pareto")["cumulative_share_pct"].iloc[-1] == pytest.approx(100, abs=0.01)
    assert q(con, "04b_seller_concentration")["cumulative_share_pct"].iloc[-1] == pytest.approx(100, abs=0.01)


def test_rfm_segments_cover_every_customer_once(con):
    rfm = q(con, "05_rfm_segments")
    customers = q(con, "03_repeat_customers")["customers"].iloc[0]
    assert rfm["customers"].sum() == customers
    assert rfm["pct_gmv"].sum() == pytest.approx(100, abs=0.2)


@pytest.mark.parametrize("path", sorted(SQL_DIR.glob("*.sql")), ids=lambda p: p.stem)
def test_every_query_is_deterministic(path: Path):
    # Window functions like NTILE split ties arbitrarily unless the ORDER BY is
    # total; a fresh connection must give exactly the same result.
    first = run_query(connect(), path)
    second = run_query(connect(), path)
    assert first.equals(second)


def test_late_orders_are_overrepresented_in_low_reviews(con):
    impact = q(con, "02c_late_delivery_impact").iloc[0]
    assert 0 < impact["late_share_of_orders_pct"] < impact["share_of_low_reviews_from_late_pct"] < 100
    # The what-if can only remove low reviews, never add them.
    assert impact["low_reviews_if_on_time"] < impact["low_reviews_now"]
