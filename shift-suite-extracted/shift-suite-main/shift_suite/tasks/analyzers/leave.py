from __future__ import annotations

import pandas as pd

from .. import leave_analyzer


class LeaveAnalyzer:
    """Wrapper around leave_analyzer module."""

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        daily = leave_analyzer.get_daily_leave_counts(df)
        return leave_analyzer.summarize_leave_by_day_count(daily, period="date")
