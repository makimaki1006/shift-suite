"""
shortage.py – v2.6.0 (過不足分析 + 最適化スコア)
────────────────────────────────────────────────────────
* v2.3.0: SUMMARY5列参照・計算ロジック修正・constants参照
* v2.4.0: heatmap.meta.json から推定休業日を読み込み、need計算に反映。
* v2.4.1: 職種別KPIの稼働日数考慮とデバッグログ強化。
* v2.5.0: excess(過剰) 指標を追加し過不足分析に対応。
* v2.6.0: need/upper 余剰・余白および最適化スコア計算を追加。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import json
from typing import Any, Dict, Iterable, List, Set, Tuple

import numpy as np
import pandas as pd

from .. import config
from .constants import SUMMARY5
from .utils import _parse_as_date, gen_labels, log, save_df_parquet, write_meta


def shortage_and_brief(
    out_dir: Path | str,
    slot: int,
    *,
    holidays: Iterable[dt.date] | None = None,
    wage_direct: float = 0.0,
    wage_temp: float = 0.0,
    penalty_per_lack: float = 0.0,
) -> Tuple[Path, Path] | None:
    """Run shortage analysis and KPI summary.

    Parameters
    ----------
    out_dir:
        Output directory containing heatmap files.
    slot:
        Slot size in minutes.
    holidays:
        Dates considered as facility holidays.
    wage_direct:
        Hourly wage for direct employees used for excess cost estimation.
    wage_temp:
        Hourly cost for temporary staff to fill shortages.
    penalty_per_lack:
        Penalty or opportunity cost per hour of shortage.
    """
    out_dir_path = Path(out_dir)
    time_labels = gen_labels(slot)
    slot_hours = slot / 60.0

    estimated_holidays_set: Set[dt.date] = set(holidays or [])

    fp_all_heatmap = out_dir_path / "heat_ALL.parquet"
    if not fp_all_heatmap.exists():
        log.error(f"[shortage] heat_ALL.parquet が見つかりません: {fp_all_heatmap}")
        return None
    try:
        heat_all_df = pd.read_parquet(fp_all_heatmap)
    except Exception as e:
        log.error(
            f"[shortage] heat_ALL.parquet の読み込み中にエラー: {e}", exc_info=True
        )
        return None

    date_columns_in_heat_all = [
        str(col)
        for col in heat_all_df.columns
        if col not in SUMMARY5 and _parse_as_date(str(col)) is not None
    ]
    if not date_columns_in_heat_all:
        log.warning("[shortage] heat_ALL.xlsx に日付データ列が見つかりませんでした。")
        # 空のExcelを生成して返す
        empty_df = pd.DataFrame(index=time_labels)
        fp_s_t_empty = save_df_parquet(
            empty_df,
            out_dir_path / "shortage_time.parquet",
            index=True,
        )
        fp_s_r_empty = save_df_parquet(
            pd.DataFrame(),
            out_dir_path / "shortage_role.parquet",
            index=False,
        )
        save_df_parquet(
            empty_df,
            out_dir_path / "shortage_freq.parquet",
            index=True,
        )
        return (fp_s_t_empty, fp_s_r_empty) if fp_s_t_empty and fp_s_r_empty else None

    staff_actual_data_all_df = (
        heat_all_df[date_columns_in_heat_all]
        .copy()
        .reindex(index=time_labels)
        .fillna(0)
    )

    need_series_per_time_overall_orig = (
        heat_all_df.get("need", pd.Series(dtype=float))
        .reindex(index=time_labels)
        .fillna(0)
        .clip(lower=0)
    )

    parsed_date_list_all = [_parse_as_date(c) for c in staff_actual_data_all_df.columns]
    holiday_mask_all = [
        d in estimated_holidays_set if d else False for d in parsed_date_list_all
    ]

    dow_need_pattern_df = pd.DataFrame()
    meta_fp = out_dir_path / "heatmap.meta.json"
    if meta_fp.exists():
        try:
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
            records = meta.get("dow_need_pattern", [])
            if records:
                dow_need_pattern_df = pd.DataFrame(records).set_index("time")
        except Exception as e:
            log.debug(f"failed reading meta file for need pattern: {e}")

    need_df_all = pd.DataFrame(index=time_labels, columns=staff_actual_data_all_df.columns, dtype=float)
    for col, parsed_date in zip(staff_actual_data_all_df.columns, parsed_date_list_all, strict=True):
        if parsed_date is None:
            need_df_all[col] = need_series_per_time_overall_orig
            continue
        if parsed_date in estimated_holidays_set:
            need_df_all[col] = 0
            continue
        dow = parsed_date.weekday()
        dow_col = str(dow)
        if not dow_need_pattern_df.empty and dow_col in dow_need_pattern_df.columns:
            need_df_all[col] = (
                dow_need_pattern_df[dow_col]
                .reindex(index=time_labels)
                .fillna(0)
                .astype(float)
            )
        else:
            # パターンが存在しない曜日の必要人数は0とする
            need_df_all[col] = 0

    lack_count_overall_df = (
        (need_df_all - staff_actual_data_all_df).clip(lower=0).fillna(0).astype(int)
    )
    shortage_ratio_df = (
        ((need_df_all - staff_actual_data_all_df) / need_df_all.replace(0, np.nan))
        .clip(lower=0)
        .fillna(0)
    )

    fp_shortage_time = save_df_parquet(
        lack_count_overall_df,
        out_dir_path / "shortage_time.parquet",
        index=True,
    )
    fp_shortage_ratio = save_df_parquet(
        shortage_ratio_df,
        out_dir_path / "shortage_ratio.parquet",
        index=True,
    )

    lack_occurrence_df = (lack_count_overall_df > 0).astype(int)
    shortage_freq_df = pd.DataFrame(
        lack_occurrence_df.sum(axis=1), columns=["shortage_days"]
    )
    fp_shortage_freq = save_df_parquet(
        shortage_freq_df,
        out_dir_path / "shortage_freq.parquet",
        index=True,
    )

    surplus_vs_need_df = (
        (staff_actual_data_all_df - need_df_all).clip(lower=0).fillna(0).astype(int)
    )
    save_df_parquet(
        surplus_vs_need_df,
        out_dir_path / "surplus_vs_need_time.parquet",
        index=True,
    )

    # ----- excess analysis -----
    fp_excess_time = fp_excess_ratio = fp_excess_freq = None
    if "upper" in heat_all_df.columns:
        upper_series_overall_orig = (
            heat_all_df["upper"].reindex(index=time_labels).fillna(0).clip(lower=0)
        )
        upper_df_all = pd.DataFrame(
            np.repeat(
                upper_series_overall_orig.values[:, np.newaxis],
                len(staff_actual_data_all_df.columns),
                axis=1,
            ),
            index=upper_series_overall_orig.index,
            columns=staff_actual_data_all_df.columns,
        )
        if any(holiday_mask_all):
            for col, is_h in zip(upper_df_all.columns, holiday_mask_all, strict=True):
                if is_h:
                    upper_df_all[col] = 0

        excess_count_overall_df = (
            (staff_actual_data_all_df - upper_df_all)
            .clip(lower=0)
            .fillna(0)
            .astype(int)
        )
        excess_ratio_df = (
            (
                (staff_actual_data_all_df - upper_df_all)
                / upper_df_all.replace(0, np.nan)
            )
            .clip(lower=0)
            .fillna(0)
        )

        fp_excess_time = save_df_parquet(
            excess_count_overall_df,
            out_dir_path / "excess_time.parquet",
            index=True,
        )
        fp_excess_ratio = save_df_parquet(
            excess_ratio_df,
            out_dir_path / "excess_ratio.parquet",
            index=True,
        )

        excess_occurrence_df = (excess_count_overall_df > 0).astype(int)
        excess_freq_df = pd.DataFrame(
            excess_occurrence_df.sum(axis=1), columns=["excess_days"]
        )
        fp_excess_freq = save_df_parquet(
            excess_freq_df,
            out_dir_path / "excess_freq.parquet",
            index=True,
        )

        margin_vs_upper_df = (
            (upper_df_all - staff_actual_data_all_df)
            .clip(lower=0)
            .fillna(0)
            .astype(int)
        )
        save_df_parquet(
            margin_vs_upper_df,
            out_dir_path / "margin_vs_upper_time.parquet",
            index=True,
        )
    else:
        log.warning(
            "[shortage] heat_ALL.xlsx に 'upper' 列がないため excess 分析をスキップします。"
        )

    weights = config.get("optimization_weights", {"lack": 0.6, "excess": 0.4})
    w_lack = float(weights.get("lack", 0.6))
    w_excess = float(weights.get("excess", 0.4))
    pen_lack_df = shortage_ratio_df
    pen_excess_df = (
        excess_ratio_df if "upper" in heat_all_df.columns else pen_lack_df * 0
    )
    optimization_score_df = 1 - (w_lack * pen_lack_df + w_excess * pen_excess_df)
    optimization_score_df = optimization_score_df.clip(lower=0, upper=1)
    save_df_parquet(
        optimization_score_df,
        out_dir_path / "optimization_score_time.parquet",
        index=True,
    )

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
        log.debug(
            f"--- shortage_role.xlsx 計算デバッグ (職種: {role_name_current}) ---"
        )

        try:
            role_heat_current_df = pd.read_excel(fp_role_heatmap_item, index_col=0)
        except Exception as e_role_heat:
            log.warning(
                f"[shortage] 職種別ヒートマップ '{fp_role_heatmap_item.name}' の読み込みエラー: {e_role_heat}"
            )
            role_kpi_rows.append(
                {
                    "role": role_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "heatmap read error",
                }
            )
            continue

        if "need" not in role_heat_current_df.columns:
            log.warning(
                f"[shortage] 職種 '{role_name_current}' のヒートマップに 'need' 列が不足。KPI計算スキップ。"
            )
            role_kpi_rows.append(
                {
                    "role": role_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "missing need column",
                }
            )
            continue
        role_need_per_time_series_orig_for_role = (
            role_heat_current_df["need"]
            .reindex(index=time_labels)
            .fillna(0)
            .clip(lower=0)
        )

        role_date_columns_list = [
            str(col)
            for col in role_heat_current_df.columns
            if col not in SUMMARY5 and _parse_as_date(str(col)) is not None
        ]
        if not role_date_columns_list:
            log.warning(
                f"[shortage] 職種 '{role_name_current}' のヒートマップに日付列がありません。KPI計算をスキップします。"
            )
            role_kpi_rows.append(
                {
                    "role": role_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "no date columns",
                }
            )
            continue

        role_staff_actual_data_df = (
            role_heat_current_df[role_date_columns_list]
            .copy()
            .reindex(index=time_labels)
            .fillna(0)
        )

        parsed_role_dates = [
            _parse_as_date(c) for c in role_staff_actual_data_df.columns
        ]
        holiday_mask_role = [
            d in estimated_holidays_set if d else False for d in parsed_role_dates
        ]

        need_df_role = pd.DataFrame(
            np.repeat(
                role_need_per_time_series_orig_for_role.values[:, np.newaxis],
                len(role_staff_actual_data_df.columns),
                axis=1,
            ),
            index=role_need_per_time_series_orig_for_role.index,
            columns=role_staff_actual_data_df.columns,
        )
        if any(holiday_mask_role):
            for c, is_h in zip(need_df_role.columns, holiday_mask_role, strict=True):
                if is_h:
                    need_df_role[c] = 0

        working_cols_role = [
            c
            for c, is_h in zip(
                role_staff_actual_data_df.columns, holiday_mask_role, strict=True
            )
            if not is_h and _parse_as_date(c)
        ]
        num_working_days_for_current_role = len(working_cols_role)
        total_need_slots_for_role_working_days = (
            role_need_per_time_series_orig_for_role.sum()
            * num_working_days_for_current_role
        )

        role_lack_count_for_specific_role_df = (
            need_df_role - role_staff_actual_data_df
        ).clip(lower=0)

        role_excess_count_for_specific_role_df = None
        if "upper" in role_heat_current_df.columns:
            role_upper_per_time_series_orig_for_role = (
                role_heat_current_df["upper"]
                .reindex(index=time_labels)
                .fillna(0)
                .clip(lower=0)
            )
            upper_df_role = pd.DataFrame(
                np.repeat(
                    role_upper_per_time_series_orig_for_role.values[:, np.newaxis],
                    len(role_staff_actual_data_df.columns),
                    axis=1,
                ),
                index=role_upper_per_time_series_orig_for_role.index,
                columns=role_staff_actual_data_df.columns,
            )
            if any(holiday_mask_role):
                for c, is_h in zip(
                    upper_df_role.columns, holiday_mask_role, strict=True
                ):
                    if is_h:
                        upper_df_role[c] = 0
            role_excess_count_for_specific_role_df = (
                role_staff_actual_data_df - upper_df_role
            ).clip(lower=0)
        else:
            log.debug(
                f"[shortage] '{role_name_current}' ヒートマップに 'upper' 列がないため excess 計算をスキップ"
            )

        total_need_hours_for_role = total_need_slots_for_role_working_days * slot_hours
        # staff_h は全日の実績で計算（休業日も実績0として含まれる）
        total_staff_hours_for_role = role_staff_actual_data_df.sum().sum() * slot_hours
        # lack_h は休業日のneed=0を考慮したlackの合計
        total_lack_hours_for_role = (
            role_lack_count_for_specific_role_df.sum().sum() * slot_hours
        )
        # excess_h は休業日のupper=0を考慮したexcessの合計
        total_excess_hours_for_role = (
            role_excess_count_for_specific_role_df.sum().sum() * slot_hours
            if role_excess_count_for_specific_role_df is not None
            else 0
        )
        # 計算結果検証用: need_h - staff_h との差分がlack_hと一致するか確認
        expected_lack_h = max(total_need_hours_for_role - total_staff_hours_for_role, 0)
        if abs(expected_lack_h - total_lack_hours_for_role) > slot_hours:
            log.debug(
                f"[shortage] mismatch for {role_name_current}: "
                f"need_h={total_need_hours_for_role:.1f}, "
                f"staff_h={total_staff_hours_for_role:.1f}, "
                f"computed lack_h={total_lack_hours_for_role:.1f}, "
                f"expected lack_h={expected_lack_h:.1f}"
            )
            try:
                daily_need_h = (need_df_role.sum() * slot_hours).rename("need_h")
                daily_staff_h = (role_staff_actual_data_df.sum() * slot_hours).rename(
                    "staff_h"
                )
                daily_lack_h = (
                    role_lack_count_for_specific_role_df.sum() * slot_hours
                ).rename("lack_h")
                daily_debug_df = pd.concat(
                    [daily_need_h, daily_staff_h, daily_lack_h], axis=1
                ).assign(diff_h=lambda d: d["need_h"] - d["staff_h"])
                log.debug(
                    f"[shortage] daily summary for {role_name_current} (first 7 days):\n"
                    f"{daily_debug_df.head(7).to_string()}"
                )
            except Exception as e_daily:
                log.debug(
                    f"[shortage] daily debug summary failed for {role_name_current}: {e_daily}"
                )

        # 月別不足h・過剰h集計
        try:
            lack_by_date = role_lack_count_for_specific_role_df.sum()
            lack_by_date.index = pd.to_datetime(lack_by_date.index)
            lack_month = (
                lack_by_date.groupby(lack_by_date.index.to_period("M")).sum()
                * slot_hours
            )
            excess_month = pd.Series(dtype=float)
            if role_excess_count_for_specific_role_df is not None:
                excess_by_date = role_excess_count_for_specific_role_df.sum()
                excess_by_date.index = pd.to_datetime(excess_by_date.index)
                excess_month = (
                    excess_by_date.groupby(excess_by_date.index.to_period("M")).sum()
                    * slot_hours
                )
            month_keys: Dict[str, Dict[str, int]] = {}
            for mon, val in lack_month.items():
                month_keys.setdefault(
                    str(mon),
                    {
                        "role": role_name_current,
                        "month": str(mon),
                        "lack_h": 0,
                        "excess_h": 0,
                    },
                )
                month_keys[str(mon)]["lack_h"] = int(round(val))
            for mon, val in excess_month.items():
                month_keys.setdefault(
                    str(mon),
                    {
                        "role": role_name_current,
                        "month": str(mon),
                        "lack_h": 0,
                        "excess_h": 0,
                    },
                )
                month_keys[str(mon)]["excess_h"] = int(round(val))
            monthly_role_rows.extend(month_keys.values())
        except Exception as e_month:
            log.debug(f"月別不足/過剰集計エラー ({role_name_current}): {e_month}")

        role_kpi_rows.append(
            {
                "role": role_name_current,
                "need_h": int(round(total_need_hours_for_role)),
                "staff_h": int(round(total_staff_hours_for_role)),
                "lack_h": int(round(total_lack_hours_for_role)),
                "excess_h": int(round(total_excess_hours_for_role)),
                "working_days_considered": num_working_days_for_current_role,
            }
        )
        log.debug(
            f"  Role: {role_name_current}, Need(h): {total_need_hours_for_role:.1f} (on {num_working_days_for_current_role} working days), "
            f"Staff(h): {total_staff_hours_for_role:.1f}, Lack(h): {total_lack_hours_for_role:.1f}, Excess(h): {total_excess_hours_for_role:.1f}"
        )
        log.debug(
            f"--- shortage_role.xlsx 計算デバッグ (職種: {role_name_current}) 終了 ---"
        )

    role_summary_df = pd.DataFrame(role_kpi_rows)
    if not role_summary_df.empty:
        role_summary_df = role_summary_df.sort_values(
            "lack_h", ascending=False, na_position="last"
        ).reset_index(drop=True)
        role_summary_df = role_summary_df.assign(
            estimated_excess_cost=lambda d: d.get("excess_h", 0) * wage_direct,
            estimated_lack_cost_if_temporary_staff=lambda d: d.get("lack_h", 0)
            * wage_temp,
            estimated_lack_penalty_cost=lambda d: d.get("lack_h", 0) * penalty_per_lack,
        )

    monthly_role_df = pd.DataFrame(monthly_role_rows)
    if not monthly_role_df.empty:
        monthly_role_df = monthly_role_df.sort_values(["month", "role"]).reset_index(
            drop=True
        )

    fp_shortage_role = out_dir_path / "shortage_role_summary.parquet"
    role_summary_df.to_parquet(fp_shortage_role, index=False)
    if not monthly_role_df.empty:
        monthly_role_df.to_parquet(
            out_dir_path / "shortage_role_monthly.parquet",
            index=False,
        )

    meta_dates_list_shortage = date_columns_in_heat_all
    meta_roles_list_shortage = (
        role_summary_df["role"].tolist()
        if not role_summary_df.empty
        else processed_role_names_list
    )
    meta_months_list_shortage = (
        monthly_role_df["month"].tolist() if not monthly_role_df.empty else []
    )

    # ── Employment shortage analysis ────────────────────────────────────────
    emp_kpi_rows: List[Dict[str, Any]] = []
    monthly_emp_rows: List[Dict[str, Any]] = []
    processed_emp_names_list = []

    for fp_emp_heatmap_item in out_dir_path.glob("heat_emp_*.xlsx"):
        emp_name_current = fp_emp_heatmap_item.stem.replace("heat_emp_", "")
        processed_emp_names_list.append(emp_name_current)
        log.debug(
            f"--- shortage_employment.xlsx 計算デバッグ (雇用形態: {emp_name_current}) ---"
        )
        try:
            emp_heat_current_df = pd.read_excel(fp_emp_heatmap_item, index_col=0)
        except Exception as e_emp_heat:
            log.warning(
                f"[shortage] 雇用形態別ヒートマップ '{fp_emp_heatmap_item.name}' の読み込みエラー: {e_emp_heat}"
            )
            emp_kpi_rows.append(
                {
                    "employment": emp_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "heatmap read error",
                }
            )
            continue

        if "need" not in emp_heat_current_df.columns:
            log.warning(
                f"[shortage] 雇用形態 '{emp_name_current}' のヒートマップに 'need' 列が不足。KPI計算スキップ。"
            )
            emp_kpi_rows.append(
                {
                    "employment": emp_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "missing need column",
                }
            )
            continue

        emp_need_series = (
            emp_heat_current_df["need"]
            .reindex(index=time_labels)
            .fillna(0)
            .clip(lower=0)
        )
        emp_date_columns = [
            str(c)
            for c in emp_heat_current_df.columns
            if c not in SUMMARY5 and _parse_as_date(str(c)) is not None
        ]
        if not emp_date_columns:
            log.warning(
                f"[shortage] 雇用形態 '{emp_name_current}' のヒートマップに日付列がありません。KPI計算をスキップします。"
            )
            emp_kpi_rows.append(
                {
                    "employment": emp_name_current,
                    "need_h": 0,
                    "staff_h": 0,
                    "lack_h": 0,
                    "working_days_considered": 0,
                    "note": "no date columns",
                }
            )
            continue

        emp_staff_df = (
            emp_heat_current_df[emp_date_columns]
            .copy()
            .reindex(index=time_labels)
            .fillna(0)
        )
        parsed_emp_dates = [_parse_as_date(c) for c in emp_staff_df.columns]
        holiday_mask_emp = [
            d in estimated_holidays_set if d else False for d in parsed_emp_dates
        ]
        need_df_emp = pd.DataFrame(
            np.repeat(
                emp_need_series.values[:, np.newaxis], len(emp_staff_df.columns), axis=1
            ),
            index=emp_need_series.index,
            columns=emp_staff_df.columns,
        )
        if any(holiday_mask_emp):
            for c, is_h in zip(need_df_emp.columns, holiday_mask_emp, strict=True):
                if is_h:
                    need_df_emp[c] = 0

        working_cols_emp = [
            c
            for c, is_h in zip(emp_staff_df.columns, holiday_mask_emp, strict=True)
            if not is_h and _parse_as_date(c)
        ]
        num_working_days_for_current_emp = len(working_cols_emp)

        lack_count_emp_df = (need_df_emp - emp_staff_df).clip(lower=0)
        excess_count_emp_df = (emp_staff_df - need_df_emp).clip(lower=0)

        total_need_hours_for_emp = need_df_emp.sum().sum() * slot_hours
        total_staff_hours_for_emp = emp_staff_df.sum().sum() * slot_hours
        total_lack_hours_for_emp = lack_count_emp_df.sum().sum() * slot_hours
        total_excess_hours_for_emp = (
            excess_count_emp_df.sum().sum() * slot_hours
            if not excess_count_emp_df.empty
            else 0
        )

        try:
            lack_by_date = lack_count_emp_df.sum()
            lack_by_date.index = pd.to_datetime(lack_by_date.index)
            lack_month = (
                lack_by_date.groupby(lack_by_date.index.to_period("M")).sum()
                * slot_hours
            )
            excess_month = pd.Series(dtype=float)
            if not excess_count_emp_df.empty:
                excess_by_date = excess_count_emp_df.sum()
                excess_by_date.index = pd.to_datetime(excess_by_date.index)
                excess_month = (
                    excess_by_date.groupby(excess_by_date.index.to_period("M")).sum()
                    * slot_hours
                )
            month_keys: Dict[str, Dict[str, int]] = {}
            for mon, val in lack_month.items():
                month_keys.setdefault(
                    str(mon),
                    {
                        "employment": emp_name_current,
                        "month": str(mon),
                        "lack_h": 0,
                        "excess_h": 0,
                    },
                )
                month_keys[str(mon)]["lack_h"] = int(round(val))
            for mon, val in excess_month.items():
                month_keys.setdefault(
                    str(mon),
                    {
                        "employment": emp_name_current,
                        "month": str(mon),
                        "lack_h": 0,
                        "excess_h": 0,
                    },
                )
                month_keys[str(mon)]["excess_h"] = int(round(val))
            monthly_emp_rows.extend(month_keys.values())
        except Exception as e_month_emp:
            log.debug(f"月別不足/過剰集計エラー ({emp_name_current}): {e_month_emp}")

        emp_kpi_rows.append(
            {
                "employment": emp_name_current,
                "need_h": int(round(total_need_hours_for_emp)),
                "staff_h": int(round(total_staff_hours_for_emp)),
                "lack_h": int(round(total_lack_hours_for_emp)),
                "excess_h": int(round(total_excess_hours_for_emp)),
                "working_days_considered": num_working_days_for_current_emp,
            }
        )
        log.debug(
            f"  Employment: {emp_name_current}, Need(h): {total_need_hours_for_emp:.1f} (on {num_working_days_for_current_emp} working days), "
            f"Staff(h): {total_staff_hours_for_emp:.1f}, Lack(h): {total_lack_hours_for_emp:.1f}, Excess(h): {total_excess_hours_for_emp:.1f}"
        )
        log.debug(
            f"--- shortage_employment.xlsx 計算デバッグ (雇用形態: {emp_name_current}) 終了 ---"
        )

    emp_summary_df = pd.DataFrame(emp_kpi_rows)
    if not emp_summary_df.empty:
        emp_summary_df = emp_summary_df.sort_values(
            "lack_h", ascending=False, na_position="last"
        ).reset_index(drop=True)
        emp_summary_df = emp_summary_df.assign(
            estimated_excess_cost=lambda d: d.get("excess_h", 0) * wage_direct,
            estimated_lack_cost_if_temporary_staff=lambda d: d.get("lack_h", 0)
            * wage_temp,
            estimated_lack_penalty_cost=lambda d: d.get("lack_h", 0) * penalty_per_lack,
        )

    monthly_emp_df = pd.DataFrame(monthly_emp_rows)
    if not monthly_emp_df.empty:
        monthly_emp_df = monthly_emp_df.sort_values(
            ["month", "employment"]
        ).reset_index(drop=True)

    fp_shortage_emp = out_dir_path / "shortage_employment_summary.parquet"
    emp_summary_df.to_parquet(fp_shortage_emp, index=False)
    if not monthly_emp_df.empty:
        monthly_emp_df.to_parquet(
            out_dir_path / "shortage_employment_monthly.parquet",
            index=False,
        )

    meta_employments_list_shortage = (
        emp_summary_df["employment"].tolist()
        if not emp_summary_df.empty
        else processed_emp_names_list
    )
    meta_months_list_shortage.extend(
        monthly_emp_df["month"].tolist() if not monthly_emp_df.empty else []
    )

    write_meta(
        out_dir_path / "shortage.meta.json",
        slot=slot,
        dates=sorted(list(set(meta_dates_list_shortage))),
        roles=sorted(list(set(meta_roles_list_shortage))),
        employments=sorted(list(set(meta_employments_list_shortage))),
        months=sorted(list(set(meta_months_list_shortage))),
        ratio_file="shortage_ratio.parquet",
        freq_file="shortage_freq.parquet",
        excess_ratio_file="excess_ratio.parquet" if fp_excess_ratio else None,
        excess_freq_file="excess_freq.parquet" if fp_excess_freq else None,
        estimated_holidays_used=[
            d.isoformat() for d in sorted(list(estimated_holidays_set))
        ],
    )

    # ── text summary output ────────────────────────────────────────────────
    summary_fp = out_dir_path / "shortage_summary.txt"
    try:
        total_lack_h = int(round(role_summary_df.get("lack_h", pd.Series()).sum()))
        total_excess_h = int(round(role_summary_df.get("excess_h", pd.Series()).sum()))
        summary_lines = [
            f"total_lack_hours: {total_lack_h}",
            f"total_excess_hours: {total_excess_h}",
        ]
        summary_fp.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        log.debug(f"failed writing shortage summary text: {e}")

    log.info(
        (
            f"[shortage] completed — shortage_time → {fp_shortage_time.name}, "
            f"shortage_ratio → {fp_shortage_ratio.name}, "
            f"shortage_freq → {fp_shortage_freq.name}, "
            f"shortage_role → {fp_shortage_role.name}, "
            f"shortage_employment → {fp_shortage_emp.name}, "
        )
        + (f"excess_time → {fp_excess_time.name}, " if fp_excess_time else "")
        + (f"excess_ratio → {fp_excess_ratio.name}, " if fp_excess_ratio else "")
        + (f"excess_freq → {fp_excess_freq.name}" if fp_excess_freq else "")
    )
    if fp_shortage_time and fp_shortage_role and fp_shortage_ratio and fp_shortage_freq:
        return fp_shortage_time, fp_shortage_role
    return None


def merge_shortage_leave(
    out_dir: Path | str,
    *,
    shortage_xlsx: str | Path = "shortage_time.parquet",
    leave_csv: str | Path = "leave_analysis.csv",
    out_excel: str | Path = "shortage_leave.csv",
) -> Path | None:
    """Combine shortage_time.parquet with leave counts.

    Parameters
    ----------
    out_dir:
        Directory containing shortage and leave files.
    shortage_xlsx:
        Name of ``shortage_time.parquet``. Must exist under ``out_dir``.
    leave_csv:
        Optional ``leave_analysis.csv`` with columns ``date`` and
        ``total_leave_days``. If missing, leave counts are treated as ``0``.
    out_excel:
        Output CSV filename.

    Returns
    -------
    Path | None
        Path to the saved CSV file or ``None`` if shortage data missing.
    """

    out_dir_path = Path(out_dir)
    shortage_fp = out_dir_path / shortage_xlsx
    if not shortage_fp.exists():
        log.error(f"[shortage] {shortage_fp} not found")
        return None

    try:
        shortage_df = pd.read_parquet(shortage_fp)
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
                leave_df.groupby("date")["total_leave_days"]
                .sum()
                .astype(int)
                .reset_index()
            )
            long_df = long_df.merge(leave_sum, on="date", how="left")
            long_df.rename(
                columns={"total_leave_days": "leave_applicants"}, inplace=True
            )
        except Exception as e:
            log.warning(f"[shortage] leave_csv load failed: {e}")
            long_df["leave_applicants"] = 0
    else:
        long_df["leave_applicants"] = 0

    long_df["leave_applicants"] = long_df["leave_applicants"].fillna(0).astype(int)
    long_df["net_shortage"] = (long_df["lack"] - long_df["leave_applicants"]).clip(
        lower=0
    )

    out_fp = out_dir_path / out_excel
    long_df.to_csv(out_fp, index=False)
    return out_fp


def _summary_by_period(df: pd.DataFrame, *, period: str) -> pd.DataFrame:
    """Return average counts by *period* and time slot.

    Parameters
    ----------
    df:
        DataFrame loaded from ``shortage_time.xlsx`` or ``excess_time.xlsx``.
    period:
        ``"weekday"`` or ``"month_period"``.

    Returns
    -------
    pd.DataFrame
        Aggregated average counts per time slot.
    """

    date_cols = [c for c in df.columns if _parse_as_date(str(c)) is not None]
    if not date_cols:
        return pd.DataFrame(columns=[period, "timeslot", "avg_count"])

    data = df[date_cols].copy()
    data.columns = pd.to_datetime(data.columns)
    df_for_melt = data.reset_index()
    # reset_index()によって生成された最初の列（=元のインデックス）の名前を動的に取得する
    index_col_name = df_for_melt.columns[0]
    long = df_for_melt.melt(
        id_vars=[index_col_name], var_name="date", value_name="count"
    )
    long.rename(columns={index_col_name: "timeslot"}, inplace=True)

    long["date"] = pd.to_datetime(long["date"])

    if period == "weekday":
        day_name_map = {
            "Monday": "月曜日",
            "Tuesday": "火曜日",
            "Wednesday": "水曜日",
            "Thursday": "木曜日",
            "Friday": "金曜日",
            "Saturday": "土曜日",
            "Sunday": "日曜日",
        }
        long[period] = long["date"].dt.day_name().map(day_name_map)
        order = list(day_name_map.values())
    elif period == "month_period":

        def _mp(day_val: int) -> str:
            if day_val <= 10:
                return "月初(1-10日)"
            if day_val <= 20:
                return "月中(11-20日)"
            return "月末(21-末日)"

        long[period] = long["date"].dt.day.apply(_mp)
        order = ["月初(1-10日)", "月中(11-20日)", "月末(21-末日)"]
    else:  # pragma: no cover - invalid option
        raise ValueError("period must be 'weekday' or 'month_period'")

    grouped = (
        long.groupby([period, "timeslot"], observed=False)["count"]
        .mean()
        .reset_index(name="avg_count")
    )
    grouped[period] = pd.Categorical(grouped[period], categories=order, ordered=True)
    return grouped.sort_values([period, "timeslot"]).reset_index(drop=True)


def weekday_timeslot_summary(
    out_dir: Path | str, *, excel: str = "shortage_time.parquet"
) -> pd.DataFrame:
    """Return average shortage counts by weekday and time slot."""

    df = pd.read_parquet(Path(out_dir) / excel)
    return _summary_by_period(df, period="weekday")


def monthperiod_timeslot_summary(
    out_dir: Path | str, *, excel: str = "shortage_time.parquet"
) -> pd.DataFrame:
    """Return average shortage counts by month period and time slot."""

    df = pd.read_parquet(Path(out_dir) / excel)
    return _summary_by_period(df, period="month_period")
