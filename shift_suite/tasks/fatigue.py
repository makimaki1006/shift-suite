"""shift_suite.fatigue – 疲労リスクスコアリング."""

from __future__ import annotations
import pandas as pd
from pathlib import Path
from .utils import save_df_xlsx, log


def _features(long_df: pd.DataFrame) -> pd.DataFrame:
    df = long_df.copy()
    df["is_night"] = df["code"].str.contains("夜", na=False)
    df["is_work"] = df.get("parsed_slots_count", 0) > 0
    df["date"] = pd.to_datetime(df["ds"]).dt.date

    basic = df.groupby("staff").agg(
        total_days=("date", "nunique"),
        night_days=("is_night", "sum"),
    )
    basic["night_ratio"] = (
        (basic["night_days"] / basic["total_days"].replace(0, pd.NA))
    ).fillna(0).round(3)

    consec_metrics = []
    for staff, grp in df[df["is_work"]].groupby("staff"):
        dates = sorted(grp["date"].unique())
        if not dates:
            consec_metrics.append({
                "staff": staff,
                "consec3_ratio": 0.0,
                "consec4_ratio": 0.0,
                "consec5_ratio": 0.0,
            })
            continue
        dates_series = pd.Series(pd.to_datetime(dates))
        groups = dates_series.diff().dt.days.ne(1).cumsum()
        lengths = dates_series.groupby(groups).transform("size")
        total = len(dates_series)
        consec_metrics.append({
            "staff": staff,
            "consec3_ratio": (lengths >= 3).sum() / total,
            "consec4_ratio": (lengths >= 4).sum() / total,
            "consec5_ratio": (lengths >= 5).sum() / total,
        })

    consec_df = pd.DataFrame(consec_metrics).set_index("staff")
    feats = basic.join(consec_df, how="left").fillna(0)
    return feats[["night_ratio", "consec3_ratio", "consec4_ratio", "consec5_ratio"]]


def train_fatigue(long_df: pd.DataFrame, out_dir: Path):
    if "staff" not in long_df.columns:
        log.error(
            "[fatigue] long_dfに 'staff' 列が見つかりません。処理をスキップします。"
        )
        # 空のDataFrameを保存するか、エラーをraiseするかは要件による
        # ここでは空のDataFrameを保存して処理の継続を試みる
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_xlsx(empty_fatigue_df, out_dir / "fatigue_score.xlsx", "fatigue")
        log.info(
            "fatigue: 'staff'列がなかったため、空のfatigue_score.xlsxを作成しました。"
        )
        return None  # または適切なエラー処理

    X = _features(long_df)
    if X.empty:
        log.warning("[fatigue] 特徴量データ(X)が空です。疲労スコアは計算されません。")
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_xlsx(empty_fatigue_df, out_dir / "fatigue_score.xlsx", "fatigue")
        return None

    X["fatigue_score"] = (
        0.6 * X["night_ratio"]
        + 0.2 * X["consec3_ratio"]
        + 0.15 * X["consec4_ratio"]
        + 0.05 * X["consec5_ratio"]
    ) * 100
    X["fatigue_score"] = X["fatigue_score"].clip(0, 100).round(2)

    # fatigue_score列のみを保存
    fatigue_output_df = X[["fatigue_score"]].copy()
    save_df_xlsx(fatigue_output_df, out_dir / "fatigue_score.xlsx", "fatigue")
    log.info(f"fatigue: score file written to {out_dir / 'fatigue_score.xlsx'}")
    # train_fatigueはモデルを返す設計だったが、app.pyでは返り値を使っていないため、Noneを返すか、必要ならモデルを返す
    return None  # model を返す場合は model
