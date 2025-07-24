"""shift_suite.fatigue – 疲労リスクスコアリング."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import log, save_df_parquet
from .analyzers.rest_time import RestTimeAnalyzer
from .constants import NIGHT_START_HOUR, NIGHT_END_HOUR, is_night_shift_time, FATIGUE_PARAMETERS


def _features(long_df: pd.DataFrame, slot_minutes: int = 30) -> pd.DataFrame:
    """Return feature dataframe used for fatigue scoring."""

    if long_df.empty or "staff" not in long_df.columns:
        return pd.DataFrame()

    df = long_df.copy()
    df["is_work"] = df.get("parsed_slots_count", 0) > 0
    df["date"] = pd.to_datetime(df["ds"]).dt.date

    work_df = df[df["is_work"]].copy()
    if work_df.empty:
        return pd.DataFrame()

    daily = (
        work_df.groupby(["staff", "date"])
        .agg(start=("ds", "min"), end=("ds", "max"), slots=("parsed_slots_count", "sum"))
        .reset_index()
    )
    daily["start_hour"] = daily["start"].dt.hour + daily["start"].dt.minute / 60
    daily["end_hour"] = (
        daily["end"] + pd.to_timedelta(slot_minutes, unit="m")
    ).dt.hour + (
        daily["end"] + pd.to_timedelta(slot_minutes, unit="m")
    ).dt.minute / 60
    daily["cross_mid"] = daily["end_hour"] <= daily["start_hour"]
    daily["end_hour_adj"] = daily["end_hour"] + 24 * daily["cross_mid"]

    def _cat(row: pd.Series) -> str:
        if (
            is_night_shift_time(int(row["start_hour"]))
            or row["cross_mid"]
            or row["end_hour_adj"] <= NIGHT_END_HOUR
        ):
            return "night"
        return "day"

    daily["time_category"] = daily.apply(_cat, axis=1)

    # ① start time randomness
    start_std = daily.groupby("staff")["start_hour"].std(ddof=0).fillna(0)

    # ② work code diversity
    code_diversity = work_df.groupby("staff")["code"].nunique()

    # ③ work hours randomness
    daily["work_hours"] = daily["slots"] * slot_minutes / 60.0
    worktime_std = daily.groupby("staff")["work_hours"].std(ddof=0).fillna(0)

    # ④ rest time penalty
    rest_df = RestTimeAnalyzer().analyze(df, slot_minutes=slot_minutes)
    min_rest_hours = FATIGUE_PARAMETERS["min_rest_hours"]
    rest_df["penalty"] = (min_rest_hours - rest_df["rest_hours"]).clip(lower=0)
    rest_penalty = rest_df.groupby("staff")["penalty"].mean() / min_rest_hours

    # ⑤ consecutive working days (existing logic)
    consec_metrics = []
    for staff, grp in work_df.groupby("staff"):
        dates = sorted(grp["date"].unique())
        if not dates:
            consec_metrics.append(
                {
                    "staff": staff,
                    "consec3_ratio": 0.0,
                    "consec4_ratio": 0.0,
                    "consec5_ratio": 0.0,
                }
            )
            continue
        dates_series = pd.Series(pd.to_datetime(dates))
        groups = dates_series.diff().dt.days.ne(1).cumsum()
        lengths = dates_series.groupby(groups).transform("size")
        total = len(dates_series)
        consec_metrics.append(
            {
                "staff": staff,
                "consec3_ratio": (lengths >= 3).sum() / total,
                "consec4_ratio": (lengths >= 4).sum() / total,
                "consec5_ratio": (lengths >= 5).sum() / total,
            }
        )
    consec_df = pd.DataFrame(consec_metrics).set_index("staff")

    # ⑥ night shift ratio using time categories with saturation
    basic = daily.groupby("staff").agg(
        total_days=("date", "nunique"),
        night_days=("time_category", lambda x: (x == "night").sum()),
    )
    basic["night_ratio"] = (
        (basic["night_days"] / basic["total_days"].replace(0, pd.NA)).fillna(0)
    )
    basic["night_ratio_adj"] = np.clip(basic["night_ratio"], 0, 0.8) / 0.8

    feats = pd.concat(
        [
            start_std.rename("start_std"),
            code_diversity.rename("code_diversity"),
            worktime_std.rename("worktime_std"),
            rest_penalty.rename("rest_penalty"),
            consec_df,
            basic[["night_ratio_adj"]],
        ],
        axis=1,
    ).fillna(0)

    return feats


def train_fatigue(
    long_df: pd.DataFrame,
    out_dir: Path,
    weights: dict[str, float] | None = None,
) -> None:
    if "staff" not in long_df.columns:
        log.error(
            "[fatigue] long_dfに 'staff' 列が見つかりません。処理をスキップします。"
        )
        # 空のDataFrameを保存するか、エラーをraiseするかは要件による
        # ここでは空のDataFrameを保存して処理の継続を試みる
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_parquet(empty_fatigue_df, out_dir / "fatigue_score.parquet")
        log.info(
            "fatigue: 'staff'列がなかったため、空のfatigue_score.xlsxを作成しました。"
        )
        return None  # または適切なエラー処理

    X = _features(long_df)
    if X.empty:
        log.warning("[fatigue] 特徴量データ(X)が空です。疲労スコアは計算されません。")
        empty_fatigue_df = pd.DataFrame(columns=["fatigue_score"])
        save_df_parquet(empty_fatigue_df, out_dir / "fatigue_score.parquet")
        return None

    weights_default = {
        "start_var": 1.0,
        "diversity": 1.0,
        "worktime_var": 1.0,
        "short_rest": 1.0,
        "consecutive": 1.0,
        "night_ratio": 1.0,
    }
    if weights:
        weights_default.update(weights)
    w = weights_default

    consec_score = (
        FATIGUE_PARAMETERS["consecutive_3_days_weight"] * X.get("consec3_ratio", 0)
        + FATIGUE_PARAMETERS["consecutive_4_days_weight"] * X.get("consec4_ratio", 0)
        + FATIGUE_PARAMETERS["consecutive_5_days_weight"] * X.get("consec5_ratio", 0)
    )

    norm_df = X.rank(pct=True)
    norm_df = norm_df.fillna(0)

    X["fatigue_score"] = (
        w["start_var"] * norm_df.get("start_std", 0)
        + w["diversity"] * norm_df.get("code_diversity", 0)
        + w["worktime_var"] * norm_df.get("worktime_std", 0)
        + w["short_rest"] * norm_df.get("rest_penalty", 0)
        + w["consecutive"] * consec_score
        + w["night_ratio"] * norm_df.get("night_ratio_adj", 0)
    )
    total_w = sum(w.values())
    if total_w > 0:
        X["fatigue_score"] = X["fatigue_score"] / total_w * 100
    X["fatigue_score"] = X["fatigue_score"].clip(0, 100).round(2)

    # fatigue_score列のみを保存
    fatigue_output_df = X[["fatigue_score"]].copy()
    save_df_parquet(fatigue_output_df, out_dir / "fatigue_score.parquet")
    log.info(f"fatigue: score file written to {out_dir / 'fatigue_score.parquet'}")
    # train_fatigueはモデルを返す設計だったが、app.pyでは返り値を使っていないため、Noneを返すか、必要ならモデルを返す
    return None  # model を返す場合は model
