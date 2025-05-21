from __future__ import annotations

import pandas as pd

class RestTimeAnalyzer:
    """Analyze rest hours between consecutive working days for each staff."""

    def analyze(self, df: pd.DataFrame, slot_minutes: int = 30) -> pd.DataFrame:
        """Return average rest hours per month for each staff."""

        if df.empty or "ds" not in df.columns:
            return pd.DataFrame(columns=["staff", "month", "avg_rest_hours"])

        if "parsed_slots_count" not in df.columns:
            return pd.DataFrame(columns=["staff", "month", "avg_rest_hours"])

        work_df = df[df["parsed_slots_count"] > 0].copy()
        if work_df.empty:
            return pd.DataFrame(columns=["staff", "month", "avg_rest_hours"])

        work_df["date"] = pd.to_datetime(work_df["ds"]).dt.date
        daily = (
            work_df.groupby(["staff", "date"])["ds"]
            .agg(["min", "max"])
            .rename(columns={"min": "start", "max": "end"})
            .reset_index()
        )
        daily["end"] = daily["end"] + pd.to_timedelta(slot_minutes, unit="m")
        daily = daily.sort_values(["staff", "start"])
        daily["rest_hours"] = (
            daily.groupby("staff")["start"].shift(-1) - daily["end"]
        ).dt.total_seconds() / 3600.0

        daily["month"] = pd.to_datetime(daily["date"]).dt.to_period("M").astype(str)
        monthly = (
            daily.groupby(["staff", "month"])["rest_hours"].mean().reset_index()
        )
        monthly = monthly.rename(columns={"rest_hours": "avg_rest_hours"})
        return monthly[["staff", "month", "avg_rest_hours"]]
