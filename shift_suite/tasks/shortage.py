"""
shortage.py – v2.1.1  (DEBUG ログ付き)
────────────────────────────────────────────────────────
* ALL シートの不足 (time × date) と
  summary5 列が無い職種ヒートマップでも不足を再計算
* DEBUG ログ:
    - 各 role の need_h / staff_h / lack_h を出力
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, List

import pandas as pd

from .utils import derive_min_staff, gen_labels, log, save_df_xlsx, write_meta

SUMMARY5 = ["need", "upper", "staff", "lack", "excess"]


def shortage_and_brief(
    out_dir: Path | str,
    slot: int,
    *,
    need_col: str = "need",
    min_method: str | None = None,
    max_method: str | None = None,
) -> Tuple[Path, Path]:
    if min_method or max_method:
        log.debug("[shortage] min_method / max_method は v2 系で未使用")

    out_dir = Path(out_dir)
    labels = gen_labels(slot)

    # ── 1. ALL レベル不足 ───────────────────────────────
    fp_all = out_dir / "heat_ALL.xlsx"
    heat_all = pd.read_excel(fp_all, index_col=0)
    staff_df = heat_all.loc[:, heat_all.columns.difference(SUMMARY5)]
    need_ser = heat_all[need_col].clip(lower=1)

    lack_df = (
        staff_df.rsub(need_ser, axis=0)
        .clip(lower=0)
        .reindex(labels)
        .fillna(0)
        .astype(int)
    )

    fp_time = save_df_xlsx(lack_df, out_dir / "shortage_time.xlsx", sheet_name="lack_time")

    # ── 2. 職種別 KPI ───────────────────────────────────
    rows: List[dict] = []

    for fp in out_dir.glob("heat_*.xlsx"):
        if fp.name == "heat_ALL.xlsx":
            continue
        role = fp.stem.replace("heat_", "")
        h = pd.read_excel(fp, index_col=0)

        if set(SUMMARY5).issubset(h.columns):
            need_h = int(h["need"].sum())
            staff_h = int(h["staff"].sum())
            lack_h = int(h["lack"].sum())
        else:
            need_ser_r = derive_min_staff(h).clip(lower=1)
            staff_ser_r = h.sum(axis=1)
            lack_ser_r = (need_ser_r - staff_ser_r).clip(lower=0)

            need_h = int(need_ser_r.sum())
            staff_h = int(staff_ser_r.sum())
            lack_h = int(lack_ser_r.sum())

            log.warning(
                f"[shortage] {fp.name}: summary5 無 → need再計算 "
                f"(need={need_h}, staff={staff_h})"
            )

        rows.append(dict(role=role, need_h=need_h, staff_h=staff_h, lack_h=lack_h))
        log.debug(
            f"[shortage] {role} need_h={need_h} staff_h={staff_h} lack_h={lack_h}"
        )

    role_df = (
        pd.DataFrame(rows)
        .sort_values("lack_h", ascending=False, na_position="last")
        .reset_index(drop=True)
    )

    fp_role = save_df_xlsx(role_df, out_dir / "shortage_role.xlsx", sheet_name="role")

    # ── 3. メタ ─────────────────────────────────────────
    write_meta(
        out_dir / "shortage.meta.json",
        slot=slot,
        dates=staff_df.columns.tolist(),
        roles=role_df["role"].tolist(),
    )

    log.info(
        f"[shortage] completed — shortage_time → {fp_time.name}, "
        f"shortage_role → {fp_role.name}"
    )
    return fp_time, fp_role
