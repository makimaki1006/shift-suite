# dash_analysis_tabs.py - Analysis tab components
"""
Analysis-related tab creation functions extracted from dash_app.py.
Includes overview, heatmap, shortage, and optimization tabs.
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash_core import (
    create_metric_card, safe_session_data_get, safe_session_data_save,
    get_session_id_from_url, create_standard_graph, create_loading_component
)
from session_integration import session_aware_data_get, session_aware_save_data

# Initialize logging
log = logging.getLogger(__name__)

# Global constants - these would need to be imported from the main app
DETECTED_SLOT_INFO = {'slot_minutes': 30, 'slot_hours': 0.5}
WAGE_RATES = {
    'average_hourly_wage': 1500,
    'temporary_staff': 2200,
    'night_differential': 1.25,
    'weekend_differential': 1.5
}
COST_PARAMETERS = {'penalty_per_shortage_hour': 4000}
STATISTICAL_THRESHOLDS = {'confidence_level': 0.95, 'min_sample_size': 30}

def create_overview_tab(selected_scenario: str = None, session_id: str = None) -> html.Div:
    """概要タブを作成（統合ダッシュボード機能を含む）"""
    if session_id is None:
        session_id = get_session_id_from_url()

    # 按分方式による一貫データ取得
    df_shortage_role = safe_session_data_get('shortage_role_summary', pd.DataFrame(), session_id)
    df_shortage_emp = safe_session_data_get('shortage_employment_summary', pd.DataFrame(), session_id)
    df_fairness = safe_session_data_get('fairness_before', pd.DataFrame(), session_id)
    df_staff = safe_session_data_get('staff_stats', pd.DataFrame(), session_id)
    df_alerts = safe_session_data_get('stats_alerts', pd.DataFrame(), session_id)

    # 統合ダッシュボードの初期化
    comprehensive_dashboard_content = None

    # 正しい不足時間計算（元のshortage_timeから直接計算）
    lack_h = 0

    # まず元のshortage_timeから正確な値を取得
    shortage_time_df = safe_session_data_get('shortage_time', pd.DataFrame(), session_id)
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
        log.warning("shortage_timeデータが見つかりません。不足時間を0として処理します。")
        lack_h = 0

    # コスト計算
    excess_cost = 0
    lack_temp_cost = 0
    lack_penalty_cost = 0

    if not df_shortage_role.empty:
        # 合計行があるかチェック
        total_rows = df_shortage_role[df_shortage_role['role'].isin(['全体', '合計', '総計'])]
        if not total_rows.empty:
            excess_cost = total_rows['estimated_excess_cost'].iloc[0] if 'estimated_excess_cost' in total_rows.columns else 0
            lack_temp_cost = total_rows['estimated_lack_cost_if_temporary_staff'].iloc[0] if 'estimated_lack_cost_if_temporary_staff' in total_rows.columns else 0
            lack_penalty_cost = total_rows['estimated_lack_penalty_cost'].iloc[0] if 'estimated_lack_penalty_cost' in total_rows.columns else 0

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
        html.Div(id='overview-insights', style={
            'padding': '15px',
            'backgroundColor': '#E3F2FD',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': '1px solid #cce5ff'
        }),
        html.H3("分析概要", style={'marginBottom': '20px'}),

        # 重要指標を大きく表示
        html.Div([
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

        # 詳細指標
        html.Div([
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

        # 計算方法の説明セクション
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
                    "• ", html.Strong("時間軸ベース分析: "), f"{DETECTED_SLOT_INFO['slot_minutes']}分スロット単位での真の過不足分析",
                    html.Br(),
                    "• ", html.Strong("スロット変換: "), f"1スロット = {DETECTED_SLOT_INFO['slot_hours']:.2f}時間",
                ], style={'lineHeight': '1.6'}),

                html.H5("コスト計算方法", style={'color': '#ff9800', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("過剰コスト: "), f"余剰時間 × 平均時給({WAGE_RATES['average_hourly_wage']}円/h)",
                    html.Br(),
                    "• ", html.Strong("不足コスト: "), f"不足時間 × 派遣時給({WAGE_RATES['temporary_staff']}円/h)",
                ], style={'lineHeight': '1.6'}),

                html.H5("公平性指標", style={'color': '#2e7d32', 'marginTop': '15px'}),
                html.P([
                    "• ", html.Strong("Jain指数: "), "0-1の範囲で1が完全公平",
                    html.Br(),
                    "• ", html.Strong("評価基準: "), "0.8以上=良好、0.6-0.8=普通、0.6未満=要改善"
                ], style={'lineHeight': '1.6'})
            ], style={'padding': '15px', 'backgroundColor': 'white', 'border': '1px solid #dee2e6', 'marginTop': '5px'})
        ], style={'marginTop': '20px', 'marginBottom': '20px'})
    ])

def create_heatmap_tab(session_id: str = None) -> html.Div:
    """ヒートマップタブを作成"""
    if session_id is None:
        session_id = get_session_id_from_url()

    return html.Div([
        html.H3("ヒートマップ分析"),
        html.P("時間帯別・職種別の過不足状況を可視化します。"),

        # Placeholder for heatmap visualization
        create_loading_component("heatmap", [
            create_standard_graph("heatmap-graph")
        ]),

        html.Div(id='heatmap-insights', style={
            'padding': '15px',
            'backgroundColor': '#FFF3E0',
            'borderRadius': '8px',
            'marginTop': '20px',
            'border': '1px solid #ffcc80'
        })
    ])

def create_shortage_tab(selected_scenario: str = None, session_id: str = None) -> html.Div:
    """不足分析タブを作成"""
    if session_id is None:
        session_id = get_session_id_from_url()

    return html.Div([
        html.H3("不足分析"),
        html.P("職種別・時間帯別の人員不足状況を詳細分析します。"),

        # Controls section
        html.Div([
            html.Label("シナリオ選択:"),
            dcc.Dropdown(
                id='shortage-scenario-dropdown',
                options=[
                    {'label': 'ベースライン', 'value': 'baseline'},
                    {'label': 'ピーク時対応', 'value': 'peak'},
                    {'label': '最適配置', 'value': 'optimized'}
                ],
                value=selected_scenario or 'baseline'
            )
        ], style={'marginBottom': '20px'}),

        # Shortage analysis visualization
        create_loading_component("shortage", [
            create_standard_graph("shortage-graph")
        ]),

        html.Div(id='shortage-insights', style={
            'padding': '15px',
            'backgroundColor': '#FFEBEE',
            'borderRadius': '8px',
            'marginTop': '20px',
            'border': '1px solid #ffcdd2'
        })
    ])

def create_optimization_tab(session_id: str = None) -> html.Div:
    """最適化タブを作成"""
    if session_id is None:
        session_id = get_session_id_from_url()

    return html.Div([
        html.H3("最適化分析"),
        html.P("人員配置の最適化提案を行います。"),

        # Optimization controls
        html.Div([
            html.Div([
                html.Label("最適化目標:"),
                dcc.RadioItems(
                    id='optimization-target',
                    options=[
                        {'label': 'コスト最小化', 'value': 'cost'},
                        {'label': '公平性最大化', 'value': 'fairness'},
                        {'label': 'バランス型', 'value': 'balanced'}
                    ],
                    value='balanced',
                    inline=True
                )
            ], style={'width': '48%', 'display': 'inline-block'}),

            html.Div([
                html.Label("制約条件:"),
                dcc.Checklist(
                    id='optimization-constraints',
                    options=[
                        {'label': '労働基準法遵守', 'value': 'labor_law'},
                        {'label': '最小人員確保', 'value': 'min_staff'},
                        {'label': '夜勤制限', 'value': 'night_limit'}
                    ],
                    value=['labor_law', 'min_staff']
                )
            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ], style={'marginBottom': '20px'}),

        # Optimization results
        create_loading_component("optimization", [
            create_standard_graph("optimization-graph")
        ]),

        html.Div(id='optimization-insights', style={
            'padding': '15px',
            'backgroundColor': '#E8F5E8',
            'borderRadius': '8px',
            'marginTop': '20px',
            'border': '1px solid #c8e6c9'
        })
    ])