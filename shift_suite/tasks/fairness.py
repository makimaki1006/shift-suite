# shift_suite/tasks/fairness.py (修正案 v0.9)

from __future__ import annotations
import datetime as dt
import logging
from pathlib import Path
from typing import Optional, Sequence
import pandas as pd

log = logging.getLogger(__name__)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
        "%Y-%m-%d %H:%M:%S",  # ★ フォーマット変更
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

_STAFF_ALIASES: Sequence[str] = [
    "staff",
    "name",
    "worker",
    "employee",
    "member",
    "スタッフ",
    "職員",
    "従業員",
]


def _find_staff_column_name(
    df: pd.DataFrame, staff_col_preference: Optional[str] = None
) -> str:
    # (変更なし)
    if staff_col_preference and staff_col_preference in df.columns:
        return staff_col_preference
    for alias in _STAFF_ALIASES:
        if alias in df.columns:
            return alias
    if isinstance(df.index, pd.MultiIndex):
        for name in df.index.names:
            if name in _STAFF_ALIASES:
                return str(name)
    obj_cols = [c for c in df.columns if df[c].dtype == "object"]
    if obj_cols:
        # よりスタッフ名らしい列を選ぶためのヒューリスティックを追加検討可能
        # 例: ユニーク数が多く、かつ文字列長がある程度のものなど
        candidate = max(obj_cols, key=lambda c: df[c].nunique())
        log.warning(f"[fairness] スタッフ列推定: '{candidate}' を使用。")
        return candidate
    raise KeyError(
        "スタッフを示す列 ('staff', 'name'など) がDataFrameに見つかりません。"
    )


def _extract_time_series(df: pd.DataFrame) -> pd.Series:
    # (変更なし - ds列から時刻を抽出する部分は問題ないはず)
    if "ds" in df.columns and pd.api.types.is_datetime64_any_dtype(df["ds"].dtype):
        log.debug(
            "[fairness] 'ds' 列 (datetime64) から時刻情報を抽出します。"
        )  # ★ DEBUGに変更
        return pd.to_datetime(df["ds"]).dt.time
    # ... (以下、既存のフォールバック処理)
    if "time" in df.columns:
        col = df["time"]
        if pd.api.types.is_object_dtype(col.dtype) or pd.api.types.is_string_dtype(
            col.dtype
        ):
            log.debug(
                "[fairness] 'time' 列 (object/string) から時刻情報をパースします。"
            )
            return pd.to_datetime(col, format="%H:%M", errors="coerce").dt.time
        elif pd.api.types.is_datetime64_any_dtype(col.dtype):
            log.debug("[fairness] 'time' 列 (datetime64) から時刻情報を抽出します。")
            return pd.to_datetime(col).dt.time
        elif all(isinstance(x, dt.time) for x in col.dropna()):
            log.debug("[fairness] 'time' 列 (datetime.time) を使用します。")
            return col
        else:
            log.warning(
                f"[fairness] 'time' 列の型が予期しません: {col.dtype}。00:00と仮定。"
            )
    for cand_col_name in ("datetime", "dt"):
        if cand_col_name in df.columns and pd.api.types.is_datetime64_any_dtype(
            df[cand_col_name].dtype
        ):
            log.debug(f"[fairness] '{cand_col_name}' 列から時刻情報を抽出。")
            return pd.to_datetime(df[cand_col_name]).dt.time
    if isinstance(df.index, pd.DatetimeIndex):
        log.debug("[fairness] DatetimeIndex から時刻情報を抽出。")
        return df.index.to_series().dt.time
    log.warning("[fairness] 時刻情報列が見つからず、全行 00:00 を仮置き。")
    return pd.Series([dt.time(0, 0)] * len(df), index=df.index)


def _is_night(
    time_obj: Optional[dt.time], night_start: dt.time, night_end: dt.time
) -> bool:
    # (変更なし)
    if time_obj is None or not isinstance(time_obj, dt.time):
        return False
    if night_start <= night_end:
        return night_start <= time_obj <= night_end
    else:
        return time_obj >= night_start or time_obj <= night_end


def run_fairness(
    long_df: pd.DataFrame,
    out_dir: Path | str,
    *,
    staff_col_preference: Optional[str] = None,
    night_start_time: dt.time = dt.time(22, 0),
    night_end_time: dt.time = dt.time(5, 59),  # 翌朝の5:59まで
) -> None:
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)  # ★ 変数名変更
    if long_df.empty:
        log.warning("[fairness] 入力DataFrame (long_df) が空。スキップ。")
        # 空の場合でもExcelファイルは作成する（引継ぎ資料の動作に合わせる）
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
        pd.DataFrame({"metric": ["jain_index"], "value": [1.0]}).to_excel(
            out_dir_path / "fairness_before.xlsx",
            sheet_name="meta_summary",
            index=False,
        )
        empty_summary.to_excel(
            out_dir_path / "fairness_before.xlsx",
            sheet_name="before_summary",
            index=False,
            mode="a",
            if_sheet_exists="replace",
        )  # mode="a" and if_sheet_exists for openpyxl
        pd.DataFrame({"metric": ["jain_index"], "value": [1.0]}).to_excel(
            out_dir_path / "fairness_after.xlsx", sheet_name="meta_summary", index=False
        )
        empty_summary.to_excel(
            out_dir_path / "fairness_after.xlsx",
            sheet_name="after_summary",
            index=False,
            mode="a",
            if_sheet_exists="replace",
        )
        return

    df_for_fairness = long_df.copy()  # ★ 変数名変更
    try:
        actual_staff_col_name = _find_staff_column_name(
            df_for_fairness, staff_col_preference
        )  # ★ 変数名変更
        log.info(f"[fairness] スタッフ識別列: '{actual_staff_col_name}'")
    except KeyError as e:
        log.error(f"[fairness] {e} スキップ。")
        return

    # ★修正箇所: 疲労分析と同様に code 列を優先的に使用して夜勤を判定
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
        )  # ★ 変数名変更

        # total_slots は全スロット（parsed_slots_count>0のもの）で計算するのが適切か、
        # それとも全レコード（parsed_slots_count=0の休暇も含む）で計算するのか。
        # ここでは、公平性評価の母数となる total_slots は、実際に勤務スロットが発生したものをカウントするのが妥当。
        # parsed_slots_count > 0 のレコードでスタッフごとに集計
        if "parsed_slots_count" in df_for_fairness.columns:
            total_slots_series = (
                df_for_fairness[df_for_fairness["parsed_slots_count"] > 0]
                .groupby(actual_staff_col_name)["ds"]
                .count()
            )
        else:  # parsed_slots_countがない場合は、便宜的に全レコードをカウント（ただしこれは不正確になる可能性）
            total_slots_series = df_for_fairness.groupby(actual_staff_col_name)[
                "ds"
            ].count()

        summary_df = pd.DataFrame(
            {  # ★ 変数名変更
                actual_staff_col_name: unique_staff_list,
                "night_slots": 0,
            }
        ).set_index(actual_staff_col_name)
        summary_df["total_slots"] = total_slots_series
        summary_df = summary_df.fillna(
            {"total_slots": 0}
        ).reset_index()  # total_slotsがないスタッフは0で埋める
        summary_df["night_ratio"] = 0.0
        jain_index_val = 1.0  # ★ 変数名変更
    else:
        # night_slots: is_night_shift が 1 のレコードをカウント
        # total_slots: parsed_slots_count > 0 のレコードをカウント (夜勤の有無に関わらず)

        # is_night_shift は既に計算済み (parsed_slots_count > 0 のレコードに対してのみ1が立つ可能性がある)
        night_slots_series = df_for_fairness.groupby(actual_staff_col_name)[
            "is_night_shift"
        ].sum()

        if "parsed_slots_count" in df_for_fairness.columns:
            total_slots_for_fairness_series = (
                df_for_fairness[df_for_fairness["parsed_slots_count"] > 0]
                .groupby(actual_staff_col_name)["ds"]
                .count()
            )  # ★ 変数名変更
        else:  # フォールバック
            total_slots_for_fairness_series = df_for_fairness.groupby(
                actual_staff_col_name
            )["ds"].count()

        summary_df = pd.DataFrame(night_slots_series).rename(
            columns={"is_night_shift": "night_slots"}
        )
        summary_df["total_slots"] = total_slots_for_fairness_series
        summary_df = summary_df.fillna(
            {"night_slots": 0, "total_slots": 0}
        ).reset_index()  # 存在しないスタッフは0で埋める

        summary_df["night_ratio"] = (
            (summary_df["night_slots"] / summary_df["total_slots"].replace(0, pd.NA))
            .fillna(0)
            .round(3)
        )

        from shift_suite.tasks.utils import calculate_jain_index

        jain_index_val = calculate_jain_index(summary_df["night_ratio"])

    # ---- per-staff fairness score ----
    mean_ratio = float(summary_df["night_ratio"].mean()) if not summary_df.empty else 0.0
    if mean_ratio == 0:
        summary_df["fairness_score"] = (summary_df["night_ratio"] == 0).astype(float)
    else:
        summary_df["fairness_score"] = 1 - (summary_df["night_ratio"] - mean_ratio).abs() / mean_ratio
    summary_df["fairness_score"] = summary_df["fairness_score"].clip(0, 1).round(3)

    jain_night_ratio = calculate_jain_index(summary_df["night_ratio"])
    jain_night_slots = calculate_jain_index(summary_df["night_slots"])
    jain_total_slots = calculate_jain_index(summary_df["total_slots"])
    jain_index_val = jain_night_ratio

    summary_df.attrs["jain_index"] = (
        jain_index_val  # summary_df に属性としてJain指数を保持
    )
    before_fp_path = out_dir_path / "fairness_before.xlsx"
    after_fp_path = out_dir_path / "fairness_after.xlsx"  # ★ 変数名変更

    # ExcelWriter を使用して複数のシートを同じファイルに書き込む
    try:
        with pd.ExcelWriter(before_fp_path, engine="openpyxl") as wb_before:
            summary_df.to_excel(wb_before, sheet_name="before_summary", index=False)
            meta_df_before = pd.DataFrame(
                {
                    "metric": [
                        "jain_night_ratio",
                        "jain_night_slots",
                        "jain_total_slots",
                    ],
                    "value": [jain_night_ratio, jain_night_slots, jain_total_slots],
                }
            )
            meta_df_before.to_excel(wb_before, sheet_name="meta_summary", index=False)
        log.info(
            f"[fairness] fairness_before.xlsx 保存 (Jain: {jain_index_val:.3f})"
        )

        with pd.ExcelWriter(after_fp_path, engine="openpyxl") as wa_after:
            summary_df.to_excel(wa_after, sheet_name="after_summary", index=False)
            meta_df_after = pd.DataFrame(
                {
                    "metric": [
                        "jain_night_ratio",
                        "jain_night_slots",
                        "jain_total_slots",
                    ],
                    "value": [jain_night_ratio, jain_night_slots, jain_total_slots],
                }
            )
            meta_df_after.to_excel(wa_after, sheet_name="meta_summary", index=False)
        log.info(f"[fairness] fairness_after.xlsx 保存 (Jain: {jain_index_val:.3f})")
    except Exception as e:
        log.error(f"[fairness] Excel書出エラー: {e}", exc_info=True)
