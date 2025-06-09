import pandas as pd
from shift_suite import app


def test_calc_ratio_from_heatmap():
    df = pd.DataFrame(
        {"need": [2, 2], "upper": [3, 3], "2024-06-01": [1, 2]},
        index=["09:00", "10:00"],
    )
    ratio = app.calc_ratio_from_heatmap(df)
    assert ratio.shape == (2, 1)
    assert ratio.iloc[0, 0] == 0.5
    assert ratio.iloc[1, 0] == 0


def test_calc_opt_score_from_heatmap():
    df = pd.DataFrame(
        {"need": [2, 2], "upper": [3, 3], "2024-06-01": [1, 2]},
        index=["09:00", "10:00"],
    )
    score = app.calc_opt_score_from_heatmap(df, 0.6, 0.4)
    assert score.shape == (2, 1)
    expected = 1 - 0.6 * pd.Series([0.5, 0], index=["09:00", "10:00"])
    assert score.iloc[0, 0] == expected.iloc[0]
    assert score.iloc[1, 0] == expected.iloc[1]
