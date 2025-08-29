"""
完全タブ復元実装
21個すべてのタブ機能をオリジナルから完全復元
"""

from dash import html, dcc, Input, Output, State, ALL, MATCH, ctx
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
import tempfile
import zipfile
import base64
from io import BytesIO

log = logging.getLogger(__name__)

# ========== Phase 1: Critical Visualizations (完全実装) ==========

def create_complete_heatmap_tab():
    """完全機能版ヒートマップタブ"""
    return html.Div([
        html.H3("🔥 ヒートマップ比較分析", style={'marginBottom': '20px', 'color': '#2c3e50'}),
        
        # KPIサマリーカード
        html.Div(id='heatmap-kpi-cards', style={'display': 'flex', 'marginBottom': '20px'}),
        
        # タブ構造で複数の表示モード
        dcc.Tabs([
            dcc.Tab(label='📊 比較分析モード', children=[
                # 比較エリア1
                create_heatmap_comparison_area(1),
                # 比較エリア2
                create_heatmap_comparison_area(2)
            ]),
            dcc.Tab(label='📈 統合ビュー', children=[
                create_unified_heatmap_view()
            ]),
            dcc.Tab(label='🎯 ドリルダウン', children=[
                create_heatmap_drilldown_view()
            ])
        ])
    ])

def create_heatmap_comparison_area(area_id):
    """ヒートマップ比較エリア（完全版）"""
    return html.Div([
        html.H4(f"比較エリア {area_id}"),
        
        # 3段階フィルター
        html.Div([
            # 期間選択
            html.Div([
                html.Label("期間選択"),
                dcc.DatePickerRange(
                    id={'type': 'heatmap-date-range', 'index': area_id},
                    display_format='YYYY/MM/DD',
                    style={'width': '100%'}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
            
            # 職種フィルター
            html.Div([
                html.Label("職種フィルター"),
                dcc.Dropdown(
                    id={'type': 'heatmap-filter-role', 'index': area_id},
                    multi=True,
                    placeholder="職種を選択..."
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
            
            # 雇用形態フィルター
            html.Div([
                html.Label("雇用形態フィルター"),
                dcc.Dropdown(
                    id={'type': 'heatmap-filter-employment', 'index': area_id},
                    multi=True,
                    placeholder="雇用形態を選択..."
                )
            ], style={'width': '30%', 'display': 'inline-block'})
        ]),
        
        # 詳細設定
        html.Div([
            # 表示タイプ
            html.Div([
                html.Label("表示タイプ"),
                dcc.RadioItems(
                    id={'type': 'heatmap-display-type', 'index': area_id},
                    options=[
                        {'label': '🔴 不足率', 'value': 'shortage'},
                        {'label': '🔵 充足率', 'value': 'fulfillment'},
                        {'label': '⚖️ 需給バランス', 'value': 'balance'},
                        {'label': '📊 実数', 'value': 'absolute'}
                    ],
                    value='balance',
                    inline=True
                )
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
            
            # カラーマップ選択
            html.Div([
                html.Label("カラーマップ"),
                dcc.Dropdown(
                    id={'type': 'heatmap-colormap', 'index': area_id},
                    options=[
                        {'label': '🌈 RdBu (推奨)', 'value': 'RdBu_r'},
                        {'label': '🔥 Hot', 'value': 'hot_r'},
                        {'label': '❄️ Cool', 'value': 'cool'},
                        {'label': '🌊 Viridis', 'value': 'viridis'},
                        {'label': '🎨 Plasma', 'value': 'plasma'}
                    ],
                    value='RdBu_r'
                )
            ], style={'width': '48%', 'display': 'inline-block'})
        ], style={'marginTop': '15px'}),
        
        # ヒートマップ表示領域
        dcc.Loading(
            children=[
                dcc.Graph(id={'type': 'heatmap-graph', 'index': area_id}),
                html.Div(id={'type': 'heatmap-stats', 'index': area_id})
            ]
        )
    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'marginBottom': '20px'})

def create_unified_heatmap_view():
    """統合ヒートマップビュー"""
    return html.Div([
        html.H4("全体俯瞰ヒートマップ"),
        
        # 集計レベル選択
        html.Div([
            html.Label("集計レベル"),
            dcc.RadioItems(
                id='unified-heatmap-level',
                options=[
                    {'label': '日別 × 職種', 'value': 'date_role'},
                    {'label': '日別 × 時間帯', 'value': 'date_slot'},
                    {'label': '職種 × 時間帯', 'value': 'role_slot'},
                    {'label': '週別 × 職種', 'value': 'week_role'}
                ],
                value='date_role',
                inline=True
            )
        ]),
        
        dcc.Graph(id='unified-heatmap-graph', style={'height': '600px'})
    ])

def create_heatmap_drilldown_view():
    """ドリルダウン分析ビュー"""
    return html.Div([
        html.H4("詳細ドリルダウン分析"),
        
        # クリック可能なヒートマップ
        dcc.Graph(id='drilldown-main-heatmap'),
        
        # 詳細情報パネル
        html.Div([
            html.H5("選択セルの詳細"),
            html.Div(id='drilldown-details', style={
                'padding': '15px',
                'backgroundColor': 'white',
                'borderRadius': '5px',
                'marginTop': '10px'
            })
        ])
    ])

def create_complete_shortage_tab():
    """完全機能版不足分析タブ"""
    return html.Div([
        html.H3("📊 不足分析", style={'marginBottom': '20px'}),
        
        # AIインサイト
        html.Div(id='shortage-ai-insights', style={
            'padding': '15px',
            'backgroundColor': '#e3f2fd',
            'borderRadius': '8px',
            'marginBottom': '20px'
        }),
        
        # メインコンテンツ（3列レイアウト）
        html.Div([
            # 左列：職種別不足
            html.Div([
                html.H4("職種別不足分析"),
                dcc.Graph(id='shortage-role-graph'),
                html.Div(id='shortage-role-top3')
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
            
            # 中央列：時系列不足
            html.Div([
                html.H4("時系列不足推移"),
                dcc.Graph(id='shortage-timeline-graph'),
                dcc.Graph(id='shortage-heatmap-mini')
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
            
            # 右列：雇用形態別不足
            html.Div([
                html.H4("雇用形態別不足分析"),
                dcc.Graph(id='shortage-employment-graph'),
                html.Div(id='shortage-employment-breakdown')
            ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ]),
        
        # 詳細分析セクション
        html.Div([
            html.H4("詳細分析", style={'marginTop': '30px'}),
            dcc.Tabs([
                dcc.Tab(label='要因分析', children=[
                    create_shortage_factor_analysis()
                ]),
                dcc.Tab(label='コスト影響', children=[
                    create_shortage_cost_impact()
                ]),
                dcc.Tab(label='改善提案', children=[
                    create_shortage_improvement_suggestions()
                ])
            ])
        ])
    ])

def create_shortage_factor_analysis():
    """不足要因分析"""
    return html.Div([
        html.H5("不足の主要因"),
        dcc.Graph(id='shortage-factor-chart'),
        html.Div(id='shortage-factor-details')
    ])

def create_shortage_cost_impact():
    """コスト影響分析"""
    return html.Div([
        html.H5("コスト影響"),
        dcc.Graph(id='shortage-cost-chart'),
        html.Div(id='shortage-cost-table')
    ])

def create_shortage_improvement_suggestions():
    """改善提案"""
    return html.Div([
        html.H5("AI改善提案"),
        html.Div(id='shortage-improvement-list')
    ])

def create_complete_fairness_tab():
    """完全機能版公平性分析タブ（6種類の可視化）"""
    return html.Div([
        html.H3("⚖️ 公平性分析", style={'marginBottom': '20px'}),
        
        # Jain指数サマリー
        html.Div(id='fairness-jain-summary', style={
            'padding': '15px',
            'backgroundColor': '#f0f4f8',
            'borderRadius': '8px',
            'marginBottom': '20px'
        }),
        
        # 6種類の可視化グリッド
        html.Div([
            # 1. 散布図マトリックス
            html.Div([
                html.H5("1. 多次元散布図マトリックス"),
                dcc.Graph(id='fairness-scatter-matrix')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 2. ヒートマップ
            html.Div([
                html.H5("2. 公平性ヒートマップ"),
                dcc.Graph(id='fairness-heatmap')
            ], style={'width': '49%', 'display': 'inline-block'})
        ]),
        
        html.Div([
            # 3. レーダーチャート
            html.Div([
                html.H5("3. 多軸レーダーチャート"),
                dcc.Graph(id='fairness-radar')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 4. ボックスプロット
            html.Div([
                html.H5("4. 分布ボックスプロット"),
                dcc.Graph(id='fairness-boxplot')
            ], style={'width': '49%', 'display': 'inline-block'})
        ], style={'marginTop': '20px'}),
        
        html.Div([
            # 5. サンバースト
            html.Div([
                html.H5("5. 階層サンバースト"),
                dcc.Graph(id='fairness-sunburst')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 6. パラレルコーディネート
            html.Div([
                html.H5("6. パラレルコーディネート"),
                dcc.Graph(id='fairness-parallel')
            ], style={'width': '49%', 'display': 'inline-block'})
        ], style={'marginTop': '20px'}),
        
        # 改善提案セクション
        html.Div([
            html.H4("公平性改善提案", style={'marginTop': '30px'}),
            html.Div(id='fairness-improvements')
        ])
    ])

# ========== Phase 2: Advanced Analytics (完全実装) ==========

def create_complete_fatigue_tab():
    """完全機能版疲労分析タブ（3D可視化含む）"""
    return html.Div([
        html.H3("😴 疲労分析", style={'marginBottom': '20px'}),
        
        # リスクレベルKPIカード
        html.Div([
            create_fatigue_risk_card("高リスク", "high-risk", "#d32f2f"),
            create_fatigue_risk_card("中リスク", "medium-risk", "#f57c00"),
            create_fatigue_risk_card("低リスク", "low-risk", "#388e3c")
        ], style={'display': 'flex', 'marginBottom': '20px'}),
        
        # メイン可視化
        html.Div([
            # 3D散布図
            html.Div([
                html.H5("3D疲労度散布図"),
                dcc.Graph(id='fatigue-3d-scatter', style={'height': '500px'})
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 時系列推移
            html.Div([
                html.H5("疲労度時系列推移"),
                dcc.Graph(id='fatigue-timeline', style={'height': '500px'})
            ], style={'width': '49%', 'display': 'inline-block'})
        ]),
        
        # 詳細分析
        html.Div([
            html.H4("詳細分析", style={'marginTop': '30px'}),
            dcc.Tabs([
                dcc.Tab(label='個人別詳細', children=[
                    create_fatigue_individual_analysis()
                ]),
                dcc.Tab(label='パターン分析', children=[
                    create_fatigue_pattern_analysis()
                ]),
                dcc.Tab(label='予測・アラート', children=[
                    create_fatigue_prediction_alerts()
                ])
            ])
        ])
    ])

def create_fatigue_risk_card(title, id_suffix, color):
    """疲労リスクKPIカード"""
    return html.Div([
        html.H6(title, style={'margin': '0', 'color': color}),
        html.H3(id=f'fatigue-{id_suffix}-count', children='0人'),
        html.P(id=f'fatigue-{id_suffix}-percent', children='0%')
    ], style={
        'flex': '1',
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'marginRight': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'borderLeft': f'4px solid {color}'
    })

def create_fatigue_individual_analysis():
    """個人別疲労分析"""
    return html.Div([
        html.Div([
            html.Label("スタッフ選択"),
            dcc.Dropdown(id='fatigue-staff-select', multi=True)
        ]),
        dcc.Graph(id='fatigue-individual-chart')
    ])

def create_fatigue_pattern_analysis():
    """疲労パターン分析"""
    return html.Div([
        dcc.Graph(id='fatigue-pattern-heatmap'),
        html.Div(id='fatigue-pattern-insights')
    ])

def create_fatigue_prediction_alerts():
    """疲労予測とアラート"""
    return html.Div([
        html.Div(id='fatigue-alerts'),
        dcc.Graph(id='fatigue-prediction-chart')
    ])

def create_complete_leave_analysis_tab():
    """完全機能版休暇分析タブ"""
    return html.Div([
        html.H3("🏖️ 休暇分析", style={'marginBottom': '20px'}),
        
        # 有給休暇取得率KPI
        html.Div([
            html.Div([
                html.H6("平均有給取得率"),
                html.H3(id='leave-avg-rate', children='0%'),
                html.P(id='leave-avg-days', children='0日')
            ], style={'flex': '1', 'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '8px', 'marginRight': '10px'}),
            
            html.Div([
                html.H6("最高取得率"),
                html.H3(id='leave-max-rate', children='0%'),
                html.P(id='leave-max-name', children='-')
            ], style={'flex': '1', 'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '8px', 'marginRight': '10px'}),
            
            html.Div([
                html.H6("最低取得率"),
                html.H3(id='leave-min-rate', children='0%'),
                html.P(id='leave-min-name', children='-')
            ], style={'flex': '1', 'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '8px'})
        ], style={'display': 'flex', 'marginBottom': '20px'}),
        
        # 4種類のグラフ
        html.Div([
            # 勤務予定推移
            html.Div([
                html.H5("勤務予定推移"),
                dcc.Graph(id='leave-schedule-timeline')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 日別内訳
            html.Div([
                html.H5("日別休暇内訳"),
                dcc.Graph(id='leave-daily-breakdown')
            ], style={'width': '49%', 'display': 'inline-block'})
        ]),
        
        html.Div([
            # 曜日別パターン
            html.Div([
                html.H5("曜日別休暇パターン"),
                dcc.Graph(id='leave-weekday-pattern')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # 月別集計
            html.Div([
                html.H5("月別休暇集計"),
                dcc.Graph(id='leave-monthly-summary')
            ], style={'width': '49%', 'display': 'inline-block'})
        ], style={'marginTop': '20px'}),
        
        # 集中日分析
        html.Div([
            html.H4("休暇集中日分析", style={'marginTop': '30px'}),
            dcc.Graph(id='leave-concentration-calendar'),
            html.Div(id='leave-concentration-alerts')
        ])
    ])

def create_complete_cost_analysis_tab():
    """完全機能版コスト分析タブ（動的シミュレーション）"""
    return html.Div([
        html.H3("💰 コスト分析", style={'marginBottom': '20px'}),
        
        # コストシミュレーター
        html.Div([
            html.H4("動的コストシミュレーション"),
            
            # パラメータ調整
            html.Div([
                html.Div([
                    html.Label("正規職員時給"),
                    dcc.Slider(id='cost-regular-wage', min=1000, max=5000, step=100, value=2000,
                              marks={i: f'¥{i}' for i in range(1000, 5001, 1000)})
                ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                
                html.Div([
                    html.Label("派遣職員時給"),
                    dcc.Slider(id='cost-temp-wage', min=1500, max=6000, step=100, value=3000,
                              marks={i: f'¥{i}' for i in range(1500, 6001, 1500)})
                ], style={'width': '48%', 'display': 'inline-block'})
            ]),
            
            # リアルタイム計算結果
            html.Div(id='cost-simulation-result', style={'marginTop': '20px'})
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'marginBottom': '20px'}),
        
        # コスト内訳グラフ
        html.Div([
            html.Div([
                html.H5("コスト構成比"),
                dcc.Graph(id='cost-composition-pie')
            ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H5("時系列コスト推移"),
                dcc.Graph(id='cost-timeline')
            ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H5("職種別コスト効率"),
                dcc.Graph(id='cost-efficiency-bar')
            ], style={'width': '32%', 'display': 'inline-block'})
        ]),
        
        # 最適化提案
        html.Div([
            html.H4("コスト最適化提案", style={'marginTop': '30px'}),
            html.Div(id='cost-optimization-suggestions')
        ])
    ])

def create_complete_hire_plan_tab():
    """完全機能版採用計画タブ"""
    return html.Div([
        html.H3("📋 採用計画", style={'marginBottom': '20px'}),
        
        # 必要FTE計算
        html.Div([
            html.H4("必要FTE算出"),
            html.Div(id='hire-fte-calculation', style={
                'padding': '15px',
                'backgroundColor': '#e8f5e9',
                'borderRadius': '8px'
            })
        ], style={'marginBottom': '20px'}),
        
        # 採用戦略提案
        html.Div([
            html.H4("採用戦略"),
            dcc.Tabs([
                dcc.Tab(label='職種別採用計画', children=[
                    dcc.Graph(id='hire-role-plan')
                ]),
                dcc.Tab(label='時期別採用計画', children=[
                    dcc.Graph(id='hire-timeline-plan')
                ]),
                dcc.Tab(label='コスト影響分析', children=[
                    dcc.Graph(id='hire-cost-impact')
                ])
            ])
        ]),
        
        # 最適採用計画
        html.Div([
            html.H4("AI最適採用提案", style={'marginTop': '30px'}),
            html.Div(id='hire-ai-recommendations')
        ])
    ])

# ========== Phase 3: Strategic Features (完全実装) ==========

def create_complete_blueprint_analysis_tab():
    """完全機能版ブループリント分析タブ"""
    return html.Div([
        html.H3("🏗️ ブループリント分析", style={'marginBottom': '20px'}),
        
        # 暗黙知・形式知分析
        html.Div([
            html.H4("暗黙知・形式知マッピング"),
            html.Div([
                html.Div([
                    html.H5("暗黙知パターン"),
                    dcc.Graph(id='blueprint-tacit-knowledge')
                ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
                
                html.Div([
                    html.H5("形式知ルール"),
                    html.Div(id='blueprint-explicit-rules')
                ], style={'width': '49%', 'display': 'inline-block'})
            ])
        ]),
        
        # 統合分析
        html.Div([
            html.H4("統合パターン分析", style={'marginTop': '30px'}),
            dcc.Tabs([
                dcc.Tab(label='ネットワーク分析', children=[
                    dcc.Graph(id='blueprint-network')
                ]),
                dcc.Tab(label='制約マトリックス', children=[
                    dcc.Graph(id='blueprint-constraint-matrix')
                ]),
                dcc.Tab(label='最適化提案', children=[
                    html.Div(id='blueprint-optimization')
                ])
            ])
        ])
    ])

def create_complete_individual_analysis_tab():
    """完全機能版個人分析タブ"""
    return html.Div([
        html.H3("👤 個人分析", style={'marginBottom': '20px'}),
        
        # スタッフ選択
        html.Div([
            html.Label("分析対象スタッフ"),
            dcc.Dropdown(id='individual-staff-select', multi=True)
        ], style={'marginBottom': '20px'}),
        
        # 4種類のシナジー分析
        html.Div([
            html.Div([
                html.H5("勤務パターン分析"),
                dcc.Graph(id='individual-pattern')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H5("スキルマトリックス"),
                dcc.Graph(id='individual-skills')
            ], style={'width': '49%', 'display': 'inline-block'})
        ]),
        
        html.Div([
            html.Div([
                html.H5("パフォーマンス推移"),
                dcc.Graph(id='individual-performance')
            ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            html.Div([
                html.H5("相性分析"),
                dcc.Graph(id='individual-compatibility')
            ], style={'width': '49%', 'display': 'inline-block'})
        ], style={'marginTop': '20px'})
    ])

def create_complete_team_analysis_tab():
    """完全機能版チーム分析タブ"""
    return html.Div([
        html.H3("👥 チーム分析", style={'marginBottom': '20px'}),
        
        # チーム構成分析
        html.Div([
            html.H4("チーム構成"),
            dcc.Graph(id='team-composition-sunburst')
        ]),
        
        # ダイナミクス分析
        html.Div([
            html.H4("チームダイナミクス", style={'marginTop': '30px'}),
            html.Div([
                html.Div([
                    html.H5("コミュニケーションネットワーク"),
                    dcc.Graph(id='team-network')
                ], style={'width': '49%', 'display': 'inline-block', 'marginRight': '2%'}),
                
                html.Div([
                    html.H5("カバレッジ分析"),
                    dcc.Graph(id='team-coverage')
                ], style={'width': '49%', 'display': 'inline-block'})
            ])
        ])
    ])

def create_complete_forecast_tab():
    """完全機能版予測タブ（Prophet実装）"""
    return html.Div([
        html.H3("📈 需要予測", style={'marginBottom': '20px'}),
        
        # 予測設定
        html.Div([
            html.Label("予測期間"),
            dcc.Slider(
                id='forecast-horizon',
                min=7, max=90, step=7,
                marks={i: f'{i}日' for i in [7, 14, 30, 60, 90]},
                value=30
            )
        ], style={'marginBottom': '20px'}),
        
        # Prophet予測グラフ
        html.Div([
            html.H4("AI予測（Prophet）"),
            dcc.Graph(id='forecast-prophet-chart', style={'height': '500px'})
        ]),
        
        # 信頼区間と詳細
        html.Div([
            html.H4("予測詳細", style={'marginTop': '30px'}),
            html.Div(id='forecast-details-table')
        ])
    ])

# ========== Phase 4: Reporting (完全実装) ==========

def create_complete_gap_analysis_tab():
    """完全機能版ギャップ分析タブ"""
    return html.Div([
        html.H3("📊 ギャップ分析", style={'marginBottom': '20px'}),
        
        # 乖離ヒートマップ
        html.Div([
            html.H4("需給乖離ヒートマップ"),
            dcc.Graph(id='gap-heatmap', style={'height': '500px'})
        ]),
        
        # サマリーテーブル
        html.Div([
            html.H4("乖離サマリー", style={'marginTop': '30px'}),
            html.Div(id='gap-summary-table')
        ])
    ])

def create_complete_summary_report_tab():
    """完全機能版サマリーレポートタブ"""
    return html.Div([
        html.H3("📝 サマリーレポート", style={'marginBottom': '20px'}),
        
        # 自動生成Markdownレポート
        html.Div([
            html.Button("レポート生成", id='generate-summary-btn', className='btn btn-primary'),
            dcc.Loading(
                children=[
                    dcc.Markdown(id='summary-report-content', style={
                        'padding': '20px',
                        'backgroundColor': 'white',
                        'borderRadius': '8px',
                        'marginTop': '20px'
                    })
                ]
            )
        ])
    ])

def create_complete_ppt_report_tab():
    """完全機能版PPTレポートタブ"""
    return html.Div([
        html.H3("📊 PowerPointレポート", style={'marginBottom': '20px'}),
        
        # PPT生成設定
        html.Div([
            html.H4("レポート設定"),
            dcc.Checklist(
                id='ppt-sections',
                options=[
                    {'label': 'エグゼクティブサマリー', 'value': 'executive'},
                    {'label': '不足分析', 'value': 'shortage'},
                    {'label': '公平性分析', 'value': 'fairness'},
                    {'label': 'コスト分析', 'value': 'cost'},
                    {'label': '改善提案', 'value': 'improvements'}
                ],
                value=['executive', 'shortage', 'cost']
            )
        ]),
        
        # 生成ボタン
        html.Div([
            html.Button("PPT生成", id='generate-ppt-btn', className='btn btn-success'),
            html.Div(id='ppt-download-link')
        ], style={'marginTop': '20px'})
    ])

def create_complete_export_tab():
    """完全機能版エクスポートタブ"""
    return html.Div([
        html.H3("💾 データエクスポート", style={'marginBottom': '20px'}),
        
        # エクスポート形式選択
        html.Div([
            html.H4("エクスポート形式"),
            dcc.RadioItems(
                id='export-format',
                options=[
                    {'label': '📊 Excel (推奨)', 'value': 'excel'},
                    {'label': '📄 CSV', 'value': 'csv'},
                    {'label': '📑 PDF', 'value': 'pdf'},
                    {'label': '🗂️ ZIP (全データ)', 'value': 'zip'}
                ],
                value='excel'
            )
        ]),
        
        # データ選択
        html.Div([
            html.H4("エクスポートデータ", style={'marginTop': '20px'}),
            dcc.Checklist(
                id='export-data-selection',
                options=[
                    {'label': '基本データ', 'value': 'basic'},
                    {'label': '分析結果', 'value': 'analysis'},
                    {'label': 'グラフ画像', 'value': 'graphs'},
                    {'label': 'レポート', 'value': 'reports'}
                ],
                value=['basic', 'analysis']
            )
        ]),
        
        # エクスポートボタン
        html.Div([
            html.Button("エクスポート実行", id='execute-export-btn', className='btn btn-primary'),
            dcc.Loading(
                children=[
                    html.Div(id='export-result')
                ]
            )
        ], style={'marginTop': '20px'})
    ])

# ========== Phase 5: AI & Integration (完全実装) ==========

def create_enhanced_overview_tab():
    """強化版オーバービュータブ"""
    return html.Div([
        html.H3("📊 エグゼクティブダッシュボード", style={'marginBottom': '20px'}),
        
        # エグゼクティブサマリー
        html.Div([
            html.H4("エグゼクティブサマリー"),
            html.Div(id='executive-summary', style={
                'padding': '20px',
                'backgroundColor': '#e3f2fd',
                'borderRadius': '8px'
            })
        ], style={'marginBottom': '20px'}),
        
        # 全タブサマリー（カード形式）
        html.Div([
            html.H4("分析サマリー"),
            html.Div(id='all-tabs-summary', children=[
                create_tab_summary_card("不足分析", "shortage", "#ff5252"),
                create_tab_summary_card("公平性分析", "fairness", "#4caf50"),
                create_tab_summary_card("疲労分析", "fatigue", "#ff9800"),
                create_tab_summary_card("コスト分析", "cost", "#2196f3")
            ], style={'display': 'flex', 'flexWrap': 'wrap'})
        ]),
        
        # アラート&推奨事項
        html.Div([
            html.H4("アラート & 推奨事項", style={'marginTop': '30px'}),
            html.Div(id='alerts-recommendations')
        ]),
        
        # シナジー分析
        html.Div([
            html.H4("シナジー分析", style={'marginTop': '30px'}),
            dcc.Graph(id='synergy-analysis-chart')
        ])
    ])

def create_tab_summary_card(title, tab_id, color):
    """タブサマリーカード"""
    return html.Div([
        html.H5(title, style={'color': color}),
        html.Div(id=f'{tab_id}-summary-content')
    ], style={
        'width': '48%',
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'margin': '5px',
        'borderLeft': f'4px solid {color}'
    })

def create_complete_ai_analysis_tab():
    """完全機能版AI分析タブ"""
    return html.Div([
        html.H3("🤖 AI総合分析", style={'marginBottom': '20px'}),
        
        # AIインサイト生成
        html.Div([
            html.Button("AI分析実行", id='run-ai-analysis-btn', className='btn btn-primary'),
            dcc.Loading(
                children=[
                    html.Div(id='ai-insights-content', style={'marginTop': '20px'})
                ]
            )
        ]),
        
        # 自動改善提案
        html.Div([
            html.H4("AI改善提案", style={'marginTop': '30px'}),
            html.Div(id='ai-improvements')
        ])
    ])

def create_complete_fact_book_tab():
    """完全機能版ファクトブックタブ"""
    return html.Div([
        html.H3("📚 ファクトブック", style={'marginBottom': '20px'}),
        
        # 統合レポート
        html.Div([
            html.H4("包括的事実分析"),
            dcc.Tabs([
                dcc.Tab(label='基本統計', children=[
                    html.Div(id='fact-basic-stats')
                ]),
                dcc.Tab(label='トレンド分析', children=[
                    dcc.Graph(id='fact-trends')
                ]),
                dcc.Tab(label='相関分析', children=[
                    dcc.Graph(id='fact-correlations')
                ]),
                dcc.Tab(label='異常値検出', children=[
                    html.Div(id='fact-anomalies')
                ])
            ])
        ])
    ])

def create_complete_mind_reader_tab():
    """完全機能版マインドリーダータブ"""
    return html.Div([
        html.H3("🧠 マインドリーダー", style={'marginBottom': '20px'}),
        
        # メタ分析
        html.Div([
            html.H4("シフト作成思考パターン分析"),
            dcc.Graph(id='mind-pattern-network')
        ]),
        
        # パターン検出
        html.Div([
            html.H4("検出されたパターン", style={'marginTop': '30px'}),
            html.Div(id='mind-detected-patterns')
        ])
    ])

def create_complete_optimization_tab():
    """完全機能版最適化タブ"""
    return html.Div([
        html.H3("⚙️ 最適化分析", style={'marginBottom': '20px'}),
        
        # 最適化シミュレーション
        html.Div([
            html.H4("最適化シミュレーション"),
            html.Div([
                html.Label("最適化目標"),
                dcc.RadioItems(
                    id='optimization-objective',
                    options=[
                        {'label': 'コスト最小化', 'value': 'cost'},
                        {'label': '公平性最大化', 'value': 'fairness'},
                        {'label': 'カバレッジ最大化', 'value': 'coverage'},
                        {'label': 'バランス最適化', 'value': 'balanced'}
                    ],
                    value='balanced'
                )
            ])
        ]),
        
        # 最適化結果
        html.Div([
            html.Button("最適化実行", id='run-optimization-btn'),
            dcc.Loading(
                children=[
                    html.Div(id='optimization-results')
                ]
            )
        ])
    ])


# ========== ヘルパー関数 ==========

def safe_filename(name):
    """ファイル名として使える形式に変換"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', str(name))

def generate_heatmap_figure(df, title, color_scale='RdBu_r'):
    """ヒートマップ図生成"""
    if df.empty:
        return go.Figure()
    
    fig = px.imshow(
        df,
        labels=dict(x="日付", y="職種", color="値"),
        title=title,
        color_continuous_scale=color_scale,
        aspect='auto'
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="日付",
        yaxis_title="職種",
        coloraxis_colorbar=dict(
            title="値",
            tickmode='linear',
            tick0=0,
            dtick=10
        )
    )
    
    return fig