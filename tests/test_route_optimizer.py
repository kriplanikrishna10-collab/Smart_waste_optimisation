import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from route_optimizer import (
    baseline_route,
    optimized_route,
    prepare_collection_bins,
)


def sample_bins():
    return pd.DataFrame(
        {
            "bin_id": ["BIN-001", "BIN-002", "BIN-003"],
            "x_coordinate_km": [1.0, 8.0, 5.0],
            "y_coordinate_km": [1.0, 8.0, 6.0],
            "capacity_kg": [100, 100, 100],
            "fill_percentage": [90, 85, 40],
            "waste_kg": [90.0, 85.0, 40.0],
            "needs_collection": [True, True, False],
        }
    )


def test_prepare_collection_bins_filters_correctly():
    bins = prepare_collection_bins(sample_bins())
    assert bins["bin_id"].tolist() == ["BIN-001", "BIN-002"]


def test_baseline_route_includes_required_bins():
    bins = prepare_collection_bins(sample_bins())
    result = baseline_route(bins)
    assert result["bin_ids"] == ["BIN-001", "BIN-002"]
    assert result["distance_km"] > 0


def test_optimizer_returns_feasible_route():
    bins = prepare_collection_bins(sample_bins())
    result = optimized_route(bins, vehicle_capacity_kg=500)
    assert result["status"] == "Success"
    assert set(result["bin_ids"]) == {"BIN-001", "BIN-002"}
    assert result["distance_km"] > 0


def test_optimizer_reports_capacity_exceeded():
    bins = prepare_collection_bins(sample_bins())
    result = optimized_route(bins, vehicle_capacity_kg=100)
    assert result["distance_km"] is None
    assert "capacity exceeded" in result["status"]


def test_optimizer_handles_no_collection():
    bins = sample_bins().iloc[0:0]
    result = optimized_route(bins)
    assert result["distance_km"] == 0.0
    assert result["bin_ids"] == []


def test_optimizer_rejects_nonpositive_capacity():
    bins = prepare_collection_bins(sample_bins())
    with pytest.raises(ValueError):
        optimized_route(bins, vehicle_capacity_kg=0)