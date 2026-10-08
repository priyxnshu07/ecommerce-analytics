# E-commerce Analytics: Olist Marketplace

End-to-end analysis of ~100,000 real orders from Olist, a Brazilian e-commerce marketplace (2016–2018): data cleaning in SQL, business analysis, an interactive dashboard and recommendations.

**[▶ Live dashboard](https://list-ecommerce-analytics.streamlit.app/)**

> Work in progress. Pipeline, SQL analysis and dashboard are done; the insights memo is next.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py   # raw CSVs, pinned to a fixed commit
python -m src.etl                 # clean tables -> data/processed/*.parquet
python -m src.analysis            # run sql/*.sql -> reports/results/*.csv
pytest                            # data-quality + analysis checks
streamlit run app.py              # interactive dashboard at http://localhost:8501
```

## Business questions

| # | Question | Query |
| --- | --- | --- |
| 1 | How are orders and revenue trending? | [`sql/01_monthly_revenue.sql`](sql/01_monthly_revenue.sql) |
| 2 | Do late deliveries hurt reviews, and by how much? | [`sql/02_delivery_vs_reviews.sql`](sql/02_delivery_vs_reviews.sql) |
| 3 | Do customers come back? | [`sql/03_repeat_customers.sql`](sql/03_repeat_customers.sql), [`sql/03b_cohort_retention.sql`](sql/03b_cohort_retention.sql) |
| 4 | Which categories and sellers drive revenue? | [`sql/04_category_pareto.sql`](sql/04_category_pareto.sql), [`sql/04b_seller_concentration.sql`](sql/04b_seller_concentration.sql) |
| 5 | Which customer segments matter most? (RFM) | [`sql/05_rfm_segments.sql`](sql/05_rfm_segments.sql) |

## Data cleaning decisions

| Issue found while profiling | Decision |
| --- | --- |
| 2016 is sparse (no orders at all in Nov 2016); Sep–Oct 2018 are partial | Analyse Jan 2017 – Aug 2018 (20 complete months); other orders kept but flagged |
| Payments differ from items + freight on 249 orders (installment interest) | Revenue (GMV) = sum of item prices; freight reported separately |
| 775 orders have no items (mostly canceled or unavailable) | Zero revenue; excluded from revenue analysis |
| 555 orders have more than one review | Keep the most recent review |
| 610 products have no category; 2 categories lack an English name | Label `unknown`; translate the 2 manually |
| 8 "delivered" orders have no delivery date | Excluded from delivery metrics only |
| `customer_id` is new for every order | Identify customers by `customer_unique_id` (96,096 people) |

## Data source

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0), downloaded from a [GitHub mirror](https://github.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist) pinned to one commit.
