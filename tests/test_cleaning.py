"""
Unit tests for Online Retail data cleaning.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

# Project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_cleaning import (
    remove_cancellations,
    remove_negative_quantity,
    remove_non_positive_unitprice,
    remove_null_customer_id,
    cast_customer_id,
    add_revenue,
    add_year_month,
)


@pytest.fixture
def sample_raw():
    """Minimal raw-like dataframe."""
    return pd.DataFrame({
        "InvoiceNo": [12345, "C12346", 12347, "A563185"],
        "Quantity": [2, 1, -1, 1],
        "UnitPrice": [10.0, 5.0, 3.0, 0.0],
        "CustomerID": [1.0, 2.0, np.nan, np.nan],
        "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02", "2011-01-03", "2011-01-04"]),
        "Description": ["Item A", "Item B", "Item C", "Adjust bad debt"],
    })


def test_remove_cancellations(sample_raw):
    out = remove_cancellations(sample_raw)
    assert len(out) == 2
    invoice_upper = out["InvoiceNo"].astype(str).str.upper()
    assert not invoice_upper.str.startswith("C").any()
    assert not invoice_upper.str.startswith("A").any()


def test_remove_negative_quantity(sample_raw):
    out = remove_negative_quantity(sample_raw)
    assert (out["Quantity"] > 0).all()
    assert len(out) == 3


def test_remove_non_positive_unitprice(sample_raw):
    out = remove_non_positive_unitprice(sample_raw)
    assert (out["UnitPrice"] > 0).all()
    assert len(out) == 3


def test_remove_null_customer_id(sample_raw):
    out = remove_null_customer_id(sample_raw)
    assert out["CustomerID"].notna().all()
    assert len(out) == 2


def test_cast_customer_id(sample_raw):
    out = remove_null_customer_id(sample_raw)
    out = cast_customer_id(out)
    assert out["CustomerID"].dtype in (np.int64, np.int32, int)
    assert (out["CustomerID"] == [1, 2]).all()


def test_add_revenue(sample_raw):
    out = add_revenue(sample_raw)
    assert "Revenue" in out.columns
    assert out.loc[0, "Revenue"] == 20.0


def test_add_year_month(sample_raw):
    out = add_year_month(sample_raw)
    assert "YearMonth" in out.columns
    assert out["YearMonth"].iloc[0] == "2011-01"
