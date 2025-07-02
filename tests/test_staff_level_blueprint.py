import pandas as pd
from shift_suite.tasks.blueprint_analyzer import create_scored_blueprint, create_staff_level_blueprint

def test_create_staff_level_blueprint():
    long_df = pd.DataFrame({
        "ds": pd.to_datetime(["2024-06-01 08:00", "2024-06-01 09:00", "2024-06-02 08:00", "2024-06-02 09:00"]),
        "staff": ["A", "B", "A", "B"],
        "parsed_slots_count": [1, 1, 1, 1],
        "code": ["M", "M", "M", "M"],
    })
    scored = create_scored_blueprint(long_df)
    staff_scores = create_staff_level_blueprint(long_df, scored)
    assert set(staff_scores.index) == {"A", "B"}
    assert "fairness_score" in staff_scores.columns
