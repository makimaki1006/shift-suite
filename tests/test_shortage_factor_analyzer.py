import pandas as pd

from shift_suite.tasks.shortage_factor_analyzer import ShortageFactorAnalyzer


def test_shortage_factor_analyzer_basic():
    long_df = pd.DataFrame(
        {
            "ds": pd.date_range("2024-06-01 09:00", periods=4, freq="30min").tolist()
            + pd.date_range("2024-06-02 09:00", periods=4, freq="30min").tolist(),
            "staff": ["A", "B", "A", "B", "A", "B", "A", "B"],
            "role": [
                "Nurse",
                "Nurse",
                "Care",
                "Care",
                "Nurse",
                "Nurse",
                "Care",
                "Care",
            ],
            "holiday_type": ["", "", "", "", "", "", "", ""],
            "parsed_slots_count": [1] * 8,
        }
    )
    heat_all_df = pd.DataFrame(
        {
            "need": [1, 1],
            "2024-06-01": [2, 1],
            "2024-06-02": [1, 2],
        },
        index=["09:00", "09:30"],
    )
    shortage_time_df = pd.DataFrame(
        {
            "2024-06-01": [0, 1],
            "2024-06-02": [1, 0],
        },
        index=["09:00", "09:30"],
    )
    leave_df = pd.DataFrame(
        {"date": ["2024-06-01", "2024-06-02"], "total_leave_days": [1, 0]}
    )
    leave_df["date"] = pd.to_datetime(leave_df["date"])
    analyzer = ShortageFactorAnalyzer()
    feats = analyzer.generate_features(
        long_df, heat_all_df, shortage_time_df, leave_df, set()
    )
    assert not feats.empty
    model, fi = analyzer.train_and_get_feature_importance(feats)
    assert not fi.empty
