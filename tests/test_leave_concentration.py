import pandas as pd
from shift_suite.tasks.leave_analyzer import (
    analyze_leave_concentration,
    analyze_both_leave_concentration,
    summarize_leave_by_day_count,
    LEAVE_TYPE_REQUESTED,
    LEAVE_TYPE_PAID,
)


def make_sample_daily_leave_df():
    data = [
        {
            "date": "2024-06-01",
            "staff": "Alice",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-01",
            "staff": "Bob",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-02",
            "staff": "Alice",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-03",
            "staff": "Bob",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-03",
            "staff": "Charlie",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-04",
            "staff": "Alice",
            "leave_type": "有給",
            "leave_day_flag": 1,
        },
    ]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def make_sample_both_leave_df():
    data = [
        {
            "date": "2024-06-01",
            "staff": "A",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-01",
            "staff": "B",
            "leave_type": LEAVE_TYPE_PAID,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-02",
            "staff": "A",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-02",
            "staff": "B",
            "leave_type": LEAVE_TYPE_REQUESTED,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-02",
            "staff": "C",
            "leave_type": LEAVE_TYPE_PAID,
            "leave_day_flag": 1,
        },
        {
            "date": "2024-06-03",
            "staff": "D",
            "leave_type": LEAVE_TYPE_PAID,
            "leave_day_flag": 1,
        },
    ]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_analyze_leave_concentration_flags_and_names():
    daily_df = make_sample_daily_leave_df()
    summary = summarize_leave_by_day_count(daily_df, period="date")

    result = analyze_leave_concentration(
        summary,
        concentration_threshold=2,
        daily_leave_df=daily_df,
    )

    assert list(result["date"]) == list(
        pd.to_datetime(["2024-06-01", "2024-06-02", "2024-06-03"])
    )
    assert result["is_concentrated"].tolist() == [True, False, True]
    assert result.loc[result["date"] == pd.Timestamp("2024-06-01"), "staff_names"].iloc[
        0
    ] == ["Alice", "Bob"]
    assert result.loc[result["date"] == pd.Timestamp("2024-06-03"), "staff_names"].iloc[
        0
    ] == ["Bob", "Charlie"]


def test_per_date_breakdown_helper_matches_groupby():
    daily_df = make_sample_daily_leave_df()
    summary = summarize_leave_by_day_count(daily_df, period="date")
    summary_req = summary[summary["leave_type"] == LEAVE_TYPE_REQUESTED].reset_index(
        drop=True
    )

    helper_df = (
        daily_df[daily_df["leave_type"] == LEAVE_TYPE_REQUESTED]
        .groupby(["date", "leave_type"])["staff"]
        .nunique()
        .reset_index(name="total_leave_days")
        .sort_values("date")
        .reset_index(drop=True)
    )

    expected = helper_df.assign(
        num_days_in_period_unit=1,
        avg_leave_days_per_day=helper_df["total_leave_days"] / 1,
    )
    expected = expected[summary_req.columns]

    pd.testing.assert_frame_equal(summary_req, expected)


def test_analyze_both_leave_concentration():
    df = make_sample_both_leave_df()
    summary = summarize_leave_by_day_count(df, period="date")
    result = analyze_both_leave_concentration(summary, concentration_threshold=1)

    assert list(result["is_concentrated"]) == [True, True, False]
    assert result["requested_count"].tolist() == [1, 2, 0]
    assert result["paid_count"].tolist() == [1, 1, 1]
