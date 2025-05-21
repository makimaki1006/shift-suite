from __future__ import annotations

import pandas as pd

class WorkPatternAnalyzer:
    """Analyse frequency of shift codes per staff."""

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or 'code' not in df.columns:
            return pd.DataFrame()
        work_df = df[df.get('parsed_slots_count', 0) > 0].copy()
        if work_df.empty:
            return pd.DataFrame()
        counts = work_df.groupby(['staff', 'code']).size().unstack(fill_value=0)
        counts = counts.reset_index()
        counts.columns = [str(c) for c in counts.columns]
        return counts
