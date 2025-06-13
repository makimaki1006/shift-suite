"""
hire_plan.py  ── “必要な採用人数” を算出するユーティリティ
-------------------------------------------------------------
入力 : demand_series.csv（1 時間粒度 ─ y 列が必要人数）
出力 : hire_plan.parquet  （職種ごとの不足 h ・必要採用数）
呼出 : build_hire_plan(csv_path       = Path,
                        out_path       = Path,
                        std_work_hours = 160,   # 月あたり所定労働時間
                        safety_factor  = 1.10,  # 安全係数（不足時間に乗算する倍率。例:1.10は10%増）
                        target_coverage= 0.95)  # シフト充足率の目標
"""

from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd

log = logging.getLogger(__name__)


def build_hire_plan(
    csv_path: Path,
    out_path: Path,
    std_work_hours: int = 160,
    safety_factor: float = 1.10,
    target_coverage: float = 0.95,
) -> pd.DataFrame:
    """
    シフト需要系列（demand_series.csv）から不足時間 → 必要採用人数を算出

    Parameters
    ----------
    csv_path : Path
        demand_series.csv のパス（列: ds, role, y など）
    out_path : Path
        hire_plan.parquet の保存先
    std_work_hours : int, default 160
        月あたりの所定労働時間 [h]（24 日 × 8 h など）
        GUI から動的入力する場合は引数で渡す
    safety_factor : float, default 1.10
        需要変動などを考慮した“安全在庫”係数
        例）1.10 → 10% 多めに人員を確保
    target_coverage : float, default 0.95
        これから確保したい充足率（95% など）

    Returns
    -------
    pd.DataFrame
        role / lack_h / hire_need などを含む DF
    """
    # 1. データ読み込み
    df = pd.read_csv(csv_path, parse_dates=["ds"])
    if "role" not in df.columns:
        df["role"] = "all"

    # 2. 不足時間の集計
    df["lack_h"] = df["y"].clip(lower=0)  # y が不足人数 (>=0) を想定
    summary = (
        df.groupby("role", as_index=False)["lack_h"]
        .sum(numeric_only=True)
        .rename(columns={"lack_h": "lack_h_total"})
    )

    # 3. 必要採用人数 = 不足時間 / 所定労働時間 / target_coverage
    #    × 安全係数（倍率として適用し、切り上げ）
    summary["hire_need"] = (
        (summary["lack_h_total"] * safety_factor) / (std_work_hours * target_coverage)
    ).apply(lambda x: int(-(-x // 1)))  # 天井関数 (ceil)

    # 4. 保存
    summary.to_parquet(out_path, index=False)
    meta = {
        "std_work_hours": std_work_hours,
        "safety_factor": safety_factor,
        "target_coverage": target_coverage,
    }
    meta_fp = out_path.with_name(out_path.stem + "_meta.parquet")
    pd.DataFrame(meta, index=[0]).to_parquet(meta_fp, index=False)

    # text summary
    summary_fp = out_path.with_suffix(".txt")
    try:
        lines = [f"total_hire_need: {int(summary['hire_need'].sum())}"]
        summary_fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.warning("Failed to write summary %s: %s", summary_fp, e)

    return summary
