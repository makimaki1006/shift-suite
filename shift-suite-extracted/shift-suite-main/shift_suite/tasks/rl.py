"""
shift_suite.tasks.rl  v0.4.0 – PPO によるシフト生成
────────────────────────────────────────────────────────
* 需要系列 CSV → ロスター最適化
* 2025-05-01 : `need` ⇆ `y` フォールバック、meta 出力などを復元
"""

from __future__ import annotations

import warnings
from pathlib import Path

import gymnasium as gym
import numpy as np
import pandas as pd
from stable_baselines3 import PPO

from .utils import log, save_df_parquet, write_meta


# ═════════════════ Env ═════════════════
class RosterEnv(gym.Env):
    """Simple environment for roster generation."""

    def __init__(
        self,
        demand: np.ndarray,
        shortage: np.ndarray | None = None,
        max_staff: int | None = None,
    ) -> None:
        super().__init__()
        self.demand = demand.astype(float)
        self.shortage = shortage if shortage is not None else np.zeros_like(self.demand)
        self.max_staff = int(max_staff or (self.demand.max() * 2))
        self.action_space = gym.spaces.Discrete(self.max_staff + 1)
        high = np.array([self.demand.max(), self.shortage.max()])
        self.observation_space = gym.spaces.Box(low=0, high=high + 1, dtype=np.float32)
        self._idx = 0

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._idx = 0
        obs = np.array(
            [self.demand[self._idx], self.shortage[self._idx]], dtype=np.float32
        )
        return obs, {}

    def step(self, action):
        demand_val = self.demand[self._idx]
        penalty_short = max(0.0, demand_val - action)
        penalty_over = max(0.0, action - demand_val)
        reward = -(2.0 * penalty_short + 1.0 * penalty_over)
        self._idx += 1
        done = self._idx >= len(self.demand)
        if done:
            obs = np.array([0.0, 0.0], dtype=np.float32)
        else:
            obs = np.array(
                [self.demand[self._idx], self.shortage[self._idx]], dtype=np.float32
            )
        return obs, reward, done, False, {}


# ═════════════════ Main ═════════════════
def learn_roster(
    demand_csv: Path,
    excel_out: Path,
    *,
    forecast_csv: Path | None = None,
    shortage_csv: Path | None = None,
    horizon: int = 14,
    model_path: Path | None = None,
    use_saved_model: bool = False,
) -> Path | None:
    """
    需要 CSV（ds, need|y）を読み込み、簡易 PPO でロスターを生成する *デモ実装*。

    実装メモ
    --------
    - 本関数はアルゴリズム枠のみ提供。実務ロジックと置き換えて利用してください。
    - `horizon` : 学習／予測対象期間（現 stub では未使用）。
    """
    log.info("[rl] learn_roster start")

    df = pd.read_csv(demand_csv, parse_dates=["ds"])

    # --- 需要列を柔軟に取得 ---------------------------
    if "need" in df.columns:
        demand = df["need"].values
    elif "y" in df.columns:
        demand = df["y"].values
        warnings.warn(
            "[rl] `need` 列が無かったため `y` 列を使用しました（forecast 由来）",
            stacklevel=2,
        )
    else:
        log.warning("[rl] 需要列 (`need` または `y`) が見つからず学習をスキップ")
        return None

    # --- 予測需要の読み込み ---------------------------
    forecast = None
    fc_dates = None
    if forecast_csv and Path(forecast_csv).exists():
        df_fc = (
            pd.read_excel(forecast_csv)
            if str(forecast_csv).endswith(".xlsx")
            else pd.read_csv(forecast_csv)
        )
        if "yhat" in df_fc.columns:
            forecast = df_fc["yhat"].values.astype(float)
        elif "forecast" in df_fc.columns:
            forecast = df_fc["forecast"].values.astype(float)
        if "ds" in df_fc.columns:
            fc_dates = df_fc["ds"].copy()

    if forecast is None:
        forecast = demand

    # --- 過去の不足パターン ---------------------------
    shortage_hist = np.zeros_like(demand, dtype=float)
    if shortage_csv and Path(shortage_csv).exists():
        df_sh = (
            pd.read_excel(shortage_csv)
            if str(shortage_csv).endswith(".xlsx")
            else pd.read_csv(shortage_csv)
        )
        col = (
            "shortage"
            if "shortage" in df_sh.columns
            else ("lack_h" if "lack_h" in df_sh.columns else None)
        )
        if col:
            shortage_hist = df_sh[col].values.astype(float)[: len(demand)]

    if len(shortage_hist) < len(forecast):
        # Padding prevents index errors when the forecast extends beyond
        # the available shortage history.
        shortage_hist = np.pad(
            shortage_hist, (0, len(forecast) - len(shortage_hist)), constant_values=0
        )

    if len(demand) < 2 or demand.sum() == 0:
        log.warning("[rl] 需要データが不足しているため学習をスキップ")
        return None

    # --- モデル学習 or 読み込み -----------------------
    env = RosterEnv(demand, shortage_hist)
    if use_saved_model and model_path and Path(model_path).exists():
        try:
            model = PPO.load(model_path)
        except Exception as e:  # pragma: no cover - just in case
            log.error(f"[rl] model load failed: {e}", exc_info=True)
            return None
    else:
        model = PPO("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=len(demand) * horizon)
        if model_path:
            model.save(model_path)

    # --- 推論対象データ準備 ---------------------------
    env_pred = RosterEnv(forecast, shortage_hist[: len(forecast)])
    obs, _ = env_pred.reset()
    roster: list[int] = []
    for _ in range(len(forecast)):
        action, _ = model.predict(obs, deterministic=True)
        roster.append(int(action))
        obs, _, done, _, _ = env_pred.step(action)
        if done:
            break

    if fc_dates is not None:
        ds_col = pd.to_datetime(fc_dates).iloc[: len(roster)]
    else:
        ds_col = df["ds"].copy()
        if len(ds_col) < len(roster):
            if len(ds_col) > 1:
                freq = ds_col.iloc[1] - ds_col.iloc[0]
            else:
                freq = pd.Timedelta(days=1)
            start = ds_col.iloc[-1] + freq
            extra = pd.date_range(start, periods=len(roster) - len(ds_col), freq=freq)
            ds_col = pd.concat([ds_col, pd.Series(extra)])
        ds_col = ds_col.iloc[: len(roster)]

    out_df = pd.DataFrame({"ds": ds_col.values, "roster": roster})
    save_df_parquet(out_df, excel_out)

    # meta
    note = "model_predict" if use_saved_model else "ppo_train"
    write_meta(
        excel_out.with_suffix(".meta.json"),
        note=note,
        horizon=horizon,
        rows=len(out_df),
    )

    if model_path and not use_saved_model:
        log.info(f"[rl] model saved → {model_path}")

    log.info(f"[rl] roster saved → {excel_out}")
    return excel_out


# ═════════════════ __all__ ═════════════════
__all__ = ["learn_roster"]
