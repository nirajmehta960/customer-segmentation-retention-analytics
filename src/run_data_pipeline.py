"""
Run the full data pipeline: cleaning -> RFM -> cohort -> clustering.
Uses default paths under data/raw, data/preprocessed, data/featured.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.data_cleaning import run_cleaning_pipeline, DEFAULT_PREPROCESSED_PATH
from src.rfm_analysis import run_rfm_pipeline, DEFAULT_FEATURED_PATH
from src.cohort_analysis import run_cohort_pipeline
from src.clustering import run_clustering_pipeline


def run_pipeline(
    raw_path: str = None,
    preprocessed_path: str = None,
    featured_path: str = None,
    n_clusters: int = 5,
):
    """
    Execute: cleaning -> preprocessed; RFM -> customer_rfm.csv + segment_profiles.csv;
    cohort retention -> cohort_retention.csv; K-Means -> customer_rfm_clusters.csv + elbow_silhouette.csv.
    """
    summary = {}

    # Phase 1: Cleaning
    try:
        print("=" * 60)
        print("PHASE 1: Data Cleaning")
        print("=" * 60)
        df_cleaned = run_cleaning_pipeline(data_path=raw_path, save_path=preprocessed_path)
        summary["cleaned_rows"] = len(df_cleaned)
        summary["unique_customers"] = df_cleaned["CustomerID"].nunique()
        summary["unique_invoices"] = df_cleaned["InvoiceNo"].nunique()
        print()
    except Exception as e:
        print(f"\nFAILED at cleaning: {e}")
        return

    # Phase 2: RFM Segmentation
    try:
        print("=" * 60)
        print("PHASE 2: RFM Segmentation")
        print("=" * 60)
        rfm = run_rfm_pipeline(input_path=preprocessed_path)
        summary["n_segments"] = rfm["segment"].nunique()
        print()
    except Exception as e:
        print(f"\nFAILED at RFM: {e}")
        return

    # Phase 3: Cohort Retention Analysis
    try:
        print("=" * 60)
        print("PHASE 3: Cohort Retention Analysis")
        print("=" * 60)
        heatmap = run_cohort_pipeline(input_path=preprocessed_path)
        summary["n_cohorts"] = len(heatmap)
        print()
    except Exception as e:
        print(f"\nFAILED at cohort analysis: {e}")
        return

    # Phase 4: K-Means Clustering
    try:
        print("=" * 60)
        print("PHASE 4: K-Means Clustering")
        print("=" * 60)
        rfm_clusters = run_clustering_pipeline(n_clusters=n_clusters)
        summary["n_clusters"] = n_clusters
        print()
    except Exception as e:
        print(f"\nFAILED at clustering: {e}")
        return

    # Pipeline Summary
    print("=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Cleaned data:  {summary.get('cleaned_rows', '?'):,} rows, {summary.get('unique_customers', '?'):,} customers, {summary.get('unique_invoices', '?'):,} invoices")
    print(f"  Segments:      {summary.get('n_segments', '?')} distinct segments assigned")
    print(f"  Cohorts:       {summary.get('n_cohorts', '?')} monthly cohorts tracked")
    print(f"  Clusters:      K={summary.get('n_clusters', '?')}")
    print("=" * 60)
    print("Data pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
