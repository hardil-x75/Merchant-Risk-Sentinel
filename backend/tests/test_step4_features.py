"""Automated tests for Step 4 features (simulation stream, threshold analysis grid, model comparison)."""


def test_simulation_stream_endpoint(client):
    """Verify simulation stream returns transaction sequence for live monitor."""
    response = client.get("/api/v1/risk/simulation-stream?mode=NORMAL&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if len(data) > 0:
        item = data[0]
        assert "transaction_id" in item
        assert "risk_score" in item
        assert "decision" in item


def test_threshold_analysis_grid_endpoint(client):
    """Verify threshold analysis grid returns validation set candidate cutoffs."""
    response = client.get("/api/v1/risk/threshold-analysis")
    assert response.status_code == 200
    data = response.json()
    assert "selected_threshold" in data
    assert "grid_results" in data
    assert len(data["grid_results"]) > 0
    first = data["grid_results"][0]
    assert "threshold" in first
    assert "precision" in first
    assert "recall" in first
    assert "financial_loss_inr" in first


def test_model_comparison_endpoint(client):
    """Verify model comparison returns side-by-side metrics on held-out test set."""
    response = client.get("/api/v1/risk/model-comparison")
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_scope"] == "HELD_OUT_TEST_SET"
    assert "comparison" in data
    assert len(data["comparison"]) == 2
    rf = next(m for m in data["comparison"] if "Random Forest" in m["model_name"])
    lr = next(m for m in data["comparison"] if "Logistic Regression" in m["model_name"])
    assert rf["f1_score"] > lr["f1_score"]
    assert rf["precision"] > lr["precision"]
