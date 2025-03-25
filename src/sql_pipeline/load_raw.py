"""
Load the project's transactional dataset into SQLite as `online_retail`.

Default source is the cleaned CSV produced by `src/data_cleaning.py`:
  data/preprocessed/online_retail_preprocessed.csv

This mirrors the diabetes project's workflow where raw tables are loaded first,
then the SQL ETL builds curated layers on top.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "retail.sqlite"
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "preprocessed" / "online_retail_preprocessed.csv"
DEFAULT_TABLE = "online_retail"


def load_online_retail(csv_path: Path, db_path: Path, table: str = DEFAULT_TABLE) -> None:
    df = pd.read_csv(csv_path)

    # Ensure InvoiceDate is a string in a SQLite-friendly ISO-ish format.
    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Online Retail data into SQLite as `online_retail`.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to preprocessed CSV.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file.")
    parser.add_argument("--table", type=str, default=DEFAULT_TABLE, help="Destination table name.")
    args = parser.parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"CSV not found: {args.csv}")

    load_online_retail(args.csv, args.db, args.table)
    print(f"Loaded {args.csv} into {args.db} as table `{args.table}`")


if __name__ == "__main__":
    main()

