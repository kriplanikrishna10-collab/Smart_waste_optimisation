import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_generator import generate_bins


def test_generate_bins_returns_requested_count():
    bins = generate_bins(number_of_bins=50)
    assert len(bins) == 50


def test_bin_ids_are_unique():
    bins = generate_bins(number_of_bins=50)
    assert bins["bin_id"].is_unique


def test_fill_percentages_are_valid():
    bins = generate_bins(number_of_bins=50)
    assert bins["fill_percentage"].between(0, 100).all()


def test_collection_flag_matches_fill_level():
    bins = generate_bins(number_of_bins=50)
    assert (bins["needs_collection"] == (bins["fill_percentage"] >= 80)).all()


def test_invalid_bin_count_is_rejected():
    with pytest.raises(ValueError):
        generate_bins(number_of_bins=0)