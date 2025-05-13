# shift_suite / tasks / heatmap.py  v1.5.0
from __future__ import annotations
from pathlib import Path
import pandas as pd, openpyxl
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.utils import get_column_letter
from .utils import (gen_labels, derive_min_staff, derive_max_staff,
                    save_df_xlsx, write_meta, safe_sheet, log)

STAFF_ALIASES = ["staff", "氏名", "名前", "従業員"]
ROLE_ALIASES  = ["role",  "職種", "役職", "部署"]
SUMMARY5      = ["need", "upper", "staff", "lack", "excess"]

def _resolve(df: pd.DataFrame, prefer: str, aliases: list[str], new: str) -> str:
    if prefer in df.columns:
        df.rename(columns={prefer: new}, inplace=True); return new
    for c in aliases:
        if c in df.columns:
            df.rename(columns={c: new}, inplace=True); return new
    raise KeyError(f"{prefer}/{aliases} 列がありません")

def _apply_colors(fp: Path):
    wb = openpyxl.load_workbook(fp)
    ws = wb.active
    rng = f"B2:{get_column_letter(ws.max_column)}{ws.max_row}"
    ws.conditional_formatting.add(
        rng,
        ColorScaleRule(start_type="min",  start_color="FFFFFF",
                       mid_type="percentile", mid_value=50, mid_color="FFB974",
                       end_type="max",  end_color="FF0000")
    )
    wb.save(fp)

def build_heatmap(long_df: pd.DataFrame, wt_df: pd.DataFrame | None,
                  out_dir: str | Path, slot_minutes: int = 30,
                  *, min_method: str = "p25", max_method: str = "p75") -> None:

    df = long_df.copy()
    staff_col = _resolve(df, "staff", STAFF_ALIASES, "staff")
    role_col  = _resolve(df, "role",  ROLE_ALIASES,  "role")

    df["time"]     = df["ds"].dt.strftime("%H:%M")
    df["date_lbl"] = df["ds"].dt.strftime("%Y-%m-%d")
    idx = gen_labels(slot_minutes)

    pivot_all = (df.drop_duplicates(subset=["date_lbl", "time", staff_col])
                   .pivot_table(index="time", columns="date_lbl",
                                values=staff_col, aggfunc="nunique",
                                fill_value=0)
                   .reindex(idx, fill_value=0))

    need   = derive_min_staff(pivot_all, min_method)
    upper  = derive_max_staff(pivot_all, max_method)
    staff  = pivot_all.sum(axis=1).round()
    lack   = (need  - staff).clip(lower=0)
    excess = (staff - upper).clip(lower=0)

    for c, s in zip(SUMMARY5, [need, upper, staff, lack, excess]):
        pivot_all[c] = s

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    fp_all = out_dir / "heat_ALL.xlsx"
    save_df_xlsx(pivot_all, fp_all, sheet_name="ALL"); _apply_colors(fp_all)

    for role in sorted(set(df[role_col])):
        sub = df[df[role_col] == role]
        p = (sub.drop_duplicates(subset=["date_lbl", "time", staff_col])
                .pivot_table(index="time", columns="date_lbl",
                             values=staff_col, aggfunc="nunique",
                             fill_value=0)
                .reindex(idx, fill_value=0)
                .reindex(columns=pivot_all.columns, fill_value=0))
        need_r   = derive_min_staff(p, min_method)
        upper_r  = derive_max_staff(p, max_method)
        staff_r  = p.sum(axis=1).round()
        lack_r   = (need_r  - staff_r).clip(lower=0)
        excess_r = (staff_r - upper_r).clip(lower=0)
        for c, s in zip(SUMMARY5, [need_r, upper_r, staff_r, lack_r, excess_r]):
            p[c] = s
        fp = out_dir / f"heat_{safe_sheet(str(role))}.xlsx"
        save_df_xlsx(p, fp, sheet_name=str(role)); _apply_colors(fp)

    write_meta(out_dir / "heatmap.meta.json",
               slot=slot_minutes,
               roles=sorted(set(df[role_col])),
               dates=sorted(pivot_all.columns.tolist()))
    log.info("[heatmap] completed")
