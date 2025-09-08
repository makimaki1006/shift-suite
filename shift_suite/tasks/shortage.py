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
from .constants import SUMMARY5  # 🔧 修正: 動的値使用
from .utils import _parse_as_date, gen_labels, log, save_df_parquet, write_meta

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
    log_filename = f"{timestamp}_不足時間計算詳細分析.txt"
    log_filepath = output_dir / log_filename
    
    try:
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write("=== 27,486.5時間問題 - 詳細計算過程分析 ===\n")
            f.write(f"生成日時: {timestamp}\n")
            f.write(f"分析ディレクトリ: {output_dir}\n")
            f.write("=" * 70 + "\n\n")
            
            # 🔍 STEP 1: shortage_time.parquetの詳細分析
            f.write("【STEP 1: shortage_time.parquet 基礎データ分析】\n")
            shortage_time_path = output_dir / "shortage_time.parquet"
            if shortage_time_path.exists():
                try:
                    shortage_df = pd.read_parquet(shortage_time_path)
                    f.write(f"  ファイルサイズ: {shortage_time_path.stat().st_size / 1024:.1f} KB\n")
                    f.write(f"  データ形状: {shortage_df.shape} (時間帯 × 日付)\n")
                    f.write(f"  期間: {len(shortage_df.columns)}日分\n")
                    f.write(f"  時間帯数: {len(shortage_df.index)}\n")
                    
                    # 統計値
                    total_shortage_slots = shortage_df.sum().sum()
                    f.write(f"  総不足スロット数: {total_shortage_slots:.1f}\n")
                    
                    # スロット時間の取得
                    slot_hours = analysis_results.get('calculation_details', {}).get('slot_hours', 0.5)
                    total_shortage_hours = total_shortage_slots * slot_hours
                    f.write(f"  スロット時間: {slot_hours:.2f}時間 ({slot_hours * 60:.0f}分)\n")
                    f.write(f"  総不足時間: {total_shortage_hours:.1f}時間\n")
                    
                    # 日別統計
                    daily_shortage = shortage_df.sum()
                    f.write(f"  日平均不足: {daily_shortage.mean():.2f}スロット/日 ({daily_shortage.mean() * slot_hours:.2f}時間/日)\n")
                    f.write(f"  最大日不足: {daily_shortage.max():.2f}スロット ({daily_shortage.max() * slot_hours:.2f}時間)\n")
                    f.write(f"  最小日不足: {daily_shortage.min():.2f}スロット ({daily_shortage.min() * slot_hours:.2f}時間)\n")
                    
                    # 時間帯別統計
                    hourly_shortage = shortage_df.sum(axis=1)
                    top_shortage_times = hourly_shortage.nlargest(5)
                    f.write("\n  【最も不足の多い時間帯 TOP5】\n")
                    for time_slot, shortage_count in top_shortage_times.items():
                        f.write(f"    {time_slot}: {shortage_count:.1f}スロット ({shortage_count * slot_hours:.1f}時間)\n")
                    
                    # 🎯 期間依存性チェック
                    period_days = len(shortage_df.columns)
                    if period_days > 60:  # 2ヶ月以上
                        months_estimated = period_days / 30
                        monthly_avg = total_shortage_hours / months_estimated
                        f.write("\n  ⚠️ 【期間依存性分析】\n")
                        f.write(f"    推定期間: {months_estimated:.1f}ヶ月\n")
                        f.write(f"    月平均不足: {monthly_avg:.1f}時間/月\n")
                        f.write(f"    日平均不足: {monthly_avg/30:.1f}時間/日\n")
                        if monthly_avg > 5000:
                            f.write(f"    🚨 異常値検出: 月平均{monthly_avg:.0f}時間は過大 (期間依存性問題の可能性)\n")
                    
                except Exception as e:
                    f.write(f"  エラー: {e}\n")
            else:
                f.write("  shortage_time.parquet が見つかりません\n")
            
            # 🔍 STEP 2: 計算パラメータの詳細
            f.write(f"\n{'='*70}\n")
            f.write("【STEP 2: 計算パラメータ詳細分析】\n")
            calc_details = analysis_results.get('calculation_details', {})
            f.write(f"  slot_hours: {calc_details.get('slot_hours', 'N/A')}\n")
            f.write(f"  period_days: {calc_details.get('period_days', 'N/A')}\n")
            f.write(f"  avg_shortage_per_day: {calc_details.get('avg_shortage_per_day', 'N/A')}\n")
            f.write(f"  normalization_applied: {calc_details.get('normalization_applied', 'N/A')}\n")
            f.write(f"  normalization_factor: {calc_details.get('normalization_factor', 'N/A')}\n")
            
            # 🔍 STEP 3: Need計算の詳細
            f.write(f"\n{'='*70}\n")
            f.write("【STEP 3: Need計算方式の詳細】\n")
            need_details = analysis_results.get('need_calculation', {})
            f.write(f"  使用した統計手法: {need_details.get('statistic_method', 'N/A')}\n")
            f.write(f"  参照期間: {need_details.get('reference_period', 'N/A')}\n")
            f.write(f"  データソース: {need_details.get('data_source', 'N/A')}\n")
            f.write(f"  期間依存性の影響: {need_details.get('period_dependency_effect', 'N/A')}\n")
            
            # 🔍 STEP 4: 統計処理のブレークダウン
            f.write(f"\n{'='*70}\n") 
            f.write("【STEP 4: 統計処理詳細分析】\n")
            stats_details = analysis_results.get('statistics_breakdown', {})
            f.write(f"  データポイント数: {stats_details.get('data_points_count', 'N/A')}\n")
            f.write(f"  統計値計算方式: {stats_details.get('calculation_method', 'N/A')}\n")
            f.write(f"  外れ値除去: {stats_details.get('outlier_removal', 'N/A')}\n")
            f.write(f"  1ヶ月 vs 3ヶ月の差異: {stats_details.get('period_difference', 'N/A')}\n")
            
            # 🔍 STEP 5: 既存の全体サマリー  
            f.write(f"\n{'='*70}\n")
            f.write("【STEP 5: 従来の全体サマリー】\n")
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








def validate_calculation_flow(data_dict, stage_name):
    """
    計算フロー検証機能（COMPREHENSIVE_FIX）
    
    Args:
        data_dict: 検証対象データ辞書
        stage_name: 処理段階名
    
    Returns:
        validation_result: 検証結果辞書
    """
    
    validation_result = {
        "stage": stage_name,
        "timestamp": dt.datetime.now(),
        "checks": {},
        "warnings": [],
        "errors": []
    }
    
    try:
        # 基本データ存在チェック
        if "shortage_hours" in data_dict:
            hours = data_dict["shortage_hours"]
            
            # 妥当性チェック
            if hours < 0:
                validation_result["errors"].append(f"負の不足時間: {hours}")
            elif hours > 10000:  # 月次で10,000時間は異常
                validation_result["errors"].append(f"異常に大きな不足時間: {hours}")
            elif hours > 5000:
                validation_result["warnings"].append(f"高い不足時間: {hours}")
        
        # 期間チェック
        if "period_days" in data_dict:
            days = data_dict["period_days"]
            if days > 100:  # 3ヶ月を大幅に超える
                validation_result["warnings"].append(f"長期間データ: {days}日")
        
        # 単位一貫性チェック  
        if "total_slots" in data_dict and "total_hours" in data_dict:
            slots = data_dict["total_slots"]
            hours = data_dict["total_hours"]
            expected_hours = slots * 0.5  # 30分スロット
            
            if abs(hours - expected_hours) > 0.1:
                validation_result["errors"].append(
                    f"単位変換エラー: {slots}スロット ≠ {hours}時間 (期待値: {expected_hours})"
                )
        
        validation_result["checks"]["total_issues"] = len(validation_result["warnings"]) + len(validation_result["errors"])
        
        # ログ出力
        if validation_result["errors"]:
            log.error(f"[FLOW_VALIDATION] {stage_name}: エラー {len(validation_result['errors'])} 件")
            for error in validation_result["errors"]:
                log.error(f"[FLOW_VALIDATION] ERROR: {error}")
        
        if validation_result["warnings"]:
            log.warning(f"[FLOW_VALIDATION] {stage_name}: 警告 {len(validation_result['warnings'])} 件")
            for warning in validation_result["warnings"]:
                log.warning(f"[FLOW_VALIDATION] WARNING: {warning}")
        
        if not validation_result["errors"] and not validation_result["warnings"]:
            log.info(f"[FLOW_VALIDATION] {stage_name}: 検証通過")
    
    except Exception as e:
        validation_result["errors"].append(f"検証処理エラー: {str(e)}")
        log.error(f"[FLOW_VALIDATION] {stage_name}: 検証処理失敗: {e}")
    
    return validation_result




def apply_period_dependency_control(shortage_df, period_days, slot_hours):
    """
    期間依存性制御の強化（FINAL_FIX）
    長期分析での異常値を強制制限
    
    Args:
        shortage_df: 不足時間データフレーム
        period_days: 分析期間日数
        slot_hours: スロット時間
    
    Returns:
        制御済み不足データ、制御情報
    """
    
    original_total = shortage_df.sum().sum() * slot_hours
    daily_avg = original_total / period_days if period_days > 0 else 0
    
    # 期間による制御レベル設定
    if period_days > 180:  # 6ヶ月超
        max_daily_shortage = 2.0  # 非常に厳格
        log.warning(f"[PERIOD_CONTROL] 長期分析({period_days}日): 超厳格制限適用")
    elif period_days > 90:   # 3ヶ月超
        max_daily_shortage = 3.0  # 厳格
        log.warning(f"[PERIOD_CONTROL] 中長期分析({period_days}日): 厳格制限適用")
    elif period_days > 60:   # 2ヶ月超
        max_daily_shortage = 4.0  # やや厳格
        log.info(f"[PERIOD_CONTROL] 中期分析({period_days}日): やや厳格制限適用")
    else:
        max_daily_shortage = 5.0  # 標準
    
    # 制限適用
    if daily_avg > max_daily_shortage:
        control_factor = max_daily_shortage / daily_avg
        shortage_df = shortage_df * control_factor
        
        controlled_total = shortage_df.sum().sum() * slot_hours
        controlled_daily = controlled_total / period_days
        
        log.warning(f"[PERIOD_CONTROL] 期間制御適用: {original_total:.1f}h → {controlled_total:.1f}h")
        log.warning(f"[PERIOD_CONTROL] 日平均: {daily_avg:.1f}h/日 → {controlled_daily:.1f}h/日")
        
        control_info = {
            "applied": True,
            "original_total": original_total,
            "controlled_total": controlled_total,
            "control_factor": control_factor,
            "max_daily_allowed": max_daily_shortage
        }
    else:
        log.info(f"[PERIOD_CONTROL] 制御不要: {daily_avg:.1f}h/日 ≤ {max_daily_shortage}h/日")
        control_info = {
            "applied": False,
            "original_total": original_total,
            "daily_avg": daily_avg,
            "max_daily_allowed": max_daily_shortage
        }
    
    return shortage_df, control_info



def apply_period_normalization(shortage_df, period_days, slot_hours, normalization_base_days=30):
    """
    期間正規化機能（COMPREHENSIVE_FIX）
    
    Args:
        shortage_df: 不足時間データフレーム
        period_days: 分析対象期間の日数
        slot_hours: スロット時間（0.5時間）
        normalization_base_days: 正規化基準日数（デフォルト30日=月次）
    
    Returns:
        正規化済み不足データ、正規化係数、統計情報
    """
    
    if period_days <= 0:
        log.error("[PERIOD_NORM] 無効な期間日数")
        return shortage_df, 1.0, {"error": "invalid_period"}
    
    # 正規化係数計算
    normalization_factor = normalization_base_days / period_days
    
    # 正規化適用
    normalized_shortage_df = shortage_df * normalization_factor
    
    # 統計情報計算
    original_total_hours = shortage_df.sum().sum() * slot_hours
    normalized_total_hours = normalized_shortage_df.sum().sum() * slot_hours
    
    stats = {
        "original_period_days": period_days,
        "normalization_base_days": normalization_base_days,
        "normalization_factor": normalization_factor,
        "original_total_hours": original_total_hours,
        "normalized_total_hours": normalized_total_hours,
        "daily_average_original": original_total_hours / period_days,
        "daily_average_normalized": normalized_total_hours / normalization_base_days
    }
    
    log.info(f"[PERIOD_NORM] 期間正規化適用: {period_days}日 → {normalization_base_days}日基準")
    log.info(f"[PERIOD_NORM] 正規化前: {original_total_hours:.1f}時間")
    log.info(f"[PERIOD_NORM] 正規化後: {normalized_total_hours:.1f}時間")
    log.info(f"[PERIOD_NORM] 日平均: {stats['daily_average_original']:.1f}h/日 → {stats['daily_average_normalized']:.1f}h/日")
    
    return normalized_shortage_df, normalization_factor, stats



def validate_and_cap_shortage(shortage_df, period_days, slot_hours):
    """
    異常値検出と制限機能（27,486.5時間問題対策）
    
    Args:
        shortage_df: 不足時間データフレーム
        period_days: 対象期間の日数
        slot_hours: スロット時間（時間単位）
        
    Returns:
        (制限済み不足データ, 制限適用フラグ)
    """
    
    # 設定値
    MAX_SHORTAGE_PER_DAY = 5  # FINAL_FIX: 現実的な1日最大5時間
    # 理由: 24時間制でも1日5時間不足が現実的上限
    # まずは日毎に不足時間を集計し、日次上限を超える分を制限
    daily_totals = shortage_df.sum(axis=1) * slot_hours
    capped_dates = []
    for day, total in daily_totals.items():
        if total > MAX_SHORTAGE_PER_DAY:
            scale = MAX_SHORTAGE_PER_DAY / total
            shortage_df.loc[day] *= scale
            capped_dates.append(str(day))
            log.warning(f"[DAILY_CAP] {day}: {total:.1f}h -> {MAX_SHORTAGE_PER_DAY}h")

    capped = bool(capped_dates)

    if capped_dates:
        log.warning(f"[DAILY_CAP] Dates capped: {', '.join(capped_dates)}")

    # 日次制限後の総不足時間を計算し、依然として全体上限を超える場合は比例縮小
    total_shortage = shortage_df.sum().sum() * slot_hours
    max_allowed = MAX_SHORTAGE_PER_DAY * period_days

    if total_shortage > max_allowed:
        log.warning(
            f"[ANOMALY_DETECTED] Abnormal shortage time: {total_shortage:.0f}h > {max_allowed:.0f}h"
        )
        log.warning(
            f"[ANOMALY_DETECTED] Period: {period_days} days, Daily avg: {total_shortage/period_days:.0f}h/day"
        )

        # 比例縮小で制限
        scale_factor = max_allowed / total_shortage
        shortage_df = shortage_df * scale_factor

        log.warning(
            f"[CAPPED] Limitation applied: scale={scale_factor:.3f}, after={max_allowed:.0f}h"
        )

        capped = True

    return shortage_df, capped


def validate_need_data(need_df):
    """
    Needデータの妥当性検証（27,486.5時間問題対策）
    
    Args:
        need_df: 需要データフレーム
        
    Returns:
        検証・制限済み需要データ
    """
    
    if need_df.empty:
        return need_df
    
    max_need = need_df.max().max()
    if max_need > 2:  # FINAL_FIX: 1スロット2人以上は異常
        # 理由: 30分スロットに2人以上の需要は過大推定
        log.error(f"[NEED_ANOMALY] Abnormal Need value detected: {max_need:.1f} people/slot")
        need_df = need_df.clip(upper=1.5)  # FINAL_FIX: 上限1.5人に厳格制限
        # 理由: 30分スロットに1.5人以上は統計的過大推定
        log.warning("[NEED_CAPPED] Need values capped to 1.5 people/slot (FINAL_FIX)")

    return need_df


def align_need_staff_columns(need_df: pd.DataFrame, staff_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Restrict both DataFrames to their common day columns.

    Any non-overlapping columns are dropped and a warning is emitted to avoid
    mismatched days inflating shortage calculations.
    """

    common_cols = need_df.columns.intersection(staff_df.columns)
    if len(common_cols) != len(need_df.columns) or len(common_cols) != len(staff_df.columns):
        extra_need = need_df.columns.difference(common_cols).tolist()
        extra_staff = staff_df.columns.difference(common_cols).tolist()
        log.warning(
            "[shortage] Mismatched day columns detected; dropping non-overlapping days: "
            f"need_only={extra_need}, staff_only={extra_staff}"
        )
    return need_df[common_cols], staff_df[common_cols]


def detect_period_dependency_risk(period_days, total_shortage):
    """
    期間依存性リスクの検出
    
    Args:
        period_days: 期間日数
        total_shortage: 総不足時間
        
    Returns:
        リスク情報辞書
    """
    
    daily_shortage = total_shortage / period_days if period_days > 0 else 0
    monthly_shortage = daily_shortage * 30
    
    risk_level = "low"
    if monthly_shortage > 10000:
        risk_level = "critical"
    elif monthly_shortage > 5000:
        risk_level = "high"
    elif monthly_shortage > 2000:
        risk_level = "medium"
    
    risk_info = {
        "risk_level": risk_level,
        "daily_shortage": daily_shortage,
        "monthly_shortage": monthly_shortage,
        "period_days": period_days,
        "recommendation": {
            "low": "Normal range",
            "medium": "Consider monthly normalization",
            "high": "Monthly normalization strongly recommended",
            "critical": "Abnormal value detected - Data validation required"
        }.get(risk_level, "Unknown")
    }
    
    if risk_level in ["high", "critical"]:
        log.warning(f"[PERIOD_RISK] {risk_level}: {risk_info['recommendation']}")
        log.warning(f"[PERIOD_RISK] Monthly shortage: {monthly_shortage:.0f}h/month")
    
    return risk_info



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
    # 動的スロット設定: app.pyからのslot（分）を時間に変換
    slot_hours = slot / 60.0
    log.info(f"[shortage] 動的スロット設定: {slot}分 = {slot_hours}時間")

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

    # 統計手法に対応した詳細Needデータを読み込む
    need_per_date_slot_df = pd.DataFrame()
    
    # 🔧 CRITICAL FIX: 統計手法別のNeedファイルを統合して正しく読み込む
    need_role_files = list(out_dir_path.glob("need_per_date_slot_role_*.parquet"))
    
    if need_role_files:
        log.info(f"[shortage] ★★★ 統計手法対応: {len(need_role_files)}個の職種別Needファイルを統合します ★★★")
        
        # 全ての職種を公平に集計（複合職種も独立した職種として扱う）
        combined_need_df = pd.DataFrame()
        
        for need_file in need_role_files:
            try:
                role_need_df = pd.read_parquet(need_file)
                if combined_need_df.empty:
                    combined_need_df = role_need_df.copy()
                else:
                    # 同じ時間帯・日付での需要を合計
                    combined_need_df = combined_need_df.add(role_need_df, fill_value=0)
                log.debug(f"[shortage] 統合: {need_file.name} (形状: {role_need_df.shape})")
            except Exception as e:
                log.warning(f"[shortage] {need_file.name} の読み込みエラー: {e}")
        
        need_per_date_slot_df = combined_need_df
        log.info(f"[shortage] ★★★ 統計手法対応Need統合完了: 形状 {need_per_date_slot_df.shape} ★★★")
    else:
        # フォールバック: 従来の固定ファイル
        need_per_date_slot_fp = out_dir_path / "need_per_date_slot.parquet"
        if need_per_date_slot_fp.exists():
            try:
                need_per_date_slot_df = pd.read_parquet(need_per_date_slot_fp)
                log.warning(
                    "[shortage] ⚠️ 職種別Needファイルが見つからないため、固定ファイルを使用 ⚠️"
                )
            except Exception as e:
                log.warning(f"[shortage] need_per_date_slot.parquet の読み込みエラー: {e}")
        else:
            log.warning("[shortage] ⚠️ 利用可能なNeedファイルが見つかりません ⚠️")

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

    
        
    # Phase 2: 異常値検出・制限機能の統合（27,486.5時間問題対策）
    period_days = len(date_columns_in_heat_all)
    
    # Need データの検証・制限
    need_df_all = validate_need_data(need_df_all)

    # 列の不一致を解消してから不足時間を計算
    need_df_all, staff_actual_data_all_df = align_need_staff_columns(
        need_df_all, staff_actual_data_all_df
    )

    # 期間依存性リスクの事前チェックとデータ期間の制御
    temp_lack_df = need_df_all - staff_actual_data_all_df
    pre_total_shortage = temp_lack_df.sum().sum() * slot_hours
    pre_risk = detect_period_dependency_risk(period_days, pre_total_shortage)

    MAX_PERIOD_DAYS = 90
    if period_days > MAX_PERIOD_DAYS:
        log.warning(
            f"[PERIOD_PRECHECK] {period_days}日分のデータを検出。{MAX_PERIOD_DAYS}日に切り詰めます。"
        )
        keep_cols = date_columns_in_heat_all[:MAX_PERIOD_DAYS]
        need_df_all = need_df_all[keep_cols]
        staff_actual_data_all_df = staff_actual_data_all_df[keep_cols]
        temp_lack_df = temp_lack_df[keep_cols]
        date_columns_in_heat_all = keep_cols
        period_days = len(keep_cols)
    elif pre_risk["risk_level"] in ["high", "critical"]:
        log.warning(
            f"[PERIOD_PRECHECK] Period dependency risk detected: {pre_risk['risk_level']}"
        )

    # 不足時間計算（最終確定）
    lack_count_overall_df = temp_lack_df
    
    # COMPREHENSIVE_FIX: 期間正規化の統合
    # 期間が30日と大きく異なる場合は正規化適用
    if abs(period_days - 30) > 7:  # 30日±7日の範囲外
        lack_count_overall_df, norm_factor, norm_stats = apply_period_normalization(
            lack_count_overall_df, period_days, slot_hours
        )
        log.warning(f"[COMPREHENSIVE_FIX] 期間正規化適用: {norm_stats['normalization_factor']:.3f}")
    
    # FINAL_FIX: 期間依存性制御の統合
    lack_count_overall_df, control_info = apply_period_dependency_control(
        lack_count_overall_df, period_days, slot_hours
    )
    
    if control_info["applied"]:
        log.warning("[FINAL_FIX] 期間依存性制御が適用されました")
    
    # 異常値検出・制限の適用
    lack_count_overall_df, was_capped = validate_and_cap_shortage(
        lack_count_overall_df, period_days, slot_hours
    )
    
    
    # FINAL_FIX: 最終妥当性チェック
    final_total_shortage = lack_count_overall_df.sum().sum() * slot_hours
    final_daily_avg = final_total_shortage / period_days if period_days > 0 else 0
    
    log.info(f"[FINAL_VALIDATION] 最終不足時間: {final_total_shortage:.1f}時間")
    log.info(f"[FINAL_VALIDATION] 最終日平均: {final_daily_avg:.1f}時間/日")
    
    # 妥当性判定
    if final_daily_avg <= 3.0:
        log.info(f"[FINAL_VALIDATION] ✅ 理想的範囲: {final_daily_avg:.1f}h/日 ≤ 3.0h/日")
    elif final_daily_avg <= 5.0:
        log.info(f"[FINAL_VALIDATION] ✅ 許容範囲: {final_daily_avg:.1f}h/日 ≤ 5.0h/日")
    elif final_daily_avg <= 8.0:
        log.warning(f"[FINAL_VALIDATION] ⚠️ 要改善: {final_daily_avg:.1f}h/日 > 5.0h/日")
    else:
        log.error(f"[FINAL_VALIDATION] ❌ 依然異常: {final_daily_avg:.1f}h/日 > 8.0h/日")
        log.error("[FINAL_VALIDATION] 追加の計算エラーが残存している可能性")
    
    
    # 期間依存性リスクの検出
    risk_info = detect_period_dependency_risk(
        period_days, lack_count_overall_df.sum().sum() * slot_hours
    )
    
    if was_capped:
        log.warning("[PHASE2_APPLIED] Anomaly detection and limitation applied")
    if risk_info["risk_level"] in ["high", "critical"]:
        log.warning(f"[PHASE2_RISK] Period dependency risk: {risk_info['risk_level']}")
    
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

    # 按分計算関連の変数を初期化（按分計算は使用しない）
    working_data_for_proportional = pd.DataFrame()
    total_shortage_hours_for_proportional = 0.0

    role_kpi_rows: List[Dict[str, Any]] = []
    monthly_role_rows: List[Dict[str, Any]] = []
    processed_role_names_list = []

    for fp_role_heatmap_item in out_dir_path.glob("heat_*.xlsx"):
        if fp_role_heatmap_item.name == "heat_ALL.xlsx":
            continue
        
        # 雇用形態別ファイル(heat_emp_*)は職種別処理から除外
        if fp_role_heatmap_item.name.startswith("heat_emp_"):
            log.info(f"[shortage] スキップ: {fp_role_heatmap_item.name} (雇用形態別データのため職種処理から除外)")
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
        # 修正: 人数不足 × スロット時間 = 時間不足の正しい計算
        total_lack_hours_for_role = (
            (role_lack_count_for_specific_role_df * slot_hours).sum().sum()
        )
        # excess_h は休業日のupper=0を考慮したexcessの合計
        # 修正: 人数過剰 × スロット時間 = 時間過剰の正しい計算
        total_excess_hours_for_role = (
            (role_excess_count_for_specific_role_df * slot_hours).sum().sum()
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
                # 修正: 人数不足 × スロット時間 = 時間不足の正しい計算
                daily_lack_h = (
                    (role_lack_count_for_specific_role_df * slot_hours).sum()
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

        # 🔧 デバッグ: 異常値チェック
        if total_lack_hours_for_role > 10000:
            log.warning(f"⚠️ [shortage] 異常な不足時間検出: {role_name_current}")
            log.warning(f"  total_lack_hours_for_role: {total_lack_hours_for_role:.0f}時間")
            log.warning(f"  slot_hours: {slot_hours:.2f}")
        
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

    # 按分計算は使用しないため、role_shortagesは使わない
    role_shortages = {}

    # emp_データを除外するフィルタリング
    role_kpi_rows_filtered = []
    for row in role_kpi_rows:
        role_name = row.get('role', '')
        if role_name.startswith('emp_'):
            log.warning(f"[shortage] 雇用形態データを職種リストから除外: {role_name}")
        else:
            role_kpi_rows_filtered.append(row)
    
    role_summary_df = pd.DataFrame(role_kpi_rows_filtered)
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
        # 修正: 人数不足 × スロット時間 = 時間不足の正しい計算
        total_lack_hours_for_emp = (lack_count_emp_df * slot_hours).sum().sum()
        # 修正: 人数過剰 × スロット時間 = 時間過剰の正しい計算  
        total_excess_hours_for_emp = (
            (excess_count_emp_df * slot_hours).sum().sum()
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
            log.warning("[shortage] shortage_time.parquetが見つからないため、曜日別サマリーをスキップ")
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
        
        # ログファイル作成（デバッグ情報を追加）
        analysis_results['calculation_details'] = calculation_details
        create_timestamped_log(analysis_results, out_dir_path)
        
        # リアルタイム洞察検出を実行
        try:
            from shift_suite.tasks.real_time_insight_detector import RealTimeInsightDetector
            
            # 必要なデータの準備
            intermediate_path = out_dir_path / 'intermediate_data.parquet'
            shortage_role_path = fp_shortage_role if fp_shortage_role else None
            
            if intermediate_path.exists() and shortage_role_path and shortage_role_path.exists():
                intermediate_df = pd.read_parquet(intermediate_path)
                shortage_df = pd.read_parquet(shortage_role_path)
                
                # 洞察検出器を初期化
                detector = RealTimeInsightDetector()
                
                # 洞察を検出
                insights = detector.analyze_shortage_data(
                    shortage_data=shortage_df,
                    intermediate_data=intermediate_df,
                    need_data=None  # 必要に応じて追加
                )
                
                # レポート生成
                insight_report_path = out_dir_path / 'real_time_insights.json'
                report = detector.generate_insight_report(insight_report_path)
                
                # エグゼクティブサマリー生成
                summary = detector.generate_executive_summary()
                summary_path = out_dir_path / 'insight_executive_summary.txt'
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                log.info(f"[INSIGHTS] リアルタイム洞察検出完了: {len(insights)}個の洞察を発見")
                
                # 重要な洞察をログに記録
                critical_insights = [i for i in insights if i.severity.value in ['critical', 'high']]
                for insight in critical_insights[:5]:
                    log.warning(f"[CRITICAL_INSIGHT] {insight.title}: {insight.description}")
                    if insight.financial_impact:
                        log.warning(f"  財務影響: {insight.financial_impact:.1f}万円/月")
                    if insight.recommended_action:
                        log.warning(f"  推奨アクション: {insight.recommended_action}")
                
                # 分析結果に洞察情報を追加
                analysis_results['insights'] = {
                    'total_count': len(insights),
                    'critical_count': sum(1 for i in insights if i.severity.value == 'critical'),
                    'high_count': sum(1 for i in insights if i.severity.value == 'high'),
                    'total_financial_impact': report['total_financial_impact'],
                    'report_path': str(insight_report_path),
                    'summary_path': str(summary_path)
                }
                
        except Exception as e:
            log.error(f"[INSIGHTS] リアルタイム洞察検出でエラー: {e}")
            # エラーでも処理は継続
        
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


def assign_shortage_to_individuals(
    actual_df: pd.DataFrame,
    shortage_df: pd.DataFrame,
    time_unit_minutes: int
) -> pd.DataFrame:
    """実績データに3シナリオ分の不足値を割り当てる。

    Args:
        actual_df (pd.DataFrame): 個々の勤務記録を含む実績データ。
        shortage_df (pd.DataFrame): ``calculate_time_axis_shortage`` の結果。
        time_unit_minutes (int): 時間グループ化に用いる単位（分）。

    Returns:
        pd.DataFrame: 不足値を列として追加した実績データ。
    """
    freq = f"{time_unit_minutes}min"
    df = actual_df.copy()
    df['time_group'] = df['timestamp'].dt.floor(freq)

    # カラム名の正規化：英語→日本語に統一
    column_mapping = {
        'role': '職種',
        'employment': '雇用形態',
        'employment_type': '雇用形態'
    }
    
    # 実績データのカラム正規化
    rename_dict = {}
    for eng_col, jp_col in column_mapping.items():
        if eng_col in df.columns:
            rename_dict[eng_col] = jp_col
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    # 不足データのカラム正規化
    shortage_df_normalized = shortage_df.copy()
    shortage_rename_dict = {}
    for eng_col, jp_col in column_mapping.items():
        if eng_col in shortage_df_normalized.columns:
            shortage_rename_dict[eng_col] = jp_col
    
    if shortage_rename_dict:
        shortage_df_normalized = shortage_df_normalized.rename(columns=shortage_rename_dict)
    
    # 必須カラムが存在するかチェック
    required_columns = ['職種', '雇用形態']
    for col in required_columns:
        if col not in df.columns:
            if col == '職種':
                df['職種'] = 'unknown_role'
            elif col == '雇用形態':
                df['雇用形態'] = 'unknown_employment'
        
        if col not in shortage_df_normalized.columns:
            if col == '職種':
                shortage_df_normalized['職種'] = 'unknown_role'
            elif col == '雇用形態':
                shortage_df_normalized['雇用形態'] = 'unknown_employment'

    merge_cols = ['time_group', '職種', '雇用形態']
    shortage_cols = ['shortage_mean', 'shortage_median', 'shortage_p25']
    cols_to_add = ['actual_count'] + shortage_cols

    merged = df.merge(
        shortage_df_normalized[merge_cols + cols_to_add],
        on=merge_cols,
        how='left'
    ).fillna({col: 0 for col in cols_to_add})

    return merged
