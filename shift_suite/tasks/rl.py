"""
shift_suite.tasks.rl  v0.3.2 – PPO によるシフト生成（stub）
────────────────────────────────────────────────────────
* 需要系列 CSV → ロスター最適化
* 2025-05-01 : `need` ⇆ `y` フォールバック、meta 出力などを復元
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from .utils import log, save_df_xlsx, write_meta


# ═════════════════ Main ═════════════════
def learn_roster(
    demand_csv: Path,
    excel_out: Path,
    *,
    horizon: int = 14,
) -> Path | None:
    """
    需要 CSV（ds, need|y）を読み込み、簡易 PPO でロスターを生成する *デモ実装*。

    実装メモ
    --------
    - 本関数はアルゴリズム枠のみ提供。実務ロジックと置き換えて利用してください。
    - `horizon` : 学習／予測対象期間（現 stub では未使用）。
    """
    log.info("[rl] learn_roster start")

    df = pd.read_csv(demand_csv, parse_dates=["ds"])

    # --- 需要列を柔軟に取得 ---------------------------
    if "need" in df.columns:
        need = df["need"].values
    elif "y" in df.columns:                           # build_demand_series のデフォルト
        need = df["y"].values
        warnings.warn("[rl] `need` 列が無かったため `y` 列を使用しました（forecast 由来）")
    else:
        log.warning("[rl] 需要列 (`need` または `y`) が見つからず学習をスキップ")
        return None

    if len(need) < 2 or need.sum() == 0:
        log.warning("[rl] 需要データが不足しているため学習をスキップ")
        return None

    # --- ↓ Stub 処理：必要人数を四捨五入してそのまま配置 ----------
    roster = np.round(need).astype(int)

    out_df = pd.DataFrame({"ds": df["ds"], "roster": roster})
    save_df_xlsx(out_df, excel_out, sheet_name="rl_roster")

    # meta
    write_meta(
        excel_out.with_suffix(".meta.json"),
        note="stub – roster = round(need)",
        horizon=horizon,
        rows=len(df),
    )

    log.info(f"[rl] roster saved → {excel_out}")
    return excel_out


# ═════════════════ __all__ ═════════════════
__all__ = ["learn_roster"]
