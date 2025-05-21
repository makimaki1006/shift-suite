"""
shortage.py – v2.4.1 (休業日対応のデバッグ強化)
────────────────────────────────────────────────────────
* v2.3.0: SUMMARY5列参照・計算ロジック修正・constants参照
* v2.4.0: heatmap.meta.json から推定休業日を読み込み、need計算に反映。
* v2.4.1: 職種別KPIの稼働日数考慮とデバッグログ強化。
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, List, Dict, Any, Set
import json
import datetime as dt

import pandas as pd
import numpy as np

from .utils import gen_labels, log, save_df_xlsx, write_meta, _parse_as_date
from .constants import SUMMARY5

def shortage_and_brief(
    out_dir: Path | str,
    slot: int,
) -> Tuple[Path, Path] | None:
    out_dir_path = Path(out_dir)
    time_labels = gen_labels(slot)
    slot_hours = slot / 60.0

    estimated_holidays_set: Set[dt.date] = set()
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
        # 空のExcelを生成して返すか、Noneを返す
        empty_df = pd.DataFrame(index=time_labels)
        fp_s_t_empty = save_df_xlsx(empty_df, out_dir_path / "shortage_time.xlsx", sheet_name="lack_time", index=True)
        fp_s_r_empty = save_df_xlsx(pd.DataFrame(), out_dir_path / "shortage_role.xlsx", sheet_name="role_summary", index=False)
        return fp_s_t_empty, fp_s_r_empty if fp_s_t_empty and fp_s_r_empty else None


    staff_actual_data_all_df = heat_all_df[date_columns_in_heat_all].copy().reindex(index=time_labels).fillna(0)

    if 'need' not in heat_all_df.columns:
        log.error("[shortage] heat_ALL.xlsx に 'need' 列 (集計列) が見つかりません。")
        return None
    need_series_per_time_overall_orig = heat_all_df['need'].reindex(index=time_labels).fillna(0).clip(lower=0)

    lack_count_overall_df = pd.DataFrame(index=staff_actual_data_all_df.index, columns=staff_actual_data_all_df.columns, dtype=float)
    log.debug(f"--- shortage_time.xlsx 計算デバッグ (全体) ---")
    for date_col_overall_str in staff_actual_data_all_df.columns:
        current_date_obj_overall = _parse_as_date(date_col_overall_str)
        is_holiday_overall = False
        if current_date_obj_overall and estimated_holidays_set and current_date_obj_overall in estimated_holidays_set:
            is_holiday_overall = True
        
        current_day_need_for_overall = pd.Series(0, index=need_series_per_time_overall_orig.index) if is_holiday_overall else need_series_per_time_overall_orig
        log.debug(f"  日付: {date_col_overall_str}, 休業日か: {is_holiday_overall}, 適用need合計: {current_day_need_for_overall.sum()}")
        lack_count_overall_df[date_col_overall_str] = (current_day_need_for_overall - staff_actual_data_all_df[date_col_overall_str]).clip(lower=0)
    
    lack_count_overall_df = lack_count_overall_df.fillna(0).astype(int)
    fp_shortage_time = save_df_xlsx(lack_count_overall_df, out_dir_path / "shortage_time.xlsx", sheet_name="lack_time", index=True)
    log.debug(f"--- shortage_time.xlsx 計算デバッグ (全体) 終了 ---")

    role_kpi_rows: List[Dict[str, Any]] = []
    processed_role_names_list = []

    for fp_role_heatmap_item in out_dir_path.glob("heat_*.xlsx"):
        if fp_role_heatmap_item.name == "heat_ALL.xlsx": continue
        
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
        role_lack_count_for_specific_role_df = pd.DataFrame(index=role_staff_actual_data_df.index, columns=role_staff_actual_data_df.columns, dtype=float)
        
        total_need_slots_for_role_working_days = 0
        num_working_days_for_current_role = 0

        for date_col_for_role_str in role_staff_actual_data_df.columns:
            current_date_obj_for_role = _parse_as_date(date_col_for_role_str)
            is_holiday_role = False
            if current_date_obj_for_role and estimated_holidays_set and current_date_obj_for_role in estimated_holidays_set:
                is_holiday_role = True
            
            current_day_need_for_role_calc = pd.Series(0, index=role_need_per_time_series_orig_for_role.index) if is_holiday_role else role_need_per_time_series_orig_for_role
            
            if not is_holiday_role and current_date_obj_for_role: # 稼働日であれば
                total_need_slots_for_role_working_days += current_day_need_for_role_calc.sum()
                num_working_days_for_current_role +=1
            
            log.debug(f"  職種日付: {date_col_for_role_str}, 休業日か: {is_holiday_role}, 適用need合計: {current_day_need_for_role_calc.sum()}")
            role_lack_count_for_specific_role_df[date_col_for_role_str] = (current_day_need_for_role_calc - role_staff_actual_data_df[date_col_for_role_str]).clip(lower=0)
        
        total_need_hours_for_role = total_need_slots_for_role_working_days * slot_hours
        # staff_h は全日の実績で計算（休業日も実績0として含まれる）
        total_staff_hours_for_role = role_staff_actual_data_df.sum().sum() * slot_hours
        # lack_h は休業日のneed=0を考慮したlackの合計
        total_lack_hours_for_role = role_lack_count_for_specific_role_df.sum().sum() * slot_hours

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
    
    fp_shortage_role = save_df_xlsx(role_summary_df, out_dir_path / "shortage_role.xlsx", sheet_name="role_summary", index=False)

    meta_dates_list_shortage = date_columns_in_heat_all
    meta_roles_list_shortage = role_summary_df["role"].tolist() if not role_summary_df.empty else processed_role_names_list

    write_meta(
        out_dir_path / "shortage.meta.json",
        slot=slot,
        dates=sorted(list(set(meta_dates_list_shortage))),
        roles=sorted(list(set(meta_roles_list_shortage))),
        estimated_holidays_used=[d.isoformat() for d in sorted(list(estimated_holidays_set))]
    )

    log.info(f"[shortage] completed — shortage_time → {fp_shortage_time.name}, shortage_role → {fp_shortage_role.name}")
    if fp_shortage_time and fp_shortage_role:
        return fp_shortage_time, fp_shortage_role
    return None
