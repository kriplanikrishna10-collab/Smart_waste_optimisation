"""SQLite storage for synthetic waste-bin data."""

import sqlite3
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "waste_collection.db"


def initialize_database(db_path: Path = DATABASE_PATH) -> None:
    """Create the waste_bins table if it does not already exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS waste_bins (
                bin_id TEXT PRIMARY KEY,
                x_coordinate_km REAL NOT NULL,
                y_coordinate_km REAL NOT NULL,
                capacity_kg INTEGER NOT NULL,
                fill_percentage INTEGER NOT NULL,
                waste_kg REAL NOT NULL,
                needs_collection INTEGER NOT NULL
            )
            """
        )


def save_bins(bins: pd.DataFrame, db_path: Path = DATABASE_PATH) -> None:
    """Save generated bins to SQLite, replacing previous simulation data."""
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        bins.to_sql("waste_bins", connection, if_exists="replace", index=False)


def load_bins(db_path: Path = DATABASE_PATH) -> pd.DataFrame:
    """Load all stored bins from SQLite."""
    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        return pd.read_sql_query(
            "SELECT * FROM waste_bins ORDER BY bin_id",
            connection,
        )


if __name__ == "__main__":
    from data_generator import generate_bins

    bins = generate_bins()
    save_bins(bins)
    loaded_bins = load_bins()

    print(f"Database: {DATABASE_PATH}")
    print(f"Rows saved: {len(loaded_bins)}")
    print(f"Bins needing collection: {int(loaded_bins['needs_collection'].sum())}")
    print("\nFirst five stored bins:")
    print(loaded_bins.head().to_string(index=False))
    