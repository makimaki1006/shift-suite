from __future__ import annotations

from pathlib import Path

import pandas as pd


class ShiftDataLoader:
    """Simple loader for shift CSV data."""

    def __init__(self, csv_path: Path | str):
        self.csv_path = Path(csv_path)

    def load(self) -> pd.DataFrame:
        """Load the CSV file into a DataFrame."""
        return pd.read_csv(self.csv_path, parse_dates=["ds"])
