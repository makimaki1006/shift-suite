import pandas as pd
from shift_suite.tasks.leave_analyzer import (
    summarize_leave_by_day_count,
    leave_ratio_by_period_and_weekday,
    LEAVE_TYPE_REQUESTED,
    LEAVE_TYPE_PAID,
)


def test_summary_contains_new_columns():
    df = pd.DataFrame(
        [
            {
                "date": "2024-06-01",
                "staff": "A",
                "leave_type": LEAVE_TYPE_REQUESTED,
                "leave_day_flag": 1,
            },
            {
                "date": "2024-06-01",
                "staff": "B",
                "leave_type": LEAVE_TYPE_REQUESTED,
                "leave_day_flag": 1,
            },
            {
                "date": "2024-06-02",
                "staff": "A",
                "leave_type": LEAVE_TYPE_REQUESTED,
                "leave_day_flag": 1,
            },
        ]
    )
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


def test_leave_ratio_by_period_and_weekday():
    df = pd.DataFrame(
        [
            {
                "date": "2024-06-01",
                "leave_type": LEAVE_TYPE_REQUESTED,
                "total_leave_days": 1,
            },
            {
                "date": "2024-06-11",
                "leave_type": LEAVE_TYPE_REQUESTED,
                "total_leave_days": 1,
            },
            {
                "date": "2024-06-02",
                "leave_type": LEAVE_TYPE_PAID,
                "total_leave_days": 1,
            },
            {
                "date": "2024-06-21",
                "leave_type": LEAVE_TYPE_PAID,
                "total_leave_days": 1,
            },
        ]
    )
    df["date"] = pd.to_datetime(df["date"])
    result = leave_ratio_by_period_and_weekday(df)
    early_sat = result[
        (result["month_period"] == "月初(1-10日)")
        & (result["dayofweek"] == "土曜日")
        & (result["leave_type"] == LEAVE_TYPE_REQUESTED)
    ]["leave_ratio"].iloc[0]
    mid_tue = result[
        (result["month_period"] == "月中(11-20日)")
        & (result["dayofweek"] == "火曜日")
        & (result["leave_type"] == LEAVE_TYPE_REQUESTED)
    ]["leave_ratio"].iloc[0]
    assert early_sat == 0.5
    assert mid_tue == 0.5
