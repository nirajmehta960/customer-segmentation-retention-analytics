"""
Plotting helpers for RFM, cohort, and segment visualizations.
Covers all PRD-required chart types (Section 2.4, 2.5).
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def set_style():
    """Set consistent style across all visualizations for portfolio consistency."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({"figure.facecolor": "white", "font.size": 11})


def save_fig(fig, path: str, dpi: int = 150):
    """Save figure; create parent dirs if needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


# ── Segment visualizations ──────────────────────────────────────────────────

def plot_segment_distribution(rfm: pd.DataFrame, segment_col: str = "segment", save_path: str = None):
    """Horizontal bar: customer count per segment."""
    set_style()
    counts = rfm[segment_col].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    counts.plot(kind="barh", ax=ax, color="steelblue")
    ax.set_title("Customer Count by Segment")
    ax.set_xlabel("Number of Customers")
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_revenue_by_segment(rfm: pd.DataFrame, segment_col: str = "segment", save_path: str = None):
    """Bar chart: total revenue by segment."""
    set_style()
    rev = rfm.groupby(segment_col)["monetary"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    rev.plot(kind="bar", ax=ax, color="teal", alpha=0.8)
    ax.set_title("Total Revenue by Segment")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Revenue (£)")
    plt.xticks(rotation=45, ha="right")
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_segment_scatter(rfm: pd.DataFrame, segment_col: str = "segment", save_path: str = None):
    """Scatter: Avg Frequency (x) vs Avg Monetary (y), bubble size = customer count.
    
    PRD Dashboard Page 2: 'Segment Scatter — Avg Frequency (x) vs Avg Monetary (y),
    bubble size = customer count.'
    """
    set_style()
    agg = rfm.groupby(segment_col).agg(
        avg_freq=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        count=("CustomerID", "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(
        agg["avg_freq"], agg["avg_monetary"],
        s=agg["count"] * 0.5, alpha=0.6, edgecolors="k", linewidths=0.5,
    )
    for _, row in agg.iterrows():
        ax.annotate(row[segment_col], (row["avg_freq"], row["avg_monetary"]),
                    fontsize=8, ha="center", va="bottom")
    ax.set_title("Segment Scatter: Frequency vs Monetary")
    ax.set_xlabel("Avg Frequency (orders)")
    ax.set_ylabel("Avg Monetary (£)")
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Retention visualizations ────────────────────────────────────────────────

def plot_retention_heatmap(heatmap_df: pd.DataFrame, save_path: str = None):
    """Seaborn heatmap for cohort retention (rows=cohort, columns=month index)."""
    set_style()
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(heatmap_df, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax, cbar_kws={"label": "Retention %"})
    ax.set_title("Cohort Retention (%)")
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first purchase month)")
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_cohort_retention_curves(heatmap_df: pd.DataFrame, top_n: int = 3, save_path: str = None):
    """Line chart: retention curves for the top N largest cohorts.
    
    PRD Dashboard Page 3: 'Retention Curves — Month-over-month retention for top 3 cohorts.'
    """
    set_style()
    # Find the largest cohorts by Month-0 value (100%)
    cohort_sizes = heatmap_df[0] if 0 in heatmap_df.columns else heatmap_df.iloc[:, 0]
    top_cohorts = cohort_sizes.dropna().nlargest(top_n).index

    fig, ax = plt.subplots(figsize=(12, 5))
    for cohort in top_cohorts:
        row = heatmap_df.loc[cohort].dropna()
        ax.plot(row.index, row.values, marker="o", markersize=4, label=str(cohort))
    ax.set_title(f"Retention Curves — Top {top_n} Cohorts")
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Retention (%)")
    ax.legend(title="Cohort")
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Revenue & geographic visualizations ─────────────────────────────────────

def plot_monthly_revenue(df: pd.DataFrame, date_col: str = "InvoiceDate", revenue_col: str = "Revenue", save_path: str = None):
    """Line chart: monthly total revenue."""
    set_style()
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    monthly = df.set_index(date_col)[revenue_col].resample("ME").sum()
    fig, ax = plt.subplots(figsize=(12, 5))
    monthly.plot(ax=ax)
    ax.set_title("Monthly Revenue")
    ax.set_ylabel("Revenue (£)")
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_revenue_by_country(df: pd.DataFrame, country_col: str = "Country", revenue_col: str = "Revenue", top_n: int = 10, save_path: str = None):
    """Bar chart: top N countries by revenue."""
    set_style()
    by_country = df.groupby(country_col)[revenue_col].sum().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    by_country.plot(kind="bar", ax=ax, color="coral", alpha=0.8)
    ax.set_title(f"Top {top_n} Countries by Revenue")
    ax.set_ylabel("Revenue (£)")
    plt.xticks(rotation=45, ha="right")
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_revenue_per_customer_by_country(df: pd.DataFrame, country_col: str = "Country", customer_col: str = "CustomerID", revenue_col: str = "Revenue", top_n: int = 10, save_path: str = None):
    """Bar chart: top N countries by revenue per customer (min 5 customers)."""
    set_style()
    agg = df.groupby(country_col).agg({revenue_col: "sum", customer_col: "nunique"})
    agg["RevenuePerCustomer"] = agg[revenue_col] / agg[customer_col]
    agg = agg[agg[customer_col] > 5]
    top_countries = agg.sort_values("RevenuePerCustomer", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(10, 5))
    top_countries["RevenuePerCustomer"].plot(kind="bar", ax=ax, color="mediumpurple", alpha=0.9)
    ax.set_title(f"Top {top_n} Countries by Revenue per Customer (min. 5 customers)")
    ax.set_ylabel("Revenue per Customer (£)")
    plt.xticks(rotation=45, ha="right")
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Product visualizations ──────────────────────────────────────────────────

def plot_top_products(df: pd.DataFrame, desc_col: str = "Description", metric_col: str = "Revenue", top_n: int = 10, save_path: str = None):
    """Bar chart: top N products by given metric (Revenue or Quantity)."""
    set_style()
    if "is_non_product" in df.columns:
        df_prod = df[~df["is_non_product"]]
    else:
        df_prod = df

    top_products = df_prod.groupby(desc_col)[metric_col].sum().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(10, 6))
    top_products.sort_values(ascending=True).plot(kind="barh", ax=ax, color="darkorange", alpha=0.8)
    ax.set_title(f"Top {top_n} Products by {metric_col}")
    ax.set_xlabel(f"Total {metric_col}")
    ax.set_ylabel("Product Description")
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── RFM distribution visualizations ────────────────────────────────────────

def plot_rfm_distributions(rfm: pd.DataFrame, save_path: str = None):
    """Histograms of Recency, Frequency, Monetary distributions."""
    set_style()
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, col, color in zip(axes, ["recency", "frequency", "monetary"], ["steelblue", "teal", "coral"]):
        rfm[col].hist(bins=50, ax=ax, color=color, alpha=0.8, edgecolor="white")
        ax.set_title(f"{col.title()} Distribution")
        ax.set_xlabel(col.title())
        ax.set_ylabel("Customers")
    fig.suptitle("RFM Distributions", fontsize=14, y=1.02)
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_order_frequency_distribution(rfm: pd.DataFrame, save_path: str = None):
    """Histogram: 1-order vs repeat breakdown.
    
    PRD Analysis 1: 'Order frequency distribution — What % are one-time vs. repeat.'
    """
    set_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    max_freq = min(rfm["frequency"].max(), 30)  # cap x-axis for readability
    rfm["frequency"].clip(upper=max_freq).hist(bins=max_freq, ax=ax, color="teal", alpha=0.8, edgecolor="white")
    one_time = (rfm["frequency"] == 1).sum()
    pct_one_time = one_time / len(rfm) * 100
    ax.set_title(f"Order Frequency Distribution ({pct_one_time:.1f}% one-time buyers)")
    ax.set_xlabel("Number of Orders")
    ax.set_ylabel("Customers")
    ax.axvline(x=1.5, color="red", linestyle="--", alpha=0.7, label=f"One-time: {one_time:,} ({pct_one_time:.1f}%)")
    ax.legend()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_pareto_curve(rfm: pd.DataFrame, save_path: str = None):
    """Revenue concentration: cumulative % of revenue vs % of customers.
    
    PRD Analysis 1: 'Revenue distribution — Median vs. mean revenue per customer; skewness.'
    Hypothesis H1: '~20% of customers generate ~60-80% of total revenue.'
    """
    set_style()
    sorted_rev = rfm["monetary"].sort_values(ascending=False).reset_index(drop=True)
    cum_pct = sorted_rev.cumsum() / sorted_rev.sum() * 100
    customer_pct = np.arange(1, len(cum_pct) + 1) / len(cum_pct) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(customer_pct, cum_pct, color="teal", linewidth=2)
    ax.axhline(y=80, color="red", linestyle="--", alpha=0.5, label="80% revenue")
    ax.axvline(x=20, color="red", linestyle="--", alpha=0.5, label="20% customers")

    # Find actual 20% contribution
    idx_20 = max(1, int(len(sorted_rev) * 0.2))
    rev_at_20 = cum_pct.iloc[idx_20 - 1]
    ax.annotate(f"Top 20% → {rev_at_20:.0f}% of revenue",
                xy=(20, rev_at_20), fontsize=10, fontweight="bold",
                xytext=(35, rev_at_20 - 10), arrowprops=dict(arrowstyle="->"))

    ax.set_title("Revenue Concentration (Pareto Curve)")
    ax.set_xlabel("% of Customers (ranked by revenue)")
    ax.set_ylabel("Cumulative % of Revenue")
    ax.legend()
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Clustering visualizations ──────────────────────────────────────────────

def plot_elbow_silhouette(elbow_df: pd.DataFrame, chosen_k: int = 5, save_path: str = None):
    """Dual-axis plot: Elbow (inertia) + Silhouette score vs K.
    
    PRD Analysis 3, Step 3: 'Determine optimal K — Elbow Method + Silhouette Score.'
    """
    set_style()
    fig, ax1 = plt.subplots(figsize=(10, 5))

    color1 = "steelblue"
    ax1.plot(elbow_df["k"], elbow_df["inertia"], "o-", color=color1, linewidth=2)
    ax1.set_xlabel("Number of Clusters (K)")
    ax1.set_ylabel("Inertia", color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = "coral"
    ax2.plot(elbow_df["k"], elbow_df["silhouette"], "s-", color=color2, linewidth=2)
    ax2.set_ylabel("Silhouette Score", color=color2)
    ax2.tick_params(axis="y", labelcolor=color2)

    ax1.axvline(x=chosen_k, color="gray", linestyle="--", alpha=0.7, label=f"Chosen K={chosen_k}")
    ax1.legend(loc="upper right")
    fig.suptitle("Elbow Method & Silhouette Score", fontsize=14)
    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


def plot_rfm_vs_kmeans_heatmap(rfm: pd.DataFrame, segment_col: str = "segment", cluster_col: str = "cluster", save_path: str = None):
    """Heatmap cross-tabulation of rule-based segments vs K-Means clusters.
    
    PRD Dashboard Page 4: 'RFM vs K-Means Comparison — Cross-tab/Heatmap.'
    """
    set_style()
    ct = pd.crosstab(rfm[segment_col], rfm[cluster_col])
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_title("RFM Segments vs K-Means Clusters")
    ax.set_xlabel("K-Means Cluster")
    ax.set_ylabel("RFM Segment")
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Temporal pattern visualizations ─────────────────────────────────────────

def plot_day_of_week_hour(df: pd.DataFrame, date_col: str = "InvoiceDate", save_path: str = None):
    """Bar charts: transactions by day of week and hour of day.
    
    PRD Analysis 1: 'Day-of-week / hour patterns — When customers buy (informs campaign timing).'
    """
    set_style()
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Day of week
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_counts = df[date_col].dt.dayofweek.value_counts().sort_index()
    axes[0].bar(day_counts.index, day_counts.values, color="steelblue", alpha=0.8)
    axes[0].set_xticks(range(7))
    axes[0].set_xticklabels(day_names)
    axes[0].set_title("Transactions by Day of Week")
    axes[0].set_ylabel("Number of Transactions")

    # Hour of day
    hour_counts = df[date_col].dt.hour.value_counts().sort_index()
    axes[1].bar(hour_counts.index, hour_counts.values, color="teal", alpha=0.8)
    axes[1].set_title("Transactions by Hour of Day")
    axes[1].set_xlabel("Hour")
    axes[1].set_ylabel("Number of Transactions")

    plt.tight_layout()
    if save_path:
        save_fig(fig, save_path)
    return fig


# ── Batch chart generation ──────────────────────────────────────────────────

def generate_all_eda_charts(preprocessed_df: pd.DataFrame, rfm_df: pd.DataFrame, save_dir: str = "images/eda_charts"):
    """Generate and save all exploratory data analysis charts.
    
    Called from notebooks (01_data_exploration, 03_rfm_analysis) to produce
    all EDA charts in a single call — matching the diabetes project pattern.
    
    Args:
        preprocessed_df: Cleaned transaction-level data (from data/preprocessed/).
        rfm_df: Customer-level RFM data (from data/featured/customer_rfm.csv).
        save_dir: Directory to save chart PNGs.
    """
    import os
    os.makedirs(save_dir, exist_ok=True)

    print("Generating EDA charts...")

    # Transaction-level charts
    plot_monthly_revenue(preprocessed_df, save_path=os.path.join(save_dir, "monthly_revenue.png"))
    print("  ✓ monthly_revenue.png")

    plot_revenue_by_country(preprocessed_df, save_path=os.path.join(save_dir, "revenue_by_country.png"))
    print("  ✓ revenue_by_country.png")

    plot_revenue_per_customer_by_country(preprocessed_df, save_path=os.path.join(save_dir, "revenue_per_customer_by_country.png"))
    print("  ✓ revenue_per_customer_by_country.png")

    plot_top_products(preprocessed_df, metric_col="Revenue", save_path=os.path.join(save_dir, "top_products_revenue.png"))
    print("  ✓ top_products_revenue.png")

    plot_top_products(preprocessed_df, metric_col="Quantity", save_path=os.path.join(save_dir, "top_products_quantity.png"))
    print("  ✓ top_products_quantity.png")

    plot_day_of_week_hour(preprocessed_df, save_path=os.path.join(save_dir, "day_hour_patterns.png"))
    print("  ✓ day_hour_patterns.png")

    # Customer-level RFM charts
    plot_rfm_distributions(rfm_df, save_path=os.path.join(save_dir, "rfm_distributions.png"))
    print("  ✓ rfm_distributions.png")

    plot_order_frequency_distribution(rfm_df, save_path=os.path.join(save_dir, "order_frequency_distribution.png"))
    print("  ✓ order_frequency_distribution.png")

    plot_segment_distribution(rfm_df, save_path=os.path.join(save_dir, "segment_distribution.png"))
    print("  ✓ segment_distribution.png")

    plot_revenue_by_segment(rfm_df, save_path=os.path.join(save_dir, "revenue_by_segment.png"))
    print("  ✓ revenue_by_segment.png")

    plot_segment_scatter(rfm_df, save_path=os.path.join(save_dir, "segment_scatter.png"))
    print("  ✓ segment_scatter.png")

    plot_pareto_curve(rfm_df, save_path=os.path.join(save_dir, "pareto_curve.png"))
    print("  ✓ pareto_curve.png")

    print(f"Done — 12 charts saved to {save_dir}/")
