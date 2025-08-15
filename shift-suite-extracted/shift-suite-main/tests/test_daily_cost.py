import pandas as pd

from shift_suite.tasks.daily_cost import calculate_daily_cost


def test_calculate_daily_cost_by_staff():
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2024-01-01 09:00", periods=6, freq="30min"),
            "staff": ["A"] * 3 + ["B"] * 3,
            "role": ["N"] * 3 + ["C"] * 3,
            "employment": ["FT"] * 6,
            "parsed_slots_count": [1] * 6,
        }
    )
    wages = {"A": 1000, "B": 2000}
    res = calculate_daily_cost(df, wages, by="staff", slot_minutes=30)
    assert res.shape[0] == 1
    assert res.loc[0, "cost"] == 4500


def test_calculate_daily_cost_by_role():
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2024-01-01 09:00", periods=4, freq="30min"),
            "staff": ["A", "A", "B", "B"],
            "role": ["Nurse", "Nurse", "Care", "Care"],
            "employment": ["FT", "FT", "PT", "PT"],
            "parsed_slots_count": [1] * 4,
        }
    )
    wages = {"Nurse": 1500, "Care": 1200}
    res = calculate_daily_cost(df, wages, by="role", slot_minutes=30)
    assert res.loc[0, "cost"] == (1500 * 0.5 * 2) + (1200 * 0.5 * 2)
    assert res["cost"].sum() == 2700
