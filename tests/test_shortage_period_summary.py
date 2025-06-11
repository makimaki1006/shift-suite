from pathlib import Path

import pandas as pd

from shift_suite.tasks.shortage import (
    shortage_and_brief,
    weekday_timeslot_summary,
    monthperiod_timeslot_summary,
)
from shift_suite.tasks.utils import gen_labels


def _create_heatmap(out_dir: Path) -> None:
    labels = gen_labels(30)[:1]
    df = pd.DataFrame(
        {
            "need": [1],
            "2024-06-01": [0],
            "2024-06-11": [2],
            "2024-06-21": [1],
        },
        index=labels,
    )
    df.to_parquet(out_dir / "heat_ALL.parquet")


def test_weekday_timeslot_summary(tmp_path: Path) -> None:
    _create_heatmap(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    df = weekday_timeslot_summary(tmp_path)
    assert {"weekday", "timeslot", "avg_count"}.issubset(df.columns)
    saturday_val = df.loc[df["weekday"] == "土曜日", "avg_count"].iloc[0]
    assert saturday_val == 1


def test_monthperiod_timeslot_summary(tmp_path: Path) -> None:
    _create_heatmap(tmp_path)
    shortage_and_brief(tmp_path, slot=30)
    df = monthperiod_timeslot_summary(tmp_path)
    assert {"month_period", "timeslot", "avg_count"}.issubset(df.columns)
    early_val = df.loc[df["month_period"] == "月初(1-10日)", "avg_count"].iloc[0]
    assert early_val == 1
