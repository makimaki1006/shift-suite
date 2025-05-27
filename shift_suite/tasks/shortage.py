"""
shortage.py – v2.4.1 (休業日対応のデバッグ強化)
────────────────────────────────────────────────────────
* v2.3.0: SUMMARY5列参照・計算ロジック修正・constants参照
* v2.4.0: heatmap.meta.json から推定休業日を読み込み、need計算に反映。
* v2.4.1: 職種別KPIの稼働日数考慮とデバッグログ強化。
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, List, Dict, Any, Set, Iterable
import json
import datetime as dt

import pandas as pd
import numpy as np

from .utils import gen_labels, log, save_df_xlsx, write_meta, _parse_as_date
from .constants import SUMMARY5

def shortage_and_brief(
    out_dir: Path | str,
    slot: int,
    *,
    holidays_global: Iterable[dt.date] | None = None,
    holidays_local: Iterable[dt.date] | None = None,
    holidays: Iterable[dt.date] | None = None,
) -> Tuple[Path, Path] | None:
    """Run shortage analysis and KPI summary.

    Parameters
    ----------
    out_dir:
        Output directory containing heatmap files.
    slot:
        Slot size in minutes.
    holidays_global:
        Dates for globally observed holidays.
    holidays_local:
        Additional local or facility specific holidays.
    holidays:
        Legacy single holiday list; combined with the above.
    """
    out_dir_path = Path(out_dir)
    time_labels = gen_labels(slot)
    slot_hours = slot / 60.0

    estimated_holidays_set: Set[dt.date] = set()
    for src in (holidays_global, holidays_local, holidays):
        if src:
            estimated_holidays_set.update(src)
    heatmap_meta_path = out_dir_path / "heatmap.meta.json"
    try:
        with open(heatmap_meta_path, 'r', encoding='utf-8') as f:
            heatmap_meta_data = json.load(f)
        holiday_date_strings = heatmap_meta_data.get("estimated_holidays", [])
        if holiday_date_strings:
            for date_str_val in holiday_date_strings:
                try:
                    estimated_holidays_set.add(dt.date.fromisoformat(date_str_val))
                except ValueError:
                    log.warning(f"[shortage] heatmap.meta.json 内の休業日 '{date_str_val}' のISO日付パースに失敗しました。")
        if estimated_holidays_set:
            log.info(f"[shortage] 読み込んだ推定休業日 ({len(estimated_holidays_set)}日): {sorted(list(estimated_holidays_set))}")
        else:
            log.info("[shortage] heatmap.meta.json に有効な推定休業日の情報はありませんでした。")
    except Exception as e:
        log.error(f"[shortage] {heatmap_meta_path} の処理中にエラー: {e}。休業日考慮なしで処理を続行します。", exc_info=True)

    fp_all_heatmap = out_dir_path / "heat_ALL.xlsx"
    if not fp_all_heatmap.exists():
        log.error(f"[shortage] heat_ALL.xlsx が見つかりません: {fp_all_heatmap}")
        return None
    try:
        heat_all_df = pd.read_excel(fp_all_heatmap, index_col=0)
    except Exception as e:
        log.error(f"[shortage] heat_ALL.xlsx の読み込み中にエラー: {e}", exc_info=True)
        return None

    date_columns_in_heat_all = [str(col) for col in heat_all_df.columns if col not in SUMMARY5 and _parse_as_date(str(col)) is not None]
    if not date_columns_in_heat_all:
        log.warning("[shortage] heat_ALL.xlsx に日付データ列が見つかりませんでした。")
        # 空のExcelを生成して返す
        empty_df = pd.DataFrame(index=time_labels)
        fp_s_t_empty = save_df_xlsx(empty_df, out_dir_path / "shortage_time.xlsx", sheet_name="lack_time", index=True)
        fp_s_r_empty = save_df_xlsx(pd.DataFrame(), out_dir_path / "shortage_role.xlsx", sheet_name="role_summary", index=False)
        save_df_xlsx(empty_df, out_dir_path / "shortage_freq.xlsx", sheet_name="freq_by_time", index=True)
        return fp_s_t_empty, fp_s_r_empty if fp_s_t_empty and fp_s_r_empty else None


    staff_actual_data_all_df = heat_all_df[date_columns_in_heat_all].copy().reindex(index=time_labels).fillna(0)

    if 'need' not in heat_all_df.columns:
        log.error("[shortage] heat_ALL.xlsx に 'need' 列 (集計列) が見つかりません。")
        return None
    need_series_per_time_overall_orig = heat_all_df['need'].reindex(index=time_labels).fillna(0).clip(lower=0)

    parsed_date_list_all = [_parse_as_date(c) for c in staff_actual_data_all_df.columns]
    holiday_mask_all = [d in estimated_holidays_set if d else False for d in parsed_date_list_all]
    need_df_all = pd.DataFrame(
        np.repeat(need_series_per_time_overall_orig.values[:, np.newaxis], len(staff_actual_data_all_df.columns), axis=1),
        index=need_series_per_time_overall_orig.index,
        columns=staff_actual_data_all_df.columns
    )
    if any(holiday_mask_all):
        for col, is_h in zip(need_df_all.columns, holiday_mask_all):
            if is_h:
                need_df_all[col] = 0

    lack_count_overall_df = (need_df_all - staff_actual_data_all_df).clip(lower=0).fillna(0).astype(int)
    shortage_ratio_df = ((need_df_all - staff_actual_data_all_df) / need_df_all.replace(0, np.nan)).clip(lower=0).fillna(0)

    fp_shortage_time = save_df_xlsx(lack_count_overall_df, out_dir_path / "shortage_time.xlsx", sheet_name="lack_time", index=True)
    fp_shortage_ratio = save_df_xlsx(shortage_ratio_df, out_dir_path / "shortage_ratio.xlsx", sheet_name="lack_ratio", index=True)

    lack_occurrence_df = (lack_count_overall_df > 0).astype(int)
    shortage_freq_df = pd.DataFrame(lack_occurrence_df.sum(axis=1), columns=["shortage_days"])
    fp_shortage_freq = save_df_xlsx(shortage_freq_df, out_dir_path / "shortage_freq.xlsx", sheet_name="freq_by_time", index=True)

    log.debug(
        "--- shortage_time.xlsx / shortage_ratio.xlsx / shortage_freq.xlsx 計算デバッグ (全体) 終了 ---"
    )

    role_kpi_rows: List[Dict[str, Any]] = []
    monthly_role_rows: List[Dict[str, Any]] = []
    processed_role_names_list = []

    for fp_role_heatmap_item in out_dir_path.glob("heat_*.xlsx"):
        if fp_role_heatmap_item.name == "heat_ALL.xlsx":
            continue
        
        role_name_current = fp_role_heatmap_item.stem.replace("heat_", "")
        processed_role_names_list.append(role_name_current)
        log.debug(f"--- shortage_role.xlsx 計算デバッグ (職種: {role_name_current}) ---")
        
        try:
            role_heat_current_df = pd.read_excel(fp_role_heatmap_item, index_col=0)
        except Exception as e_role_heat:
            log.warning(f"[shortage] 職種別ヒートマップ '{fp_role_heatmap_item.name}' の読み込みエラー: {e_role_heat}")
            role_kpi_rows.append({"role": role_name_current, "need_h": 0, "staff_h": 0, "lack_h": 0, "working_days_considered":0, "note": "heatmap read error"})
            continue

        if 'need' not in role_heat_current_df.columns:
            log.warning(f"[shortage] 職種 '{role_name_current}' のヒートマップに 'need' 列が不足。KPI計算スキップ。")
            role_kpi_rows.append({"role": role_name_current, "need_h": 0, "staff_h": 0, "lack_h": 0, "working_days_considered":0, "note": "missing need column"})
            continue
        role_need_per_time_series_orig_for_role = role_heat_current_df['need'].reindex(index=time_labels).fillna(0).clip(lower=0)

        role_date_columns_list = [str(col) for col in role_heat_current_df.columns if col not in SUMMARY5 and _parse_as_date(str(col)) is not None]
        if not role_date_columns_list:
            log.warning(f"[shortage] 職種 '{role_name_current}' のヒートマップに日付列がありません。KPI計算をスキップします。")
            role_kpi_rows.append({"role": role_name_current, "need_h": 0, "staff_h": 0, "lack_h": 0, "working_days_considered":0, "note": "no date columns"})
            continue
        
        role_staff_actual_data_df = role_heat_current_df[role_date_columns_list].copy().reindex(index=time_labels).fillna(0)

        parsed_role_dates = [_parse_as_date(c) for c in role_staff_actual_data_df.columns]
        holiday_mask_role = [d in estimated_holidays_set if d else False for d in parsed_role_dates]

        need_df_role = pd.DataFrame(
            np.repeat(role_need_per_time_series_orig_for_role.values[:, np.newaxis], len(role_staff_actual_data_df.columns), axis=1),
            index=role_need_per_time_series_orig_for_role.index,
            columns=role_staff_actual_data_df.columns
        )
        if any(holiday_mask_role):
            for c, is_h in zip(need_df_role.columns, holiday_mask_role):
                if is_h:
                    need_df_role[c] = 0

        working_cols_role = [c for c, is_h in zip(role_staff_actual_data_df.columns, holiday_mask_role) if not is_h and _parse_as_date(c)]
        num_working_days_for_current_role = len(working_cols_role)
        total_need_slots_for_role_working_days = role_need_per_time_series_orig_for_role.sum() * num_working_days_for_current_role

        role_lack_count_for_specific_role_df = (need_df_role - role_staff_actual_data_df).clip(lower=0)
        
        total_need_hours_for_role = total_need_slots_for_role_working_days * slot_hours
        # staff_h は全日の実績で計算（休業日も実績0として含まれる）
        total_staff_hours_for_role = role_staff_actual_data_df.sum().sum() * slot_hours
        # lack_h は休業日のneed=0を考慮したlackの合計
        total_lack_hours_for_role = role_lack_count_for_specific_role_df.sum().sum() * slot_hours

        # 月別不足h集計
        try:
            lack_by_date = role_lack_count_for_specific_role_df.sum()
            lack_by_date.index = pd.to_datetime(lack_by_date.index)
            lack_month = lack_by_date.groupby(lack_by_date.index.to_period("M")).sum() * slot_hours
            for mon, val in lack_month.items():
                monthly_role_rows.append({
                    "role": role_name_current,
                    "month": str(mon),
                    "lack_h": int(round(val)),
                })
        except Exception as e_month:
            log.debug(f"月別不足集計エラー ({role_name_current}): {e_month}")

        role_kpi_rows.append({
            "role": role_name_current,
            "need_h": int(round(total_need_hours_for_role)),
            "staff_h": int(round(total_staff_hours_for_role)),
            "lack_h": int(round(total_lack_hours_for_role)),
            "working_days_considered": num_working_days_for_current_role
        })
        log.debug(f"  Role: {role_name_current}, Need(h): {total_need_hours_for_role:.1f} (on {num_working_days_for_current_role} working days), Staff(h): {total_staff_hours_for_role:.1f}, Lack(h): {total_lack_hours_for_role:.1f}")
        log.debug(f"--- shortage_role.xlsx 計算デバッグ (職種: {role_name_current}) 終了 ---")

    role_summary_df = pd.DataFrame(role_kpi_rows)
    if not role_summary_df.empty:
        role_summary_df = role_summary_df.sort_values("lack_h", ascending=False, na_position="last").reset_index(drop=True)

    monthly_role_df = pd.DataFrame(monthly_role_rows)
    if not monthly_role_df.empty:
        monthly_role_df = monthly_role_df.sort_values(["month", "role"]).reset_index(drop=True)

    fp_shortage_role = out_dir_path / "shortage_role.xlsx"
    with pd.ExcelWriter(fp_shortage_role, engine="openpyxl") as ew:
        role_summary_df.to_excel(ew, sheet_name="role_summary", index=False)
        if not monthly_role_df.empty:
            monthly_role_df.to_excel(ew, sheet_name="role_monthly", index=False)

    meta_dates_list_shortage = date_columns_in_heat_all
    meta_roles_list_shortage = role_summary_df["role"].tolist() if not role_summary_df.empty else processed_role_names_list
    meta_months_list_shortage = monthly_role_df["month"].tolist() if not monthly_role_df.empty else []

    write_meta(
        out_dir_path / "shortage.meta.json",
        slot=slot,
        dates=sorted(list(set(meta_dates_list_shortage))),
        roles=sorted(list(set(meta_roles_list_shortage))),
        months=sorted(list(set(meta_months_list_shortage))),
        ratio_file="shortage_ratio.xlsx",
        freq_file="shortage_freq.xlsx",
        estimated_holidays_used=[d.isoformat() for d in sorted(list(estimated_holidays_set))]
    )

    log.info(
        f"[shortage] completed — shortage_time → {fp_shortage_time.name}, "
        f"shortage_ratio → {fp_shortage_ratio.name}, "
        f"shortage_freq → {fp_shortage_freq.name}, shortage_role → {fp_shortage_role.name}"
    )
    if fp_shortage_time and fp_shortage_role and fp_shortage_ratio and fp_shortage_freq:
        return fp_shortage_time, fp_shortage_role
    return None


def merge_shortage_leave(
    out_dir: Path | str,
    *,
    shortage_xlsx: str | Path = "shortage_time.xlsx",
    leave_csv: str | Path = "leave_analysis.csv",
    out_excel: str | Path = "shortage_leave.xlsx",
) -> Path | None:
    """Combine shortage_time.xlsx with leave counts.

    Parameters
    ----------
    out_dir:
        Directory containing shortage and leave files.
    shortage_xlsx:
        Name of ``shortage_time.xlsx``. Must exist under ``out_dir``.
    leave_csv:
        Optional ``leave_analysis.csv`` with columns ``date`` and
        ``total_leave_days``. If missing, leave counts are treated as ``0``.
    out_excel:
        Output Excel filename.

    Returns
    -------
    Path | None
        Path to the saved Excel file or ``None`` if shortage data missing.
    """

    out_dir_path = Path(out_dir)
    shortage_fp = out_dir_path / shortage_xlsx
    if not shortage_fp.exists():
        log.error(f"[shortage] {shortage_fp} not found")
        return None

    try:
        shortage_df = pd.read_excel(shortage_fp, index_col=0)
    except Exception as e:
        log.error(f"[shortage] failed to read {shortage_fp}: {e}")
        return None

    # Convert wide time×date to long format
    long_df = shortage_df.stack().reset_index()
    long_df.columns = ["time", "date", "lack"]
    long_df["date"] = pd.to_datetime(long_df["date"])

    leave_fp = out_dir_path / leave_csv
    if leave_fp.exists():
        try:
            leave_df = pd.read_csv(leave_fp, parse_dates=["date"])
            leave_sum = (
                leave_df.groupby("date")["total_leave_days"].sum().astype(int).reset_index()
            )
            long_df = long_df.merge(leave_sum, on="date", how="left")
            long_df.rename(columns={"total_leave_days": "leave_applicants"}, inplace=True)
        except Exception as e:
            log.warning(f"[shortage] leave_csv load failed: {e}")
            long_df["leave_applicants"] = 0
    else:
        long_df["leave_applicants"] = 0

    long_df["leave_applicants"] = long_df["leave_applicants"].fillna(0).astype(int)
    long_df["net_shortage"] = (long_df["lack"] - long_df["leave_applicants"]).clip(lower=0)

    out_fp = save_df_xlsx(long_df, out_dir_path / out_excel, index=False)
    return out_fp


