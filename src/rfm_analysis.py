"""
RFM (Recency, Frequency, Monetary) analysis and rule-based segmentation.
Reference: PRD segment definitions (Champions, Loyal, At Risk, etc.).
"""

import os
import pandas as pd
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PREPROCESSED_PATH = os.path.join(_PROJECT_ROOT, "data", "preprocessed", "online_retail_preprocessed.csv")
DEFAULT_FEATURED_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "customer_rfm.csv")
DEFAULT_PROFILE_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "segment_profiles.csv")


def compute_rfm(
    df: pd.DataFrame,
    reference_date: pd.Timestamp = None,
    date_col: str = "InvoiceDate",
    customer_col: str = "CustomerID",
    invoice_col: str = "InvoiceNo",
    revenue_col: str = "Revenue",
) -> pd.DataFrame:
    """
    Compute Recency, Frequency, Monetary per customer.
    reference_date: 'today' for Recency; default = max(InvoiceDate) + 1 day.
    """
    if reference_date is None:
        reference_date = df[date_col].max() + pd.Timedelta(days=1)

    agg = df.groupby(customer_col).agg(
        last_purchase=(date_col, "max"),
        frequency=(invoice_col, "nunique"),
        monetary=(revenue_col, "sum"),
    ).reset_index()
    agg["recency"] = (reference_date - agg["last_purchase"]).dt.days
    return agg


def score_quartiles(
    rfm: pd.DataFrame,
    recency_col: str = "recency",
    frequency_col: str = "frequency",
    monetary_col: str = "monetary",
) -> pd.DataFrame:
    """
    Assign quartile-based scores 1-4.
    Recency: lower is better -> reverse scored (low recency_days = high score 4).
    Frequency and Monetary: higher is better.
    """
    rfm = rfm.copy()

    # Recency: pd.qcut bins lowest values into first bin; labels [4,3,2,1] gives
    # the lowest (most recent) a score of 4. duplicates="drop" handles tied boundaries.
    rfm["r_score"] = pd.qcut(rfm[recency_col], q=4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)

    # Frequency: 34.4% of customers have frequency=1, so more than an entire quartile
    # shares the same value. pd.qcut on raw values would fail with a ValueError.
    # Using .rank(method="first") breaks ties by row position, guaranteeing 4 equal bins.
    rfm["f_score"] = pd.qcut(rfm[frequency_col].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)

    rfm["m_score"] = pd.qcut(rfm[monetary_col], q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)
    return rfm


def assign_segment(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Rule-based segment assignment per PRD.
    Champions R>=4 F>=4 M>=4; Loyal R>=3 F>=3; New R>=4 F<=2;
    Potential Loyalists R>=3 M>=3; At Risk R=2 F>=2; Can't Lose R=1 F>=2;
    Lost R<=2 F<=2 M<=2; Need Attention = rest.

    Note: Rules are evaluated in if/elif order via np.where. Loyal Customers (R>=3, F>=3)
    is checked before Potential Loyalists (R>=3, M>=3), which means Potential Loyalists
    only captures customers with R>=3, M>=3, and F<3. This is intentional — high-frequency
    customers belong in Loyal; Potential Loyalists are recent, high-spend, low-frequency
    customers who could be nurtured into Loyal/Champions.
    """
    rfm = rfm.copy()
    r, f, m = rfm["r_score"], rfm["f_score"], rfm["m_score"]

    segment = np.where((r >= 4) & (f >= 4) & (m >= 4), "Champions",
             np.where((r >= 3) & (f >= 3), "Loyal Customers",
             np.where((r >= 4) & (f <= 2), "New Customers",
             np.where((r >= 3) & (m >= 3), "Potential Loyalists",
             np.where((r == 2) & (f >= 2), "At Risk",
             np.where((r == 1) & (f >= 2), "Can't Lose Them",
             np.where((r <= 2) & (f <= 2) & (m <= 2), "Lost / Hibernating",
                      "Need Attention")))))))
    rfm["segment"] = segment
    rfm["rfm_segment"] = rfm["r_score"].astype(str) + "-" + rfm["f_score"].astype(str) + "-" + rfm["m_score"].astype(str)
    return rfm


def profile_segments(rfm: pd.DataFrame) -> pd.DataFrame:
    """Generate segment profiles: count, %, avg R/F/M, total revenue, revenue share.
    
    PRD Step 7: 'Profile each segment — Calculate avg Recency, Frequency, Monetary,
    customer count, revenue share.'
    """
    profile = rfm.groupby("segment").agg(
        customer_count=("CustomerID", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    ).reset_index()
    profile["pct_customers"] = (profile["customer_count"] / len(rfm) * 100).round(1)
    profile["pct_revenue"] = (profile["total_revenue"] / profile["total_revenue"].sum() * 100).round(1)
    profile = profile.round({"avg_recency": 1, "avg_frequency": 1, "avg_monetary": 2, "total_revenue": 2})
    return profile.sort_values("total_revenue", ascending=False)


def run_rfm_pipeline(
    input_path: str = None,
    save_path: str = None,
    profile_path: str = None,
    df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Load preprocessed data (or use provided df), compute RFM, score, assign segments,
    profile, and save both RFM data and segment profiles.
    """
    if df is None:
        path = input_path or DEFAULT_PREPROCESSED_PATH
        df = pd.read_csv(path)
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    rfm = compute_rfm(df)
    rfm = score_quartiles(rfm)
    rfm = assign_segment(rfm)

    save_path = save_path or DEFAULT_FEATURED_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    rfm.to_csv(save_path, index=False)
    print(f"RFM segments saved to {save_path}")
    print(rfm["segment"].value_counts().to_string())

    # Save segment profiles
    profile = profile_segments(rfm)
    profile_path = profile_path or DEFAULT_PROFILE_PATH
    profile.to_csv(profile_path, index=False)
    print(f"\nSegment profiles saved to {profile_path}")
    print(profile.to_string(index=False))
    return rfm


if __name__ == "__main__":
    run_rfm_pipeline()
