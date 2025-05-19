"""shift_suite.fatigue – 疲労リスクスコアリング (LightGBM 回帰)"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from lightgbm import LGBMRegressor
from .utils import save_df_xlsx, log


def _features(long_df: pd.DataFrame) -> pd.DataFrame:
    df = long_df.copy()
    df["is_night"] = df["code"].str.contains("夜", na=False)
    # 特徴量エンジニアリングの際、スタッフ識別列を "name" から "staff" に変更
    feats = (
        df.groupby("staff") # "name" から "staff" に変更
          .agg(total_shift=("code", "size"), night=("is_night", "sum"))
    )
    # total_shiftが0の場合のZeroDivisionErrorを避ける
    feats["night_ratio"] = (feats["night"] / feats["total_shift"].replace(0, pd.NA)).fillna(0).round(3)
    return feats[["night_ratio"]]


def train_fatigue(long_df: pd.DataFrame, out_dir: Path):
    if "staff" not in long_df.columns:
        log.error("[fatigue] long_dfに 'staff' 列が見つかりません。処理をスキップします。")
        # 空のDataFrameを保存するか、エラーをraiseするかは要件による
        # ここでは空のDataFrameを保存して処理の継続を試みる
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_xlsx(empty_fatigue_df, out_dir / "fatigue_score.xlsx", "fatigue")
        log.info("fatigue: 'staff'列がなかったため、空のfatigue_score.xlsxを作成しました。")
        return None # または適切なエラー処理

    X = _features(long_df)
    if X.empty:
        log.warning("[fatigue] 特徴量データ(X)が空です。疲労スコアは計算されません。")
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_xlsx(empty_fatigue_df, out_dir / "fatigue_score.xlsx", "fatigue")
        return None

    y = (X["night_ratio"] * 100).clip(0, 100)         # 疲労 = 夜勤比率×100
    
    # データが少ない場合や、yのバリエーションがない場合にLGBMがエラーを出すことがあるため、最小限の行数チェック
    if len(X) < 2 or len(y.unique()) < 2 :
        log.warning(f"[fatigue] 学習データが不足しているか、目的変数のバリエーションがありません (Xの行数: {len(X)}, yのユニーク数: {len(y.unique())})。疲労スコアは0として記録します。")
        X["fatigue_score"] = 0.0
    else:
        try:
            model = LGBMRegressor(random_state=0, verbosity=-1).fit(X, y) # verbosity=-1で警告を抑制
            X["fatigue_score"] = model.predict(X).clip(0, 100).round(2)
        except Exception as e:
            log.error(f"[fatigue] LGBMRegressorの学習または予測中にエラーが発生しました: {e}。疲労スコアは0として記録します。")
            X["fatigue_score"] = 0.0

    # fatigue_score列のみを保存
    fatigue_output_df = X[["fatigue_score"]].copy()
    save_df_xlsx(fatigue_output_df, out_dir / "fatigue_score.xlsx", "fatigue")
    log.info(f"fatigue: score file written to {out_dir / 'fatigue_score.xlsx'}")
    # train_fatigueはモデルを返す設計だったが、app.pyでは返り値を使っていないため、Noneを返すか、必要ならモデルを返す
    return None # model を返す場合は model
