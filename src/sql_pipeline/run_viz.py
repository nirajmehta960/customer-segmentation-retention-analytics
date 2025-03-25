"""
Run the SQL-based visualization pipeline.
This script queries the SQLite 'Mart' views created by the ETL pipeline
and generates charts to prove the data is consumption-ready.
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "retail.sqlite"
IMAGE_DIR = PROJECT_ROOT / "images" / "sql_marts"

def set_style():
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({"figure.facecolor": "white", "font.size": 11})

def fetch_data(query: str, db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(str(db_path)) as conn:
        return pd.read_sql_query(query, conn)

def plot_segment_summary(db_path: Path, save_dir: Path):
    """Plot customer count and revenue share from mart_segment_summary."""
    df = fetch_data("SELECT * FROM mart_segment_summary;", db_path)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Bar chart for customer count
    sns.barplot(data=df, x="segment", y="customer_count", ax=ax1, color="steelblue", alpha=0.7)
    ax1.set_ylabel("Number of Customers", color="steelblue", fontweight="bold")
    ax1.set_xlabel("Segment", fontweight="bold")
    ax1.tick_params(axis='y', labelcolor="steelblue")
    plt.xticks(rotation=45, ha="right")
    
    # Line chart for revenue percentage on second axis
    ax2 = ax1.twinx()
    sns.lineplot(data=df, x="segment", y="pct_revenue", ax=ax2, color="crimson", marker="o", linewidth=2)
    ax2.set_ylabel("% of Total Revenue", color="crimson", fontweight="bold")
    ax2.tick_params(axis='y', labelcolor="crimson")
    ax2.set_ylim(0, max(df["pct_revenue"]) * 1.2)
    
    plt.title("SQL Mart: Segment Performance (Count vs. Revenue Share)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(save_dir / "sql_segment_performance.png", dpi=150)
    plt.close()
    print("  ✓ sql_segment_performance.png created")

def plot_top_countries(db_path: Path, save_dir: Path):
    """Plot top countries by revenue from mart_revenue_by_country."""
    df = fetch_data("SELECT * FROM mart_revenue_by_country LIMIT 10;", db_path)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="revenue", y="country", palette="viridis")
    plt.title("SQL Mart: Top 10 Countries by Revenue", fontsize=14, fontweight="bold")
    plt.xlabel("Total Revenue (£)", fontweight="bold")
    plt.ylabel("Country", fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_dir / "sql_top_countries.png", dpi=150)
    plt.close()
    print("  ✓ sql_top_countries.png created")

def plot_retention_heatmap(db_path: Path, save_dir: Path):
    """Plot retention heatmap using the cohort_index logic from mart_cohort_retention_input."""
    query = """
    SELECT 
        cohort_month, 
        cohort_index, 
        customers_active * 100.0 / FIRST_VALUE(customers_active) OVER (PARTITION BY cohort_month ORDER BY cohort_index) as retention_pct
    FROM mart_cohort_retention_input;
    """
    df = fetch_data(query, db_path)
    
    # Pivot for heatmap
    pivot_df = df.pivot(index="cohort_month", columns="cohort_index", values="retention_pct")
    
    plt.figure(figsize=(14, 8))
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': 'Retention %'})
    plt.title("SQL Mart: Cohort Retention (%)", fontsize=14, fontweight="bold")
    plt.xlabel("Months Since First Purchase (Cohort Index)", fontweight="bold")
    plt.ylabel("Cohort Month", fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_dir / "sql_cohort_heatmap.png", dpi=150)
    plt.close()
    print("  ✓ sql_cohort_heatmap.png created")

def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}. Run 'python -m src.run_sql_etl' first.")
        return

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    set_style()
    
    print("Generating visualizations from SQL Mart views...")
    
    # 1. Segment Analysis
    plot_segment_summary(DB_PATH, IMAGE_DIR)
    
    # 2. Country Analysis
    plot_top_countries(DB_PATH, IMAGE_DIR)
    
    # 3. Cohort Analysis (using the new cohort_index improvement)
    plot_retention_heatmap(DB_PATH, IMAGE_DIR)
    
    # 4. Print KPI Printout
    kpis = fetch_data("SELECT * FROM mart_kpis;", DB_PATH).iloc[0]
    print("\n--- SQL MART KPI SUMMARY ---")
    print(f"Total Revenue:   £{kpis['total_revenue']:,.2f}")
    print(f"Unique Customers: {kpis['unique_customers']:,}")
    print(f"Unique Invoices:  {kpis['unique_invoices']:,}")
    print(f"Rev / Customer:  £{kpis['revenue_per_customer']:,.2f}")
    print("----------------------------")
    print(f"\nAll SQL visualizations saved to: {IMAGE_DIR}")

if __name__ == "__main__":
    main()
