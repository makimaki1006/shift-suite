"""
cost_benefit.py ── “採用 / 派遣 / 漏れ (罰金)” コストを試算するユーティリティ
-------------------------------------------------------------------
入力 : shortage_role.xlsx（不足 h）   hire_plan.xlsx（hire_need）
出力 : cost_benefit.xlsx（シナリオ別比較表）
呼出 : analyze_cost_benefit(out_dir            = Path,
                            wage_direct        = 1500,
                            wage_temp          = 2200,
                            hiring_cost_once   = 180000,
                            penalty_per_lack_h = 4000)
※ すべて GUI スライダー / テキスト入力で動的に変更できるよう引数化
"""

from __future__ import annotations
from pathlib import Path

import pandas as pd


def analyze_cost_benefit(
    out_dir: Path,
    wage_direct: int = 1500,
    wage_temp: int = 2200,
    hiring_cost_once: int = 180_000,
    penalty_per_lack_h: int = 4_000,
) -> pd.DataFrame:
    """
    コストシミュレーションを実施し、Excel ファイルに保存

    Parameters
    ----------
    out_dir : Path
        shortage_role.xlsx / hire_plan.xlsx が置かれている out フォルダ
    wage_direct : int, default 1500
        正社員（常勤換算）1 h あたりの人件費
    wage_temp : int, default 2200
        派遣 / バイト 1 h あたりのコスト
    hiring_cost_once : int, default 180_000
        1 名採用あたりの一時コスト（紹介料・研修など）
    penalty_per_lack_h : int, default 4_000
        不足 1 h あたりのサービス品質ペナルティ（機会損失・行政指導等）

    Returns
    -------
    pd.DataFrame
        シナリオ別コスト比較表
    """
    kpi_fp = out_dir / "shortage_role.xlsx"
    hire_fp = out_dir / "hire_plan.xlsx"

    if not (kpi_fp.exists() and hire_fp.exists()):
        raise FileNotFoundError("必要な KPI / hire_plan ファイルが out フォルダに見つかりません")

    lack = pd.read_excel(kpi_fp)
    plan = pd.read_excel(hire_fp, sheet_name="hire_plan")

    lack_h_total = lack["lack_h"].sum()
    hire_need_total = plan["hire_need"].sum()

    # --- シナリオ試算 ----------------------------------------------------------
    scenarios = {}

    # S0: 何もしない → 派遣＋罰金
    cost_temp = lack_h_total * wage_temp
    cost_penalty = lack_h_total * penalty_per_lack_h
    scenarios["StatusQuo"] = cost_temp + cost_penalty

    # S1: 全部派遣で補填（罰金ゼロ）
    scenarios["FullTemp"] = lack_h_total * wage_temp

    # S2: 採用で補填（不足 h = CFFTE）
    hire_headcount = hire_need_total
    cost_hiring = hire_headcount * hiring_cost_once
    cost_direct_labor = lack_h_total * wage_direct
    scenarios["Hire"] = cost_hiring + cost_direct_labor

    # S3: ハイブリッド（採用 50% + 派遣 50%）
    lack_half = lack_h_total / 2
    hire_half = hire_headcount / 2
    cost_hybrid = (
        hire_half * hiring_cost_once
        + lack_half * wage_direct
        + lack_half * wage_temp
    )
    scenarios["Hybrid50"] = cost_hybrid

    df = (
        pd.Series(scenarios, name="Cost_JPY")
        .to_frame()
        .assign(Cost_Million=lambda d: d["Cost_JPY"] / 1_000_000)
    )

    # Excel 保存
    df.to_excel(out_dir / "cost_benefit.xlsx")

    return df
