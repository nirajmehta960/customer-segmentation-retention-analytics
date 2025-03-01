"""
Data cleaning for Online Retail dataset (UCI).
Phase 2: Remove cancellations, null CustomerIDs, invalid Quantity/UnitPrice; add Revenue, YearMonth.
Per PRD: ~541K rows -> ~400K after cleaning; ~4,300 unique customers.
"""

import os
import pandas as pd
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RAW_PATH = os.path.join(_PROJECT_ROOT, "data", "raw", "Online Retail.xlsx")
DEFAULT_PREPROCESSED_PATH = os.path.join(_PROJECT_ROOT, "data", "preprocessed", "online_retail_preprocessed.csv")

# Non-product StockCodes to flag (for product analysis); kept in cleaned data for revenue transparency
NON_PRODUCT_CODES = {"POST", "DOT", "M", "BANK CHARGES", "PADS", "CRUK", "D", "C2", "S", "AMAZONFEE", "DCG1", "DCG2", "DCG3"}


def load_raw(data_path: str = None) -> pd.DataFrame:
    """Load raw Excel file. Columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country."""
    path = data_path or DEFAULT_RAW_PATH
    df = pd.read_excel(path, engine="openpyxl")
    return df


def parse_invoice_date(df: pd.DataFrame) -> pd.DataFrame:
    """Parse InvoiceDate to datetime."""
    df = df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    return df


def remove_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where InvoiceNo starts with 'C' (cancellations) or 'A' (accounting adjustments)."""
    df = df.copy()
    # Ensure InvoiceNo is string and stripped for reliable prefix matching
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    invoice_upper = df["InvoiceNo"].str.upper()
    mask = invoice_upper.str.startswith("C") | invoice_upper.str.startswith("A")
    n_cancelled = invoice_upper.str.startswith("C").sum()
    n_adjusted = invoice_upper.str.startswith("A").sum()
    if n_adjusted > 0:
        print(f"  Identified {n_cancelled:,} cancellation rows (C-prefix) and {n_adjusted} accounting adjustment rows (A-prefix)")
    return df[~mask].copy()


def remove_negative_quantity(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with Quantity > 0."""
    return df[df["Quantity"] > 0].copy()


def remove_non_positive_unitprice(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with UnitPrice > 0."""
    return df[df["UnitPrice"] > 0].copy()


def remove_null_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing CustomerID (required for segmentation)."""
    return df[df["CustomerID"].notna()].copy()


def cast_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    """Cast CustomerID from float to int after nulls are removed.
    
    CustomerID loads as float64 (e.g., 17850.0) because the column has NaN values
    in the raw data. After dropping nulls, all remaining values are valid integers.
    Keeping them as floats causes downstream issues: CSVs show '17850.0', and 
    cross-CSV joins can silently fail on float-to-int mismatches.
    """
    df = df.copy()
    df["CustomerID"] = df["CustomerID"].astype(int)
    return df


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Add Revenue = Quantity * UnitPrice."""
    df = df.copy()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    return df


def add_year_month(df: pd.DataFrame) -> pd.DataFrame:
    """Add YearMonth (YYYY-MM) from InvoiceDate for trend analysis."""
    df = df.copy()
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


def add_is_non_product(df: pd.DataFrame) -> pd.DataFrame:
    """Flag non-product StockCodes for downstream product analysis."""
    df = df.copy()
    if "StockCode" in df.columns:
        codes = df["StockCode"].astype(str).str.upper().str.strip()
        df["is_non_product"] = codes.isin({c.upper() for c in NON_PRODUCT_CODES})
    return df


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows and log the impact."""
    before = len(df)
    dupes = df[df.duplicated(keep=False)]
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        n_invoices_affected = dupes["InvoiceNo"].nunique() if "InvoiceNo" in dupes.columns else "N/A"
        print(f"  Found {n_dupes:,} duplicate rows across {n_invoices_affected} invoices")
    df = df.drop_duplicates()
    print(f"  Dropped {before - len(df):,} duplicate rows")
    return df


def log_outlier_investigation(df: pd.DataFrame, revenue_col: str = "Revenue", threshold: float = 10000) -> pd.DataFrame:
    """Log high-revenue transactions for documentation. Does not remove — decision logged.
    
    PRD Section 2.3 requires: "Investigate transactions with Revenue > £10,000 (likely wholesale).
    Decide whether to cap/exclude or keep based on business context. Document decision."
    
    Decision: Keep original values in the cleaned dataset for accurate total revenue reporting.
    For RFM and clustering, downstream scripts should cap monetary at the 99th percentile
    to prevent extreme outliers from distorting quartile scoring and cluster centroids.
    """
    high_rev = df[df[revenue_col] > threshold]
    if len(high_rev) > 0:
        total_rev = df[revenue_col].sum()
        print(f"\n  OUTLIER INVESTIGATION: {len(high_rev)} rows with Revenue > £{threshold:,.0f}")
        print(f"  These represent £{high_rev[revenue_col].sum():,.0f} ({high_rev[revenue_col].sum()/total_rev*100:.1f}% of total revenue)")
        for _, row in high_rev.iterrows():
            print(f"    Customer {int(row.get('CustomerID', 0))}: {row.get('Description', '?')} | Qty={row['Quantity']:,} | Revenue=£{row[revenue_col]:,.0f}")
        print(f"  Decision: Retained in cleaned data (revenue reporting). Downstream RFM/clustering should cap at 99th percentile.\n")
    return df


def run_cleaning_pipeline(
    data_path: str = None,
    save_path: str = None,
) -> pd.DataFrame:
    """
    Run full cleaning pipeline for Online Retail data.
    Uses default paths when arguments are None.
    """
    data_path = data_path or DEFAULT_RAW_PATH
    save_path = save_path or DEFAULT_PREPROCESSED_PATH

    df = load_raw(data_path)
    print(f"Started with: {len(df):,} rows, {df['CustomerID'].notna().sum():,} with CustomerID")

    df = parse_invoice_date(df)
    df = remove_cancellations(df)
    print(f"After removing cancellations/adjustments: {len(df):,} rows")

    df = remove_negative_quantity(df)
    df = remove_non_positive_unitprice(df)
    df = remove_null_customer_id(df)
    df = cast_customer_id(df)
    print(f"After Quantity/UnitPrice/CustomerID filters: {len(df):,} rows")

    df = add_revenue(df)
    df = add_year_month(df)
    df = add_is_non_product(df)
    df = drop_duplicate_rows(df)
    df = log_outlier_investigation(df)

    print(f"Final preprocessed rows: {len(df):,}")
    print(f"Unique customers: {df['CustomerID'].nunique():,}")
    print(f"Unique invoices: {df['InvoiceNo'].nunique():,}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    return df


if __name__ == "__main__":
    run_cleaning_pipeline()
    print(f"Preprocessed data saved to {DEFAULT_PREPROCESSED_PATH}")
