import sys
import types
import numpy as np
import pandas as pd


def test_learn_roster_generates_excel(tmp_path, monkeypatch):
    # Stub gymnasium before importing rl
    fake_gym = types.SimpleNamespace()

    class FakeEnv:
        def reset(self, *args, **kwargs):
            return None

    fake_gym.Env = FakeEnv
    fake_gym.spaces = types.SimpleNamespace(
        Discrete=lambda *a, **kw: None,
        Box=lambda *a, **kw: None,
    )
    monkeypatch.setitem(sys.modules, "gymnasium", fake_gym)

    # Stub stable_baselines3.PPO
    class FakePPO:
        def __init__(self, policy, env, verbose=0):
            self.env = env

        def learn(self, total_timesteps):
            pass

        def predict(self, obs, deterministic=True):
            return np.array([1]), None

        @classmethod
        def load(cls, path):
            return cls(None, None)

        def save(self, path):
            pass

    fake_sb3 = types.SimpleNamespace(PPO=FakePPO)
    monkeypatch.setitem(sys.modules, "stable_baselines3", fake_sb3)

    from shift_suite.tasks.rl import learn_roster

    demand_df = pd.DataFrame({
        "ds": pd.date_range("2024-01-01", periods=3),
        "need": [1, 2, 3],
    })
    demand_csv = tmp_path / "demand.csv"
    demand_df.to_csv(demand_csv, index=False)

    forecast_df = pd.DataFrame({
        "ds": pd.date_range("2024-01-04", periods=5),
        "forecast": [2] * 5,
    })
    forecast_csv = tmp_path / "forecast.csv"
    forecast_df.to_csv(forecast_csv, index=False)

    excel_fp = tmp_path / "roster.xlsx"
    horizon = 5

    out = learn_roster(demand_csv, excel_fp, forecast_csv=forecast_csv, horizon=horizon)
    assert out.exists()
    roster_df = pd.read_excel(out)
    assert len(roster_df) == horizon


def test_learn_roster_model_load_failure(tmp_path, monkeypatch):
    fake_gym = types.SimpleNamespace()

    class FakeEnv:
        def reset(self, *args, **kwargs):
            return None

    fake_gym.Env = FakeEnv
    fake_gym.spaces = types.SimpleNamespace(
        Discrete=lambda *a, **kw: None,
        Box=lambda *a, **kw: None,
    )
    monkeypatch.setitem(sys.modules, "gymnasium", fake_gym)

    class FakePPO:
        def __init__(self, policy, env, verbose=0):
            self.env = env

        def learn(self, total_timesteps):
            pass

        def predict(self, obs, deterministic=True):
            return np.array([1]), None

        @classmethod
        def load(cls, path):
            raise RuntimeError("load failed")

        def save(self, path):
            pass

    fake_sb3 = types.SimpleNamespace(PPO=FakePPO)
    monkeypatch.setitem(sys.modules, "stable_baselines3", fake_sb3)

    from shift_suite.tasks.rl import learn_roster

    demand_df = pd.DataFrame({
        "ds": pd.date_range("2024-01-01", periods=2),
        "need": [1, 2],
    })
    demand_csv = tmp_path / "demand.csv"
    demand_df.to_csv(demand_csv, index=False)

    forecast_df = pd.DataFrame({
        "ds": pd.date_range("2024-01-03", periods=3),
        "forecast": [2] * 3,
    })
    forecast_csv = tmp_path / "forecast.csv"
    forecast_df.to_csv(forecast_csv, index=False)

    model_fp = tmp_path / "model.zip"
    model_fp.write_text("x")

    excel_fp = tmp_path / "roster.xlsx"

    out = learn_roster(
        demand_csv,
        excel_fp,
        forecast_csv=forecast_csv,
        model_path=model_fp,
        use_saved_model=True,
    )
    assert out is None
