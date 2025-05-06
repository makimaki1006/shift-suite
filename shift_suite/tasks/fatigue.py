"""shift_suite.fatigue – 疲労リスクスコアリング (LightGBM 回帰)"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from lightgbm import LGBMRegressor
from .utils import save_df_xlsx, log


def _features(long_df: pd.DataFrame) -> pd.DataFrame:
    df = long_df.copy()
    df["is_night"] = df["code"].str.contains("夜", na=False)
    feats = (
        df.groupby("name")
          .agg(total_shift=("code", "size"), night=("is_night", "sum"))
    )
    feats["night_ratio"] = feats["night"] / feats["total_shift"]
    return feats[["night_ratio"]]


def train_fatigue(long_df: pd.DataFrame, out_dir: Path):
    X = _features(long_df)
    y = (X["night_ratio"] * 100).clip(0, 100)         # 疲労 = 夜勤比率×100
    model = LGBMRegressor(random_state=0).fit(X, y)
    X["fatigue_score"] = model.predict(X).clip(0, 100)
    save_df_xlsx(X[["fatigue_score"]], out_dir / "fatigue_score.xlsx", "fatigue")
    log.info("fatigue: score file written")
    return model
