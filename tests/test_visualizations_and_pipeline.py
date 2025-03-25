import os
import sys
from datetime import datetime, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.python_pipeline import visualizations as viz
import matplotlib

# Use a non-interactive backend suitable for headless test environments
matplotlib.use("Agg")
from src.python_pipeline.run_pipeline import run_pipeline


def _make_small_preprocessed_df():
    """Tiny cleaned-like dataset for visualization smoke tests."""
    base = datetime(2011, 1, 1)
    rows = [
        dict(
            InvoiceNo="10001",
            StockCode="P1",
            Description="Prod A",
            Quantity=10,
            UnitPrice=5.0,
            CustomerID=1,
            Country="United Kingdom",
            InvoiceDate=base,
            Revenue=50.0,
            YearMonth="2011-01",
            is_non_product=False,
        ),
        dict(
            InvoiceNo="10002",
            StockCode="P2",
            Description="Prod B",
            Quantity=3,
            UnitPrice=20.0,
            CustomerID=2,
            Country="France",
            InvoiceDate=base + timedelta(days=10),
            Revenue=60.0,
            YearMonth="2011-01",
            is_non_product=False,
        ),
    ]
    return pd.DataFrame(rows)


def _make_small_rfm_df_for_viz():
    return pd.DataFrame(
        {
            "CustomerID": [1, 2],
            "recency": [5, 30],
            "frequency": [3, 1],
            "monetary": [500.0, 100.0],
            "segment": ["Champions", "Lost / Hibernating"],
        }
    )


def test_visualization_functions_smoke(tmp_path):
    """Smoke-test a subset of visualization helpers: they should run and save files."""
    pre = _make_small_preprocessed_df()
    rfm = _make_small_rfm_df_for_viz()

    save_dir = tmp_path / "eda_charts"
    save_dir.mkdir()

    # Just ensure no exceptions and that files are created
    viz.plot_monthly_revenue(pre, save_path=str(save_dir / "monthly_revenue.png"))
    viz.plot_revenue_by_country(pre, save_path=str(save_dir / "revenue_by_country.png"))
    viz.plot_segment_distribution(rfm, save_path=str(save_dir / "segment_distribution.png"))

    for name in ["monthly_revenue.png", "revenue_by_country.png", "segment_distribution.png"]:
        assert (save_dir / name).exists()


def test_run_pipeline_on_real_data(tmp_path, monkeypatch):
    """
    Lightweight integration test:
    - Point pipeline at the real raw Excel if it exists locally.
    - Override default output directory to a temp location to avoid clobbering project files.
    If the raw Excel is missing, test is skipped.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(project_root, "data", "raw", "Online Retail.xlsx")
    if not os.path.exists(raw_path):
        # Allow running tests without the dataset
        return

    # Patch DEFAULT paths to temp dir for this test run
    featured_dir = tmp_path / "featured"
    preprocessed_dir = tmp_path / "preprocessed"
    featured_dir.mkdir()
    preprocessed_dir.mkdir()

    from src.python_pipeline import data_cleaning as dc
    from src.python_pipeline import rfm_analysis as rfm_mod
    from src.python_pipeline import cohort_analysis as cohort_mod
    from src.python_pipeline import clustering as clust_mod

    dc.DEFAULT_RAW_PATH = raw_path
    dc.DEFAULT_PREPROCESSED_PATH = str(preprocessed_dir / "online_retail_preprocessed.csv")
    rfm_mod.DEFAULT_PREPROCESSED_PATH = dc.DEFAULT_PREPROCESSED_PATH
    rfm_mod.DEFAULT_FEATURED_PATH = str(featured_dir / "customer_rfm.csv")
    rfm_mod.DEFAULT_PROFILE_PATH = str(featured_dir / "segment_profiles.csv")
    cohort_mod.DEFAULT_PREPROCESSED_PATH = dc.DEFAULT_PREPROCESSED_PATH
    cohort_mod.DEFAULT_COHORT_OUTPUT_PATH = str(featured_dir / "cohort_retention.csv")
    clust_mod.DEFAULT_RFM_PATH = rfm_mod.DEFAULT_FEATURED_PATH
    clust_mod.DEFAULT_CLUSTER_OUTPUT_PATH = str(featured_dir / "customer_rfm_clusters.csv")
    clust_mod.DEFAULT_ELBOW_OUTPUT_PATH = str(featured_dir / "elbow_silhouette.csv")

    # Run pipeline; should complete without raising
    run_pipeline(
        raw_path=raw_path,
        preprocessed_path=dc.DEFAULT_PREPROCESSED_PATH,
        featured_path=rfm_mod.DEFAULT_FEATURED_PATH,
        n_clusters=3,
    )

    # Check that key outputs were written to temp dir
    for fname in [
        "online_retail_preprocessed.csv",
        "customer_rfm.csv",
        "segment_profiles.csv",
        "cohort_retention.csv",
        "customer_rfm_clusters.csv",
        "elbow_silhouette.csv",
    ]:
        assert (featured_dir / fname).exists() or (preprocessed_dir / fname).exists()

