import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from road_routing import generate_road_based_bins


def test_generate_road_based_bins_returns_requested_count():
    bins = generate_road_based_bins(number_of_bins=5, seed=42)
    assert len(bins) == 5


def test_road_based_bin_ids_are_unique():
    bins = generate_road_based_bins(number_of_bins=5, seed=42)
    assert bins["bin_id"].is_unique


def test_road_based_bins_have_valid_coordinates():
    bins = generate_road_based_bins(number_of_bins=5, seed=42)
    assert bins["latitude"].between(-90, 90).all()
    assert bins["longitude"].between(-180, 180).all()


def test_road_based_bins_have_road_node_ids():
    bins = generate_road_based_bins(number_of_bins=5, seed=42)
    assert bins["road_node"].notna().all()


def test_invalid_road_bin_count_is_rejected():
    with pytest.raises(ValueError):
        generate_road_based_bins(number_of_bins=0)
