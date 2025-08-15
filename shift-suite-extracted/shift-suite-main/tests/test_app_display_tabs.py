import types

import pandas as pd

from shift_suite import app


class DummyTab:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def make_dummy_st():
    messages = []
    metric_calls = []

    def columns(n, **k):
        return [
            types.SimpleNamespace(
                metric=lambda *aa, **kk: metric_calls.append((aa, kk))
            )
            for _ in range(n)
        ]

    dummy = types.SimpleNamespace(
        subheader=lambda *a, **k: None,
        dataframe=lambda *a, **k: None,
        plotly_chart=lambda *a, **k: None,
        radio=lambda *a, **k: None,
        slider=lambda *a, **k: None,
        selectbox=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        info=lambda msg: messages.append(msg),
        columns=columns,
    )
    return dummy, messages, metric_calls


def test_display_fairness_tab_empty(monkeypatch, tmp_path):
    (tmp_path / "fairness_after.parquet").touch()
    monkeypatch.setattr(app, "load_data_cached", lambda *a, **k: pd.DataFrame())
    dummy_st, infos, _ = make_dummy_st()
    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)
    app.display_fairness_tab(DummyTab(), tmp_path)
    assert "Data not available" in infos[0]


def test_display_leave_analysis_tab_handles_dict(monkeypatch):
    df = pd.DataFrame(
        {"date": ["2024-06-01"], "leave_type": ["requested"], "total_leave_days": [2]}
    )
    results = {"daily_summary": df}
    dummy_st, infos, _ = make_dummy_st()
    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)
    app.display_leave_analysis_tab(DummyTab(), results)
    assert infos == []


def test_display_overview_tab_metrics(monkeypatch, tmp_path):
    df_shortage = pd.DataFrame(
        {
            "lack_h": [5, 3],
            "estimated_excess_cost": [0, 0],
            "estimated_lack_cost_if_temporary_staff": [0, 0],
            "estimated_lack_penalty_cost": [0, 0],
        }
    )
    df_meta = pd.DataFrame({"metric": ["jain_index"], "value": [0.8]})
    df_staff = pd.DataFrame({"night_ratio": [0.2, 0.3]})
    df_alerts = pd.DataFrame({"category": ["c"], "value": [1]})

    def fake_load_data_cached(path, *a, **k):
        if "shortage_role_summary.parquet" in path:
            return df_shortage
        if "fairness_before.parquet" in path:
            return df_meta
        if "staff_stats.parquet" in path:
            return df_staff
        return pd.DataFrame()

    class DummyXLS:
        sheet_names = ["alerts"]

        def parse(self, name):
            assert name == "alerts"
            return df_alerts

    monkeypatch.setattr(app, "load_data_cached", fake_load_data_cached)
    # stats_alerts.parquet loaded via load_data_cached as well

    dummy_st, infos, metrics = make_dummy_st()
    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)

    app.display_overview_tab(DummyTab(), tmp_path)
    assert infos == []
    assert len(metrics) == 8
