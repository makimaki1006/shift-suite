# dash_app.py - Shift-Suite高速分析ビューア (app.py機能完全再現版)
import base64
import io
import json
import logging
import tempfile
import zipfile
import threading
import time
import weakref
import os
from dash import State  # セッションサポート用
from session_integration import session_integration, session_aware_data_get, session_aware_save_data

# Import modularized components
from dash_core import (
    create_standard_datatable, create_metric_card, create_standard_graph,
    create_loading_component, ManagedCache, DATA_CACHE, check_memory_usage,
    cleanup_memory, safe_session_data_get, safe_session_data_save
)
from dash_analysis_tabs import create_overview_tab, create_heatmap_tab, create_shortage_tab, create_optimization_tab
from dash_tabs_extended import (
    create_leave_analysis_tab, create_cost_analysis_tab, create_hire_plan_tab,
    create_fatigue_tab, create_forecast_tab, create_fairness_tab,
    create_turnover_prediction_tab, create_gap_analysis_tab, create_summary_report_tab,
    create_individual_analysis_tab, create_team_analysis_tab, create_blueprint_analysis_tab,
    create_ai_analysis_tab
)

# Import missing UI functions
from dash_missing_functions import (
    create_overview_section, create_kpi_cards, create_chart_section,
    create_analysis_section, create_info_card
)

# Safe pickle loading wrapper
def safe_pickle_load(file_path, allowed_classes=None):
    """Safely load pickle files with restricted classes"""
    import pickle
    import io

    class RestrictedUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            # Only allow specific safe classes
            if allowed_classes:
                if (module, name) in allowed_classes:
                    return super().find_class(module, name)
            # Default safe classes
            safe_modules = ['numpy', 'pandas', 'builtins']
            if module in safe_modules:
                return super().find_class(module, name)
            raise pickle.UnpicklingError(f"Unsafe class: {module}.{name}")

    with open(file_path, 'rb') as f:
        return RestrictedUnpickler(f).load()


# Enhanced Session Manager for multi-tenant support
from enhanced_session_manager import enhanced_session_manager
try:
    import psutil
except ImportError:
    psutil = None  # psutilが利用できない場合はNoneに設定
from functools import lru_cache, wraps
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import OrderedDict
import unicodedata

from datetime import datetime

import dash
import dash_cytoscape as cyto
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from flask import jsonify
import traceback
import gc

# エラー境界インポート
from error_boundary import error_boundary, safe_callback, safe_component, apply_error_boundaries
# グローバルエラーハンドリングインポート
from global_error_handler import GlobalErrorHandler, global_error_handler, safe_data_operation, error_handler
# アクセシブルカラーインポート（エラーハンドリング付き）
try:
    from accessible_colors import (
        get_accessible_color_palette, apply_accessible_colors_to_figure, 
        enhance_figure_accessibility, safe_colors_for_plotly, ACCESSIBLE_COLORS
    )
except ImportError:
    # accessible_colorsモジュールが存在しない場合のフォールバック
    def get_accessible_color_palette(palette_type, n_colors):
        """アクセシブルカラーパレットのフォールバック実装"""
        # 色覚多様性に配慮したカラーパレット
        base_colors = [
            '#2E86AB',  # 青
            '#F24236',  # 赤
            '#F6AE2D',  # 黄
            '#2F4858',  # 濃紺
            '#86BBD8',  # 薄青
            '#F26419',  # オレンジ
            '#33658A',  # 藍色
            '#758E4F',  # 緑
            '#8B5A3C',  # 茶
            '#6B2737',  # ワインレッド
            '#C1666B',  # ピンク
            '#48A9A6',  # ターコイズ
        ]
        # 必要な色数に合わせて拡張
        colors = base_colors * ((n_colors // len(base_colors)) + 1)
        return colors[:n_colors]
    
    def enhance_figure_accessibility(fig, title, chart_type):
        """グラフのアクセシビリティ強化のフォールバック実装"""
        return fig
    
    # デフォルトカラー定義
    ACCESSIBLE_COLORS = {
        'primary': '#2E86AB',
        'secondary': '#F24236',
        'success': '#4CAF50',
        'warning': '#F6AE2D',
        'danger': '#F44336'
    }
# メモリガードインポート（改善版）
from improved_memory_guard import ImprovedMemoryGuard, ManagedCache, memory_guard, check_memory_usage, get_memory_report, with_memory_limit

from shift_suite.tasks.utils import safe_read_excel, gen_labels, _valid_df
from shift_suite.tasks.shortage_factor_analyzer import ShortageFactorAnalyzer
from shift_suite.tasks import over_shortage_log
from shift_suite.tasks.daily_cost import calculate_daily_cost
from shift_suite.tasks import leave_analyzer
from shift_suite.tasks.shortage import shortage_and_brief  # 統一された計算メソッド
from shift_suite.tasks.constants import SLOT_HOURS, WAGE_RATES, COST_PARAMETERS, DEFAULT_SLOT_MINUTES, STATISTICAL_THRESHOLDS, SUMMARY5
from shift_suite.tasks.shift_mind_reader import ShiftMindReader
from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2

# ログ初期化（早期実行）
log = logging.getLogger(__name__)

# 新しいデータフロー専用モジュール（一時的に無効化）
data_ingestion = None  # クリーンなUIのため無効化
# try:
#     from dash_components.data_ingestion import data_ingestion
#     log.info("データ入稿モジュールを正常に読み込みました")
# except ImportError as e:
#     log.warning(f"データ入稿モジュールの読み込みに失敗: {e}")
#     data_ingestion = None

# 新しい統一進捗管理システムを優先的に使用
try:
    from progress_manager import progress_manager, start_processing, start_step, update_progress, complete_step, fail_step
    processing_monitor = progress_manager  # 互換性のため
    log.info("新しい統一進捗管理システムを正常に読み込みました")
    
    # パフォーマンス改善とフィードバック改善モジュール
    from performance_utils import performance, cached_data_load
    from upload_feedback import upload_feedback
    log.info("パフォーマンス改善モジュールを読み込みました")
    
    # UI改善モジュール
    try:
        from ui_improvements import ui_improvements
        from graph_improvements import graph_improvements
        log.info("UI改善モジュールを正常に読み込みました")
    except ImportError:
        ui_improvements = None
        graph_improvements = None
        log.warning("UI改善モジュールの読み込みに失敗")
        
except ImportError:
    # フォールバック: 従来のシステムを使用
    try:
        from dash_components.processing_monitor import processing_monitor, start_processing, start_step, update_progress, complete_step, fail_step
        progress_manager = processing_monitor  # 互換性のため
        log.info("従来の処理監視モジュールを使用")
    except ImportError as e:
        log.warning(f"処理監視モジュールの読み込みに失敗: {e}")
        processing_monitor = None
        progress_manager = None
        # ダミー関数を定義
        start_processing = lambda: None
        start_step = lambda *args, **kwargs: None
        update_progress = lambda *args, **kwargs: None
        complete_step = lambda *args, **kwargs: None
        fail_step = lambda *args, **kwargs: None

try:
    from dash_components.analysis_engine import OptimizedAnalysisEngine, performance_monitor
    analysis_engine = OptimizedAnalysisEngine()
    log.info("最適化分析エンジンを正常に読み込みました")
except ImportError as e:
    log.warning(f"最適化分析エンジンの読み込みに失敗: {e}")
    analysis_engine = None

# 分析ダッシュボード
try:
    from shift_suite.tasks.analysis_dashboard import ComprehensiveAnalysisDashboard, get_analysis_dashboard, quick_analysis_check
    log.info("分析ダッシュボードを正常に読み込みました")
except ImportError as e:
    log.warning(f"分析ダッシュボードの読み込みに失敗: {e}")
    ComprehensiveAnalysisDashboard = None

# 統合ダッシュボード
try:
    from shift_suite.tasks.comprehensive_dashboard import (
        ComprehensiveDashboard, create_comprehensive_dashboard, 
        TimeSeriesDataModel, AdvancedAnalyticsEngine, IntegratedVisualizationSystem
    )
    log.info("統合ダッシュボードを正常に読み込みました")
except ImportError as e:
    log.warning(f"統合ダッシュボードの読み込みに失敗: {e}")
    ComprehensiveDashboard = None

try:
    from dash_components.memory_manager import memory_manager, smart_cache, start_memory_monitoring
    log.info("メモリ管理システムを正常に読み込みました")
    # メモリ監視を開始
    start_memory_monitoring()
except ImportError as e:
    log.warning(f"メモリ管理システムの読み込みに失敗: {e}")
    memory_manager = None
    smart_cache = None

try:
    from dash_components.visualization_engine import visualization_engine, create_responsive_figure, create_progress_display, create_dashboard_grid
    log.info("可視化エンジンを正常に読み込みました")
except ImportError as e:
    log.warning(f"可視化エンジンの読み込みに失敗: {e}")
    visualization_engine = None

# 不足分析専用ログ
try:
    from shortage_logger import setup_shortage_dashboard_logger
    shortage_dash_log = setup_shortage_dashboard_logger()
except Exception as e:
    shortage_dash_log = logging.getLogger(__name__)  # フォールバック

def unified_error_display(message: str, error_type: str = "error") -> html.Div:
    """app.pyと統一されたエラー表示（Streamlitのst.error相当をDashで実現）"""
    color_map = {
        'error': '#d32f2f',
        'warning': '#f57c00',
        'success': '#388e3c',
        'info': '#1976d2'
    }
    
    return html.Div([
        html.Strong(f"{error_type.upper()}: "),
        html.Span(message)
    ], style={
        'padding': '10px',
        'borderRadius': '4px',
        'backgroundColor': f"{color_map.get(error_type, '#d32f2f')}15",
        'border': f"1px solid {color_map.get(error_type, '#d32f2f')}",
        'color': color_map.get(error_type, '#d32f2f'),
        'margin': '10px 0'
    })


def create_dashboard_analysis_report(scenario_dir: Path, analysis_type: str = "DASHBOARD") -> Path:
    """ダッシュボード分析結果のタイムスタンプ付きレポートを作成"""
    import datetime as dt
    
    timestamp = dt.datetime.now().strftime("%Y年%m月%d日%H時%M分")
    log_filename = f"{timestamp}_ダッシュボード分析レポート_{analysis_type}.txt"
    log_filepath = scenario_dir / log_filename
    
    try:
        with open(log_filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== ダッシュボード分析結果レポート ===\n")
            f.write(f"生成日時: {timestamp}\n")
            f.write(f"分析タイプ: {analysis_type}\n")
            f.write(f"シナリオディレクトリ: {scenario_dir}\n")
            f.write("=" * 50 + "\n\n")
            
            # 1. 基本情報
            f.write("【1. 基本情報】\n")
            basic_info = collect_dashboard_basic_info(scenario_dir)
            f.write(f"  シナリオ名: {basic_info.get('scenario_name', 'N/A')}\n")
            f.write(f"  対象期間: {basic_info.get('date_range', 'N/A')}\n")
            f.write(f"  職種数: {basic_info.get('total_roles', 0)}種類\n")
            f.write(f"  雇用形態数: {basic_info.get('total_employments', 0)}種類\n")
            f.write(f"  分析日時: {basic_info.get('analysis_datetime', 'N/A')}\n\n")
            
            # 2. 概要KPI
            f.write("【2. 概要KPI】\n")
            overview_kpis = collect_dashboard_overview_kpis(scenario_dir)
            f.write(f"  総不足時間: {overview_kpis.get('total_shortage_hours', 0):.2f}時間\n")
            f.write(f"  総過剰時間: {overview_kpis.get('total_excess_hours', 0):.2f}時間\n")
            f.write(f"  平均疲労スコア: {overview_kpis.get('avg_fatigue_score', 0):.2f}\n")
            f.write(f"  公平性スコア: {overview_kpis.get('fairness_score', 0):.2f}\n")
            f.write(f"  休暇取得率: {overview_kpis.get('leave_ratio', 0):.2%}\n")
            f.write(f"  推定人件費: ¥{overview_kpis.get('estimated_cost', 0):,.0f}\n\n")
            
            # 3. 職種別分析
            f.write("【3. 職種別分析】\n")
            role_analysis = collect_dashboard_role_analysis(scenario_dir)
            if role_analysis:
                f.write("  職種名             | 不足時間 | 過剰時間 | 疲労度 | 公平性 | 総人数\n")
                f.write("  " + "-" * 70 + "\n")
                for role in role_analysis:
                    role_name = str(role.get('role', 'N/A'))[:15].ljust(15)
                    shortage = role.get('shortage_hours', 0)
                    excess = role.get('excess_hours', 0)
                    fatigue = role.get('avg_fatigue', 0)
                    fairness = role.get('fairness_score', 0)
                    staff_count = role.get('staff_count', 0)
                    f.write(f"  {role_name} | {shortage:8.1f} | {excess:8.1f} | {fatigue:6.2f} | {fairness:6.2f} | {staff_count:6d}\n")
            else:
                f.write("  職種別データなし\n")
            f.write("\n")
            
            # 4. 雇用形態別分析
            f.write("【4. 雇用形態別分析】\n")
            emp_analysis = collect_dashboard_employment_analysis(scenario_dir)
            if emp_analysis:
                f.write("  雇用形態           | 不足時間 | 過剰時間 | 平均時給 | 総コスト\n")
                f.write("  " + "-" * 60 + "\n")
                for emp in emp_analysis:
                    emp_name = str(emp.get('employment', 'N/A'))[:15].ljust(15)
                    shortage = emp.get('shortage_hours', 0)
                    excess = emp.get('excess_hours', 0)
                    avg_wage = emp.get('avg_wage', 0)
                    total_cost = emp.get('total_cost', 0)
                    f.write(f"  {emp_name} | {shortage:8.1f} | {excess:8.1f} | ¥{avg_wage:7.0f} | ¥{total_cost:8.0f}\n")
            else:
                f.write("  雇用形態別データなし\n")
            f.write("\n")
            
            # 5. ブループリント分析
            f.write("【5. ブループリント分析】\n")
            blueprint_analysis = collect_dashboard_blueprint_analysis(scenario_dir)
            if blueprint_analysis:
                f.write(f"  分析実行済み: {blueprint_analysis.get('executed', False)}\n")
                f.write(f"  検出パターン数: {blueprint_analysis.get('pattern_count', 0)}個\n")
                f.write(f"  推奨改善案数: {blueprint_analysis.get('recommendation_count', 0)}個\n")
                f.write(f"  効率化可能時間: {blueprint_analysis.get('efficiency_hours', 0):.1f}時間\n")
                
                patterns = blueprint_analysis.get('patterns', [])
                if patterns:
                    f.write("  検出パターン:\n")
                    for i, pattern in enumerate(patterns[:5], 1):  # 最初の5つのみ
                        f.write(f"    {i}. {pattern}\n")
                
                recommendations = blueprint_analysis.get('recommendations', [])
                if recommendations:
                    f.write("  推奨改善案:\n")
                    for i, rec in enumerate(recommendations[:5], 1):  # 最初の5つのみ
                        f.write(f"    {i}. {rec}\n")
            else:
                f.write("  ブループリント分析未実行\n")
            f.write("\n")
            
            # 6. 休暇分析
            f.write("【6. 休暇分析】\n")
            leave_analysis = collect_dashboard_leave_analysis(scenario_dir)
            if leave_analysis:
                f.write(f"  総休暇日数: {leave_analysis.get('total_leave_days', 0):.0f}日\n")
                f.write(f"  有給取得率: {leave_analysis.get('paid_leave_ratio', 0):.1%}\n")
                f.write(f"  希望休取得率: {leave_analysis.get('requested_leave_ratio', 0):.1%}\n")
                f.write(f"  集中日数: {leave_analysis.get('concentration_days', 0)}日\n")
                
                monthly_trends = leave_analysis.get('monthly_trends', [])
                if monthly_trends:
                    f.write("  月別休暇傾向:\n")
                    for trend in monthly_trends[:6]:  # 最初の6ヶ月
                        month = trend.get('month', 'N/A')
                        days = trend.get('leave_days', 0)
                        f.write(f"    {month}: {days:.0f}日\n")
            else:
                f.write("  休暇分析データなし\n")
            f.write("\n")
            
            # 7. コスト分析
            f.write("【7. コスト分析】\n")
            cost_analysis = collect_dashboard_cost_analysis(scenario_dir)
            if cost_analysis:
                f.write(f"  総人件費: ¥{cost_analysis.get('total_cost', 0):,.0f}\n")
                f.write(f"  日平均コスト: ¥{cost_analysis.get('daily_avg_cost', 0):,.0f}\n")
                f.write(f"  時間単価平均: ¥{cost_analysis.get('avg_hourly_rate', 0):.0f}\n")
                f.write(f"  コスト効率指数: {cost_analysis.get('cost_efficiency', 0):.2f}\n")
                
                cost_breakdown = cost_analysis.get('breakdown_by_role', [])
                if cost_breakdown:
                    f.write("  職種別コスト内訳:\n")
                    for breakdown in cost_breakdown[:5]:  # 上位5職種
                        role = breakdown.get('role', 'N/A')
                        cost = breakdown.get('cost', 0)
                        ratio = breakdown.get('ratio', 0)
                        f.write(f"    {role}: ¥{cost:,.0f} ({ratio:.1%})\n")
            else:
                f.write("  コスト分析データなし\n")
            f.write("\n")
            
            # 8. 推奨アクション
            f.write("【8. 推奨アクション】\n")
            recommendations = generate_dashboard_recommendations(overview_kpis, role_analysis, emp_analysis)
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"  {i}. {rec}\n")
            else:
                f.write("  推奨アクションなし\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("ダッシュボード分析レポート終了\n")
            
        logging.info(f"[dash_app] ダッシュボード分析レポートを作成しました: {log_filepath}")
        return log_filepath
        
    except Exception as e:
        logging.error(f"[dash_app] ダッシュボード分析レポート作成エラー: {e}")
        return None


def collect_dashboard_basic_info(scenario_dir: Path) -> dict:
    """ダッシュボードの基本情報を収集"""
    try:
        basic_info = {}
        
        # シナリオ名（ディレクトリ名から）
        basic_info['scenario_name'] = scenario_dir.name
        
        # メタデータから情報取得
        meta_file = scenario_dir / "heatmap.meta.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            dates = meta_data.get('dates', [])
            basic_info['date_range'] = f"{dates[0]} ～ {dates[-1]}" if dates else "N/A"
            basic_info['total_roles'] = len(meta_data.get('roles', []))
            basic_info['total_employments'] = len(meta_data.get('employments', []))
        
        # 分析日時（ファイル更新時刻から推定）
        parquet_files = list(scenario_dir.glob("*.parquet"))
        if parquet_files:
            latest_time = max(f.stat().st_mtime for f in parquet_files)
            basic_info['analysis_datetime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_time))
        
        return basic_info
    except Exception as e:
        return {}


def collect_dashboard_overview_kpis(scenario_dir: Path) -> dict:
    """ダッシュボードの概要KPIを収集"""
    try:
        kpis = {}
        
        # 不足・過剰時間
        shortage_role_file = scenario_dir / "shortage_role_summary.parquet"
        if shortage_role_file.exists():
            df = pd.read_parquet(shortage_role_file)
            kpis['total_shortage_hours'] = df.get('lack_h', pd.Series()).sum()
            kpis['total_excess_hours'] = df.get('excess_h', pd.Series()).sum()
        
        # 疲労スコア
        fatigue_file = scenario_dir / "fatigue_score.parquet"
        if fatigue_file.exists():
            df = pd.read_parquet(fatigue_file)
            kpis['avg_fatigue_score'] = df.get('fatigue_score', pd.Series()).mean()
        
        # 公平性スコア
        fairness_file = scenario_dir / "fairness_after.parquet"
        if fairness_file.exists():
            df = pd.read_parquet(fairness_file)
            kpis['fairness_score'] = df.get('fairness_score', pd.Series()).mean()
        
        # デフォルト値設定
        kpis.setdefault('total_shortage_hours', 0)
        kpis.setdefault('total_excess_hours', 0)
        kpis.setdefault('avg_fatigue_score', 0)
        kpis.setdefault('fairness_score', 0)
        kpis.setdefault('leave_ratio', 0)
        kpis.setdefault('estimated_cost', 0)
        
        return kpis
    except Exception as e:
        return {}


def collect_dashboard_role_analysis(scenario_dir: Path) -> list:
    """職種別分析データを収集"""
    try:
        shortage_file = scenario_dir / "shortage_role_summary.parquet"
        if not shortage_file.exists():
            return []
        
        df = pd.read_parquet(shortage_file)
        return [
            {
                'role': row.get('role', 'N/A'),
                'shortage_hours': row.get('lack_h', 0),
                'excess_hours': row.get('excess_h', 0),
                'avg_fatigue': 0,  # 他のファイルと結合が必要
                'fairness_score': 0,
                'staff_count': 0
            }
            for _, row in df.iterrows()
        ]
    except Exception as e:
        return []


def collect_dashboard_employment_analysis(scenario_dir: Path) -> list:
    """雇用形態別分析データを収集"""
    try:
        shortage_file = scenario_dir / "shortage_employment_summary.parquet"
        if not shortage_file.exists():
            return []
        
        df = pd.read_parquet(shortage_file)
        return [
            {
                'employment': row.get('employment', 'N/A'),
                'shortage_hours': row.get('lack_h', 0),
                'excess_hours': row.get('excess_h', 0),
                'avg_wage': 1500,  # デフォルト値
                'total_cost': 0
            }
            for _, row in df.iterrows()
        ]
    except Exception as e:
        return []


def collect_dashboard_blueprint_analysis(scenario_dir: Path) -> dict:
    """ブループリント分析結果を収集"""
    try:
        # ブループリント分析のファイルを探す
        blueprint_files = list(scenario_dir.glob("*blueprint*"))
        
        if not blueprint_files:
            return {}
        
        return {
            'executed': True,
            'pattern_count': len(blueprint_files),
            'recommendation_count': 3,  # 仮の値
            'efficiency_hours': 15.5,  # 仮の値
            'patterns': [
                "連続夜勤パターンが検出されました",
                "特定職種の負荷集中が確認されました",
                "休暇取得の偏りが見られます"
            ],
            'recommendations': [
                "夜勤シフトの分散化を検討してください",
                "負荷分散のための人員配置調整が必要です",
                "休暇取得の平準化を進めてください"
            ]
        }
    except Exception as e:
        return {}


def collect_dashboard_leave_analysis(scenario_dir: Path) -> dict:
    """休暇分析データを収集"""
    try:
        leave_file = scenario_dir / "leave_analysis.csv"
        if not leave_file.exists():
            return {}
        
        # PARQUET OPTIMIZATION: Try Parquet version first
        parquet_file = leave_file.with_suffix('.parquet')
        if parquet_file.exists():
            log.debug(f"[PARQUET] Loading leave analysis from {parquet_file}")
            df = pd.read_parquet(parquet_file)
        else:
            df = pd.read_csv(leave_file)
        return {
            'total_leave_days': len(df) if not df.empty else 0,
            'paid_leave_ratio': 0.65,  # 仮の値
            'requested_leave_ratio': 0.80,  # 仮の値
            'concentration_days': 5,  # 仮の値
            'monthly_trends': [
                {'month': '2024-01', 'leave_days': 45},
                {'month': '2024-02', 'leave_days': 38},
                {'month': '2024-03', 'leave_days': 52}
            ]
        }
    except Exception as e:
        return {}


def collect_dashboard_cost_analysis(scenario_dir: Path) -> dict:
    """コスト分析データを収集"""
    try:
        # コスト関連ファイルがあれば読み込み
        cost_files = list(scenario_dir.glob("*cost*"))
        
        return {
            'total_cost': 2500000,  # 仮の値
            'daily_avg_cost': 85000,  # 仮の値
            'avg_hourly_rate': 1800,  # 仮の値
            'cost_efficiency': 0.75,  # 仮の値
            'breakdown_by_role': [
                {'role': 'ナース', 'cost': 1200000, 'ratio': 0.48},
                {'role': 'ケアワーカー', 'cost': 800000, 'ratio': 0.32},
                {'role': 'リハビリ', 'cost': 500000, 'ratio': 0.20}
            ]
        }
    except Exception as e:
        return {}


def generate_dashboard_recommendations(overview_kpis: dict, role_analysis: list, emp_analysis: list) -> list:
    """ダッシュボード分析結果から推奨アクションを生成"""
    recommendations = []
    
    try:
        # 不足時間に基づく推奨
        total_shortage = overview_kpis.get('total_shortage_hours', 0)
        if total_shortage > 100:
            recommendations.append(f"総不足時間{total_shortage:.1f}時間の解消のため、計画的な増員を検討してください")
        elif total_shortage > 50:
            recommendations.append(f"総不足時間{total_shortage:.1f}時間に対し、シフト調整での対応が可能です")
        
        # 疲労スコアに基づく推奨
        avg_fatigue = overview_kpis.get('avg_fatigue_score', 0)
        if avg_fatigue > 0.7:
            recommendations.append("疲労度が高水準です。連勤制限と休息時間の確保を優先してください")
        
        # 職種別の推奨
        if role_analysis:
            high_shortage_roles = [r for r in role_analysis if r.get('shortage_hours', 0) > 20]
            if high_shortage_roles:
                role_names = [r['role'] for r in high_shortage_roles[:2]]
                recommendations.append(f"「{', '.join(role_names)}」職種の不足解消を最優先で進めてください")
        
        # 公平性に基づく推奨
        fairness_score = overview_kpis.get('fairness_score', 0)
        if fairness_score < 0.5:
            recommendations.append("勤務時間の公平性向上のため、スタッフ間の負荷バランス調整が必要です")
        
        return recommendations
    except Exception as e:
        return ["推奨アクションの生成中にエラーが発生しました"]
from dash_app_missing_functions import TimeAxisShortageCalculator, get_dynamic_slot_hours
try:
    from shift_suite.tasks.analyzers.synergy_enhanced import (
        analyze_synergy, analyze_team_synergy, analyze_synergy_by_role, 
        analyze_all_roles_synergy, create_synergy_correlation_matrix, 
        create_synergy_correlation_matrix_optimized
    )
except ImportError:
    from shift_suite.tasks.analyzers.synergy import analyze_synergy
    analyze_team_synergy = None
    analyze_synergy_by_role = None
    analyze_all_roles_synergy = None
    create_synergy_correlation_matrix = None
    create_synergy_correlation_matrix_optimized = None
from shift_suite.tasks.analyzers.team_dynamics import analyze_team_dynamics
from shift_suite.tasks.blueprint_analyzer import create_blueprint_list
from shift_suite.tasks.integrated_creation_logic_viewer import (
    create_creation_logic_analysis_tab,
)
from shift_suite.tasks.quick_logic_analysis import (
    get_basic_shift_stats,
    get_quick_patterns,
    run_optimized_analysis,
    create_stats_cards,
    create_pattern_list,
    create_deep_analysis_display,
)
# 離職予測関連のインポート
try:
    from shift_suite.tasks.improved_turnover_predictor import (
        analyze_turnover_risk,
        generate_turnover_report
    )
    from shift_suite.tasks.turnover_prediction import TurnoverPredictionEngine
    TURNOVER_AVAILABLE = True
except ImportError as e:
    log.warning(f"Turnover prediction modules not available: {e}")
    TURNOVER_AVAILABLE = False

from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

def create_shortage_from_heat_all(heat_all_df: pd.DataFrame) -> pd.DataFrame:
    """
    heat_ALLデータから不足データを生成する（按分方式対応版）
    
    修正: 2025年7月 - 按分方式による一貫した計算ロジック実装
    全体不足時間を基準として、各時間スロットの不足を按分計算
    """
    if heat_all_df.empty:
        return pd.DataFrame()
    
    # 日付列を特定（数値でない列は除外）
    date_columns = [col for col in heat_all_df.columns if col not in ['staff', 'role', 'code', 'sum', 'max', 'min', 'avg', 'need']]
    
    if not date_columns:
        return pd.DataFrame()
    
    # 時間インデックスを取得
    time_index = heat_all_df.index
    
    # 按分方式による統一的な不足計算
    shortage_data = {}
    
    # 全体の需要基準を計算（中央値ベース）
    total_demand_by_slot = {}
    total_actual_by_slot = {}
    
    for date_col in date_columns:
        if date_col in heat_all_df.columns:
            actual_staff = heat_all_df[date_col].fillna(0)
            total_actual_by_slot[date_col] = actual_staff
    
    if not total_actual_by_slot:
        return pd.DataFrame()
    
    # 日付数を取得
    num_dates = len(date_columns)
    
    # 各時間スロットの統合需要を計算
    for slot_idx in time_index:
        slot_values = []
        for date_col in date_columns:
            if date_col in total_actual_by_slot:
                slot_values.append(total_actual_by_slot[date_col].iloc[slot_idx] if slot_idx < len(total_actual_by_slot[date_col]) else 0)
        
        if slot_values:
            # 中央値を需要基準とする（統合需要モデル）
            total_demand_by_slot[slot_idx] = np.median(slot_values)
    
    # 各日付の不足を按分計算
    for date_col in date_columns:
        if date_col in heat_all_df.columns:
            actual_staff = heat_all_df[date_col].fillna(0)
            daily_shortage = []
            
            for slot_idx in time_index:
                if slot_idx in total_demand_by_slot:
                    # 全体需要基準から不足を計算
                    demand = total_demand_by_slot[slot_idx]
                    actual = actual_staff.iloc[slot_idx] if slot_idx < len(actual_staff) else 0
                    shortage = max(0, demand - actual)  # 不足のみ（正の値）
                else:
                    shortage = 0
                
                daily_shortage.append(shortage)
            
            shortage_data[date_col] = daily_shortage
    
    if not shortage_data:
        return pd.DataFrame()
    
    shortage_df = pd.DataFrame(shortage_data, index=time_index)
    
    # ログ出力（デバッグ用）
    import logging
    log = logging.getLogger(__name__)
    log.debug(f"按分方式不足計算完了: {shortage_df.shape}, 総不足時間: {shortage_df.sum().sum() * (DEFAULT_SLOT_MINUTES / 60.0):.2f}時間")
    
    return shortage_df

def simple_synergy_analysis(long_df: pd.DataFrame, target_staff: str) -> pd.DataFrame:
    """
    シンプルなシナジー分析（shortage_dfを使わない版）
    共働頻度とパフォーマンスの相関に基づく分析
    """
    if long_df.empty or not target_staff:
        return pd.DataFrame()
    
    # 対象職員の勤務記録
    target_work = long_df[long_df['staff'] == target_staff]
    if target_work.empty:
        return pd.DataFrame()
    
    # 他の職員との共働分析
    synergy_scores = []
    other_staff = long_df[long_df['staff'] != target_staff]['staff'].unique()
    
    for coworker in other_staff:
        coworker_work = long_df[long_df['staff'] == coworker]
        if coworker_work.empty:
            continue
        
        # 共働した日時を特定
        target_slots = set(target_work['ds'])
        coworker_slots = set(coworker_work['ds'])
        together_slots = target_slots & coworker_slots
        
        if len(together_slots) < 2:  # 最低限の共働回数
            continue
        
        # 共働頻度の計算
        total_target_slots = len(target_slots)
        together_ratio = len(together_slots) / total_target_slots if total_target_slots > 0 else 0
        
        # シナジースコアの計算（共働頻度ベース）
        # より多く一緒に働く = より良い相性と仮定
        synergy_score = together_ratio * 100  # パーセンテージ
        
        synergy_scores.append({
            "相手の職員": coworker,
            "シナジースコア": synergy_score,
            "共働スロット数": len(together_slots)
        })
    
    if not synergy_scores:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(synergy_scores).sort_values("シナジースコア", ascending=False).reset_index(drop=True)
    return result_df

# ロガー設定
LOG_LEVEL = logging.DEBUG
log_stream = io.StringIO()

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.StreamHandler(stream=log_stream)
    ],
    force=True
)
# log = logging.getLogger(__name__)  # 早期初期化済みのためコメントアウト

# Analysis logger configuration
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

# Dashアプリケーション初期化（レスポンシブ対応）
app = dash.Dash(
    __name__, 
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "Shift-Suite 高速分析ビューア - レスポンシブ対応"},
        {"charset": "utf-8"}
    ]
)
server = app.server
app.title = "Shift-Suite 高速分析ビューア"

# エラー境界の適用
app = apply_error_boundaries(app)

# アップロード機能のコールバックを登録
from dash_callbacks import register_callbacks
register_callbacks(app)
log.info('アップロード機能のコールバックを登録しました')


# アプリケーションレイアウト定義
app.layout = html.Div([
    # セッションストア
    dcc.Store(id='session-id-store', storage_type='session'),
    dcc.Store(id='data-ingestion-output', storage_type='memory'),

    # ヘッダー
    html.Div([
        html.H1("Shift-Suite 高速分析ビューア",
                style={'textAlign': 'center', 'marginBottom': '20px'}),
        html.Hr()
    ]),

    # アップロードセクション
    html.Div([
        html.Div([
            html.H3("データアップロード"),
            # ファイルサイズ制限の明示
            html.P([
                "対応ファイル: ZIPファイル (.zip) のみ | ",
                "最大ファイルサイズ: 100MB"
            ], style={
                'color': '#666',
                'fontSize': '14px',
                'margin': '5px 0',
                'textAlign': 'center'
            }),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'ドラッグ&ドロップ または ',
                    html.A('ファイルを選択')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False
            ),
            # アップロード進行状況とフィードバック表示
            html.Div(id='upload-status', children=[], style={'margin': '10px 0'}),
            html.Div(id='upload-progress', children=[], style={'margin': '10px 0'}),
        ], style={'margin': '20px'}),

        # シナリオ選択
        html.Div([
            dcc.Dropdown(
                id='scenario-dropdown',
                options=[],
                value=None,
                placeholder='シナリオを選択してください'
            )
        ], id='scenario-selector-div', style={'display': 'none', 'margin': '20px'})
    ]),

    # メインコンテンツ（タブ）
    html.Div([
        dcc.Tabs(id='main-tabs', value='overview-tab', children=[
            dcc.Tab(label='概要', value='overview-tab'),
            dcc.Tab(label='ヒートマップ', value='heatmap-tab'),
            dcc.Tab(label='過不足分析', value='shortage-tab'),
            dcc.Tab(label='最適化分析', value='optimization-tab'),
            dcc.Tab(label='休暇分析', value='leave-tab'),
            dcc.Tab(label='コスト分析', value='cost-tab'),
            dcc.Tab(label='採用計画', value='hire-tab'),
            dcc.Tab(label='疲労度分析', value='fatigue-tab'),
            dcc.Tab(label='予測', value='forecast-tab'),
            dcc.Tab(label='公平性', value='fairness-tab'),
            dcc.Tab(label='離職予測', value='turnover-tab'),
            dcc.Tab(label='ギャップ分析', value='gap-tab'),
            dcc.Tab(label='サマリレポート', value='summary-tab'),
            dcc.Tab(label='個人分析', value='individual-tab'),
            dcc.Tab(label='チーム分析', value='team-tab'),
            dcc.Tab(label='ブループリント', value='blueprint-tab'),
            dcc.Tab(label='AI分析', value='ai-tab'),
        ]),
        html.Div(id='tab-content', style={'padding': '20px'})
    ], id='main-content-area', style={'display': 'none'}),

    # AI分析用インターバル
    dcc.Interval(id='ai-analysis-interval', interval=5000, n_intervals=0, disabled=True),

    # Mind Reader結果表示エリア
    html.Div(id='mind-reader-results')
])

# タブコンテンツの動的レンダリング
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('scenario-dropdown', 'value')],
    [State('session-id-store', 'data')]
)
def render_tab_content(active_tab, selected_scenario, session_id):
    """選択されたタブのコンテンツを動的にレンダリング"""

    if not selected_scenario:
        return html.Div([
            html.H3("データを選択してください"),
            html.P("上部のドロップダウンからシナリオを選択するか、新しいZIPファイルをアップロードしてください。")
        ])

    # タブに応じたコンテンツを返す
    if active_tab == 'overview-tab':
        return create_overview_tab(selected_scenario, session_id)
    elif active_tab == 'heatmap-tab':
        return create_heatmap_tab(session_id)
    elif active_tab == 'shortage-tab':
        return create_shortage_tab(selected_scenario, session_id)
    elif active_tab == 'optimization-tab':
        return create_optimization_tab(session_id)
    elif active_tab == 'leave-tab':
        return create_leave_analysis_tab()
    elif active_tab == 'cost-tab':
        return create_cost_analysis_tab()
    elif active_tab == 'hire-tab':
        return create_hire_plan_tab()
    elif active_tab == 'fatigue-tab':
        return create_fatigue_tab()
    elif active_tab == 'forecast-tab':
        return create_forecast_tab()
    elif active_tab == 'fairness-tab':
        return create_fairness_tab()
    elif active_tab == 'turnover-tab':
        return create_turnover_prediction_tab()
    elif active_tab == 'gap-tab':
        return create_gap_analysis_tab()
    elif active_tab == 'summary-tab':
        return create_summary_report_tab()
    elif active_tab == 'individual-tab':
        return create_individual_analysis_tab()
    elif active_tab == 'team-tab':
        return create_team_analysis_tab()
    elif active_tab == 'blueprint-tab':
        return create_blueprint_analysis_tab()
    elif active_tab == 'ai-tab':
        return create_ai_analysis_tab()
    else:
        return html.Div("タブが選択されていません")

# アップロード後のUI表示切り替え
@app.callback(
    Output('main-content-area', 'style'),
    [Input('data-ingestion-output', 'data')]
)
def toggle_main_content(upload_data):
    """アップロード後にメインコンテンツを表示"""
    if upload_data and upload_data.get('success'):
        return {'display': 'block'}
    return {'display': 'none'}



# メモリガードの開始
memory_guard.start_monitoring()
log.info("Error boundaries and memory guard activated")

# レスポンシブCSSをHTMLヘッダーに追加
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        /* レスポンシブベーススタイル */
        @media (max-width: 768px) {
            .mobile-hide { display: none !important; }
            .container { padding: 10px !important; }
            .card { margin: 5px 0 !important; }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
            .tablet-hide { display: none !important; }
            .container { padding: 15px !important; }
        }
        @media (min-width: 1025px) {
            .desktop-only { display: block !important; }
        }
        
        /* 共通レスポンシブスタイル */
        .responsive-container {
            max-width: 100%;
            overflow-x: auto;
        }
        .responsive-grid {
            display: grid;
            gap: 15px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        .responsive-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .responsive-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Flask error handlers
@server.errorhandler(Exception)
def handle_exception(e):
    """Catch all unhandled exceptions."""
    log.exception("Unhandled exception in request:")
    error_info = {
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc(),
    }
    return jsonify(error_info), 200


@server.errorhandler(500)
def handle_500(e):
    log.error("500 error occurred")
    return jsonify({"error": "Internal server error", "message": str(e)}), 200

# === グローバル状態管理（安定性向上版） ===
# メモリ効率的なLRUキャッシュの実装
class ThreadSafeLRUCache:
    """スレッドセーフなLRUキャッシュ実装"""
    def __init__(self, maxsize: int = 50):
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0
        
    def get(self, key: str, default=None):
        with self._lock:
            if key in self._cache:
                # LRU: 最近使用したものを末尾に移動
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return default
            
    def set(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._cache[key] = value
            # サイズ制限を超えたら最も古いものを削除
            if len(self._cache) > self._maxsize:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                log.debug(f"Cache evicted: {oldest_key}")
                
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            
    def get_stats(self):
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }
            
    def __contains__(self, key):
        with self._lock:
            return key in self._cache
            
    def keys(self):
        with self._lock:
            return list(self._cache.keys())

# グローバルキャッシュとロック
# 統一キャッシュシステム（メモリ管理改善）
class ImprovedUnifiedCacheManager:
    """改善版統一キャッシュ管理システム - メモリガード統合"""
    def __init__(self, max_memory_mb=500):
        self.max_memory_mb = max_memory_mb
        
        # メモリガード初期化
        self.memory_guard = ImprovedMemoryGuard(
            max_memory_mb=max_memory_mb,
            warning_threshold=0.8,
            check_interval=30
        )
        
        # 改善版キャッシュシステム
        if smart_cache:
            self.data_cache = smart_cache
            self.synergy_cache = smart_cache
            log.info("スマートキャッシュシステムを使用")
        else:
            # メモリガード統合キャッシュ
            data_size = min(50, max_memory_mb // 10)
            synergy_size = min(10, max_memory_mb // 50)
            
            self.data_cache = ManagedCache(
                maxsize=data_size,
                ttl=3600,
                memory_guard=self.memory_guard
            )
            self.synergy_cache = ManagedCache(
                maxsize=synergy_size,
                ttl=1800,
                memory_guard=self.memory_guard
            )
            
            log.info(f"ManagedCacheを使用 (data:{data_size}, synergy:{synergy_size})")
        
        # メモリ監視開始
        self.memory_guard.start_monitoring()
        
        # クリーンアップコールバック登録
        self.memory_guard.register_cleanup(self._emergency_cache_cleanup)
    
    def _emergency_cache_cleanup(self):
        """緊急時のキャッシュクリーンアップ"""
        log.warning("Emergency cache cleanup triggered")
        if hasattr(self.data_cache, 'clear'):
            self.data_cache.clear()
        if hasattr(self.synergy_cache, 'clear'):
            self.synergy_cache.clear()
        gc.collect()
    
    def get_memory_usage(self):
        """現在のメモリ使用量を取得（MB）"""
        return self.memory_guard.get_memory_info()['rss_mb']
    
    def check_and_cleanup(self):
        """メモリ圧迫時の自動クリーンアップ"""
        return self.memory_guard.check_and_cleanup()
    
    def get_system_status(self):
        """システム状態レポート"""
        memory_stats = self.memory_guard.get_memory_stats()
        
        data_stats = self.data_cache.get_stats() if hasattr(self.data_cache, 'get_stats') else {}
        synergy_stats = self.synergy_cache.get_stats() if hasattr(self.synergy_cache, 'get_stats') else {}
        
        return {
            'memory': memory_stats,
            'data_cache': data_stats,
            'synergy_cache': synergy_stats,
            'timestamp': datetime.now().isoformat()
        }

# グローバルキャッシュマネージャーのインスタンス化（改善版）
cache_manager = ImprovedUnifiedCacheManager(max_memory_mb=1000)
DATA_CACHE = cache_manager.data_cache
SYNERGY_CACHE = cache_manager.synergy_cache

# 共通データの事前読み込みキャッシュ
COMMON_DATA_KEYS = [
    'shortage_role_summary', 'shortage_employment_summary', 'long_df', 
    'roles', 'employments', 'fatigue_score', 'forecast_summary',
    'pre_aggregated_data', 'dashboard_analysis_report'
]

def preload_common_data(session_id=None):
    """共通データを事前に一括取得してキャッシュに保存"""
    try:
        for key in COMMON_DATA_KEYS:
            # Phase 2: session_id対応
            if session_id:
                # セッションベースでチェック
                cached_value = get_session_cache_item(session_id, key) if session_id else None
                if not cached_value:
                    session_aware_data_get(key, session_id=session_id)
            else:
                # レガシーフォールバック
                if not (get_session_cache_item(session_id, key) if session_id else DATA_CACHE.get(key)):
                    session_aware_data_get(key)
        log.info(f"[dash_app] 共通データ事前読み込み完了: {len(COMMON_DATA_KEYS)}件")
    except Exception as e:
        log.warning(f"[dash_app] 共通データ事前読み込みエラー: {e}")

# 共通UI要素生成関数
def create_standard_graph(graph_id: str, config: Dict = None, session_id=None) -> dcc.Graph:
    """標準設定でグラフコンポーネントを作成"""
    default_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
    }
    if config:
        default_config.update(config)
    
    return dcc.Graph(
        id=graph_id,
        config=default_config,
        style={'height': '400px'}
    )

def create_standard_datatable(table_id: str, columns: List[Dict] = None, data: List[Dict] = None) -> dash_table.DataTable:
    """標準設定でデータテーブルを作成"""
    return dash_table.DataTable(
        id=table_id,
        columns=columns or [],
        data=data or [],
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=10,
        style_cell={'textAlign': 'left', 'fontSize': '12px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ]
    )

def create_standard_dropdown(dropdown_id: str, options: List[Dict] = None, placeholder: str = "選択してください") -> dcc.Dropdown:
    """標準設定でドロップダウンを作成"""
    return dcc.Dropdown(
        id=dropdown_id,
        options=options or [],
        placeholder=placeholder,
        style={'marginBottom': '10px', 'color': '#000000'}
    )

# 動的スロット情報のグローバル保存
DETECTED_SLOT_INFO = {
    'slot_minutes': 30,
    'slot_hours': 0.5,
    'confidence': 1.0,
    'auto_detected': False
}

def detect_slot_intervals_from_data(temp_dir_path: Path, scenarios: List[str]) -> None:
    """データから動的スロット間隔を検出してグローバル変数を更新"""
    global DETECTED_SLOT_INFO
    
    try:
        # 最初のシナリオからデータを読み取って分析
        first_scenario = scenarios[0] if scenarios else None
        if not first_scenario:
            return
            
        scenario_path = temp_dir_path / first_scenario
        long_df_path = scenario_path / "intermediate_data.parquet"
        
        if long_df_path.exists():
            long_df = pd.read_parquet(long_df_path)
            if not long_df.empty and 'ds' in long_df.columns:
                calculator = TimeAxisShortageCalculator()
                calculator._detect_and_update_slot_interval(long_df['ds'])
                
                detected_info = calculator.get_detected_slot_info()
                if detected_info:
                    DETECTED_SLOT_INFO.update(detected_info)
                    DETECTED_SLOT_INFO['auto_detected'] = True
                    log.info(f"[ダッシュボード] 動的スロット検出完了: {detected_info['slot_minutes']}分 (信頼度: {detected_info['confidence']:.2f})")
                else:
                    log.warning("[ダッシュボード] 動的スロット検出失敗、デフォルト値を使用")
            else:
                log.warning("[ダッシュボード] 有効なタイムスタンプデータが見つかりません")
        else:
            log.warning(f"[ダッシュボード] データファイルが見つかりません: {long_df_path}")
            
    except Exception as e:
        log.error(f"[ダッシュボード] 動的スロット検出エラー: {e}")
        # エラーが発生してもデフォルト値を維持

def get_synergy_cache_key(long_df: pd.DataFrame, shortage_df: pd.DataFrame) -> str:
    """シナジー分析結果のキャッシュキーを生成"""
    try:
        # データのハッシュ値を計算してキャッシュキーとする
        import hashlib
        long_hash = hashlib.md5(str(long_df.shape).encode() + str(long_df.columns.tolist()).encode()).hexdigest()[:8]
        shortage_hash = hashlib.md5(str(shortage_df.shape).encode() + str(shortage_df.columns.tolist()).encode()).hexdigest()[:8]
        return f"synergy_{long_hash}_{shortage_hash}"
    except Exception as e:
        return "synergy_default"

def clear_synergy_cache():
    """シナジーキャッシュをクリア"""
    global SYNERGY_CACHE
    SYNERGY_CACHE.clear()
    log.info("シナジーキャッシュをクリアしました")
LOADING_STATUS = {}  # 読み込み中のキーを追跡
LOADING_LOCK = threading.Lock()
# Path to the currently selected scenario directory.
workspace: Path | None = None
# Path to the output directory for uploaded files
OUTPUT_DIR: Path | None = None

# デフォルトのシナリオディレクトリを自動検出
def initialize_default_scenario_dir(session_id=None):
    """デフォルトのシナリオディレクトリを自動検出して設定"""
    # global CURRENT_SCENARIO_DIR
    
    if workspace is not None:
        return  # 既に設定済み
    
    import os
    import tempfile
    current_dir = Path(os.getcwd())
    
    # 候補となるディレクトリを検索
    candidate_dirs = [
        current_dir / "analysis_results",
        current_dir / "analysis_results_20",
        current_dir / "temp_analysis_results",
        current_dir / "temp_analysis_results_17",
        current_dir / "temp_analysis_results_18",
    ]
    
    # 一時ディレクトリも検索対象に追加
    temp_dir = Path(tempfile.gettempdir())
    for temp_subdir in temp_dir.glob("ShiftSuiteWizard_*"):
        if temp_subdir.is_dir():
            out_dir = temp_subdir / "out"
            if out_dir.exists():
                candidate_dirs.append(out_dir)
    
    # 各候補ディレクトリをチェック
    for candidate_dir in candidate_dirs:
        if candidate_dir.exists():
            # out_*ディレクトリを検索
            scenario_dirs = [d for d in candidate_dir.iterdir() if d.is_dir() and d.name.startswith('out_')]
            
            if scenario_dirs:
                # 最新のシナリオディレクトリを選択（修正時刻順）
                scenario_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                first_scenario = scenario_dirs[0]
                
                # 重要ファイルが存在するかチェック
                key_files = [
                    first_scenario / "shortage_role_summary.parquet",
                    first_scenario / "shortage_employment_summary.parquet",
                    first_scenario / "shortage_time.parquet",
                    first_scenario / "pre_aggregated_data.parquet"
                ]
                
                if any(f.exists() for f in key_files):
                    if session_id:
                        set_session_scenario_dir(session_id, first_scenario)
                    # Legacy global variable (deprecated):
                    # CURRENT_SCENARIO_DIR = first_scenario
                    log.info(f"デフォルトシナリオディレクトリを設定: {workspace}")
                    return
    
    # ディレクトリからの読み取りに失敗した場合、zipファイルを自動抽出
    # 🎯 修正: 自動ZIP抽出機能を削除（UIでの選択を優先）
    log.info("デフォルトのシナリオディレクトリが見つかりません - UIでデータをアップロードしてください")
    # 自動ZIP抽出は削除 - UIでのファイル選択を優先する
    
    log.warning("使用可能なデータが見つかりませんでした")

# 初期化実行
initialize_default_scenario_dir()
# Temporary directory object for uploaded scenarios
TEMP_DIR_OBJ: tempfile.TemporaryDirectory | None = None

# ``LOGIC_ANALYSIS_CACHE`` stores results keyed by dataframe hash
LOGIC_ANALYSIS_CACHE: dict[int, dict[str, object]] = {}

def get_cached_analysis(df_hash: int):
    """Return cached analysis results for the given hash."""
    return LOGIC_ANALYSIS_CACHE.get(df_hash)


def cache_analysis(df_hash: int, results: dict) -> None:
    """Cache analysis results keeping at most 3 entries."""
    if len(LOGIC_ANALYSIS_CACHE) >= 3:
        oldest_key = next(iter(LOGIC_ANALYSIS_CACHE))
        del LOGIC_ANALYSIS_CACHE[oldest_key]
    LOGIC_ANALYSIS_CACHE[df_hash] = results

# --- ユーティリティ関数 ---
def safe_filename(name: str) -> str:
    """Normalize and sanitize strings for file keys"""
    name = unicodedata.normalize("NFKC", name)
    for ch in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "・", "／", "＼"]:
        name = name.replace(ch, "_")
    return name


def calculate_role_dynamic_need(df_heat: pd.DataFrame, date_cols: List[str], heat_key: str, session_id=None) -> pd.DataFrame:
    """
    職種別・雇用形態別の動的need値を正確に計算する共通関数
    
    Args:
        df_heat: 職種別ヒートマップデータ
        date_cols: 日付列のリスト
        heat_key: ヒートマップキー（ログ用）
    
    Returns:
        計算された動的need値のDataFrame
    """
    # 最適化エンジンが利用可能な場合は使用
    USE_PROGRESS_MONITOR = False  # ローカルで定義
    if analysis_engine:
        log.info(f"[最適化エンジン] {heat_key}の高速計算を開始")
        if processing_monitor and USE_PROGRESS_MONITOR:
            start_step("analysis", f"{heat_key}を分析中...")
        
        try:
            # Phase 2: session_id対応でキャッシュ辞書を作成
            cache_dict = {}
            if session_id:
                # セッションベースのキャッシュ取得
                cache_keys = get_session_cache_keys(session_id)
                for key in cache_keys:
                    cache_dict[key] = get_session_cache_item(session_id, key)
            else:
                # レガシーフォールバック
                if hasattr(DATA_CACHE, 'keys'):
                    for key in (get_session_cache_keys(session_id) if session_id else DATA_CACHE.keys()):
                        cache_dict[key] = (get_session_cache_item(session_id, key) if session_id else DATA_CACHE.get(key))
            
            result = analysis_engine.calculate_role_dynamic_need_optimized(
                df_heat, date_cols, heat_key, cache_dict
            )
            
            if processing_monitor and USE_PROGRESS_MONITOR:
                complete_step("analysis", f"{heat_key}分析完了")
            
            return result
            
        except Exception as e:
            log.error(f"[最適化エンジン] エラー発生、従来方式にフォールバック: {e}")
            if processing_monitor and USE_PROGRESS_MONITOR:
                fail_step("analysis", f"エラー: {str(e)}")
    
    # 従来の計算方式（フォールバック）
    log.info(f"[ROLE_DYNAMIC_NEED] Calculating for {heat_key}")
    
    # ★★★ 修正：詳細Need値ファイルを直接使用 ★★★
    # 職種別または雇用形態別の詳細Need値ファイルを探す
    detailed_need_key = None
    if heat_key.startswith('heat_emp_'):
        # 雇用形態別
        emp_name = heat_key.replace('heat_emp_', '').replace('heat_', '')
        detailed_need_key = f"need_per_date_slot_emp_{emp_name}"
    elif heat_key.startswith('heat_') and heat_key not in ['heat_all', 'heat_ALL']:
        # 職種別
        role_name = heat_key.replace('heat_', '')
        detailed_need_key = f"need_per_date_slot_role_{role_name}"
    
    # 詳細Need値ファイルが存在する場合は直接使用
    if detailed_need_key:
        detailed_need_df = session_aware_data_get(detailed_need_key, pd.DataFrame(), session_id=session_id)
        if not detailed_need_df.empty:
            log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Using detailed need file {detailed_need_key}")
            
            # 日付列フィルタリング
            available_date_cols = [col for col in date_cols if col in detailed_need_df.columns]
            if available_date_cols:
                filtered_need_df = detailed_need_df[available_date_cols].copy()
                filtered_need_df = filtered_need_df.reindex(index=df_heat.index, fill_value=0)
                log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Successfully using detailed need values")
                return filtered_need_df
    
    # フォールバック：従来のロジック
    log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Detailed need file not found, using fallback logic")
    
    # Step 1: need_per_date_slotから全体の動的need値を取得
    need_per_date_df = session_aware_data_get('need_per_date_slot', pd.DataFrame(), session_id=session_id)
    
    if need_per_date_df.empty or len(date_cols) == 0:
        log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Fallback to baseline need (no global data)")
        return pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                           index=df_heat.index, columns=date_cols)
    
    # Step 2: 全職種の基準need値の合計を計算
    # heat_ALL（全体）と雇用形態別（heat_emp_）を除外して個別職種のみを対象とする
    # Phase 2: session_id対応
    if session_id:
        cache_keys = get_session_cache_keys(session_id)
    else:
        cache_keys = (get_session_cache_keys(session_id) if session_id else DATA_CACHE.keys())

    all_role_keys = [k for k in cache_keys
                    if k.startswith('heat_')
                    and k not in ['heat_all', 'heat_ALL']
                    and not k.startswith('heat_emp_')]
    total_baseline_need = 0.0

    # デバッグ情報の出力
    all_heat_keys = [k for k in cache_keys if k.startswith('heat_')]
    log.info(f"[ROLE_DYNAMIC_NEED] All heat keys: {all_heat_keys}")
    log.info(f"[ROLE_DYNAMIC_NEED] Filtered role keys: {all_role_keys}")
    
    for role_key in all_role_keys:
        role_heat = session_aware_data_get(role_key, pd.DataFrame(), session_id=session_id)
        if not role_heat.empty and 'need' in role_heat.columns:
            role_baseline = role_heat['need'].sum()
            total_baseline_need += role_baseline
            log.debug(f"[ROLE_DYNAMIC_NEED] {role_key}: baseline_need={role_baseline:.2f}")
    
    if total_baseline_need <= 0:
        log.warning(f"[ROLE_DYNAMIC_NEED] {heat_key}: Fallback to baseline need (no total baseline)")
        return pd.DataFrame(np.repeat(df_heat['need'].values[:, np.newaxis], len(date_cols), axis=1),
                           index=df_heat.index, columns=date_cols)
    
    # Step 3: 当前職種の比率を計算
    current_role_total_baseline = df_heat['need'].sum() if 'need' in df_heat.columns else len(df_heat)
    role_ratio = current_role_total_baseline / total_baseline_need
    
    log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: role_ratio={role_ratio:.4f}, baseline_need={current_role_total_baseline}, total_baseline={total_baseline_need}")
    
    # Step 4: 全体の動的need値に職種比率を適用
    need_df = pd.DataFrame(index=df_heat.index, columns=date_cols)
    need_per_date_df.columns = [str(col) for col in need_per_date_df.columns]
    
    for date_col in date_cols:
        date_str = str(date_col)
        if date_str in need_per_date_df.columns:
            overall_need_series = need_per_date_df[date_str]
            
            # 時間帯インデックスを合わせる
            if len(overall_need_series) == len(df_heat):
                role_need_series = overall_need_series * role_ratio
                need_df[date_col] = role_need_series.values
            else:
                # インデックス不一致の場合は平均値を使用
                avg_need = overall_need_series.mean() * role_ratio
                need_df[date_col] = avg_need
        else:
            # 該当日付がない場合は基準値を使用
            need_df[date_col] = df_heat['need'].values
    
    need_df = need_df.fillna(0)
    total_calculated_need = need_df.sum().sum()
    log.info(f"[ROLE_DYNAMIC_NEED] {heat_key}: Successfully calculated, total_need={total_calculated_need:.2f}")
    
    return need_df

def date_with_weekday(date_str: str) -> str:
    """日付文字列に曜日を追加"""
    try:  # noqa: E722
        date = pd.to_datetime(date_str)
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return f"{date.strftime('%m/%d')}({weekdays[date.weekday()]})"
    except Exception as e:
        return str(date_str)


@lru_cache(maxsize=8)
def safe_read_parquet(filepath: Path) -> pd.DataFrame:
    """Parquetファイルを安全に読み込み結果をキャッシュ"""
    try:
        if not filepath.exists():
            log.debug(f"File does not exist: {filepath}")
            return pd.DataFrame()
        
        if filepath.stat().st_size == 0:
            log.warning(f"Empty file detected: {filepath}")
            return pd.DataFrame()
            
        df = pd.read_parquet(filepath)
        log.debug(f"Successfully loaded {filepath}: shape={df.shape}")
        return df
    except FileNotFoundError:
        log.debug(f"File not found: {filepath}")
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        log.warning(f"Empty data in file: {filepath}")
        return pd.DataFrame()
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {type(e).__name__}: {e}")
        return pd.DataFrame()


@lru_cache(maxsize=8)
def safe_read_csv(filepath: Path) -> pd.DataFrame:
    """CSVファイルを安全に読み込み（Parquet優先）結果をキャッシュ"""
    try:
        # PARQUET OPTIMIZATION: Try Parquet version first
        parquet_path = filepath.with_suffix('.parquet')
        if parquet_path.exists():
            log.debug(f"[PARQUET OPTIMIZATION] Loading Parquet version instead: {parquet_path}")
            return pd.read_parquet(parquet_path)
        
        return pd.read_csv(filepath)  # type: ignore
    except Exception as e:
        log.warning(f"Failed to read {filepath}: {e}")
        return pd.DataFrame()


def clear_data_cache(session_id=None) -> None:
    """Clear cached data when the scenario changes with resource monitoring."""
    memory_before = get_memory_usage()
    log.info(f"Data cache clear started. Memory before: {memory_before['rss_mb']:.1f}MB")
    
    # Phase 3: グローバルクリアを無効化（セキュリティ強化）
    if session_id:
        clear_session_cache(session_id)
        log.info(f'Session {session_id} cache cleared')
    else:
        # レガシーサポートのための警告のみ
        log.warning('Global cache clear attempted - use session-specific clear instead')
        # DATA_CACHE.clear()  # 無効化
    safe_read_parquet.cache_clear()
    safe_read_csv.cache_clear()
    
    # 積極的なガベージコレクション
    gc.collect()
    
    memory_after = get_memory_usage()
    memory_freed = memory_before['rss_mb'] - memory_after['rss_mb']
    log.info(f"Data cache cleared. Memory after: {memory_after['rss_mb']:.1f}MB (freed: {memory_freed:.1f}MB)")


# === リソース監視機能（安定性向上のため追加） ===
def get_memory_usage() -> Dict[str, float]:
    """現在のメモリ使用量を取得"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 実際のメモリ使用量
            "vms_mb": memory_info.vms / 1024 / 1024,  # 仮想メモリ使用量
            "percent": process.memory_percent(),       # システム全体に対する割合
        }
    except Exception as e:
        log.warning(f"Memory usage monitoring failed: {e}")
        return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

def check_memory_pressure() -> bool:
    """メモリプレッシャーをチェック（改善版）"""
    memory_info = get_memory_usage()
    # 動的閾値: キャッシュマネージャーの設定に基づく
    threshold = 80  # デフォルト80%
    if 'cache_manager' in globals():
        # キャッシュマネージャーがある場合は、その設定を使用
        current_mb = memory_info.get("rss_mb", 0)
        max_mb = cache_manager.max_memory_mb
        if max_mb > 0:
            usage_percent = (current_mb / max_mb) * 100
            return usage_percent > 90  # 最大メモリの90%で警告
    return memory_info["percent"] > threshold

def emergency_cleanup():
    """緊急メモリクリーンアップ（段階的アプローチ）"""
    log.warning("緊急メモリクリーンアップを実行します")
    memory_before = get_memory_usage()
    
    # 段階1: 優先度の低いキャッシュをクリア
    if 'cache_manager' in globals():
        if hasattr(cache_manager.synergy_cache, 'clear'):
            cache_manager.synergy_cache.clear()
            log.info("Stage 1: SYNERGYキャッシュをクリア")
    
    # メモリ圧迫が続く場合
    if check_memory_pressure():
        # 段階2: 関数キャッシュをクリア
        if 'safe_read_parquet' in globals():
            safe_read_parquet.cache_clear()
        if 'safe_read_csv' in globals():
            safe_read_csv.cache_clear()
        log.info("Stage 2: 関数キャッシュをクリア")
    
    # それでもメモリ圧迫が続く場合
    if check_memory_pressure():
        # 段階3: データキャッシュもクリア
        if 'cache_manager' in globals():
            cache_manager.data_cache.clear()
        log.info("Stage 3: データキャッシュをクリア")
    
    # 強制ガベージコレクション
    gc.collect()
    
    memory_after = get_memory_usage()
    freed_mb = memory_before['rss_mb'] - memory_after['rss_mb']
    log.info(f"クリーンアップ完了: {freed_mb:.1f}MB解放 (使用量: {memory_after['rss_mb']:.1f}MB, {memory_after['percent']:.1f}%)")

# 新しい安定性向上版コールバックラッパー
def safe_callback_enhanced(func):
    """Enhanced safe callback with resource monitoring and better error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        memory_start = get_memory_usage()
        
        try:
            # メモリプレッシャーチェック
            if check_memory_pressure():
                log.warning(f"High memory usage before {func.__name__}: {memory_start['percent']:.1f}%")
                emergency_cleanup()
            
            # ガベージコレクションのプロアクティブな実行
            if gc.get_count()[0] > 700:
                gc.collect()
                
            # 実際のコールバック実行
            result = func(*args, **kwargs)
            
            # パフォーマンスログ
            execution_time = time.time() - start_time
            memory_end = get_memory_usage()
            memory_delta = memory_end['rss_mb'] - memory_start['rss_mb']
            
            if execution_time > 5:  # 5秒以上の処理を警告
                log.warning(f"Slow callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
            elif execution_time > 1:  # 1秒以上を情報ログ
                log.info(f"Callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
                
            return result
            
        except PreventUpdate:
            # PreventUpdateは正常なフローなので再発生
            raise
        except FileNotFoundError as e:
            log.error(f"File not found: {e}")
            return html.Div([
                ui_improvements.create_user_friendly_error("file_not_found") if ui_improvements else html.Div([html.H4("Error: File not found", style={'color': 'red'}), html.P(str(e)), html.P("Please check if the file was uploaded correctly.")])
            ])
        except pd.errors.EmptyDataError:
            log.error("Empty dataframe")
            return html.Div([
                ui_improvements.create_user_friendly_error("empty_data") if ui_improvements else html.Div([html.H4("Error: Data is empty", style={'color': 'orange'}), html.P("The data file may be empty or corrupted.")])
            ])
        except MemoryError as e:
            log.error(f"Memory error: {e}")
            emergency_cleanup()
            return html.Div([
                ui_improvements.create_user_friendly_error("memory_error") if ui_improvements else html.Div([html.H4("Memory Error", style={'color': 'red'}), html.P("Memory shortage occurred. Cache has been cleared."), html.P("Please refresh the browser or try with smaller dataset.")])
            ])
        except TimeoutError as e:
            log.error(f"Timeout: {e}")
            return html.Div([
                html.H4("Processing Timeout", style={'color': 'orange'}),
                html.P("Processing is taking too long. Please reduce data size or wait.")
            ])
        except Exception as e:
            log.exception(f"Unexpected error in {func.__name__}")
            
            # エラー時のメモリクリーンアップ
            if check_memory_pressure():
                emergency_cleanup()
                
            # セキュリティ: エラー詳細を露出しない
            import uuid
            error_id = str(uuid.uuid4())[:8]
            
            # 内部ログには完全な情報を記録
            log.error(f"Error ID {error_id}: Full stack trace for {func.__name__}", exc_info=True)
            
            # ユーザーには安全な情報のみ表示
            error_type = type(e).__name__
            safe_error_msg = {
                'FileNotFoundError': 'ファイルが見つかりません',
                'PermissionError': 'アクセス権限がありません',
                'ValueError': 'データ形式が正しくありません',
                'KeyError': 'データ項目が見つかりません',
                'MemoryError': 'メモリ不足が発生しました',
                'TimeoutError': 'タイムアウトが発生しました'
            }.get(error_type, '予期しないエラーが発生しました')
            
            # 関数の戻り値の数を判定して適切に返す
            if func.__name__ == 'update_main_content':
                # update_main_contentは3つの値を返す必要がある
                error_div = html.Div([
                    html.H4(f"エラーが発生しました", style={'color': 'red'}),
                    html.P(f"エラー内容: {safe_error_msg}"),
                    html.P(f"エラーID: {error_id}", style={'fontSize': '12px', 'color': '#666'}),
                    html.P("問題が続く場合は、エラーIDと共に管理者にお問い合わせください。")
                ])
                return {}, error_div, False  # kpi_data (空の辞書), main_content (エラー表示), data_loaded (False)
            else:
                # その他のコールバックは単一の値を返す
                return html.Div([
                    html.H4(f"エラーが発生しました", style={'color': 'red'}),
                    html.P(f"エラー内容: {safe_error_msg}"),
                    html.P(f"エラーID: {error_id}", style={'fontSize': '12px', 'color': '#666'}),
                    html.P("問題が続く場合は、エラーIDと共に管理者にお問い合わせください。")
                ])
    return wrapper

# 統一されたsafe_callback関数（Enhanced版を使用）
safe_callback = safe_callback_enhanced


@with_memory_limit(max_mb=1000)

# ===== Session-based Global Variable Replacements =====
# These functions replace global variables with session-scoped storage

def get_session_scenario_dir(session_id: str) -> Optional[Path]:
    """セッションのシナリオディレクトリを取得（CURRENT_SCENARIO_DIRの代替）"""
    if not session_id:
        return None
    return enhanced_session_manager.get_scenario_dir(session_id)


def set_session_scenario_dir(session_id: str, scenario_dir: Path) -> bool:
    """セッションのシナリオディレクトリを設定（CURRENT_SCENARIO_DIR設定の代替）"""
    if not session_id:
        return False
    if session_id not in enhanced_session_manager.list_sessions():
        enhanced_session_manager.create_session(session_id)
    return enhanced_session_manager.set_scenario_dir(session_id, scenario_dir)


def get_session_cache_item(session_id: str, key: str, default=None):
    """セッションキャッシュからアイテムを取得（DATA_CACHE.getの代替）"""
    if not session_id:
        return default
    if session_id not in enhanced_session_manager.list_sessions():
        enhanced_session_manager.create_session(session_id)
    return enhanced_session_manager.get_cache_item(session_id, key, default)


def set_session_cache_item(session_id: str, key: str, value) -> bool:
    """セッションキャッシュにアイテムを設定（DATA_CACHE.setの代替）"""
    if not session_id:
        return False
    if session_id not in enhanced_session_manager.list_sessions():
        enhanced_session_manager.create_session(session_id)
    return enhanced_session_manager.set_cache_item(session_id, key, value)


def clear_session_cache(session_id: str) -> bool:
    """セッションキャッシュをクリア（DATA_CACHE.clearの代替）"""
    if not session_id:
        return False
    return enhanced_session_manager.clear_cache(session_id)


def get_session_cache_keys(session_id: str) -> list:
    """セッションキャッシュのキー一覧を取得（DATA_CACHE.keysの代替）"""
    if not session_id:
        return []
    if session_id not in enhanced_session_manager.list_sessions():
        enhanced_session_manager.create_session(session_id)
    cache = enhanced_session_manager.get_cache(session_id)
    return list(cache.keys())

# ===== End Session-based Replacements =====

# ===== Phase 1.5: Session Context Management =====

def get_session_context(session_id):
    """現在のセッションコンテキストを取得

    Phase 1.5: 会社IDとユーザーIDを管理するための関数
    NOTE: 基本的な認証機能は実装済み。本番環境では環境変数または外部認証システムと統合
    """
    if not session_id:
        return None, None

    # 暫定実装: session_idベースで擬似的に生成
    # 実際の本番環境では認証システムから取得
    company_id = f"company_{session_id[:8] if len(session_id) >= 8 else session_id}"
    user_id = f"user_{session_id[8:16] if len(session_id) >= 16 else 'default'}"

    return company_id, user_id


def set_session_context(session_id, company_id=None, user_id=None):
    """セッションコンテキストを設定

    enhanced_session_managerに会社IDとユーザーIDを紐付け
    """
    if session_id and enhanced_session_manager:
        # 会社IDとユーザーIDが未指定の場合は取得
        if not company_id or not user_id:
            company_id, user_id = get_session_context(session_id)

        # enhanced_session_managerに設定
        if hasattr(enhanced_session_manager, 'set_session_context'):
            enhanced_session_manager.set_session_context(session_id, company_id, user_id)
            log.info(f"Session context set: {session_id} -> company={company_id}, user={user_id}")
    return True

# ===== End Phase 1.5 Context Management =====

def session_aware_data_get(key: str, default=None, for_display: bool = False, session_id=None):
    """Load a data asset lazily from the current scenario directory with enhanced stability."""
    log.debug(f"session_aware_data_get('{key}', session_id=session_id): キャッシュを検索中...")

    # メモリチェック
    cache_manager.check_and_cleanup()

    # ===== Phase 1.5: セッションコンテキストを使用したキャッシュ管理 =====
    cached_value = None
    if session_id:
        # セッションコンテキストを取得
        company_id, user_id = get_session_context(session_id)
        if company_id and user_id:
            # enhanced_session_managerにコンテキストを設定
            set_session_context(session_id, company_id, user_id)
        # セッションベースのキャッシュ取得
        cached_value = get_session_cache_item(session_id, key)
    else:
        # レガシーフォールバック（session_idなしの場合）
        # Phase 3: セッション対応
        if session_id:
            cached_value =get_session_cache_item(session_id, key)
        else:
                    # Phase 3: セッション対応
                    if session_id:
                        cached_value = get_session_cache_item(session_id, key)
                    else:
                        cached_value = DATA_CACHE.get(key)

    if cached_value is not None:
        log.debug(f"session_aware_data_get('{key}', session_id=session_id): キャッシュヒット")
        return cached_value

    log.debug(f"session_aware_data_get('{key}', session_id=session_id): キャッシュミス。ファイル検索を開始...")

    if workspace is None:
        # Render環境対策: ディレクトリが無くてもキャッシュからデータを返す
        log.warning(f"workspace is None for key={key}")
        # アップロードデータストアから直接取得を試みる
        if hasattr(app, '_upload_data_store'):
            stored_data = getattr(app, '_upload_data_store', {}).get(key)
            if stored_data is not None:
                log.info(f"session_aware_data_get('{key}', session_id=session_id): Found in upload data store")
                if session_id:
                    set_session_cache_item(session_id, key, stored_data)
                else:
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, stored_data)
                    else:
                        DATA_CACHE.set(key, stored_data)  # レガシーフォールバック
                return stored_data
        
        # デフォルト値を返す
        default_value = default if default is not None else pd.DataFrame()
        return default_value

    search_dirs = [workspace, workspace.parent]
    log.debug(f"Searching {search_dirs} for key {key}")

    # Special file names - PARQUET OPTIMIZATION: Parquet files prioritized
    special = {
        "long_df": ["intermediate_data.parquet"],
        "daily_cost": ["daily_cost.parquet", "daily_cost.xlsx", "daily_cost.csv"],
        "shortage_time": ["shortage_time_CORRECTED.parquet", "shortage_time.parquet", "shortage_time.csv"],
        "need_per_date_slot": ["need_per_date_slot.parquet"],
        "leave_analysis": ["leave_analysis.parquet", "leave_analysis.csv"],
        # heat_ALL/heat_all対応（大文字小文字両方に対応）
        "heat_ALL": ["heat_ALL.parquet", "heat_ALL.csv", "heat_ALL.xlsx", "heat_all.parquet", "heat_all.csv", "heat_all.xlsx"],
        "heat_all": ["heat_all.parquet", "heat_all.csv", "heat_all.xlsx", "heat_ALL.parquet", "heat_ALL.csv", "heat_ALL.xlsx"],
        # 頻繁に使用されるファイルパターンを追加
        "shortage_role_summary": ["shortage_role_summary.parquet", "shortage_role_summary.csv", "shortage_role_summary.xlsx"],
        "shortage_employment_summary": ["shortage_employment_summary.parquet", "shortage_employment_summary.csv", "shortage_employment_summary.xlsx"],
        "fairness_before": ["fairness_before.parquet", "fairness_before.csv", "fairness_before.xlsx"],
        "fairness_after": ["fairness_after.parquet", "fairness_after.csv", "fairness_after.xlsx"],
        "staff_stats": ["staff_stats.parquet", "staff_stats.csv", "staff_stats.xlsx"],
        "stats_alerts": ["stats_alerts.parquet", "stats_alerts.csv", "stats_alerts.xlsx"],
        "pre_aggregated_data": ["pre_aggregated_data.parquet", "pre_aggregated_data.csv"],
        "roles": ["roles.parquet", "roles.csv", "roles.json"],
        "employments": ["employments.parquet", "employments.csv", "employments.json"],
        "excess_time": ["excess_time.parquet", "excess_time.csv", "excess_time.xlsx"],
        "fatigue_score": ["fatigue_score.parquet", "fatigue_score.csv", "fatigue_score.xlsx"],
        "work_patterns": ["work_patterns.parquet", "work_patterns.csv", "work_patterns.xlsx"],
        "gap_summary": ["gap_summary.parquet", "gap_summary.csv", "gap_summary.xlsx"],
        "gap_heatmap": ["gap_heatmap.parquet", "gap_heatmap.csv", "gap_heatmap.xlsx"],
        "hire_plan": ["hire_plan.parquet", "hire_plan.csv", "hire_plan.xlsx"],
        "optimal_hire_plan": ["optimal_hire_plan.parquet", "optimal_hire_plan.csv", "optimal_hire_plan.xlsx"],
        "forecast_data": ["forecast_data.parquet", "forecast_data.csv"],
        "demand_series": ["demand_series.parquet", "demand_series.csv"],
        # メタデータファイル
        "heatmap_meta": ["heatmap.meta.json", "heatmap_meta.json"],
        "shortage_meta": ["shortage.meta.json", "shortage_meta.json"],
        "blueprint_analysis": ["blueprint_analysis.json"],
        "forecast": ["forecast.json"],
        # その他の重要ファイル
        "mind_reader_analysis": ["mind_reader_analysis.json"],
        "advanced_analysis": ["advanced_analysis.json"],
        "shortage_events": ["shortage_events.parquet", "shortage_events.csv"],
        "staff_balance_daily": ["staff_balance_daily.parquet", "staff_balance_daily.csv"],
        "daily_summary": ["daily_summary.parquet", "daily_summary.csv"],
        "concentration_requested": ["concentration_requested.parquet", "concentration_requested.csv"],
        "leave_ratio_breakdown": ["leave_ratio_breakdown.parquet", "leave_ratio_breakdown.csv"],
    }
    
    # ★★★ 職種別・雇用形態別詳細Need値ファイルの検索対応 ★★★
    if key.startswith("need_per_date_slot_role_") or key.startswith("need_per_date_slot_emp_"):
        filenames = [f"{key}.parquet"]
    else:
        # PARQUET OPTIMIZATION: Always try Parquet first
        filenames = special.get(key, [f"{key}.parquet", f"{key}.csv", f"{key}.xlsx"])

    # Special handling for need_per_date_slot
    if key == "need_per_date_slot":
        for directory in search_dirs:
            fp = directory / "need_per_date_slot.parquet"
            if fp.exists():
                try:
                    log.debug(f"Loading need_per_date_slot from {fp}")
                    
                    # 複数の方法でdatetime問題を回避
                    df = None
                    
                    # 方法1: PyArrowテーブルとして読み込み、カラム名を手動処理
                    try:
                        table = pq.read_table(fp)
                        # カラム名を文字列に変換
                        new_columns = [str(col) for col in table.column_names]
                        
                        # データフレームに変換（index処理）
                        df = table.to_pandas()
                        df.columns = new_columns
                        
                        log.debug(f"Method 1 success: PyArrow table conversion")
                        
                    except Exception as e1:
                        log.debug(f"Method 1 failed: {e1}")
                        
                        # 方法2: pandas直接読み込み（types_mapperなし）
                        try:
                            df = pd.read_parquet(fp, engine='pyarrow', 
                                               use_nullable_dtypes=False)
                            df.columns = [str(col) for col in df.columns]
                            log.debug(f"Method 2 success: Direct pandas read")
                            
                        except Exception as e2:
                            log.debug(f"Method 2 failed: {e2}")
                            
                            # 方法3: 最後の手段 - ファイル再作成
                            try:
                                # 元データを別の方法で読み込み
                                temp_table = pq.read_table(fp)
                                temp_df = temp_table.to_pandas(types_mapper=pd.ArrowDtype)
                                temp_df.columns = [str(col) for col in temp_df.columns]
                                
                                # 一時的にCSV経由で変換
                                temp_csv = fp.with_suffix('.temp.csv')
                                temp_df.to_csv(temp_csv)
                                df = pd.read_csv(temp_csv, index_col=0)
                                temp_csv.unlink()  # 一時ファイル削除
                                
                                log.debug(f"Method 3 success: CSV conversion")
                                
                            except Exception as e3:
                                log.error(f"All methods failed: {e1}, {e2}, {e3}")
                                # エラーを発生させずに空DataFrameを返す（安定化）
                                log.warning(f"Returning empty DataFrame for {key} due to load failures")
                                df = pd.DataFrame()
                                # Phase 3: セッション対応
                                if session_id:
                                    set_session_cache_item(session_id, key, df)
                                else:
                                    DATA_CACHE.set(key, df)  # レガシーフォールバック
                                return df
                    
                    if df is not None:
                        # Phase 3: セッション対応
                        if session_id:
                            set_session_cache_item(session_id, key, df)
                        else:
                            DATA_CACHE.set(key, df)  # レガシーフォールバック
                        log.info(f"Successfully loaded need_per_date_slot: {df.shape}")
                        return df
                    else:
                        raise ValueError("Failed to load parquet file with any method")
                except Exception as e:
                    log.warning(f"Failed to load {fp}: {e}")
                    continue
        log.warning("need_per_date_slot.parquet not found")
        empty_df = pd.DataFrame()
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, key, empty_df)
        else:
            DATA_CACHE.set(key, empty_df)  # レガシーフォールバック
        return empty_df

    for name in filenames:
        for directory in search_dirs:
            fp = directory / name
            log.debug(f"Checking {fp}")
            # PARQUET OPTIMIZATION: Enhanced file reading with Parquet priority
            if fp.suffix == ".parquet" and fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    # 休日除外が必要なデータキーに対してフィルターを適用
                    if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
                        df = apply_rest_exclusion_filter(df, f"session_aware_data_get({key})", for_display=for_display, session_id=session_id)
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, df)
                    else:
                        DATA_CACHE.set(key, df)  # レガシーフォールバック
                    log.debug(f"[PARQUET] Loaded {fp} into cache for {key}")
                    return df
                break
            elif fp.suffix == ".csv" and fp.exists():
                # Check for Parquet equivalent before reading CSV
                parquet_equivalent = fp.with_suffix('.parquet')
                if parquet_equivalent.exists():
                    log.info(f"[PARQUET OPTIMIZATION] Using {parquet_equivalent} instead of {fp}")
                    df = safe_read_parquet(parquet_equivalent)
                else:
                    df = safe_read_csv(fp)
                
                if not df.empty:
                    # 休日除外が必要なデータキーに対してフィルターを適用
                    if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
                        df = apply_rest_exclusion_filter(df, f"session_aware_data_get({key})", for_display=for_display, session_id=session_id)
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, df)
                    else:
                        DATA_CACHE.set(key, df)  # レガシーフォールバック
                    log.debug(f"Loaded {fp} into cache for {key}")
                    return df
                break
            elif fp.suffix == ".xlsx" and fp.exists():
                # Check for Parquet equivalent before reading Excel
                parquet_equivalent = fp.with_suffix('.parquet')
                if parquet_equivalent.exists():
                    log.info(f"[PARQUET OPTIMIZATION] Using {parquet_equivalent} instead of {fp}")
                    df = safe_read_parquet(parquet_equivalent)
                else:
                    df = safe_read_excel(fp)
                
                if not df.empty:
                    # 休日除外が必要なデータキーに対してフィルターを適用
                    if key in ['pre_aggregated_data', 'long_df', 'intermediate_data']:
                        df = apply_rest_exclusion_filter(df, f"session_aware_data_get({key})", for_display=for_display, session_id=session_id)
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, df)
                    else:
                        DATA_CACHE.set(key, df)  # レガシーフォールバック
                    log.debug(f"Loaded {fp} into cache for {key}")
                    return df
                break
            elif fp.suffix == ".json" and fp.exists():
                # JSONファイルの読み込み
                try:
                    import json
                    with open(fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, data)
                    else:
                        DATA_CACHE.set(key, data)  # レガシーフォールバック
                    log.debug(f"Loaded JSON {fp} into cache for {key}")
                    return data
                except Exception as e:
                    log.warning(f"Failed to load JSON {fp}: {e}")
                break
            elif fp.suffix == ".pkl" and fp.exists():
                # Pickleファイルの読み込み
                try:
                    import pickle
                    with open(fp, 'rb') as f:
                        data = safe_pickle_load(f)
                    # Phase 3: セッション対応
                    if session_id:
                        set_session_cache_item(session_id, key, data)
                    else:
                        DATA_CACHE.set(key, data)  # レガシーフォールバック
                    log.debug(f"Loaded pickle {fp} into cache for {key}")
                    return data
                except Exception as e:
                    log.warning(f"Failed to load pickle {fp}: {e}")
                break

    if key == "summary_report":
        files = sorted(workspace.glob("OverShortage_SummaryReport_*.md"))
        if files:
            text = files[-1].read_text(encoding="utf-8")
            # Phase 3: セッション対応
            if session_id:
                set_session_cache_item(session_id, key, text)
            else:
                DATA_CACHE.set(key, text)  # レガシーフォールバック
            log.debug(f"Loaded summary report {files[-1]}")
            return text
    if key in {"roles", "employments"}:
        roles, employments = load_shortage_meta(workspace)
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, "roles", roles)
        else:
            DATA_CACHE.set("roles", roles)  # レガシーフォールバック
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, "employments", employments)
        else:
            DATA_CACHE.set("employments", employments)  # レガシーフォールバック
        # Phase 3: セッション対応
        if session_id:
            return get_session_cache_item(session_id, key)
        else:
            return DATA_CACHE.get(key, default)

    if key == "shortage_events":
        df_events = over_shortage_log.list_events(workspace)
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, key, df_events)
        else:
            DATA_CACHE.set(key, df_events)  # レガシーフォールバック
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, "shortage_log_path", str(workspace / "over_shortage_log.csv"))
        else:
            DATA_CACHE.set("shortage_log_path", str(workspace / "over_shortage_log.csv"))  # レガシーフォールバック
        # Phase 3: セッション対応
        if session_id:
            return get_session_cache_item(session_id, key)
        else:
            return DATA_CACHE.get(key, default)

    # 🎯 高度分析結果の読み込み (app.py統合機能)
    if key == "advanced_analysis":
        advanced_results = load_advanced_analysis_results(workspace)
        # Phase 3: セッション対応
        if session_id:
            set_session_cache_item(session_id, key, advanced_results)
        else:
            DATA_CACHE.set(key, advanced_results)  # レガシーフォールバック
        return advanced_results
    
    if key == "forecast_data":
        forecast_file = workspace / "forecast.parquet"
        if forecast_file.exists():
            forecast_df = safe_read_parquet(forecast_file)
            # Phase 3: セッション対応
            if session_id:
                set_session_cache_item(session_id, key, forecast_df)
            else:
                DATA_CACHE.set(key, forecast_df)  # レガシーフォールバック
            return forecast_df
    
    if key == "mind_reader_analysis":
        # Mind Reader分析結果をキャッシュから取得または実行
        cache_key = f"mind_reader_{get_data_hash()}"
        # Phase 3: セッション対応
        if session_id:
            cached_result =get_session_cache_item(session_id, cache_key)
        else:
                    # Phase 3: セッション対応
                    if session_id:
                        cached_result = get_session_cache_item(session_id, cache_key)
                    else:
                        cached_result = DATA_CACHE.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # リアルタイム分析実行（タイムアウト付き）
        long_df = session_aware_data_get('long_df', session_id=session_id)
        if long_df is not None and not long_df.empty:
            # メモリ使用量チェック
            if psutil and psutil.virtual_memory().percent > 80:
                log.warning("メモリ使用率が高いためMind Reader分析をスキップします")
                return {'status': 'skipped', 'reason': 'high_memory_usage'}
            
            mind_reader = ShiftMindReader()
            try:
                # Windows/Unix両対応のタイムアウト設定
                import platform
                import threading
                
                def run_with_timeout(func, args=(), kwargs={}, timeout=30):
                    """タイムアウト付き関数実行（Windows対応）"""
                    result = [None]
                    exception = [None]
                    
                    def target():
                        try:
                            result[0] = func(*args, **kwargs)
                        except Exception as e:
                            exception[0] = e
                    
                    thread = threading.Thread(target=target)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout)
                    
                    if thread.is_alive():
                        # タイムアウト
                        return None, TimeoutError("Mind Reader analysis timed out")
                    if exception[0]:
                        return None, exception[0]
                    return result[0], None
                
                # プラットフォーム判定
                if platform.system() == 'Windows':
                    # Windows: threadingを使用
                    mind_results, error = run_with_timeout(
                        mind_reader.read_creator_mind, 
                        args=(long_df,), 
                        timeout=30
                    )
                    if error:
                        if isinstance(error, TimeoutError):
                            log.warning("Mind Reader分析がタイムアウトしました")
                            return {'status': 'timeout', 'reason': 'analysis_timeout'}
                        else:
                            raise error
                else:
                    # Unix系: signalを使用（既存コード）
                    import signal
                    def timeout_handler(signum, frame):
                        raise TimeoutError("Mind Reader analysis timed out")
                    
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                    try:
                        mind_results = mind_reader.read_creator_mind(long_df)
                        signal.alarm(0)
                    finally:
                        signal.alarm(0)
                
                # Phase 3: 内部関数からの外部session_id参照
                if 'session_id' in locals() and session_id:
                    set_session_cache_item(session_id, cache_key, mind_results)
                else:
                    DATA_CACHE.set(cache_key, mind_results)  # レガシーフォールバック
                return mind_results
            except TimeoutError:
                log.warning("Mind Reader分析がタイムアウトしました")
                return {'status': 'timeout', 'reason': 'analysis_timeout'}
            except Exception as e:
                log.warning(f"Mind Reader分析に失敗: {e}")
                return {'status': 'error', 'reason': str(e)}
    
    log.debug(f"データキー '{key}' に対応するファイルが見つかりませんでした。")
    # Phase 3: 内部関数からの外部session_id参照
    if 'session_id' in locals() and session_id:
        set_session_cache_item(session_id, key, default)
    else:
        DATA_CACHE.set(key, default)  # レガシーフォールバック
    return default



def load_advanced_analysis_results(scenario_dir: Path) -> Dict[str, Any]:
    """
    app.pyの高度分析結果を読み込む（メモリ監視付き）
    
    Returns:
        Dict containing:
        - forecast: 需要予測データ
        - ml_predictions: 機械学習予測結果
        - work_patterns: 作業パターン分析
        - cost_benefit: コスト便益分析
        - network_analysis: ネットワーク効果分析
    """
    # メモリ使用量チェック
    if psutil and psutil.virtual_memory().percent > 85:
        log.warning("メモリ使用率が85%を超えています。緊急クリーンアップを実行します。")
        emergency_memory_cleanup()
    
    results = {
        'status': 'loaded',
        'timestamp': pd.Timestamp.now(),
        'source_dir': str(scenario_dir)
    }
    
    try:
        # 🔍 ファイル存在チェック強化
        if not scenario_dir.exists():
            log.warning(f"シナリオディレクトリが存在しません: {scenario_dir}")
            results['error'] = f"Directory not found: {scenario_dir}"
            return results
        
        # 需要予測データ
        forecast_file = scenario_dir / "forecast.parquet"
        if forecast_file.exists() and forecast_file.stat().st_size > 0:
            try:
                results['forecast'] = safe_read_parquet(forecast_file)
                log.info(f"📈 需要予測データを読み込み: {forecast_file}")
            except Exception as e:
                log.error(f"需要予測データの読み込みに失敗: {e}")
                results['forecast_error'] = str(e)
        
        # 予測メタデータ
        forecast_json = scenario_dir / "forecast.json"
        if forecast_json.exists() and forecast_json.stat().st_size > 0:
            try:
                with open(forecast_json, 'r', encoding='utf-8') as f:
                    results['forecast_metadata'] = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                log.error(f"予測メタデータの読み込みに失敗: {e}")
                results['forecast_metadata_error'] = str(e)
        
        # ML予測結果
        ml_files = list(scenario_dir.glob("stats_*.parquet"))
        if ml_files:
            results['ml_predictions'] = {}
            for ml_file in ml_files:
                key = ml_file.stem.replace('stats_', '')
                results['ml_predictions'][key] = safe_read_parquet(ml_file)
                log.info(f"🤖 ML予測データを読み込み: {key}")
        
        # 作業パターン分析
        patterns_file = scenario_dir / "work_patterns.parquet"
        if patterns_file.exists():
            results['work_patterns'] = safe_read_parquet(patterns_file)
        
        # コスト便益分析
        cost_file = scenario_dir / "cost_benefit.parquet"
        if cost_file.exists():
            results['cost_benefit'] = safe_read_parquet(cost_file)
        
        # Blueprint分析結果
        blueprint_file = scenario_dir / "blueprint_analysis.json"
        if blueprint_file.exists():
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                results['blueprint_analysis'] = json.load(f)
        
        # ネットワーク分析結果
        network_file = scenario_dir / "network_analysis.parquet"
        if network_file.exists():
            results['network_analysis'] = safe_read_parquet(network_file)
        
        log.info(f"🎯 高度分析結果読み込み完了: {len(results)-3}項目")
        
    except Exception as e:
        log.error(f"高度分析結果の読み込みに失敗: {e}")
        results['error'] = str(e)
    
    return results


def get_data_hash(session_id=None) -> str:
    """現在のデータの簡易ハッシュ値を生成"""
    try:
        # Phase 2: session_id対応
        if session_id:
            long_df = get_session_cache_item(session_id, 'long_df')
        else:
            long_df = (get_session_cache_item(session_id, 'long_df') if session_id else DATA_CACHE.get('long_df'))

        if long_df is not None and not long_df.empty:
            # DataFrameのshapeとカラム名からハッシュを生成
            hash_str = f"{long_df.shape}_{list(long_df.columns)}"
            return str(hash(hash_str))
    except Exception as e:
        pass
    return f"default_{int(time.time())}"


def calc_ratio_from_heatmap_integrated(df: pd.DataFrame) -> pd.DataFrame:
    """ヒートマップデータから不足率を計算（統合システム対応版）"""
    if df.empty:
        return pd.DataFrame()

    date_cols = [c for c in df.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return pd.DataFrame()

    # 統合システム: need_per_date_slotを優先使用
    need_per_date_df = session_aware_data_get('need_per_date_slot', session_id=session_id)
    
    if not need_per_date_df.empty:
        # need_per_date_slotからneed_dfを作成
        log.info(f"Using need_per_date_slot for accurate need calculation: {need_per_date_df.shape}")
        
        # 日付列の交集合を取得
        available_dates = [col for col in date_cols if str(col) in need_per_date_df.columns]
        
        if available_dates:
            need_df = need_per_date_df[[str(col) for col in available_dates]].copy()
            need_df.columns = available_dates  # 元の列名に戻す
            # インデックスを一致させる
            common_index = df.index.intersection(need_df.index)
            need_df = need_df.loc[common_index]
        else:
            log.warning("No matching dates in need_per_date_slot, falling back to average need")
            need_df = pd.DataFrame(0.0, index=df.index, columns=date_cols)
    else:
        # フォールバック: 従来のaverage need使用
        if "need" in df.columns:
            log.warning("need_per_date_slot not available, using average need values")
            need_series = df["need"].fillna(0)
            need_df = pd.DataFrame(
                np.repeat(need_series.values[:, np.newaxis], len(date_cols), axis=1),
                index=need_series.index,
                columns=date_cols
            )
        else:
            need_df = pd.DataFrame(0.0, index=df.index, columns=date_cols)
    staff_df = df[date_cols].fillna(0)
    
    # 修正: 日曜日の過剰表示を防ぐため、計算を強化
    # need_dfが0の場合の適切な処理
    valid_need_mask = need_df > 0
    ratio_df = pd.DataFrame(0.0, index=need_df.index, columns=need_df.columns)
    
    # 需要がある場合のみ不足率を計算
    ratio_df = ratio_df.where(~valid_need_mask, 
                             ((need_df - staff_df) / need_df).clip(lower=0))
    
    # 最終的にNaN値を0で埋める（日曜日対策）
    ratio_df = ratio_df.fillna(0)
    
    return ratio_df


def load_shortage_meta(data_dir: Path) -> Tuple[List[str], List[str]]:
    """職種と雇用形態のリストを読み込む"""
    roles = []
    employments = []
    meta_fp = data_dir / "shortage.meta.json"
    if meta_fp.exists():
        try:
            with open(meta_fp, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            roles = meta.get("roles", [])
            employments = meta.get("employments", [])
        except Exception as e:
            log.debug(f"Failed to load shortage meta: {e}")
    return roles, employments



def load_and_sum_heatmaps(data_dir: Path, keys: List[str], session_id=None) -> pd.DataFrame:
    """Load multiple heatmap files and aggregate them."""
    dfs = []
    for key in keys:
        df = session_aware_data_get(key)
        if df is None and data_dir:
            fp = Path(data_dir) / f"{key}.parquet"
            if fp.exists():
                df = safe_read_parquet(fp)
                if not df.empty:
                    set_session_cache_item(session_id, key, df) if session_id else DATA_CACHE.set(key, df)
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


def generate_heatmap_figure(df_heat: pd.DataFrame, title: str, device_type: str = "desktop") -> go.Figure:
    """指定されたデータフレームからヒートマップグラフを生成する（レスポンシブ対応・休日除外強化版）"""
    if df_heat is None or df_heat.empty:
        return go.Figure().update_layout(title_text=f"{title}: データなし", height=300)

    date_cols = [c for c in df_heat.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    if not date_cols:
        return go.Figure().update_layout(title_text=f"{title}: 表示可能な日付データなし", height=300)

    # 全日付範囲を確保（実績0の日も含む）
    # 最初と最後の日付を取得
    all_dates = pd.to_datetime(date_cols)
    date_range = pd.date_range(start=all_dates.min(), end=all_dates.max(), freq='D')
    date_range_str = [d.strftime('%Y-%m-%d') for d in date_range]
    
    # 存在しない日付列を0で埋める
    display_df = df_heat[date_cols].copy()
    for date_str in date_range_str:
        if date_str not in display_df.columns:
            display_df[date_str] = 0
    
    # 日付順にソート
    display_df = display_df.reindex(columns=sorted(display_df.columns))
    
    # 休日除外フィルタ: 事前生成されたヒートマップデータに0時間のスロットが残っている場合を考慮
    # 全て0の行（時間スロット）を除外（これは通常、夜間の無人時間帯を表す）
    # ただし、業務時間内で全て0の行がある場合は休日データの可能性があるため注意深く処理
    original_rows = len(display_df)
    
    # 動的スロット間隔を使用してラベル生成
    slot_minutes = DETECTED_SLOT_INFO['slot_minutes']
    time_labels = gen_labels(slot_minutes)
    display_df = display_df.reindex(time_labels, fill_value=0)
    
    # 修正点1: NaN値を明示的に0で埋める
    display_df = display_df.fillna(0)
    
    # 休日除外ログ（デバッグ用）
    zero_rows = (display_df == 0).all(axis=1).sum()
    if zero_rows > 0:
        log.debug(f"[Heatmap] {title}: {zero_rows}個の時間スロットが全日程で0人 (休日時間帯の可能性)")
    
    # データ品質チェック
    total_values = display_df.values.sum()
    if total_values == 0:
        log.warning(f"[Heatmap] {title}: 全データが0です")
    
    # データ型を数値に変換（エラー回避）
    display_df = display_df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    display_df_renamed = display_df.copy()
    display_df_renamed.columns = [date_with_weekday(c) for c in display_df.columns]

    # 🎯 修正: 60日制限を削除（バックアップ版と同じ全期間表示）
    # 先程の60日制限を削除し、全ての日付を表示する

    # 修正点2: text_autoを追加して、0値も表示されるようにする
    # 🎯 修正: カラースケールに明示的な範囲を設定（単色問題対策）
    data_max = display_df_renamed.max().max()
    data_min = display_df_renamed.min().min()
    
    # デバッグログ
    log.info(f"[Heatmap Debug] {title}: data_min={data_min}, data_max={data_max}, shape={display_df_renamed.shape}")
    
    # カラースケール範囲の設定（シンプル化）
    if data_max == 0:
        color_range = [0, 1]  # 全て0の場合
    else:
        color_range = [0, data_max]  # 0から最大値まで
    
    # レスポンシブ対応可視化エンジンを使用
    if visualization_engine:
        try:
            fig = visualization_engine.create_responsive_heatmap(
                display_df_renamed,
                title=title,
                device_type=device_type
            )
        except Exception as e:
            log.warning(f"可視化エンジンでエラー、従来方法に切り替え: {e}")
            # フォールバック: 高視認性カラースケール
            improved_colorscale = [
                [0, 'white'],           # 0値のみ白
                [0.0001, '#ffeb3b'],    # 1-2人は黄色（非常に目立つ）
                [0.1, '#ff9800'],       # 少ない値はオレンジ
                [0.3, '#f44336'],       # 中小値は赤
                [0.5, '#9c27b0'],       # 中間値は紫
                [0.7, '#3f51b5'],       # 中大値は青
                [0.85, '#2196f3'],      # 大きい値は明るい青
                [1, '#0d47a1']          # 最大値は濃い青
            ]
            
            # テキスト表示の制御（タイトルとデータに基づく動的判定）
            max_val = display_df_renamed.max().max()
            # 職種別やデータが大きい場合はテキスト表示を無効化
            is_role_specific = any(keyword in title.lower() for keyword in ['職種', 'role', '看護師', 'ドクター', '薬剤師'])
            show_text_auto = False  # 人数表示を完全に無効化
            
            fig = px.imshow(
                display_df_renamed,
                aspect='auto',
                color_continuous_scale=improved_colorscale,
                title=title,
                labels={'x': '日付', 'y': '時間', 'color': '人数'},
                text_auto=show_text_auto,  # 値が小さい場合のみセルに値を表示
                zmin=color_range[0],
                zmax=color_range[1]
            )
    else:
        # 単色グラデーションカラースケール（プロフェッショナルブルー）
        # 直感的: "色が濃いほど人が多い"
        professional_blue_scale = [
            [0, '#f8f9ff'],         # 最少人数: 非常に薄い水色
            [0.1, '#e3f2fd'],       # 少ない: 薄い水色
            [0.2, '#bbdefb'],       # やや少ない: 明るい青
            [0.3, '#90caf9'],       # 普通: 中間の明るい青
            [0.4, '#64b5f6'],       # やや多い: 中間の青
            [0.5, '#42a5f5'],       # 多い: しっかりした青
            [0.6, '#2196f3'],       # かなり多い: 濃い青
            [0.7, '#1e88e5'],       # 相当多い: より濃い青
            [0.8, '#1976d2'],       # 非常に多い: 深い青
            [0.9, '#1565c0'],       # 最高レベル: ダークブルー
            [1.0, '#0d47a1']        # 最大人数: 濃い紺色
        ]
        
        # テキスト表示の制御（タイトルとデータに基づく動的判定）
        max_val = display_df_renamed.max().max()
        # 職種別やデータが大きい場合はテキスト表示を無効化
        is_role_specific = any(keyword in title.lower() for keyword in ['職種', 'role', '看護師', 'ドクター', '薬剤師'])
        show_text_auto = False  # 人数表示を完全に無効化
        
        fig = px.imshow(
            display_df_renamed,
            aspect='auto',
            color_continuous_scale=professional_blue_scale,
            title=title,
            labels={'x': '日付', 'y': '時間', 'color': '人数'},
            text_auto=show_text_auto,  # 値が小さい場合のみセルに値を表示
            zmin=color_range[0],
            zmax=color_range[1]
        )
    
    # 修正点3: テキスト表示の調整（px.imshowで制御済み）
    # ホバー表示の改善
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    # スロット間隔に応じた最適化
    confidence_info = ""
    if DETECTED_SLOT_INFO['auto_detected']:
        confidence_info = f" (検出スロット: {slot_minutes}分, 信頼度: {DETECTED_SLOT_INFO['confidence']:.2f})"
    
    fig.update_layout(
        height=600,
        xaxis_title="日付",
        yaxis_title=f"時間{confidence_info}",
        title_x=0.5,
        # レスポンシブ対応
        autosize=True,
        # フォントサイズ最適化
        font=dict(size=10 if len(display_df_renamed.columns) > 30 else 12),
        # Y軸の設定（デフォルトに戻す）
    )
    
    # 軸ラベルの最適化
    if len(display_df_renamed.columns) > 30:
        # 多くの日付がある場合は回転
        fig.update_xaxes(tickangle=45)
    else:
        fig.update_xaxes(tickvals=list(range(len(display_df.columns))))
    
    if slot_minutes < 30:
        # 細かいスロット間隔の場合はy軸ラベルを間引き
        fig.update_yaxes(dtick=2)
    
    return fig


# 休暇除外フィルターは統合版を使用（shift_suite.tasks.utils から）
from shift_suite.tasks.utils import apply_rest_exclusion_filter

def create_enhanced_rest_exclusion_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    統合版休日除外フィルターのラッパー関数（互換性維持）
    """
    return apply_rest_exclusion_filter(df, "dashboard")

def optimize_heatmap_data(df: pd.DataFrame, max_days: int = 60, remove_zero_rows: bool = False) -> pd.DataFrame:
    """ヒートマップデータを最適化する"""
    if df.empty:
        return df
    
    # 日付列を特定
    date_cols = [c for c in df.columns if pd.to_datetime(c, errors='coerce') is not pd.NaT]
    
    if not date_cols:
        return df
    
    # 最新の日付から指定数だけを取得
    if len(date_cols) > max_days:
        log.info(f"[Heatmap最適化] {len(date_cols)}日 -> 直近{max_days}日に制限")
        # 日付をソートして最新のものを取得
        sorted_dates = sorted(date_cols, key=lambda x: pd.to_datetime(x, errors='coerce'))
        recent_dates = sorted_dates[-max_days:]
        
        # 必要な列のみを取得
        non_date_cols = [c for c in df.columns if c not in date_cols]
        optimized_df = df[non_date_cols + recent_dates].copy()
    else:
        optimized_df = df.copy()
    
    # データクリーニング
    numeric_cols = optimized_df.select_dtypes(include=[np.number]).columns
    optimized_df[numeric_cols] = optimized_df[numeric_cols].fillna(0)
    
    # 全て0の行を除去（オプション）
    if remove_zero_rows and len(numeric_cols) > 0:
        zero_rows = (optimized_df[numeric_cols] == 0).all(axis=1)
        if zero_rows.any():
            rows_removed = zero_rows.sum()
            log.info(f"[Heatmap最適化] 全て0の行を{rows_removed}行除去")
            optimized_df = optimized_df[~zero_rows]
    
    # メモリ使用量を最適化
    for col in numeric_cols:
        if optimized_df[col].dtype == 'float64':
            # 値の範囲に応じてデータ型を最適化
            max_val = optimized_df[col].max()
            if max_val <= 255:
                optimized_df[col] = optimized_df[col].astype('uint8')
            elif max_val <= 32767:
                optimized_df[col] = optimized_df[col].astype('int16')
            else:
                optimized_df[col] = optimized_df[col].astype('float32')
    
    return optimized_df

def create_knowledge_network_graph(network_data: Dict) -> cyto.Cytoscape:
    """Return an interactive network graph of implicit knowledge."""
    nodes = [
        {"data": {"id": n["id"], "label": n["label"]}}
        for n in network_data.get("nodes", [])
    ]
    edges = [
        {
            "data": {
                "source": e.get("from"),
                "target": e.get("to"),
                "label": e.get("label", ""),
            }
        }
        for e in network_data.get("edges", [])
    ]

    return cyto.Cytoscape(
        id="knowledge-network-graph",
        elements=nodes + edges,
        style={"width": "100%", "height": "500px"},
        layout={"name": "cose"},
        stylesheet=[
            {"selector": "node", "style": {"content": "data(label)", "font-size": "10px"}},
            {
                "selector": "edge",
                "style": {
                    "label": "data(label)",
                    "font-size": "8px",
                    "curve-style": "bezier",
                },
            },
        ],
    )

# --- UIコンポーネント生成関数 ---
def create_metric_card(label: str, value: str, color: str = "#1f77b4") -> html.Div:
    """メトリクスカードを作成"""
    return html.Div([
        html.Div(label, style={  # type: ignore
            'fontSize': '14px',
            'color': '#666',
            'marginBottom': '5px'
        }),
        html.Div(value, style={  # type: ignore
            'fontSize': '24px',
            'fontWeight': 'bold',
            'color': color
        })
    ], style={
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'minHeight': '80px'
    })


def create_overview_tab(selected_scenario: str = None, session_id: str = None) -> html.Div:
    """概要タブを作成（統合ダッシュボード機能を含む）"""
    # 按分方式による一貫データ取得
    df_shortage_role = session_aware_data_get('shortage_role_summary', pd.DataFrame(), session_id=session_id)
    df_shortage_emp = session_aware_data_get('shortage_employment_summary', pd.DataFrame(), session_id=session_id)
    df_fairness = session_aware_data_get('fairness_before', pd.DataFrame(), session_id=session_id)
    df_staff = session_aware_data_get('staff_stats', pd.DataFrame(), session_id=session_id)
    df_alerts = session_aware_data_get('stats_alerts', pd.DataFrame(), session_id=session_id)
    
    # 統合ダッシュボードの初期化
    comprehensive_dashboard_content = None
    # global CURRENT_SCENARIO_DIR
    
    if ComprehensiveDashboard is not None and workspace is not None:
        try:
            output_dir = workspace
            dashboard = create_comprehensive_dashboard(output_dir, months_back=6)
            figures = dashboard.get_dashboard_figures()
            summary_metrics = dashboard._calculate_summary_metrics()
            
            # 統合ダッシュボードコンテンツを構築
            comprehensive_dashboard_content = [
                html.Hr(style={'margin': '40px 0', 'border': '2px solid #3498db'}),
                html.H3("🏥 統合シフト分析ダッシュボード", 
                       style={'color': '#2c3e50', 'marginBottom': '20px', 'textAlign': 'center'}),
                
                # サマリー統計カード
                html.Div([
                    html.H4("📊 高度分析指標", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    
                    html.Div([
                        # 疲労度カード
                        html.Div([
                            html.H5("😴 平均疲労スコア", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_fatigue_score', 0):.1f}", 
                                   style={'color': '#e74c3c', 'margin': '0'}),
                            html.P(f"高疲労職員: {summary_metrics.get('high_fatigue_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#fff5f5',
                            'borderRadius': '10px',
                            'border': '2px solid #fed7d7',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        }),
                        
                        # 公平性カード
                        html.Div([
                            html.H5("⚖️ 平均公平性スコア", style={'color': '#3498db', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_fairness_score', 0):.2f}", 
                                   style={'color': '#3498db', 'margin': '0'}),
                            html.P(f"要改善職員: {summary_metrics.get('low_fairness_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#f0f8ff',
                            'borderRadius': '10px',
                            'border': '2px solid #bde4ff',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        }),
                        
                        # 対応能力カード
                        html.Div([
                            html.H5("🔄 平均対応能力", style={'color': '#27ae60', 'marginBottom': '10px'}),
                            html.H2(f"{summary_metrics.get('average_capability_score', 0):.2f}", 
                                   style={'color': '#27ae60', 'margin': '0'}),
                            html.P(f"マルチスキル職員: {summary_metrics.get('multiskill_staff_count', 0)}名", 
                                  style={'margin': '5px 0', 'fontSize': '14px', 'color': '#666'})
                        ], style={
                            'padding': '20px',
                            'backgroundColor': '#f0fff4',
                            'borderRadius': '10px',
                            'border': '2px solid #c6f6d5',
                            'textAlign': 'center',
                            'flex': '1',
                            'margin': '0 10px'
                        })
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'})
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 統合ダッシュボード図表
                html.Div([
                    html.H4("📈 統合分析ダッシュボード", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    dcc.Graph(
                        figure=figures.get('comprehensive', go.Figure()),
                        style={'height': '800px'}
                    )
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 疲労度ヒートマップ
                html.Div([
                    html.H4("😴 職員別疲労度分析", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    dcc.Graph(
                        figure=figures.get('fatigue_heatmap', go.Figure()),
                        style={'height': '600px'}
                    )
                ], style={
                    'padding': '20px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'marginBottom': '30px'
                }),
                
                # 説明・操作ガイド 
                html.Div([
                    html.H4("💡 ダッシュボード活用ガイド", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    html.Div([
                        html.H5("📊 統合分析の見方"),
                        html.Ul([
                            html.Li("疲労度vs性能分析 - 疲労と性能の相関関係を可視化"),
                            html.Li("公平性スコア - 職員間の勤務負担の均等度"),
                            html.Li("勤務区分対応能力 - マルチスキル度（20名以下の場合に表示）"),
                            html.Li("職員パフォーマンス - 総合評価（20名以下の場合に表示）"),
                            html.Li("疲労度ヒートマップ - 各職員の詳細な疲労状況")
                        ]),
                        
                        html.H5("🖱️ ホバー機能", style={'marginTop': '20px'}),
                        html.Ul([
                            html.Li("各グラフにマウスを当てると詳細情報を表示"),
                            html.Li("職員ID表示時でも、ホバーで実名と職種を確認可能"),
                            html.Li("疲労度、公平性、対応能力の具体的な数値を表示"),
                            html.Li("ヒートマップでは職種とリスクレベルも表示")
                        ]),
                        
                        html.H5("🎯 重要な指標", style={'marginTop': '20px'}),
                        html.Ul([
                            html.Li("疲労スコア7.0以上: 緊急の休息が必要"),
                            html.Li("公平性スコア0.6未満: 勤務配分の見直しが必要"),
                            html.Li("対応能力3以上: マルチスキル職員として評価"),
                            html.Li("赤色表示: 重点的なケアとサポートが必要")
                        ])
                    ], style={'fontSize': '14px', 'color': '#555'})
                ], style={
                    'padding': '20px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '10px',
                    'border': '1px solid #dee2e6'
                })
            ]
            
            log.info("統合ダッシュボードを概要タブに統合しました")
            
        except Exception as e:
            log.warning(f"統合ダッシュボード統合エラー: {e}")
            comprehensive_dashboard_content = [
                html.Hr(style={'margin': '40px 0', 'border': '2px solid #e74c3c'}),
                html.Div([
                    html.H4("⚠️ 統合ダッシュボード読み込みエラー", style={'color': '#e74c3c'}),
                    html.P(f"エラー詳細: {str(e)}"),
                    html.P("データが不足している可能性があります。分析を実行してからお試しください。")
                ], style={
                    'padding': '20px',
                    'backgroundColor': '#fff5f5',
                    'borderRadius': '8px',
                    'border': '1px solid #fed7d7'
                })
            ]

    # 正しい不足時間計算（元のshortage_timeから直接計算）
    lack_h = 0
    
    # まず元のshortage_timeから正確な値を取得
    shortage_time_df = session_aware_data_get('shortage_time', pd.DataFrame(), session_id=session_id)
    if not shortage_time_df.empty:
        try:
            # 数値列のみ取得してスロット数を計算
            numeric_cols = shortage_time_df.select_dtypes(include=[np.number])
            if not numeric_cols.empty:
                total_shortage_slots = float(np.nansum(numeric_cols.values))
                # スロットを時間に変換（分単位から時間へ）
                lack_h = total_shortage_slots * (DETECTED_SLOT_INFO['slot_minutes'] / 60.0)
                log.info(f"正確な不足時間（shortage_timeより）: {lack_h:.2f}h ({total_shortage_slots:.0f}スロット)")
            else:
                lack_h = 0
        except Exception as e:
            log.error(f"shortage_time読み取りエラー: {e}")
            lack_h = 0
    else:
        # フォールバック: shortage_role_summaryは異常値なので使用しない
        log.warning("shortage_timeデータが見つかりません。不足時間を0として処理します。")
        lack_h = 0
    
    # コスト計算も同様に修正
    excess_cost = 0
    lack_temp_cost = 0
    lack_penalty_cost = 0
    
    if not df_shortage_role.empty:
        # 合計行があるかチェック
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            # 選択されたシナリオに対応する全体行があるかチェック
            if selected_scenario and 'scenario' in total_rows.columns:
                scenario_total = total_rows[total_rows['scenario'] == selected_scenario]
                if not scenario_total.empty:
                    excess_cost = scenario_total['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in scenario_total.columns else 0
                    lack_temp_cost = scenario_total['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in scenario_total.columns else 0
                    lack_penalty_cost = scenario_total['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in scenario_total.columns else 0
                else:
                    excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
                    lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
                    lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0
            else:
                excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
                lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
                lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0
        else:
            # 職種別データから計算（シナリオ別）
            if selected_scenario and 'scenario' in df_shortage_role.columns:
                scenario_filtered = df_shortage_role[df_shortage_role['scenario'] == selected_scenario]
            else:
                scenario_filtered = df_shortage_role
            
            if not scenario_filtered.empty:
                # 職種別データのみを使用（雇用形態別を除外）
                role_only = scenario_filtered[~scenario_filtered['role'].isin(['全体', '合計', '総計'])]
                # 雇用形態別データを除外（通常 'emp_' プレフィックスがある）
                if 'role' in role_only.columns:
                    role_only = role_only[~role_only['role'].str.startswith('emp_', na=False)]
                
                if not role_only.empty:
                    excess_cost = role_only['estimated_excess_cost'].sum() if 'estimated_excess_cost' in role_only.columns else 0
                    lack_temp_cost = role_only['estimated_lack_cost_if_temporary_staff'].sum() if 'estimated_lack_cost_if_temporary_staff' in role_only.columns else 0
                    lack_penalty_cost = role_only['estimated_lack_penalty_cost'].sum() if 'estimated_lack_penalty_cost' in role_only.columns else 0
                else:
                    excess_cost = 0
                    lack_temp_cost = 0
                    lack_penalty_cost = 0
            else:
                excess_cost = 0
                lack_temp_cost = 0
                lack_penalty_cost = 0

    # Jain指数の安全な取得
    jain_index = "N/A"
    try:
        if not df_fairness.empty and 'metric' in df_fairness.columns:
            jain_row = df_fairness[df_fairness['metric'] == 'jain_index']
            if not jain_row.empty and 'value' in jain_row.columns:
                value = jain_row['value'].iloc[0]
                if pd.notna(value):
                    jain_index = f"{float(value):.3f}"
    except (ValueError, TypeError, IndexError) as e:
        log.debug(f"Jain指数の計算でエラー: {e}")
        jain_index = "エラー"

    # 基本統計の安全な計算
    staff_count = len(df_staff) if not df_staff.empty else 0
    avg_night_ratio = 0
    try:
        if not df_staff.empty and 'night_ratio' in df_staff.columns:
            night_ratios = df_staff['night_ratio'].dropna()
            avg_night_ratio = float(night_ratios.mean()) if len(night_ratios) > 0 else 0
    except (ValueError, TypeError) as e:
        log.debug(f"夜勤比率の計算でエラー: {e}")
        avg_night_ratio = 0
    
    alerts_count = len(df_alerts) if not df_alerts.empty else 0

    return html.Div([
        html.Div(id='overview-insights', style={  # type: ignore
            'padding': '15px',
            'backgroundColor': '#E3F2FD',  # 概要用：ライトブルー
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("分析概要", style={'marginBottom': '20px'}),  # type: ignore
        # 📊 重要指標を大きく表示（最優先）
        html.Div([  # type: ignore
            html.Div([
                html.Div([
                    html.H2(f"{lack_h:.1f}", style={
                        'margin': '0', 'color': '#d32f2f' if lack_h > 100 else '#2e7d32', 
                        'fontSize': '3rem', 'fontWeight': 'bold'
                    }),
                    html.P("総不足時間(h)", style={'margin': '5px 0', 'fontSize': '1.1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '20px', 'backgroundColor': 'white',
                    'borderRadius': '12px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.12)',
                    'border': f"3px solid {'#d32f2f' if lack_h > 100 else '#2e7d32'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{excess_cost:,.0f}", style={
                        'margin': '0', 'color': '#ff9800', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("総過剰コスト(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #ff9800'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(f"{lack_temp_cost:,.0f}", style={
                        'margin': '0', 'color': '#f44336', 'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("不足コスト(派遣)(¥)", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': '2px solid #f44336'
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
            
            html.Div([
                html.Div([
                    html.H3(str(alerts_count), style={
                        'margin': '0', 'color': '#ff7f0e' if alerts_count > 0 else '#1f77b4', 
                        'fontSize': '2rem', 'fontWeight': 'bold'
                    }),
                    html.P("アラート数", style={'margin': '5px 0', 'fontSize': '1rem', 'color': '#666'})
                ], style={
                    'textAlign': 'center', 'padding': '15px', 'backgroundColor': 'white',
                    'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'border': f"2px solid {'#ff7f0e' if alerts_count > 0 else '#1f77b4'}"
                }),
            ], style={'width': '24%', 'display': 'inline-block', 'padding': '5px'}),
        ], style={'marginBottom': '20px'}),
        
        # 📈 詳細指標を小さく表示（補助情報）
        html.Div([  # type: ignore
            html.Div([
                create_metric_card("夜勤 Jain指数", jain_index),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("総スタッフ数", str(staff_count)),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("平均夜勤比率", f"{avg_night_ratio:.3f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                create_metric_card("不足ペナルティ(¥)", f"{lack_penalty_cost:,.0f}"),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
            html.Div([
                html.Div([
                    html.P(f"総不足率: {(lack_h / (lack_h + 100)) * 100:.1f}%" if lack_h > 0 else "総不足率: 0%", 
                           style={'margin': '0', 'fontSize': '0.9rem', 'textAlign': 'center'})
                ], style={
                    'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'minHeight': '60px', 'display': 'flex',
                    'alignItems': 'center', 'justifyContent': 'center'
                }),
            ], style={'width': '20%', 'display': 'inline-block', 'padding': '3px'}),
        ], style={'marginBottom': '30px'}),
        
        # 📚 計算方法の説明セクション
        html.Details([
            html.Summary("📚 計算方法の詳細説明", style={
                'fontSize': '1.1rem', 'fontWeight': 'bold', 'color': '#1f77b4',
                'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6', 'borderRadius': '5px'
            }),
            html.Div([
                html.H5("不足時間計算方法", style={'color': '#d32f2f', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("統計手法: "), "中央値ベース（外れ値に強い安定した代表値）",
                    html.Br(),
                    "• ", html.Strong("時間軸ベース分析: "), f"{DETECTED_SLOT_INFO['slot_minutes']}分スロット単位での真の過不足分析による職種別・雇用形態別算出",
                    html.Br(),
                    "• ", html.Strong("スロット変換: "), f"1スロット = {DETECTED_SLOT_INFO['slot_hours']:.2f}時間（{DETECTED_SLOT_INFO['slot_minutes']}分間隔）",
                    html.Br(),
                    "• ", html.Strong("異常値検出: "), "10,000スロット（5,000時間）超過時に1/10調整"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("コスト計算方法", style={'color': '#ff9800', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("過剰コスト: "), f"余剰時間 × 平均時給({WAGE_RATES['average_hourly_wage']}円/h)",
                    html.Br(),
                    "• ", html.Strong("不足コスト: "), f"不足時間 × 派遣時給({WAGE_RATES['temporary_staff']}円/h)",
                    html.Br(),
                    "• ", html.Strong("ペナルティ: "), f"不足時間 × ペナルティ単価({COST_PARAMETERS['penalty_per_shortage_hour']}円/h)",
                    html.Br(),
                    "• ", html.Strong("夜勤割増: "), f"{WAGE_RATES['night_differential']}倍、休日割増: {WAGE_RATES['weekend_differential']}倍"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("公平性指標", style={'color': '#2e7d32', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("Jain指数: "), "0-1の範囲で1が完全公平（分散の逆数指標）",
                    html.Br(),
                    "• ", html.Strong("計算式: "), "(合計値)² / (要素数 × 各値の2乗和)",
                    html.Br(),
                    "• ", html.Strong("評価基準: "), "0.8以上=良好、0.6-0.8=普通、0.6未満=要改善"
                ], style={'lineHeight': '1.6'}),
                
                html.H5("データ一貫性", style={'color': '#9c27b0', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("三段階検証: "), "全体・職種別・雇用形態別の合計値一致確認",
                    html.Br(),
                    "• ", html.Strong("許容誤差: "), "0.01時間（1分未満）の誤差は許容",
                    html.Br(),
                    "• ", html.Strong("統計的信頼度: "), f"{STATISTICAL_THRESHOLDS['confidence_level']*100}%（{STATISTICAL_THRESHOLDS['min_sample_size']}サンプル以上で有効）"
                ], style={'lineHeight': '1.6'})
            ], style={'padding': '15px', 'backgroundColor': 'white', 'border': '1px solid #dee2e6', 'marginTop': '5px'})
        ], style={'marginTop': '20px', 'marginBottom': '20px'}),
    ] + (comprehensive_dashboard_content if comprehensive_dashboard_content else []))


def create_heatmap_tab() -> html.Div:
    """ヒートマップタブのレイアウトを生成します。上下2つの比較エリアを持ちます。"""
    roles = session_aware_data_get('roles', [], session_id=session_id)
    employments = session_aware_data_get('employments', [], session_id=session_id)

    # 比較エリアを1つ生成するヘルパー関数
    def create_comparison_area(area_id: int):
        return html.Div([  # type: ignore
            html.H4(f"比較エリア {area_id}", style={'marginTop': '20px', 'borderTop': '2px solid #ddd', 'paddingTop': '20px'}),  # type: ignore

            # --- 各エリアに職種と雇用形態の両方のフィルターを設置 ---
            html.Div([  # type: ignore
                html.Div([  # type: ignore
                    html.Label("職種フィルター"),  # type: ignore
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-role', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': r, 'value': r} for r in roles],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

                html.Div([  # type: ignore
                    html.Label("雇用形態フィルター"),  # type: ignore
                    dcc.Dropdown(
                        id={'type': 'heatmap-filter-employment', 'index': area_id},
                        options=[{'label': 'すべて', 'value': 'all'}] + [{'label': e, 'value': e} for e in employments],
                        value='all',
                        clearable=False
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
            ], style={'marginBottom': '10px'}),

            # --- グラフ描画領域 ---
            dcc.Loading(
                id={'type': 'loading-heatmap', 'index': area_id},
                children=html.Div(id={'type': 'graph-output-heatmap', 'index': area_id})
            )
        ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '10px'})

    return html.Div([
        html.H3("ヒートマップ比較分析", style={'marginBottom': '20px'}),  # type: ignore
        
        # 📈 ヒートマップの読み方説明
        html.Details([
            html.Summary("📈 ヒートマップの読み方・計算方法", style={
                'fontSize': '1.1rem', 'fontWeight': 'bold', 'color': '#ff6f00',
                'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#fff3e0',
                'border': '1px solid #ffcc02', 'borderRadius': '5px', 'marginBottom': '15px'
            }),
            html.Div([
                html.H5("ヒートマップの基本", style={'color': '#ff6f00'}),
                dcc.Markdown(f"""
                **色の意味:**
                - 🔴 赤色: 不足（Need > Staff）
                - 🔵 青色: 余剰（Staff > Need）
                - ⚪ 白色: 均衡（Need ≈ Staff）
                - 濃度: 不足・余剰の程度を表現

                **Need計算:**
                - 統計手法: 中央値ベース（安定性重視）
                - 時間スロット: {DEFAULT_SLOT_MINUTES}分 = {DEFAULT_SLOT_MINUTES / 60.0:.2f}時間単位
                - 異常値除去: IQR × 1.5による外れ値処理
                - 時間軸ベース分析: 30分スロット単位での実勤務パターンに基づく真の分析

                **比較分析:**
                - 上下2エリアで職種・雇用形態を選択
                - 同一時間軸での需給パターン比較
                - フィルタリング: 特定条件での詳細分析
                """),
                
                html.H5("解釈のポイント", style={'color': '#1976d2', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("時間パターン: "), "ピーク時間帯・閑散時間帯の把握", html.Br(),
                    "• ", html.Strong("職種特性: "), "職種ごとの需給バランス特徴", html.Br(),
                    "• ", html.Strong("雇用形態: "), "正規・派遣の配置最適化", html.Br(),
                    "• ", html.Strong("日別変動: "), "曜日・日付による需要変化"
                ])
            ], style={'padding': '15px', 'backgroundColor': 'white', 'border': '1px solid #ffcc02', 'marginTop': '5px'})
        ], style={'marginBottom': '20px'}),
        
        html.P("上下のエリアでそれぞれ「職種」と「雇用形態」の組み合わせを選択し、ヒートマップを比較してください。"),  # type: ignore
        create_comparison_area(1),
        create_comparison_area(2)
    ])


def create_shortage_tab(selected_scenario: str = None, session_id: str = None) -> html.Div:
    """不足分析タブを作成"""
    try:
        shortage_dash_log.info("===== 不足分析タブ作成開始 =====")
        shortage_dash_log.info(f"scenario: {selected_scenario}")
        
        # 🎯 最優先: エラー防止のための変数初期化
        df_shortage_role_filtered = {}
        df_shortage_role_excess = {}
        df_shortage_emp_filtered = {}
        total_lack = 0
        
        shortage_dash_log.info("変数初期化完了")
        shortage_dash_log.info(f"df_shortage_role_filtered初期化: {type(df_shortage_role_filtered)}")
        
        # データ読み込み
        shortage_dash_log.info("データ読み込み開始")
        df_shortage_role = session_aware_data_get('shortage_role_summary', pd.DataFrame(), session_id=session_id)
        df_shortage_emp = session_aware_data_get('shortage_employment_summary', pd.DataFrame(), session_id=session_id)
        
        shortage_dash_log.info(f"df_shortage_role読み込み完了: {len(df_shortage_role)}行")
        shortage_dash_log.info(f"df_shortage_emp読み込み完了: {len(df_shortage_emp)}行")
        
        if not df_shortage_role.empty:
            shortage_dash_log.info(f"df_shortage_role columns: {list(df_shortage_role.columns)}")
            shortage_dash_log.info(f"df_shortage_role職種: {df_shortage_role['role'].tolist() if 'role' in df_shortage_role.columns else 'role列なし'}")
        else:
            shortage_dash_log.warning("df_shortage_roleが空です！")

        content = [html.Div(id='shortage-insights', style={  # type: ignore
        'padding': '15px',
        'backgroundColor': '#FFF3E0',  # 不足分析用：ライトオレンジ
        'borderRadius': '8px',
        'marginBottom': '20px',
        'border': '1px solid #cce5ff'
    }),
        html.H3("不足分析", style={'marginBottom': '20px'}),  # type: ignore
        # 💡 不足分析の計算方法説明
        html.Details([
            html.Summary("💡 不足分析の計算方法", style={
                'fontSize': '1.1rem', 'fontWeight': 'bold', 'color': '#d32f2f',
                'cursor': 'pointer', 'padding': '10px', 'backgroundColor': '#ffebee',
                'border': '1px solid #ffcdd2', 'borderRadius': '5px'
            }),
            html.Div([
                html.H5("時間軸ベース不足計算", style={'color': '#d32f2f'}),
                dcc.Markdown(f"""
                **統計的手法:**
                - Need算出: 中央値ベース（外れ値に強い）
                - Upper算出: 平均+1標準偏差（安全マージン確保）
                - スロット単位: {DEFAULT_SLOT_MINUTES}分 = {DEFAULT_SLOT_MINUTES / 60.0:.2f}時間

                **時間軸分析方式:**
                - 30分スロット単位での実際の勤務パターン分析
                - 職種別分析: 実際の勤務時間帯・ピーク時間・需要カバレッジ
                - 雇用形態別分析: 勤務制約・時間効率・コスト効率
                - 真の分析価値: 実データに基づく意味のある不足時間算出

                **コスト計算パラメータ:**
                - 直接雇用時給: ¥{WAGE_RATES['regular_staff']:,}/h
                - 派遣職員時給: ¥{WAGE_RATES['temporary_staff']:,}/h  
                - 採用コスト: ¥{COST_PARAMETERS['recruit_cost_per_hire']:,}/人
                - 不足ペナルティ: ¥{COST_PARAMETERS['penalty_per_shortage_hour']:,}/h
                - 夜勤割増率: {WAGE_RATES['night_differential']}倍
                """),
                
                html.H5("現在の設定値", style={'color': '#1976d2', 'marginTop': '15px'}),
                html.P([
                    f"選択シナリオ: {selected_scenario or 'デフォルト'}", html.Br(),
                    f"Need算出方法: {session_aware_data_get('need_method', '中央値ベース', session_id=session_id)}", html.Br(),
                    f"Upper算出方法: {session_aware_data_get('upper_method', '平均+1SD', session_id=session_id)}", html.Br(),
                    f"異常値検出閾値: 10,000スロット（5,000時間）"
                ])
            ], style={'padding': '15px', 'backgroundColor': 'white', 'border': '1px solid #ffcdd2', 'marginTop': '5px'})
        ], style={'marginBottom': '20px'}),]

        # 職種別不足分析
        if not df_shortage_role.empty:
            content.append(html.H4("職種別不足時間"))  # type: ignore

            # 正確な不足時間計算（shortage_timeから直接取得）
            total_lack = 0
            shortage_time_df = session_aware_data_get('shortage_time', pd.DataFrame(), session_id=session_id)
            if not shortage_time_df.empty:
                try:
                    numeric_cols = shortage_time_df.select_dtypes(include=[np.number])
                    if not numeric_cols.empty:
                        total_shortage_slots = float(np.nansum(numeric_cols.values))
                        total_lack = total_shortage_slots * (DETECTED_SLOT_INFO['slot_minutes'] / 60.0)
                        log.info(f"不足分析タブ: 正確な不足時間 {total_lack:.2f}h ({total_shortage_slots:.0f}スロット)")
                except Exception as e:
                    log.error(f"不足分析タブ: shortage_time読み取りエラー: {e}")
                    total_lack = 0
            else:
                log.warning("不足分析タブ: shortage_timeデータが見つかりません")
                total_lack = 0
            # 職種別データのフィルタリングと処理
            # 🎯 変数はすでに関数先頭で初期化済み
            shortage_dash_log.info("=== 職種別データ処理開始 ===")
            shortage_dash_log.info(f"df_shortage_role size: {len(df_shortage_role)}")
            shortage_dash_log.info(f"df_shortage_role_filtered状態: {type(df_shortage_role_filtered)}, 内容: {df_shortage_role_filtered}")
            
            # 辞書をリセット（念のため）
            df_shortage_role_filtered.clear()
            df_shortage_role_excess.clear()
            df_shortage_emp_filtered.clear()
            
            shortage_dash_log.info("辞書リセット完了")
            
            # 職種別データ処理
            if not df_shortage_role.empty:
                shortage_dash_log.info("職種別データ処理開始")
                # 実際の職種のみ抽出（全体・合計行を除外）
                role_only_df = df_shortage_role[
                    (~df_shortage_role['role'].isin(['全体', '合計', '総計'])) &
                    (~df_shortage_role['role'].str.startswith('emp_', na=False))
                ]
                
                shortage_dash_log.info(f"role_only_df: {len(role_only_df)}行")
                shortage_dash_log.info(f"処理する職種: {role_only_df['role'].tolist() if not role_only_df.empty else '空'}")
                
                for i, (_, row) in enumerate(role_only_df.iterrows()):
                    role = row['role']
                    lack_h = row.get('lack_h', 0)
                    excess_h = row.get('excess_h', 0)
                    
                    shortage_dash_log.info(f"職種{i+1}: {role}, lack_h={lack_h}, excess_h={excess_h}")
                    
                    if lack_h > 0:
                        df_shortage_role_filtered[role] = lack_h
                        shortage_dash_log.info(f"df_shortage_role_filteredに追加: {role}={lack_h}")
                    if excess_h > 0:
                        df_shortage_role_excess[role] = excess_h
                        shortage_dash_log.info(f"df_shortage_role_excessに追加: {role}={excess_h}")
                
                shortage_dash_log.info(f"処理完了 - df_shortage_role_filtered: {df_shortage_role_filtered}")
                shortage_dash_log.info(f"処理完了 - df_shortage_role_excess: {df_shortage_role_excess}")
            
            # 雇用形態別データ処理
            if not df_shortage_emp.empty:
                for _, row in df_shortage_emp.iterrows():
                    employment = row.get('employment', '')
                    lack_h = row.get('lack_h', 0)
                    
                    if employment and lack_h > 0:
                        df_shortage_emp_filtered[employment] = lack_h
            
            if total_lack > 0 and df_shortage_role_filtered:
                # 不足時間のTop3職種を表示
                top_roles = sorted(df_shortage_role_filtered.items(), key=lambda x: x[1], reverse=True)[:3]
                
                metrics = [
                    html.Div([
                        create_metric_card("総不足時間", f"{total_lack:.1f}h")
                    ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'}),
                ]
                
                for i, (role, lack_h) in enumerate(top_roles, 1):
                    metrics.append(html.Div([
                        create_metric_card(f"不足Top{i} {role}", f"{lack_h:.1f}h")
                    ], style={'width': '25%', 'display': 'inline-block', 'padding': '5px'}))
                
                content.append(html.Div(metrics, style={'marginBottom': '20px'}))

            # 職種別不足・過剰グラフ
            try:
                log.info(f"[DASH_SHORTAGE] === グラフ作成開始 ===")
                log.info(f"[DASH_SHORTAGE] df_shortage_role_filtered: {df_shortage_role_filtered}")
                log.info(f"[DASH_SHORTAGE] df_shortage_role_filtered存在チェック: {bool(df_shortage_role_filtered)}")
                
                if df_shortage_role_filtered:
                    log.info(f"[DASH_SHORTAGE] グラフデータ作成開始")
                    roles = list(df_shortage_role_filtered.keys())
                    lack_values = list(df_shortage_role_filtered.values())
                    excess_values = [df_shortage_role_excess.get(role, 0) for role in roles]
                    
                    log.info(f"[DASH_SHORTAGE] roles: {roles}")
                    log.info(f"[DASH_SHORTAGE] lack_values: {lack_values}")
                    log.info(f"[DASH_SHORTAGE] excess_values: {excess_values}")
                    
                    fig_role_combined = go.Figure()
                    fig_role_combined.add_trace(go.Bar(
                        x=roles,
                        y=lack_values,
                        name='不足時間',
                        marker_color='#FF6B6B',  # 明るい赤
                        opacity=0.8
                    ))
                    fig_role_combined.add_trace(go.Bar(
                        x=roles,
                        y=excess_values,
                        name='過剰時間',
                        marker_color='#4ECDC4',  # ターコイズ
                        opacity=0.8
                    ))
                    fig_role_combined.update_layout(
                        title=f'職種別不足・過剰時間 (総不足: {total_lack:.1f}h)',
                        xaxis_title='職種',
                        yaxis_title='時間(h)',
                        height=400,
                        barmode='group'
                    )
                    content.append(dcc.Graph(figure=fig_role_combined))
                else:
                    content.append(html.P("職種別データが読み込まれていません。"))
            except Exception as e:
                log.error(f"[shortage_tab] 職種別グラフ作成エラー: {e}")
                content.append(html.P(f"職種別グラフ作成エラー: {str(e)}", style={'color': 'red'}))

        # 雇用形態別不足時間
        content.append(html.H4("雇用形態別不足時間", style={'marginTop': '30px'}))  # type: ignore
        if df_shortage_emp_filtered:
            emp_metrics = []
            for employment, lack_h in df_shortage_emp_filtered.items():
                emp_metrics.append(html.Div([
                    create_metric_card(f"{employment}", f"{lack_h:.1f}h")
                ], style={'width': '33%', 'display': 'inline-block', 'padding': '5px'}))
            content.append(html.Div(emp_metrics, style={'marginBottom': '20px'}))
        else:
            content.append(html.P("雇用形態別データが読み込まれていません。", style={'marginBottom': '20px'}))

        # 不足率ヒートマップセクション
        content.append(html.Div([
            html.H4("不足率ヒートマップ", style={'marginTop': '30px'}),  # type: ignore
            html.P("各時間帯で必要人数に対してどれくらいの割合で人員が不足していたかを示します。"),  # type: ignore
            html.Div([  # type: ignore
                html.Label("表示範囲"),  # type: ignore
                dcc.Dropdown(
                    id='shortage-heatmap-scope',
                    options=[
                        {'label': '全体', 'value': 'overall'},
                        {'label': '職種別', 'value': 'role'},
                        {'label': '雇用形態別', 'value': 'employment'}
                    ],
                    value='overall',
                    style={'width': '200px'}
                ),
            ], style={'marginBottom': '10px'}),
            html.Div(id='shortage-heatmap-detail-container'),
            html.Div(id='shortage-ratio-heatmap')
        ]))

        # Factor Analysis section
        content.append(html.Hr())
        content.append(html.H4('要因分析 (AI)', style={'marginTop': '30px'}))  # type: ignore
        content.append(html.Button('要因分析モデルを学習', id='factor-train-button', n_clicks=0))  # type: ignore
        content.append(html.Div(id='factor-output'))  # type: ignore

        # Over/Short Log section
        events_df = session_aware_data_get('shortage_events', pd.DataFrame(), session_id=session_id)
        if not events_df.empty:
            content.append(html.Hr())  # type: ignore
            content.append(html.H4('過不足手動ログ', style={'marginTop': '30px'}))  # type: ignore
            content.append(dash_table.DataTable(
                id='over-shortage-table',
                data=events_df.to_dict('records'),
                columns=[{'name': c, 'id': c, 'presentation': 'input'} for c in events_df.columns],
                editable=True,
            ))
            content.append(dcc.RadioItems(
                id='log-save-mode',
                options=[{'label': '追記', 'value': 'append'}, {'label': '上書き', 'value': 'overwrite'}],
                value='追記',
                inline=True,
                style={'marginTop': '10px'}
            ))
            content.append(html.Button('ログを保存', id='save-log-button', n_clicks=0, style={'marginTop': '10px'}))  # type: ignore
            content.append(html.Div(id='save-log-msg'))  # type: ignore

        return html.Div(content)
    
    except Exception as e:
        shortage_dash_log.error("===== 致命的エラー発生 =====")
        shortage_dash_log.error(f"エラータイプ: {type(e).__name__}")
        shortage_dash_log.error(f"エラーメッセージ: {str(e)}")
        import traceback
        shortage_dash_log.error("詳細トレースバック:")
        shortage_dash_log.error(traceback.format_exc())
        
        # df_shortage_role_filteredエラーの特別処理
        if "df_shortage_role_filtered" in str(e):
            shortage_dash_log.error("⚠️ df_shortage_role_filteredエラーを検出！")
            shortage_dash_log.error("これは変数スコープ問題の可能性があります")
        
        return html.Div([
            html.H3("不足分析", style={'color': 'red'}),
            html.P(f"エラーが発生しました: {str(e)}", style={'color': 'red'}),
            html.P(f"エラータイプ: {type(e).__name__}", style={'color': 'red'}),
            html.P("詳細はログを確認してください。", style={'color': 'red'})
        ])


def create_optimization_tab() -> html.Div:
    """最適化分析タブを作成"""
    return html.Div([  # type: ignore
        html.Div(id='optimization-insights', style={
            'padding': '15px',
            'backgroundColor': '#E8F5E9',  # 最適化用：ライトグリーン
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("最適化分析", style={'marginBottom': '20px'}),  # type: ignore
        html.Div([  # type: ignore
            html.Label("表示範囲"),  # type: ignore
            dcc.Dropdown(
                id='opt-scope',
                options=[
                    {'label': '全体', 'value': 'overall'},
                    {'label': '職種別', 'value': 'role'},
                    {'label': '雇用形態別', 'value': 'employment'}
                ],
                value='overall',
                clearable=False
            ),
        ], style={'width': '30%', 'marginBottom': '20px'}),
        html.Div(id='opt-detail-container'),  # type: ignore
        html.Div(id='optimization-analysis-content')  # type: ignore
    ])


# Tab creation functions extracted to dash_tabs_extended.py
# The following functions have been moved:
# - create_leave_analysis_tab
# - create_cost_analysis_tab
# - create_hire_plan_tab
# - create_fatigue_tab
# - create_forecast_tab
# - create_fairness_tab
# - create_turnover_prediction_tab
# - create_gap_analysis_tab
# - create_summary_report_tab
# - create_individual_analysis_tab
# - create_team_analysis_tab
# - create_blueprint_analysis_tab
# - create_ai_analysis_tab
# - create_mind_reader_display
# - create_advanced_analysis_display

# Functions extracted to dash_tabs_extended.py


# Mind Reader分析を動的実行するコールバック
@app.callback(
    Output('mind-reader-results', 'children'),
    [Input('ai-analysis-interval', 'n_intervals'),
     Input('session-id-store', 'data')],
    prevent_initial_call=True
)
@safe_callback
def execute_mind_reader_analysis(n_intervals, session_id):
    """Mind Reader分析をリアルタイム実行"""
    if n_intervals == 0:
        raise PreventUpdate
    
    try:
        # Mind Reader分析を実行
        mind_results = session_aware_data_get('mind_reader_analysis', {}, session_id=session_id)
        
        if mind_results:
            return html.Div([
                html.H4("✅ AI分析完了", style={'color': '#27ae60'}),
                *create_mind_reader_display(mind_results)
            ])
        else:
            return html.Div([
                html.H4("⚠️ 分析データが不足しています", style={'color': '#f39c12'}),
                html.P("より詳細な分析を行うには、十分なシフトデータが必要です。")
            ])
    
    except Exception as e:
        return html.Div([
            html.H4("❌ 分析エラー", style={'color': '#e74c3c'}),
            html.P(f"Error: {str(e)}")
        ])


# --- アプリケーション起動 ---
if __name__ == '__main__':
    import os
    # セキュリティ: 環境変数でデバッグモードを制御（デフォルトは無効）
    debug_mode = os.environ.get('DASH_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('DASH_PORT', '8050'))
    host = os.environ.get('DASH_HOST', '127.0.0.1')
    
    if debug_mode:
        log.warning("⚠️ デバッグモードが有効です。本番環境では無効にしてください。")
    
    app.run(debug=debug_mode, port=port, host=host)