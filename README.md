# E-commerce Analytics: Olist Marketplace

End-to-end analysis of ~100,000 real orders from Olist, a Brazilian e-commerce marketplace (2016–2018): data cleaning in SQL, business analysis, an interactive dashboard and recommendations.

> Work in progress. Step 1 (data pipeline) is done; analysis, dashboard and insights are next.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py   # raw CSVs, pinned to a fixed commit
python -m src.etl                 # clean tables -> data/processed/*.parquet
pytest                            # 11 data-quality checks
```

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
