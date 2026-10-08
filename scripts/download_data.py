"""Download the raw Olist e-commerce CSVs into data/raw/.

Source: Olist, "Brazilian E-Commerce Public Dataset" (Kaggle, CC BY-NC-SA 4.0),
via a GitHub mirror pinned to one commit so the data can never change silently.
Run:  python scripts/download_data.py
"""
from pathlib import Path
from urllib.request import urlopen

MIRROR = "https://raw.githubusercontent.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist"
COMMIT = "fa0cc6d1aff713d3c8b9a1e633b56889881848bf"
FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = RAW_DIR / name
        if target.exists():
            print(f"skip  {name} (already downloaded)")
            continue
        with urlopen(f"{MIRROR}/{COMMIT}/files/{name}", timeout=120) as resp:
            target.write_bytes(resp.read())
        print(f"saved {name} ({target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
