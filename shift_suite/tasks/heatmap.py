# shift_suite / tasks / heatmap.py
# v1.8.1 (日曜日Need計算修正版)
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Set

import numpy as np
import openpyxl
import pandas as pd
import logging
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

from .constants import SUMMARY5
from shift_suite.i18n import translate as _

# 'log' という名前でロガーを取得 (utils.pyからインポートされるlogと同じ)
import pyarrow as pa
import pyarrow.parquet as pq
from .utils import (
    _parse_as_date,
    derive_max_staff,
    gen_labels,
    log,
    safe_sheet,
    save_df_xlsx,
    write_meta,
    validate_need_calculation,
)

analysis_logger = logging.getLogger('analysis')
# 簡素化された統合Need計算システム
try:
    from shift_suite.core.statistics_engine import AdaptiveStatisticsEngine
    _unified_stats_engine = AdaptiveStatisticsEngine()
    _UNIFIED_SYSTEM_AVAILABLE = True
    analysis_logger.info("[UNIFIED] 統合システム利用可能")
except ImportError as e:
    _unified_stats_engine = None
    _UNIFIED_SYSTEM_AVAILABLE = False
    analysis_logger.warning(f"[UNIFIED] 統合システム不可: {e}")


# 新規追加: 通常勤務の判定用定数
DEFAULT_HOLIDAY_TYPE = "通常勤務"

STAFF_ALIASES = ["staff", "氏名", "名前", "従業員"]
ROLE_ALIASES = ["role", "職種", "役職", "部署"]


def _resolve(df: pd.DataFrame, prefer: str, aliases: list[str], new: str) -> str:
    if prefer in df.columns:
        df.rename(columns={prefer: new}, inplace=True)
        return new
    for alias_name in aliases:
        if alias_name in df.columns:
            df.rename(columns={alias_name: new}, inplace=True)
            return new
    raise KeyError(
        f"列 '{prefer}' またはそのエイリアス {aliases} がDataFrameに見つかりません。"
    )


def _apply_conditional_formatting_to_worksheet(
    worksheet: openpyxl.worksheet.worksheet.Worksheet, df_data_columns: pd.Index
):
    log.debug(f"[heatmap._apply_cf] 書式設定対象のワークシート: '{worksheet.title}'")
    log.debug(
        f"[heatmap._apply_cf] 書式設定の基準となるデータ列 (df_data_columns): {df_data_columns.tolist() if isinstance(df_data_columns, pd.Index) else df_data_columns}"
    )
    if worksheet.max_row <= 1:
        return
    if (
        df_data_columns.empty
        if isinstance(df_data_columns, pd.Index)
        else not df_data_columns
    ):
        return
    first_data_col_excel_idx = 2
    last_data_col_excel_idx = (
        first_data_col_excel_idx + (len(df_data_columns) - 1)
        if (isinstance(df_data_columns, pd.Index) and not df_data_columns.empty)
        or (not isinstance(df_data_columns, pd.Index) and df_data_columns)
        else first_data_col_excel_idx - 1
    )
    if last_data_col_excel_idx < first_data_col_excel_idx:
        return
    range_start_cell = "B2"
    range_end_col_letter = get_column_letter(last_data_col_excel_idx)
    range_end_row_num = worksheet.max_row
    data_range_string = f"{range_start_cell}:{range_end_col_letter}{range_end_row_num}"
    log.info(
        f"[heatmap._apply_cf] シート '{worksheet.title}' に条件付き書式を適用します。範囲: {data_range_string}"
    )
    try:
        color_scale_rule = ColorScaleRule(
            start_type="min",
            start_color="FFFFE0",
            mid_type="percentile",
            mid_value=50,
            mid_color="FFA500",
            end_type="max",
            end_color="FF0000",
        )
        worksheet.conditional_formatting.add(data_range_string, color_scale_rule)
    except Exception as e:
        log.error(f"[heatmap._apply_cf] 条件付き書式適用中にエラー: {e}", exc_info=True)


def _apply_holiday_column_styling(
    worksheet: openpyxl.worksheet.worksheet.Worksheet,
    date_columns_in_excel: pd.Index,
    estimated_holidays: Set[dt.date],
    utils_parse_as_date_func,
):
    if not estimated_holidays or date_columns_in_excel.empty:
        return
    holiday_fill = PatternFill(
        start_color="D3D3D3", end_color="D3D3D3", fill_type="solid"
    )
    first_data_col_excel_letter_idx = 2
    for i, col_name_excel_str in enumerate(date_columns_in_excel):
        current_col_date = utils_parse_as_date_func(str(col_name_excel_str))
        if current_col_date and current_col_date in estimated_holidays:
            target_excel_col_idx = first_data_col_excel_letter_idx + i
            col_letter = get_column_letter(target_excel_col_idx)
            for row_idx in range(1, worksheet.max_row + 1):
                worksheet[f"{col_letter}{row_idx}"].fill = holiday_fill


def calculate_pattern_based_need(
    actual_staff_by_slot_and_date: pd.DataFrame,
    ref_start_date: dt.date,
    ref_end_date: dt.date,
    statistic_method: str,
    remove_outliers: bool,
    iqr_multiplier: float = 1.5,
    slot_minutes_for_empty: int = 30,
    *,
    holidays: set[dt.date] | None = None,
    adjustment_factor: float = 1.0,
    include_zero_days: bool = True,
    all_dates_in_period: list[dt.date] | None = None,
    long_df: pd.DataFrame | None = None,  # 連続勤務検出用
) -> pd.DataFrame:
    # 修正箇所: logger.info -> log.info など、ロガー名を 'log' に統一
    log.info(
        f"[heatmap.calculate_pattern_based_need] 参照期間: {ref_start_date} - {ref_end_date}, 手法: {statistic_method}, 外れ値除去: {remove_outliers}"
    )

    # ★★★ 動的連続勤務検出システム追加 ★★★
    continuous_shift_detector = None
    if long_df is not None and not long_df.empty:
        try:
            from .dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
            
            # 設定ファイルパスの決定
            config_path = Path(__file__).parent.parent / "config" / "dynamic_continuous_shift_config.json"
            
            # 動的検出器の初期化
            continuous_shift_detector = DynamicContinuousShiftDetector(config_path)
            
            # wt_dfも渡して完全に動的な検出を実行
            wt_df_for_detection = None
            if 'wt_df' in locals() or 'wt_df' in globals():
                wt_df_for_detection = wt_df if 'wt_df' in locals() else globals().get('wt_df')
            
            continuous_shifts = continuous_shift_detector.detect_continuous_shifts(long_df, wt_df_for_detection)
            log.info(f"[DYNAMIC_CONTINUOUS] 動的連続勤務検出完了: {len(continuous_shifts)}件")
            
            # 検出統計出力
            summary = continuous_shift_detector.get_detection_summary()
            log.info(f"[DYNAMIC_CONTINUOUS] 統計: {summary}")
            
            # 学習した設定の自動保存
            if summary.get('total_count', 0) > 0:
                learned_config_path = config_path.parent / f"learned_config_{dt.date.today().strftime('%Y%m%d')}.json"
                continuous_shift_detector.export_config(learned_config_path)
                log.info(f"[DYNAMIC_CONTINUOUS] 学習済み設定保存: {learned_config_path}")
            
        except Exception as e:
            log.warning(f"[DYNAMIC_CONTINUOUS] 動的連続勤務検出エラー: {e}")
            # フォールバック: 従来のシステムを使用
            try:
                from .continuous_shift_detector import ContinuousShiftDetector
                continuous_shift_detector = ContinuousShiftDetector()
                continuous_shifts = continuous_shift_detector.detect_continuous_shifts(long_df)
                log.info(f"[FALLBACK] フォールバック連続勤務検出: {len(continuous_shifts)}件")
            except Exception as fallback_error:
                log.error(f"[FALLBACK] フォールバック検出もエラー: {fallback_error}")
                continuous_shift_detector = None

    time_index_labels = pd.Index(gen_labels(slot_minutes_for_empty), name="time")
    default_dow_need_df = pd.DataFrame(
        0, index=time_index_labels, columns=range(7)
    )  # 月曜0 - 日曜6

    if actual_staff_by_slot_and_date.empty:
        log.warning(
            "[heatmap.calculate_pattern_based_need] 入力実績データが空です。デフォルトの0 needを返します。"
        )
        return default_dow_need_df

    # actual_staff_by_slot_and_date の列名が日付オブジェクトであることを確認・変換
    # 呼び出し元(build_heatmap)で列名をdt.dateオブジェクトに変換済みのものを渡すように修正
    df_for_calc = actual_staff_by_slot_and_date.copy()

    holidays_set = set(holidays or [])

    if include_zero_days:
        log.info("[NEED_FIX] include_zero_days=True → 休業日除外なし")

    # 重要な修正：全期間の日付を考慮する
    if all_dates_in_period and include_zero_days:
        all_dates_in_ref = [
            d for d in all_dates_in_period
            if isinstance(d, dt.date) and ref_start_date <= d <= ref_end_date and d not in holidays_set
        ]

        # 実績がない日付を0で埋める
        for date in all_dates_in_ref:
            if date not in df_for_calc.columns:
                df_for_calc[date] = 0

        log.info(f"[NEED_FIX] 全期間の日付を考慮: 元の列数={len(actual_staff_by_slot_and_date.columns)}, 補完後={len(df_for_calc.columns)}")

    # 参照期間でデータをフィルタリング (列名がdt.dateオブジェクトであることを前提)
    cols_to_process_dow = [
        col_date
        for col_date in df_for_calc.columns
        if (
            isinstance(col_date, dt.date)
            and ref_start_date <= col_date <= ref_end_date
            and col_date not in holidays_set
        )
    ]

    if not cols_to_process_dow:
        log.warning(
            f"[heatmap.calculate_pattern_based_need] 参照期間 ({ref_start_date} - {ref_end_date}) に該当する実績データがありません。"
        )
        return default_dow_need_df

    filtered_slot_df_dow = df_for_calc[cols_to_process_dow]
    dow_need_df_calculated = pd.DataFrame(
        index=filtered_slot_df_dow.index, columns=range(7), dtype=float
    )

    for day_of_week_idx in range(7):
        dow_cols_to_agg = [
            col_dt
            for col_dt in filtered_slot_df_dow.columns
            if col_dt.weekday() == day_of_week_idx
        ]

        # デバッグ: 曜日名マッピング
        dow_names = {0: "月曜日", 1: "火曜日", 2: "水曜日", 3: "木曜日", 4: "金曜日", 5: "土曜日", 6: "日曜日"}
        dow_name = dow_names.get(day_of_week_idx, f"曜日{day_of_week_idx}")
        log.info(f"[NEED_DEBUG] === {dow_name} ({day_of_week_idx}) 処理開始 ===")
        log.info(f"[NEED_DEBUG] 対象日付数: {len(dow_cols_to_agg)}")

        if not dow_cols_to_agg:
            log.warning(f"[NEED_DEBUG] {dow_name}: 対象データなし")
            dow_need_df_calculated[day_of_week_idx] = 0
            continue

        # デバッグ情報出力（全曜日）
        log.info(
            f"[NEED_DEBUG] 対象日付例: {[d.strftime('%Y-%m-%d') for d in dow_cols_to_agg[:3]]}{'...' if len(dow_cols_to_agg) > 3 else ''}"
        )

        data_for_dow_calc = filtered_slot_df_dow[dow_cols_to_agg]

        # ★★★ 統合Need計算システム統合修正 ★★★
        # 曜日固有ロジックを除去し、動的データ対応の汎用統計計算を適用
        is_significant_holiday = False
        
        # 日毎の合計人数を初期化（empty対応）
        daily_totals = data_for_dow_calc.sum() if not data_for_dow_calc.empty else pd.Series(dtype=float)
        
        if not data_for_dow_calc.empty:
            avg_staff_per_day_overall = filtered_slot_df_dow.sum().mean()
            avg_staff_per_day_dow = data_for_dow_calc.sum().mean()
            
            # daily_totalsは上記で既に計算済み
            
            analysis_logger.info(
                f"曜日 '{dow_name}'({day_of_week_idx}) の必要人数計算: "
                f"曜日別平均勤務人数 = {avg_staff_per_day_dow:.2f}, "
                f"全体平均勤務人数 = {avg_staff_per_day_overall:.2f}, "
                f"適用中の統計手法 = '{statistic_method}'"
            )
            
            # 統合システムによる適応的判定（曜日に依存しない）
            # 条件を緩和：低実績またはデータの変動が大きい場合に適用
            data_variance = np.var(daily_totals) if len(daily_totals) > 1 else 0
            avg_data_value = daily_totals.mean() if not daily_totals.empty else 0
            
            # 適用条件：日曜日の問題を解決するため条件を大幅緩和
            # データドリブンな統計処理の適用条件（曜日に依存しない）
            # 1. 平均勤務人数が全体の50%未満
            # 2. 全体平均も低い場合（≤1名）は必ず適用
            # 3. データの変動が大きい（変動係数 > 0.5）
            # 4. データ数が少ない（5未満）
            should_apply_adaptive = (
                avg_staff_per_day_overall <= 1.0 or  # 全体が少ない場合
                avg_staff_per_day_dow < (avg_staff_per_day_overall * 0.5) or  # 該当曜日が平均の50%未満
                (avg_data_value > 0 and (np.sqrt(data_variance) / avg_data_value) > 0.5) or  # 変動が大きい
                len(daily_totals) < 5  # データ数が少ない
            )
            
            if should_apply_adaptive:
                analysis_logger.warning(
                    f"曜日 '{dow_name}'({day_of_week_idx}) はデータの性質により、"
                    f"統合システムの適応的統計手法を適用します。"
                )
                is_significant_holiday = True
                analysis_logger.info(f"[ADAPTIVE_STATS] {dow_name}: データドリブンな統計処理を適用")
            elif avg_staff_per_day_dow < (avg_staff_per_day_overall * 0.25):
                analysis_logger.warning(
                    f"曜日 '{dow_name}'({day_of_week_idx}) は勤務実績が著しく少ないため、"
                    f"必要人数が実態と乖離する可能性があります。"
                )
                is_significant_holiday = True

        # 日毎の合計人数（上記で既に計算済み）
        # daily_totals = data_for_dow_calc.sum()  # 重複削除
        log.info(f"  各日の総勤務人数: {daily_totals.values.tolist()}")
        log.info(f"  日平均総勤務人数: {daily_totals.mean():.2f}")

        # 時間帯別の詳細（特に日曜日は詳細に）
        if day_of_week_idx == 6:
            log.info("[SUNDAY_DEBUG] ========== 日曜日の詳細分析 ==========")
            log.info("[SUNDAY_DEBUG] 対象期間の全日曜日:")
            for d in dow_cols_to_agg:
                daily_sum = data_for_dow_calc[d].sum()
                log.info(f"[SUNDAY_DEBUG]   {d.strftime('%Y-%m-%d')}: {daily_sum}名")

            log.info("[SUNDAY_DEBUG] 代表的な時間帯の値:")
            sample_times = ["09:00", "12:00", "15:00", "18:00"]
            for time_slot in sample_times:
                if time_slot in data_for_dow_calc.index:
                    values = data_for_dow_calc.loc[time_slot].values.tolist()
                    log.info(f"[SUNDAY_DEBUG]   {time_slot}: {values}")
# ★★★ 統合Need計算システムの統計エンジン適用 ★★★
        # 統計手法を決定する（動的データ対応）
        if is_significant_holiday:
            # 統合システムの適応的統計手法を使用
            analysis_logger.info(
                f" -> 曜日 '{dow_name}' は統合システムの適応的統計手法を適用"
            )
            current_statistic_method = "adaptive"  # 統合システム標識
        else:
            current_statistic_method = statistic_method

        for time_slot_val, row_series_data in data_for_dow_calc.iterrows():
            if include_zero_days:
                values_at_slot_current = [0.0 if pd.isna(v) else float(v) for v in row_series_data]
            else:
                values_at_slot_current = row_series_data.dropna().astype(float).tolist()
            analysis_logger.info(
                f"[DEBUG_NEED_DETAIL] 処理中の時間帯: {time_slot_val} ({dow_name}), 元データ ({len(values_at_slot_current)}点): {values_at_slot_current}"
            )

            if not values_at_slot_current:
                dow_need_df_calculated.loc[time_slot_val, day_of_week_idx] = 0
                continue
            values_for_stat_calc = values_at_slot_current
            if day_of_week_idx == 6 and time_slot_val in ["09:00", "12:00", "15:00"]:
                log.info(f"[SUNDAY_DETAIL] {time_slot_val} 時間帯:")
                log.info(f"[SUNDAY_DETAIL]   元データ: {values_at_slot_current}")
            # 統計値の計算前にデバッグ情報を出力
            if day_of_week_idx == 6 or (day_of_week_idx == 1 and time_slot_val == "09:00"):
                log.info(f"\n  [統計計算デバッグ] {dow_name} {time_slot_val}")
                log.info(f"    元データ: {values_at_slot_current}")
                log.info(f"    データ数: {len(values_at_slot_current)}")

            if remove_outliers and len(values_at_slot_current) >= 4:
                q1_val = np.percentile(values_at_slot_current, 25)
                q3_val = np.percentile(values_at_slot_current, 75)
                iqr_val = q3_val - q1_val
                lower_bound_val = q1_val - iqr_multiplier * iqr_val
                upper_bound_val = q3_val + iqr_multiplier * iqr_val
                values_filtered_outlier = [
                    x_val
                    for x_val in values_at_slot_current
                    if lower_bound_val <= x_val <= upper_bound_val
                ]
                # デバッグ: 外れ値除去の詳細
                if day_of_week_idx == 6 and time_slot_val in ["09:00", "12:00", "15:00"]:
                    log.info(f"[SUNDAY_DETAIL]   外れ値除去後: {values_filtered_outlier}")

                analysis_logger.info(
                    f"[DEBUG_NEED_DETAIL] 外れ値除去実行前 (Q1:{q1_val:.1f}, Q3:{q3_val:.1f}, IQR:{iqr_val:.1f}), フィルタリング後 ({len(values_filtered_outlier)}点): {values_filtered_outlier}"
                )

                if not values_filtered_outlier:
                    log.debug(
                        f"  曜日 {day_of_week_idx}, 時間帯 {time_slot_val}: 外れ値除去後データなし。元のリストで計算します。"
                    )
                else:
                    values_for_stat_calc = values_filtered_outlier
            need_calculated_val = 0.0
            if values_for_stat_calc:
                # ★★★ 統合システム適用 ★★★
                if current_statistic_method == "adaptive" and _UNIFIED_SYSTEM_AVAILABLE:
                    # 統合システムのAdaptiveStatisticsEngineを使用
                    try:
                        need_value, confidence, method = _unified_stats_engine.calculate_need(
                            historical_data=values_for_stat_calc,
                            target_confidence=0.75
                        )
                        need_calculated_val = need_value
                        analysis_logger.info(
                            f"[UNIFIED] 時間帯 {time_slot_val} ({dow_name}): "
                            f"統合Need={need_value:.2f}, 信頼度={confidence:.3f}, 手法={method}"
                        )
                        
                        # 低信頼度の警告
                        if confidence < 0.3:
                            analysis_logger.warning(
                                f"[UNIFIED] 時間帯 {time_slot_val}: 低信頼度 {confidence:.3f}"
                            )
                    except Exception as e:
                        analysis_logger.error(f"[UNIFIED] 統合システムエラー: {e}")
                        # フォールバック: 平均値
                        need_calculated_val = np.mean(values_for_stat_calc)
                        
                elif current_statistic_method == "adaptive":
                    # 統合システム不可の場合のフォールバック
                    analysis_logger.warning("[UNIFIED] 統合システム不可、平均値で代替")
                    need_calculated_val = np.mean(values_for_stat_calc)
                        
                # 従来の統計手法
                elif current_statistic_method == "10パーセンタイル":
                    need_calculated_val = np.percentile(values_for_stat_calc, 10)
                elif current_statistic_method == "25パーセンタイル":
                    need_calculated_val = np.percentile(values_for_stat_calc, 25)
                elif current_statistic_method == "中央値":
                    need_calculated_val = np.median(values_for_stat_calc)
                elif current_statistic_method == "75パーセンタイル":
                    need_calculated_val = np.percentile(values_for_stat_calc, 75)
                elif current_statistic_method == "90パーセンタイル":
                    need_calculated_val = np.percentile(values_for_stat_calc, 90)
                else:  # 平均値
                    need_calculated_val = np.mean(values_for_stat_calc)
            analysis_logger.info(
                f"[DEBUG_NEED_DETAIL] 統計手法({current_statistic_method})適用後のNeed仮値: {need_calculated_val:.2f}"
            )

            # データの中央値が小さい場合はNeedを上限2.0に制限
            if values_at_slot_current and np.median(values_at_slot_current) < 2.0:
                need_calculated_val = min(need_calculated_val, 2.0)
                analysis_logger.info(
                    f"  [NEED_CAP] 曜日 {day_of_week_idx}, 時間帯 {time_slot_val}: "
                    f"実績中央値が2未満のためNeedを {need_calculated_val:.1f} に制限しました。"
                )
                analysis_logger.info(
                    f"[DEBUG_NEED_DETAIL] Need上限適用判定: 元データ中央値={np.median(values_at_slot_current):.1f}。制限後Need={need_calculated_val:.2f}"
                )

            # ★★★ 動的連続勤務考慮のNeed値調整 ★★★
            if continuous_shift_detector:
                sample_date = ref_start_date + dt.timedelta(days=day_of_week_idx)
                
                # 動的検出器を使用（メソッド名を適切に調整）
                if hasattr(continuous_shift_detector, 'should_adjust_need_dynamic'):
                    should_adjust, continuing_count, rule_info = continuous_shift_detector.should_adjust_need_dynamic(
                        time_slot_val, sample_date.strftime('%Y-%m-%d')
                    )
                else:
                    # フォールバック：従来のロジック
                    should_adjust, continuing_count = continuous_shift_detector.should_adjust_need(
                        time_slot_val, sample_date.strftime('%Y-%m-%d')
                    )
                    rule_info = "従来ルール"
                
                if should_adjust and continuing_count > 0:
                    # 動的調整方法の適用
                    original_need = need_calculated_val
                    
                    # 基本調整：継続勤務者数を考慮
                    base_adjustment = max(need_calculated_val, continuing_count)
                    
                    # 時間帯別の追加調整
                    if time_slot_val.startswith('00:') or time_slot_val.startswith('01:'):
                        # 深夜時間帯：継続勤務者の疲労を考慮して増員
                        fatigue_adjustment = continuing_count * 0.2
                        adjusted_need = base_adjustment + fatigue_adjustment
                    elif time_slot_val.startswith('06:') or time_slot_val.startswith('07:'):
                        # 早朝時間帯：引き継ぎ重視
                        handover_adjustment = continuing_count * 0.1
                        adjusted_need = base_adjustment + handover_adjustment
                    else:
                        adjusted_need = base_adjustment
                    
                    need_calculated_val = adjusted_need
                    
                    log.info(
                        f"[DYNAMIC_NEED] {dow_name} {time_slot_val}: "
                        f"継続勤務者{continuing_count}名考慮 (ルール: {rule_info}) "
                        f"Need {original_need:.2f} → {adjusted_need:.2f}"
                    )

            # 調整係数の適用
            need_calculated_val *= adjustment_factor
            
            # 実データが少ない場合の特殊処理
            if is_significant_holiday:
                # データが少ない場合は、実際の最大値を上限として設定
                max_actual_val = max(values_at_slot_current) if values_at_slot_current else 0
                
                # 実績が0の場合の汎用的処理（曜日に関係なく）
                if max_actual_val == 0:
                    # 実績が0の場合、Needも0に設定（過大評価を防ぐ）
                    original_need = need_calculated_val
                    need_calculated_val = 0.0
                    log.info(f"[ZERO_DATA_FIX] {dow_name} {time_slot_val}: 実績0のためNeedを {original_need:.2f} → {need_calculated_val:.2f} に修正")
                elif need_calculated_val > max_actual_val * 1.5:  # 実際の最大値の1.5倍を上限
                    original_need = need_calculated_val
                    need_calculated_val = max_actual_val * 1.5
                    log.info(f"[STATS_FIX] {dow_name} {time_slot_val}: Need値を {original_need:.2f} → {need_calculated_val:.2f} に制限（実データ考慮）")
                
                # さらに、0が多いデータでは0により近い値に調整
                zero_ratio = values_at_slot_current.count(0) / len(values_at_slot_current) if values_at_slot_current else 1
                if zero_ratio > 0.5:  # 50%以上が0の場合
                    need_calculated_val *= (1 - zero_ratio * 0.5)  # 0の比率に応じて減算
                    log.info(f"[STATS_FIX] {dow_name} {time_slot_val}: 0データ比率{zero_ratio:.2f}により調整 → {need_calculated_val:.2f}")
            
            final_need = round(need_calculated_val) if not pd.isna(need_calculated_val) else 0
            dow_need_df_calculated.loc[time_slot_val, day_of_week_idx] = final_need
            log.debug(
                f"  曜日 {day_of_week_idx}, 時間帯 {time_slot_val}: 元データ長 {len(row_series_data.dropna())} -> 外れ値除去後 {len(values_for_stat_calc)} -> Need {dow_need_df_calculated.loc[time_slot_val, day_of_week_idx]}"
            )

    # 全曜日の計算完了後、サマリーを出力
    log.info("[NEED_DEBUG] ========== Need計算完了サマリー ==========")
    for dow_idx in range(7):
        dow_name = dow_names.get(dow_idx, f"曜日{dow_idx}")
        total_need = dow_need_df_calculated[dow_idx].sum()
        max_need = dow_need_df_calculated[dow_idx].max()
        avg_need = dow_need_df_calculated[dow_idx].mean()
        log.info(f"[NEED_DEBUG] {dow_name}: 合計={total_need:.0f}, 最大={max_need:.0f}, 平均={avg_need:.2f}")

    # 特に日曜日の詳細
    if 6 in dow_need_df_calculated.columns:
        sunday_data = dow_need_df_calculated[6]
        log.info("\n[日曜日の時間帯別Need値]")
        for time_slot, need_val in sunday_data.items():
            if need_val > 0:
                log.info(f"  {time_slot}: {need_val}")

    log.info("[heatmap.calculate_pattern_based_need] 曜日別・時間帯別needの算出完了。")
    return dow_need_df_calculated.fillna(0).astype(int)


def _filter_work_records(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    新規追加: 通常勤務のレコードのみを抽出する
    休暇レコード（holiday_type != "通常勤務"）を除外し、
    実際に勤務時間がある（parsed_slots_count > 0）レコードのみを返す
    """
    if long_df.empty:
        return long_df

    # 通常勤務且つ勤務時間があるレコードのみ抽出
    work_records = long_df[
        (long_df.get("holiday_type", DEFAULT_HOLIDAY_TYPE) == DEFAULT_HOLIDAY_TYPE)
        & (long_df.get("parsed_slots_count", 0) > 0)
    ].copy()

    original_count = len(long_df)
    work_count = len(work_records)
    leave_count = original_count - work_count

    log.info(
        f"[heatmap._filter_work_records] フィルタリング結果: 全レコード={original_count}, 勤務レコード={work_count}, 休暇レコード={leave_count}"
    )

    if not work_records.empty:
        holiday_stats = long_df["holiday_type"].value_counts()
        log.debug(f"[heatmap._filter_work_records] 休暇タイプ別統計:\n{holiday_stats}")

    return work_records


def build_heatmap(
    long_df: pd.DataFrame,
    out_dir: "str | Path",
    slot_minutes: int = 30,
    *,
    need_calc_method: str | None = None,
    need_stat_method: str | None = None,
    include_zero_days: bool = True,
    need_manual_values: dict | None = None,
    upper_calc_method: str | None = None,
    upper_calc_param: dict | None = None,
    # legacy parameters kept for backward compatibility
    ref_start_date_for_need: dt.date | None = None,
    ref_end_date_for_need: dt.date | None = None,
    need_statistic_method: str | None = None,
    need_remove_outliers: bool | None = None,
    need_iqr_multiplier: float | None = 1.5,
    need_adjustment_factor: float = 1.0,
    min_method: str = "p25",
    max_method: str = "p75",
    holidays: set[dt.date] | None = None,
) -> None:
    holidays_set = set(holidays or [])

    if long_df.empty:
        log.warning("[heatmap.build_heatmap] 入力DataFrame (long_df) が空です。")
        return
    required_long_df_cols = {
        "ds",
        "staff",
        "role",
        "code",
        "holiday_type",
        "parsed_slots_count",
    }
    if not required_long_df_cols.issubset(long_df.columns):
        missing_cols = required_long_df_cols - set(long_df.columns)
        log.error(f"[heatmap.build_heatmap] long_dfに必要な列 {missing_cols} が不足。")
        out_dir_path = Path(out_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        write_meta(
            out_dir_path / "heatmap.meta.json",
            slot=slot_minutes,
            roles=[],
            dates=[],
            summary_columns=SUMMARY5,
            estimated_holidays=[d.isoformat() for d in sorted(list(holidays or set()))],
        )
        return

    # 重要: 休暇レコードの統計を先に収集
    leave_stats = {}
    if not long_df.empty and "holiday_type" in long_df.columns:
        holiday_type_stats = long_df["holiday_type"].value_counts()
        leave_stats = {
            "total_records": len(long_df),
            "leave_records": len(
                long_df[long_df["holiday_type"] != DEFAULT_HOLIDAY_TYPE]
            ),
            "holiday_type_breakdown": holiday_type_stats.to_dict(),
        }
        log.info(f"[heatmap.build_heatmap] 休暇統計: {leave_stats}")
    estimated_holidays_set: Set[dt.date] = set()
    all_dates_in_period_list: List[dt.date] = []
    if (
        not long_df.empty
        and "ds" in long_df.columns
        and "parsed_slots_count" in long_df.columns
    ):
        long_df_for_holiday_check = long_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(long_df_for_holiday_check["ds"]):
            long_df_for_holiday_check["ds"] = pd.to_datetime(
                long_df_for_holiday_check["ds"], errors="coerce"
            )
        valid_ds_long_df = long_df_for_holiday_check.dropna(subset=["ds"])
        if not valid_ds_long_df.empty:
            min_date_val = valid_ds_long_df["ds"].dt.date.min()
            max_date_val = valid_ds_long_df["ds"].dt.date.max()
            if (
                pd.NaT not in [min_date_val, max_date_val]
                and isinstance(min_date_val, dt.date)
                and isinstance(max_date_val, dt.date)
            ):
                current_scan_date = min_date_val
                while current_scan_date <= max_date_val:
                    all_dates_in_period_list.append(current_scan_date)
                    current_scan_date += dt.timedelta(days=1)
            else:
                log.warning("[heatmap.build_heatmap] 有効な日付範囲を決定できません。")
            if all_dates_in_period_list:
                for current_date_val_iter in all_dates_in_period_list:
                    df_for_current_date_iter = valid_ds_long_df[
                        valid_ds_long_df["ds"].dt.date == current_date_val_iter
                    ]
                    if df_for_current_date_iter.empty:
                        estimated_holidays_set.add(current_date_val_iter)
                        log.debug(
                            f"施設休業日(推定): {current_date_val_iter} (勤務記録なし)"
                        )
                        continue

                    # 修正: 通常勤務のレコードのみで判定
                    work_records_today = _filter_work_records(df_for_current_date_iter)
                    if work_records_today.empty:
                        estimated_holidays_set.add(current_date_val_iter)
                        log.debug(
                            f"施設休業日(推定): {current_date_val_iter} (通常勤務なし)"
                        )
            if estimated_holidays_set:
                log.info(
                    f"[heatmap.build_heatmap] 推定された休業日 ({len(estimated_holidays_set)}日): {sorted(list(estimated_holidays_set))}"
                )
            else:
                log.info("[heatmap.build_heatmap] 推定される休業日はありませんでした。")
        else:
            log.warning(
                "[heatmap.build_heatmap] 'ds'列に有効な日時データがないため、休業日を推定できません。"
            )
    else:
        log.warning(
            "[heatmap.build_heatmap] long_dfが空か、必要な列がないため、休業日を推定できません。"
        )

    # 重要: 通常勤務のレコードのみでヒートマップ作成
    # 注意：明け番シフトは元の日付で処理され、0:00-11:59の時間帯も含まれる
    df_for_heatmap_actuals = _filter_work_records(long_df)
    
    # 明け番シフトのデバッグ：早朝時間帯のデータがあるかチェック
    if not df_for_heatmap_actuals.empty and "time" in df_for_heatmap_actuals.columns:
        all_times = df_for_heatmap_actuals["time"].unique()
        early_morning_times = [t for t in all_times if isinstance(t, str) and t.startswith(("00:", "01:", "02:", "03:", "04:", "05:", "06:", "07:"))]
        if early_morning_times:
            log.info(f"[OVERNIGHT_DEBUG] 実績データに早朝時間帯を検出: {sorted(early_morning_times)}")
            # 早朝時間帯のレコード数確認
            early_morning_records = df_for_heatmap_actuals[df_for_heatmap_actuals["time"].isin(early_morning_times)]
            log.info(f"[OVERNIGHT_DEBUG] 早朝時間帯レコード数: {len(early_morning_records)}")
            if not early_morning_records.empty and "code" in early_morning_records.columns:
                early_codes = early_morning_records["code"].unique()
                log.info(f"[OVERNIGHT_DEBUG] 早朝時間帯のシフトコード: {early_codes}")
        else:
            log.info("[OVERNIGHT_DEBUG] 実績データに早朝時間帯（00:xx-07:xx）が見つかりません")
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    all_date_labels_in_period_str: List[str] = (
        sorted([d.strftime("%Y-%m-%d") for d in all_dates_in_period_list])
        if all_dates_in_period_list
        else []
    )
    
    time_index_labels = pd.Index(gen_labels(slot_minutes), name="time")

    if df_for_heatmap_actuals.empty and not all_date_labels_in_period_str:
        log.warning(
            "[heatmap.build_heatmap] 有効な勤務データも日付範囲もないため、ヒートマップは空になります。"
        )
        empty_pivot = pd.DataFrame(index=time_index_labels)
        for col_name_ep_loop in SUMMARY5:
            empty_pivot[col_name_ep_loop] = 0
        fp_all_empty_path = out_dir_path / "heat_ALL.parquet"
        try:
            empty_pivot.to_parquet(fp_all_empty_path)
        except Exception as e_empty_write:
            log.error(f"空のheat_ALL.parquetの書き込みに失敗: {e_empty_write}")
        all_unique_roles_val = (
            sorted(list(set(long_df["role"]))) if "role" in long_df.columns else []
        )
        write_meta(
            out_dir_path / "heatmap.meta.json",
            slot=slot_minutes,
            roles=all_unique_roles_val,
            dates=[],
            summary_columns=SUMMARY5,
            estimated_holidays=[d.isoformat() for d in sorted(list(holidays or set()))],
            leave_statistics=leave_stats,  # 休暇統計を追加
        )
        return

    # 明け番シフトデバッグ：ds列から時間抽出前の状況確認
    if not df_for_heatmap_actuals.empty:
        log.info(f"[OVERNIGHT_DEBUG] time/date_lbl変換前のレコード数: {len(df_for_heatmap_actuals)}")
        sample_ds = df_for_heatmap_actuals["ds"].head(5).tolist()
        log.info(f"[OVERNIGHT_DEBUG] ds列のサンプル値: {sample_ds}")
        
        # 明け番関連のコードがあるレコードの確認
        if "code" in df_for_heatmap_actuals.columns:
            overnight_codes = ['明', 'アケ', 'ake', '明け', 'AKE']
            overnight_records = df_for_heatmap_actuals[df_for_heatmap_actuals["code"].isin(overnight_codes)]
            if not overnight_records.empty:
                log.info(f"[OVERNIGHT_DEBUG] 明け番レコード数: {len(overnight_records)}")
                overnight_ds_sample = overnight_records["ds"].head(3).tolist()
                log.info(f"[OVERNIGHT_DEBUG] 明け番のds値サンプル: {overnight_ds_sample}")
    
    df_for_heatmap_actuals["time"] = pd.to_datetime(
        df_for_heatmap_actuals["ds"], errors="coerce"
    ).dt.strftime("%H:%M")
    df_for_heatmap_actuals["date_lbl"] = pd.to_datetime(
        df_for_heatmap_actuals["ds"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    
    # 明け番シフトデバッグ：time/date_lbl変換後の確認
    if not df_for_heatmap_actuals.empty:
        unique_times = df_for_heatmap_actuals["time"].unique()
        early_times = [t for t in unique_times if t.startswith(("00:", "01:", "02:", "03:", "04:", "05:", "06:", "07:"))]
        log.info(f"[OVERNIGHT_DEBUG] 変換後の早朝時間帯: {sorted(early_times)}")
        
        if "code" in df_for_heatmap_actuals.columns:
            overnight_codes = ['明', 'アケ', 'ake', '明け', 'AKE']
            overnight_records = df_for_heatmap_actuals[df_for_heatmap_actuals["code"].isin(overnight_codes)]
            if not overnight_records.empty:
                overnight_times = overnight_records["time"].unique()
                log.info(f"[OVERNIGHT_DEBUG] 明け番レコードの時間帯: {sorted(overnight_times)}")
    
    # ★★★ 動的連続勤務重複カウント防止システム ★★★
    if not long_df.empty:
        try:
            from .dynamic_continuous_shift_detector import DynamicContinuousShiftDetector
            
            # 設定ファイルパスの決定
            config_path = Path(__file__).parent.parent / "config" / "dynamic_continuous_shift_config.json"
            
            detector = DynamicContinuousShiftDetector(config_path)
            
            # wt_dfも含めて動的検出
            wt_df_for_detection = None
            if 'wt_df' in locals() or 'wt_df' in globals():
                wt_df_for_detection = wt_df if 'wt_df' in locals() else globals().get('wt_df')
            
            continuous_shifts = detector.detect_continuous_shifts(long_df, wt_df_for_detection)
            
            # 動的重複除去対象の特定
            duplicates_to_remove = set()
            slot_minutes = 15  # 動的に取得も可能
            
            for date_str in df_for_heatmap_actuals["date_lbl"].unique():
                if hasattr(detector, 'get_dynamic_duplicate_time_slots'):
                    duplicates = detector.get_dynamic_duplicate_time_slots(date_str, slot_minutes)
                else:
                    # フォールバック
                    from .continuous_shift_detector import ContinuousShiftDetector
                    fallback_detector = ContinuousShiftDetector()
                    fallback_shifts = fallback_detector.detect_continuous_shifts(long_df)
                    duplicates = fallback_detector.get_duplicate_time_slots(date_str)
                
                for staff, time_slot in duplicates:
                    duplicates_to_remove.add((staff, time_slot, date_str))
            
            # 重複レコードの除去
            if duplicates_to_remove:
                original_count = len(df_for_heatmap_actuals)
                mask = ~df_for_heatmap_actuals.apply(
                    lambda row: (row['staff'], row['time'], row['date_lbl']) in duplicates_to_remove,
                    axis=1
                )
                df_for_heatmap_actuals = df_for_heatmap_actuals[mask]
                removed_count = original_count - len(df_for_heatmap_actuals)
                
                log.info(f"[DYNAMIC_DUPLICATE_REMOVAL] 動的連続勤務重複除去: {removed_count}件のレコードを除去")
                log.debug(f"[DYNAMIC_DUPLICATE_REMOVAL] 除去対象: {duplicates_to_remove}")
                
                # 検出統計の出力
                summary = detector.get_detection_summary()
                log.info(f"[DYNAMIC_DUPLICATE_REMOVAL] 検出統計: {summary}")
                
        except Exception as e:
            log.warning(f"[DYNAMIC_DUPLICATE_REMOVAL] 動的重複除去処理エラー: {e}")
            # フォールバック処理は既存コードをそのまま実行
    df_for_heatmap_actuals.dropna(
        subset=["time", "date_lbl", "staff", "role"], inplace=True
    )

    staff_col_name = "staff"
    role_col_name = "role"
    log.info("[heatmap.build_heatmap] 全体ヒートマップ作成開始。")

    pivot_data_all_actual_staff = pd.DataFrame(index=time_index_labels)
    if not df_for_heatmap_actuals.empty:
        if len(df_for_heatmap_actuals) > 50000:
            log.info(
                "[heatmap.build_heatmap] Large dataset detected, using chunked processing"
            )
            chunk_size = 10000
            pivot_chunks = []

            for i in range(0, len(df_for_heatmap_actuals), chunk_size):
                chunk = df_for_heatmap_actuals.iloc[i : i + chunk_size]
                chunk_pivot = chunk.drop_duplicates(
                    subset=["date_lbl", "time", staff_col_name]
                ).pivot_table(
                    index="time",
                    columns="date_lbl",
                    values=staff_col_name,
                    aggfunc="nunique",
                    fill_value=0,
                )
                pivot_chunks.append(chunk_pivot)

            if pivot_chunks:
                pivot_data_all_actual_staff = pd.concat(pivot_chunks, axis=1)
                pivot_data_all_actual_staff = pivot_data_all_actual_staff.groupby(
                    level=0, axis=1
                ).sum()
                pivot_data_all_actual_staff = pivot_data_all_actual_staff.reindex(
                    index=time_index_labels, fill_value=0
                )
        else:
            pivot_data_all_actual_staff = (
                df_for_heatmap_actuals.drop_duplicates(
                    subset=["date_lbl", "time", staff_col_name]
                )
                .pivot_table(
                    index="time",
                    columns="date_lbl",
                    values=staff_col_name,
                    aggfunc="nunique",
                    fill_value=0,
                )
                .reindex(index=time_index_labels, fill_value=0)
            )

    # Ensure all dates in the period are present as columns, filling missing ones with 0
    pivot_data_all_actual_staff = pivot_data_all_actual_staff.reindex(
        columns=all_date_labels_in_period_str, fill_value=0
    )

    actual_staff_for_need_input = pivot_data_all_actual_staff.copy()
    if not actual_staff_for_need_input.empty:
        new_column_map_for_need_input = {}
        for col_str_need in actual_staff_for_need_input.columns:
            dt_obj_need = _parse_as_date(str(col_str_need))
            if dt_obj_need:
                # parsed_date_columns_for_need_input.append(dt_obj_need) # これは不要
                new_column_map_for_need_input[col_str_need] = dt_obj_need
            else:
                log.debug(
                    f"Need計算用実績データの列名'{col_str_need}'を日付にパースできませんでした。"
                )
        if new_column_map_for_need_input:
            # renameする前に、キー(元の列名)が存在するか確認
            valid_keys_for_rename = [
                k
                for k in new_column_map_for_need_input.keys()
                if k in actual_staff_for_need_input.columns
            ]
            actual_staff_for_need_input = actual_staff_for_need_input[
                valid_keys_for_rename
            ].rename(columns=new_column_map_for_need_input)
        else:
            actual_staff_for_need_input = pd.DataFrame(index=time_index_labels)

    # app.pyから渡される新しい引数(need_stat_method)を優先し、
    # legacy引数(need_statistic_method)があればバックアップとして使用する
    final_statistic_method = (
        need_stat_method if need_stat_method is not None else need_statistic_method
    )

    if include_zero_days:
        log.info("[NEED_FIX] include_zero_days=True → 推定休業日を無視")
        final_holidays_to_use = holidays_set
    else:
        final_holidays_to_use = holidays_set.union(estimated_holidays_set)

    overall_dow_need_pattern_df = calculate_pattern_based_need(
        actual_staff_for_need_input,
        ref_start_date_for_need,
        ref_end_date_for_need,
        final_statistic_method,
        need_remove_outliers,
        need_iqr_multiplier,
        slot_minutes_for_empty=slot_minutes,
        holidays=final_holidays_to_use,
        adjustment_factor=need_adjustment_factor,
        include_zero_days=include_zero_days,
        all_dates_in_period=all_dates_in_period_list,
        long_df=long_df,  # 連続勤務検出用にlong_dfを渡す
    )

    pivot_data_all_final = pd.DataFrame(
        index=time_index_labels, columns=all_date_labels_in_period_str, dtype=float
    ).fillna(0)
    need_all_final_for_summary = pd.DataFrame(
        index=time_index_labels, columns=all_date_labels_in_period_str, dtype=float
    ).fillna(0)

    for date_str_col_map in all_date_labels_in_period_str:
        if date_str_col_map in pivot_data_all_actual_staff.columns:
            pivot_data_all_final[date_str_col_map] = pivot_data_all_actual_staff[
                date_str_col_map
            ]
        current_date_obj_map = dt.datetime.strptime(date_str_col_map, "%Y-%m-%d").date()
        if current_date_obj_map.weekday() == 6:
            log.info(f"[SUNDAY_APPLY] 日曜日 {date_str_col_map} のNeed適用:")
            log.info(f"[SUNDAY_APPLY]   休業日判定: {current_date_obj_map in holidays_set}")
        if current_date_obj_map in holidays_set:
            if current_date_obj_map.weekday() == 6:
                log.info("[SUNDAY_APPLY]   → 休業日のためNeed=0に設定")
            need_all_final_for_summary[date_str_col_map] = 0
        else:
            day_of_week_map = current_date_obj_map.weekday()
            if day_of_week_map in overall_dow_need_pattern_df.columns:
                need_all_final_for_summary[date_str_col_map] = overall_dow_need_pattern_df[day_of_week_map]
                if current_date_obj_map.weekday() == 6:
                    need_values = overall_dow_need_pattern_df[day_of_week_map]
                    log.info(f"[SUNDAY_APPLY]   → Need値適用: 合計={need_values.sum():.0f}")
                    log.info(f"[SUNDAY_APPLY]   → Need値詳細（最初5つ）: {need_values.head().tolist()}")

            else:
                need_all_final_for_summary[date_str_col_map] = 0
                log.warning(
                    f"曜日 {day_of_week_map} のneedパターンが見つかりません ({date_str_col_map})。Needは0とします。"
                )

    # 詳細なNeedデータをParquetファイルとして保存（datetime問題対応）
    # カラム名を明示的に文字列として保存
    need_df_for_save = need_all_final_for_summary.copy()
    need_df_for_save.columns = [str(col) for col in need_df_for_save.columns]
    
    # PyArrowテーブルとして保存（カラム型を明示的に指定）
    table = pa.Table.from_pandas(need_df_for_save, preserve_index=True)
    
    # メタデータにカラム型情報を追加
    metadata = table.schema.metadata or {}
    metadata[b'column_format'] = b'string_dates'
    new_schema = table.schema.with_metadata(metadata)
    table = table.cast(new_schema)
    
    pq.write_table(table, out_dir_path / "need_per_date_slot.parquet")
    log.info("Need per date/slot data saved to need_per_date_slot.parquet.")

    upper_s_representative = (
        derive_max_staff(pivot_data_all_actual_staff, max_method)
        if not pivot_data_all_actual_staff.empty
        else pd.Series(0, index=time_index_labels)
    )

    total_lack_per_time = pd.Series(0, index=time_index_labels, dtype=float)
    total_excess_per_time = pd.Series(0, index=time_index_labels, dtype=float)
    working_day_count = 0

    for date_col in need_all_final_for_summary.columns:
        if date_col in pivot_data_all_final.columns:
            daily_staff = pivot_data_all_final[date_col]
            daily_need = need_all_final_for_summary[date_col]

            date_obj = dt.datetime.strptime(date_col, "%Y-%m-%d").date()
            if date_obj not in holidays_set:
                working_day_count += 1
                daily_lack = (daily_need - daily_staff).clip(lower=0)
                daily_excess = (daily_staff - upper_s_representative).clip(lower=0)

                total_lack_per_time += daily_lack
                total_excess_per_time += daily_excess

    avg_need_series = need_all_final_for_summary.mean(axis=1).round()
    avg_staff_series = (
        pivot_data_all_final.drop(columns=SUMMARY5, errors="ignore")
        .mean(axis=1)
        .round()
        if not pivot_data_all_final.empty
        else pd.Series(0, index=time_index_labels)
    )
    avg_lack_series = (total_lack_per_time / max(working_day_count, 1)).round()
    avg_excess_series = (total_excess_per_time / max(working_day_count, 1)).round()

    pivot_to_excel_all = pivot_data_all_final.copy()
    for col_name_summary_loop, series_data_summary_loop in zip(
        SUMMARY5,
        [
            avg_need_series,
            upper_s_representative,
            avg_staff_series,
            avg_lack_series,
            avg_excess_series,
        ],
        strict=True,
    ):
        pivot_to_excel_all[col_name_summary_loop] = series_data_summary_loop

    analysis_logger.info(
        f"[DEBUG_HEATMAP_FINAL_COLS] heat_ALL.parquetに保存される最終列: {pivot_to_excel_all.columns.tolist()}"
    )

    fp_all_path = out_dir_path / "heat_ALL.parquet"
    try:
        pivot_to_excel_all.to_parquet(fp_all_path)
        log.info(
            "[heatmap.build_heatmap] 全体ヒートマップ (heat_ALL.parquet) 作成完了。"
        )
    except Exception as e_write_all:
        log.error(
            f"[heatmap.build_heatmap] heat_ALL.parquet 作成エラー: {e_write_all}",
            exc_info=True,
        )

    fp_all_xlsx_path = out_dir_path / "heat_ALL.xlsx"
    try:
        save_df_xlsx(pivot_to_excel_all, fp_all_xlsx_path, sheet_name="heat_ALL")
    except Exception as e_xlsx_all:
        log.error(
            f"[heatmap.build_heatmap] heat_ALL.xlsx 作成エラー: {e_xlsx_all}",
            exc_info=True,
        )

    try:
        log.info(f"{fp_all_xlsx_path.name} に書式を設定します。")
        wb = openpyxl.load_workbook(fp_all_xlsx_path)
        ws = wb.active

        data_columns = pivot_to_excel_all.columns.drop(SUMMARY5, errors="ignore")

        _apply_conditional_formatting_to_worksheet(ws, data_columns)
        _apply_holiday_column_styling(ws, data_columns, holidays_set, _parse_as_date)

        wb.save(fp_all_xlsx_path)
        log.info(f"書式設定を {fp_all_xlsx_path.name} に保存しました。")
    except Exception as e:
        log.error(f"{fp_all_xlsx_path.name} への書式設定中にエラー: {e}", exc_info=True)

    unique_roles_list_final_loop = sorted(
        list(set(df_for_heatmap_actuals[role_col_name]))
    )
    log.info(
        f"[heatmap.build_heatmap] 職種別ヒートマップ作成開始。対象: {unique_roles_list_final_loop}"
    )
    for role_item_final_loop in unique_roles_list_final_loop:
        role_safe_name_final_loop = safe_sheet(str(role_item_final_loop))
        log.debug(f"職種 '{role_item_final_loop}' 開始...")
        df_role_subset = df_for_heatmap_actuals[
            df_for_heatmap_actuals[role_col_name] == role_item_final_loop
        ]
        pivot_data_role_actual = pd.DataFrame(index=time_index_labels)
        if not df_role_subset.empty:
            pivot_data_role_actual = (
                df_role_subset.drop_duplicates(
                    subset=["date_lbl", "time", staff_col_name]
                )
                .pivot_table(
                    index="time",
                    columns="date_lbl",
                    values=staff_col_name,
                    aggfunc="nunique",
                    fill_value=0,
                )
                .reindex(index=time_index_labels, fill_value=0)
            )
        pivot_data_role_final = pivot_data_role_actual.reindex(
            columns=all_date_labels_in_period_str, fill_value=0
        )
        if not pivot_data_role_final.columns.empty:
            try:
                cols_to_sort_r = pd.Series(pivot_data_role_final.columns).astype(str)
                valid_date_cols_r = cols_to_sort_r[
                    cols_to_sort_r.str.match(r"^\d{4}-\d{2}-\d{2}$")
                ]
                if not valid_date_cols_r.empty:
                    sorted_cols_r = sorted(
                        valid_date_cols_r,
                        key=lambda d: dt.datetime.strptime(d, "%Y-%m-%d").date(),
                    )
                    other_cols_r = [
                        c
                        for c in pivot_data_role_final.columns
                        if c not in valid_date_cols_r.tolist()
                    ]
                    pivot_data_role_final = pivot_data_role_final[
                        sorted_cols_r + other_cols_r
                    ]
            except Exception as e_sort_r:
                log.warning(f"職種 '{role_item_final_loop}' 日付ソート失敗: {e_sort_r}")

        actual_staff_for_role_need_input = pivot_data_role_actual.copy()
        if not actual_staff_for_role_need_input.empty:
            new_column_map_for_role_need = {}
            for col_str_role in actual_staff_for_role_need_input.columns:
                dt_obj_role = _parse_as_date(str(col_str_role))
                if dt_obj_role:
                    new_column_map_for_role_need[col_str_role] = dt_obj_role

            if new_column_map_for_role_need:
                valid_keys_for_role_rename = [
                    k
                    for k in new_column_map_for_role_need.keys()
                    if k in actual_staff_for_role_need_input.columns
                ]
                actual_staff_for_role_need_input = actual_staff_for_role_need_input[
                    valid_keys_for_role_rename
                ].rename(columns=new_column_map_for_role_need)
            else:
                actual_staff_for_role_need_input = pd.DataFrame(index=time_index_labels)

        # 重要な修正：職種別でも全期間の日付を補完
        if include_zero_days and all_dates_in_period_list:
            for date in all_dates_in_period_list:
                if ref_start_date_for_need <= date <= ref_end_date_for_need and date not in final_holidays_to_use:
                    if date not in actual_staff_for_role_need_input.columns:
                        actual_staff_for_role_need_input[date] = 0

        # ★★★ 重要な修正：職種別need値を全体needから按分計算 ★★★
        # 全体のneed_per_date_slot.parquetを読み込み
        need_per_date_slot_file = out_dir_path / "need_per_date_slot.parquet"
        
        if need_per_date_slot_file.exists():
            log.info(f"[ROLE_NEED] Using global need_per_date_slot.parquet for role {role_item_final_loop} proportional calculation")
            
            try:
                # 全体のneed値を読み込み（詳細な日付×時間帯データ）
                global_need_df = pd.read_parquet(need_per_date_slot_file)
                
                # 職種別のstaff比率を計算
                role_staff_total = pivot_data_role_actual.sum().sum()
                
                # 全職種のstaff合計を計算（比率算出のため）
                # pivot_data_all_finalから全体のstaff合計を計算
                try:
                    if not pivot_data_all_final.empty:
                        date_cols_all = [c for c in pivot_data_all_final.columns 
                                       if c not in SUMMARY5 and pd.to_datetime(c, errors='coerce') is not pd.NaT]
                        if date_cols_all:
                            all_staff_total = pivot_data_all_final[date_cols_all].sum().sum()
                        else:
                            raise ValueError("No date columns found in pivot_data_all_final")
                    else:
                        raise ValueError("pivot_data_all_final is empty")
                except Exception as e:
                    log.warning(f"[ROLE_NEED] Could not calculate accurate staff ratio for {role_item_final_loop}: {e}")
                    # フォールバック：独立計算
                    dow_need_pattern_role_df = calculate_pattern_based_need(
                        actual_staff_for_role_need_input,
                        ref_start_date_for_need,
                        ref_end_date_for_need,
                        final_statistic_method,
                        need_remove_outliers,
                        need_iqr_multiplier,
                        slot_minutes_for_empty=slot_minutes,
                        holidays=final_holidays_to_use,
                        adjustment_factor=need_adjustment_factor,
                        include_zero_days=include_zero_days,
                        all_dates_in_period=all_dates_in_period_list,
                    )
                    need_r_series = dow_need_pattern_role_df.mean(axis=1).round()
                else:
                    # 職種比率を計算
                    role_ratio = role_staff_total / all_staff_total if all_staff_total > 0 else 0
                    
                    # ★★★ 修正：詳細Need値の全日程に比率を適用 ★★★
                    # 各日付×時間帯の詳細Need値に職種比率を適用
                    role_need_df = global_need_df * role_ratio
                    
                    # 時間帯別の平均Need値を算出（ヒートマップ用）
                    need_r_series = role_need_df.mean(axis=1).round()
                    
                    # ★★★ 重要：詳細Need値も保存（後で出力） ★★★
                    role_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_role_{role_safe_name_final_loop}.parquet"
                    role_need_df.to_parquet(role_need_per_date_slot_file)
                    
                    log.info(f"[ROLE_NEED] Role {role_item_final_loop}: staff_ratio={role_ratio:.4f}, "
                           f"role_staff={role_staff_total}, all_staff={all_staff_total}, "
                           f"detailed_need_sum={role_need_df.sum().sum():.2f}, avg_need_sum={need_r_series.sum():.2f}")
            
            except Exception as e:
                log.warning(f"[ROLE_NEED] Failed to use proportional calculation for {role_item_final_loop}: {e}, falling back to independent calculation")
                # フォールバック：従来の独立計算
                dow_need_pattern_role_df = calculate_pattern_based_need(
                    actual_staff_for_role_need_input,
                    ref_start_date_for_need,
                    ref_end_date_for_need,
                    final_statistic_method,
                    need_remove_outliers,
                    need_iqr_multiplier,
                    slot_minutes_for_empty=slot_minutes,
                    holidays=final_holidays_to_use,
                    adjustment_factor=need_adjustment_factor,
                    include_zero_days=include_zero_days,
                    all_dates_in_period=all_dates_in_period_list,
                )
                need_r_series = dow_need_pattern_role_df.mean(axis=1).round()
        else:
            log.warning(f"[ROLE_NEED] need_per_date_slot.parquet not found, using independent calculation for {role_item_final_loop}")
            # フォールバック：従来の独立計算
            dow_need_pattern_role_df = calculate_pattern_based_need(
                actual_staff_for_role_need_input,
                ref_start_date_for_need,
                ref_end_date_for_need,
                final_statistic_method,
                need_remove_outliers,
                need_iqr_multiplier,
                slot_minutes_for_empty=slot_minutes,
                holidays=final_holidays_to_use,
                adjustment_factor=need_adjustment_factor,
                include_zero_days=include_zero_days,
                all_dates_in_period=all_dates_in_period_list,
            )
            need_r_series = dow_need_pattern_role_df.mean(axis=1).round()

        if upper_calc_method == _("下限値(Need) + 固定値"):
            fixed_val = (upper_calc_param or {}).get("fixed_value", 0)
            upper_r_series = need_r_series + fixed_val
        elif upper_calc_method == _("下限値(Need) * 固定係数"):
            factor = (upper_calc_param or {}).get("factor", 1.0)
            upper_r_series = (need_r_series * factor).apply(np.ceil)
        elif upper_calc_method == _("過去実績のパーセンタイル"):
            pct = (upper_calc_param or {}).get("percentile", 90) / 100
            upper_r_series = pivot_data_role_actual.quantile(pct, axis=1).round()
        else:
            upper_r_series = (
                derive_max_staff(pivot_data_role_actual, max_method)
                if not pivot_data_role_actual.empty
                else pd.Series(0, index=time_index_labels)
            )

        upper_r_series = np.maximum(upper_r_series, need_r_series)
        staff_r_series = (
            pivot_data_role_final.drop(columns=SUMMARY5, errors="ignore")
            .sum(axis=1)
            .round()
        )
        lack_r_series = (need_r_series - staff_r_series).clip(lower=0)
        excess_r_series = (staff_r_series - upper_r_series).clip(lower=0)

        pivot_to_excel_role = pivot_data_role_final.copy()
        for col, data in zip(
            SUMMARY5,
            [
                need_r_series,
                upper_r_series,
                staff_r_series,
                lack_r_series,
                excess_r_series,
            ],
            strict=True,
        ):
            pivot_to_excel_role[col] = data

        fp_role = out_dir_path / f"heat_{role_safe_name_final_loop}.parquet"
        try:
            pivot_to_excel_role.to_parquet(fp_role)
            log.info(f"職種 '{role_item_final_loop}' ヒートマップ作成完了。")
        except Exception as e_role_write:
            log.error(
                f"heat_{role_safe_name_final_loop}.parquet 作成エラー: {e_role_write}",
                exc_info=True,
            )

        fp_role_xlsx = out_dir_path / f"heat_{role_safe_name_final_loop}.xlsx"
        try:
            save_df_xlsx(
                pivot_to_excel_role,
                fp_role_xlsx,
                sheet_name=f"heat_{role_safe_name_final_loop}",
            )
        except Exception as e_role_xlsx:
            log.error(
                f"heat_{role_safe_name_final_loop}.xlsx 作成エラー: {e_role_xlsx}",
                exc_info=True,
            )

        try:
            log.info(f"{fp_role_xlsx.name} に書式を設定します。")
            wb = openpyxl.load_workbook(fp_role_xlsx)
            ws = wb.active
            data_columns = pivot_to_excel_role.columns.drop(SUMMARY5, errors="ignore")
            _apply_conditional_formatting_to_worksheet(ws, data_columns)
            _apply_holiday_column_styling(
                ws, data_columns, holidays_set, _parse_as_date
            )
            wb.save(fp_role_xlsx)
        except Exception as e:
            log.error(f"{fp_role_xlsx.name} への書式設定中にエラー: {e}", exc_info=True)

    # ── Employment heatmaps ───────────────────────────────────────────────
    employment_col_name = "employment"
    unique_employments_list_final_loop = (
        sorted(list(set(df_for_heatmap_actuals[employment_col_name])))
        if employment_col_name in df_for_heatmap_actuals.columns
        else []
    )
    log.info(
        f"[heatmap.build_heatmap] 雇用形態別ヒートマップ作成開始。対象: {unique_employments_list_final_loop}"
    )
    for emp_item_final_loop in unique_employments_list_final_loop:
        emp_safe_name_final_loop = safe_sheet(str(emp_item_final_loop))
        log.debug(f"雇用形態 '{emp_item_final_loop}' 開始...")
        df_emp_subset = df_for_heatmap_actuals[
            df_for_heatmap_actuals[employment_col_name] == emp_item_final_loop
        ]
        pivot_data_emp_actual = pd.DataFrame(index=time_index_labels)
        if not df_emp_subset.empty:
            pivot_data_emp_actual = (
                df_emp_subset.drop_duplicates(
                    subset=["date_lbl", "time", staff_col_name]
                )
                .pivot_table(
                    index="time",
                    columns="date_lbl",
                    values=staff_col_name,
                    aggfunc="nunique",
                    fill_value=0,
                )
                .reindex(index=time_index_labels, fill_value=0)
            )
        pivot_data_emp_final = pivot_data_emp_actual.reindex(
            columns=all_date_labels_in_period_str, fill_value=0
        )
        if not pivot_data_emp_final.columns.empty:
            try:
                cols_to_sort_e = pd.Series(pivot_data_emp_final.columns).astype(str)
                valid_date_cols_e = cols_to_sort_e[
                    cols_to_sort_e.str.match(r"^\d{4}-\d{2}-\d{2}$")
                ]
                if not valid_date_cols_e.empty:
                    sorted_cols_e = sorted(
                        valid_date_cols_e,
                        key=lambda d: dt.datetime.strptime(d, "%Y-%m-%d").date(),
                    )
                    other_cols_e = [
                        c
                        for c in pivot_data_emp_final.columns
                        if c not in valid_date_cols_e.tolist()
                    ]
                    pivot_data_emp_final = pivot_data_emp_final[
                        sorted_cols_e + other_cols_e
                    ]
            except Exception as e_sort_e:
                log.warning(
                    f"雇用形態 '{emp_item_final_loop}' 日付ソート失敗: {e_sort_e}"
                )

        actual_staff_for_emp_need_input = pivot_data_emp_actual.copy()
        if not actual_staff_for_emp_need_input.empty:
            new_column_map_for_emp_need = {}
            for col_str_emp in actual_staff_for_emp_need_input.columns:
                dt_obj_emp = _parse_as_date(str(col_str_emp))
                if dt_obj_emp:
                    new_column_map_for_emp_need[col_str_emp] = dt_obj_emp

            if new_column_map_for_emp_need:
                valid_keys_for_emp_rename = [
                    k
                    for k in new_column_map_for_emp_need.keys()
                    if k in actual_staff_for_emp_need_input.columns
                ]
                actual_staff_for_emp_need_input = actual_staff_for_emp_need_input[
                    valid_keys_for_emp_rename
                ].rename(columns=new_column_map_for_emp_need)
            else:
                actual_staff_for_emp_need_input = pd.DataFrame(index=time_index_labels)

        # ★★★ 修正：雇用形態別Need計算も按分ベースに統一 ★★★
        if need_per_date_slot_file.exists():
            log.info(f"[EMP_NEED] Using global need_per_date_slot.parquet for employment {emp_item_final_loop} proportional calculation")
            
            try:
                # 全体のneed値を読み込み（詳細な日付×時間帯データ）
                global_need_df = pd.read_parquet(need_per_date_slot_file)
                
                # 雇用形態別のstaff比率を計算
                emp_staff_total = pivot_data_emp_actual.sum().sum()
                
                # 全雇用形態のstaff合計を計算（比率算出のため）
                try:
                    if not pivot_data_all_final.empty:
                        date_cols_all = [c for c in pivot_data_all_final.columns 
                                       if c not in SUMMARY5 and pd.to_datetime(c, errors='coerce') is not pd.NaT]
                        if date_cols_all:
                            all_staff_total = pivot_data_all_final[date_cols_all].sum().sum()
                        else:
                            raise ValueError("No date columns found in pivot_data_all_final")
                    else:
                        raise ValueError("pivot_data_all_final is empty")
                        
                    # 雇用形態比率を計算
                    emp_ratio = emp_staff_total / all_staff_total if all_staff_total > 0 else 0
                    
                    # ★★★ 修正：詳細Need値の全日程に比率を適用 ★★★
                    # 各日付×時間帯の詳細Need値に雇用形態比率を適用
                    emp_need_df = global_need_df * emp_ratio
                    
                    # 時間帯別の平均Need値を算出（ヒートマップ用）
                    need_e_series = emp_need_df.mean(axis=1).round()
                    
                    # ★★★ 重要：詳細Need値も保存（後で出力） ★★★
                    emp_need_per_date_slot_file = out_dir_path / f"need_per_date_slot_emp_{emp_safe_name_final_loop}.parquet"
                    emp_need_df.to_parquet(emp_need_per_date_slot_file)
                    
                    log.info(f"[EMP_NEED] Employment {emp_item_final_loop}: staff_ratio={emp_ratio:.4f}, "
                           f"emp_staff={emp_staff_total}, all_staff={all_staff_total}, "
                           f"detailed_need_sum={emp_need_df.sum().sum():.2f}, avg_need_sum={need_e_series.sum():.2f}")
                    
                    # 按分計算成功フラグ
                    emp_proportional_success = True
                    
                except Exception as e:
                    log.warning(f"[EMP_NEED] Could not calculate accurate staff ratio for {emp_item_final_loop}: {e}")
                    emp_proportional_success = False
                    
            except Exception as e:
                log.warning(f"[EMP_NEED] Failed to use proportional calculation for {emp_item_final_loop}: {e}, falling back to independent calculation")
                emp_proportional_success = False
        else:
            log.warning(f"[EMP_NEED] need_per_date_slot.parquet not found, using independent calculation for {emp_item_final_loop}")
            emp_proportional_success = False
            
        # フォールバック：従来の独立計算
        if not emp_proportional_success:
            # 重要な修正：雇用形態別でも全期間の日付を補完
            if include_zero_days and all_dates_in_period_list:
                for date in all_dates_in_period_list:
                    if ref_start_date_for_need <= date <= ref_end_date_for_need and date not in final_holidays_to_use:
                        if date not in actual_staff_for_emp_need_input.columns:
                            actual_staff_for_emp_need_input[date] = 0

            dow_need_pattern_emp_df = calculate_pattern_based_need(
                actual_staff_for_emp_need_input,
                ref_start_date_for_need,
                ref_end_date_for_need,
                final_statistic_method,
                need_remove_outliers,
                need_iqr_multiplier,
                slot_minutes_for_empty=slot_minutes,
                holidays=final_holidays_to_use,
                adjustment_factor=need_adjustment_factor,
                include_zero_days=include_zero_days,
                all_dates_in_period=all_dates_in_period_list,
            )
            
            need_e_series = dow_need_pattern_emp_df.mean(axis=1).round()

        # ★★★ 修正：按分計算成功時は詳細Need値を使用 ★★★
        if emp_proportional_success:
            # 按分で計算済みのneed_e_seriesを使用
            need_df_emp_final = pd.DataFrame(index=time_index_labels, columns=pivot_data_emp_final.columns, dtype=float).fillna(0)
            
            # 各日付に need_e_series の値を設定（休日は0）
            for date_str_col_map in pivot_data_emp_final.columns:
                current_date_obj_map = dt.datetime.strptime(date_str_col_map, "%Y-%m-%d").date()
                if current_date_obj_map in holidays_set:
                    need_df_emp_final[date_str_col_map] = 0
                else:
                    need_df_emp_final[date_str_col_map] = need_e_series
        else:
            # 従来方式：曜日パターンベース
            need_df_emp_final = pd.DataFrame(index=time_index_labels, columns=pivot_data_emp_final.columns, dtype=float).fillna(0)
            for date_str_col_map in pivot_data_emp_final.columns:
                current_date_obj_map = dt.datetime.strptime(date_str_col_map, "%Y-%m-%d").date()
                if current_date_obj_map in holidays_set:
                    need_df_emp_final[date_str_col_map] = 0
                else:
                    day_of_week_map = current_date_obj_map.weekday()
                    if day_of_week_map in dow_need_pattern_emp_df.columns:
                        need_df_emp_final[date_str_col_map] = dow_need_pattern_emp_df[day_of_week_map]
                    else:
                        need_df_emp_final[date_str_col_map] = 0
            
            need_e_series = need_df_emp_final.mean(axis=1).round()
        upper_e_series = (
            derive_max_staff(pivot_data_emp_actual, max_method)
            if not pivot_data_emp_actual.empty
            else pd.Series(0, index=time_index_labels)
        )
        staff_e_series = (
            pivot_data_emp_final.drop(columns=SUMMARY5, errors="ignore")
            .sum(axis=1)
            .round()
        )
        lack_e_series = (need_e_series - staff_e_series).clip(lower=0)
        excess_e_series = (staff_e_series - upper_e_series).clip(lower=0)

        pivot_to_excel_emp = pivot_data_emp_final.copy()
        for col, data in zip(
            SUMMARY5,
            [
                need_e_series,
                upper_e_series,
                staff_e_series,
                lack_e_series,
                excess_e_series,
            ],
            strict=True,
        ):
            pivot_to_excel_emp[col] = data

        fp_emp = out_dir_path / f"heat_emp_{emp_safe_name_final_loop}.parquet"
        try:
            pivot_to_excel_emp.to_parquet(fp_emp)
            log.info(f"雇用形態 '{emp_item_final_loop}' ヒートマップ作成完了。")
        except Exception as e_emp_write:
            log.error(
                f"heat_emp_{emp_safe_name_final_loop}.parquet 作成エラー: {e_emp_write}",
                exc_info=True,
            )

        fp_emp_xlsx = out_dir_path / f"heat_emp_{emp_safe_name_final_loop}.xlsx"
        try:
            save_df_xlsx(
                pivot_to_excel_emp,
                fp_emp_xlsx,
                sheet_name=f"heat_emp_{emp_safe_name_final_loop}",
            )
        except Exception as e_emp_xlsx:
            log.error(
                f"heat_emp_{emp_safe_name_final_loop}.xlsx 作成エラー: {e_emp_xlsx}",
                exc_info=True,
            )

        try:
            log.info(f"{fp_emp_xlsx.name} に書式を設定します。")
            wb = openpyxl.load_workbook(fp_emp_xlsx)
            ws = wb.active
            data_columns = pivot_to_excel_emp.columns.drop(SUMMARY5, errors="ignore")
            _apply_conditional_formatting_to_worksheet(ws, data_columns)
            _apply_holiday_column_styling(
                ws, data_columns, holidays_set, _parse_as_date
            )
            wb.save(fp_emp_xlsx)
        except Exception as e:
            log.error(f"{fp_emp_xlsx.name} への書式設定中にエラー: {e}", exc_info=True)

    all_unique_roles_from_orig_long_df_meta = (
        sorted(list(set(long_df["role"]))) if "role" in long_df.columns else []
    )
    all_unique_employments_from_orig_long_df_meta = (
        sorted(list(set(long_df["employment"])))
        if "employment" in long_df.columns
        else []
    )
    dow_need_pattern_output = (
        overall_dow_need_pattern_df.reset_index()
        .rename(columns={"time": "time"})
        .to_dict(orient="records")
        if not overall_dow_need_pattern_df.empty
        else []
    )  #  index名変更

    write_meta(
        out_dir_path / "heatmap.meta.json",
        slot=slot_minutes,
        roles=all_unique_roles_from_orig_long_df_meta,
        dates=all_date_labels_in_period_str,
        summary_columns=SUMMARY5,
        estimated_holidays=[d.isoformat() for d in sorted(list(holidays or set()))],
        employments=all_unique_employments_from_orig_long_df_meta,
        dow_need_pattern=dow_need_pattern_output,
        need_calculation_params={
            "ref_start_date": ref_start_date_for_need.isoformat(),
            "ref_end_date": ref_end_date_for_need.isoformat(),
            "statistic_method": final_statistic_method,
            "remove_outliers": need_remove_outliers,
            "iqr_multiplier": need_iqr_multiplier if need_remove_outliers else None,
        },
        leave_statistics=leave_stats,  # 休暇統計をメタデータに追加
    )
    validate_need_calculation(need_all_final_for_summary, pivot_data_all_final)
    
    # ★★★ Need合計値の整合性検証 ★★★
    log.info("[NEED_VALIDATION] Need値の整合性を検証します...")
    
    try:
        # 全体Need総計
        if need_per_date_slot_file.exists():
            global_need_df = pd.read_parquet(need_per_date_slot_file)
            global_need_total = global_need_df.sum().sum()
            log.info(f"[NEED_VALIDATION] 全体Need総計: {global_need_total:.2f}")
            
            # 職種別Need総計
            role_need_total = 0
            role_need_files = list(out_dir_path.glob("need_per_date_slot_role_*.parquet"))
            
            for role_need_file in role_need_files:
                if role_need_file.exists():
                    role_need_df = pd.read_parquet(role_need_file)
                    role_sum = role_need_df.sum().sum()
                    role_need_total += role_sum
                    role_name = role_need_file.stem.replace("need_per_date_slot_role_", "")
                    log.info(f"[NEED_VALIDATION] 職種別Need '{role_name}': {role_sum:.2f}")
            
            # 雇用形態別Need総計
            emp_need_total = 0
            emp_need_files = list(out_dir_path.glob("need_per_date_slot_emp_*.parquet"))
            
            for emp_need_file in emp_need_files:
                if emp_need_file.exists():
                    emp_need_df = pd.read_parquet(emp_need_file)
                    emp_sum = emp_need_df.sum().sum()
                    emp_need_total += emp_sum
                    emp_name = emp_need_file.stem.replace("need_per_date_slot_emp_", "")
                    log.info(f"[NEED_VALIDATION] 雇用形態別Need '{emp_name}': {emp_sum:.2f}")
            
            # 整合性チェック
            role_diff = abs(global_need_total - role_need_total)
            emp_diff = abs(global_need_total - emp_need_total)
            
            log.info(f"[NEED_VALIDATION] 職種別Need総計: {role_need_total:.2f} (差: {role_diff:.2f})")
            log.info(f"[NEED_VALIDATION] 雇用形態別Need総計: {emp_need_total:.2f} (差: {emp_diff:.2f})")
            
            # 許容誤差（1%以内）でのチェック
            tolerance = global_need_total * 0.01 if global_need_total > 0 else 1.0
            if role_diff <= tolerance and emp_diff <= tolerance:
                log.info("[NEED_VALIDATION] ✅ Need値の整合性: OK（誤差は許容範囲内）")
            else:
                log.warning(f"[NEED_VALIDATION] ⚠️ Need値の整合性: 要注意（許容誤差: {tolerance:.2f}）")
                
    except Exception as e:
        log.warning(f"[NEED_VALIDATION] Need値整合性検証でエラー: {e}")
    
    log.info("[heatmap.build_heatmap] ヒートマップ生成処理完了。")
