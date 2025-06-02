from __future__ import annotations

import pandas as pd


class AttendanceBehaviorAnalyzer:
    """Simple attendance rate analysis based on working days."""

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate attendance rate for each staff.

        Parameters
        ----------
        df : pd.DataFrame
            Input data containing ``ds``, ``staff`` and ``parsed_slots_count`` columns.

        Returns
        -------
        pd.DataFrame
            DataFrame with ``staff`` and ``attendance_rate`` columns.
        """
        if df.empty or "ds" not in df.columns or "parsed_slots_count" not in df.columns:
            return pd.DataFrame(columns=["staff", "attendance_rate"])
        df["date"] = pd.to_datetime(df["ds"]).dt.date
        daily = df.groupby(["staff", "date"])["parsed_slots_count"].sum().reset_index()
        daily["worked"] = daily["parsed_slots_count"] > 0
        summary = (
            daily.groupby("staff")["worked"].mean().reset_index(name="attendance_rate")
        )
        return summary
