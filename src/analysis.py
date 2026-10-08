"""Run every business-question query in sql/ and save the results.

    python -m src.analysis

Each sql/NN_name.sql file answers one question. Results are written to
reports/results/NN_name.csv, which the dashboard and the insights memo read.
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
RESULTS = ROOT / "reports" / "results"

# "Revenue orders": inside the analysis window, with at least one item, and
# not canceled or unavailable. Every revenue question uses this one definition.
REVENUE_ORDERS = """
    CREATE OR REPLACE VIEW revenue_orders AS
    SELECT * FROM orders
    WHERE in_window
      AND items > 0
      AND order_status NOT IN ('canceled', 'unavailable')
"""


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"CREATE VIEW orders AS SELECT * FROM '{(PROCESSED / 'orders.parquet').as_posix()}'")
    con.execute(f"CREATE VIEW order_items AS SELECT * FROM '{(PROCESSED / 'order_items.parquet').as_posix()}'")
    con.execute(REVENUE_ORDERS)
    return con


def run_query(con: duckdb.DuckDBPyConnection, path: Path):
    return con.execute(path.read_text()).df()


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    con = connect()
    for path in sorted(SQL_DIR.glob("*.sql")):
        df = run_query(con, path)
        out = RESULTS / f"{path.stem}.csv"
        df.to_csv(out, index=False)
        print(f"\n== {path.stem}  ({len(df)} rows -> {out.relative_to(ROOT)})")
        print(df.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
