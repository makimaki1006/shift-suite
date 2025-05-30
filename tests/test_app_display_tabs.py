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
    dummy = types.SimpleNamespace(
        subheader=lambda *a, **k: None,
        dataframe=lambda *a, **k: None,
        plotly_chart=lambda *a, **k: None,
        radio=lambda *a, **k: None,
        slider=lambda *a, **k: None,
        selectbox=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        info=lambda msg: messages.append(msg),
        columns=lambda *a, **k: [types.SimpleNamespace(metric=lambda *aa, **kk: None) for _ in range(a[0])],
    )
    return dummy, messages


def test_display_fairness_tab_empty(monkeypatch, tmp_path):
    (tmp_path / "fairness_after.xlsx").touch()
    monkeypatch.setattr(app, "load_excel_cached", lambda *a, **k: pd.DataFrame())
    dummy_st, infos = make_dummy_st()
    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)
    app.display_fairness_tab(DummyTab(), tmp_path)
    assert "Data not available" in infos[0]


def test_display_leave_analysis_tab_handles_csv(monkeypatch, tmp_path):
    df = pd.DataFrame({"date": ["2024-06-01"], "leave_type": ["requested"], "total_leave_days": [2]})
    (tmp_path / "leave_analysis.csv").write_text(df.to_csv(index=False))
    dummy_st, infos = make_dummy_st()
    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "_", lambda x: x)
    app.display_leave_analysis_tab(DummyTab(), tmp_path)
    assert infos == []
