"""
build_stats.py ― KPI 集約＋全体／月別集計
----------------------------------------

* 初回実行時 stats.xlsx が無ければ新規作成（mode='w'）
* 2 回目以降は追記（mode='a'）
* 月別集計は列ラベルが DatetimeIndex / Excel シリアル / 文字列
  いずれでも柔軟に月番号を抽出
* 主要ステップごとに詳細ログを出力（DEBUG/INFO レベル）
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

# --------------------------------------------------------------------------- #
# ロガー設定
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
if not logger.handlers:  # スクリプト二重読み込み時の重複ハンドラ対策
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)  # DEBUG まで出力


# --------------------------------------------------------------------------- #
# 内部ユーティリティ
# --------------------------------------------------------------------------- #
def _to_month(value) -> int | None:
    """列ラベルから月番号 (1‒12) を抽出。失敗時は None"""
    try:
        # Timestamp / datetime.date
        if isinstance(value, (pd.Timestamp, dt.date, dt.datetime)):
            return value.month

        # Excel シリアル (1900系)
        if isinstance(value, (int, float)):
            ts = pd.to_datetime("1899-12-30") + pd.to_timedelta(int(value), "D")
            return ts.month

        # 文字列 ('2025-04-01', '4/1', '20250401'…)
        if isinstance(value, str):
            ts = pd.to_datetime(value, errors="coerce")
            return ts.month if not pd.isna(ts) else None

        return None
    except Exception as e:  # pragma: no cover
        logger.debug(f"_to_month: failed to parse {value!r}: {e}")
        return None


def _check_files_exist(out_dir: Path, required: Iterable[str]) -> List[str]:
    """必要ファイルが存在するか確認し、欠損リストを返す"""
    missing = [f for f in required if not (out_dir / f).exists()]
    if missing:
        logger.error(f"Missing upstream outputs: {missing}")
    else:
        logger.debug("All required upstream files exist.")
    return missing


# --------------------------------------------------------------------------- #
# メイン関数
# --------------------------------------------------------------------------- #
def build_stats(out_dir: str | Path, *, need_col: str = "need") -> None:
    """
    ① Overall_Summary
    ② Monthly_Summary
    の 2 シートを stats.xlsx に書き込む。

    Parameters
    ----------
    out_dir : str | Path
        一時出力ディレクトリ
    need_col : str, default "need"
        heat_ALL.xlsx に含まれる不足列プレフィクス
    """

    out_dir = Path(out_dir)
    stats_fp = out_dir / "stats.xlsx"

    logger.info(f"=== build_stats start (out_dir={out_dir}) ===")

    # --- 入力ファイル存在チェック -------------------------------------------------
    missing = _check_files_exist(out_dir, ["heat_ALL.xlsx"])
    if missing:
        raise FileNotFoundError(f"Required files not found: {missing}")

    # --- 入力読み込み ------------------------------------------------------------
    logger.debug("Reading heat_ALL.xlsx …")
    heat_all = pd.read_excel(out_dir / "heat_ALL.xlsx", index_col=0)
    logger.debug(f"heat_ALL shape: {heat_all.shape}")

    df_need = heat_all.filter(regex=f"{need_col}.*", axis=1)
    if df_need.empty:
        logger.warning(f"No columns matching '{need_col}' found; skipping stats aggregation.")
        return
    logger.debug(f"Filtered need columns: {list(df_need.columns)[:10]}… total={df_need.shape[1]}")

    # --- Overall_Summary --------------------------------------------------------
    overall = pd.DataFrame(
        {
            "metric": ["total_need", "mean_need_per_slot", "max_need", "min_need"],
            "value": [
                df_need.sum().sum(),
                df_need.mean().mean(),
                df_need.max().max(),
                df_need.min().min(),
            ],
        }
    )
    logger.debug(f"Overall summary calculated: {overall.to_dict(orient='list')}")

    # --- Monthly_Summary --------------------------------------------------------
    month_labels = [_to_month(c) for c in df_need.columns]
    month_series = pd.Series(month_labels, index=df_need.columns, name="month")
    valid_cols = month_series.dropna().index.tolist()

    if not valid_cols:
        logger.warning("No date-like columns detected; Monthly_Summary will be empty.")
        monthly = pd.DataFrame()
    else:
        df_valid = df_need[valid_cols]
        month_series = month_series.loc[valid_cols].astype(int)

        monthly_stats = {}
        for m in sorted(month_series.unique()):
            grp = df_valid.loc[:, month_series == m]
            monthly_stats[m] = {
                "total_need": grp.sum().sum(),
                "mean_need": grp.mean().mean(),
                "max_need": grp.max().max(),
                "min_need": grp.min().min(),
            }
            logger.debug(f"Month {m:02d}: rows={grp.shape[0]} cols={grp.shape[1]}")

        monthly = (
            pd.DataFrame.from_dict(monthly_stats, orient="index")
            .rename_axis("month")
            .sort_index()
        )
        monthly.index = monthly.index.map(lambda x: f"{x:02d}")

    # --- stats.xlsx 書き出し -----------------------------------------------------
    writer_mode = "a" if stats_fp.exists() else "w"

    logger.debug(
        f"Writing to stats.xlsx (path={stats_fp}, mode={writer_mode})"
        + (" — sheet overwrite=replace" if writer_mode == "a" else "")
    )

    # append 時のみ if_sheet_exists を指定
    if writer_mode == "a":
        writer_kwargs = dict(if_sheet_exists="replace")
    else:
        writer_kwargs = {}

    with pd.ExcelWriter(stats_fp, engine="openpyxl", mode=writer_mode, **writer_kwargs) as writer:
        overall.to_excel(writer, sheet_name="Overall_Summary", index=False)
        if not monthly.empty:
            monthly.to_excel(writer, sheet_name="Monthly_Summary")
        else:
            pd.DataFrame({"msg": ["No date-like columns found"]}).to_excel(
                writer, sheet_name="Monthly_Summary", index=False
            )

    logger.info(f"✅ stats.xlsx updated successfully at {stats_fp}")
    logger.info("=== build_stats end ===")
