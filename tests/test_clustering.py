import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.python_pipeline.clustering import (
    prepare_rfm_for_clustering,
    find_optimal_k,
    fit_kmeans,
    profile_clusters,
)


def _make_small_rfm_df():
    """Synthetic RFM data for 10 customers with varying values."""
    return pd.DataFrame(
        {
            "CustomerID": range(1, 11),
            "recency": [5, 10, 20, 40, 80, 120, 200, 250, 300, 365],
            "frequency": [20, 15, 10, 8, 6, 4, 3, 2, 2, 1],
            "monetary": [10000, 8000, 5000, 3000, 2000, 1500, 800, 600, 400, 200],
        }
    )


def test_prepare_rfm_for_clustering_shapes():
    rfm = _make_small_rfm_df()
    X_scaled, scaler, feat_names = prepare_rfm_for_clustering(rfm)

    assert X_scaled.shape == (10, 3)
    assert len(feat_names) == 3
    # Standardized data should have ~zero mean for each column
    means = X_scaled.mean(axis=0)
    assert np.all(np.abs(means) < 1e-6)


def test_find_optimal_k_returns_expected_range():
    rfm = _make_small_rfm_df()
    X_scaled, _, _ = prepare_rfm_for_clustering(rfm)
    elbow_df = find_optimal_k(X_scaled, k_range=range(2, 5))

    assert list(elbow_df["k"]) == [2, 3, 4]
    assert elbow_df["inertia"].gt(0).all()
    assert elbow_df["silhouette"].between(-1, 1).all()


def test_fit_kmeans_and_profile_clusters():
    rfm = _make_small_rfm_df()
    X_scaled, _, _ = prepare_rfm_for_clustering(rfm)
    labels, model = fit_kmeans(X_scaled, n_clusters=3)

    assert len(labels) == len(rfm)
    assert set(labels) == {0, 1, 2}

    rfm_with_cluster = rfm.copy()
    rfm_with_cluster["cluster"] = labels
    profile = profile_clusters(rfm_with_cluster)

    # Profiles should have 3 clusters and aggregate back to total customers
    assert profile["cluster"].nunique() == 3
    assert profile["count"].sum() == len(rfm)

