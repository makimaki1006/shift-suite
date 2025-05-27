import pandas as pd
import numpy as np
from pathlib import Path
from shift_suite.tasks import rl

class DummyPPO:
    def __init__(self, *args, **kwargs):
        self.env = args[1]
    def learn(self, *args, **kwargs):
        pass
    def predict(self, obs, deterministic=True):
        return np.array([0]), None
    def save(self, path):
        pass
    @classmethod
    def load(cls, path):
        return cls(None, rl.RosterEnv(np.array([0])))

def test_learn_roster_forecast_longer(monkeypatch, tmp_path):
    demand_df = pd.DataFrame({"ds": pd.date_range("2024-01-01", periods=2), "need": [1,2]})
    demand_fp = tmp_path / "demand.csv"
    demand_df.to_csv(demand_fp, index=False)

    fc_df = pd.DataFrame({"yhat": [1,2,3,4]})
    fc_fp = tmp_path / "fc.csv"
    fc_df.to_csv(fc_fp, index=False)

    sh_df = pd.DataFrame({"shortage": [0]})
    sh_fp = tmp_path / "sh.csv"
    sh_df.to_csv(sh_fp, index=False)

    monkeypatch.setattr(rl, "PPO", DummyPPO)

    out = rl.learn_roster(demand_fp, tmp_path / "out.xlsx", forecast_csv=fc_fp, shortage_csv=sh_fp)
    assert out is not None
