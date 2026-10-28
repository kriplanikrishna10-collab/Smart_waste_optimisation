"""Generate reproducible synthetic waste-bin data."""

import numpy as np
import pandas as pd


def generate_bins(number_of_bins: int = 50, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic waste bins with locations and fill levels."""
    if number_of_bins < 1:
        raise ValueError("number_of_bins must be at least 1")

    rng = np.random.default_rng(seed)

    bins = pd.DataFrame(
        {
            "bin_id": [f"BIN-{i:03d}" for i in range(1, number_of_bins + 1)],
            "x_coordinate_km": rng.uniform(0, 10, number_of_bins).round(2),
            "y_coordinate_km": rng.uniform(0, 10, number_of_bins).round(2),
            "capacity_kg": rng.choice([100, 150, 200, 250], number_of_bins),
            "fill_percentage": rng.integers(0, 101, number_of_bins),
        }
    )

    bins["waste_kg"] = (
        bins["capacity_kg"] * bins["fill_percentage"] / 100
    ).round(2)

    bins["needs_collection"] = bins["fill_percentage"] >= 80

    return bins


if __name__ == "__main__":
    generated_bins = generate_bins()
    print(generated_bins.head(10).to_string(index=False))
    print(f"\nTotal bins generated: {len(generated_bins)}")
    print(f"Bins requiring collection: {generated_bins['needs_collection'].sum()}")