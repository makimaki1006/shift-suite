import types

import numpy as np
import pandas as pd

from shift_suite.tasks import forecast
from shift_suite.tasks.forecast import forecast_need


class FakeARIMA:
    def __init__(self, y):
        self.arima_res_ = types.SimpleNamespace(
            data=types.SimpleNamespace(endog=np.asarray(y))
        )
        # intentionally no 'y' attribute

    def predict(self, n_periods, exogenous=None):
        return np.repeat(self.arima_res_.data.endog[-1], n_periods)

    def predict_in_sample(self):
        return self.arima_res_.data.endog


def fake_auto_arima(y, **kwargs):
    return FakeARIMA(y)


def test_forecast_need_arima_without_y(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2024-01-01", periods=5),
            "y": [1, 2, 3, 4, 5],
        }
    )
    demand_fp = tmp_path / "demand.csv"
    df.to_csv(demand_fp, index=False)

    excel_fp = tmp_path / "out.parquet"

    monkeypatch.setattr(forecast, "_HAS_PMDARIMA", True)
    monkeypatch.setattr(
        forecast, "pm", types.SimpleNamespace(auto_arima=fake_auto_arima)
    )

    out = forecast_need(demand_fp, excel_fp, choose="arima", periods=3)
    assert out.exists()
    result = pd.read_parquet(out)
    assert len(result) == 3
