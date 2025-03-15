import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rfm_analysis import (
    compute_rfm,
    score_quartiles,
    assign_segment,
    profile_segments,
)


def _make_small_clean_df():
    """Synthetic cleaned-like data for 3 customers."""
    today = datetime(2011, 12, 10)
    rows = [
        # Customer 1: very recent, frequent, high spend (Champion-ish)
        dict(
            CustomerID=1,
            InvoiceNo="10001",
            InvoiceDate=today - timedelta(days=1),
            Revenue=1000.0,
        ),
        dict(
            CustomerID=1,
            InvoiceNo="10002",
            InvoiceDate=today - timedelta(days=5),
            Revenue=500.0,
        ),
        # Customer 2: older, moderate frequency and spend
        dict(
            CustomerID=2,
            InvoiceNo="10003",
            InvoiceDate=today - timedelta(days=40),
            Revenue=200.0,
        ),
        dict(
            CustomerID=2,
            InvoiceNo="10004",
            InvoiceDate=today - timedelta(days=50),
            Revenue=150.0,
        ),
        # Customer 3: oldest, low frequency and spend
        dict(
            CustomerID=3,
            InvoiceNo="10005",
            InvoiceDate=today - timedelta(days=200),
            Revenue=50.0,
        ),
    ]
    return pd.DataFrame(rows)


def test_compute_rfm_basic():
    df = _make_small_clean_df()
    rfm = compute_rfm(df, reference_date=df["InvoiceDate"].max() + pd.Timedelta(days=1))

    assert set(rfm.columns) >= {"CustomerID", "last_purchase", "frequency", "monetary", "recency"}
    # 3 customers
    assert len(rfm) == 3
    # frequency is number of unique invoices
    assert rfm.set_index("CustomerID").loc[1, "frequency"] == 2
    # recency is days since last purchase
    cust3 = rfm.set_index("CustomerID").loc[3]
    assert cust3["recency"] > 150


def test_score_quartiles_shapes_and_ranges():
    df = _make_small_clean_df()
    rfm = compute_rfm(df)
    scored = score_quartiles(rfm)

    for col in ["r_score", "f_score", "m_score"]:
        assert col in scored.columns
        assert scored[col].between(1, 4).all()


def test_assign_segment_creates_valid_labels():
    df = _make_small_clean_df()
    rfm = compute_rfm(df)
    rfm = score_quartiles(rfm)
    seg = assign_segment(rfm)

    assert "segment" in seg.columns
    assert "rfm_segment" in seg.columns
    # Every customer has a non-empty segment label
    assert seg["segment"].notna().all()
    assert (seg["segment"].str.len() > 0).all()


def test_profile_segments_totals_match():
    df = _make_small_clean_df()
    rfm = compute_rfm(df)
    rfm = score_quartiles(rfm)
    rfm = assign_segment(rfm)

    profiles = profile_segments(rfm)

    # Sum of customer_count should equal number of rows in rfm
    assert profiles["customer_count"].sum() == len(rfm)
    # pct_customers should be close to 100 (allow small rounding drift)
    assert abs(profiles["pct_customers"].sum() - 100.0) < 0.2

