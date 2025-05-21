from __future__ import annotations

import pandas as pd

class LowStaffLoadAnalyzer:
    """Analyze how often staff work on low-staffed days."""

    def analyze(self, df: pd.DataFrame, threshold: int | float = 0.25) -> pd.DataFrame:
        """Return count and ratio of working on low-staff days per staff.

        Parameters
        ----------
        df : pd.DataFrame
            Long format DataFrame containing at least ``ds``, ``staff`` and
            ``parsed_slots_count`` columns.
        threshold : int | float
            Numeric threshold for defining low-staff days.  If between 0 and 1,
            it is treated as a quantile of daily staff counts (e.g. ``0.25`` for
            the 25th percentile).
        """
        if df.empty or not {"ds", "staff"}.issubset(df.columns):
            return pd.DataFrame(columns=["staff", "low_staff_days", "ratio"])

        if "parsed_slots_count" not in df.columns:
            return pd.DataFrame(columns=["staff", "low_staff_days", "ratio"])

        work_df = df[df["parsed_slots_count"] > 0].copy()
        if work_df.empty:
            return pd.DataFrame(columns=["staff", "low_staff_days", "ratio"])

        work_df["date"] = pd.to_datetime(work_df["ds"]).dt.normalize()

        daily_staff = work_df.groupby("date")["staff"].nunique()

        if isinstance(threshold, (int, float)) and 0 < float(threshold) < 1:
            thr_val = daily_staff.quantile(float(threshold))
        else:
            thr_val = float(threshold)

        low_dates = daily_staff[daily_staff < thr_val].index
        low_work_df = work_df[work_df["date"].isin(low_dates)]

        low_counts = low_work_df.groupby("staff")["date"].nunique()
        total_days = work_df.groupby("staff")["date"].nunique()

        result = pd.DataFrame({"staff": total_days.index})
        result["low_staff_days"] = low_counts.reindex(result["staff"], fill_value=0).astype(int)
        result["ratio"] = (result["low_staff_days"] / total_days.values).fillna(0)
        return result.sort_values("ratio", ascending=False).reset_index(drop=True)
