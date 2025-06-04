import pandas as pd
from shift_suite.tasks import dashboard


def test_shortage_heatmap_returns_fig():
    df = pd.DataFrame({"2024-01-01": [0.1, 0.2]}, index=["08:00", "08:30"])
    fig = dashboard.shortage_heatmap(df)
    assert hasattr(fig, "data")


def test_fatigue_distribution_returns_fig():
    df = pd.DataFrame({"staff": ["A", "B"], "fatigue_score": [50, 70]})
    fig = dashboard.fatigue_distribution(df)
    assert hasattr(fig, "data")


def test_fairness_histogram_returns_fig():
    df = pd.DataFrame({"staff": ["A", "B"], "night_ratio": [0.1, 0.2]})
    fig = dashboard.fairness_histogram(df)
    assert hasattr(fig, "data")


def test_fairness_histogram_custom_metric():
    df = pd.DataFrame({"staff": ["A", "B"], "fairness_score": [0.9, 0.8]})
    fig = dashboard.fairness_histogram(df, metric="fairness_score")
    assert hasattr(fig, "data")
