"""
K-Means clustering on RFM features to validate rule-based segments.
Log-transform, StandardScaler, elbow/silhouette for K, then fit and profile.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RFM_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "customer_rfm.csv")
DEFAULT_CLUSTER_OUTPUT_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "customer_rfm_clusters.csv")
DEFAULT_ELBOW_OUTPUT_PATH = os.path.join(_PROJECT_ROOT, "data", "featured", "elbow_silhouette.csv")


def prepare_rfm_for_clustering(
    rfm: pd.DataFrame,
    recency_col: str = "recency",
    frequency_col: str = "frequency",
    monetary_col: str = "monetary",
    cap_percentile: float = 99,
) -> tuple:
    """Log-transform (log1p) and scale RFM; return (X_scaled, scaler, feature_names).
    
    Caps monetary at the given percentile before transformation to prevent extreme
    outliers (e.g., £168K single-customer revenue) from distorting cluster centroids.
    K-Means is sensitive to outliers; capping at 99th percentile is standard practice.
    """
    rfm = rfm.copy()
    X = rfm[[recency_col, frequency_col, monetary_col]].copy()

    # Cap monetary at the specified percentile to limit outlier influence
    if cap_percentile and cap_percentile < 100:
        monetary_cap = X[monetary_col].quantile(cap_percentile / 100)
        n_capped = (X[monetary_col] > monetary_cap).sum()
        if n_capped > 0:
            print(f"  Capped {n_capped} customers' monetary at 99th percentile (£{monetary_cap:,.0f}) for clustering")
            X[monetary_col] = X[monetary_col].clip(upper=monetary_cap)

    X = np.log1p(X)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler, [recency_col, frequency_col, monetary_col]


def find_optimal_k(X: np.ndarray, k_range: range = range(2, 11), random_state: int = 42) -> pd.DataFrame:
    """Run Elbow Method and Silhouette analysis to determine optimal K.
    
    PRD Section 2.4 Analysis 3, Step 3: 'Determine optimal K — Elbow Method
    (inertia vs. K) + Silhouette Score (cohesion vs. separation).'
    
    Returns a DataFrame with columns: k, inertia, silhouette.
    """
    results = {"k": [], "inertia": [], "silhouette": []}
    print("  Elbow / Silhouette analysis:")
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X)
        sil = silhouette_score(X, labels)
        results["k"].append(k)
        results["inertia"].append(km.inertia_)
        results["silhouette"].append(round(sil, 4))
        print(f"    K={k}: Inertia={km.inertia_:,.0f}, Silhouette={sil:.3f}")
    return pd.DataFrame(results)


def fit_kmeans(X: np.ndarray, n_clusters: int = 5, random_state: int = 42) -> tuple:
    """Fit K-Means and return (cluster labels, fitted KMeans model)."""
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = km.fit_predict(X)
    return labels, km


def profile_clusters(rfm: pd.DataFrame, cluster_col: str = "cluster") -> pd.DataFrame:
    """Profile each cluster with mean RFM values, size, and percentage.
    
    PRD Step 5: 'Calculate cluster centroids and map to business labels.'
    """
    profile = rfm.groupby(cluster_col).agg(
        count=("CustomerID", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    ).reset_index()
    profile["pct"] = (profile["count"] / len(rfm) * 100).round(1)
    profile = profile.round({"avg_recency": 1, "avg_frequency": 1, "avg_monetary": 2, "total_revenue": 2})
    return profile.sort_values("avg_monetary", ascending=False)


def run_clustering_pipeline(
    input_path: str = None,
    save_path: str = None,
    elbow_path: str = None,
    rfm_df: pd.DataFrame = None,
    n_clusters: int = 5,
) -> pd.DataFrame:
    """
    Load RFM data (or use provided), run elbow/silhouette analysis, scale,
    fit K-Means, profile clusters, add cluster label to RFM, save.
    """
    if rfm_df is None:
        path = input_path or DEFAULT_RFM_PATH
        rfm_df = pd.read_csv(path)

    X_scaled, scaler, feat_names = prepare_rfm_for_clustering(rfm_df)

    # Elbow / Silhouette analysis — justifies choice of K
    elbow_results = find_optimal_k(X_scaled)
    elbow_path = elbow_path or DEFAULT_ELBOW_OUTPUT_PATH
    os.makedirs(os.path.dirname(elbow_path), exist_ok=True)
    elbow_results.to_csv(elbow_path, index=False)
    print(f"  Elbow/Silhouette results saved to {elbow_path}")

    # Best silhouette
    best_row = elbow_results.loc[elbow_results["silhouette"].idxmax()]
    print(f"  Best silhouette: K={int(best_row['k'])} (score={best_row['silhouette']:.3f})")
    print(f"  Using K={n_clusters} (as specified)\n")

    # Fit with chosen K
    labels, km_model = fit_kmeans(X_scaled, n_clusters=n_clusters)
    rfm_df = rfm_df.copy()
    rfm_df["cluster"] = labels

    # Cluster profiling
    cluster_profile = profile_clusters(rfm_df)
    print("Cluster profiles:")
    print(cluster_profile.to_string(index=False))

    save_path = save_path or DEFAULT_CLUSTER_OUTPUT_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    rfm_df.to_csv(save_path, index=False)
    print(f"\nK-Means (K={n_clusters}) labels saved to {save_path}")

    if "segment" in rfm_df.columns:
        print("RFM vs K-Means cross-tab:")
        print(pd.crosstab(rfm_df["segment"], rfm_df["cluster"], margins=True).to_string())
    return rfm_df


if __name__ == "__main__":
    run_clustering_pipeline()
