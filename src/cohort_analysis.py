"""
Cohort retention analysis: assign cohort by first purchase month, compute retention by month index.
"""

import os
import pandas as pd
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PREPROCESSED_PATH = os.path.join(_PROJECT_ROOT, "data", "preprocessed", "online_retail_preprocessed.csv")
DEFAULT_COHORT_OUTPUT_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "cohort_retention.csv")


def assign_cohort_and_index(
    df: pd.DataFrame,
    date_col: str = "InvoiceDate",
    customer_col: str = "CustomerID",
) -> pd.DataFrame:
    """Add cohort (first purchase month) and cohort_index (months since first purchase) per transaction."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    first_purchase = df.groupby(customer_col)[date_col].min().reset_index()
    first_purchase.columns = [customer_col, "first_purchase"]
    first_purchase["cohort"] = first_purchase["first_purchase"].dt.to_period("M").astype(str)
    df = df.merge(first_purchase, on=customer_col, how="left")
    df["cohort_index"] = (df[date_col].dt.year - df["first_purchase"].dt.year) * 12 + (df[date_col].dt.month - df["first_purchase"].dt.month)
    return df


def retention_heatmap_data(
    df: pd.DataFrame,
    customer_col: str = "CustomerID",
) -> pd.DataFrame:
    """
    For each cohort (row) and cohort_index (column), compute % of cohort still active.
    Returns wide-format dataframe: index=cohort, columns=0,1,2,... (months since first purchase).
    """
    df = df.copy()
    if "cohort" not in df.columns or "cohort_index" not in df.columns:
        df = assign_cohort_and_index(df)

    # Active in month = unique customers per (cohort, cohort_index)
    active = df.groupby(["cohort", "cohort_index"])[customer_col].nunique().reset_index(name="n_customers")
    cohort_sizes = df.groupby("cohort")[customer_col].nunique()
    pivot = active.pivot(index="cohort", columns="cohort_index", values="n_customers")

    # Retention % = active in month N / cohort size
    # Use pandas index alignment (no .values) to avoid silent misalignment bugs
    for col in pivot.columns:
        pivot[col] = (pivot[col] / cohort_sizes.reindex(pivot.index) * 100).round(1)
    return pivot


def summarize_retention(heatmap: pd.DataFrame) -> dict:
    """Extract key retention KPIs averaged across cohorts.
    
    PRD Dashboard Page 3 requires: 'Month-1 retention, Month-6 retention, Month-12 retention.'
    Returns a dict like {"month_1_retention": 25.3, "month_3_retention": 18.1, ...}.
    """
    summary = {}
    for month in [1, 3, 6, 12]:
        if month in heatmap.columns:
            summary[f"month_{month}_retention"] = round(heatmap[month].mean(), 1)
    return summary


def run_cohort_pipeline(
    input_path: str = None,
    save_path: str = None,
    df: pd.DataFrame = None,
) -> pd.DataFrame:
    """Load preprocessed data, compute cohort retention heatmap data, save."""
    if df is None:
        path = input_path or DEFAULT_PREPROCESSED_PATH
        df = pd.read_csv(path)
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    df = assign_cohort_and_index(df)
    heatmap = retention_heatmap_data(df)
    save_path = save_path or DEFAULT_COHORT_OUTPUT_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    heatmap.to_csv(save_path)
    print(f"Cohort retention heatmap data saved to {save_path}")

    # Print key retention KPIs
    kpis = summarize_retention(heatmap)
    if kpis:
        print("Retention KPIs (avg across cohorts):")
        for key, val in kpis.items():
            print(f"  {key.replace('_', ' ').title()}: {val}%")

    return heatmap


if __name__ == "__main__":
    run_cohort_pipeline()
