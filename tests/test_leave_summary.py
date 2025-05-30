import pandas as pd
from shift_suite.tasks.leave_analyzer import summarize_leave_by_day_count, LEAVE_TYPE_REQUESTED


def test_summary_contains_new_columns():
    df = pd.DataFrame([
        {"date": "2024-06-01", "staff": "A", "leave_type": LEAVE_TYPE_REQUESTED, "leave_day_flag": 1},
        {"date": "2024-06-01", "staff": "B", "leave_type": LEAVE_TYPE_REQUESTED, "leave_day_flag": 1},
        {"date": "2024-06-02", "staff": "A", "leave_type": LEAVE_TYPE_REQUESTED, "leave_day_flag": 1},
    ])
    df["date"] = pd.to_datetime(df["date"])

    summary = summarize_leave_by_day_count(df, period="dayofweek")

    expected_cols = {
        "period_unit",
        "leave_type",
        "total_leave_days",
        "num_days_in_period_unit",
        "avg_leave_days_per_day",
    }
    assert expected_cols == set(summary.columns)
    sat = summary.loc[summary["period_unit"] == "土曜日"].iloc[0]
    assert sat["total_leave_days"] == 2
    assert sat["num_days_in_period_unit"] == 1
    assert sat["avg_leave_days_per_day"] == 2
