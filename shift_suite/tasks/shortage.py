"""
shift_suite.tasks.shortage  v1.3.1 – 不足人数サマリ
─────────────────────────────────────────────────────
* heat_ALL.xlsx → shortage_time.xlsx（時間×日付の不足）
* heat_*        → shortage_role.xlsx（職種別 KPI）
* heat_* が 0 件でも空シートを保存
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from .utils import derive_min_staff, gen_labels, log, save_df_xlsx


# ═══════════════════════ Main API ═══════════════════════
def shortage_and_brief(
    out_dir: Path,
    slot: int,
    *,
    min_method: str = "mean-1s",
    need_col: str = "need",
) -> Tuple[Path, Path]:
    """
    out_dir  : OUT フォルダ
    slot     : インターバル（分）
    Returns  : (shortage_time.xlsx, shortage_role.xlsx)
    """
    out_dir = Path(out_dir)
    labels = gen_labels(slot)

    # ─── 全体ヒートマップ ───
    heat_fp = out_dir / "heat_ALL.xlsx"
    if not heat_fp.exists():
        raise FileNotFoundError(f"{heat_fp} が見つかりません")
    heat = pd.read_excel(heat_fp, index_col=0)

    need_ser = heat[need_col]
    staff_df = heat.loc[:, heat.columns.difference(
        ["need", "upper", "staff", "lack", "excess"]
    )]
    staff_sum = staff_df.groupby(level=0, axis=0).sum()
    lack_df = (need_ser - staff_sum).clip(lower=0).reindex(labels)

    time_fp = save_df_xlsx(lack_df, out_dir / "shortage_time.xlsx")

    # ─── 職種別 KPI ───
    role_rows = []
    for heat_p in out_dir.glob("heat_*.xlsx"):
        if heat_p.name == "heat_ALL.xlsx":
            continue
        role = heat_p.stem.replace("heat_", "")
        h = pd.read_excel(heat_p, index_col=0)
        need = derive_min_staff(h, min_method).sum()
        staff = h.sum().sum()
        role_rows.append({
            "role": role,
            "need_h": need,
            "staff_h": staff,
            "lack_h": max(need - staff, 0),
        })

    # 空でも列は保持
    if role_rows:
        role_df = (
            pd.DataFrame(role_rows)
              .sort_values("lack_h", ascending=False)
              .reset_index(drop=True)
        )
    else:
        role_df = pd.DataFrame(columns=["role", "need_h", "staff_h", "lack_h"])

    role_fp = save_df_xlsx(role_df, out_dir / "shortage_role.xlsx", sheet_name="role")

    log.info(f"[shortage] shortage_time → {time_fp.name}, shortage_role → {role_fp.name}")
    return time_fp, role_fp


__all__ = ["shortage_and_brief"]
