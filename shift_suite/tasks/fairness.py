import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from .analyzers.rest_time import RestTimeAnalyzer
from .leave_analyzer import approval_rate_by_staff
from .constants import NIGHT_START_TIME, NIGHT_END_TIME, is_night_shift_time, FATIGUE_PARAMETERS
from .utils import calculate_jain_index

log = logging.getLogger(__name__)


def _find_staff_column_name(df: pd.DataFrame, preference: Optional[str] = None) -> str:
    """
    スタッフを識別する列名を探す。
    preference が指定されていればそれを優先、なければ 'staff' を探す。
    """
    if preference and preference in df.columns:
        return preference

    candidates = ["staff", "スタッフ", "氏名", "名前", "employee", "name"]
    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    available_cols = list(df.columns)
    raise KeyError(
        f"スタッフ識別列が見つかりません。利用可能な列: {available_cols}. "
        f"preference='{preference}' も見つかりませんでした。"
    )


def _extract_time_series(df: pd.DataFrame) -> pd.Series:
    """
    long_df から時刻情報を抽出する。
    ds 列が datetime 型であることを前提とする。
    """
    if "ds" not in df.columns:
        raise KeyError("'ds' 列が見つかりません。")

    time_series = pd.to_datetime(df["ds"]).dt.time
    return time_series


def _is_night(
    time_obj: dt.time,
    night_start: dt.time = NIGHT_START_TIME,
    night_end: dt.time = NIGHT_END_TIME,
) -> bool:
    """
    指定された時刻が夜勤時間帯かどうかを判定する。
    統一された定数を使用: 22:00 - 05:59 (翌朝)。
    """
    return is_night_shift_time(time_obj)



def run_fairness(
    long_df: pd.DataFrame,
    out_dir: Path | str,
    *,
    staff_col_preference: Optional[str] = None,
    night_start_time: dt.time = dt.time(22, 0),
    night_end_time: dt.time = dt.time(5, 59),  # 翌朝の5:59まで
) -> None:
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    log.info("[fairness] run_fairness start")
    log.info(f"[fairness] long_df shape: {long_df.shape}")
    log.info(f"[fairness] out_dir_path: {out_dir_path}")
    log.debug(f"[fairness] long_df columns: {list(long_df.columns)}")
    log.debug(f"[fairness] long_df sample data:\n{long_df.head()}")
    log.debug(
        f"[fairness] unique staff members: {long_df['staff'].nunique() if 'staff' in long_df.columns else 'N/A'}"
    )

    if long_df.empty:
        log.warning("[fairness] 入力DataFrame (long_df) が空。スキップ。")
        empty_summary = pd.DataFrame(
            columns=[
                _find_staff_column_name(long_df, staff_col_preference)
                if not long_df.empty
                else "staff",
                "night_slots",
                "total_slots",
                "night_ratio",
            ]
        )
        pd.DataFrame({"metric": ["jain_index"], "value": [1.0]}).to_parquet(
            out_dir_path / "fairness_before.parquet",
            index=False,
        )
        empty_summary.to_parquet(
            out_dir_path / "fairness_after.parquet",
            index=False,
        )
        return

    df_for_fairness = long_df.copy()
    try:
        actual_staff_col_name = _find_staff_column_name(
            df_for_fairness, staff_col_preference
        )
        log.info(f"[fairness] スタッフ識別列: '{actual_staff_col_name}'")
    except KeyError as e:
        log.error(f"[fairness] {e} スキップ。")
        return

    use_code = (
        "code" in df_for_fairness.columns
        and df_for_fairness["code"].astype(str).str.contains("夜", na=False).any()
    )

    if use_code:
        log.info("[fairness] 'code' 列から夜勤判定を行います。")
        if "parsed_slots_count" in df_for_fairness.columns:
            working_slots_df = df_for_fairness[
                df_for_fairness["parsed_slots_count"] > 0
            ].copy()
        else:
            working_slots_df = df_for_fairness.copy()

        if not working_slots_df.empty:
            working_slots_df["is_night_shift"] = (
                working_slots_df["code"]
                .astype(str)
                .str.contains("夜", na=False)
                .astype(int)
            )
            df_for_fairness = df_for_fairness.merge(
                working_slots_df[["is_night_shift"]],
                left_index=True,
                right_index=True,
                how="left",
            ).fillna({"is_night_shift": 0})
            df_for_fairness["is_night_shift"] = df_for_fairness[
                "is_night_shift"
            ].astype(int)
        else:
            df_for_fairness["is_night_shift"] = 0
    elif "parsed_slots_count" not in df_for_fairness.columns:
        log.error(
            "[fairness] long_dfに 'parsed_slots_count' 列が見つかりません。夜勤判定をスキップします。"
        )
        df_for_fairness["is_night_shift"] = 0
    else:
        working_slots_df = df_for_fairness[
            df_for_fairness["parsed_slots_count"] > 0
        ].copy()
        if not working_slots_df.empty:
            time_series_working = _extract_time_series(working_slots_df)
            log.info(
                f"[fairness] 夜勤フラグ計算中 (夜勤帯: {night_start_time:%H:%M} - {night_end_time:%H:%M}) 対象レコード数: {len(working_slots_df)}"
            )
            working_slots_df["is_night_shift"] = time_series_working.apply(
                lambda t: int(_is_night(t, night_start_time, night_end_time))
            )
            df_for_fairness = df_for_fairness.merge(
                working_slots_df[["is_night_shift"]],
                left_index=True,
                right_index=True,
                how="left",
            ).fillna({"is_night_shift": 0})
            df_for_fairness["is_night_shift"] = df_for_fairness[
                "is_night_shift"
            ].astype(int)
        else:
            log.info(
                "[fairness] parsed_slots_count > 0 の勤務記録がないため、夜勤シフトはありません。"
            )
            df_for_fairness["is_night_shift"] = 0

    if df_for_fairness.empty or not df_for_fairness["is_night_shift"].any():
        log.info("[fairness] 夜勤シフト無しかデータ無。Jain指数1.0で処理。")
        unique_staff_list = (
            df_for_fairness[actual_staff_col_name].unique()
            if actual_staff_col_name in df_for_fairness
            else []
        )

        if "parsed_slots_count" in df_for_fairness.columns:
            total_slots_series = (
                df_for_fairness[df_for_fairness["parsed_slots_count"] > 0]
                .groupby(actual_staff_col_name)["ds"]
                .count()
            )
        else:
            total_slots_series = df_for_fairness.groupby(actual_staff_col_name)[
                "ds"
            ].count()

        summary_df = pd.DataFrame(
            {
                actual_staff_col_name: unique_staff_list,
                "night_slots": 0,
            }
        ).set_index(actual_staff_col_name)
        summary_df["total_slots"] = total_slots_series
        summary_df = summary_df.fillna({"total_slots": 0}).reset_index()
        summary_df["night_ratio"] = 0.0
        jain_index_val = 1.0
    else:
        night_slots_series = df_for_fairness.groupby(actual_staff_col_name)[
            "is_night_shift"
        ].sum()

        if "parsed_slots_count" in df_for_fairness.columns:
            total_slots_for_fairness_series = (
                df_for_fairness[df_for_fairness["parsed_slots_count"] > 0]
                .groupby(actual_staff_col_name)["ds"]
                .count()
            )
        else:
            total_slots_for_fairness_series = df_for_fairness.groupby(
                actual_staff_col_name
            )["ds"].count()

        summary_df = pd.DataFrame(night_slots_series).rename(
            columns={"is_night_shift": "night_slots"}
        )
        summary_df["total_slots"] = total_slots_for_fairness_series
        summary_df = summary_df.fillna(
            {"night_slots": 0, "total_slots": 0}
        ).reset_index()

        summary_df["night_ratio"] = (
            (summary_df["night_slots"] / summary_df["total_slots"].replace(0, pd.NA))
            .fillna(0)
            .round(3)
        )

        jain_index_val = calculate_jain_index(summary_df["night_ratio"])

    mean_ratio = (
        float(summary_df["night_ratio"].mean()) if not summary_df.empty else 0.0
    )
    if mean_ratio == 0:
        summary_df["fairness_score"] = (summary_df["night_ratio"] == 0).astype(float)
    else:
        summary_df["fairness_score"] = (
            1 - (summary_df["night_ratio"] - mean_ratio).abs() / mean_ratio
        )
    summary_df["fairness_score"] = summary_df["fairness_score"].clip(0, 1).round(3)

    # -- Additional metrics -------------------------------------------------
    work_slots_series = (
        df_for_fairness[df_for_fairness.get("parsed_slots_count", 0) > 0]
        .groupby(actual_staff_col_name)["parsed_slots_count"]
        .sum()
    )
    summary_df["total_work_slots"] = summary_df[actual_staff_col_name].map(work_slots_series).fillna(0)

    leave_rate_series = approval_rate_by_staff(long_df)
    summary_df["approval_rate"] = summary_df[actual_staff_col_name].map(leave_rate_series).fillna(0)

    rta = RestTimeAnalyzer()
    rest_daily = rta.analyze(long_df)
    consec_series = rta.consecutive_leave_frequency(rest_daily)
    summary_df["consecutive_leave_freq"] = summary_df[actual_staff_col_name].map(consec_series).fillna(0)

    # -- deviation from mean -----------------------------------------------
    def _dev(s: pd.Series, mean_val: float) -> pd.Series:
        if mean_val == 0:
            return pd.Series(0.0, index=s.index)
        return (s - mean_val).abs() / mean_val

    summary_df["dev_night_ratio"] = _dev(summary_df["night_ratio"], summary_df["night_ratio"].mean())
    summary_df["dev_work_slots"] = _dev(summary_df["total_work_slots"], summary_df["total_work_slots"].mean())
    summary_df["dev_approval_rate"] = _dev(summary_df["approval_rate"], summary_df["approval_rate"].mean())
    summary_df["dev_consecutive"] = _dev(summary_df["consecutive_leave_freq"], summary_df["consecutive_leave_freq"].mean())
    summary_df["unfairness_score"] = (
        summary_df[["dev_night_ratio", "dev_work_slots", "dev_approval_rate", "dev_consecutive"]].mean(axis=1)
    )
    summary_df["unfairness_rank"] = summary_df["unfairness_score"].rank(method="min", ascending=False).astype(int)
    summary_df = summary_df.sort_values("unfairness_rank").reset_index(drop=True)

    jain_night_ratio = calculate_jain_index(summary_df["night_ratio"])
    jain_night_slots = calculate_jain_index(summary_df["night_slots"])
    jain_total_slots = calculate_jain_index(summary_df["total_slots"])
    jain_index_val = jain_night_ratio

    log.debug(
        f"[fairness] Jain指数詳細 - night_ratio: {jain_night_ratio:.3f}, night_slots: {jain_night_slots:.3f}, total_slots: {jain_total_slots:.3f}"
    )
    log.debug(f"[fairness] summary_df shape: {summary_df.shape}")
    log.debug(f"[fairness] summary_df sample:\n{summary_df.head()}")

    summary_df.attrs["jain_index"] = jain_index_val
    before_fp_path = out_dir_path / "fairness_before.parquet"
    after_fp_path = out_dir_path / "fairness_after.parquet"

    try:
        meta_df = pd.DataFrame(
            {
                "metric": [
                    "jain_night_ratio",
                    "jain_night_slots",
                    "jain_total_slots",
                ],
                "value": [jain_night_ratio, jain_night_slots, jain_total_slots],
            }
        )
        meta_df.to_parquet(before_fp_path, index=False)
        summary_df.to_parquet(after_fp_path, index=False)
        log.info(
            f"[fairness] fairness_before.parquet / fairness_after.parquet 保存 (Jain: {jain_index_val:.3f})"
        )
    except Exception as e:
        log.error(f"[fairness] Parquet書出エラー: {e}", exc_info=True)
