from __future__ import annotations

import pandas as pd

class AttendanceBehaviorAnalyzer:
    """Simple attendance rate analysis based on working days."""

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or 'ds' not in df.columns:
            return pd.DataFrame(columns=['staff', 'attendance_rate'])
        df['date'] = pd.to_datetime(df['ds']).dt.date
        daily = df.groupby(['staff', 'date'])['parsed_slots_count'].sum().reset_index()
        daily['worked'] = daily['parsed_slots_count'] > 0
        summary = daily.groupby('staff')['worked'].mean().reset_index(name='attendance_rate')
        return summary
