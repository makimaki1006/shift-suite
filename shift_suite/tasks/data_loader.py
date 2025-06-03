from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd

log = logging.getLogger(__name__)


class ShiftDataLoader:
    """Simple loader for shift CSV data."""

    def __init__(self, csv_path: Path | str):
        self.csv_path = Path(csv_path)

    def load(self) -> pd.DataFrame:
        """Load the CSV file into a DataFrame."""
        if not self.csv_path.exists():
            log.error("CSV file not found: %s", self.csv_path)
            raise FileNotFoundError(self.csv_path)

        try:
            df = pd.read_csv(self.csv_path, parse_dates=["ds"])
        except Exception as e:  # pragma: no cover - network/file errors
            log.error("Failed to read CSV %s: %s", self.csv_path, e)
            raise

        if "ds" not in df.columns:
            log.warning("Column 'ds' missing in %s", self.csv_path)

        if df.empty:
            log.warning("CSV contains no rows: %s", self.csv_path)

        return df
