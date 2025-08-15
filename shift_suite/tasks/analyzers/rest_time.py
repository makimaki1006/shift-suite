from __future__ import annotations

import pandas as pd


class RestTimeAnalyzer:
    """Analyze rest hours between working days and summarize results monthly.

    The :meth:`analyze` method returns a ``pandas.DataFrame`` aggregated by
    month.  The returned frame contains the ``staff`` identifier, a ``month``
    column in ``YYYY-MM`` format, and aggregated metrics such as
    ``rest_hours`` for that period.
    """

    def analyze(self, df: pd.DataFrame, slot_minutes: int = 30) -> pd.DataFrame:
        if df.empty or "ds" not in df.columns:
            return pd.DataFrame(columns=["staff", "date", "rest_hours"])

        if "parsed_slots_count" not in df.columns:
            return pd.DataFrame(columns=["staff", "date", "rest_hours"])

        work_df = df[df["parsed_slots_count"] > 0].copy()
        if work_df.empty:
            return pd.DataFrame(columns=["staff", "date", "rest_hours"])

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
        return daily[["staff", "date", "rest_hours"]]

    def monthly(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily rest time DataFrame to monthly averages."""
        if daily_df.empty or not {"staff", "date", "rest_hours"}.issubset(
            daily_df.columns
        ):
            return pd.DataFrame()

        df = daily_df.copy()
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        monthly = df.groupby(["staff", "month"])["rest_hours"].mean().reset_index()
        monthly["month"] = monthly["month"].astype(str)
        return monthly

    def consecutive_leave_frequency(
        self, daily_df: pd.DataFrame, threshold_hours: float = 48.0
    ) -> pd.Series:
        """Return frequency of rest periods above ``threshold_hours`` per staff."""
        if daily_df.empty or not {"staff", "rest_hours"}.issubset(daily_df.columns):
            return pd.Series(dtype=float)

        df = daily_df.copy()
        df["long_break"] = df["rest_hours"] >= threshold_hours
        return df.groupby("staff")["long_break"].mean()
