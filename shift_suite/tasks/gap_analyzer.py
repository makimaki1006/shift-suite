from __future__ import annotations

import pandas as pd
from shift_suite.tasks.constants import SLOT_HOURS


def analyze_standards_gap(
    heat_all_df: pd.DataFrame, manual_need_values: dict[str, int]
) -> dict[str, pd.DataFrame]:
    """Compare statistical need with standard need."""
    # 1. Need_実態 (statistical) - here simply use existing 'need' column
    if "need" in heat_all_df.columns:
        need_stat = heat_all_df["need"].copy()
    else:
        need_stat = pd.Series(0, index=heat_all_df.index)

    # 2. Need_基準 constructed from manual values
    need_standard = pd.DataFrame(index=heat_all_df.index)
    for role, val in manual_need_values.items():
        need_standard[role] = val
    if not need_standard.empty:
        need_standard["need"] = need_standard.sum(axis=1)
    else:
        need_standard["need"] = 0

    gap_heatmap = need_stat - need_standard["need"]

    gap_summary = pd.DataFrame(
        {
            "role": list(manual_need_values.keys()),
            "total_gap_hours": [gap_heatmap.sum() * SLOT_HOURS] * len(manual_need_values),
        }
    )

    return {
        "gap_heatmap": gap_heatmap.to_frame("gap"),
        "gap_summary": gap_summary,
    }
