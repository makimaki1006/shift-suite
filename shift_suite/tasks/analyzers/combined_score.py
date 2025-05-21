from __future__ import annotations

import pandas as pd

class CombinedScoreCalculator:
    """Calculate a simple combined score from other analyses."""

    def calculate(
        self,
        rest_df: pd.DataFrame,
        work_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
    ) -> pd.DataFrame:
        if attendance_df.empty:
            return pd.DataFrame()

        avg_rest = (
            rest_df.groupby('staff')['rest_hours'].mean().reset_index()
            if not rest_df.empty else pd.DataFrame(columns=['staff', 'rest_hours'])
        )

        if not work_df.empty:
            tmp = work_df.set_index('staff')
            totals = tmp.sum(axis=1)
            dominant = tmp.max(axis=1) / totals.replace(0, pd.NA)
            pattern_df = dominant.reset_index(name='dominant_ratio')
        else:
            pattern_df = pd.DataFrame(columns=['staff', 'dominant_ratio'])

        df = attendance_df.merge(avg_rest, on='staff', how='left').merge(pattern_df, on='staff', how='left')
        df['rest_score'] = df['rest_hours'].fillna(0) / 24
        df['pattern_score'] = 1 - df['dominant_ratio'].fillna(0)
        df['final_score'] = 0.5 * df['attendance_rate'].fillna(0) + 0.25 * df['rest_score'] + 0.25 * df['pattern_score']
        return df[['staff', 'final_score']]
