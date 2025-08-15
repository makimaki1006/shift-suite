"""
shift_suite.summary  v0.3
───────────────────────────────────────────────────────────
  make_summary : Heatmap → 時間帯×職種 別の統計 5 指標
  build_stats  : 長形式シフト → staff_stats.xlsx（個人統計＋要約）
───────────────────────────────────────────────────────────
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from .utils import log


__all__ = ["make_summary", "build_stats"]


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
        return pd.Series(
            {
                "max":    x.max(),
                "min":    x.min(),
                "mean":   x.mean(),
                "median": x.median(),
                "mode":   x.mode().iat[0] if not x.mode().empty else 0,
            }
        )

    if by_role and isinstance(heat_df.columns, pd.MultiIndex):
        # index = (time, role)
        out = (
            heat_df.stack(level=1)
                   .groupby(level=[0, 1])
                   .apply(_stats)
        )
    else:
        # index = time
        out = heat_df.apply(_stats, axis=1)

    return out


# ══════════════════════════════════════════════════════════
def build_stats(long_df: pd.DataFrame, out_dir: Path) -> Path:
    """
    長形式シフト (= ingest_excel が返すもの) から
    * by_staff  : 個人単位の稼働統計
    * summary   : 列方向 5 数要約
    を 2 シート構成の **staff_stats.xlsx** に出力する。

    Returns
    -------
    Path : 保存したファイルパス
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    df = long_df.copy()
    df["is_night"] = df["code"].str.contains("夜", na=False)

    # ---- 個人統計 ----
    staff_df = (
        df.groupby("name")
          .agg(
              total_days     = ("date", "nunique"),
              total_shifts   = ("code", "size"),
              night_shifts   = ("is_night", "sum"),
              distinct_codes = ("code", "nunique"),
          )
    )
    staff_df["night_ratio"] = (staff_df["night_shifts"] /
                               staff_df["total_shifts"]).round(3)

    # ---- 5-number summary ----
    def _five(col: pd.Series) -> pd.Series:
        return pd.Series(
            {
                "max":    col.max(),
                "min":    col.min(),
                "mean":   col.mean(),
                "median": col.median(),
                "mode":   col.mode().iat[0] if not col.mode().empty else 0,
            }
        )

    summary_df = staff_df.apply(_five)

    # ---- 保存 ----
    fp = out_dir / "staff_stats.xlsx"
    with pd.ExcelWriter(fp, engine="openpyxl") as ew:
        staff_df.to_excel(ew, sheet_name="by_staff")
        summary_df.to_excel(ew, sheet_name="summary")

    log.info("[build_stats] staff_stats.xlsx → %s", fp)
    return fp
