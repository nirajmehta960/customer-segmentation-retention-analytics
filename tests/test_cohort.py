import os
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cohort_analysis import (
    assign_cohort_and_index,
    retention_heatmap_data,
    summarize_retention,
)


def _make_small_cohort_df():
    """Two customers with simple month-separated purchases."""
    rows = [
        # Customer 1: buys in Jan and Feb
        dict(
            CustomerID=1,
            InvoiceDate=datetime(2011, 1, 15),
        ),
        dict(
            CustomerID=1,
            InvoiceDate=datetime(2011, 2, 10),
        ),
        # Customer 2: buys only in Feb
        dict(
            CustomerID=2,
            InvoiceDate=datetime(2011, 2, 5),
        ),
    ]
    return pd.DataFrame(rows)


def test_assign_cohort_and_index_adds_columns():
    df = _make_small_cohort_df()
    out = assign_cohort_and_index(df)

    assert {"cohort", "cohort_index", "first_purchase"}.issubset(out.columns)
    # Cohort 2011-01 and 2011-02 should both appear
    assert set(out["cohort"]) == {"2011-01", "2011-02"}


def test_retention_heatmap_and_summary():
    df = _make_small_cohort_df()
    heatmap = retention_heatmap_data(df)

    # We should have one row per cohort
    assert set(heatmap.index) == {"2011-01", "2011-02"}
    # Month-0 should always be 100%
    assert (heatmap[0] == 100.0).all()

    summary = summarize_retention(heatmap)
    # Month-1 retention should exist (two-month span)
    assert "month_1_retention" in summary
    assert 0.0 <= summary["month_1_retention"] <= 100.0

