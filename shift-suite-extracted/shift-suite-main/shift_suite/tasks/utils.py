# shift_suite/tasks/utils.py
# v1.2.1 ( _parse_as_date 移設)
"""
shift_suite.tasks.utils  v1.2.0 – UTF-8 write_meta 版
────────────────────────────────────────────────────────
* 共通ユーティリティ
* 2025-05-06
    - write_meta(): Windows でも文字化けしないよう `encoding="utf-8"` を明示
      （既定 CP932 だと "–" などの Unicode 文字列で UnicodeEncodeError）
    - 旧 API・関数名は一切変更なし
* 2025-05-16
    - build_stats.py から _parse_as_date を移設
* 2025-07-21
    - dash_app.py と app.py から _valid_df を統合
"""

from __future__ import annotations

import datetime as dt  #  dt エイリアスも明示的にインポート (他モジュールとの互換性のため)
import json
import logging
import math
import re
import shutil
import tempfile
import zipfile
from datetime import (
    datetime,
    timedelta,
)  #  dt エイリアスではなく datetime, timedelta を直接使用
from pathlib import Path
from typing import Any, Dict, Sequence

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from ..logger_config import configure_logging

# 追加箇所: constants から SUMMARY5 をインポート ( _parse_as_date で使用)
from .constants import SUMMARY5

# ────────────────── 1. ロガー ──────────────────
configure_logging()
log = logging.getLogger(__name__)
analysis_logger = logging.getLogger('analysis')


# ────────────────── 2. 休暇除外フィルター（統合版） ──────────────────
def apply_rest_exclusion_filter(df: pd.DataFrame, context: str = "unknown", for_display: bool = False, exclude_leave_records: bool = False) -> pd.DataFrame:
    """
    データパイプライン全体で使用する統一的な休暇除外フィルター
    
    Args:
        df: 対象データフレーム
        context: 適用箇所の説明（ログ用）
        for_display: True の場合、表示用として実績0の勤務日も保持
        exclude_leave_records: True の場合、holiday_type != '通常勤務' のレコードを除外
    
    Returns:
        フィルタリング済みデータフレーム
    """
    if df.empty:
        return df
    
    original_count = len(df)
    analysis_logger.info(f"[RestExclusion] {context}: フィルター開始 ({original_count}レコード)")
    
    # 1. スタッフ名による除外（最も重要）
    if 'staff' in df.columns:
        rest_patterns = [
            '×', 'X', 'x',           # 基本的な休み記号
            '休', '休み', '休暇',      # 日本語の休み
            '欠', '欠勤',             # 欠勤
            'OFF', 'off', 'Off',     # オフ
            '-', '−', '―',           # ハイフン類
            'nan', 'NaN', 'null',    # NULL値系
            '有', '有休',             # 有給
            '特', '特休',             # 特休
            '代', '代休',             # 代休
            '振', '振休'              # 振替休日
        ]
        
        excluded_by_pattern = {}
        for pattern in rest_patterns:
            if pattern.strip():  
                pattern_mask = (
                    (df['staff'].str.strip() == pattern) |
                    (df['staff'].str.contains(pattern, na=False, regex=False))
                )
                excluded_count = pattern_mask.sum()
                if excluded_count > 0:
                    excluded_by_pattern[pattern] = excluded_count
                    df = df[~pattern_mask]
        
        # 空文字・NaN除外
        empty_mask = (
            df['staff'].isna() |
            (df['staff'].str.strip() == '') |
            (df['staff'].str.strip() == ' ') |
            (df['staff'].str.strip() == '　')
        )
        excluded_count = empty_mask.sum()
        if excluded_count > 0:
            excluded_by_pattern['empty'] = excluded_count
            df = df[~empty_mask]
        
        if excluded_by_pattern:
            analysis_logger.info(f"[RestExclusion] {context}: スタッフ名による除外: {excluded_by_pattern}")
    
    # 2. parsed_slots_count による除外
    if 'parsed_slots_count' in df.columns:
        zero_slots_mask = df['parsed_slots_count'] <= 0
        zero_slots_count = zero_slots_mask.sum()
        if zero_slots_count > 0:
            df = df[~zero_slots_mask]
            analysis_logger.info(f"[RestExclusion] {context}: 0スロット除外: {zero_slots_count}件")
    
    # 3. staff_count による除外（事前集計データ用）
    # 🎯 表示用フィルター分離: 表示用の場合はstaff_count=0でも保持
    if 'staff_count' in df.columns and not for_display:
        # 按分計算用: 実績0を除外（精度向上）
        if 'holiday_type' not in df.columns:
            # holiday_typeがない場合のみ、以前の動作を維持
            zero_staff_mask = df['staff_count'] <= 0
            zero_staff_count = zero_staff_mask.sum()
            if zero_staff_count > 0:
                df = df[~zero_staff_mask]
                analysis_logger.info(f"[RestExclusion] {context}: 0人数除外: {zero_staff_count}件")
    elif 'staff_count' in df.columns and for_display:
        # 表示用: 実績0の勤務日も保持（俯瞰的観察用）
        analysis_logger.info(f"[RestExclusion] {context}: 表示用のため実績0の勤務日も保持")
    
    # 4. holiday_type による除外（明示的に要求された場合のみ）
    if 'holiday_type' in df.columns and exclude_leave_records:
        holiday_mask = df['holiday_type'] != '通常勤務'
        holiday_count = holiday_mask.sum()
        if holiday_count > 0:
            df = df[~holiday_mask]
            analysis_logger.info(f"[RestExclusion] {context}: 休暇タイプ除外: {holiday_count}件")
    elif 'holiday_type' in df.columns:
        # 休暇レコードを保持（デフォルト動作）
        holiday_count = (df['holiday_type'] != '通常勤務').sum()
        if holiday_count > 0:
            analysis_logger.info(f"[RestExclusion] {context}: 休暇レコード保持: {holiday_count}件 (exclude_leave_records=False)")
    
    final_count = len(df)
    total_excluded = original_count - final_count
    exclusion_rate = total_excluded / original_count if original_count > 0 else 0
    
    analysis_logger.info(f"[RestExclusion] {context}: 完了: {original_count} -> {final_count} (除外: {total_excluded}件, {exclusion_rate:.1%})")
    
    return df


# ────────────────── 3. Excel 日付ユーティリティ ──────────────────
def excel_date(excel_serial: Any) -> dt.date | None:
    """Excel 1900 シリアル or pandas.Timestamp 等 → date"""  #  docstring変更
    if excel_serial in (None, "", np.nan):
        return None
    if isinstance(excel_serial, (datetime, np.datetime64, pd.Timestamp)):
        # pd.Timestamp(...).to_pydatetime() は datetime オブジェクトを返す
        # その日付部分のみを取得するには .date() を呼び出す
        return pd.Timestamp(excel_serial).to_pydatetime().date()  #  .date() を追加
    try:
        base = datetime(1899, 12, 30)  # Excel 起点 (1900-01-00)
        return (base + timedelta(days=float(excel_serial))).date()
    except (ValueError, TypeError):
        return None


def to_hhmm(x: Any) -> str | None:
    """8.5 → '08:30' / '23:45' → '23:45' / Excel シリアルなど柔軟変換"""
    if x in (None, "", np.nan):
        return None
    if isinstance(x, (int, float)) and not math.isnan(x):
        h = int(x)
        m = int(round((x - h) * 60))
        return f"{h:02d}:{m:02d}"
    x_str = str(x).strip()  #  変数名を x_str に変更
    m = re.match(r"^(\d{1,2}):(\d{1,2})$", x_str)
    if m:
        return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
    #  追加: HH:MM:SS 形式も考慮 (秒は切り捨て)
    m_ss = re.match(r"^(\d{1,2}):(\d{1,2}):(\d{1,2})$", x_str)
    if m_ss:
        return f"{int(m_ss.group(1)):02d}:{int(m_ss.group(2)):02d}"
    return None


# ────────────────── 3. ラベル／ファイル名 ──────────────────
def gen_labels(slot: int) -> list[str]:
    """00:00-23:59 を slot 分刻みで HH:MM ラベル化"""
    t = datetime(2000, 1, 1)
    labels: list[str] = []
    while t.day == 1:  # 24h
        labels.append(t.strftime("%H:%M"))
        t += timedelta(minutes=slot)
    return labels


INVALID_CHARS = r"[\\/*?:\[\]]|\n|\r"


def safe_sheet(name: str, *, for_path: bool = False) -> str:
    """Excel シート／ファイル用に危険文字を置換"""
    out = re.sub(INVALID_CHARS, "_", str(name))
    out = out.strip()[:31]  # Excel シートは 31 文字上限
    if for_path:
        out = out.replace(" ", "_")
    return out or "sheet"


def safe_read_excel(fp: Path | str, **kwargs: Any) -> DataFrame:
    """Read an Excel file with basic error handling.

    Parameters
    ----------
    fp : Path | str
        Excel file path.
    **kwargs : Any
        Options forwarded to ``pd.read_excel``.

    Returns
    -------
    DataFrame
        Loaded DataFrame.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        For empty files or other read errors.
    """
    path = Path(fp)
    if not path.exists():
        log.error("Excel file not found: %s", path)
        raise FileNotFoundError(path)
    try:
        return pd.read_excel(path, **kwargs)
    except pd.errors.EmptyDataError as e:
        log.error("Excel file '%s' is empty: %s", path, e)
        raise ValueError(f"Excel file '{path}' is empty") from e
    except Exception as e:  # noqa: BLE001
        log.error("Failed to read Excel file '%s': %s", path, e)
        raise ValueError(f"Failed to read Excel file '{path}': {e}") from e


# ────────────────── 4. DataFrame 保存 ──────────────────
def save_df_xlsx(
    df: DataFrame,
    fp: Path | str,
    sheet_name: str | None = None,
    *,
    index: bool = True,
    engine: str = "openpyxl",
) -> Path:
    """
    汎用 Excel 保存ラッパー
    - 長いパスも一時ファイル経由で安全に保存
    - sheet_name=None → ファイル名を安全化
    """
    fp_path = Path(fp)  #  変数名を fp_path に変更
    final_sheet_name = sheet_name or safe_sheet(
        fp_path.stem
    )  #  変数名を final_sheet_name に変更
    to_excel_kwargs = dict(index=index, sheet_name=final_sheet_name, engine=engine)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, **to_excel_kwargs)
        tmp.flush()  # Ensure all data is written to disk
        # tmp.close() # Close should happen before move on some OS, but pd might handle it.
        # Explicitly closing here might be safer before shutil.move.
        # However, pandas might need the file open if it's not fully flushed.
        # For safety, ensure pandas writer is closed if used, or rely on NamedTemporaryFile's delete=False behavior.
        # pd.ExcelWriter context manager is better if more control is needed.
    # Ensure the target directory exists
    fp_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(tmp.name, fp_path)

    return fp_path


def save_df_parquet(
    df: DataFrame,
    fp: Path | str,
    *,
    index: bool = True,
) -> Path:
    """Save DataFrame to Parquet file."""
    fp_path = Path(fp)
    fp_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(fp_path, index=index)
    return fp_path


# ────────────────── 5. メタファイル ──────────────────
def write_meta(target: Path | str, /, **meta) -> Path:
    """
    JSON メタ情報を書き出し。UTF-8 固定で UnicodeEncodeError を防止。

    Parameters
    ----------
    target : Path | str
        * ディレクトリを渡した場合 → `<dir>/meta.json`
        * ファイルパスを渡した場合 → そのファイルに書き込み
    meta : dict
        書き込むキー＝値
    """
    target_path = Path(target)  #  変数名を target_path に変更
    meta_fp = target_path / "meta.json" if target_path.is_dir() else target_path
    meta_fp.parent.mkdir(parents=True, exist_ok=True)
    # ensure_ascii=False と indent=2 はJSONを見やすくするために良い習慣
    try:
        meta_fp.write_text(
            json.dumps(
                meta, ensure_ascii=False, indent=2, default=str
            ),  #  default=str を追加 (datetime等非シリアライズ可能オブジェクト対策)
            encoding="utf-8",
        )
    except Exception as e:
        log.error(f"Failed to write meta file {meta_fp}: {e}")
        # Optionally, re-raise or handle as appropriate
    return meta_fp


# ────────────────── 6. ZIP ユーティリティ ──────────────────
def safe_make_archive(src_dir: Path, dst_zip: Path) -> Path:
    """Windows 長パス対応付き shutil.make_archive 相当"""
    src_dir_path, dst_zip_path = Path(src_dir), Path(dst_zip)  #  変数名変更
    if dst_zip_path.exists():
        dst_zip_path.unlink()

    with zipfile.ZipFile(dst_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p_item in src_dir_path.rglob("*"):  #  変数名変更
            zf.write(p_item, p_item.relative_to(src_dir_path))
    return dst_zip_path


# ────────────────── 7. スタッフ数閾値計算 ──────────────────
def derive_min_staff(heat: DataFrame | Series, method: str = "p25") -> Series:
    # (既存のロジックのままとします)
    if isinstance(heat, Series):
        if method == "p25":
            return pd.Series([heat.quantile(0.25)]).round()
        if method == "mean-1s":
            return pd.Series([max(0, heat.mean() - heat.std())]).round()
        if method == "mode":
            # mode() can return an empty Series if all values are unique or NaN
            modes = heat.mode()
            return pd.Series([modes.iloc[0] if not modes.empty else np.nan]).round()
        raise ValueError(f"Unknown min_method: {method}")
    else:
        values = heat.select_dtypes(include=np.number)  #  include=np.number に変更
        if values.empty:  # 数値列がない場合
            return pd.Series(dtype=float)  # 空のSeriesを返す
        if method == "p25":
            return values.quantile(0.25, axis=1).round()
        if method == "mean-1s":
            return (values.mean(axis=1) - values.std(axis=1)).clip(lower=0).round()
        if method == "mode":
            # DataFrame.mode() can also result in multiple rows if multiple modes exist for a row
            # Taking the first mode found for each row.
            modes_df = values.mode(axis=1)
            return (
                modes_df.iloc[:, 0].round()
                if not modes_df.empty
                else pd.Series(index=values.index, dtype=float).fillna(np.nan)
            )
        raise ValueError(f"Unknown min_method: {method}")  #  max_method -> min_method


def derive_max_staff(heat: DataFrame | Series, method: str = "mean+1s") -> Series:
    # (既存のロジックのままとします)
    if isinstance(heat, Series):
        if method == "mean+1s":
            std_val = heat.std()
            if pd.isna(std_val):
                std_val = 0
            return pd.Series([heat.mean() + std_val]).round()
        if method == "p75":
            return pd.Series([heat.quantile(0.75)]).round()
        raise ValueError(f"Unknown max_method: {method}")
    else:
        values = heat.select_dtypes(include=np.number)  #  include=np.number に変更
        if values.empty:  # 数値列がない場合
            return pd.Series(dtype=float)
        if method == "mean+1s":
            mu = values.mean(axis=1)
            sig = values.std(axis=1).fillna(0)  # NaN→0
            return (mu + sig).round()
        if method == "p75":
            return values.quantile(0.75, axis=1).round()
        raise ValueError(f"Unknown max_method: {method}")


# ────────────────── 8. Jain 指数計算 ──────────────────
def calculate_jain_index(values: pd.Series) -> float:
    """分布の公平性を評価する Jain 指数 (0-1)。1 が完全公平"""
    # Ensure the series contains numeric data and handle NaNs
    numeric_values = pd.to_numeric(values, errors="coerce").dropna()
    if (
        numeric_values.empty or len(numeric_values) == 0
    ):  #  len(numeric_values) == 0 もチェック
        return 1.0  # Consider what to return for empty or all-NaN series
    if (
        numeric_values < 0
    ).any():  # Jain index is typically for non-negative resource allocation
        log.warning(
            "Jain index calculation: input series contains negative values. Results may be misleading."
        )

    # (sum of all values)^2 / (number of values * sum of squares of all values)
    sum_of_values_sq = (numeric_values.sum()) ** 2
    sum_of_squares = (numeric_values**2).sum()

    if sum_of_squares == 0:  # Avoid division by zero if all values are zero
        return (
            1.0 if numeric_values.nunique() <= 1 else 0.0
        )  # All zero is fair, multiple zeros and some non-zeros is not max fair.
        # If all are zero, it's perfectly fair in one sense.

    return round(sum_of_values_sq / (len(numeric_values) * sum_of_squares), 3)


# 追加箇所: _parse_as_date 関数の定義 (build_stats.py から移設)
def _parse_as_date(column_name: Any) -> dt.date | None:
    """列名を日付オブジェクトにパース試行。失敗時は None"""
    # 🔍 【追加】パース過程のデバッグログ（必要に応じて有効化）
    # log.debug(f"[DATE_PARSE] パース試行: '{column_name}' (型: {type(column_name)})")

    result: dt.date | None = None
    if isinstance(column_name, (dt.date, dt.datetime, pd.Timestamp)):
        if isinstance(column_name, pd.Timestamp):
            result = column_name.date()
        elif isinstance(column_name, dt.datetime):
            result = column_name.date()
        else:
            result = column_name
    elif isinstance(column_name, str):
        if column_name.lower() in [s.lower() for s in SUMMARY5]:
            result = None
        else:
            m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", column_name)
            if m:
                try:
                    result = pd.to_datetime(m.group(1), errors="raise").date()
                except (ValueError, TypeError, pd.errors.ParserError):
                    result = None
            if result is None:
                try:
                    result = pd.to_datetime(column_name.split(" ")[0], errors="raise").date()
                except (ValueError, TypeError, pd.errors.ParserError):
                    try:
                        if "." in column_name:
                            excel_serial = float(column_name)
                        else:
                            excel_serial = int(column_name)
                        if 0 < excel_serial < 200000:
                            result = (datetime(1899, 12, 30) + timedelta(days=excel_serial)).date()
                    except ValueError:
                        result = None
    elif isinstance(column_name, (int, float)):
        try:
            if column_name > 0 and column_name < 200000:
                result = (datetime(1899, 12, 30) + timedelta(days=int(column_name))).date()
        except (ValueError, OverflowError, TypeError):
            result = None
    if result and result.weekday() == 6:
        log.debug(f"[DATE_PARSE] 日曜日を検出: {column_name} → {result}")
    return result


# ────────────────── 8. Date + Weekday Helpers ──────────────────
def date_with_weekday(date_val: Any) -> str:
    """Return ``YYYY-MM-DD(曜日)`` for the given date string."""

    try:
        dt_val = pd.to_datetime(date_val, errors="raise")
    except Exception:  # noqa: BLE001 - parse failure
        return str(date_val)
    weekday_jp = "月火水木金土日"[dt_val.weekday()]
    return dt_val.strftime("%Y-%m-%d") + f"({weekday_jp})"


def validate_need_calculation(
    need_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    tolerance_factor: float = 3.0,
) -> Dict[str, Any]:
    """Validate need calculation results."""

    validation_results = {
        "status": "PASS",
        "warnings": [],
        "errors": [],
        "statistics": {},
    }

    for column in need_df.columns:
        if column in actual_df.columns:
            need_total = need_df[column].sum()
            actual_total = actual_df[column].sum()

            if actual_total > 0 and need_total > actual_total * tolerance_factor:
                warning_msg = (
                    f"{column}: Need({need_total:.1f})が実績({actual_total:.1f})の{tolerance_factor}倍を超過"
                )
                validation_results["warnings"].append(warning_msg)
                validation_results["status"] = "WARNING"
                log.warning(f"[VALIDATION_WARN] {warning_msg}")

            validation_results["statistics"][column] = {
                "need_total": need_total,
                "actual_total": actual_total,
                "ratio": need_total / actual_total if actual_total > 0 else float("inf"),
            }

    return validation_results


def log_need_calculation_summary(
    need_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    method: str,
) -> None:
    """Log summary of need calculation."""

    log.info(f"[NEED_SUMMARY] ========== Need計算サマリー ({method}) ==========")

    dow_names = ["月", "火", "水", "木", "金", "土", "日"]

    for column in need_df.columns:
        if column in actual_df.columns:
            date_obj = _parse_as_date(column)
            if date_obj:
                dow_name = dow_names[date_obj.weekday()]
                need_total = need_df[column].sum()
                actual_total = actual_df[column].sum()
                log.info(
                    f"[NEED_SUMMARY] {column}({dow_name}): Need={need_total:.1f}, 実績={actual_total:.1f}"
                )


# ────────────────── 9. DataFrame Validation ──────────────────
def _valid_df(df: pd.DataFrame) -> bool:
    """Return True if df is a non-empty pandas DataFrame."""
    return isinstance(df, pd.DataFrame) and not df.empty


# ────────────────── 10. Public Re-export ──────────────────
__all__: Sequence[str] = [
    "log",
    "excel_date",
    "to_hhmm",
    "gen_labels",
    "safe_sheet",
    "safe_read_excel",
    "save_df_xlsx",
    "save_df_parquet",
    "write_meta",
    "safe_make_archive",
    "derive_min_staff",
    "derive_max_staff",
    "calculate_jain_index",
    "_parse_as_date",  # 追加
    "_valid_df",       # 統合追加
    "date_with_weekday",
    "validate_need_calculation",
    "log_need_calculation_summary",
]
