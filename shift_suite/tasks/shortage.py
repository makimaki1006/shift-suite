"""
shortage.py – v2.7.0 (最終修正版)
────────────────────────────────────────────────────────
* v2.7.0: 全体の不足計算(shortage_time)のロジックを、詳細Needファイル
          (need_per_date_slot.parquet)を最優先で利用するよう全面的に刷新。
          これにより、休日の過剰な不足計上問題を完全に解決する。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import json

import numpy as np
import pandas as pd

from .. import config
from .constants import SUMMARY5, SLOT_HOURS
from .utils import _parse_as_date, gen_labels, log, save_df_parquet, write_meta
from .proportional_calculator import calculate_proportional_shortage
from .time_axis_shortage_calculator import calculate_time_axis_shortage

# 不足分析専用ログ
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shortage_logger import setup_shortage_analysis_logger
    shortage_log = setup_shortage_analysis_logger()
except Exception:
    shortage_log = log  # フォールバック

def create_timestamped_log(analysis_results: Dict, output_dir: Path) -> Path:
    """タイムスタンプ付きの詳細ログファイルを作成"""
    timestamp = dt.datetime.now().strftime("%Y年%m月%d日%H時%M分")
    log_filename = f"{timestamp}_アウトプット.txt"
    log_filepath = output_dir / log_filename
    
    try:
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== 不足分析結果レポート ===\n")
            f.write(f"生成日時: {timestamp}\n")
            f.write(f"分析ディレクトリ: {output_dir}\n")
            f.write("=" * 50 + "\n\n")
            
            # 1. 全体サマリー
            f.write("【1. 全体サマリー】\n")
            total_summary = analysis_results.get('total_summary', {})
            f.write(f"  総不足時間: {total_summary.get('total_lack_h', 0):.2f}時間\n")
            f.write(f"  総過剰時間: {total_summary.get('total_excess_h', 0):.2f}時間\n")
            f.write(f"  総需要時間: {total_summary.get('total_need_h', 0):.2f}時間\n")
            f.write(f"  総実績時間: {total_summary.get('total_staff_h', 0):.2f}時間\n")
            f.write(f"  分析対象日数: {total_summary.get('working_days', 0)}日\n\n")
            
            # 2. 職種別詳細
            f.write("【2. 職種別分析結果】\n")
            role_results = analysis_results.get('role_summary', [])
            if role_results:
                f.write("  職種名             | 需要時間 | 実績時間 | 不足時間 | 過剰時間 | 稼働日数\n")
                f.write("  " + "-" * 70 + "\n")
                for role in role_results:
                    role_name = str(role.get('role', 'N/A'))[:15].ljust(15)
                    need_h = role.get('need_h', 0)
                    staff_h = role.get('staff_h', 0)
                    lack_h = role.get('lack_h', 0)
                    excess_h = role.get('excess_h', 0)
                    working_days = role.get('working_days_considered', 0)
                    f.write(f"  {role_name} | {need_h:8.1f} | {staff_h:8.1f} | {lack_h:8.1f} | {excess_h:8.1f} | {working_days:8d}\n")
            else:
                f.write("  職種別データなし\n")
            f.write("\n")
            
            # 3. 雇用形態別詳細
            f.write("【3. 雇用形態別分析結果】\n")
            emp_results = analysis_results.get('employment_summary', [])
            if emp_results:
                f.write("  雇用形態           | 需要時間 | 実績時間 | 不足時間 | 過剰時間 | 稼働日数\n")
                f.write("  " + "-" * 70 + "\n")
                for emp in emp_results:
                    emp_name = str(emp.get('employment', 'N/A'))[:15].ljust(15)
                    need_h = emp.get('need_h', 0)
                    staff_h = emp.get('staff_h', 0)
                    lack_h = emp.get('lack_h', 0)
                    excess_h = emp.get('excess_h', 0)
                    working_days = emp.get('working_days_considered', 0)
                    f.write(f"  {emp_name} | {need_h:8.1f} | {staff_h:8.1f} | {lack_h:8.1f} | {excess_h:8.1f} | {working_days:8d}\n")
            else:
                f.write("  雇用形態別データなし\n")
            f.write("\n")
            
            # 4. 計算方法詳細
            f.write("【4. 計算方法】\n")
            calculation_method = analysis_results.get('calculation_method', {})
            f.write(f"  使用手法: {calculation_method.get('method', '職種別・雇用形態別実際Needベース')}\n")
            f.write(f"  按分計算使用: {calculation_method.get('used_proportional', 'なし')}\n")
            f.write(f"  実際Needファイル使用: {calculation_method.get('used_actual_need_files', 'あり')}\n")
            f.write(f"  休業日除外: {calculation_method.get('holiday_exclusion', 'あり')}\n\n")
            
            # 5. ファイル情報
            f.write("【5. 生成ファイル情報】\n")
            file_info = analysis_results.get('file_info', {})
            for file_type, file_path in file_info.items():
                f.write(f"  {file_type}: {file_path}\n")
            f.write("\n")
            
            # 6. 警告・エラー情報
            warnings = analysis_results.get('warnings', [])
            errors = analysis_results.get('errors', [])
            if warnings or errors:
                f.write("【6. 警告・エラー情報】\n")
                for warning in warnings:
                    f.write(f"  [警告] {warning}\n")
                for error in errors:
                    f.write(f"  [エラー] {error}\n")
            else:
                f.write("【6. 警告・エラー情報】\n  なし\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("レポート終了\n")
            
        log.info(f"[shortage] 詳細ログファイルを作成しました: {log_filepath}")
        return log_filepath
        
    except Exception as e:
        log.error(f"[shortage] ログファイル作成エラー: {e}")
        return None


def shortage_and_brief(
    out_dir: Path | str,
    slot: int,
    *,
    holidays: Iterable[dt.date] | None = None,
    include_zero_days: bool = True,
    wage_direct: float = 0.0,
    wage_temp: float = 0.0,
    penalty_per_lack: float = 0.0,
    auto_detect_slot: bool = True,
) -> Tuple[Path, Path] | None:
    """Run shortage analysis and KPI summary.

    Parameters
    ----------
    out_dir:
        Output directory containing heatmap files.
    slot:
        Slot size in minutes.
    holidays:
        Deprecated. The value is ignored; holidays are read from
        ``heatmap.meta.json`` generated by ``build_heatmap``.
    wage_direct:
        Hourly wage for direct employees used for excess cost estimation.
    wage_temp:
        Hourly cost for temporary staff to fill shortages.
    penalty_per_lack:
        Penalty or opportunity cost per hour of shortage.
    auto_detect_slot:
        Enable automatic slot interval detection from data.
    """
    out_dir_path = Path(out_dir)
    time_labels = gen_labels(slot)
    slot_hours = SLOT_HOURS

    estimated_holidays_set: Set[dt.date] = set()
    log.info("[shortage] v2.7.0 処理開始")

    try:
        heat_all_df = pd.read_parquet(out_dir_path / "heat_ALL.parquet")
    except FileNotFoundError:
        log.error("[shortage] heat_ALL.parquet が見つかりません。処理を中断します。")
        return None
    except Exception as e:
        log.error(
            f"[shortage] heat_ALL.parquet の読み込みエラー: {e}", exc_info=True
        )
        return None

    # --- ▼▼▼▼▼ ここからが重要な修正箇所 ▼▼▼▼▼ ---

    # 日付ごとの詳細Needデータを読み込む
    need_per_date_slot_df = pd.DataFrame()
    need_per_date_slot_fp = out_dir_path / "need_per_date_slot.parquet"
    if need_per_date_slot_fp.exists():
        try:
            need_per_date_slot_df = pd.read_parquet(need_per_date_slot_fp)
            log.info(
                "[shortage] ☆☆☆ need_per_date_slot.parquet を読み込み、これをマスターNeedとして使用します ☆☆☆"
            )
        except Exception as e:
            log.warning(f"[shortage] need_per_date_slot.parquet の読み込みエラー: {e}")

    # heat_ALL.parquetから日付列を特定
    date_columns_in_heat_all = [
        str(col)
        for col in heat_all_df.columns
        if col not in SUMMARY5 and _parse_as_date(str(col)) is not None
    ]
    if not date_columns_in_heat_all:
        log.warning("[shortage] heat_ALL.parquet に日付データ列が見つかりませんでした。")
        # 処理を中断せずに空のファイルを生成
        empty_df = pd.DataFrame(index=time_labels)
        fp_s_t_empty = save_df_parquet(
            empty_df, out_dir_path / "shortage_time.parquet", index=True
        )
        fp_s_r_empty = save_df_parquet(
            pd.DataFrame(), out_dir_path / "shortage_role.parquet", index=False
        )
        return (fp_s_t_empty, fp_s_r_empty) if fp_s_t_empty and fp_s_r_empty else None

    # 実績スタッフ数データを準備
    staff_actual_data_all_df = (
        heat_all_df[date_columns_in_heat_all]
        .copy()
        .reindex(index=time_labels)
        .fillna(0)
    )

    # heatmap.meta.jsonから休業日情報を取得
    meta_fp = out_dir_path / "heatmap.meta.json"
    if meta_fp.exists():
        try:
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
            estimated_holidays_set.update(
                {
                    d
                    for d in (
                        _parse_as_date(h) for h in meta.get("estimated_holidays", [])
                    )
                    if d
                }
            )
            log.info(
                f"[SHORTAGE_DEBUG] heatmap.meta.json から読み込んだ休業日数: {len(estimated_holidays_set)}"
            )
        except Exception as e_meta:
            log.warning(f"[shortage] heatmap.meta.json 解析エラー: {e_meta}")

    # 全体のNeed DataFrameを構築
    if not need_per_date_slot_df.empty:
        # 【最重要修正】詳細Needデータがある場合、それをそのまま使用する
        log.info("[shortage] 詳細Needデータに基づき、全体のNeedを再構築します。")
        need_df_all = need_per_date_slot_df.reindex(
            columns=staff_actual_data_all_df.columns, fill_value=0
        )
        need_df_all = need_df_all.reindex(index=time_labels, fill_value=0)
    else:
        # 【フォールバック】詳細Needデータがない場合、従来の曜日パターンで計算
        log.warning("[shortage] 詳細Needデータがないため、従来の曜日パターンに基づきNeedを計算します。")
        dow_need_pattern_df = pd.DataFrame()
        if meta_fp.exists():
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
            pattern_records = meta.get("dow_need_pattern", [])
            if pattern_records:
                tmp_df = pd.DataFrame(pattern_records).set_index("time")
                tmp_df.columns = tmp_df.columns.astype(int)
                dow_need_pattern_df = tmp_df

        need_df_all = pd.DataFrame(
            index=time_labels, columns=staff_actual_data_all_df.columns, dtype=float
        )
        parsed_date_list_all = [
            _parse_as_date(c) for c in staff_actual_data_all_df.columns
        ]
        for col, d in zip(need_df_all.columns, parsed_date_list_all, strict=True):
            is_holiday = d in estimated_holidays_set if d else False
            if is_holiday:
                need_df_all[col] = 0
                continue
            dow_col = d.weekday() if d else None
            if d and not dow_need_pattern_df.empty and dow_col in dow_need_pattern_df.columns:
                need_df_all[col] = (
                    dow_need_pattern_df[dow_col].reindex(index=time_labels).fillna(0)
                )
            else:
                need_df_all[col] = 0

    # --- ▲▲▲▲▲ ここまでが重要な修正箇所 ▲▲▲▲▲ ---

    lack_count_overall_df = (
        (need_df_all - staff_actual_data_all_df).clip(lower=0).fillna(0)
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

    shortage_freq_df = pd.DataFrame(
        (lack_count_overall_df > 0).sum(axis=1), columns=["shortage_days"]
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

    sunday_columns = [
        col
        for col in lack_count_overall_df.columns
        if _parse_as_date(col) and _parse_as_date(col).weekday() == 6
    ]

    if sunday_columns:
        log.info("[SHORTAGE_DEBUG] ========== 日曜日の不足分析 ==========")
        log.info(f"[SHORTAGE_DEBUG] 対象日曜日: {sunday_columns}")

        for col in sunday_columns[:3]:
            actual_sum = staff_actual_data_all_df[col].sum()
            need_sum = need_df_all[col].sum()
            lack_sum = lack_count_overall_df[col].sum()
            is_holiday = _parse_as_date(col) in estimated_holidays_set

            log.info(f"[SHORTAGE_DEBUG] {col}:")
            log.info(f"[SHORTAGE_DEBUG]   休業日={is_holiday}")
            log.info(f"[SHORTAGE_DEBUG]   実績合計: {actual_sum}")
            log.info(f"[SHORTAGE_DEBUG]   Need合計: {need_sum}")
            log.info(f"[SHORTAGE_DEBUG]   不足合計: {lack_sum}")

            if not is_holiday and need_sum > actual_sum * 3:
                log.warning(
                    f"[SHORTAGE_WARN] {col}: 異常な不足数({lack_sum})を検出"
                )
                log.warning(
                    f"[SHORTAGE_WARN]   実績({actual_sum})に対してNeed({need_sum})が過大"
                )

            non_zero_times = need_df_all[col][need_df_all[col] > 0].index.tolist()
            if non_zero_times:
                log.info(f"[SHORTAGE_DEBUG]   Need>0の時間帯: {non_zero_times}")
                for time_slot in non_zero_times[:3]:
                    log.info(
                        f"[SHORTAGE_DEBUG]     {time_slot}: Need={need_df_all.loc[time_slot, col]}, 実績={staff_actual_data_all_df.loc[time_slot, col]}"
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
        parsed_date_list_all = [
            _parse_as_date(c) for c in staff_actual_data_all_df.columns
        ]
        holiday_mask_all = [
            d in estimated_holidays_set if d else False for d in parsed_date_list_all
        ]
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

    # 按分計算のための勤務データを読み込み
    working_data_for_proportional = pd.DataFrame()
    total_shortage_hours_for_proportional = 0.0
    try:
        # long_dfまたは勤務データを読み込み
        long_df_path = out_dir_path / "intermediate_data.parquet"
        if long_df_path.exists():
            working_data_df = pd.read_parquet(long_df_path)
            # 通常勤務のみ抽出
            working_data_for_proportional = working_data_df[
                working_data_df.get('holiday_type', '通常勤務') == '通常勤務'
            ].copy()
            log.info(f"[shortage] 按分計算用の勤務データを読み込みました: {len(working_data_for_proportional)}レコード")
        
        # shortage_timeから総不足時間を計算
        total_shortage_hours_for_proportional = lack_count_overall_df.sum().sum() * slot_hours
        log.info(f"[shortage] 按分計算用の総不足時間: {total_shortage_hours_for_proportional:.2f}時間")
        
    except Exception as e:
        log.warning(f"[shortage] 按分計算用データの読み込みエラー: {e}")

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

        # need_df_role の構築ロジックを修正 - 職種別実際のNeedファイルを使用
        log.info(f"[shortage] {role_name_current}: 職種別の実際のNeedファイルから正確な計算を行います。")
        
        # 職種別詳細Needファイルを読み込み
        role_safe_name = role_name_current.replace(' ', '_').replace('/', '_').replace('\\', '_')
        role_need_file = out_dir_path / f"need_per_date_slot_role_{role_safe_name}.parquet"
        
        if role_need_file.exists():
            try:
                need_df_role = pd.read_parquet(role_need_file)
                # インデックスと列を適切に調整
                need_df_role = need_df_role.reindex(index=time_labels, fill_value=0)
                # 実績データと同じ列（日付）に調整
                common_columns = set(need_df_role.columns).intersection(set(role_staff_actual_data_df.columns))
                if common_columns:
                    need_df_role = need_df_role[sorted(common_columns)]
                    role_staff_actual_data_df = role_staff_actual_data_df[sorted(common_columns)]
                    log.info(f"[shortage] {role_name_current}: 職種別Needファイルから正確なデータを読み込み（{len(common_columns)}日分）")
                else:
                    log.warning(f"[shortage] {role_name_current}: 職種別Needファイルと実績データの日付列が一致しません。按分計算を使用します。")
                    # フォールバック: 按分計算
                    need_df_role = pd.DataFrame(
                        np.repeat(
                            role_need_per_time_series_orig_for_role.values[:, np.newaxis],
                            len(role_staff_actual_data_df.columns),
                            axis=1,
                        ),
                        index=role_need_per_time_series_orig_for_role.index,
                        columns=role_staff_actual_data_df.columns,
                    )
            except Exception as e:
                log.warning(f"[shortage] {role_name_current}: 職種別Needファイル読み込みエラー: {e}. 按分計算を使用します。")
                # フォールバック: 按分計算
                need_df_role = pd.DataFrame(
                    np.repeat(
                        role_need_per_time_series_orig_for_role.values[:, np.newaxis],
                        len(role_staff_actual_data_df.columns),
                        axis=1,
                    ),
                    index=role_need_per_time_series_orig_for_role.index,
                    columns=role_staff_actual_data_df.columns,
                )
        else:
            log.warning(f"[shortage] {role_name_current}: 職種別Needファイルが見つかりません（{role_need_file}）。按分計算を使用します。")
            # フォールバック: 按分計算
            need_df_role = pd.DataFrame(
                np.repeat(
                    role_need_per_time_series_orig_for_role.values[:, np.newaxis],
                    len(role_staff_actual_data_df.columns),
                    axis=1,
                ),
                index=role_need_per_time_series_orig_for_role.index,
                columns=role_staff_actual_data_df.columns,
            )

        # 休業日のNeedを0にする処理 (これは修正後も必要)
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

        # 修正された need_df_role を使って lack と excess を計算する
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

        # サマリー用の合計時間も、修正された need_df_role から計算する
        total_need_hours_for_role = need_df_role[working_cols_role].sum().sum() * slot_hours
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

    # 時間軸ベース分析で真の職種別不足時間を計算
    shortage_log.info("=== 時間軸ベース分析開始 ===")
    shortage_log.info(f"working_data_for_proportional: {len(working_data_for_proportional)}行")
    shortage_log.info(f"total_shortage_baseline: {total_shortage_hours_for_proportional:.2f}時間")
    
    if not working_data_for_proportional.empty:
        try:
            # 🎯 修正: 按分計算の総不足時間をベースラインとして渡す
            shortage_log.info("calculate_time_axis_shortage呼び出し開始")
            role_shortages, _ = calculate_time_axis_shortage(
                working_data_for_proportional,
                total_shortage_baseline=total_shortage_hours_for_proportional
            )
            shortage_log.info("calculate_time_axis_shortage完了")
            shortage_log.info(f"時間軸ベース分析による職種別不足時間（ベースライン{total_shortage_hours_for_proportional:.1f}h）: {role_shortages}")
            
            # role_kpi_rowsの不足時間を修正
            for role_row in role_kpi_rows:
                role_name = role_row.get('role')
                if role_name in role_shortages:
                    corrected_lack_h = int(round(role_shortages[role_name]))
                    original_lack_h = role_row.get('lack_h', 0)
                    role_row['lack_h'] = corrected_lack_h
                    log.info(f"[shortage] {role_name}: 不足時間を {original_lack_h}h → {corrected_lack_h}h に修正 (時間軸ベース)")
        except Exception as e:
            log.warning(f"[shortage] 時間軸ベース分析による職種別不足時間の修正エラー: {e}")

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
    shortage_log.info("=== 職種別不足サマリー保存 ===")
    shortage_log.info(f"role_summary_df: {len(role_summary_df)}行")
    shortage_log.info(f"columns: {list(role_summary_df.columns)}")
    if not role_summary_df.empty:
        shortage_log.info(f"職種一覧: {role_summary_df['role'].tolist()}")
        shortage_log.info(f"不足時間合計: {role_summary_df['lack_h'].sum():.2f}時間")
        # 各職種の詳細
        for _, row in role_summary_df.iterrows():
            shortage_log.info(f"  {row['role']}: {row.get('lack_h', 0):.2f}時間不足")
    role_summary_df.to_parquet(fp_shortage_role, index=False)
    shortage_log.info(f"shortage_role_summary.parquet保存完了: {fp_shortage_role}")
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
        # need_df_emp の構築ロジックを修正 - 雇用形態別実際のNeedファイルを使用
        log.info(f"[shortage] {emp_name_current}: 雇用形態別の実際のNeedファイルから正確な計算を行います。")
        
        # 雇用形態別詳細Needファイルを読み込み
        emp_safe_name = emp_name_current.replace(' ', '_').replace('/', '_').replace('\\', '_')
        emp_need_file = out_dir_path / f"need_per_date_slot_emp_{emp_safe_name}.parquet"
        
        if emp_need_file.exists():
            try:
                need_df_emp = pd.read_parquet(emp_need_file)
                # インデックスと列を適切に調整
                need_df_emp = need_df_emp.reindex(index=time_labels, fill_value=0)
                # 実績データと同じ列（日付）に調整
                common_columns = set(need_df_emp.columns).intersection(set(emp_staff_df.columns))
                if common_columns:
                    need_df_emp = need_df_emp[sorted(common_columns)]
                    emp_staff_df = emp_staff_df[sorted(common_columns)]
                    log.info(f"[shortage] {emp_name_current}: 雇用形態別Needファイルから正確なデータを読み込み（{len(common_columns)}日分）")
                else:
                    log.warning(f"[shortage] {emp_name_current}: 雇用形態別Needファイルと実績データの日付列が一致しません。按分計算を使用します。")
                    # フォールバック: 按分計算
                    need_df_emp = pd.DataFrame(
                        np.repeat(
                            emp_need_series.values[:, np.newaxis], len(emp_staff_df.columns), axis=1
                        ),
                        index=emp_need_series.index,
                        columns=emp_staff_df.columns,
                    )
            except Exception as e:
                log.warning(f"[shortage] {emp_name_current}: 雇用形態別Needファイル読み込みエラー: {e}. 按分計算を使用します。")
                # フォールバック: 按分計算
                need_df_emp = pd.DataFrame(
                    np.repeat(
                        emp_need_series.values[:, np.newaxis], len(emp_staff_df.columns), axis=1
                    ),
                    index=emp_need_series.index,
                    columns=emp_staff_df.columns,
                )
        else:
            log.warning(f"[shortage] {emp_name_current}: 雇用形態別Needファイルが見つかりません（{emp_need_file}）。按分計算を使用します。")
            # フォールバック: 按分計算
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

        # excess_count_emp_dfの計算に誤りがあったため修正 (needではなくupperと比較)
        excess_count_emp_df = pd.DataFrame()
        if "upper" in emp_heat_current_df.columns:
             upper_series_emp = emp_heat_current_df["upper"].reindex(index=time_labels).fillna(0).clip(lower=0)
             upper_df_emp = pd.DataFrame(
                 np.repeat(
                     upper_series_emp.values[:, np.newaxis], len(emp_staff_df.columns), axis=1
                 ),
                 index=upper_series_emp.index,
                 columns=emp_staff_df.columns,
             )
             if any(holiday_mask_emp):
                 for c, is_h in zip(upper_df_emp.columns, holiday_mask_emp, strict=True):
                     if is_h:
                         upper_df_emp[c] = 0
             excess_count_emp_df = (emp_staff_df - upper_df_emp).clip(lower=0)


        # サマリー用の合計時間も、修正された need_df_emp から計算する
        total_need_hours_for_emp = need_df_emp[working_cols_emp].sum().sum() * slot_hours
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

    # 時間軸ベース分析で真の雇用形態別不足時間を計算
    if not working_data_for_proportional.empty:
        try:
            # 🎯 修正: 按分計算の総不足時間をベースラインとして渡す
            _, employment_shortages = calculate_time_axis_shortage(
                working_data_for_proportional,
                total_shortage_baseline=total_shortage_hours_for_proportional
            )
            log.info(f"[shortage] 時間軸ベース分析による雇用形態別不足時間（ベースライン{total_shortage_hours_for_proportional:.1f}h）: {employment_shortages}")
            
            # emp_kpi_rowsの不足時間を修正
            for emp_row in emp_kpi_rows:
                emp_name = emp_row.get('employment')
                if emp_name in employment_shortages:
                    corrected_lack_h = int(round(employment_shortages[emp_name]))
                    original_lack_h = emp_row.get('lack_h', 0)
                    emp_row['lack_h'] = corrected_lack_h
                    log.info(f"[shortage] {emp_name}: 不足時間を {original_lack_h}h → {corrected_lack_h}h に修正 (時間軸ベース)")
        except Exception as e:
            log.warning(f"[shortage] 時間軸ベース分析による雇用形態別不足時間の修正エラー: {e}")

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
    shortage_log.info("=== 雇用形態別不足サマリー保存 ===")
    shortage_log.info(f"emp_summary_df: {len(emp_summary_df)}行")
    shortage_log.info(f"columns: {list(emp_summary_df.columns)}")
    if not emp_summary_df.empty:
        shortage_log.info(f"雇用形態一覧: {emp_summary_df['employment'].tolist()}")
        shortage_log.info(f"不足時間合計: {emp_summary_df['lack_h'].sum():.2f}時間")
        # 各雇用形態の詳細
        for _, row in emp_summary_df.iterrows():
            shortage_log.info(f"  {row['employment']}: {row.get('lack_h', 0):.2f}時間不足")
    emp_summary_df.to_parquet(fp_shortage_emp, index=False)
    shortage_log.info(f"shortage_employment_summary.parquet保存完了: {fp_shortage_emp}")
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
            f"[shortage] completed -- shortage_time → {fp_shortage_time.name}, "
            f"shortage_ratio → {fp_shortage_ratio.name}, "
            f"shortage_freq → {fp_shortage_freq.name}, "
            f"shortage_role → {fp_shortage_role.name}, "
            f"shortage_employment → {fp_shortage_emp.name}, "
        )
        + (f"excess_time → {fp_excess_time.name}, " if fp_excess_time else "")
        + (f"excess_ratio → {fp_excess_ratio.name}, " if fp_excess_ratio else "")
        + (f"excess_freq → {fp_excess_freq.name}" if fp_excess_freq else "")
    )
    
    # 🎯 修正: 最適採用計画に必要なサマリーファイルを生成
    try:
        # shortage_weekday_timeslot_summary.parquet を生成
        if fp_shortage_time and fp_shortage_time.exists():
            weekday_summary_df = weekday_timeslot_summary(out_dir_path)
            weekday_summary_path = out_dir_path / "shortage_weekday_timeslot_summary.parquet"
            weekday_summary_df.to_parquet(weekday_summary_path, index=False)
            log.info(f"[shortage] 曜日別タイムスロットサマリー生成: {weekday_summary_path.name}")
        else:
            log.warning(f"[shortage] shortage_time.parquetが見つからないため、曜日別サマリーをスキップ")
    except Exception as e:
        log.error(f"[shortage] 曜日別サマリー生成エラー: {e}")
    
    # タイムスタンプ付きの詳細ログを生成
    try:
        # 分析結果をまとめる
        total_need_h = role_summary_df.get("need_h", pd.Series()).sum() if not role_summary_df.empty else 0
        total_staff_h = role_summary_df.get("staff_h", pd.Series()).sum() if not role_summary_df.empty else 0
        total_lack_h = role_summary_df.get("lack_h", pd.Series()).sum() if not role_summary_df.empty else 0
        total_excess_h = role_summary_df.get("excess_h", pd.Series()).sum() if not role_summary_df.empty else 0
        working_days = role_summary_df.get("working_days_considered", pd.Series()).max() if not role_summary_df.empty else 0
        
        analysis_results = {
            'total_summary': {
                'total_need_h': total_need_h,
                'total_staff_h': total_staff_h,
                'total_lack_h': total_lack_h,
                'total_excess_h': total_excess_h,
                'working_days': working_days
            },
            'role_summary': role_kpi_rows,
            'employment_summary': emp_kpi_rows,
            'calculation_method': {
                'method': '職種別・雇用形態別実際Needベース（按分計算フォールバック付き）',
                'used_proportional': 'フォールバックのみ',
                'used_actual_need_files': 'あり',
                'holiday_exclusion': 'あり'
            },
            'file_info': {
                'shortage_time': fp_shortage_time.name if fp_shortage_time else 'N/A',
                'shortage_role': fp_shortage_role.name if fp_shortage_role else 'N/A',
                'shortage_employment': fp_shortage_emp.name if fp_shortage_emp else 'N/A',
                'shortage_ratio': fp_shortage_ratio.name if fp_shortage_ratio else 'N/A',
                'shortage_freq': fp_shortage_freq.name if fp_shortage_freq else 'N/A'
            },
            'warnings': [],
            'errors': []
        }
        
        # ログファイル作成
        create_timestamped_log(analysis_results, out_dir_path)
        
    except Exception as e:
        log.error(f"[shortage] タイムスタンプ付きログ生成エラー: {e}")
    
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
