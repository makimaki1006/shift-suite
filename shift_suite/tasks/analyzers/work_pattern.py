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

        work_df['month'] = pd.to_datetime(work_df['ds']).dt.to_period('M').astype(str)

        counts = (
            work_df.groupby(['staff', 'month', 'code'])
            .size()
            .unstack(fill_value=0)
        )
        counts = counts.reset_index()
        counts.columns = [str(c) for c in counts.columns]

        ratio_cols = []
        code_cols = [c for c in counts.columns if c not in {'staff', 'month'}]
        if code_cols:
            totals = counts[code_cols].sum(axis=1)
            for col in code_cols:
                ratio_col = f"{col}_ratio"
                counts[ratio_col] = counts[col] / totals.replace(0, pd.NA)
                ratio_cols.append(ratio_col)

        return counts
