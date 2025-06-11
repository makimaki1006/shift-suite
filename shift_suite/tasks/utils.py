# shift_suite/tasks/utils.py
# v1.2.1 ( _parse_as_date 移設)
"""
shift_suite.tasks.utils  v1.2.0 – UTF-8 write_meta 版
────────────────────────────────────────────────────────
* 共通ユーティリティ
* 2025-05-06
    - write_meta(): Windows でも文字化けしないよう `encoding="utf-8"` を明示
      （既定 CP932 だと “–” などの Unicode 文字列で UnicodeEncodeError）
    - 旧 API・関数名は一切変更なし
* 2025-05-16
    - build_stats.py から _parse_as_date を移設
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
from typing import Any, Sequence  #  Any を追加

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from ..logger_config import configure_logging

# 追加箇所: constants から SUMMARY5 をインポート ( _parse_as_date で使用)
from .constants import SUMMARY5

# ────────────────── 1. ロガー ──────────────────
configure_logging()
log = logging.getLogger(__name__)


# ────────────────── 2. Excel 日付ユーティリティ ──────────────────
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
    if isinstance(
        column_name, (dt.date, dt.datetime, pd.Timestamp)
    ):  #  dt.date を先頭に
        # Ensure it's converted to a Python date object
        if isinstance(column_name, pd.Timestamp):
            return column_name.date()
        if isinstance(column_name, dt.datetime):
            return column_name.date()
        return column_name  # dt.date の場合

    if isinstance(column_name, str):
        # SUMMARY5 に含まれる列名は日付ではないと明確に判定
        if column_name.lower() in [s.lower() for s in SUMMARY5]:
            return None

        # まずは YYYY-MM-DD のような部分文字列を正規表現で抽出してみる
        m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", column_name)
        if m:
            try:
                return pd.to_datetime(m.group(1), errors="raise").date()
            except (ValueError, TypeError, pd.errors.ParserError):
                pass

        try:
            # "YYYY-MM-DD HH:MM:SS" のような文字列を想定し、空白で分割して日付部分を抽出
            return pd.to_datetime(column_name.split(" ")[0], errors="raise").date()
        except (ValueError, TypeError, pd.errors.ParserError):
            # Excel日付シリアル値のような文字列 "45321.0" や "45321" もここで処理できるか試す
            try:
                if "." in column_name:  # "45321.0"
                    excel_serial = float(column_name)
                else:  # "45321"
                    excel_serial = int(column_name)
                if 0 < excel_serial < 200000:  # 妥当な範囲
                    return (
                        datetime(1899, 12, 30) + timedelta(days=excel_serial)
                    ).date()
            except ValueError:
                pass  # 文字列から数値への変換失敗
        return None  # 上記でパースできなければ None

    if isinstance(column_name, (int, float)):  # Excelシリアル値
        try:
            # Excelの日付は1899-12-30が0
            # 有効なExcel日付シリアルの範囲を考慮 (例: 1 (1900-01-01) から、現実的な未来の日付まで)
            # Pythonのintやfloatが巨大な場合にOverflowErrorを避ける
            if (
                column_name > 0 and column_name < 200000
            ):  # 200000は約2444年なので十分なはず
                return (
                    datetime(1899, 12, 30) + timedelta(days=int(column_name))
                ).date()
        except (ValueError, OverflowError, TypeError):  # TypeErrorも追加
            return None
    return None


# ────────────────── 8. Date + Weekday Helpers ──────────────────
def date_with_weekday(date_val: Any) -> str:
    """Return ``YYYY-MM-DD(曜日)`` for the given date string."""

    try:
        dt_val = pd.to_datetime(date_val, errors="raise")
    except Exception:  # noqa: BLE001 - parse failure
        return str(date_val)
    weekday_jp = "月火水木金土日"[dt_val.weekday()]
    return dt_val.strftime("%Y-%m-%d") + f"({weekday_jp})"


# ────────────────── 9. Public Re-export ──────────────────
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
    "date_with_weekday",
]
