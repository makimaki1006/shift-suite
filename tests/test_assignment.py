import pandas as pd
import pytest

from shift_suite.tasks.assignment import generate_optimal_schedule


def test_generate_optimal_schedule_basic():
    pytest.importorskip("ortools")
    roster_df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3),
            "required_personnel": [1, 1, 1],
        }
    )
    staff_df = pd.DataFrame(
        {"name": ["Alice", "Bob"], "wage": [100, 100]}, index=[1, 2]
    )
    leave_df = pd.DataFrame({"staff_id": [1], "date": ["2024-01-02"]})

    config = {
        "time_limit_phase1": 5,
        "time_limit_phase2": 5,
        "max_consecutive_work_days": 2,
        "window_for_off_days": 3,
    }

    schedule = generate_optimal_schedule(roster_df, staff_df, leave_df, config)
    assert not schedule.empty
    assert set(schedule.columns) == {"date", "staff_id", "name"}
    # Ensure leave day is respected
    day2 = pd.to_datetime("2024-01-02").date()
    assert schedule[schedule["date"] == day2]["staff_id"].tolist() == [2]
