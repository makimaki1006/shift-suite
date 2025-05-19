"""
shift_suite.summary  v0.3.1 (KeyError: 'name' 対応)
───────────────────────────────────────────────────────────
  make_summary : Heatmap → 時間帯×職種 別の統計 5 指標
  build_staff_stats  : 長形式シフト → staff_stats.xlsx（個人統計＋要約）
───────────────────────────────────────────────────────────
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from .utils import log


__all__ = ["make_summary", "build_staff_stats"]


# ══════════════════════════════════════════════════════════
def make_summary(heat_df: pd.DataFrame, by_role: bool = False) -> pd.DataFrame:
    """
    Heatmap (index=time, columns=date or (date,role)) から
    5 数要約 [max/min/mean/median/mode] を返す。

    Parameters
    ----------
    heat_df : DataFrame
        index=time ('HH:MM'), columns=date  または MultiIndex(date,role)
    by_role : bool, default False
        True の場合 MultiIndex 列を role ごとに分解して集計

    Returns
    -------
    DataFrame
        index=time  または (time,role)
        columns=['max','min','mean','median','mode']
    """
    if heat_df.empty:
        log.warning("make_summary: empty heat_df → returns empty DF")
        return pd.DataFrame()

    def _stats(x: pd.Series) -> pd.Series:
        x = x.dropna()
        if x.empty: # dropna後に空になる場合
            return pd.Series({
                "max":    pd.NA, "min":    pd.NA, "mean":   pd.NA,
                "median": pd.NA, "mode":   pd.NA
            })
        return pd.Series(
            {
                "max":    x.max(),
                "min":    x.min(),
                "mean":   x.mean(),
                "median": x.median(),
                "mode":   x.mode().iat[0] if not x.mode().empty else pd.NA, # 0ではなくNA
            }
        )

    if by_role and isinstance(heat_df.columns, pd.MultiIndex):
        # index = (time, role)
        out = (
            heat_df.stack(level=1) # roleをindexに移動
                   .groupby(level=[heat_df.index.name, heat_df.columns.names[1]]) # timeとroleでグループ化
                   .apply(_stats, include_groups=False) # include_groups=False for pandas >= 2.0
        )
    else:
        # index = time
        out = heat_df.apply(_stats, axis=1)

    return out


# ══════════════════════════════════════════════════════════
def build_staff_stats(long_df: pd.DataFrame, out_dir: Path) -> Path:
    """
    長形式シフト (= ingest_excel が返すもの) から
    * by_staff  : 個人単位の稼働統計
    * summary   : 列方向 5 数要約
    を 2 シート構成の **staff_stats.xlsx** に出力する。

    Parameters
    ----------
    long_df : pd.DataFrame
        長形式シフトデータ (列: ds, staff, role, code など)
    out_dir : Path
        出力ディレクトリ

    Returns
    -------
    Path : 保存したファイルパス
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "staff_stats.xlsx"

    if "staff" not in long_df.columns or "code" not in long_df.columns or "ds" not in long_df.columns:
        log.error("[build_staff_stats] long_dfに必要な列 (staff, code, ds) が不足しています。")
        # 空のExcelファイルを作成して早期リターン
        with pd.ExcelWriter(fp, engine="openpyxl") as ew:
            pd.DataFrame().to_excel(ew, sheet_name="by_staff")
            pd.DataFrame().to_excel(ew, sheet_name="summary")
        return fp

    df = long_df.copy()
    # 'ds' 列を datetime 型に変換 (もし文字列なら)
    df["ds"] = pd.to_datetime(df["ds"])
    df["date"] = df["ds"].dt.date # 日付のみの列を追加
    df["is_night"] = df["code"].str.contains("夜", na=False)

    # ---- 個人統計 ----
    # スタッフ識別列を "name" から "staff" に変更
    staff_df = (
        df.groupby("staff")
          .agg(
              total_days     = ("date", "nunique"), # 日付列を使用
              total_shifts   = ("code", "size"),    # シフトレコード数
              night_shifts   = ("is_night", "sum"),
              distinct_codes = ("code", "nunique"),
          )
    )
    # total_shiftsが0の場合のZeroDivisionErrorを避ける
    staff_df["night_ratio"] = (staff_df["night_shifts"] /
                               staff_df["total_shifts"].replace(0, pd.NA)).fillna(0).round(3)

    # ---- 5-number summary ----
    def _five(col: pd.Series) -> pd.Series:
        if col.empty or col.isnull().all(): # 空または全てNAの列の場合
            return pd.Series({
                "max": pd.NA, "min": pd.NA, "mean": pd.NA,
                "median": pd.NA, "mode": pd.NA
            })
        # 数値型でない場合は統計量を計算できないため、数値型のみを対象とするか、エラーハンドリングが必要
        if not pd.api.types.is_numeric_dtype(col):
            log.warning(f"[build_staff_stats] _five: 数値型でない列 '{col.name}' の統計量は計算できません。")
            return pd.Series({
                "max": pd.NA, "min": pd.NA, "mean": pd.NA,
                "median": pd.NA, "mode": pd.NA
            })

        return pd.Series(
            {
                "max":    col.max(),
                "min":    col.min(),
                "mean":   col.mean(),
                "median": col.median(),
                "mode":   col.mode().iat[0] if not col.mode().empty else pd.NA, # 0ではなくNA
            }
        )

    # staff_df の数値列に対してのみ _five を適用
    numeric_cols_staff_df = staff_df.select_dtypes(include=np.number).columns
    if not numeric_cols_staff_df.empty:
        summary_df = staff_df[numeric_cols_staff_df].apply(_five)
    else:
        summary_df = pd.DataFrame() # 数値列がない場合は空のDataFrame


    # ---- 保存 ----
    with pd.ExcelWriter(fp, engine="openpyxl") as ew:
        staff_df.to_excel(ew, sheet_name="by_staff")
        summary_df.to_excel(ew, sheet_name="summary")

    log.info(f"[build_staff_stats] staff_stats.xlsx → {fp}")
    return fp
