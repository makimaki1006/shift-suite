# ─────────────────────────────  app.py  (Part 1 / 3)  ──────────────────────────
# Shift-Suite Streamlit GUI + 内蔵ダッシュボード  v1.30.0 (休暇分析機能追加)
# ==============================================================================
# 変更履歴
#   • v1.30.0: 休暇分析機能を追加。leave_analyzer モジュールとの連携を実装。
#   • v1.29.13: st.experimental_rerun() を st.rerun() に修正。
#   • v1.29.12: need_ref_start/end_date_widget の StreamlitAPIException 対策。
#               ファイルアップロード時の日付範囲推定結果を、フラグを用いて
#               次回のスクリプト実行時にウィジェットのデフォルト値として安全に反映するよう修正。
#   • v1.29.11: ログで指摘されたエラー箇所を修正。
#               - shift_sheets_multiselect_widget の StreamlitAPIException 対策。
#               - param_penalty_per_lack の NameError 修正。
#               - progress_bar_exec_main_run 等の NameError 修正。
#               - ログメッセージ内のタイポ修正。
#   • v1.29.10: selectboxのdefault引数エラーをindexに統一し、オプションリストをセッションから正しく参照。
#               全てのウィジェットの値をセッションステートで管理し、初期化を徹底。
#               ヘッダー開始行UIの表示と値の利用を確実化。
#               Excel日付範囲推定の安定化。
#               on_changeコールバックを削除し、よりシンプルなセッションステート管理を目指す。
# ==============================================================================

from __future__ import annotations

import datetime
import io
import logging
import os

# Streamlit's watchdog can print repeated errors on Windows
# unless STREAMLIT_WATCHER_TYPE is set to "poll".
os.environ.setdefault("STREAMLIT_WATCHER_TYPE", "poll")

import re
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import IO, Optional
import json
import numpy as np

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import subprocess
from streamlit.runtime import exists as st_runtime_exists

try:
    from streamlit_plotly_events import plotly_events
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    plotly_events = None
    logging.getLogger(__name__).warning(
        "streamlit-plotly-events not installed; interactive plots disabled"
    )
import datetime as dt

from shift_suite.i18n import translate as _
from shift_suite.logger_config import configure_logging
from shift_suite.tasks import (
    dashboard,
    leave_analyzer,  #  新規インポート
    over_shortage_log,
)
from shift_suite.tasks.utils import (
    safe_read_excel,
    safe_sheet,
    _parse_as_date,
    _valid_df,
    date_with_weekday,
)

# 🎯 実行結果テキスト出力機能追加
try:
    from execution_logger import create_app_logger, ExecutionLogger
    EXECUTION_LOGGING_AVAILABLE = True
except ImportError:
    EXECUTION_LOGGING_AVAILABLE = False
    log.warning("実行ログ機能が利用できません")

# ──────────────────────────────────────────────────────────────────────────────
from shift_suite.tasks.analyzers import (
    AttendanceBehaviorAnalyzer,
    CombinedScoreCalculator,
    LowStaffLoadAnalyzer,
    RestTimeAnalyzer,
    WorkPatternAnalyzer,
)
from shift_suite.tasks.anomaly import detect_anomaly
from shift_suite.tasks.build_stats import build_stats
from shift_suite.tasks.cluster import cluster_staff
from shift_suite.tasks.constants import SUMMARY5 as SUMMARY5_CONST
from shift_suite.tasks.cost_benefit import analyze_cost_benefit
from shift_suite.tasks.fairness import run_fairness
from shift_suite.tasks.fatigue import train_fatigue
from shift_suite.tasks.forecast import build_demand_series, forecast_need
from shift_suite.tasks.h2hire import build_hire_plan as build_hire_plan_from_kpi
from shift_suite.tasks.heatmap import build_heatmap
from shift_suite.tasks.hire_plan import build_hire_plan

# ── Shift-Suite task modules ─────────────────────────────────────────────────
from shift_suite.tasks.io_excel import SHEET_COL_ALIAS, _normalize, ingest_excel
from shift_suite.tasks.leave_analyzer import (
    LEAVE_TYPE_PAID,
    LEAVE_TYPE_REQUESTED,
    LEAVE_TYPE_OTHER,
)
# from shift_suite.tasks.rl import learn_roster  # Temporarily disabled due to gymnasium dependency
from shift_suite.tasks.shortage import (
    merge_shortage_leave,
    shortage_and_brief,
    weekday_timeslot_summary,
)
from shift_suite.tasks.shortage_factor_analyzer import ShortageFactorAnalyzer
from shift_suite.tasks.skill_nmf import build_skill_matrix
from shift_suite.tasks.daily_cost import calculate_daily_cost  # <-- added
from shift_suite.tasks.optimal_hire_plan import create_optimal_hire_plan

# ★新規インポート
from shift_suite.tasks.gap_analyzer import analyze_standards_gap
from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt


def create_comprehensive_analysis_log(output_dir: Path, analysis_type: str = "FULL") -> Path:
    """包括的な分析ログファイルを作成（app.py用）- 詳細版"""
    timestamp = datetime.datetime.now().strftime("%Y年%m月%d日%H時%M分")
    log_filename = f"{timestamp}_包括分析レポート_{analysis_type}.txt"
    log_filepath = output_dir / log_filename
    
    try:
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write(f"                           包括分析結果レポート\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"生成日時: {timestamp}\n")
            f.write(f"分析タイプ: {analysis_type}\n")
            f.write(f"分析ディレクトリ: {output_dir}\n")
            f.write(f"分析エンジンバージョン: Shift-Suite v1.30.0\n")
            f.write("=" * 100 + "\n\n")
            
            # 1. 実行サマリー（詳細版）
            f.write("【1. 実行サマリー】\n")
            f.write("-" * 80 + "\n")
            summary_stats = collect_execution_summary(output_dir)
            f.write(f"  実行開始時刻: {summary_stats.get('start_time', 'N/A')}\n")
            f.write(f"  実行終了時刻: {summary_stats.get('end_time', 'N/A')}\n")
            f.write(f"  処理時間: {summary_stats.get('duration', 'N/A')}\n")
            f.write(f"  処理ステップ数: {summary_stats.get('total_steps', 0)}\n")
            f.write(f"  成功ステップ数: {summary_stats.get('successful_steps', 0)}\n")
            f.write(f"  エラーステップ数: {summary_stats.get('failed_steps', 0)}\n")
            f.write(f"  警告数: {summary_stats.get('warnings', 0)}\n")
            f.write(f"  使用メモリ: {summary_stats.get('memory_usage', 'N/A')}\n")
            f.write(f"  実行環境: {summary_stats.get('environment', 'N/A')}\n\n")
            
            # 2. データ概要（詳細版）
            f.write("【2. データ概要】\n")
            f.write("-" * 80 + "\n")
            data_stats = collect_data_overview(output_dir)
            f.write(f"  対象期間: {data_stats.get('date_range', 'N/A')}\n")
            f.write(f"  総レコード数: {data_stats.get('total_records', 0):,}件\n")
            f.write(f"  スタッフ数: {data_stats.get('total_staff', 0)}名\n")
            f.write(f"  職種数: {data_stats.get('total_roles', 0)}種類\n")
            f.write(f"  雇用形態数: {data_stats.get('total_employments', 0)}種類\n")
            f.write(f"  勤務パターン数: {data_stats.get('total_patterns', 0)}種類\n")
            f.write(f"  休業日数: {data_stats.get('holiday_count', 0)}日\n")
            f.write(f"  スロット間隔: {data_stats.get('slot_minutes', 30)}分\n")
            f.write(f"  時間軸数: {data_stats.get('time_slots', 48)}スロット/日\n\n")
            
            # 3. 主要KPI（詳細版）
            f.write("【3. 主要KPI】\n")
            f.write("-" * 80 + "\n")
            kpi_stats = collect_main_kpis(output_dir)
            f.write(f"  ■ 不足・過剰分析\n")
            f.write(f"    総不足時間: {kpi_stats.get('total_shortage_hours', 0):.2f}時間\n")
            f.write(f"    総過剰時間: {kpi_stats.get('total_excess_hours', 0):.2f}時間\n")
            f.write(f"    不足率: {kpi_stats.get('shortage_ratio', 0):.2%}\n")
            f.write(f"    過剰率: {kpi_stats.get('excess_ratio', 0):.2%}\n")
            f.write(f"    最大不足時間（1日）: {kpi_stats.get('max_daily_shortage', 0):.1f}時間\n")
            f.write(f"    平均不足時間（1日）: {kpi_stats.get('avg_daily_shortage', 0):.1f}時間\n")
            f.write(f"\n  ■ 労務指標\n")
            f.write(f"    平均疲労スコア: {kpi_stats.get('avg_fatigue_score', 0):.2f}\n")
            f.write(f"    公平性スコア: {kpi_stats.get('fairness_score', 0):.2f}\n")
            f.write(f"    最適化スコア: {kpi_stats.get('optimization_score', 0):.2f}\n")
            f.write(f"    リスクスコア: {kpi_stats.get('risk_score', 0):.2f}\n")
            f.write(f"\n  ■ コスト指標\n")
            f.write(f"    総人件費: ¥{kpi_stats.get('total_cost', 0):,.0f}\n")
            f.write(f"    月平均人件費: ¥{kpi_stats.get('monthly_avg_cost', 0):,.0f}\n")
            f.write(f"    時間単価平均: ¥{kpi_stats.get('avg_hourly_rate', 0):.0f}\n")
            f.write(f"    不足時間の機会損失: ¥{kpi_stats.get('shortage_opportunity_cost', 0):,.0f}\n\n")
            
            # 4. 職種別パフォーマンス（詳細版）
            f.write("【4. 職種別パフォーマンス】\n")
            f.write("-" * 80 + "\n")
            role_performance = collect_role_performance_detailed(output_dir)
            if role_performance:
                for i, role in enumerate(role_performance, 1):
                    f.write(f"\n  ◆ {i}. {role.get('role', 'N/A')}\n")
                    f.write(f"    ├─ 不足時間: {role.get('shortage_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 過剰時間: {role.get('excess_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 必要人員: {role.get('required_staff', 0):.1f}人\n")
                    f.write(f"    ├─ 実績人員: {role.get('actual_staff', 0):.1f}人\n")
                    f.write(f"    ├─ 充足率: {role.get('fulfillment_rate', 0):.1%}\n")
                    f.write(f"    ├─ 平均疲労スコア: {role.get('avg_fatigue', 0):.2f}\n")
                    f.write(f"    ├─ 公平性スコア: {role.get('fairness_score', 0):.2f}\n")
                    f.write(f"    ├─ 人件費: ¥{role.get('total_cost', 0):,.0f}\n")
                    f.write(f"    ├─ コスト比率: {role.get('cost_ratio', 0):.1%}\n")
                    f.write(f"    └─ 主要課題: {role.get('main_issue', 'N/A')}\n")
            else:
                f.write("  職種別データなし\n")
            
            # 5. 雇用形態別分析（詳細版）
            f.write("\n【5. 雇用形態別分析】\n")
            f.write("-" * 80 + "\n")
            emp_analysis = collect_employment_analysis_detailed(output_dir)
            if emp_analysis:
                for i, emp in enumerate(emp_analysis, 1):
                    f.write(f"\n  ◆ {i}. {emp.get('employment', 'N/A')}\n")
                    f.write(f"    ├─ 総人数: {emp.get('staff_count', 0)}人\n")
                    f.write(f"    ├─ 不足時間: {emp.get('shortage_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 過剰時間: {emp.get('excess_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 平均勤務時間: {emp.get('avg_work_hours', 0):.1f}時間/月\n")
                    f.write(f"    ├─ 時給平均: ¥{emp.get('avg_hourly_wage', 0):.0f}\n")
                    f.write(f"    ├─ 総人件費: ¥{emp.get('total_cost', 0):,.0f}\n")
                    f.write(f"    ├─ 効率性指標: {emp.get('efficiency', 0):.2f}\n")
                    f.write(f"    └─ 活用度: {emp.get('utilization', 0):.1%}\n")
            
            # 6. 月別トレンド（詳細版）
            f.write("\n【6. 月別トレンド分析】\n")
            f.write("-" * 80 + "\n")
            monthly_trends = collect_monthly_trends_detailed(output_dir)
            if monthly_trends:
                for month_data in monthly_trends:
                    month = month_data.get('month', 'N/A')
                    f.write(f"\n  ■ {month}\n")
                    f.write(f"    ├─ 不足時間: {month_data.get('shortage_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 過剰時間: {month_data.get('excess_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 休暇日数: {month_data.get('leave_days', 0):.0f}日\n")
                    f.write(f"    ├─ 有給取得: {month_data.get('paid_leave', 0):.0f}日\n")
                    f.write(f"    ├─ アラート数: {month_data.get('alerts', 0)}件\n")
                    f.write(f"    ├─ 疲労度平均: {month_data.get('avg_fatigue', 0):.2f}\n")
                    f.write(f"    ├─ 人件費: ¥{month_data.get('cost', 0):,.0f}\n")
                    f.write(f"    └─ 特記事項: {month_data.get('notes', 'なし')}\n")
            
            # 7. 時間帯別分析（新規追加）
            f.write("\n【7. 時間帯別分析】\n")
            f.write("-" * 80 + "\n")
            time_analysis = collect_time_slot_analysis(output_dir)
            if time_analysis:
                f.write("  時間帯     | 平均必要人員 | 平均実績人員 | 不足率 | 主要職種\n")
                f.write("  " + "-" * 65 + "\n")
                for slot in time_analysis[:10]:  # 上位10時間帯
                    time_slot = str(slot.get('time_slot', 'N/A')).ljust(10)
                    avg_need = slot.get('avg_need', 0)
                    avg_actual = slot.get('avg_actual', 0)
                    shortage_rate = slot.get('shortage_rate', 0)
                    main_role = slot.get('main_role', 'N/A')[:10]
                    f.write(f"  {time_slot} | {avg_need:12.1f} | {avg_actual:12.1f} | {shortage_rate:6.1%} | {main_role}\n")
            
            # 8. 勤務パターン分析（新規追加）
            f.write("\n【8. 勤務パターン分析】\n")
            f.write("-" * 80 + "\n")
            pattern_analysis = collect_work_pattern_analysis(output_dir)
            if pattern_analysis:
                for i, pattern in enumerate(pattern_analysis[:15], 1):  # 上位15パターン
                    f.write(f"\n  ◆ パターン{i}: {pattern.get('pattern_name', 'N/A')}\n")
                    f.write(f"    ├─ 使用頻度: {pattern.get('frequency', 0)}回\n")
                    f.write(f"    ├─ スタッフ数: {pattern.get('staff_count', 0)}人\n")
                    f.write(f"    ├─ 1日勤務時間: {pattern.get('daily_hours', 0):.1f}時間\n")
                    f.write(f"    ├─ 連続勤務: {pattern.get('consecutive_days', 0)}日\n")
                    f.write(f"    ├─ 疲労影響: {pattern.get('fatigue_impact', 'N/A')}\n")
                    f.write(f"    └─ 推奨度: {pattern.get('recommendation_score', 0):.1f}/10\n")
            
            # 9. 休暇分析（詳細版）
            f.write("\n【9. 休暇分析】\n")
            f.write("-" * 80 + "\n")
            leave_analysis = collect_leave_analysis_detailed(output_dir)
            if leave_analysis:
                f.write(f"  ■ 全体統計\n")
                f.write(f"    総休暇日数: {leave_analysis.get('total_leave_days', 0):.0f}日\n")
                f.write(f"    有給取得率: {leave_analysis.get('paid_leave_ratio', 0):.1%}\n")
                f.write(f"    希望休取得率: {leave_analysis.get('requested_leave_ratio', 0):.1%}\n")
                f.write(f"    集中日数: {leave_analysis.get('concentration_days', 0)}日\n")
                f.write(f"\n  ■ 休暇タイプ別内訳\n")
                for leave_type in leave_analysis.get('by_type', []):
                    f.write(f"    {leave_type['type']}: {leave_type['days']}日 ({leave_type['ratio']:.1%})\n")
                f.write(f"\n  ■ 月別休暇傾向\n")
                for month_leave in leave_analysis.get('monthly', [])[:6]:
                    f.write(f"    {month_leave['month']}: {month_leave['days']}日\n")
            
            # 10. 異常値・アラート分析（新規追加）
            f.write("\n【10. 異常値・アラート分析】\n")
            f.write("-" * 80 + "\n")
            anomaly_analysis = collect_anomaly_analysis(output_dir)
            if anomaly_analysis:
                f.write(f"  ■ 検出された異常値\n")
                for i, anomaly in enumerate(anomaly_analysis.get('anomalies', [])[:10], 1):
                    f.write(f"    {i}. {anomaly['date']} {anomaly['type']}: {anomaly['description']}\n")
                f.write(f"\n  ■ アラート統計\n")
                f.write(f"    高リスクアラート: {anomaly_analysis.get('high_risk_count', 0)}件\n")
                f.write(f"    中リスクアラート: {anomaly_analysis.get('medium_risk_count', 0)}件\n")
                f.write(f"    低リスクアラート: {anomaly_analysis.get('low_risk_count', 0)}件\n")
            
            # 11. ブループリント分析サマリー（新規追加）
            f.write("\n【11. ブループリント分析サマリー】\n")
            f.write("-" * 80 + "\n")
            blueprint_summary = collect_blueprint_summary(output_dir)
            if blueprint_summary:
                f.write(f"  ■ 発見された暗黙知\n")
                for i, knowledge in enumerate(blueprint_summary.get('implicit_knowledge', [])[:20], 1):
                    f.write(f"    {i}. {knowledge}\n")
                f.write(f"\n  ■ 制約パターン\n")
                for i, constraint in enumerate(blueprint_summary.get('constraints', [])[:15], 1):
                    f.write(f"    {i}. {constraint}\n")
                f.write(f"\n  ■ 最適化提案\n")
                for i, suggestion in enumerate(blueprint_summary.get('optimization_suggestions', [])[:10], 1):
                    f.write(f"    {i}. {suggestion}\n")
            
            # 12. 生成ファイル一覧（詳細版）
            f.write("\n【12. 生成ファイル一覧】\n")
            f.write("-" * 80 + "\n")
            generated_files = collect_generated_files_detailed(output_dir)
            if generated_files:
                for category, files in generated_files.items():
                    f.write(f"\n  ■ {category}\n")
                    for file_info in files:
                        f.write(f"    {file_info}\n")
            
            # 13. システム推奨事項（詳細版）
            f.write("\n【13. システム推奨事項】\n")
            f.write("-" * 80 + "\n")
            recommendations = generate_comprehensive_recommendations(output_dir)
            if recommendations:
                f.write("  ■ 緊急対応事項\n")
                for i, rec in enumerate(recommendations.get('urgent', []), 1):
                    f.write(f"    {i}. {rec}\n")
                f.write("\n  ■ 短期改善事項（1-3ヶ月）\n")
                for i, rec in enumerate(recommendations.get('short_term', []), 1):
                    f.write(f"    {i}. {rec}\n")
                f.write("\n  ■ 中長期改善事項（3-6ヶ月）\n")
                for i, rec in enumerate(recommendations.get('long_term', []), 1):
                    f.write(f"    {i}. {rec}\n")
            
            # 14. 詳細データダンプ（オプション）
            if analysis_type == "FULL":
                f.write("\n【14. 詳細データダンプ】\n")
                f.write("-" * 80 + "\n")
                f.write("  ※ 詳細データは別ファイルに出力されています。\n")
                f.write(f"    - {timestamp}_詳細データ_職種別.csv\n")
                f.write(f"    - {timestamp}_詳細データ_時系列.csv\n")
                f.write(f"    - {timestamp}_詳細データ_パターン.csv\n")
            
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"レポート生成完了: {timestamp}\n")
            f.write("このレポートは機密情報を含む可能性があります。取り扱いにご注意ください。\n")
            f.write("=" * 100 + "\n")
            
        logging.info(f"[app] 包括分析ログファイルを作成しました: {log_filepath}")
        return log_filepath
        
    except Exception as e:
        logging.error(f"[app] 包括分析ログ作成エラー: {e}")
        return None


def collect_execution_summary(output_dir: Path) -> dict:
    """実行サマリー情報を収集"""
    try:
        # 実行時間の推定（ファイル更新時刻から）
        parquet_files = list(output_dir.glob("*.parquet"))
        if parquet_files:
            timestamps = [f.stat().st_mtime for f in parquet_files]
            start_time = datetime.datetime.fromtimestamp(min(timestamps)).strftime("%H:%M:%S")
            end_time = datetime.datetime.fromtimestamp(max(timestamps)).strftime("%H:%M:%S")
            duration_sec = max(timestamps) - min(timestamps)
            duration = f"{duration_sec:.1f}秒"
        else:
            start_time = "N/A"
            end_time = "N/A"
            duration = "N/A"
        
        # ファイル数からステップ数を推定
        all_files = list(output_dir.glob("*"))
        successful_steps = len([f for f in all_files if f.suffix in ['.parquet', '.xlsx', '.json']])
        total_steps = successful_steps  # エラーステップの正確な計測は困難
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'failed_steps': 0
        }
    except:
        return {}


def collect_data_overview(output_dir: Path) -> dict:
    """データ概要情報を収集"""
    try:
        # メタデータから情報を取得
        meta_file = output_dir / "heatmap.meta.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            dates = meta_data.get('dates', [])
            roles = meta_data.get('roles', [])
            employments = meta_data.get('employments', [])
            
            date_range = f"{dates[0]} ～ {dates[-1]}" if dates else "N/A"
            
            # heat_ALL.parquetからレコード数を取得
            heat_all_file = output_dir / "heat_ALL.parquet"
            total_records = 0
            if heat_all_file.exists():
                try:
                    df = pd.read_parquet(heat_all_file)
                    total_records = df.shape[0] * df.shape[1] if not df.empty else 0
                except:
                    pass
            
            return {
                'date_range': date_range,
                'total_records': total_records,
                'total_staff': 0,  # スタッフ数は他のファイルから取得が必要
                'total_roles': len(roles),
                'total_employments': len(employments),
                'total_patterns': 0  # パターン数も他のファイルから取得が必要
            }
        else:
            return {}
    except:
        return {}


def collect_main_kpis(output_dir: Path) -> dict:
    """主要KPI情報を収集"""
    try:
        kpis = {}
        
        # shortage_role_summary.parquetから不足・過剰時間
        shortage_role_file = output_dir / "shortage_role_summary.parquet"
        if shortage_role_file.exists():
            try:
                df = pd.read_parquet(shortage_role_file)
                kpis['total_shortage_hours'] = df.get('lack_h', pd.Series()).sum()
                kpis['total_excess_hours'] = df.get('excess_h', pd.Series()).sum()
            except:
                pass
        
        # fatigue_score.parquetから疲労スコア
        fatigue_file = output_dir / "fatigue_score.parquet"
        if fatigue_file.exists():
            try:
                df = pd.read_parquet(fatigue_file)
                kpis['avg_fatigue_score'] = df.get('fatigue_score', pd.Series()).mean()
            except:
                pass
        
        # fairness_after.parquetから公平性スコア
        fairness_file = output_dir / "fairness_after.parquet"
        if fairness_file.exists():
            try:
                df = pd.read_parquet(fairness_file)
                kpis['fairness_score'] = df.get('fairness_score', pd.Series()).mean()
            except:
                pass
        
        # その他のデフォルト値
        kpis.setdefault('total_shortage_hours', 0)
        kpis.setdefault('total_excess_hours', 0)
        kpis.setdefault('avg_fatigue_score', 0)
        kpis.setdefault('fairness_score', 0)
        kpis.setdefault('optimization_score', 0)
        kpis.setdefault('total_cost', 0)
        
        return kpis
    except:
        return {}


def collect_role_performance(output_dir: Path) -> list:
    """職種別パフォーマンス情報を収集"""
    try:
        shortage_role_file = output_dir / "shortage_role_summary.parquet"
        if shortage_role_file.exists():
            df = pd.read_parquet(shortage_role_file)
            return [
                {
                    'role': row.get('role', 'N/A'),
                    'shortage_hours': row.get('lack_h', 0),
                    'excess_hours': row.get('excess_h', 0),
                    'avg_fatigue': 0,  # 疲労度は別ファイルとの結合が必要
                    'total_cost': 0    # コストも別ファイルとの結合が必要
                }
                for _, row in df.iterrows()
            ]
        else:
            return []
    except:
        return []


def collect_monthly_trends(output_dir: Path) -> list:
    """月別トレンド情報を収集"""
    try:
        monthly_role_file = output_dir / "shortage_role_monthly.parquet"
        if monthly_role_file.exists():
            df = pd.read_parquet(monthly_role_file)
            monthly_summary = df.groupby('month').agg({
                'lack_h': 'sum',
                'excess_h': 'sum'
            }).reset_index()
            
            return [
                {
                    'month': row['month'],
                    'shortage_hours': row.get('lack_h', 0),
                    'excess_hours': row.get('excess_h', 0),
                    'leave_days': 0,  # 休暇データは別ファイルから
                    'alerts': 0       # アラート数も別ファイルから
                }
                for _, row in monthly_summary.iterrows()
            ]
        else:
            return []
    except:
        return []


def collect_generated_files(output_dir: Path) -> dict:
    """生成ファイル一覧を収集"""
    try:
        files_by_category = {
            'ヒートマップ': [],
            '不足分析': [],
            '疲労分析': [],
            '公平性分析': [],
            'その他': []
        }
        
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                file_info = f"{file_path.name} ({file_size} bytes)"
                
                if 'heat_' in file_path.name:
                    files_by_category['ヒートマップ'].append(file_info)
                elif 'shortage_' in file_path.name:
                    files_by_category['不足分析'].append(file_info)
                elif 'fatigue_' in file_path.name:
                    files_by_category['疲労分析'].append(file_info)
                elif 'fairness_' in file_path.name:
                    files_by_category['公平性分析'].append(file_info)
                else:
                    files_by_category['その他'].append(file_info)
        
        return files_by_category
    except:
        return {}


def generate_recommendations(kpi_stats: dict, role_performance: list) -> list:
    """KPIと職種別パフォーマンスから推奨事項を生成"""
    recommendations = []
    
    try:
        # 不足時間に基づく推奨
        total_shortage = kpi_stats.get('total_shortage_hours', 0)
        if total_shortage > 100:
            recommendations.append(f"総不足時間が{total_shortage:.1f}時間と高い水準です。追加採用を検討してください。")
        elif total_shortage > 50:
            recommendations.append(f"総不足時間が{total_shortage:.1f}時間です。シフト調整で改善可能です。")
        
        # 過剰時間に基づく推奨
        total_excess = kpi_stats.get('total_excess_hours', 0)
        if total_excess > 50:
            recommendations.append(f"総過剰時間が{total_excess:.1f}時間です。シフト最適化の余地があります。")
        
        # 職種別の推奨
        if role_performance:
            high_shortage_roles = [r for r in role_performance if r.get('shortage_hours', 0) > 20]
            if high_shortage_roles:
                role_names = [r['role'] for r in high_shortage_roles[:3]]
                recommendations.append(f"職種「{', '.join(role_names)}」で不足が顕著です。優先的な対応が必要です。")
        
        # 疲労スコアに基づく推奨
        avg_fatigue = kpi_stats.get('avg_fatigue_score', 0)
        if avg_fatigue > 0.7:
            recommendations.append("平均疲労スコアが高い水準です。勤務間隔と連勤回数の見直しをお勧めします。")
        
        # 公平性スコアに基づく推奨
        fairness_score = kpi_stats.get('fairness_score', 0)
        if fairness_score < 0.5:
            recommendations.append("公平性スコアが低い水準です。スタッフ間の勤務時間バランスの調整をお勧めします。")
        
        return recommendations
    except:
        return ["推奨事項の生成中にエラーが発生しました。"]


def _patch_streamlit_watcher() -> None:
    """Patch Streamlit's module watcher to ignore failing modules."""
    try:
        from streamlit.watcher import local_sources_watcher as _lsw  # type: ignore
    except Exception:
        return

    if not hasattr(_lsw, "extract_paths"):
        return

    if getattr(_lsw.extract_paths, "_patched", False):
        return

    _orig = _lsw.extract_paths

    def _safe_extract_paths(module):
        try:
            return _orig(module)
        except Exception as e:  # pragma: no cover - optional
            logging.getLogger(__name__).debug(
                "streamlit watcher skipped %s due to %s",
                getattr(module, "__name__", repr(module)),
                e,
            )
            return []

    _safe_extract_paths._patched = True  # type: ignore[attr-defined]
    _lsw.extract_paths = _safe_extract_paths


# Call the watcher patch before configuring logging so that any modules
# imported during setup won't trigger errors.
_patch_streamlit_watcher()
# ── ロガー設定 ─────────────────────────────────
configure_logging()
log = logging.getLogger(__name__)

analysis_logger = logging.getLogger('analysis')
analysis_logger.setLevel(logging.INFO)
analysis_logger.propagate = False
try:
    file_handler = logging.FileHandler('analysis_log.log', mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s] - %(message)s')
    file_handler.setFormatter(formatter)
    if not analysis_logger.handlers:
        analysis_logger.addHandler(file_handler)
except Exception as e:
    logging.error(f"\u5206\u6790\u30ed\u30b0\u30d5\u30a1\u30a4\u30eb\u306e\u8a2d\u5b9a\u306b\u5931\u6557\u3057\u307e\u3057\u305f: {e}")


def log_environment_info() -> None:
    """Log basic environment details to help with debugging."""
    import os
    import platform
    import sys

    log.info("Python: %s", sys.version.replace("\n", " "))
    log.info("Platform: %s", platform.platform())
    log.info("Working dir: %s", Path.cwd())
    log.info("Streamlit: %s", st.__version__)
    try:
        import torch

        log.info("PyTorch: %s", torch.__version__)
    except Exception as e:  # pragma: no cover - optional
        log.info("PyTorch not available: %s", e)
    log.debug("Environment PATH: %s", os.getenv("PATH", ""))


log_environment_info()


# ── Utility: log error to terminal and show in Streamlit ──
def log_and_display_error(msg: str, exc: Exception | None) -> None:
    """Log an error and also show it in the Streamlit interface.

    Parameters
    ----------
    msg : str
        User-facing error message.
    exc : Exception | None
        Exception instance, if available. ``None`` is allowed to avoid
        displaying ``NoneType: None`` when an exception object is absent.
    """

    if exc is not None:
        log.error(f"{msg}: {exc}", exc_info=True)
        st.error(f"{msg}: {exc}")
    else:
        log.error(msg)
        st.error(msg)


def log_and_display_error_enhanced(step: str, msg: str, exc: Exception) -> None:
    """Show user friendly error messages with technical details in logs."""
    log.error(f"[{step}] {msg}: {exc}", exc_info=True)

    user_messages = {
        "年月セル読み込み": "年月情報セルの読み込みに失敗しました。セル位置を確認してください。",
        "勤務区分読み込み": "勤務区分シートの読み込みに失敗しました。シート名と形式を確認してください。",
        "時刻変換": "勤務区分の時刻データ変換に失敗しました。開始・終了時刻の形式を確認してください。",
        "シート読み込み": "実績シートの読み込みに失敗しました。シート名と列構造を確認してください。",
        "日付列解析": "日付列の解析に失敗しました。日付の形式を確認してください。",
    }

    user_msg = user_messages.get(step, f"{step}の処理に失敗しました。")
    st.error(f"❌ {user_msg}")
    with st.expander("技術的な詳細情報"):
        st.code(f"エラータイプ: {type(exc).__name__}\nメッセージ: {str(exc)}")


# ── 日本語ラベル辞書は resources/strings_ja.json で管理 ──


def _file_mtime(path: Path) -> float:
    """Return the modification time of a file for cache keys."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0




def load_shortage_meta(data_dir: Path) -> tuple[list[str], list[str]]:
    """Return role and employment lists from ``shortage.meta.json`` if present."""
    roles: list[str] = []
    employments: list[str] = []
    meta_fp = data_dir / "shortage.meta.json"
    if meta_fp.exists():
        try:
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
            roles = meta.get("roles", []) or []
            employments = meta.get("employments", []) or []
        except Exception as e:  # noqa: BLE001
            log.debug("failed to load shortage meta: %s", e)
    return roles, employments


@st.cache_data
def calc_ratio_from_heatmap_simple(df: pd.DataFrame) -> pd.DataFrame:
    """Return shortage ratio DataFrame calculated from heatmap data (simple version)."""
    if df is None or df.empty or "need" not in df.columns:
        return pd.DataFrame()
    date_cols = [c for c in df.columns if _parse_as_date(str(c)) is not None]
    if not date_cols:
        return pd.DataFrame()
    need_series = df["need"].fillna(0)
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=need_series.index,
        columns=date_cols,
    )
    staff_df = df[date_cols].fillna(0)
    ratio_df = (
        ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    )
    return ratio_df


@st.cache_data
def calc_opt_score_from_heatmap(
    df: pd.DataFrame, w_lack: float = 0.6, w_excess: float = 0.4
) -> pd.DataFrame:
    """Return optimization score heatmap from raw heatmap data."""
    if df is None or df.empty or "need" not in df.columns:
        return pd.DataFrame()
    date_cols = [c for c in df.columns if _parse_as_date(str(c)) is not None]
    if not date_cols:
        return pd.DataFrame()
    need_series = df["need"].fillna(0)
    need_df = pd.DataFrame(
        np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
        index=need_series.index,
        columns=date_cols,
    )
    staff_df = df[date_cols].fillna(0)
    lack_ratio = (
        ((need_df - staff_df) / need_df.replace(0, np.nan)).clip(lower=0).fillna(0)
    )
    if "upper" in df.columns:
        upper_series = df["upper"].fillna(0)
        upper_df = pd.DataFrame(
            np.repeat(upper_series.values[:, np.newaxis], len(date_cols), axis=1),
            index=upper_series.index,
            columns=date_cols,
        )
        excess_ratio = (
            ((staff_df - upper_df) / upper_df.replace(0, np.nan))
            .clip(lower=0)
            .fillna(0)
        )
    else:
        excess_ratio = staff_df * 0
    score_df = 1 - (w_lack * lack_ratio + w_excess * excess_ratio)
    return score_df.clip(lower=0, upper=1)


def excel_cell_to_row_col(cell: str) -> tuple[int, int] | None:
    """Convert Excel style cell like 'A1' to 0-based row/column indexes."""
    m = re.match(r"^([A-Za-z]+)(\d+)$", cell.strip())
    if not m:
        return None
    col_txt, row_txt = m.groups()
    col = 0
    for ch in col_txt.upper():
        col = col * 26 + (ord(ch) - 64)
    return int(row_txt) - 1, col - 1


def run_import_wizard() -> None:
    """Show step-by-step wizard for Excel ingest."""
    step = st.session_state.get("wizard_step", 1)
    st.header("📥 Excel Import Wizard")

    if step == 1:
        default_excel = os.getenv("SHIFT_SUITE_DEFAULT_EXCEL")
        if default_excel and not st.session_state.get("wizard_excel_path"):
            try:
                xls = pd.ExcelFile(default_excel)
            except Exception as e:  # noqa: BLE001
                log_and_display_error(
                    "Excel\u30d5\u30a1\u30a4\u30eb\u306e\u81ea\u52d5\u8aad\u307f\u8fbc\u307f\u306b\u5931\u6557\u3057\u307e\u3057\u305f",
                    e,
                )
            else:
                default_path = Path(default_excel)
                st.session_state.wizard_excel_path = str(default_path)
                st.session_state.wizard_file_size = default_path.stat().st_size
                st.session_state.wizard_sheet_names = xls.sheet_names
                st.session_state.work_root_path_str = str(default_path.parent)

        uploaded = st.file_uploader("Excel file", type=["xlsx"], key="wiz_upload")
        if uploaded is not None:
            if st.session_state.get("wizard_file_size") != uploaded.size:
                tmp = tempfile.mkdtemp(prefix="ShiftSuiteWizard_")
                path = Path(tmp) / uploaded.name
                with open(path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.session_state.wizard_excel_path = str(path)
                st.session_state.wizard_file_size = uploaded.size
                st.session_state.work_root_path_str = str(tmp)
                xls = pd.ExcelFile(path)
                st.session_state.wizard_sheet_names = xls.sheet_names
        if st.session_state.wizard_excel_path:
            master = st.selectbox(
                "勤務区分シート", st.session_state.wizard_sheet_names, key="wiz_master"
            )
            opts = [s for s in st.session_state.wizard_sheet_names if s != master]
            st.multiselect("シフト実績シート", opts, key="wiz_shift_sheets")
            if st.button("Next", disabled=not st.session_state.get("wiz_shift_sheets")):
                st.session_state.shift_sheets_multiselect_widget = (
                    st.session_state.wiz_shift_sheets[:]
                )
                st.session_state.candidate_sheet_list_for_ui = (
                    st.session_state.wiz_shift_sheets[:]
                )
                st.session_state.uploaded_files_info = {
                    uploaded.name: {
                        "path": st.session_state.wizard_excel_path,
                        "size": uploaded.size,
                    }
                }
                st.session_state.year_month_cell_input_widget = "D1"
                st.session_state.header_row_input_widget = 1
                st.session_state.wizard_step = 2
                st.rerun()
        return

    if step == 2:
        for sheet in st.session_state.shift_sheets_multiselect_widget:
            st.subheader(sheet)
            ym = st.text_input(
                "年月情報セル位置", value="A1", key=f"ym_{sheet}", help="例: A1"
            )
            hdr = st.number_input(
                "列名ヘッダー行番号", 1, 20, value=1, key=f"hdr_{sheet}"
            )
            st.number_input(
                "データ開始行番号", 1, 200, value=hdr + 1, key=f"data_{sheet}"
            )
            df_prev = pd.read_excel(
                st.session_state.wizard_excel_path,
                sheet_name=sheet,
                header=int(hdr) - 1,
                nrows=10,
            )
            st.dataframe(df_prev, use_container_width=True)
            rc = excel_cell_to_row_col(ym)
            ym_text = "N/A"
            if rc is not None:
                r, c = rc
                try:
                    cell_df = pd.read_excel(
                        st.session_state.wizard_excel_path,
                        sheet_name=sheet,
                        header=None,
                        skiprows=r,
                        nrows=1,
                        usecols=[c],
                        dtype=str,
                    )
                    ym_text = str(cell_df.iloc[0, 0])
                except Exception:
                    pass
            st.caption(f"抽出年月: {ym_text}")
            st.caption(f"認識列名: {df_prev.columns.tolist()}")
        if st.button("Next", key="wiz_next2"):
            first = st.session_state.shift_sheets_multiselect_widget[0]
            st.session_state.year_month_cell_input_widget = st.session_state[
                f"ym_{first}"
            ]
            st.session_state.header_row_input_widget = st.session_state[f"hdr_{first}"]
            st.session_state.wizard_step = 3
            st.rerun()
        return

    if step == 3:
        first = st.session_state.shift_sheets_multiselect_widget[0]
        hdr = st.session_state.get(
            f"hdr_{first}", st.session_state.get("header_row_input_widget", 1)
        )
        df_cols = pd.read_excel(
            st.session_state.wizard_excel_path,
            sheet_name=first,
            header=int(hdr) - 1,
            nrows=1,
        )
        cols = list(df_cols.columns)
        guessed: dict[str, str] = {}
        for c in cols:
            canon = SHEET_COL_ALIAS.get(_normalize(str(c)))
            if canon and canon not in guessed:
                guessed[canon] = c
        st.selectbox(
            "氏名列",
            cols,
            index=cols.index(guessed.get("staff", cols[0])),
            key="map_staff",
        )
        st.selectbox(
            "職種列",
            cols,
            index=cols.index(guessed.get("role", cols[0])),
            key="map_role",
        )
        st.selectbox(
            "雇用形態列",
            cols,
            index=cols.index(guessed.get("employment", cols[0])),
            key="map_emp",
        )
        date_cols = [c for c in cols if re.search(r"\d", str(c))]
        if date_cols:
            st.caption(f"最初の日付列候補: {date_cols[0]}")
        if st.button("Next", key="wiz_next3"):
            st.session_state.wizard_mapping = {
                "staff": st.session_state.map_staff,
                "role": st.session_state.map_role,
                "employment": st.session_state.map_emp,
            }
            st.session_state.wizard_step = 4
            st.rerun()
        return

    if step == 4:
        st.write("### 設定内容確認")
        st.write("実績シート:", st.session_state.shift_sheets_multiselect_widget)
        st.write("年月セル:", st.session_state.year_month_cell_input_widget)
        st.write("ヘッダー行:", st.session_state.header_row_input_widget)
        st.write("列マッピング:", st.session_state.wizard_mapping)
        if st.button("取り込み開始", key="wiz_ingest"):
            try:
                long_df, _, unknown_codes = ingest_excel(
                    Path(st.session_state.wizard_excel_path),
                    shift_sheets=st.session_state.shift_sheets_multiselect_widget,
                    header_row=int(st.session_state.header_row_input_widget) - 1,  # Convert from 1-indexed to 0-indexed
                    slot_minutes=int(st.session_state.slot_input_widget),
                    year_month_cell_location=st.session_state.year_month_cell_input_widget,
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"読み込みに失敗しました: {e}")
                log.error(f"Wizard ingest failed: {e}", exc_info=True)
                return
            st.session_state.analysis_results = {"preview": long_df.head()}
            st.session_state.long_df = long_df
            if not long_df.empty:
                if "role" in long_df.columns:
                    st.session_state.available_roles = (
                        sorted(long_df["role"].astype(str).dropna().unique().tolist())
                    )
                if "employment" in long_df.columns:
                    st.session_state.available_employments = (
                        sorted(long_df["employment"].astype(str).dropna().unique().tolist())
                    )
            if unknown_codes:
                st.warning("未知の勤務コード: " + ", ".join(sorted(unknown_codes)))
            st.success("取り込み完了")
            st.dataframe(long_df.head(), use_container_width=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_data_cached(
    file_path: str,
    *,
    file_mtime: float | None = None,
    is_parquet: bool = False,
    **kwargs,
) -> pd.DataFrame:
    """Load an Excel or Parquet file with caching."""
    p = Path(file_path)
    if not p.exists():
        return pd.DataFrame()

    if is_parquet:
        return pd.read_parquet(p)

    return safe_read_excel(file_path, **kwargs)


@st.cache_data(show_spinner=False, ttl=1800)
def compute_heatmap_ratio_cached(
    heat_df: pd.DataFrame, need_series: pd.Series
) -> pd.DataFrame:
    """Cache expensive ratio calculations for heatmaps."""
    if heat_df.empty or need_series.empty:
        return pd.DataFrame()

    clean_df = heat_df.drop(
        columns=[c for c in SUMMARY5_CONST if c in heat_df.columns], errors="ignore"
    )
    need_series_safe = need_series.replace(0, np.nan)
    return clean_df.div(need_series_safe, axis=0).clip(lower=0, upper=2)


@st.cache_data(show_spinner=False, ttl=1800)
def prepare_heatmap_display_data(df_heat: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Cache heatmap display data preparation."""
    if df_heat.empty:
        return pd.DataFrame()

    if mode == "Ratio":
        need_series = df_heat.get("need", pd.Series())
        return compute_heatmap_ratio_cached(df_heat, need_series)
    else:
        return df_heat.drop(
            columns=[c for c in SUMMARY5_CONST if c in df_heat.columns],
            errors="ignore",
        )


@st.cache_data(show_spinner=False, ttl=1800)
def optimize_large_heatmap_display(
    df: pd.DataFrame, max_cells: int = 10000
) -> pd.DataFrame:
    """Optimize large heatmap display by intelligent sampling."""
    if df.empty or df.shape[0] * df.shape[1] <= max_cells:
        return df

    sample_step_rows = max(1, len(df) // 100)
    sample_step_cols = max(1, len(df.columns) // 50)
    return df.iloc[::sample_step_rows, ::sample_step_cols]


@st.cache_data(show_spinner=False, ttl=1800)
def load_all_heatmap_files(data_dir: Path) -> dict:
    """Load all available heatmap parquet files dynamically."""
    heatmap_data: dict[str, pd.DataFrame] = {}

    base_files = {"heat_all": "heat_ALL.parquet"}

    for key, filename in base_files.items():
        fp = data_dir / filename
        if fp.exists():
            try:
                heatmap_data[key] = pd.read_parquet(fp)
                log.info(
                    "'%s'を読み込み、heatmap_data['%s']に格納しました。", filename, key
                )
            except Exception as e:  # noqa: BLE001
                log.warning("%s の読み込みに失敗しました: %s", filename, e)

    for pattern in ["heat_role_*.parquet", "heat_emp_*.parquet"]:
        for fp in data_dir.glob(pattern):
            try:
                if pattern.startswith("heat_role_"):
                    key = f"heat_role_{fp.stem.replace('heat_role_', '')}"
                else:
                    key = f"heat_emp_{fp.stem.replace('heat_emp_', '')}"
                heatmap_data[key] = pd.read_parquet(fp)
                log.info(
                    "'%s'を読み込み、heatmap_data['%s']に格納しました。", fp.name, key
                )
            except Exception as e:  # noqa: BLE001
                log.warning("%s の読み込みに失敗しました: %s", fp.name, e)

    return heatmap_data


def load_and_sum_heatmaps(data_dir: Path, keys: list[str]) -> pd.DataFrame:
    """Load multiple heatmap files and return their aggregated sum."""
    dfs = []
    for key in keys:
        df = st.session_state.display_data.get(key)
        if df is None:
            fp = data_dir / f"{key}.parquet"
            if fp.exists():
                try:
                    df = pd.read_parquet(fp)
                    st.session_state.display_data[key] = df
                except Exception as e:  # noqa: BLE001
                    log.warning("%s の読み込みに失敗しました: %s", fp.name, e)
                    df = None
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()

    total = dfs[0].copy()
    for df in dfs[1:]:
        total = total.add(df, fill_value=0)

    if {"need", "staff"}.issubset(total.columns):
        total["lack"] = (total["need"] - total["staff"]).clip(lower=0)
    if {"staff", "upper"}.issubset(total.columns):
        total["excess"] = (total["staff"] - total["upper"]).clip(lower=0)
    return total


def update_display_data_with_heatmaps(out_dir: Path) -> None:
    """Update ``display_data`` including dynamically loaded heatmap files."""
    log.info(f"表示用データの更新を開始します。ディレクトリ: {out_dir}")

    st.session_state.display_data = {}

    files_to_load = {
        "shortage_role": "shortage_role_summary.parquet",
        "shortage_emp": "shortage_employment_summary.parquet",
        "shortage_time": "shortage_time.parquet",
        "excess_time": "excess_time.parquet",
        "shortage_ratio": "shortage_ratio.parquet",
        "excess_ratio": "excess_ratio.parquet",
        "shortage_freq": "shortage_freq.parquet",
        "excess_freq": "excess_freq.parquet",
        "shortage_leave": "shortage_leave.parquet",
        "fatigue_score": "fatigue_score.parquet",
        "fairness_before": "fairness_before.parquet",
        "fairness_after": "fairness_after.parquet",
        "forecast": "forecast.parquet",
        "hire_plan": "hire_plan.parquet",
        "optimal_hire_plan": "optimal_hire_plan.parquet",
        "cost_benefit": "cost_benefit.parquet",
        "daily_cost": "daily_cost.parquet",
        "staff_stats": "staff_stats.parquet",
        "stats_alerts": "stats_alerts.parquet",
        "demand_series": "demand_series.csv",
    }

    initial_loaded = 0
    for key, filename in files_to_load.items():
        fp = out_dir / filename
        if fp.exists():
            try:
                if filename.endswith(".csv"):
                    st.session_state.display_data[key] = pd.read_csv(fp)
                else:
                    st.session_state.display_data[key] = pd.read_parquet(fp)
                initial_loaded += 1
                log.info(
                    "'%s'を読み込み、display_data['%s']に格納しました。", filename, key
                )
            except Exception as e:  # noqa: BLE001
                log.warning("%s の読み込みに失敗しました: %s", filename, e)
        else:
            log.debug(f"ファイルが存在しません: {fp}")

    # --- ヒートマップと派生データの事前計算を追加 ---

    # 1. 全てのヒートマップを一括で読み込む
    heatmap_data = load_all_heatmap_files(out_dir)
    st.session_state.display_data.update(heatmap_data)

    # 2. メタデータ（職種・雇用形態リスト）を読み込む
    roles, employments = load_shortage_meta(out_dir)
    st.session_state.available_roles = roles
    st.session_state.available_employments = employments

    # 3. 読み込んだ各ヒートマップから派生データを計算して保存
    for key, df_heat in heatmap_data.items():
        if not isinstance(df_heat, pd.DataFrame) or df_heat.empty:
            continue

        # 不足率ヒートマップ
        ratio_key = key.replace("heat_", "ratio_")
        st.session_state.display_data[ratio_key] = calc_ratio_from_heatmap_simple(df_heat)

        # 最適化スコアヒートマップ
        score_key = key.replace("heat_", "score_")
        st.session_state.display_data[score_key] = calc_opt_score_from_heatmap(df_heat)

        # 最適化分析タブ用のデータ (Surplus, Margin)
        date_cols = [c for c in df_heat.columns if _parse_as_date(str(c)) is not None]
        if not date_cols:
            continue

        staff_df = df_heat[date_cols].fillna(0)
        need_df = pd.DataFrame(
            np.repeat(df_heat["need"].values[:, np.newaxis], len(date_cols), axis=1),
            index=df_heat.index,
            columns=date_cols,
        )
        upper_df = pd.DataFrame(
            np.repeat(df_heat["upper"].values[:, np.newaxis], len(date_cols), axis=1),
            index=df_heat.index,
            columns=date_cols,
        )

        surplus_key = key.replace("heat_", "surplus_")
        st.session_state.display_data[surplus_key] = (staff_df - need_df).clip(lower=0).fillna(0).astype(int)

        margin_key = key.replace("heat_", "margin_")
        st.session_state.display_data[margin_key] = (upper_df - staff_df).clip(lower=0).fillna(0).astype(int)

    loaded_count = len(st.session_state.display_data)
    log.info(
        "display_data更新完了: %d個のデータをメモリに読み込みました。", loaded_count
    )


@st.cache_data(show_spinner=False, ttl=900)
def get_optimized_display_data(
    df_heat: pd.DataFrame, mode: str, max_display_cells: int = 15000
) -> pd.DataFrame:
    """Get optimized display data with intelligent sampling for large datasets."""
    if df_heat.empty:
        return pd.DataFrame()

    prepared_data = prepare_heatmap_display_data(df_heat, mode)

    if prepared_data.shape[0] * prepared_data.shape[1] > max_display_cells:
        return optimize_large_heatmap_display(prepared_data, max_display_cells)

    return prepared_data


@st.cache_data(show_spinner=False, ttl=600)
def create_progress_indicator():
    """Create reusable progress indicator components."""
    return st.empty(), st.empty()


@st.cache_data(show_spinner=False, ttl=3600)
def generate_heatmap_figure(df_heat, mode, scope_info, max_display_cells=15000):
    """Generate and cache heatmap figure."""
    if not isinstance(df_heat, pd.DataFrame) or df_heat.empty:
        return px.imshow(pd.DataFrame(), title=_("Data not available or empty"))

    prepared_data = prepare_heatmap_display_data(df_heat, mode)

    if prepared_data.shape[0] * prepared_data.shape[1] > max_display_cells:
        display_df = optimize_large_heatmap_display(prepared_data, max_display_cells)
        st.info("大きなデータセットのため、表示を最適化しています...")
    else:
        display_df = prepared_data

    color_scale = "RdBu_r" if mode == "Ratio" else "Blues"
    title = f"{scope_info} - {_('Heatmap') if mode != 'Ratio' else _('Ratio (staff ÷ need)')}"

    fig = px.imshow(
        display_df,
        aspect="auto",
        color_continuous_scale=color_scale,
        title=title,
        labels={"x": _("Date"), "y": _("Time"), "color": _(mode)},
    )
    fig.update_xaxes(
        tickvals=list(range(len(display_df.columns))),
        ticktext=[date_with_weekday(c) for c in display_df.columns],
    )
    return fig


st.set_page_config(
    page_title="Shift-Suite", layout="wide", initial_sidebar_state="expanded"
)
st.title("🗂️ Shift-Suite : 勤務シフト分析ツール")

master_sheet_keyword = "勤務区分"

# --- セッションステートの初期化 (一度だけ実行) ---
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.analysis_done = False
    st.session_state.work_root_path_str = None
    st.session_state.out_dir_path_str = None
    st.session_state.current_step_for_progress = 0

    # データ格納用の辞書を確実に初期化
    st.session_state.display_data = {}
    st.session_state.analysis_results = {}
    st.session_state.analysis_status = {}
    st.session_state.leave_analysis_results = {}

    # パフォーマンス関連の初期化を確実に実行
    if "heatmap_cache_key" not in st.session_state:
        st.session_state.heatmap_cache_key = None

    if "performance_mode" not in st.session_state:
        st.session_state.performance_mode = "auto"

    log.info("アプリケーションを初期化しました。全てのデータ格納用辞書を初期化。")

    today_val = datetime.date.today()

    # サイドバーのウィジェットのキーとデフォルト値をセッションステートに初期設定
    st.session_state.slot_input_widget = 30
    st.session_state.header_row_input_widget = 1
    st.session_state.year_month_cell_input_widget = "D1"
    st.session_state.candidate_sheet_list_for_ui = []
    st.session_state.shift_sheets_multiselect_widget = []
    st.session_state._force_update_multiselect_flag = False

    st.session_state.need_ref_start_date_widget = today_val - datetime.timedelta(
        days=59
    )  # 初期デフォルト
    st.session_state.need_ref_end_date_widget = today_val - datetime.timedelta(
        days=1
    )  # 初期デフォルト
    st.session_state._force_update_need_ref_dates_flag = False
    st.session_state._intended_need_ref_start_date = None
    st.session_state._intended_need_ref_end_date = None

    st.session_state.need_stat_method_options_widget = [
        "10パーセンタイル",
        "25パーセンタイル",
        "中央値",
        "平均値",
    ]
    st.session_state.need_stat_method_widget = "中央値"
    st.session_state.need_remove_outliers_widget = True
    st.session_state.need_adjustment_factor_widget = 1.0

    st.session_state.min_method_for_upper_options_widget = ["mean-1s", "p25", "mode"]
    st.session_state.min_method_for_upper_widget = "p25"
    st.session_state.max_method_for_upper_options_widget = ["mean+1s", "p75"]
    st.session_state.max_method_for_upper_widget = "p75"

    #  休暇分析を含む追加モジュールリスト
    st.session_state.available_ext_opts_widget = [
        "Stats",
        "Anomaly",
        "Fatigue",
        "Cluster",
        "Skill",
        "Fairness",
        "Rest Time Analysis",
        "Work Pattern Analysis",
        "Attendance Analysis",
        "Combined Score",
        "Low Staff Load",
        _("Leave Analysis"),
        "Need forecast",
        "RL roster (PPO)",
        "RL roster (model)",
        "Hire plan",
        "Cost / Benefit",
        "最適採用計画",
    ]
    # デフォルトで休暇分析も選択状態にするかはお好みで
    st.session_state.ext_opts_multiselect_widget = (
        st.session_state.available_ext_opts_widget[:]
    )

    st.session_state.save_mode_selectbox_options_widget = [
        _("ZIP Download"),
        _("Save to folder"),
    ]
    st.session_state.save_mode_selectbox_widget = _("ZIP Download")

    st.session_state.std_work_hours_widget = 160
    st.session_state.safety_factor_widget = 0.0
    st.session_state.target_coverage_widget = 0.95
    st.session_state.wage_direct_widget = 1500
    st.session_state.wage_temp_widget = 2200
    st.session_state.hiring_cost_once_widget = 180000
    st.session_state.penalty_per_lack_widget = 4000
    st.session_state.forecast_period_widget = 30

    #  休暇分析用パラメータの初期化
    st.session_state.leave_analysis_target_types_widget = [
        LEAVE_TYPE_REQUESTED,
        LEAVE_TYPE_PAID,
        LEAVE_TYPE_OTHER,
    ]  # デフォルトで両方
    st.session_state.leave_concentration_threshold_widget = (
        3  # 希望休集中度閾値のデフォルト
    )

    #  休暇分析結果格納用
    st.session_state.leave_analysis_results = {}

    st.session_state.rest_time_results = None
    st.session_state.rest_time_monthly = None
    st.session_state.work_pattern_results = None
    st.session_state.work_pattern_monthly = None
    st.session_state.attendance_results = None
    st.session_state.combined_score_results = None
    st.session_state.low_staff_load_results = None
    st.session_state.uploaded_files_info = {}
    st.session_state.file_options = {}
    st.session_state.analysis_results = {}
    st.session_state.analysis_status = {}
    st.session_state.wizard_step = 1
    st.session_state.wizard_excel_path = None
    st.session_state.wizard_sheet_names = []
    st.session_state.wizard_shift_sheets = []
    st.session_state.wizard_mapping = {}
    st.session_state.long_df = pd.DataFrame()
    log.info("セッションステートを初期化しました。")

run_import_wizard()

# --- サイドバーのUI要素 ---
with st.sidebar:
    st.header("🛠️ 解析設定")

    with st.expander("基本設定", expanded=True):
        st.number_input(
            _("Slot (min)"),
            5,
            120,
            key="slot_input_widget",
            help="分析の時間間隔（分）",
        )

    with st.expander("📄 シート選択とヘッダー", expanded=True):
        if st.session_state.get("wizard_step", 1) <= 2:
            st.info("Use the Excel Import Wizard to select sheets")
        else:
            if st.session_state.get("_force_update_multiselect_flag", False):
                new_options = st.session_state.candidate_sheet_list_for_ui
                current_selection = st.session_state.get(
                    "shift_sheets_multiselect_widget", []
                )
                valid_selection = [s for s in current_selection if s in new_options]
                if not valid_selection and new_options:
                    st.session_state.shift_sheets_multiselect_widget = new_options[:]
                elif valid_selection:
                    st.session_state.shift_sheets_multiselect_widget = valid_selection
                else:
                    st.session_state.shift_sheets_multiselect_widget = []
                st.session_state._force_update_multiselect_flag = False

            st.multiselect(
                _("Select shift sheets to analyze (multiple)"),
                options=st.session_state.candidate_sheet_list_for_ui,
                default=st.session_state.shift_sheets_multiselect_widget,
                key="shift_sheets_multiselect_widget",
                help="解析対象とするシートを選択します。",
            )
            # Force reset session state if it has invalid value
            if st.session_state.get("header_row_input_widget", 1) < 1:
                st.session_state.header_row_input_widget = 1
            st.number_input(
                _("Header row number (1-indexed)"),
                1,
                20,
                value=1,
                key="header_row_input_widget",
                help="スクリーンショット例の 'No' など列名がある行番号",
            )
            st.text_input(
                _("Year-Month cell location"),
                key="year_month_cell_input_widget",
                help="年月情報が記載されているセル位置 (例: A1)",
            )

    st.subheader("分析基準設定")
    need_calc_method = st.radio(
        _("最適ゾーンの下限値(Need)の算出方法"),
        options=[
            _("過去の実績から統計的に推定する"),
            _("人員配置基準に基づき設定する"),
        ],
        key="need_calc_method_widget",
        horizontal=True,
    )

    if need_calc_method == _("過去の実績から統計的に推定する"):
        st.date_input(_("参照期間 開始日"), key="need_ref_start_date_widget")
        st.date_input(_("参照期間 終了日"), key="need_ref_end_date_widget")
        st.selectbox(
            _("統計的指標"),
            options=["中央値", "平均値", "25パーセンタイル", "10パーセンタイル"],
            key="need_stat_method_widget",
        )
        st.checkbox(
            _("外れ値を除去してNeedを算出"),
            value=True,
            key="need_remove_outliers_widget",
        )
        st.slider(
            "必要人数 調整係数",
            min_value=0.1,
            max_value=1.0,
            value=st.session_state.get("need_adjustment_factor_widget", 1.0),
            step=0.05,
            key="need_adjustment_factor_widget",
        )
    else:
        st.number_input(
            _("分析対象の平均利用者数"), min_value=0, key="avg_users_widget"
        )
        st.write("職種ごとの最低必要人数（配置基準）を入力してください:")
        if "long_df" in st.session_state and not st.session_state.long_df.empty:
            roles = sorted(st.session_state.long_df["role"].unique())
            manual_need_values = {}
            for role in roles:
                manual_need_values[role] = st.number_input(
                    f"{role}",
                    min_value=0,
                    key=f"manual_need_{role}",
                )
            st.session_state.manual_need_values_widget = manual_need_values

    st.divider()
    upper_calc_method = st.selectbox(
        _("最適ゾーンの上限値(Upper)の算出方法"),
        options=[
            _("下限値(Need) + 固定値"),
            _("下限値(Need) * 固定係数"),
            _("過去実績のパーセンタイル"),
        ],
        key="upper_calc_method_widget",
    )

    if upper_calc_method == _("下限値(Need) + 固定値"):
        st.number_input(
            _("加算する人数"), min_value=0, step=1, key="upper_param_fixed_val"
        )
    elif upper_calc_method == _("下限値(Need) * 固定係数"):
        st.slider(
            _("乗算する係数"),
            min_value=1.0,
            max_value=2.0,
            value=1.2,
            step=0.05,
            key="upper_param_factor_val",
        )
    else:
        st.selectbox(
            _("パーセンタイル"),
            options=[75, 80, 85, 90, 95],
            index=3,
            key="upper_param_percentile_val",
        )

    st.divider()
    with st.expander("追加分析モジュール"):
        if "ext_opts_multiselect_widget" not in st.session_state:
            st.session_state.ext_opts_multiselect_widget = st.session_state.get(
                "available_ext_opts_widget", []
            )

        st.multiselect(
            _("Extra modules"),
            st.session_state.available_ext_opts_widget,
            default=st.session_state.ext_opts_multiselect_widget,
            key="ext_opts_multiselect_widget",
            help="実行する追加の分析モジュールを選択します。",
        )

        if _("Leave Analysis") in st.session_state.ext_opts_multiselect_widget:
            # Nested expanders trigger StreamlitAPIException, so use a heading
            # instead of an inner st.expander here.
            st.markdown("### 📊 " + _("Leave Analysis") + " 設定")
            st.multiselect(
                "分析対象の休暇タイプ",
                options=[
                    LEAVE_TYPE_REQUESTED,
                    LEAVE_TYPE_PAID,
                    LEAVE_TYPE_OTHER,
                ],
                key="leave_analysis_target_types_widget",
                help="分析する休暇の種類を選択します。",
            )
            if (
                LEAVE_TYPE_REQUESTED
                in st.session_state.leave_analysis_target_types_widget
            ):
                st.number_input(
                    "希望休 集中度判定閾値 (人)",
                    min_value=1,
                    step=1,
                    key="leave_concentration_threshold_widget",
                    help="同日にこの人数以上の希望休があった場合に『集中』とみなします。",
                )

    current_save_mode_idx_val = 0
    try:
        current_save_mode_idx_val = (
            st.session_state.save_mode_selectbox_options_widget.index(
                st.session_state.save_mode_selectbox_widget
            )
        )
    except (ValueError, AttributeError):
        current_save_mode_idx_val = 0
    st.selectbox(
        _("Save method"),
        options=st.session_state.save_mode_selectbox_options_widget,
        index=current_save_mode_idx_val,
        key="save_mode_selectbox_widget",
        help="解析結果の保存方法を選択します。",
    )

    with st.expander("疲労スコア重み設定"):
        st.slider(
            "① 勤務開始時刻ランダム性",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_start_var_widget",
        )
        st.slider(
            "② 業務多様性",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_diversity_widget",
        )
        st.slider(
            "③ 労働時間のランダム性",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_worktime_var_widget",
        )
        st.slider(
            "④ 夜勤間の休息不足",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_short_rest_widget",
        )
        st.slider(
            "⑤ 連勤日数",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_consecutive_widget",
        )
        st.slider(
            "⑥ 夜勤比率",
            0.0,
            2.0,
            value=1.0,
            step=0.1,
            key="weight_night_ratio_widget",
        )

    with st.expander(_("Cost & Hire Parameters")):
        st.subheader("人件費計算 設定")
        cost_by_key = st.radio(
            _("Unit Price Standard"),
            options=["role", "employment", "staff"],
            captions=[_("Role"), _("Employment"), _("Staff")],
            index=0,
            horizontal=True,
            key="cost_by_widget",
        )
        if "long_df" in st.session_state and not st.session_state.long_df.empty:
            if cost_by_key in st.session_state.long_df.columns:
                unique_keys = sorted(st.session_state.long_df[cost_by_key].unique())
                if "wage_config" not in st.session_state:
                    st.session_state.wage_config = {}
                for key in unique_keys:
                    wage_key = f"wage_{cost_by_key}_{key}"
                    if wage_key not in st.session_state:
                        st.session_state[wage_key] = st.session_state.get(
                            "default_wage", 1000
                        )
                    wage_val = st.number_input(
                        f"{_('Hourly Wage')}: {key}",
                        value=st.session_state[wage_key],
                        key=wage_key,
                    )
                    st.session_state.wage_config[key] = wage_val
        st.divider()
        st.subheader("採用・コスト試算 設定")
        st.number_input(
            _("Standard work hours (h/month)"), 100, 300, key="std_work_hours_widget"
        )
        st.slider(
            _("Safety factor (shortage h multiplier)"),
            0.00,
            2.00,
            key="safety_factor_widget",
            help="不足時間に乗算する倍率 (例: 1.10 は 10% 上乗せ)",
        )
        st.slider(_("Target coverage rate"), 0.50, 1.00, key="target_coverage_widget")
        st.number_input(
            _("Direct employee labor cost (¥/h)"), 500, 10000, key="wage_direct_widget"
        )
        st.number_input(
            _("Temporary staff labor cost (¥/h)"), 800, 12000, key="wage_temp_widget"
        )
        st.number_input(
            _("One-time hiring cost (¥/person)"),
            0,
            1000000,
            key="hiring_cost_once_widget",
        )
        st.number_input(
            _("Penalty for shortage (¥/h)"), 0, 20000, key="penalty_per_lack_widget"
        )

    with st.expander("上級設定"):
        st.number_input(
            _("Forecast days"),
            1,
            365,
            key="forecast_period_widget",
            help="Need forecast モジュールで先読みする日数",
        )

    st.markdown("---")
    st.subheader("🚨 緊急対処")
    if st.button("🔄 全データリセット", type="secondary"):
        for key in list(st.session_state.keys()):
            if key not in ["app_initialized"]:
                del st.session_state[key]
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.rerun()

    if st.button("📊 display_data強制再読み込み", type="secondary"):
        st.session_state.display_data = {}
        st.rerun()

# --- メインコンテンツエリア ---
holiday_file_global_uploaded = st.file_uploader(
    _("Global holiday file (CSV or JSON)"),
    type=["csv", "json"],
    key="holiday_file_global_widget",
    help="全国共通の祝日など (YYYY-MM-DD)",
)
holiday_file_local_uploaded = st.file_uploader(
    _("Local holiday file (CSV or JSON)"),
    type=["csv", "json"],
    key="holiday_file_local_widget",
    help="施設固有の休業日 (YYYY-MM-DD)",
)

run_button_disabled_status = (
    not st.session_state.uploaded_files_info
    or not st.session_state.get("shift_sheets_multiselect_widget", [])
)
run_button_clicked = st.button(
    _("Run Analysis"),
    key="run_analysis_button_final_trigger",
    use_container_width=True,
    type="primary",
    disabled=run_button_disabled_status,
)

if (
    st.session_state.get("shift_sheets_multiselect_widget")
    and st.session_state.uploaded_files_info
):
    try:
        first_file_path = next(iter(st.session_state.uploaded_files_info.values()))[
            "path"
        ]
        preview_df_sidebar = pd.read_excel(
            first_file_path,
            sheet_name=st.session_state.shift_sheets_multiselect_widget[0],
            nrows=5,
            header=None,
        )
        st.caption(
            _("Preview")
            + f": {st.session_state.shift_sheets_multiselect_widget[0]} (first 5 rows)"
        )
        st.dataframe(preview_df_sidebar.astype(str), use_container_width=True)
    except Exception as e_prev:
        st.warning(_("Error during preview display") + f": {e_prev}")

# ─────────────────────────────  app.py  (Part 2 / 3)  ──────────────────────────
if run_button_clicked:
    # 完全なリセット処理
    st.session_state.analysis_done = False
    st.session_state.analysis_results = {}
    st.session_state.analysis_status = {}

    # 表示用データも完全にクリア
    st.session_state.display_data = {}

    # 休暇分析結果もクリア
    st.session_state.leave_analysis_results = {}

    # その他の分析結果もクリア
    st.session_state.rest_time_results = None
    st.session_state.rest_time_monthly = None
    st.session_state.work_pattern_results = None
    st.session_state.work_pattern_monthly = None
    st.session_state.attendance_results = None
    st.session_state.combined_score_results = None
    st.session_state.low_staff_load_results = None

    # 1. 比較したい分析シナリオを定義
    analysis_scenarios = {
        "median_based": {"name": "中央値ベース", "need_stat_method": "中央値"},
        "mean_based": {"name": "平均値ベース", "need_stat_method": "平均値"},
        "p25_based": {"name": "25パーセンタイルベース", "need_stat_method": "25パーセンタイル"},
    }

    # キャッシュクリア
    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        log.info("キャッシュをクリアしました。")
    except Exception as e:
        log.warning(f"キャッシュクリアに失敗: {e}")

    log.info("新しい分析を開始します。すべてのセッションデータをクリアしました。")

    holiday_dates_global_for_run = None
    holiday_dates_local_for_run = None

    def _read_holiday_upload(uploaded_file: IO[str | bytes]) -> list[dt.date]:
        """Return dates from an uploaded CSV or JSON file."""
        if uploaded_file.name.lower().endswith(".json"):
            import json

            return [pd.to_datetime(d).date() for d in json.load(uploaded_file)]
        df_h = pd.read_csv(uploaded_file, header=None)
        return [pd.to_datetime(x).date() for x in df_h.iloc[:, 0].dropna().unique()]

    if holiday_file_global_uploaded is not None:
        try:
            holiday_dates_global_for_run = _read_holiday_upload(
                holiday_file_global_uploaded
            )
        except Exception as e_hread:
            st.warning(_("Holiday file parse error") + f": {e_hread}")
            log.warning(f"Holiday file parse error: {e_hread}")

    if holiday_file_local_uploaded is not None:
        try:
            holiday_dates_local_for_run = _read_holiday_upload(
                holiday_file_local_uploaded
            )
        except Exception as e_hread:
            st.warning(_("Holiday file parse error") + f": {e_hread}")
            log.warning(f"Holiday file parse error: {e_hread}")

    for file_name, file_info in st.session_state.uploaded_files_info.items():
        st.session_state.current_step_for_progress = 0

        excel_path_to_use = Path(file_info["path"])
        if (
            st.session_state.work_root_path_str is None
            or not excel_path_to_use.exists()
        ):
            log_and_display_error(
                "Excelファイルが正しくアップロードされていません。ファイルを再アップロードしてください。",
                FileNotFoundError(excel_path_to_use),
            )
            st.stop()

        work_root_exec = excel_path_to_use.parent
        st.session_state.work_root_path_str = str(work_root_exec)
        st.session_state.out_dir_path_str = str(work_root_exec / "out")
        out_dir_exec = Path(st.session_state.out_dir_path_str)
        out_dir_exec.mkdir(parents=True, exist_ok=True)
        log.info(f"解析出力ディレクトリ: {out_dir_exec} (file: {file_name})")
        base_work_dir = Path(st.session_state.work_root_path_str)

        # --- 実行時のUIの値をセッションステートから取得 ---
        param_selected_sheets = st.session_state.shift_sheets_multiselect_widget
        param_header_row = st.session_state.header_row_input_widget - 1  # Convert from 1-indexed to 0-indexed
        param_year_month_cell = st.session_state.year_month_cell_input_widget
        param_slot = st.session_state.slot_input_widget
        param_need_calc_method = st.session_state.need_calc_method_widget
        param_need_ref_start = st.session_state.get("need_ref_start_date_widget")
        param_need_ref_end = st.session_state.get("need_ref_end_date_widget")
        param_need_stat_method = st.session_state.get("need_stat_method_widget")
        param_need_manual = st.session_state.get("manual_need_values_widget")
        param_need_remove_outliers = st.session_state.get(
            "need_remove_outliers_widget",
            True,
        )
        param_upper_method = st.session_state.upper_calc_method_widget
        param_upper_param = {
            "fixed_value": st.session_state.get("upper_param_fixed_val"),
            "factor": st.session_state.get("upper_param_factor_val"),
            "percentile": st.session_state.get("upper_param_percentile_val"),
        }
        param_ext_opts = st.session_state.ext_opts_multiselect_widget
        param_save_mode = st.session_state.save_mode_selectbox_widget
        param_std_work_hours = st.session_state.std_work_hours_widget
        param_safety_factor = st.session_state.safety_factor_widget
        param_target_coverage = st.session_state.target_coverage_widget
        param_wage_direct = st.session_state.wage_direct_widget
        param_wage_temp = st.session_state.wage_temp_widget
        param_hiring_cost = st.session_state.hiring_cost_once_widget
        param_penalty_lack = st.session_state.penalty_per_lack_widget
        param_forecast_period = st.session_state.forecast_period_widget

        #  休暇分析用パラメータの取得
        param_leave_target_types = st.session_state.leave_analysis_target_types_widget
        param_leave_concentration_threshold = (
            st.session_state.leave_concentration_threshold_widget
        )

        #  セッションステート内の前回結果をクリア
        st.session_state.leave_analysis_results = {}
        # --- UI値取得ここまで ---

        st.session_state.rest_time_results = None
        st.session_state.work_pattern_results = None
        st.session_state.attendance_results = None
        st.session_state.combined_score_results = None
        st.session_state.low_staff_load_results = None
        progress_status = st.empty()
        progress_text_area = st.empty()
        progress_bar_val = st.progress(0)
        total_steps_exec_run = 3 + len(param_ext_opts)

        def update_progress_exec_run(step_name_key_exec: str):
            st.session_state.current_step_for_progress += 1
            progress_percentage_exec_run = int(
                (st.session_state.current_step_for_progress / total_steps_exec_run)
                * 100
            )
            progress_percentage_exec_run = min(progress_percentage_exec_run, 100)
            try:
                progress_bar_val.progress(progress_percentage_exec_run)
                progress_text_area.info(
                    f"⚙️ {st.session_state.current_step_for_progress}/{total_steps_exec_run} - {_(step_name_key_exec)}"
                )
                progress_status.write(_(step_name_key_exec))
            except Exception as e_prog_exec_run:
                log.warning(f"進捗表示の更新中にエラー: {e_prog_exec_run}")

        st.markdown("---")
        st.header("2. 解析処理")
        try:
            if param_selected_sheets and excel_path_to_use:
                update_progress_exec_run("File Preview (first 8 rows)")
                st.subheader(_("File Preview (first 8 rows)"))
                try:
                    preview_df_exec_run = pd.read_excel(
                        excel_path_to_use,
                        sheet_name=param_selected_sheets[0],
                        header=None,
                        nrows=8,
                    )
                    st.dataframe(
                        preview_df_exec_run.astype(str), use_container_width=True
                    )
                except Exception as e_prev_exec_run:
                    st.warning(
                        _("Error during preview display") + f": {e_prev_exec_run}"
                    )
                    log.warning(
                        f"プレビュー表示エラー: {e_prev_exec_run}", exc_info=True
                    )
            else:
                st.warning(
                    "プレビューを表示するシートが選択されていないか、ファイルパスが無効です。"
                )

            long_df = None
            try:
                update_progress_exec_run("Ingest: Reading Excel data...")
                long_df, wt_df, unknown_codes = ingest_excel(
                    excel_path_to_use,
                    shift_sheets=param_selected_sheets,
                    header_row=param_header_row,
                    slot_minutes=param_slot,
                    year_month_cell_location=param_year_month_cell,
                )
                intermediate_parquet_path = work_root_exec / "intermediate_data.parquet"
                long_df.to_parquet(intermediate_parquet_path)
                if wt_df is not None and not wt_df.empty:
                    wt_df.to_parquet(work_root_exec / "work_patterns.parquet", index=False)
                    log.info("勤務区分情報を work_patterns.parquet に保存しました。")
                st.session_state["intermediate_parquet_path"] = str(intermediate_parquet_path)
                st.session_state.analysis_status["ingest"] = "success"
                log.info(
                    f"Ingest完了. long_df shape: {long_df.shape}, wt_df shape: {wt_df.shape if wt_df is not None else 'N/A'}"
                )
                if unknown_codes:
                    st.warning("未知の勤務コード: " + ", ".join(sorted(unknown_codes)))
                    log.warning(
                        f"Unknown shift codes encountered: {sorted(unknown_codes)}"
                    )
                st.success("✅ Excelデータ読み込み完了")
                st.session_state.long_df = long_df
                if not long_df.empty:
                    if "role" in long_df.columns:
                        st.session_state.available_roles = (
                            sorted(long_df["role"].astype(str).dropna().unique().tolist())
                        )
                    if "employment" in long_df.columns:
                        st.session_state.available_employments = (
                            sorted(long_df["employment"].astype(str).dropna().unique().tolist())
                        )
            except Exception as e:
                st.session_state.analysis_status["ingest"] = "failure"
                log_and_display_error(
                    "Excelデータの読み込み中にエラーが発生しました", e
                )

            base_out_dir = Path(st.session_state.work_root_path_str) / "out"
            base_out_dir.mkdir(parents=True, exist_ok=True)

            # --- 共通分析をシナリオループの前に実行 ---
            try:
                if "Fairness" in param_ext_opts:
                    run_fairness(long_df, base_out_dir)
                    fairness_xlsx = base_out_dir / "fairness_after.xlsx"
                    if fairness_xlsx.exists():
                        try:
                            fairness_df = pd.read_excel(fairness_xlsx)
                            fairness_df.to_parquet(base_out_dir / "fairness_after.parquet")
                        except Exception as e_conv:
                            log.warning(f"fairness_after.xlsx conversion failed: {e_conv}")
                if "Fatigue" in param_ext_opts:
                    fatigue_weights = {
                        "start_var": st.session_state.get("weight_start_var_widget", 1.0),
                        "diversity": st.session_state.get("weight_diversity_widget", 1.0),
                        "worktime_var": st.session_state.get("weight_worktime_var_widget", 1.0),
                        "short_rest": st.session_state.get("weight_short_rest_widget", 1.0),
                        "consecutive": st.session_state.get("weight_consecutive_widget", 1.0),
                        "night_ratio": st.session_state.get("weight_night_ratio_widget", 1.0),
                    }
                    train_fatigue(long_df, base_out_dir, weights=fatigue_weights)
                if _("Leave Analysis") in param_ext_opts:
                    daily_leave_df = leave_analyzer.get_daily_leave_counts(long_df, target_leave_types=param_leave_target_types)
                    if not daily_leave_df.empty:
                        staff_balance = (
                            long_df[long_df["parsed_slots_count"] > 0]
                            .assign(date=lambda df: pd.to_datetime(df["ds"]).dt.normalize())
                            .groupby("date")["staff"]
                            .nunique()
                            .reset_index(name="total_staff")
                        )
                        leave_counts = (
                            leave_analyzer.summarize_leave_by_day_count(daily_leave_df.copy(), period="date")
                            .groupby("date")["total_leave_days"]
                            .sum()
                            .reset_index(name="leave_applicants_count")
                        )
                        staff_balance = staff_balance.merge(leave_counts, on="date", how="left")
                        staff_balance["leave_applicants_count"] = staff_balance["leave_applicants_count"].fillna(0).astype(int)
                        staff_balance["non_leave_staff"] = staff_balance["total_staff"] - staff_balance["leave_applicants_count"]
                        staff_balance["leave_ratio"] = staff_balance["leave_applicants_count"] / staff_balance["total_staff"]
                        staff_balance.to_csv(base_out_dir / "staff_balance_daily.csv", index=False)

                        summary = leave_analyzer.summarize_leave_by_day_count(daily_leave_df.copy(), period="date")
                        summary.to_csv(base_out_dir / "leave_analysis.csv", index=False)
                        ratio_df = leave_analyzer.leave_ratio_by_period_and_weekday(summary.copy())
                        ratio_df.to_csv(base_out_dir / "leave_ratio_breakdown.csv", index=False)

                        if LEAVE_TYPE_REQUESTED in param_leave_target_types:
                            req_daily = daily_leave_df[daily_leave_df["leave_type"] == LEAVE_TYPE_REQUESTED]
                            if not req_daily.empty:
                                applicants = leave_analyzer.summarize_leave_by_day_count(req_daily.copy(), period="date")
                                conc = leave_analyzer.analyze_leave_concentration(
                                    applicants,
                                    leave_type_to_analyze=LEAVE_TYPE_REQUESTED,
                                    concentration_threshold=param_leave_concentration_threshold,
                                    daily_leave_df=req_daily.copy(),
                                )
                                conc.to_csv(base_out_dir / "concentration_requested.csv", index=False)
                if "Cluster" in param_ext_opts:
                    cluster_staff(long_df, base_out_dir)
                if "Skill" in param_ext_opts:
                    build_skill_matrix(long_df, base_out_dir)
            except Exception as e_common:
                log.warning(f"common analysis failed: {e_common}")

            for scenario_key, scenario_params in analysis_scenarios.items():
                st.info(f"シナリオ '{scenario_params['name']}' の分析を開始...")
                scenario_out_dir = base_out_dir / f"out_{scenario_key}"
                scenario_out_dir.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy(intermediate_parquet_path, scenario_out_dir / "intermediate_data.parquet")
                    log.info(f"Copied intermediate_data.parquet to {scenario_out_dir}")
                    if (work_root_exec / "work_patterns.parquet").exists():
                        shutil.copy(
                            work_root_exec / "work_patterns.parquet",
                            scenario_out_dir / "work_patterns.parquet",
                        )
                except Exception as e:
                    log_and_display_error(
                        f"Failed to copy intermediate files to {scenario_out_dir}",
                        e,
                    )
                    continue

                try:
                    update_progress_exec_run("Heatmap: Generating heatmap...")
                    build_heatmap(
                        long_df,
                        scenario_out_dir,
                        param_slot,
                        include_zero_days=True,
                        need_calc_method=param_need_calc_method,
                        ref_start_date_for_need=param_need_ref_start,
                        ref_end_date_for_need=param_need_ref_end,
                        need_stat_method=scenario_params["need_stat_method"],
                        need_manual_values=param_need_manual,
                        need_remove_outliers=param_need_remove_outliers,
                        upper_calc_method=param_upper_method,
                        upper_calc_param=param_upper_param,
                    )
                    if _("基準乖離分析") in param_ext_opts and param_need_calc_method == _(
                        "人員配置基準に基づき設定する"
                    ):
                        heat_all_df = pd.read_parquet(scenario_out_dir / "heat_ALL.parquet")
                        gap_results = analyze_standards_gap(heat_all_df, param_need_manual)
                        st.session_state.gap_analysis_results = gap_results
                        gap_results["gap_summary"].to_excel(
                            scenario_out_dir / "gap_summary.xlsx", index=False
                        )
                        gap_results["gap_heatmap"].to_excel(
                            scenario_out_dir / "gap_heatmap.xlsx"
                        )
                    st.session_state.analysis_status["heatmap"] = "success"
                    st.success(f"✅ Heatmap生成完了 ({scenario_key})")
                except Exception as e:
                    st.session_state.analysis_status["heatmap"] = "failure"
                    log_and_display_error("Heatmapの生成中にエラーが発生しました", e)
                    continue

                try:
                    update_progress_exec_run("Shortage: Analyzing shortage...")
                    shortage_result_exec_run = shortage_and_brief(
                        scenario_out_dir,
                        param_slot,
                        holidays=(holiday_dates_global_for_run or [])
                        + (holiday_dates_local_for_run or []),
                        include_zero_days=True,
                        wage_direct=param_wage_direct,
                        wage_temp=param_wage_temp,
                        penalty_per_lack=param_penalty_lack,
                    )
                    st.session_state.analysis_status["shortage"] = "success"
                    if shortage_result_exec_run is None:
                        st.warning(
                            "Shortage (不足分析) の一部または全てが完了しませんでした。"
                        )
                    else:
                        st.success(f"✅ Shortage (不足分析) 完了 ({scenario_key})")
                        if "Hire plan" in param_ext_opts:
                            try:
                                build_hire_plan_from_kpi(
                                    scenario_out_dir,
                                    monthly_hours_fte=param_std_work_hours,
                                    hourly_wage=param_wage_direct,
                                    recruit_cost=param_hiring_cost,
                                    safety_factor=param_safety_factor,
                                )
                            except Exception as e:
                                log.warning(f"hire_plan generation error: {e}")
                except Exception as e:
                    st.session_state.analysis_status["shortage"] = "failure"
                    log_and_display_error("不足分析の処理中にエラーが発生しました", e)

                # 4. dash_app.py用の「中間サマリーテーブル」を生成
                # 全日付・時間帯・職種・雇用形態の組み合わせを網羅するベースデータを作成
                # 🎯 重要：休日除外済みのデータのみから組み合わせを作成
                working_long_df = long_df[
                    (long_df.get("parsed_slots_count", 0) > 0) & 
                    (long_df.get("holiday_type", "通常勤務") == "通常勤務")
                ]
                all_combinations_from_long_df = working_long_df[[
                    "ds",
                    "role",
                    "employment",
                ]].drop_duplicates().copy()

                all_combinations_from_long_df["date_lbl"] = all_combinations_from_long_df[
                    "ds"
                ].dt.strftime("%Y-%m-%d")
                all_combinations_from_long_df["time"] = all_combinations_from_long_df[
                    "ds"
                ].dt.strftime("%H:%M")

                # parsed_slots_count > 0 のスロットのみスタッフ数をカウント
                working_staff_data = long_df[long_df.get("parsed_slots_count", 0) > 0].copy()
                working_staff_data["date_lbl"] = working_staff_data["ds"].dt.strftime("%Y-%m-%d")
                working_staff_data["time"] = working_staff_data["ds"].dt.strftime("%H:%M")

                staff_counts_actual = (
                    working_staff_data.groupby([
                        "date_lbl",
                        "time",
                        "role",
                        "employment",
                    ])["staff"]
                    .nunique()
                    .reset_index()
                    .rename(columns={"staff": "staff_count"})
                )

                # すべての組み合わせに実際のスタッフ数を結合し、稼働がない場合は0で埋める
                pre_aggregated_df = pd.merge(
                    all_combinations_from_long_df,
                    staff_counts_actual,
                    on=["date_lbl", "time", "role", "employment"],
                    how="left",
                )
                pre_aggregated_df["staff_count"] = pre_aggregated_df["staff_count"].fillna(0).astype(int)

                pre_aggregated_df.to_parquet(
                    scenario_out_dir / "pre_aggregated_data.parquet",
                    index=False,
                )
                log.info(f"シナリオ '{scenario_params['name']}' 用の中間サマリーを保存しました。")
                st.success(f"シナリオ '{scenario_params['name']}' の分析が完了しました。")


            # ----- 休暇分析モジュールの実行 -----
            # "休暇分析" (日本語) が選択されているか確認
            if _("Leave Analysis") in param_ext_opts:
                update_progress_exec_run("Leave Analysis: Processing...")
                st.info(f"{_('Leave Analysis')} 処理中…")
                try:
                    if "long_df" in locals() and not long_df.empty:
                        # 1. 日次・職員別の休暇取得フラグデータを生成
                        daily_leave_df = leave_analyzer.get_daily_leave_counts(
                            long_df, target_leave_types=param_leave_target_types
                        )
                        st.session_state.leave_analysis_results["daily_leave_df"] = (
                            daily_leave_df
                        )

                        if not daily_leave_df.empty:
                            leave_results_temp = {}  # 一時的な結果格納用

                            # 2. 希望休関連の集計と分析
                            if LEAVE_TYPE_REQUESTED in param_leave_target_types:
                                requested_leave_daily = daily_leave_df[
                                    daily_leave_df["leave_type"] == LEAVE_TYPE_REQUESTED
                                ]
                                if not requested_leave_daily.empty:
                                    leave_results_temp["summary_dow_requested"] = (
                                        leave_analyzer.summarize_leave_by_day_count(
                                            requested_leave_daily.copy(),
                                            period="dayofweek",
                                        )
                                    )
                                    leave_results_temp[
                                        "summary_month_period_requested"
                                    ] = leave_analyzer.summarize_leave_by_day_count(
                                        requested_leave_daily.copy(),
                                        period="month_period",
                                    )
                                    leave_results_temp["summary_month_requested"] = (
                                        leave_analyzer.summarize_leave_by_day_count(
                                            requested_leave_daily.copy(), period="month"
                                        )
                                    )

                                    daily_requested_applicants_counts = (
                                        leave_analyzer.summarize_leave_by_day_count(
                                            requested_leave_daily.copy(), period="date"
                                        )
                                    )
                                    leave_results_temp["concentration_requested"] = (
                                        leave_analyzer.analyze_leave_concentration(
                                            daily_requested_applicants_counts,
                                            leave_type_to_analyze=LEAVE_TYPE_REQUESTED,
                                            concentration_threshold=param_leave_concentration_threshold,
                                            daily_leave_df=requested_leave_daily.copy(),
                                        )
                                    )
                                else:
                                    log.info(
                                        f"{LEAVE_TYPE_REQUESTED} のデータが見つからなかったため、関連する集計・分析をスキップしました。"
                                    )
                                    leave_results_temp["summary_dow_requested"] = (
                                        pd.DataFrame()
                                    )
                                    leave_results_temp[
                                        "summary_month_period_requested"
                                    ] = pd.DataFrame()
                                    leave_results_temp["summary_month_requested"] = (
                                        pd.DataFrame()
                                    )
                                    leave_results_temp["concentration_requested"] = (
                                        pd.DataFrame()
                                    )

                            # 勤務予定人数との比較データ作成 (全休暇タイプ)
                            try:
                                total_staff_per_day = (
                                    long_df[long_df["parsed_slots_count"] > 0]
                                    .assign(
                                        date=lambda df: pd.to_datetime(
                                            df["ds"]
                                        ).dt.normalize()
                                    )
                                    .groupby("date")["staff"]
                                    .nunique()
                                    .reset_index(name="total_staff")
                                )
                                all_leave_counts = (
                                    leave_analyzer.summarize_leave_by_day_count(
                                        daily_leave_df.copy(),
                                        period="date",
                                    )
                                    .groupby("date")["total_leave_days"]
                                    .sum()
                                    .reset_index(name="leave_applicants_count")
                                )
                                staff_balance = total_staff_per_day.merge(
                                    all_leave_counts,
                                    on="date",
                                    how="left",
                                )
                                staff_balance["leave_applicants_count"] = (
                                    staff_balance["leave_applicants_count"]
                                    .fillna(0)
                                    .astype(int)
                                )
                                staff_balance["non_leave_staff"] = (
                                    staff_balance["total_staff"]
                                    - staff_balance["leave_applicants_count"]
                                )
                                staff_balance["leave_ratio"] = (
                                    staff_balance["leave_applicants_count"]
                                    / staff_balance["total_staff"]
                                )
                                leave_results_temp["staff_balance_daily"] = (
                                    staff_balance
                                )
                            except Exception as e:
                                log.error(f"勤務予定人数の計算中にエラー: {e}")

                            # 3. 有給休暇関連の集計
                            if LEAVE_TYPE_PAID in param_leave_target_types:
                                paid_leave_daily = daily_leave_df[
                                    daily_leave_df["leave_type"] == LEAVE_TYPE_PAID
                                ]
                                if not paid_leave_daily.empty:
                                    leave_results_temp["summary_dow_paid"] = (
                                        leave_analyzer.summarize_leave_by_day_count(
                                            paid_leave_daily.copy(), period="dayofweek"
                                        )
                                    )
                                    leave_results_temp["summary_month_paid"] = (
                                        leave_analyzer.summarize_leave_by_day_count(
                                            paid_leave_daily.copy(), period="month"
                                        )
                                    )
                                else:
                                    log.info(
                                        f"{LEAVE_TYPE_PAID} のデータが見つからなかったため、関連する集計をスキップしました。"
                                    )
                                    leave_results_temp["summary_dow_paid"] = (
                                        pd.DataFrame()
                                    )
                                    leave_results_temp["summary_month_paid"] = (
                                        pd.DataFrame()
                                    )

                            # 4. 職員別休暇リスト (終日のみ)
                            leave_results_temp["staff_leave_list"] = (
                                leave_analyzer.get_staff_leave_list(
                                    long_df, target_leave_types=param_leave_target_types
                                )
                            )

                            st.session_state.leave_analysis_results.update(
                                leave_results_temp
                            )

                            # Save each analysis output as individual CSV files
                            if "staff_balance_daily" in leave_results_temp:
                                leave_results_temp["staff_balance_daily"].to_csv(
                                    scenario_out_dir / "staff_balance_daily.csv",
                                    index=False,
                                )
                            if "concentration_requested" in leave_results_temp:
                                leave_results_temp[
                                    "concentration_requested"
                                ].to_csv(
                                    scenario_out_dir / "concentration_requested.csv",
                                    index=False,
                                )

                            # Save summary by date for external use
                            try:
                                daily_summary = (
                                    leave_analyzer.summarize_leave_by_day_count(
                                        daily_leave_df.copy(), period="date"
                                    )
                                )
                                st.session_state.leave_analysis_results[
                                    "daily_summary"
                                ] = daily_summary
                                ratio_df = (
                                    leave_analyzer.leave_ratio_by_period_and_weekday(
                                        daily_summary.copy()
                                    )
                                )
                                st.session_state.leave_analysis_results[
                                    "leave_ratio_breakdown"
                                ] = ratio_df
                                try:
                                    ratio_df.to_csv(
                                        scenario_out_dir / "leave_ratio_breakdown.csv",
                                        index=False,
                                    )
                                except Exception as e_ratio:
                                    log.warning(
                                        f"leave_ratio_breakdown.csv write error: {e_ratio}"
                                    )
                                try:
                                    both_conc = leave_analyzer.analyze_both_leave_concentration(
                                        daily_summary.copy(),
                                        concentration_threshold=param_leave_concentration_threshold,
                                    )
                                    st.session_state.leave_analysis_results[
                                        "concentration_both"
                                    ] = both_conc
                                except Exception as e_both:
                                    log.warning(
                                        f"concentration_both generation error: {e_both}"
                                    )
                                leave_csv = scenario_out_dir / "leave_analysis.csv"
                                daily_summary.to_csv(leave_csv, index=False)

                                # Also generate shortage_leave.xlsx for the Shortage tab
                                merge_shortage_leave(scenario_out_dir, leave_csv=leave_csv)
                            except FileNotFoundError:
                                log.warning("shortage_time.parquet not found for merge, skipping.")
                            except Exception as e_save:  # noqa: BLE001
                                log.warning(
                                    f"leave_analysis.csv 書き出しまたは shortage_leave.xlsx 生成中にエラー: {e_save}"
                                )

                            st.success(f"✅ {_('Leave Analysis')} 完了")
                        else:
                            st.info(
                                f"{_('Leave Analysis')}: 分析対象となる休暇データが見つかりませんでした。"
                            )
                    else:
                        st.warning(
                            f"{_('Leave Analysis')}: 前提となる long_df が存在しないか空のため、処理をスキップしました。"
                        )
                except Exception as e_leave:
                    log_and_display_error(
                        f"{_('Leave Analysis')} の処理中にエラーが発生しました", e_leave
                    )
            # ----- 休暇分析モジュールの実行ここまで -----

            # 他の追加モジュールの実行

            skip_opts = {"Fairness", "Fatigue", "Cluster", "Skill"}
            for opt_module_name_exec_run in st.session_state.available_ext_opts_widget:
                if (
                    opt_module_name_exec_run in param_ext_opts
                    and opt_module_name_exec_run not in skip_opts
                    and opt_module_name_exec_run != _("Leave Analysis")
                ):
                    progress_key_exec_run = f"{opt_module_name_exec_run}: Processing..."
                    if opt_module_name_exec_run != "Stats":
                        update_progress_exec_run(progress_key_exec_run)
                    st.info(f"{_(opt_module_name_exec_run)} 処理中…")
                    try:
                        if opt_module_name_exec_run == "Stats":
                            if (
                                st.session_state.analysis_status.get("heatmap")
                                == "success"
                            ):
                                update_progress_exec_run("Stats: Processing...")
                                build_stats(
                                    scenario_out_dir,
                                    holidays=(holiday_dates_global_for_run or [])
                                    + (holiday_dates_local_for_run or []),
                                    wage_direct=param_wage_direct,
                                    wage_temp=param_wage_temp,
                                    penalty_per_lack=param_penalty_lack,
                                )
                                st.session_state.analysis_status["stats"] = "success"
                                st.success("✅ Stats (統計情報) 生成完了")
                            else:
                                st.session_state.analysis_status["stats"] = "skipped"
                                st.warning(
                                    "Heatmap生成が失敗したため、Stats処理をスキップしました。"
                                )
                        elif opt_module_name_exec_run == "Anomaly":
                            detect_anomaly(scenario_out_dir)
                        elif opt_module_name_exec_run == "Fatigue":
                            fatigue_weights = {
                                "start_var": st.session_state.get("weight_start_var_widget", 1.0),
                                "diversity": st.session_state.get("weight_diversity_widget", 1.0),
                                "worktime_var": st.session_state.get("weight_worktime_var_widget", 1.0),
                                "short_rest": st.session_state.get("weight_short_rest_widget", 1.0),
                                "consecutive": st.session_state.get("weight_consecutive_widget", 1.0),
                                "night_ratio": st.session_state.get("weight_night_ratio_widget", 1.0),
                            }
                            result_df = train_fatigue(
                                long_df, scenario_out_dir, weights=fatigue_weights
                            )
                            if result_df is not None and not getattr(result_df, "empty", True):
                                result_df.to_parquet(
                                    scenario_out_dir / "fatigue_score.parquet"
                                )
                        elif opt_module_name_exec_run == "Cluster":
                            cluster_staff(long_df, scenario_out_dir)
                        elif opt_module_name_exec_run == "Skill":
                            build_skill_matrix(long_df, scenario_out_dir)
                        elif opt_module_name_exec_run == "Fairness":
                            run_fairness(long_df, scenario_out_dir)
                            fairness_xlsx = scenario_out_dir / "fairness_after.xlsx"
                            if fairness_xlsx.exists():
                                try:
                                    fairness_df = pd.read_excel(fairness_xlsx)
                                    fairness_df.to_parquet(
                                        scenario_out_dir / "fairness_after.parquet"
                                    )
                                except Exception as e_conv:
                                    log.warning(f"fairness_after.xlsx conversion failed: {e_conv}")
                        elif opt_module_name_exec_run == "Rest Time Analysis":
                            rta = RestTimeAnalyzer()
                            st.session_state.rest_time_results = rta.analyze(
                                long_df, slot_minutes=param_slot
                            )
                            st.session_state.rest_time_results.to_csv(
                                scenario_out_dir / "rest_time.csv", index=False
                            )
                            st.session_state.rest_time_monthly = rta.monthly(
                                st.session_state.rest_time_results
                            )
                            if st.session_state.rest_time_monthly is not None:
                                st.session_state.rest_time_monthly.to_csv(
                                    scenario_out_dir / "rest_time_monthly.csv", index=False
                                )
                        elif opt_module_name_exec_run == "Work Pattern Analysis":
                            wpa = WorkPatternAnalyzer()
                            st.session_state.work_pattern_results = wpa.analyze(long_df)
                            st.session_state.work_pattern_results.to_csv(
                                scenario_out_dir / "work_patterns.csv", index=False
                            )
                            st.session_state.work_pattern_monthly = wpa.analyze_monthly(
                                long_df
                            )
                            if st.session_state.work_pattern_monthly is not None:
                                st.session_state.work_pattern_monthly.to_csv(
                                    scenario_out_dir / "work_pattern_monthly.csv",
                                    index=False,
                                )
                        elif opt_module_name_exec_run == "Attendance Analysis":
                            st.session_state.attendance_results = (
                                AttendanceBehaviorAnalyzer().analyze(long_df)
                            )
                            st.session_state.attendance_results.to_csv(
                                scenario_out_dir / "attendance.csv", index=False
                            )
                        elif opt_module_name_exec_run == "Low Staff Load":
                            lsl = LowStaffLoadAnalyzer()
                            st.session_state.low_staff_load_results = lsl.analyze(
                                long_df, threshold=0.25
                            )
                            st.session_state.low_staff_load_results.to_csv(
                                scenario_out_dir / "low_staff_load.csv", index=False
                            )
                        elif opt_module_name_exec_run == "Combined Score":
                            rest_df = (
                                st.session_state.rest_time_results
                                if st.session_state.rest_time_results is not None
                                else pd.DataFrame()
                            )
                            work_df = (
                                st.session_state.work_pattern_results
                                if st.session_state.work_pattern_results is not None
                                else pd.DataFrame()
                            )
                            att_df = (
                                st.session_state.attendance_results
                                if st.session_state.attendance_results is not None
                                else pd.DataFrame()
                            )
                            st.session_state.combined_score_results = (
                                CombinedScoreCalculator().calculate(
                                    rest_df, work_df, att_df
                                )
                            )
                            st.session_state.combined_score_results.to_csv(
                                scenario_out_dir / "combined_score.csv", index=False
                            )
                        elif opt_module_name_exec_run == "Need forecast":
                            demand_csv_exec_run_fc = scenario_out_dir / "demand_series.csv"
                            forecast_xls_exec_run_fc = (
                                scenario_out_dir / "forecast.parquet"
                            )  # 出力もparquetに
                            heat_all_for_fc_exec_run_fc = (
                                scenario_out_dir / "heat_ALL.parquet"
                            )  # 入力をparquetに
                            if not heat_all_for_fc_exec_run_fc.exists():
                                st.warning(
                                    _("Need forecast")
                                    + f": 必須ファイル {heat_all_for_fc_exec_run_fc.name} が見つかりません。"
                                )
                            else:
                                build_demand_series(
                                    heat_all_for_fc_exec_run_fc,
                                    demand_csv_exec_run_fc,
                                    leave_csv=scenario_out_dir / "leave_analysis.csv"
                                    if (scenario_out_dir / "leave_analysis.csv").exists()
                                    else None,
                                )
                                if demand_csv_exec_run_fc.exists():
                                    fc_leave = scenario_out_dir / "leave_analysis.csv"
                                    forecast_need(
                                        demand_csv_exec_run_fc,
                                        forecast_xls_exec_run_fc,
                                        periods=param_forecast_period,
                                        leave_csv=fc_leave
                                        if fc_leave.exists()
                                        else None,
                                        holidays=(holiday_dates_global_for_run or [])
                                        + (holiday_dates_local_for_run or []),
                                        log_csv=scenario_out_dir / "forecast_history.csv",
                                    )
                                    if forecast_xls_exec_run_fc.exists() and forecast_xls_exec_run_fc.suffix.lower() in {".xlsx", ".xls"}:
                                        try:
                                            forecast_df = pd.read_excel(forecast_xls_exec_run_fc)
                                            forecast_df.to_parquet(
                                                scenario_out_dir / "forecast.parquet"
                                            )
                                        except Exception as e_conv:
                                            log.warning(f"forecast parquet conversion error: {e_conv}")
                                else:
                                    st.warning(
                                        _("Need forecast")
                                        + ": demand_series.csv の生成に失敗しました。"
                                    )
                        elif opt_module_name_exec_run == "RL roster (PPO)":
                            demand_csv_rl_exec_run_rl = (
                                scenario_out_dir / "demand_series.csv"
                            )
                            rl_roster_xls_exec_run_rl = scenario_out_dir / "rl_roster.xlsx"
                            model_zip_rl = scenario_out_dir / "ppo_model.zip"
                            fc_xls = scenario_out_dir / "forecast.xlsx"
                            shortage_xlsx = scenario_out_dir / "shortage_time.xlsx"
                            if demand_csv_rl_exec_run_rl.exists():
                                # learn_roster temporarily disabled due to gymnasium dependency
                                # learn_roster(
                                #     demand_csv_rl_exec_run_rl,
                                #     rl_roster_xls_exec_run_rl,
                                #     forecast_csv=fc_xls if fc_xls.exists() else None,
                                #     shortage_csv=shortage_xlsx
                                #     if shortage_xlsx.exists()
                                #     else None,
                                #     model_path=model_zip_rl,
                                # )
                                pass
                            else:
                                st.warning(
                                    _("RL Roster")
                                    + ": 需要予測データ (demand_series.csv) がありません。"
                                )
                        elif opt_module_name_exec_run == "RL roster (model)":
                            demand_csv_rl_exec_run_rl = (
                                scenario_out_dir / "demand_series.csv"
                            )
                            rl_roster_xls_use = scenario_out_dir / "rl_roster.xlsx"
                            model_zip_rl = scenario_out_dir / "ppo_model.zip"
                            fc_xls = scenario_out_dir / "forecast.xlsx"
                            shortage_xlsx = scenario_out_dir / "shortage_time.xlsx"
                            if model_zip_rl.exists() and fc_xls.exists():
                                # learn_roster temporarily disabled due to gymnasium dependency
                                # learn_roster(
                                #     demand_csv_rl_exec_run_rl
                                #     if demand_csv_rl_exec_run_rl.exists()
                                #     else fc_xls,
                                #     rl_roster_xls_use,
                                #     forecast_csv=fc_xls,
                                #     shortage_csv=shortage_xlsx
                                #     if shortage_xlsx.exists()
                                #     else None,
                                #     model_path=model_zip_rl,
                                #     use_saved_model=True,
                                # )
                                pass
                            else:
                                st.warning(
                                    _("RL Roster")
                                    + ": 学習済みモデルまたは forecast.xlsx が見つかりません。"
                                )
                        elif opt_module_name_exec_run == "Hire plan":
                            demand_csv_hp_exec_run_hp = (
                                scenario_out_dir / "demand_series.csv"
                            )
                            hire_xls_exec_run_hp = scenario_out_dir / "hire_plan.xlsx"
                            if demand_csv_hp_exec_run_hp.exists():
                                build_hire_plan(
                                    demand_csv_hp_exec_run_hp,
                                    hire_xls_exec_run_hp,
                                    param_std_work_hours,
                                    param_safety_factor,
                                    param_target_coverage,
                                )
                            else:
                                st.warning(
                                    _("Hire Plan")
                                    + ": 需要予測データ (demand_series.csv) がありません。"
                                )
                        elif opt_module_name_exec_run == "Cost / Benefit":
                            analyze_cost_benefit(
                                scenario_out_dir,
                                param_wage_direct,
                                param_wage_temp,
                                param_hiring_cost,
                                param_penalty_lack,
                            )
                        elif opt_module_name_exec_run == "最適採用計画":
                            if (
                                st.session_state.analysis_status.get("shortage")
                                == "success"
                            ):
                                try:
                                    log.info(
                                        "最適採用計画のためのサマリーファイルを生成します。"
                                    )
                                    weekday_summary_df = weekday_timeslot_summary(
                                        scenario_out_dir
                                    )
                                    summary_fp = (
                                        scenario_out_dir
                                        / "shortage_weekday_timeslot_summary.xlsx"
                                    )
                                    weekday_summary_df.to_excel(summary_fp, index=False)
                                    log.info(
                                        f"不足分析の曜日・時間帯サマリーを保存しました: {summary_fp}"
                                    )

                                    original_excel_path = Path(
                                        next(
                                            iter(
                                                st.session_state.uploaded_files_info.values()
                                            )
                                        )["path"]
                                    )
                                    create_optimal_hire_plan(
                                        scenario_out_dir, original_excel_path
                                    )
                                    st.success("✅ 最適採用計画 生成完了")
                                except Exception as e_opt_hire:
                                    log.error(
                                        f"最適採用計画の生成中にエラーが発生しました: {e_opt_hire}",
                                        exc_info=True,
                                    )
                                    st.warning(
                                        "最適採用計画の生成に失敗しました。詳細はログを確認してください。"
                                    )
                            else:
                                st.warning(
                                    "最適採用計画の生成には、不足分析が先に完了している必要があります。"
                                )
                        st.success(f"✅ {_(opt_module_name_exec_run)} 完了")
                    except FileNotFoundError as fe_opt_exec_run_loop:
                        log_and_display_error(
                            f"{_(opt_module_name_exec_run)} の処理中にエラー (ファイル未検出)",
                            fe_opt_exec_run_loop,
                        )
                        log.error(
                            f"{opt_module_name_exec_run} 処理エラー (FileNotFoundError): {fe_opt_exec_run_loop}",
                            exc_info=True,
                        )
                    except Exception as e_opt_exec_run_loop:
                        log_and_display_error(
                            f"{_(opt_module_name_exec_run)} の処理中にエラーが発生しました",
                            e_opt_exec_run_loop,
                        )
                        log.error(
                            f"{opt_module_name_exec_run} 処理エラー: {e_opt_exec_run_loop}",
                            exc_info=True,
                        )

            # --- 日別人件費の計算と保存 ---
            if (
                "wage_config" in st.session_state
                and st.session_state.analysis_status.get("ingest") == "success"
                and not long_df.empty
            ):
                try:
                    daily_cost_df = calculate_daily_cost(
                        long_df,
                        st.session_state.wage_config,
                        by=st.session_state.get("cost_by_widget", "role"),
                        slot_minutes=param_slot,
                    )
                    daily_cost_df.to_excel(
                        out_dir_exec / "daily_cost.xlsx", index=False
                    )
                    daily_cost_df.to_parquet(
                        out_dir_exec / "daily_cost.parquet", index=False
                    )
                except Exception as e_cost:
                    log.warning(f"daily cost calculation failed: {e_cost}")

            progress_bar_val.progress(100)
            progress_text_area.success("✨ 全工程完了！")
            st.balloons()
            st.success(_("All processes complete!"))
            st.session_state.analysis_done = True
            st.success("✅ 分析が完了しました。")
            st.header("ステップ1: 分析結果をダウンロード")
            st.write(
                "以下のボタンをクリックして、分析結果がすべて入ったZIPファイルを手元のPCに保存してください。"
            )

            zip_buffer = io.BytesIO()
            zip_base = Path(st.session_state.work_root_path_str) / "out"
            if zip_base.exists():
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                    for f_path in zip_base.glob("**/*"):
                        zf.write(f_path, f_path.relative_to(zip_base))

                st.download_button(
                    label="📥 analysis_results.zip をダウンロード",
                    data=zip_buffer.getvalue(),
                    file_name="analysis_results.zip",
                    mime="application/zip",
                    type="primary",
                )
            else:
                st.error("分析結果ディレクトリが見つかりませんでした。")

            st.header("ステップ2: 高速ビューアで結果を確認")
            st.write(
                "結果のダウンロード後、以下のリンクからビューアを開き、ダウンロードしたZIPファイルをアップロードしてください。"
            )

            DASH_APP_URL = "http://127.0.0.1:8050"
            st.markdown(
                f"### [📈 分析結果を高速ビューアで表示する]({DASH_APP_URL})",
                unsafe_allow_html=True,
            )
            
            # 包括分析ログの生成
            if st.session_state.analysis_done and st.session_state.out_dir_path_str:
                try:
                    output_dir = Path(st.session_state.out_dir_path_str)
                    log_file = create_comprehensive_analysis_log(output_dir, analysis_type="FULL")
                    if log_file:
                        st.success(f"📋 包括分析レポートを生成しました: {log_file.name}")
                        logging.info(f"[app] 包括分析レポート生成完了: {log_file}")
                    else:
                        st.warning("⚠️ 包括分析レポートの生成に失敗しました")
                except Exception as e_log:
                    st.warning(f"⚠️ 包括分析レポート生成エラー: {e_log}")
                    logging.error(f"[app] 包括分析レポート生成エラー: {e_log}")
        except ValueError as ve_exec_run_main:
            log_and_display_error(
                _("Error during analysis (ValueError)"), ve_exec_run_main
            )
            log.error(f"解析エラー (ValueError): {ve_exec_run_main}", exc_info=True)
            st.session_state.analysis_done = False
        except FileNotFoundError as fe_exec_run_main:
            log_and_display_error(_("Required file not found"), fe_exec_run_main)
            log.error(f"ファイル未検出エラー: {fe_exec_run_main}", exc_info=True)
            st.session_state.analysis_done = False
        except Exception as e_exec_run_main:
            log_and_display_error(_("Unexpected error occurred"), e_exec_run_main)
            log.error(f"予期せぬエラー: {e_exec_run_main}", exc_info=True)
            st.session_state.analysis_done = False
        finally:
            if "progress_bar_val" in locals() and progress_bar_val is not None:
                progress_bar_val.empty()
            if "progress_text_area" in locals() and progress_text_area is not None:
                progress_text_area.empty()
            if "progress_status" in locals() and progress_status is not None:
                progress_status.empty()

        if st.session_state.analysis_done and st.session_state.out_dir_path_str:
            out_dir_to_save_exec_main_run = Path(st.session_state.out_dir_path_str)
            if out_dir_to_save_exec_main_run.exists():
                st.markdown("---")
                st.header("3. " + _("Save Analysis Results"))
                with st.expander(_("Run Parameters")):
                    st.json(
                        {
                            "sheets": param_selected_sheets,
                            "slot": param_slot,
                            "need_calc": param_need_calc_method,
                            "stat": param_need_stat_method,
                            "ext_modules": param_ext_opts,
                        }
                    )
                current_save_mode_exec_main_run = (
                    st.session_state.save_mode_selectbox_widget
                )
                if current_save_mode_exec_main_run == _("Save to folder"):
                    st.info(_("Output folder") + f": `{out_dir_to_save_exec_main_run}`")
                    st.markdown(_("Open the above path in Explorer."))
                else:  # ZIP Download
                    zip_base_name_exec_main_run = f"ShiftSuite_Analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    if st.session_state.work_root_path_str is None:
                        log_and_display_error(
                            "一時作業ディレクトリが見つかりません。ZIPファイルの作成に失敗しました。",
                            FileNotFoundError("work_root"),
                        )
                    else:
                        work_root_for_zip_dl_exec_main_run = Path(
                            st.session_state.work_root_path_str
                        )
                        zip_path_obj_to_download_exec_main_run = (
                            work_root_for_zip_dl_exec_main_run
                            / f"{zip_base_name_exec_main_run}.zip"
                        )
                        try:
                            with zipfile.ZipFile(
                                zip_path_obj_to_download_exec_main_run,
                                "w",
                                zipfile.ZIP_DEFLATED,
                            ) as zf_dl_exec_main_run:
                                base_dir = Path(st.session_state.work_root_path_str)
                                scenario_dirs = sorted(base_dir.glob("out_*"))
                                if not scenario_dirs:
                                    scenario_dirs = [out_dir_to_save_exec_main_run]
                                for s_dir in scenario_dirs:
                                    for file_to_zip_dl_exec_main_run in s_dir.rglob("*"):
                                        if file_to_zip_dl_exec_main_run.is_file():
                                            zf_dl_exec_main_run.write(
                                                file_to_zip_dl_exec_main_run,
                                                file_to_zip_dl_exec_main_run.relative_to(base_dir),
                                            )
                            with open(
                                zip_path_obj_to_download_exec_main_run, "rb"
                            ) as fp_zip_data_to_download_dl_exec_main_run:
                                st.download_button(
                                    label=_("Download analysis results as ZIP"),
                                    data=fp_zip_data_to_download_dl_exec_main_run,
                                    file_name=f"{zip_base_name_exec_main_run}.zip",
                                    mime="application/zip",
                                    use_container_width=True,
                                )
                            log.info(
                                f"ZIPファイルを作成し、ダウンロードボタンを表示しました: {zip_path_obj_to_download_exec_main_run}"
                            )
                        except Exception as e_zip_final_exec_run_main_ex_v3:
                            log_and_display_error(
                                _("Error creating ZIP file"),
                                e_zip_final_exec_run_main_ex_v3,
                            )
                            log.error(
                                f"ZIP作成エラー (最終段階): {e_zip_final_exec_run_main_ex_v3}",
                                exc_info=True,
                            )
        else:
            log.warning(
                f"解析は完了しましたが、出力ディレクトリ '{st.session_state.out_dir_path_str}' が見つかりません。"
            )

        st.session_state.analysis_results[file_name] = {
            "out_dir_path_str": st.session_state.out_dir_path_str,
            "leave_analysis_results": st.session_state.leave_analysis_results,
            "rest_time_results": st.session_state.rest_time_results,
            "work_pattern_results": st.session_state.work_pattern_results,
            "attendance_results": st.session_state.attendance_results,
            "combined_score_results": st.session_state.combined_score_results,
            "low_staff_load_results": st.session_state.low_staff_load_results,
        }


# 分析が完了している場合は常にdisplay_dataを更新
if st.session_state.get("analysis_done"):
    out_dir_path = st.session_state.get("out_dir_path_str")
    if out_dir_path:
        out_dir = Path(out_dir_path)
        if out_dir.exists():
            update_display_data_with_heatmaps(out_dir)
        else:
            log.warning(f"出力ディレクトリが存在しません: {out_dir}")
            st.warning(f"出力ディレクトリが見つかりません: {out_dir}")
    else:
        log.warning("出力ディレクトリパスが設定されていません。")
        st.warning("分析結果のディレクトリパスが設定されていません。")

# 完全修正版 - 休暇分析結果表示コード全体

# Plotlyの全体問題を修正した休暇分析コード


#  新しい「休暇分析」タブの表示 (解析が完了し、休暇分析が選択されている場合)
# ─────────────────────────────  app.py  (Part 3 / 3)  ──────────────────────────
def display_overview_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Overview"))
        display_data = st.session_state.get("display_data", {})
        df_sh_role = display_data.get("shortage_role")
        lack_h = 0.0
        excess_cost = lack_temp_cost = lack_penalty_cost = 0.0
        if isinstance(df_sh_role, pd.DataFrame):
            try:
                lack_h = df_sh_role["lack_h"].sum() if "lack_h" in df_sh_role else 0.0
                excess_cost = float(
                    df_sh_role.get("estimated_excess_cost", pd.Series()).sum()
                )
                lack_temp_cost = float(
                    df_sh_role.get(
                        "estimated_lack_cost_if_temporary_staff", pd.Series()
                    ).sum()
                )
                lack_penalty_cost = float(
                    df_sh_role.get("estimated_lack_penalty_cost", pd.Series()).sum()
                )
            except Exception as e:
                st.warning(f"shortage_role_summary.parquet 読込/集計エラー: {e}")
                excess_cost = lack_temp_cost = lack_penalty_cost = 0.0

        meta_df = display_data.get("fairness_before")
        jain_display = "N/A"
        if isinstance(meta_df, pd.DataFrame):
            try:
                jain_row = meta_df[meta_df["metric"] == "jain_index"]
                if not jain_row.empty:
                    jain_display = f"{float(jain_row['value'].iloc[0]):.3f}"
            except Exception:
                pass

        staff_count = 0
        avg_night_ratio = 0.0
        df_staff = display_data.get("staff_stats")
        if isinstance(df_staff, pd.DataFrame):
            try:
                staff_count = len(df_staff)
                if (
                    "night_ratio" in df_staff.columns
                    and not df_staff["night_ratio"].empty
                ):
                    avg_night_ratio = float(df_staff["night_ratio"].mean())
            except Exception:
                pass

        alerts_count = 0
        df_alerts = display_data.get("stats_alerts")
        if isinstance(df_alerts, pd.DataFrame):
            try:
                if _valid_df(df_alerts):
                    alerts_count = len(df_alerts)
            except Exception:
                pass

        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
        c1.metric(_("総不足時間(h) (職種別合計)"), f"{lack_h:.1f}")
        c2.metric("夜勤 Jain指数", jain_display)
        c3.metric(_("Total Staff"), staff_count)
        c4.metric(_("Avg. Night Ratio"), f"{avg_night_ratio:.3f}")
        c5.metric(_("Alerts Count"), alerts_count)
        c6.metric(_("総過剰コスト試算(¥)"), f"{excess_cost:,.0f}")
        c7.metric(_("総不足コスト試算(派遣補填時)(¥)"), f"{lack_temp_cost:,.0f}")
        c8.metric(_("総不足ペナルティ試算(¥)"), f"{lack_penalty_cost:,.0f}")


def display_heatmap_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Heatmap"))

        # 選択肢およびデータは事前に st.session_state に格納済み
        roles = st.session_state.get("available_roles", [])
        employments = st.session_state.get("available_employments", [])

        scope_opts = {"overall": _("Overall")}
        if roles:
            scope_opts["role"] = _("Role")
        if employments:
            scope_opts["employment"] = _("Employment")

        # --- UIコントロール ---
        with st.form(key="heatmap_controls_form"):
            st.write(
                "表示するヒートマップの範囲とモードを選択し、更新ボタンを押してください。"
            )

            c1, c2 = st.columns(2)
            with c1:
                scope_lbl = st.selectbox(
                    "表示範囲", list(scope_opts.values()), key="heat_scope_form"
                )
            scope = [k for k, v in scope_opts.items() if v == scope_lbl][0]

            sel_item = []
            with c2:
                if scope == "role":
                    sel_item = st.multiselect(
                        _("Role"), roles, key="heat_scope_role_form"
                    )
                elif scope == "employment":
                    sel_item = st.multiselect(
                        _("Employment"), employments, key="heat_scope_emp_form"
                    )

            mode_opts = {"Raw": _("Raw Count"), "Ratio": _("Ratio (staff ÷ need)")}
            mode_lbl = st.radio(
                _("Display Mode"),
                list(mode_opts.values()),
                horizontal=True,
                key="dash_heat_mode_radio_form",
            )

            submitted = st.form_submit_button("ヒートマップを更新")

        # --- フォーム送信後にグラフを描画 ---
        if submitted:
            scope_info_for_title = scope_lbl
            heat_keys = ["heat_all"]
            if scope == "role" and sel_item:
                heat_keys = [f"heat_role_{safe_sheet(x, for_path=True)}" for x in sel_item]
                scope_info_for_title += f" ({', '.join(sel_item)})"
            elif scope == "employment" and sel_item:
                heat_keys = [f"heat_emp_{safe_sheet(x, for_path=True)}" for x in sel_item]
                scope_info_for_title += f" ({', '.join(sel_item)})"

            df_heat = load_and_sum_heatmaps(data_dir, heat_keys)
            mode = [k for k, v in mode_opts.items() if v == mode_lbl][0]

            if df_heat is not None and not df_heat.empty:
                fig = generate_heatmap_figure(df_heat, mode, scope_info_for_title)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("ヒートマップデータが見つかりません")


def display_shortage_tab(tab_container, data_dir):
    with tab_container:
        if st.session_state.analysis_status.get("shortage") != "success":
            st.warning("不足分析が正常に完了していないため、結果を表示できません。")
            return
        st.subheader(_("Shortage"))
        st.info(
            "\n".join(
                [
                    "### 計算に使用したパラメータ",
                    f"- Need算出方法: {st.session_state.get('need_calc_method_widget')}",
                    f"- Upper算出方法: {st.session_state.get('upper_calc_method_widget')}",
                    f"- 直接雇用単価: ¥{st.session_state.get('wage_direct_widget', 0):,.0f}/h",
                    f"- 派遣単価: ¥{st.session_state.get('wage_temp_widget', 0):,.0f}/h",
                    f"- 採用コスト: ¥{st.session_state.get('hiring_cost_once_widget', 0):,}/人",
                    f"- 不足ペナルティ: ¥{st.session_state.get('penalty_per_lack_widget', 0):,.0f}/h",
                ]
            )
        )
        # メタデータはメモリ上の session_state から取得
        roles = st.session_state.get("available_roles", [])
        employments = st.session_state.get("available_employments", [])
        display_data = st.session_state.get("display_data", {})
        df_s_role = display_data.get("shortage_role")
        if isinstance(df_s_role, pd.DataFrame):
            if not _valid_df(df_s_role):
                st.info("Data not available")
                return
                display_role_df = df_s_role.rename(
                    columns={
                        "role": _("Role"),
                        "need_h": _("Need Hours"),
                        "staff_h": _("Staff Hours"),
                        "lack_h": _("Shortage Hours"),
                        "excess_h": _("Excess Hours"),
                        "estimated_excess_cost": _("Excess Cost Est.(¥)"),
                        "estimated_lack_cost_if_temporary_staff": _(
                            "Lack Cost if Temp(¥)"
                        ),
                        "estimated_lack_penalty_cost": _("Lack Penalty Est.(¥)"),
                        "working_days_considered": _("Working Days"),
                        "note": _("Note"),
                    }
                )
                total_lack = float(df_s_role.get("lack_h", pd.Series()).sum())
                if total_lack:
                    cols = st.columns(4)
                    cols[0].metric(_("Total Shortage Hours"), f"{total_lack:.1f}")
                    if {"role", "lack_h"}.issubset(df_s_role.columns):
                        top_roles = df_s_role.nlargest(3, "lack_h")[["role", "lack_h"]]
                        for i, row in enumerate(
                            top_roles.itertuples(index=False), start=1
                        ):
                            cols[i].metric(
                                _("Top shortage role {n}").format(n=i),
                                f"{row.role}: {row.lack_h:.1f}h",
                            )
                st.dataframe(display_role_df, use_container_width=True, hide_index=True)
                if "role" in df_s_role and "lack_h" in df_s_role:
                    fig_role = px.bar(
                        df_s_role,
                        x="role",
                        y="lack_h",
                        labels={"role": _("Role"), "lack_h": _("Shortage Hours")},
                        color_discrete_sequence=["#FFA500"],
                    )
                    st.plotly_chart(
                        fig_role, use_container_width=True, key="short_role_chart"
                    )
                    st.caption(_("Shortage by role caption"))
                if "role" in df_s_role and "excess_h" in df_s_role:
                    fig_role_ex = px.bar(
                        df_s_role,
                        x="role",
                        y="excess_h",
                        labels={"role": _("Role"), "excess_h": _("Excess Hours")},
                        color_discrete_sequence=["#00BFFF"],
                    )
                    st.plotly_chart(
                        fig_role_ex, use_container_width=True, key="excess_role_chart"
                    )
                cost_cols = [
                    "estimated_excess_cost",
                    "estimated_lack_cost_if_temporary_staff",
                    "estimated_lack_penalty_cost",
                ]
                if {"role"}.issubset(df_s_role.columns) and any(
                    c in df_s_role.columns for c in cost_cols
                ):
                    cost_df = df_s_role[
                        ["role"] + [c for c in cost_cols if c in df_s_role.columns]
                    ]
                    cost_long = cost_df.melt(
                        id_vars="role", var_name="type", value_name="cost"
                    )
                    fig_cost = px.bar(
                        cost_long,
                        x="role",
                        y="cost",
                        color="type",
                        barmode="group",
                        labels={
                            "role": _("Role"),
                            "cost": _("Cost (¥)"),
                            "type": _("Type"),
                        },
                    )
                    st.plotly_chart(
                        fig_cost, use_container_width=True, key="cost_role_chart"
                    )

                fp_hire = data_dir / "hire_plan.parquet"
                if fp_hire.exists():
                    try:
                        df_hire = load_data_cached(
                            str(fp_hire),
                            is_parquet=True,
                            file_mtime=_file_mtime(fp_hire),
                        )
                        if not _valid_df(df_hire):
                            st.info("Data not available")
                            return
                        if {"role", "hire_fte"}.issubset(df_hire.columns):
                            st.markdown(_("Required FTE per Role"))
                            display_hire_df = df_hire[["role", "hire_fte"]].rename(
                                columns={"role": _("Role"), "hire_fte": _("hire_fte")}
                            )
                            st.dataframe(
                                display_hire_df,
                                use_container_width=True,
                                hide_index=True,
                            )
                            fig_hire = px.bar(
                                df_hire,
                                x="role",
                                y="hire_fte",
                                labels={"role": _("Role"), "hire_fte": _("hire_fte")},
                                color_discrete_sequence=["#1f77b4"],
                            )
                            st.plotly_chart(
                                fig_hire,
                                use_container_width=True,
                                key="short_hire_chart",
                            )
                    except Exception as e:
                        log_and_display_error("hire_plan.parquet 表示エラー", e)

                role_month_fp = data_dir / "shortage_role_monthly.parquet"
                if role_month_fp.exists():
                    df_month = load_data_cached(
                        str(role_month_fp),
                        is_parquet=True,
                        file_mtime=_file_mtime(role_month_fp),
                    )
                    if not _valid_df(df_month):
                        st.info("Data not available")
                        return
                    if not df_month.empty and {"month", "role", "lack_h"}.issubset(
                        df_month.columns
                    ):
                        fig_m = px.bar(
                            df_month,
                            x="month",
                            y="lack_h",
                            color="role",
                            barmode="stack",
                            title=_("Monthly Shortage Hours by Role"),
                            labels={
                                "month": _("Month"),
                                "lack_h": _("Shortage Hours"),
                                "role": _("Role"),
                            },
                        )
                        st.plotly_chart(
                            fig_m, use_container_width=True, key="short_month_chart"
                        )
                        with st.expander(_("Monthly shortage data")):
                            st.dataframe(
                                df_month, use_container_width=True, hide_index=True
                            )
        else:
            st.info(
                _("Shortage")
                + " (shortage_role_summary.parquet) "
                + _("が見つかりません。")
            )

        fp_s_emp = data_dir / "shortage_employment_summary.parquet"
        if fp_s_emp.exists():
            try:
                df_s_emp = load_data_cached(
                    str(fp_s_emp),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_s_emp),
                )
                if _valid_df(df_s_emp):
                    display_emp_df = df_s_emp.rename(
                        columns={
                            "employment": _("Employment"),
                            "need_h": _("Need Hours"),
                            "staff_h": _("Staff Hours"),
                            "lack_h": _("Shortage Hours"),
                            "excess_h": _("Excess Hours"),
                            "estimated_excess_cost": _("Excess Cost Est.(¥)"),
                            "estimated_lack_cost_if_temporary_staff": _(
                                "Lack Cost if Temp(¥)"
                            ),
                            "estimated_lack_penalty_cost": _("Lack Penalty Est.(¥)"),
                            "working_days_considered": _("Working Days"),
                            "note": _("Note"),
                        }
                    )
                    st.dataframe(
                        display_emp_df, use_container_width=True, hide_index=True
                    )
                    if "employment" in df_s_emp and "lack_h" in df_s_emp:
                        fig_emp = px.bar(
                            df_s_emp,
                            x="employment",
                            y="lack_h",
                            labels={
                                "employment": _("Employment"),
                                "lack_h": _("Shortage Hours"),
                            },
                            color_discrete_sequence=["#2ca02c"],
                        )
                        st.plotly_chart(
                            fig_emp, use_container_width=True, key="short_emp_chart"
                        )
                    if "employment" in df_s_emp and "excess_h" in df_s_emp:
                        fig_emp_ex = px.bar(
                            df_s_emp,
                            x="employment",
                            y="excess_h",
                            labels={
                                "employment": _("Employment"),
                                "excess_h": _("Excess Hours"),
                            },
                            color_discrete_sequence=["#00BFFF"],
                        )
                        st.plotly_chart(
                            fig_emp_ex, use_container_width=True, key="excess_emp_chart"
                        )
                    cost_cols_emp = [
                        "estimated_excess_cost",
                        "estimated_lack_cost_if_temporary_staff",
                        "estimated_lack_penalty_cost",
                    ]
                    if {"employment"}.issubset(df_s_emp.columns) and any(
                        c in df_s_emp.columns for c in cost_cols_emp
                    ):
                        emp_cost_df = df_s_emp[
                            ["employment"]
                            + [c for c in cost_cols_emp if c in df_s_emp.columns]
                        ]
                        emp_cost_long = emp_cost_df.melt(
                            id_vars="employment", var_name="type", value_name="cost"
                        )
                        fig_emp_cost = px.bar(
                            emp_cost_long,
                            x="employment",
                            y="cost",
                            color="type",
                            barmode="group",
                            labels={
                                "employment": _("Employment"),
                                "cost": _("Cost (¥)"),
                                "type": _("Type"),
                            },
                        )
                        st.plotly_chart(
                            fig_emp_cost,
                            use_container_width=True,
                            key="cost_emp_chart",
                        )
                emp_month_fp = data_dir / "shortage_employment_monthly.parquet"
                if emp_month_fp.exists():
                    df_emp_month = load_data_cached(
                        str(emp_month_fp),
                        is_parquet=True,
                        file_mtime=_file_mtime(emp_month_fp),
                    )
                    if _valid_df(df_emp_month) and {
                        "month",
                        "employment",
                        "lack_h",
                    }.issubset(df_emp_month.columns):
                        fig_emp_m = px.bar(
                            df_emp_month,
                            x="month",
                            y="lack_h",
                            color="employment",
                            barmode="stack",
                            title=_("Monthly Shortage Hours by Employment"),
                            labels={
                                "month": _("Month"),
                                "lack_h": _("Shortage Hours"),
                                "employment": _("Employment"),
                            },
                        )
                        st.plotly_chart(
                            fig_emp_m,
                            use_container_width=True,
                            key="short_emp_month_chart",
                        )
                        with st.expander(_("Monthly shortage data")):
                            st.dataframe(
                                df_emp_month, use_container_width=True, hide_index=True
                            )
            except Exception as e:
                log_and_display_error(
                    "shortage_employment_summary.parquet 表示エラー", e
                )
        else:
            st.info(
                _("Shortage")
                + " (shortage_employment_summary.parquet) "
                + _("が見つかりません。")
            )
        st.markdown("---")
        fp_s_time = data_dir / "shortage_time.parquet"
        if fp_s_time.exists():
            try:
                df_s_time = load_data_cached(
                    str(fp_s_time),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_s_time),
                )
                if not _valid_df(df_s_time):
                    st.info("Data not available")
                    return
                st.write(_("Shortage by Time (count per day)"))
                avail_dates = df_s_time.columns.tolist()
                if avail_dates:
                    sel_date = st.selectbox(
                        _("Select date to display"),
                        avail_dates,
                        key="dash_short_time_date",
                    )
                    if sel_date:
                        fig_time = px.bar(
                            df_s_time[sel_date].reset_index(),
                            x=df_s_time.index.name or "index",
                            y=sel_date,
                            labels={
                                df_s_time.index.name or "index": _("Time"),
                                sel_date: _("Shortage Hours"),
                            },
                            color_discrete_sequence=["#FFA500"],
                            title=f"{sel_date} の時間帯別不足時間",
                        )
                        st.plotly_chart(
                            fig_time, use_container_width=True, key="short_time_chart"
                        )
                        st.caption(_("Shortage by time caption"))
                else:
                    st.info(_("No date columns in shortage data."))
                with st.expander(_("Display all time-slot shortage data")):
                    st.dataframe(df_s_time, use_container_width=True)
            except Exception as e:
                log_and_display_error("shortage_time.parquet 表示エラー", e)
        else:
            st.info(
                _("Shortage") + " (shortage_time.parquet) " + _("が見つかりません。")
            )

        fp_e_time = data_dir / "excess_time.parquet"
        if fp_e_time.exists():
            try:
                df_e_time = load_data_cached(
                    str(fp_e_time),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_e_time),
                )
                if not _valid_df(df_e_time):
                    st.info("Data not available")
                    return
                st.write(_("Excess by Time (count per day)"))
                avail_e_dates = df_e_time.columns.tolist()
                if avail_e_dates:
                    sel_e_date = st.selectbox(
                        _("Select date to display"),
                        avail_e_dates,
                        key="excess_time_date",
                    )
                    if sel_e_date:
                        fig_e_time = px.bar(
                            df_e_time[sel_e_date].reset_index(),
                            x=df_e_time.index.name or "index",
                            y=sel_e_date,
                            labels={
                                df_e_time.index.name or "index": _("Time"),
                                sel_e_date: _("Excess Hours"),
                            },
                            color_discrete_sequence=["#00BFFF"],
                            title=f"{sel_e_date} の時間帯別過剰時間",
                        )
                        st.plotly_chart(
                            fig_e_time,
                            use_container_width=True,
                            key="excess_time_chart",
                        )
                else:
                    st.info(_("No date columns in excess data."))
                with st.expander(_("Display all time-slot excess data")):
                    st.dataframe(df_e_time, use_container_width=True)
            except Exception as e:
                log_and_display_error("excess_time.parquet 表示エラー", e)
        else:
            st.info(
                _("Excess by Time (count per day)")
                + " (excess_time.parquet) "
                + _("が見つかりません。")
            )

        st.markdown("##### 不足率ヒートマップ")
        st.info(
            """
            このヒートマップは、各時間帯で**必要人数に対してどれくらいの割合で人員が不足していたか**を示します。
            - **色が濃い（赤に近い）**: 不足の割合が高く、人員配置が特に手薄だった時間帯です。
            - **色が薄い（白に近い）**: 不足がなかった、または少なかった時間帯です。
            """
        )

        roles = st.session_state.get("available_roles", [])
        employments = st.session_state.get("available_employments", [])
        scope_opts_shortage = {"overall": _("Overall")}
        if roles:
            scope_opts_shortage["role"] = _("Role")
        if employments:
            scope_opts_shortage["employment"] = _("Employment")

        c1_short, c2_short, c3_short = st.columns(3)
        with c1_short:
            scope_lbl_s = st.selectbox(
                "表示範囲",
                list(scope_opts_shortage.values()),
                key="shortage_heat_scope",
            )
            scope_s = [k for k, v in scope_opts_shortage.items() if v == scope_lbl_s][0]

        sel_item_s = None
        with c2_short:
            if scope_s == "role":
                sel_item_s = st.selectbox(
                    _("Role"), roles, key="shortage_heat_scope_role"
                )
            elif scope_s == "employment":
                sel_item_s = st.selectbox(
                    _("Employment"), employments, key="shortage_heat_scope_emp"
                )

        df_ratio = pd.DataFrame()
        ratio_key = None
        if scope_s == "overall":
            ratio_key = "ratio_all"
        elif scope_s == "role" and sel_item_s:
            ratio_key = f"ratio_role_{safe_sheet(sel_item_s, for_path=True)}"
        elif scope_s == "employment" and sel_item_s:
            ratio_key = f"ratio_emp_{safe_sheet(sel_item_s, for_path=True)}"

        if ratio_key:
            df_ratio = st.session_state.display_data.get(ratio_key, pd.DataFrame())

        if _valid_df(df_ratio):
            fig_ratio_heat = dashboard.shortage_heatmap(df_ratio)
            fig_ratio_heat.update_layout(
                title=f"不足率ヒートマップ ({scope_lbl_s}{': ' + sel_item_s if sel_item_s else ''})"
            )
            st.plotly_chart(
                fig_ratio_heat,
                use_container_width=True,
                key="shortage_tab_ratio_heatmap_dynamic",
            )
        else:
            st.info("選択されたスコープの不足率データを表示できません。")

        fp_e_ratio = data_dir / "excess_ratio.parquet"
        if fp_e_ratio.exists():
            try:
                df_e_ratio = load_data_cached(
                    str(fp_e_ratio),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_e_ratio),
                )
                if not _valid_df(df_e_ratio):
                    st.info("Data not available")
                    return
                st.write(_("Excess Ratio by Time"))
                avail_er_dates = df_e_ratio.columns.tolist()
                if avail_er_dates:
                    sel_er_date = st.selectbox(
                        _("Select date for ratio"),
                        avail_er_dates,
                        key="excess_ratio_date",
                    )
                    if sel_er_date:
                        fig_er = px.bar(
                            df_e_ratio[sel_er_date].reset_index(),
                            x=df_e_ratio.index.name or "index",
                            y=sel_er_date,
                            labels={
                                df_e_ratio.index.name or "index": _("Time"),
                                sel_er_date: _("Excess Hours"),
                            },
                            color_discrete_sequence=["#00BFFF"],
                            title=f"{sel_er_date} の時間帯別過剰率",
                        )
                        st.plotly_chart(
                            fig_er, use_container_width=True, key="excess_ratio_chart"
                        )
                else:
                    st.info(_("No date columns in excess data."))
                with st.expander(_("Display all ratio data")):
                    st.dataframe(df_e_ratio, use_container_width=True)
            except Exception as e:
                log_and_display_error("excess_ratio.parquet 表示エラー", e)
        else:
            st.info(
                _("Excess Ratio by Time")
                + " (excess_ratio.parquet) "
                + _("が見つかりません。")
            )

        fp_s_freq = data_dir / "shortage_freq.parquet"
        if fp_s_freq.exists():
            try:
                df_freq = load_data_cached(
                    str(fp_s_freq),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_s_freq),
                )
                if not _valid_df(df_freq):
                    st.info("Data not available")
                    return
                st.write(_("Shortage Frequency (days)"))
                fig_freq = px.bar(
                    df_freq.reset_index(),
                    x=df_freq.index.name or "index",
                    y="shortage_days",
                    labels={
                        df_freq.index.name or "index": _("Time"),
                        "shortage_days": _("Shortage Frequency (days)"),
                    },
                    color_discrete_sequence=["#708090"],
                    title="時間帯別不足日数",
                )
                st.plotly_chart(
                    fig_freq, use_container_width=True, key="short_freq_chart"
                )
                with st.expander(_("Data")):
                    st.dataframe(df_freq, use_container_width=True)
            except Exception as e:
                log_and_display_error("shortage_freq.parquet 表示エラー", e)
        else:
            st.info(
                _("Shortage") + " (shortage_freq.parquet) " + _("が見つかりません。")
            )

        fp_e_freq = data_dir / "excess_freq.parquet"
        if fp_e_freq.exists():
            try:
                df_e_freq = load_data_cached(
                    str(fp_e_freq),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_e_freq),
                )
                if not _valid_df(df_e_freq):
                    st.info("Data not available")
                    return
                st.write(_("Excess Frequency (days)"))
                fig_efreq = px.bar(
                    df_e_freq.reset_index(),
                    x=df_e_freq.index.name or "index",
                    y="excess_days",
                    labels={
                        df_e_freq.index.name or "index": _("Time"),
                        "excess_days": _("Excess Frequency (days)"),
                    },
                    color_discrete_sequence=["#00BFFF"],
                    title="時間帯別過剰日数",
                )
                st.plotly_chart(
                    fig_efreq, use_container_width=True, key="excess_freq_chart"
                )
                with st.expander(_("Data")):
                    st.dataframe(df_e_freq, use_container_width=True)
            except Exception as e:
                log_and_display_error("excess_freq.parquet 表示エラー", e)
        else:
            st.info(
                _("Excess Frequency (days)")
                + " (excess_freq.parquet) "
                + _("が見つかりません。")
            )

        fp_s_leave = data_dir / "shortage_leave.parquet"
        if fp_s_leave.exists():
            try:
                df_sl = load_data_cached(
                    str(fp_s_leave),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_s_leave),
                )
                if not _valid_df(df_sl):
                    st.info("Data not available")
                    return
                st.write(_("Shortage with Leave"))
                display_sl = df_sl.rename(
                    columns={
                        "time": _("Time"),
                        "date": _("Date"),
                        "lack": _("Shortage Hours"),
                        "leave_applicants": _("Total Leave Days"),
                        "net_shortage": _("Net Shortage"),
                    }
                )
                st.dataframe(display_sl, use_container_width=True, hide_index=True)
            except Exception as e:
                log_and_display_error("shortage_leave.parquet 表示エラー", e)
        else:
            st.info(
                _("Shortage") + " (shortage_leave.parquet) " + _("が見つかりません。")
            )

        fp_cost = data_dir / "cost_benefit.parquet"
        if fp_cost.exists():
            st.markdown("---")
            try:
                df_cost = load_data_cached(
                    str(fp_cost),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_cost),
                )
                if not _valid_df(df_cost):
                    st.info("Data not available")
                    return
                st.write(_("Estimated Cost Impact (Million ¥)"))
                if "Cost_Million" in df_cost:
                    fig_cost = px.bar(
                        df_cost.reset_index(),
                        x=df_cost.index.name or "index",
                        y="Cost_Million",
                        labels={"Cost_Million": _("Estimated Cost Impact (Million ¥)")},
                        title="推定コスト影響",
                    )
                    st.plotly_chart(
                        fig_cost, use_container_width=True, key="short_cost_chart"
                    )
                st.dataframe(df_cost, use_container_width=True)
            except Exception as e:
                log_and_display_error("cost_benefit.parquet 表示エラー", e)

        fp_stats = data_dir / "stats_alerts.parquet"
        if fp_stats.exists():
            try:
                df_alerts = load_data_cached(
                    str(fp_stats),
                    is_parquet=True,
                    file_mtime=_file_mtime(fp_stats),
                )
                if not _valid_df(df_alerts):
                    st.info("Data not available")
                    return
                if not df_alerts.empty:
                    st.markdown("---")
                    st.subheader(_("Alerts"))
                    st.dataframe(df_alerts, use_container_width=True, hide_index=True)
            except Exception as e:
                log_and_display_error("stats_alerts.parquet alerts表示エラー", e)

        display_shortage_factor_section(data_dir)


def display_shortage_factor_section(data_dir: Path) -> None:
    """Train and display shortage factor model."""
    st.markdown("---")
    st.subheader(_("Factor Analysis (AI)"))

    train_key = "train_factor_model_button"
    if st.button(_("Train factor model"), key=train_key, use_container_width=True):
        try:
            heat_df = load_data_cached(
                str(data_dir / "heat_ALL.parquet"),
                is_parquet=True,
                file_mtime=_file_mtime(data_dir / "heat_ALL.parquet"),
            )
            short_df = load_data_cached(
                str(data_dir / "shortage_time.parquet"),
                is_parquet=True,
                file_mtime=_file_mtime(data_dir / "shortage_time.parquet"),
            )
            leave_fp = data_dir / "leave_analysis.csv"
            leave_df = (
                pd.read_csv(leave_fp, parse_dates=["date"])
                if leave_fp.exists()
                else pd.DataFrame()
            )
            analyzer = ShortageFactorAnalyzer()
            features = analyzer.generate_features(
                pd.DataFrame(), heat_df, short_df, leave_df, set()
            )
            model, fi_df = analyzer.train_and_get_feature_importance(features)
            st.session_state.factor_features = features
            st.session_state.factor_model = model
            st.session_state.factor_importance_df = fi_df
            st.success("Model trained")
        except Exception as e:
            log_and_display_error("factor model training error", e)

    fi_df = st.session_state.get("factor_importance_df")
    feat_df = st.session_state.get("factor_features")
    if fi_df is not None and feat_df is not None and not feat_df.empty:
        dates = sorted({idx[0] for idx in feat_df.index})
        slots = sorted({idx[1] for idx in feat_df.index})
        sel_date = st.selectbox(
            _("Select date for factor analysis"),
            dates,
            key="factor_date_select",
        )
        sel_slot = st.selectbox(
            _("Select time slot for factor analysis"),
            slots,
            key="factor_slot_select",
        )
        if (sel_date, sel_slot) in feat_df.index:
            row = feat_df.loc[(sel_date, sel_slot)]
            top = fi_df.head(5)
            st.write(_("Top factors"))
            st.dataframe(top, hide_index=True)
            with st.expander("Feature values"):
                st.dataframe(row[top["feature"].tolist()].to_frame("value"))


def display_over_shortage_log_section(data_dir: Path) -> None:
    """Display editable over/shortage log."""
    st.markdown("---")
    st.subheader(_("Over/Short Log"))

    events = over_shortage_log.list_events(data_dir)
    if events.empty:
        st.info("No shortage/excess data.")
        return

    staff_options: list[str] = []
    fp_staff = data_dir / "staff_stats.parquet"
    if fp_staff.exists():
        try:
            staff_df = pd.read_parquet(fp_staff)
            if "staff" in staff_df.columns:
                staff_options = staff_df["staff"].astype(str).dropna().unique().tolist()
        except Exception:
            staff_options = []

    log_fp = data_dir / "over_shortage_log.csv"
    existing = over_shortage_log.load_log(log_fp)
    merged = events.merge(
        existing,
        on=["date", "time", "type"],
        how="left",
        suffixes=("", "_log"),
    )

    updated_rows = []
    reason_opts = [
        _("Sudden absence"),
        _("Planned leave"),
        _("Training/Meeting"),
        _("Resident response"),
        _("Hiring delay"),
        _("Other"),
    ]

    for idx, row in merged.iterrows():
        st.write(f"{row['date']} {row['time']} [{row['type']}] ({row['count']})")
        reason = st.selectbox(
            _("Reason Category"),
            reason_opts,
            index=reason_opts.index(row["reason"])
            if pd.notna(row.get("reason")) and row["reason"] in reason_opts
            else 0,
            key=f"reason_{idx}",
        )
        staff_sel = st.multiselect(
            _("Related Staff"),
            staff_options,
            default=str(row.get("staff", "")).split(";")
            if pd.notna(row.get("staff")) and str(row.get("staff"))
            else [],
            key=f"staff_{idx}",
        )
        memo = st.text_area(
            _("Memo"),
            value=str(row.get("memo", "")),
            key=f"memo_{idx}",
        )
        updated_rows.append(
            {
                "date": row["date"],
                "time": row["time"],
                "type": row["type"],
                "count": row["count"],
                "reason": reason,
                "staff": ";".join(staff_sel),
                "memo": memo,
            }
        )

    mode = st.radio(_("Save method"), [_("Append"), _("Overwrite")], horizontal=True)
    if st.button(_("Save log")):
        df_save = pd.DataFrame(updated_rows)
        over_shortage_log.save_log(
            df_save,
            log_fp,
            mode="append" if mode == _("Append") else "overwrite",
        )
        st.success(_("Save log"))

    if not existing.empty:
        summary = existing.groupby("reason")["count"].sum().reset_index()
        st.subheader(_("Reason stats"))
        fig = px.bar(
            summary,
            x="reason",
            y="count",
            labels={"reason": _("Reason Category"), "count": _("Count")},
            title="不足理由別件数",
        )
        st.plotly_chart(fig, use_container_width=True)


def display_optimization_tab(tab_container, data_dir):
    """Display staffing optimization metrics."""
    with tab_container:
        st.subheader(_("Optimization Analysis"))

        roles = st.session_state.get("available_roles", [])
        employments = st.session_state.get("available_employments", [])

        # --- UI Controls at the top ---
        c1, c2, c3 = st.columns(3)
        with c1:
            scope_opts = {
                "overall": _("Overall"),
                "role": _("Role"),
                "employment": _("Employment"),
            }
            scope_lbl = st.selectbox(
                "ヒートマップの対象範囲",
                list(scope_opts.values()),
                key="opt_scope",
            )
            scope = [k for k, v in scope_opts.items() if v == scope_lbl][0]

        sel_role = None
        with c2:
            if scope == "role" and roles:
                sel_role = st.selectbox(_("Role"), roles, key="opt_scope_role")

        sel_emp = None
        with c3:
            if scope == "employment" and employments:
                sel_emp = st.selectbox(
                    _("Employment"), employments, key="opt_scope_emp"
                )

        # --- Display data retrieval ---
        base_key = None
        if scope == "overall":
            base_key = "heat_all"
        elif scope == "role" and sel_role:
            base_key = f"heat_role_{safe_sheet(sel_role, for_path=True)}"
        elif scope == "employment" and sel_emp:
            base_key = f"heat_emp_{safe_sheet(sel_emp, for_path=True)}"

        df_surplus = pd.DataFrame()
        df_margin = pd.DataFrame()
        df_score = pd.DataFrame()

        if base_key:
            df_surplus = st.session_state.display_data.get(base_key.replace("heat_", "surplus_"))
            df_margin = st.session_state.display_data.get(base_key.replace("heat_", "margin_"))
            df_score = st.session_state.display_data.get(base_key.replace("heat_", "score_"))

        if not (_valid_df(df_surplus) and _valid_df(df_margin) and _valid_df(df_score)):
            st.warning("選択されたスコープのデータが見つかりません。")
            return

        st.divider()

        # --- Display Heatmaps Vertically ---

        st.markdown("##### 1. 必要人数に対する余剰 (Surplus vs Need)")
        st.info(
            """
            このヒートマップは、各時間帯で**必要人数（need）に対して何人多くスタッフがいたか**を示します。
            - **値が高い（色が濃い）**: 必要人数を大幅に超える人員が配置されており、過剰人員（コスト増）の可能性があります。
            - **値が0**: 必要人数ちょうどか、それ以下の人員しか配置されていません。
            """
        )
        fig_surplus = px.imshow(
            df_surplus,
            aspect="auto",
            color_continuous_scale="Blues",
            labels={"x": _("Date"), "y": _("Time"), "color": _("Surplus vs Need")},
            x=[date_with_weekday(c) for c in df_surplus.columns],
            title="必要人数に対する余剰人員ヒートマップ",
        )
        st.plotly_chart(fig_surplus, use_container_width=True, key="surplus_need_heat")

        st.markdown("##### 2. 上限に対する余白 (Margin to Upper)")
        st.info(
            """
            このヒートマップは、各時間帯で**配置人数の上限（upper）まであと何人の余裕があったか**を示します。
            - **値が高い（色が濃い）**: 上限までまだ余裕があり、追加の人員を受け入れられるキャパシティがあったことを示します。
            - **値が0に近い**: 上限ギリギリで稼働しており、突発的な事態に対応する余裕が少なかったことを示唆します。
            """
        )
        fig_margin = px.imshow(
            df_margin,
            aspect="auto",
            color_continuous_scale="Greens",
            labels={"x": _("Date"), "y": _("Time"), "color": _("Margin vs Upper")},
            x=[date_with_weekday(c) for c in df_margin.columns],
            title="上限人数までの余白ヒートマップ",
        )
        st.plotly_chart(fig_margin, use_container_width=True, key="margin_upper_heat")
        st.info(
            "注: この余白は、過去の実績から算出された上限人数と実際の配置人数の差を示します。"
            "需要が低い日や休業日（例: 日曜日）は、過去のデータに基づく上限値が高めに算出されることで、"
            "見かけ上の余白が大きくなる場合があります。これは、潜在的な過剰人員やコスト発生の可能性を示唆しています。"
        )

        st.markdown("##### 3. 人員配置 最適化スコア")
        st.info(
            """
            このヒートマップは、**人員配置の効率性**を0から1のスコアで示します（1が最も良い）。
            - **スコアが高い（緑色に近い）**: 必要人数（need）を満たしつつ、上限（upper）を超えない、効率的な人員配置ができています。
            - **スコアが低い（赤色に近い）**: 人員不足、または過剰人員が発生しており、改善の余地があることを示します。
            """
        )
        fig_score = px.imshow(
            df_score,
            aspect="auto",
            color_continuous_scale="RdYlGn",
            zmin=0,
            zmax=1,
            labels={"x": _("Date"), "y": _("Time"), "color": _("Optimization Score")},
            x=[date_with_weekday(c) for c in df_score.columns],
            title="最適化スコア ヒートマップ",
        )
        st.plotly_chart(fig_score, use_container_width=True, key="optimization_heat")


def display_fatigue_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Fatigue Score per Staff"))
        display_data = st.session_state.get("display_data", {})
        df = display_data.get("fatigue_score")
        if isinstance(df, pd.DataFrame):
            if not _valid_df(df):
                st.info(_("Data not available or empty"))
                return

            try:
                display_df = df.rename(
                    columns={"staff": _("Staff"), "fatigue_score": _("Score")}
                )
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                if "fatigue_score" in df and "staff" in df:
                    fig_fatigue = px.bar(
                        df,
                        x="staff",
                        y="fatigue_score",
                        labels={"staff": _("Staff"), "fatigue_score": _("Score")},
                        color_discrete_sequence=["#FF8C00"],
                        title="スタッフ別疲労スコア",
                    )
                    st.plotly_chart(
                        fig_fatigue, use_container_width=True, key="fatigue_chart"
                    )
                    fig_fatigue_hist = dashboard.fatigue_distribution(df)
                    fig_fatigue_hist.update_layout(title="疲労スコア分布")
                    st.plotly_chart(
                        fig_fatigue_hist,
                        use_container_width=True,
                        key="fatigue_hist",
                    )
            except AttributeError as e:
                log_and_display_error("Invalid data format in fatigue_score.parquet", e)
            except Exception as e:
                log_and_display_error("fatigue_score.parquet 表示エラー", e)
        else:
            st.info(
                _("Fatigue") + " (fatigue_score.parquet) " + _("が見つかりません。")
            )


def display_forecast_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Demand Forecast (yhat)"))
        display_data = st.session_state.get("display_data", {})
        df_fc = display_data.get("forecast")
        df_actual = display_data.get("demand_series")
        if isinstance(df_fc, pd.DataFrame):
            if not _valid_df(df_fc):
                st.info(_("Forecast data not available or empty"))
                return

            try:
                fig = go.Figure()
                if "ds" in df_fc and "yhat" in df_fc:
                    fig.add_trace(
                        go.Scatter(
                            x=df_fc["ds"],
                            y=df_fc["yhat"],
                            mode="lines+markers",
                            name=_("Demand Forecast (yhat)"),
                        )
                    )
                if isinstance(df_actual, pd.DataFrame):
                    if _valid_df(df_actual) and "ds" in df_actual and "y" in df_actual:
                        fig.add_trace(
                            go.Scatter(
                                x=df_actual["ds"],
                                y=df_actual["y"],
                                mode="lines",
                                name=_("Actual (y)"),
                                line=dict(dash="dash"),
                            )
                        )
                fig.update_layout(
                    title=_("Demand Forecast vs Actual"),
                    xaxis_title=_("Date"),
                    yaxis_title=_("Demand"),
                )
                st.plotly_chart(fig, use_container_width=True, key="forecast_chart")
                with st.expander(_("Display forecast data")):
                    st.dataframe(df_fc, use_container_width=True, hide_index=True)
            except AttributeError as e:
                log_and_display_error("Invalid data format in forecast.parquet", e)
            except Exception as e:
                log_and_display_error("forecast.parquet 表示エラー", e)
        else:
            st.info(_("Forecast") + " (forecast.parquet) " + _("が見つかりません。"))


def display_fairness_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Fairness (Unfairness Score)"))
        display_data = st.session_state.get("display_data", {})
        df = display_data.get("fairness_after")
        if isinstance(df, pd.DataFrame):
            if not _valid_df(df):
                st.info(_("Fairness data not available or empty"))
                return

            try:
                rename_map = {
                    "staff": _("Staff"),
                    "night_ratio": _("Night Shift Ratio"),
                }
                if "unfairness_score" in df.columns:
                    rename_map["unfairness_score"] = _("Unfairness Score")
                if "fairness_score" in df.columns:
                    rename_map["fairness_score"] = _("Fairness Score")
                display_df = df.rename(columns=rename_map)
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                metric_col = (
                    "unfairness_score"
                    if "unfairness_score" in df.columns
                    else (
                        "fairness_score" if "fairness_score" in df.columns else "night_ratio"
                    )
                )
                if "staff" in df and metric_col in df:
                    fig_fair = px.bar(
                        df,
                        x="staff",
                        y=metric_col,
                        labels={
                            "staff": _("Staff"),
                            metric_col: _("Unfairness Score")
                            if metric_col == "unfairness_score"
                            else _("Fairness Score")
                            if metric_col == "fairness_score"
                            else _("Night Shift Ratio"),
                        },
                        color_discrete_sequence=["#FF8C00"],
                    )
                    avg_val = df[metric_col].mean()
                    fig_fair.add_hline(y=avg_val, line_dash="dash", line_color="red")
                    st.plotly_chart(
                        fig_fair, use_container_width=True, key="fairness_chart"
                    )
                    fig_hist = dashboard.fairness_histogram(df, metric=metric_col)
                    fig_hist.add_vline(x=avg_val, line_dash="dash", line_color="red")
                    st.plotly_chart(
                        fig_hist,
                        use_container_width=True,
                        key="fairness_hist",
                    )
                if "unfairness_score" in df.columns:
                    ranking = df.sort_values("unfairness_score", ascending=False)[[
                        "staff",
                        "unfairness_score",
                    ]]
                    ranking.index += 1
                    st.subheader(_("Unfairness Ranking"))
                    st.dataframe(ranking, use_container_width=True)
            except AttributeError as e:
                log_and_display_error(
                    "Invalid data format in fairness_after.parquet", e
                )
            except Exception as e:
                log_and_display_error("fairness_after.parquet 表示エラー", e)
        else:
            st.info(
                _("Fairness") + " (fairness_after.parquet) " + _("が見つかりません。")
            )


def display_cost_tab(tab_container, data_dir):
    with tab_container:
        st.subheader("人件費分析")
        display_data = st.session_state.get("display_data", {})
        df = display_data.get("daily_cost")
        if isinstance(df, pd.DataFrame):
            if not _valid_df(df):
                st.info(_("Cost simulation data not available or empty"))
                return

            try:
                # --- ここからが追加・変更部分 ---
                long_df = st.session_state.get("long_df")

                if (
                    long_df is not None
                    and not long_df.empty
                    and "ds" in long_df.columns
                ):
                    daily_details = (
                        long_df[long_df["parsed_slots_count"] > 0]
                        .assign(date=lambda x: x["ds"].dt.normalize())
                        .groupby("date")
                        .agg(
                            day_of_week=(
                                "ds",
                                lambda x: ["月", "火", "水", "木", "金", "土", "日"][
                                    x.iloc[0].weekday()
                                ],
                            ),
                            total_staff=("staff", "nunique"),
                            role_breakdown=(
                                "role",
                                lambda x: ", ".join(
                                    f"{role}:{count}"
                                    for role, count in x.value_counts().items()
                                ),
                            ),
                            staff_list=(
                                "staff",
                                lambda x: ", ".join(sorted(x.unique())),
                            ),
                        )
                        .reset_index()
                    )

                    def summarize_staff(staff_str, limit=5):
                        staff_list = staff_str.split(", ")
                        if len(staff_list) > limit:
                            return (
                                ", ".join(staff_list[:limit])
                                + f", ...他{len(staff_list) - limit}名"
                            )
                        return staff_str

                    daily_details["staff_list_summary"] = daily_details[
                        "staff_list"
                    ].apply(summarize_staff)

                    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
                    daily_details["date"] = pd.to_datetime(
                        daily_details["date"]
                    ).dt.normalize()

                    df = pd.merge(df, daily_details, on="date", how="left")

                custom_data = [
                    "day_of_week",
                    "total_staff",
                    "role_breakdown",
                    "staff_list_summary",
                ]

                final_custom_data = [col for col in custom_data if col in df.columns]

                hovertemplate = (
                    "<b>%{x|%Y-%m-%d} (%{customdata[0]})</b><br><br>"
                    "コスト: %{y:,.0f}円<br>"
                    "構成人数: %{customdata[1]}人<br>"
                    "職種一覧: %{customdata[2]}<br>"
                    "スタッフ: %{customdata[3]}"
                    "<extra></extra>"
                )

                st.subheader("日別コスト")
                fig_cost = px.bar(
                    df,
                    x="date",
                    y="cost",
                    title="日別発生人件費",
                    custom_data=final_custom_data if final_custom_data else None,
                )
                fig_cost.update_xaxes(tickformat="%m/%d(%a)")

                if final_custom_data:
                    fig_cost.update_traces(hovertemplate=hovertemplate)

                st.plotly_chart(
                    fig_cost, use_container_width=True, key="daily_cost_chart_enhanced"
                )

                # --- 変更ここまで ---

                st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("累計人件費の推移")
                df_sorted = df.sort_values(by="date").copy()
                if "cost" in df_sorted.columns:
                    df_sorted["cumulative_cost"] = df_sorted["cost"].cumsum()
                    fig_cumulative = px.line(
                        df_sorted,
                        x="date",
                        y="cumulative_cost",
                        title="日別累計人件費",
                        labels={"date": "日付", "cumulative_cost": "累計人件費 (円)"},
                        markers=True,
                    )
                    fig_cumulative.update_xaxes(tickformat="%m/%d(%a)")
                    fig_cumulative.update_layout(
                        yaxis_title="累計人件費 (円)",
                        xaxis_title="日付",
                    )
                    st.plotly_chart(
                        fig_cumulative,
                        use_container_width=True,
                        key="cumulative_cost_chart",
                    )

            except Exception as e:
                log_and_display_error("daily_cost.parquet 表示エラー", e)
        else:
            st.info("人件費分析結果ファイルが見つかりません。")


def display_hireplan_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("Hiring Plan (Needed FTE)"))
        display_data = st.session_state.get("display_data", {})
        df_plan = display_data.get("hire_plan")
        if isinstance(df_plan, pd.DataFrame):
            if not _valid_df(df_plan):
                st.info(_("Hiring plan data is empty"))
            else:
                display_plan_df = df_plan.rename(
                    columns={"role": _("Role"), "hire_fte": _("hire_fte")}
                )
                st.dataframe(display_plan_df, use_container_width=True, hide_index=True)
                if "role" in df_plan and "hire_fte" in df_plan:
                    fig_plan = px.bar(
                        df_plan,
                        x="role",
                        y="hire_fte",
                        labels={"role": _("Role"), "hire_fte": _("hire_fte")},
                    )
                    st.plotly_chart(
                        fig_plan, use_container_width=True, key="hireplan_chart"
                    )
        else:
            st.info(
                _("Hiring Plan") + " (hire_plan.parquet) " + _("が見つかりません。")
            )

        # --- 最適採用計画のセクションをここに追加 ---
        st.divider()
        st.subheader("最適採用計画")
        df_optimal = display_data.get("optimal_hire_plan")
        if isinstance(df_optimal, pd.DataFrame):
            st.info("分析の結果、以下の具体的な採用計画を推奨します。")
            st.dataframe(df_optimal, use_container_width=True, hide_index=True)
        else:
            st.info("最適採用計画の分析結果ファイルが見つかりません。")


def display_summary_report_tab(tab_container, data_dir):
    """Show auto-generated shortage summary report."""

    with tab_container:
        st.subheader(_("Summary Report"))
        report_files = sorted(Path(data_dir).glob("OverShortage_SummaryReport_*.md"))
        latest = report_files[-1] if report_files else None

        if st.button(_("Generate Summary Report")):
            try:
                from shift_suite.tasks.report_generator import generate_summary_report

                latest = generate_summary_report(Path(data_dir))
                st.success(_("Report generated"))
            except Exception as e:
                log_and_display_error("summary report generation failed", e)

        if latest and latest.exists():
            md_text = latest.read_text(encoding="utf-8")
            st.markdown(md_text)
            with open(latest, "rb") as f:
                st.download_button(
                    label=_("Download Report (Markdown)"),
                    data=f,
                    file_name=latest.name,
                    mime="text/markdown",
                    use_container_width=True,
                )


def load_leave_results_from_dir(data_dir: Path) -> dict:
    """Wrapper for :func:`dashboard.load_leave_results_from_dir`."""

    return dashboard.load_leave_results_from_dir(data_dir)


def display_leave_analysis_tab(tab_container, results_dict: dict | None = None):
    """Display leave analysis results with interactive charts.

    Parameters
    ----------
    tab_container : Any
        Streamlit tab container.
    results_dict : dict | None
        In-memory results dictionary produced by ``leave_analyzer``.  If ``None``
        the function falls back to ``st.session_state.leave_analysis_results``.
    """

    with tab_container:
        st.subheader(_("Leave Analysis"))

        if results_dict is None:
            results_dict = st.session_state.leave_analysis_results

        leave_df = results_dict.get("daily_summary")

        if not isinstance(leave_df, pd.DataFrame) or leave_df.empty:
            st.info(_("No leave analysis results available."))
            return

        st.dataframe(leave_df, use_container_width=True, hide_index=True)

        staff_balance = results_dict.get("staff_balance_daily")
        if isinstance(staff_balance, pd.DataFrame) and not staff_balance.empty:
            st.subheader("勤務予定人数と全休暇取得者数の推移")
            fig_bal = px.line(
                staff_balance,
                x="date",
                y=["total_staff", "leave_applicants_count", "non_leave_staff"],
                markers=True,
                labels={
                    "date": _("Date"),
                    "value": _("Count"),
                    "variable": _("Metric"),
                    "total_staff": _("Total staff"),
                    "leave_applicants_count": _("Leave applicants"),
                    "non_leave_staff": _("Non-leave staff"),
                },
                title="スタッフバランスの推移",
            )
            fig_bal.update_xaxes(tickformat="%m/%d(%a)")
            st.plotly_chart(
                fig_bal, use_container_width=True, key="staff_balance_chart"
            )
            st.dataframe(staff_balance, use_container_width=True, hide_index=True)

            daily_summary_for_chart = results_dict.get("daily_summary")
            if (
                isinstance(daily_summary_for_chart, pd.DataFrame)
                and not daily_summary_for_chart.empty
            ):
                st.subheader("日別 休暇取得者数（内訳）")
                fig_breakdown = px.bar(
                    daily_summary_for_chart,
                    x="date",
                    y="total_leave_days",
                    color="leave_type",
                    barmode="stack",
                    labels={
                        "date": _("Date"),
                        "total_leave_days": _("Leave applicants"),
                        "leave_type": _("Leave type"),
                    },
                    title="日別 休暇取得者数（内訳）",
                )
                fig_breakdown.update_xaxes(tickformat="%m/%d(%a)")
                st.plotly_chart(
                    fig_breakdown,
                    use_container_width=True,
                    key="daily_leave_breakdown_chart",
                )

        ratio_break = results_dict.get("leave_ratio_breakdown")
        if isinstance(ratio_break, pd.DataFrame) and not ratio_break.empty:
            st.subheader("月初・月中・月末 各曜日の休暇割合")
            fig_ratio_break = px.bar(
                ratio_break,
                x="dayofweek",
                y="leave_ratio",
                color="leave_type",
                facet_col="month_period",
                category_orders={
                    "dayofweek": [
                        "月曜日",
                        "火曜日",
                        "水曜日",
                        "木曜日",
                        "金曜日",
                        "土曜日",
                        "日曜日",
                    ],
                    "month_period": ["月初(1-10日)", "月中(11-20日)", "月末(21-末日)"],
                },
                labels={
                    "dayofweek": _("Day"),
                    "leave_ratio": _("Ratio"),
                    "leave_type": _("Leave type"),
                    "month_period": _("Month period"),
                },
                title="曜日・月期間別休暇取得率",
            )
            st.plotly_chart(
                fig_ratio_break,
                use_container_width=True,
                key="leave_ratio_breakdown_chart",
            )
            st.dataframe(ratio_break, use_container_width=True, hide_index=True)

        daily_summary_for_chart = results_dict.get("daily_summary")
        if (
            isinstance(daily_summary_for_chart, pd.DataFrame)
            and not daily_summary_for_chart.empty
        ):
            st.subheader("休暇タイプ別 取得者数の推移")
            fig_type = px.line(
                daily_summary_for_chart,
                x="date",
                y="total_leave_days",
                color="leave_type",
                markers=True,
                labels={
                    "date": _("Date"),
                    "total_leave_days": _("Leave applicants"),
                    "leave_type": _("Leave type"),
                },
                title="休暇タイプ別 取得者数の推移",
            )
            fig_type.update_xaxes(tickformat="%m/%d(%a)")
            st.plotly_chart(
                fig_type, use_container_width=True, key="leave_type_trend_chart"
            )
            st.dataframe(
                daily_summary_for_chart, use_container_width=True, hide_index=True
            )

        concentration = results_dict.get("concentration_requested")
        if isinstance(concentration, pd.DataFrame) and not concentration.empty:
            conc_df = concentration.copy()

            st.subheader(_("Leave concentration graphs"))
            st.info(
                "下のグラフの◇マーカー（閾値超過日）をクリックすると、該当日に休暇を申請した職員を確認できます。複数日のクリックで対象を追加・解除できます。"
            )

            fig_conc = go.Figure()
            fig_conc.add_trace(
                go.Scatter(
                    x=conc_df["date"],
                    y=conc_df["leave_applicants_count"],
                    mode="lines+markers",
                    name=_("Leave applicants"),
                    line=dict(shape="spline", smoothing=0.5),
                    marker=dict(size=6),
                )
            )

            focused_mask = conc_df.get("is_concentrated")
            focused_df = (
                conc_df[focused_mask] if focused_mask is not None else pd.DataFrame()
            )
            if not focused_df.empty:
                fig_conc.add_trace(
                    go.Scatter(
                        x=focused_df["date"],
                        y=focused_df["leave_applicants_count"],
                        mode="markers",
                        marker=dict(color="red", size=12, symbol="diamond"),
                        name=_("Exceeds threshold"),
                        hoverinfo="text",
                        text=[
                            f"<b>{row['date'].strftime('%Y-%m-%d')}</b><br>申請者: {row['leave_applicants_count']}人<br>氏名: {', '.join(row['staff_names'])}"
                            for _, row in focused_df.iterrows()
                        ],
                    )
                )

            fig_conc.update_layout(
                title="希望休 申請者数の推移と集中日",
                xaxis_title="日付",
                yaxis_title="申請者数",
            )
            fig_conc.update_xaxes(tickformat="%m/%d(%a)")

            if plotly_events:
                selected_points = plotly_events(
                    fig_conc, click_event=True, key="leave_conc_events"
                )
            else:
                st.plotly_chart(fig_conc, use_container_width=True)
                selected_points = []

            if "selected_leave_dates" not in st.session_state:
                st.session_state.selected_leave_dates = set()

            for point in selected_points:
                try:
                    clicked_date = pd.to_datetime(point["x"]).normalize()
                    if clicked_date in st.session_state.selected_leave_dates:
                        st.session_state.selected_leave_dates.remove(clicked_date)
                    else:
                        st.session_state.selected_leave_dates.add(clicked_date)
                except Exception as e:
                    log.debug(f"クリックイベントの処理中にエラー: {e}")

            if st.button("選択をクリア"):
                st.session_state.selected_leave_dates.clear()
                st.rerun()

            selected_dates = sorted(list(st.session_state.selected_leave_dates))
            if selected_dates:
                st.markdown("---")
                st.markdown("##### 選択された集中日の休暇申請者")

                all_names_in_selection = []
                for selected_date in selected_dates:
                    names_series = conc_df.loc[
                        conc_df["date"] == selected_date, "staff_names"
                    ]
                    if not names_series.empty and isinstance(
                        names_series.iloc[0], list
                    ):
                        names_list = names_series.iloc[0]
                        st.markdown(
                            f"**{selected_date.strftime('%Y-%m-%d')}**: {', '.join(names_list)}"
                        )
                        all_names_in_selection.extend(names_list)

                if all_names_in_selection:
                    st.markdown("##### 選択範囲内での申請回数")
                    name_counts = (
                        pd.Series(all_names_in_selection).value_counts().reset_index()
                    )
                    name_counts.columns = ["職員名", "申請回数"]
                    st.dataframe(name_counts, use_container_width=True, hide_index=True)


def display_gap_analysis_tab(tab_container, data_dir):
    with tab_container:
        st.subheader(_("基準乖離分析"))
        if "gap_analysis_results" in st.session_state:
            results = st.session_state.gap_analysis_results
            st.info(
                "「実態の必要人数」と「基準の必要人数」の差分を示します。値がプラスの場合、基準よりも多くの人員が実態として必要だったことを意味します。"
            )
            st.write("#### 職種別 月間総乖離時間")
            st.dataframe(results["gap_summary"])
            st.write("#### 時間帯・職種別 乖離ヒートマップ")
            fig = px.imshow(
                results["gap_heatmap"],
                aspect="auto",
                color_continuous_scale="RdBu_r",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("解析結果がありません。")


def display_mind_reader_tab(tab_container, data_dir: Path) -> None:
    """Display the Mind Reader analysis tab."""
    with tab_container:
        st.subheader("🧠 シフト作成思考プロセス解読")

        if "mind_reader_results" not in st.session_state:
            if st.button("思考プロセスを解読する"):
                with st.spinner("思考を解読中..."):
                    engine = AdvancedBlueprintEngineV2()
                    long_df = st.session_state.get("long_df")
                    if long_df is not None and not long_df.empty:
                        results = engine.run_full_blueprint_analysis(long_df)
                        st.session_state.mind_reader_results = results["mind_reading"]
                        st.rerun()
                    else:
                        st.error("分析の元となる勤務データが見つかりません。")
        else:
            results = st.session_state.mind_reader_results

        # results変数の安全性確保
        if 'results' not in locals() or results is None:
            results = {}

        st.markdown("#### 優先順位（判断基準の重要度）")
        st.info(
            "作成者が無意識にどの項目を重視しているかを数値化したものです。絶対値が大きいほど重要です。"
        )
        importance_df = results.get("feature_importance") if results else None
        if importance_df is not None:
            st.dataframe(importance_df)

        st.markdown("#### 思考フローチャート（決定木）")
        st.info(
            "「誰を配置するか」という判断の分岐を模倣したものです。上にある分岐ほど、優先的に考慮されています。"
        )
        tree_model = results.get("thinking_process_tree") if results else None
        if tree_model:
            fig, _ = plt.subplots(figsize=(20, 10))
            plot_tree(
                tree_model,
                filled=True,
                feature_names=getattr(tree_model, "feature_names_in_", None),
                class_names=True,
                max_depth=3,
                fontsize=10,
            )
            st.pyplot(fig)

        st.markdown("#### トレードオフ分析")
        st.info(
            "横軸と縦軸の指標の間で、作成者がどのようなバランスを取ってきたかを示します。"
        )
        trade_off_df = results.get("trade_offs") if results else None
        if trade_off_df is not None and not trade_off_df.empty:
            fig = px.scatter(
                trade_off_df,
                x="total_cost",
                y="fairness_score",
                title="コスト vs 公平性 トレードオフ",
            )
            st.plotly_chart(fig, use_container_width=True)


def display_ppt_tab(tab_container, data_dir_ignored, key_prefix: str = ""):
    with tab_container:
        st.subheader(_("PPT Report"))
        button_key = f"dash_generate_ppt_button_{key_prefix or 'default'}"
        if st.button(
            _("Generate PowerPoint Report (β)"),
            key=button_key,
            use_container_width=True,
        ):
            st.info(_("Generating PowerPoint report..."))
            try:
                from shift_suite.tasks.ppt import build_ppt

                ppt_path = build_ppt(data_dir_ignored)
                with open(ppt_path, "rb") as ppt_file_data_dash:
                    st.download_button(
                        label=_("Download Report (PPTX)"),
                        data=ppt_file_data_dash,
                        file_name=f"ShiftSuite_Report_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
                Path(ppt_path).unlink(missing_ok=True)
                st.success(_("PowerPoint report ready."))
            except ImportError as e:
                log_and_display_error("python-pptx library required for PPT", e)
            except Exception as e_ppt_dash:
                log_and_display_error(
                    _("Error generating PowerPoint report"), e_ppt_dash
                )
        else:
            st.markdown(_("Click button to generate report."))


# Multi-file results display の直前に追加
if st.session_state.get("analysis_done", False):
    with st.expander("🔍 ダッシュボードデバッグ情報", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**セッションステート状況:**")
            st.write(f"- analysis_done: {st.session_state.get('analysis_done', False)}")
            st.write(
                f"- out_dir_path_str: {st.session_state.get('out_dir_path_str', 'None')}"
            )
            st.write(
                f"- analysis_results件数: {len(st.session_state.get('analysis_results', {}))}"
            )
            st.write(
                f"- display_data件数: {len(st.session_state.get('display_data', {}))}"
            )

        with col2:
            st.write("**利用可能なdisplay_dataキー:**")
            display_keys = list(st.session_state.get("display_data", {}).keys())
            if display_keys:
                for key in display_keys:
                    data = st.session_state.display_data[key]
                    if hasattr(data, "shape"):
                        st.write(f"- {key}: {data.shape}")
                    else:
                        st.write(f"- {key}: {type(data).__name__}")
            else:
                st.write("データが読み込まれていません")

        if st.button("🔄 display_dataを強制更新"):
            st.session_state.display_data = {}
            st.rerun()

# Multi-file results display
if st.session_state.get("analysis_done", False) and st.session_state.analysis_results:
    st.divider()
    file_tabs = st.tabs(list(st.session_state.analysis_results.keys()))
    for tab_obj, fname in zip(file_tabs, st.session_state.analysis_results.keys()):
        with tab_obj:
            results = st.session_state.analysis_results[fname]
            log.debug("Display results for %s: type=%s", fname, type(results))
            st.subheader(_("Results for {fname}").format(fname=fname))
            out_dir_path = (
                results.get("out_dir_path_str") if isinstance(results, dict) else None
            )
            if not out_dir_path:
                if fname == "preview" and isinstance(results, pd.DataFrame):
                    st.dataframe(results, use_container_width=True)
                else:
                    st.error(
                        _("Output directory not found for {fname}").format(fname=fname)
                    )
                    log.warning(
                        "Missing out_dir_path_str for results '%s': %s", fname, results
                    )
                continue
            data_dir = Path(out_dir_path)
            tab_keys_en_dash = [
                "Mind Reader",
                "Overview",
                "Heatmap",
                "Shortage",
                "Optimization Analysis",
                "Fatigue",
                "Forecast",
                "Fairness",
                "Leave Analysis",
                "基準乖離分析",
                "Cost Analysis",
                "Hire Plan",
                "Summary Report",
                "PPT Report",
            ]
            tab_labels_dash = [_(key) for key in tab_keys_en_dash]
            inner_tabs = st.tabs(tab_labels_dash)
            tab_func_map_dash = {
                "Mind Reader": display_mind_reader_tab,
                "Overview": display_overview_tab,
                "Heatmap": display_heatmap_tab,
                "Shortage": display_shortage_tab,
                "Optimization Analysis": display_optimization_tab,
                "Fatigue": display_fatigue_tab,
                "Forecast": display_forecast_tab,
                "Fairness": display_fairness_tab,
                "Leave Analysis": display_leave_analysis_tab,
                "基準乖離分析": display_gap_analysis_tab,
                "Cost Analysis": display_cost_tab,
                "Hire Plan": display_hireplan_tab,
                "Summary Report": display_summary_report_tab,
                "PPT Report": display_ppt_tab,
            }
            for i, key in enumerate(tab_keys_en_dash):
                if key in tab_func_map_dash:
                    if key == "PPT Report":
                        tab_func_map_dash[key](
                            inner_tabs[i], data_dir, key_prefix=fname
                        )
                    elif key == "Leave Analysis":
                        tab_func_map_dash[key](
                            inner_tabs[i], results.get("leave_analysis_results") if results else None
                        )
                    else:
                        tab_func_map_dash[key](inner_tabs[i], data_dir)


st.divider()
st.header(_("Dashboard (Upload ZIP)"))
zip_file_uploaded_dash_final_v3_display_main_dash = st.file_uploader(
    _("Upload ZIP file of 'out' folder"),
    type=["zip"],
    key="dashboard_zip_uploader_widget_final_v3_key_dash",
)

if zip_file_uploaded_dash_final_v3_display_main_dash:
    dashboard_temp_base = Path(tempfile.gettempdir()) / "ShiftSuite_Dash_Uploads"
    dashboard_temp_base.mkdir(parents=True, exist_ok=True)
    current_dash_tmp_dir = Path(
        tempfile.mkdtemp(prefix="dash_", dir=dashboard_temp_base)
    )
    log.info(f"ダッシュボード用一時ディレクトリを作成: {current_dash_tmp_dir}")
    extracted_data_dir: Optional[Path] = None
    try:
        with zipfile.ZipFile(
            io.BytesIO(zip_file_uploaded_dash_final_v3_display_main_dash.read())
        ) as zf:
            base_resolved = current_dash_tmp_dir.resolve()
            for file_name in zf.namelist():
                dest_path = (current_dash_tmp_dir / file_name).resolve()
                if not dest_path.is_relative_to(base_resolved):
                    st.error(_("Invalid path in ZIP file."))
                    log.warning(f"ZIP展開中に不正なパスを検出: {file_name}")
                    st.stop()
                zf.extract(file_name, current_dash_tmp_dir)
            if (current_dash_tmp_dir / "out").exists() and (
                current_dash_tmp_dir / "out" / "heat_ALL.parquet"
            ).exists():
                extracted_data_dir = current_dash_tmp_dir / "out"
            elif (current_dash_tmp_dir / "heat_ALL.parquet").exists():
                extracted_data_dir = current_dash_tmp_dir
            else:
                found_heat_all = list(current_dash_tmp_dir.rglob("heat_ALL.parquet"))
                if found_heat_all:
                    extracted_data_dir = found_heat_all[0].parent
                else:
                    log_and_display_error(
                        _("heat_ALL.parquet not found in ZIP"),
                        FileNotFoundError("heat_ALL.parquet"),
                    )
                    log.error(
                        f"ZIP展開後、heat_ALL.parquet が見つかりません in {current_dash_tmp_dir}"
                    )
                    st.stop()
        log.info(f"ダッシュボード表示用のデータディレクトリ: {extracted_data_dir}")
    except Exception as e_zip:
        log_and_display_error(_("Error during ZIP file extraction"), e_zip)
        log.error(f"ZIP展開中エラー: {e_zip}", exc_info=True)
        st.stop()

    import plotly.express as px
    import plotly.graph_objects as go

    tab_keys_en_dash = [
        "Mind Reader",
        "Overview",
        "Heatmap",
        "Shortage",
        "Optimization Analysis",
        "Fatigue",
        "Forecast",
        "Fairness",
        "Leave Analysis",
        "基準乖離分析",
        "Cost Analysis",
        "Hire Plan",
        "Summary Report",
        "PPT Report",
    ]
    tab_labels_dash = [_(key) for key in tab_keys_en_dash]
    tabs_obj_dash = st.tabs(tab_labels_dash)

    if extracted_data_dir:
        tab_function_map_dash = {
            "Mind Reader": display_mind_reader_tab,
            "Overview": display_overview_tab,
            "Heatmap": display_heatmap_tab,
            "Shortage": display_shortage_tab,
            "Optimization Analysis": display_optimization_tab,
            "Fatigue": display_fatigue_tab,
            "Forecast": display_forecast_tab,
            "Fairness": display_fairness_tab,
            "Leave Analysis": display_leave_analysis_tab,
            "基準乖離分析": display_gap_analysis_tab,
            "Cost Analysis": display_cost_tab,
            "Hire Plan": display_hireplan_tab,
            "Summary Report": display_summary_report_tab,
            "PPT Report": display_ppt_tab,
        }

        # 各タブに対応する表示関数を呼び出す
        for i, tab_key in enumerate(tab_keys_en_dash):
            if tab_key in tab_function_map_dash:
                if tab_key == "PPT Report":
                    tab_function_map_dash[tab_key](
                        tabs_obj_dash[i], extracted_data_dir, key_prefix="zip"
                    )
                elif tab_key == "Leave Analysis":
                    leave_results_zip = load_leave_results_from_dir(extracted_data_dir)
                    tab_function_map_dash[tab_key](tabs_obj_dash[i], leave_results_zip)
                else:
                    tab_function_map_dash[tab_key](tabs_obj_dash[i], extracted_data_dir)
            else:
                with tabs_obj_dash[i]:
                    st.subheader(_(tab_key))
                    st.info(f"{_(tab_key)} の表示は現在準備中です。")

        st.success("✅ 分析が完了しました！")
        st.info("以下のリンクをクリックすると、結果を高速ビューアで快適に閲覧できます。")
        st.markdown(
            "### [📈 分析結果を高速ビューアで表示する](http://127.0.0.1:8050)",
            unsafe_allow_html=True,
        )
        st.caption(
            "（注意: 上記リンクを利用するには、事前に別のターミナルで `python dash_app.py` を実行してビューアを起動しておく必要があります）"
        )
        if st.button("高速ビューアを起動する"):
            try:
                subprocess.Popen(["python", "dash_app.py"])
                st.toast(
                    "ビューアを新しいプロセスで起動しました。ブラウザで http://127.0.0.1:8050 を開いてください。"
                )
            except Exception as e:
                st.error(f"ビューアの起動に失敗しました: {e}")
    else:
        st.warning(
            "ダッシュボードを表示するためのデータがロードされていません。ZIPファイルをアップロードしてください。"
        )

if __name__ == "__main__" and not st_runtime_exists():
    import argparse

    log.info("CLIモードでapp.pyを実行します。")
    parser = argparse.ArgumentParser(
        description="Shift-Suite CLI (app.py経由のデバッグ用)"
    )
    parser.add_argument("xlsx_file_cli", help="Excel シフト原本 (.xlsx)")
    parser.add_argument(
        "--sheets_cli", nargs="+", required=True, help="解析対象のシート名"
    )
    parser.add_argument(
        "--header_cli", type=int, default=3, help="ヘッダー開始行 (1-indexed)"
    )
    try:
        cli_args = parser.parse_args()
        log.info(
            f"CLI Args: file='{cli_args.xlsx_file_cli}', sheets={cli_args.sheets_cli}, header={cli_args.header_cli}"
        )
    except SystemExit:
        pass
    except Exception as e_cli:
        log.error(f"CLIモードでの実行中にエラー: {e_cli}", exc_info=True)
