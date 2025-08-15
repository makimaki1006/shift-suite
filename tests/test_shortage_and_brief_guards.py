import pathlib
import sys
import pandas as pd
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from pathlib import Path
from shift_suite.tasks.shortage import shortage_and_brief
from shift_suite.tasks.utils import gen_labels, write_meta
import pytest


def test_shortage_and_brief_caps_and_guards(tmp_path: Path) -> None:
    """Synthetic run covering column alignment and period caps.

    * Need vs staff have misaligned date columns (extra day in need data).
    * More than 90 days are supplied to trigger the period limiter.
    * Each day initially has 6h shortage which is capped below 5h.
    """
    slot = 30
    labels = gen_labels(slot)[:12]  # 12 slots -> 6h potential shortage
    days = 95
    dates = [pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(days)]
    missing_day = dates[50]

    # heat_ALL.parquet with one day missing (misalignment)
    heat_data = {"need": [1] * len(labels)}
    for d in dates:
        if d != missing_day:
            heat_data[d.strftime("%Y-%m-%d")] = [0] * len(labels)
    pd.DataFrame(heat_data, index=labels).to_parquet(tmp_path / "heat_ALL.parquet")

    # Need data includes all days including the missing one
    need_data = {d.strftime("%Y-%m-%d"): [1] * len(labels) for d in dates}
    pd.DataFrame(need_data, index=labels).to_parquet(
        tmp_path / "need_per_date_slot.parquet"
    )

    # Minimal metadata
    write_meta(
        tmp_path / "heatmap.meta.json",
        slot=slot,
        dates=[d.strftime("%Y-%m-%d") for d in dates],
        summary_columns=["need", "upper", "staff", "lack", "excess"],
        estimated_holidays=[],
        dow_need_pattern=[{"time": t, **{str(i): 1 for i in range(7)}} for t in labels],
    )

    shortage_and_brief(tmp_path, slot=slot)
    shortage_df = pd.read_parquet(tmp_path / "shortage_time.parquet")

    # Period limiter: only first 90 days should remain
    assert shortage_df.shape[1] == 90
    # Misaligned day should be dropped
    assert missing_day.strftime("%Y-%m-%d") not in shortage_df.columns

    slot_hours = slot / 60
    total_hours = shortage_df.sum().sum() * slot_hours
    avg_hours_per_day = total_hours / shortage_df.shape[1]
    # Baseline expectation: about 0.67h per day after all guards
    assert avg_hours_per_day == pytest.approx(0.67, abs=0.01)
    assert avg_hours_per_day <= 5
