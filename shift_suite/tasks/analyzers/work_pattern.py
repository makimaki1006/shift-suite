from __future__ import annotations

import pandas as pd

class WorkPatternAnalyzer:
    """Analyse frequency of shift codes per staff."""

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "code" not in df.columns:
            return pd.DataFrame()

        work_df = df[df.get("parsed_slots_count", 0) > 0].copy()
        if work_df.empty:
            return pd.DataFrame()

        # raw counts of each shift code per staff
        counts = work_df.groupby(["staff", "code"]).size().unstack(fill_value=0)

        # calculate per-staff totals and ratios for each code
        totals = counts.sum(axis=1)
        ratios = counts.div(totals.replace(0, pd.NA), axis=0).fillna(0)
        ratios = ratios.add_suffix("_ratio")

        # combine counts and ratio columns
        df_out = pd.concat([counts, ratios], axis=1).reset_index()
        df_out.columns = [str(c) for c in df_out.columns]
        return df_out

    def analyze_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyse shift patterns per staff for each month."""
        if df.empty or "code" not in df.columns or "ds" not in df.columns:
            return pd.DataFrame()

        work_df = df[df.get("parsed_slots_count", 0) > 0].copy()
        if work_df.empty:
            return pd.DataFrame()

        work_df["month"] = pd.to_datetime(work_df["ds"]).dt.to_period("M")
        counts = work_df.groupby(["staff", "month", "code"]).size().unstack(fill_value=0)

        totals = counts.sum(axis=1)
        ratios = counts.div(totals.replace(0, pd.NA), axis=0).fillna(0)
        ratios = ratios.add_suffix("_ratio")

        df_out = pd.concat([counts, ratios], axis=1).reset_index()
        df_out.columns = [str(c) for c in df_out.columns]
        df_out["month"] = df_out["month"].astype(str)
        return df_out
