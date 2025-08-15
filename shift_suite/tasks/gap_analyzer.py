from __future__ import annotations

import pandas as pd
from shift_suite.tasks.utils import validate_and_convert_slot_minutes, safe_slot_calculation
import logging

log = logging.getLogger(__name__)

def analyze_standards_gap(
    heat_all_df: pd.DataFrame, 
    manual_need_values: dict[str, int],
    *,
    slot_minutes: int = 30
) -> dict[str, pd.DataFrame]:
    """
    Compare statistical need with standard need.
    
    Parameters
    ----------
    heat_all_df : pd.DataFrame
        Heat map data
    manual_need_values : dict[str, int]
        Manual need values by role
    slot_minutes : int, default 30
        Slot interval in minutes
        
    Returns
    -------
    dict[str, pd.DataFrame]
        Gap analysis results
    """
    slot_hours = validate_and_convert_slot_minutes(slot_minutes, "analyze_standards_gap")
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
            "total_gap_hours": [safe_slot_calculation(
                gap_heatmap, slot_minutes, "sum", "analyze_standards_gap"
            )] * len(manual_need_values),
        }
    )

    return {
        "gap_heatmap": gap_heatmap.to_frame("gap"),
        "gap_summary": gap_summary,
    }
