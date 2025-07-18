#!/usr/bin/env python3
"""
advanced_features_app.py - 高度機能専用アプリケーション
════════════════════════════════════════════════════════════════════════════════

このアプリは、Shift-Suiteの高度機能（Tier 1〜3）のみを提供します：
- 高度予測（SARIMA, Prophet, LSTM）
- 季節性分析（時系列分解、スペクトル解析）
- 疲労度予測（ディープラーニング）
- 離職リスク予測（機械学習）

使用方法:
    python advanced_features_app.py

要件:
    pip install -r requirements.txt  # 全ライブラリが必要
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# メイン設定
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# 基本設定
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Dashアプリ初期化
app = dash.Dash(
    __name__,
    title="Shift-Suite Advanced Features",
    suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
    ]
)

# サンプルデータ生成関数
def generate_sample_data():
    """デモ用のサンプルデータを生成"""
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    
    # 基本的な時系列データ
    np.random.seed(42)
    base_demand = 50 + 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)  # 年次周期
    weekly_pattern = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)  # 週次周期
    noise = np.random.normal(0, 5, len(dates))
    demand = base_demand + weekly_pattern + noise
    
    # 需要データ
    demand_df = pd.DataFrame({
        'ds': dates,
        'y': np.maximum(0, demand)  # 負の値は0にクリップ
    })
    
    # シフトデータ（long形式）
    staff_names = [f"スタッフ{i:02d}" for i in range(1, 21)]
    roles = ['看護師', '准看護師', '介護士', '事務員']
    employments = ['正職員', '非常勤', 'パート']
    
    shift_data = []
    for date in dates[::7]:  # 週次でサンプリング
        for staff in staff_names[:10]:  # 10名のスタッフ
            # ランダムなシフト生成
            if np.random.random() > 0.2:  # 80%の確率で勤務
                start_time = np.random.choice(['08:00', '16:00', '00:00'])
                for hour in range(8):  # 8時間勤務
                    shift_data.append({
                        'ds': pd.to_datetime(f"{date.date()} {start_time}") + pd.Timedelta(hours=hour),
                        'staff': staff,
                        'role': np.random.choice(roles),
                        'employment': np.random.choice(employments),
                        'code': f"WORK_{hour}"
                    })
    
    shift_df = pd.DataFrame(shift_data)
    
    return demand_df, shift_df

# レイアウト
app.layout = html.Div([
    # ヘッダー
    html.Div([
        html.H1("🚀 Shift-Suite Advanced Features", className="text-primary mb-0"),
        html.P("高度予測・分析機能専用アプリケーション", className="text-muted")
    ], className="container-fluid bg-light py-3 mb-4"),
    
    # メインコンテンツ
    html.Div([
        # 機能選択タブ
        dcc.Tabs(id="advanced-tabs", value="forecast-tab", children=[
            dcc.Tab(label="🔮 高度予測", value="forecast-tab"),
            dcc.Tab(label="📈 需要予測", value="demand-forecast-tab"),
            dcc.Tab(label="🔍 ロジック解明", value="logic-analysis-tab"),
            dcc.Tab(label="📊 季節性分析", value="seasonal-tab"),
            dcc.Tab(label="😴 疲労度予測", value="fatigue-tab"),
            dcc.Tab(label="⚠️ 離職リスク", value="turnover-tab"),
        ]),
        
        # タブコンテンツ
        html.Div(id="tab-content", className="mt-4"),
        
        # データ状態
        dcc.Store(id="sample-data-store"),
        
    ], className="container-fluid")
])

# データ初期化
@app.callback(
    Output('sample-data-store', 'data'),
    Input('advanced-tabs', 'value')
)
def initialize_data(tab_value):
    """サンプルデータを初期化"""
    demand_df, shift_df = generate_sample_data()
    return {
        'demand': demand_df.to_dict('records'),
        'shift': shift_df.to_dict('records')
    }

# タブコンテンツ切り替え
@app.callback(
    Output('tab-content', 'children'),
    [Input('advanced-tabs', 'value'),
     Input('sample-data-store', 'data')]
)
def render_tab_content(active_tab, data):
    """タブに応じたコンテンツを表示"""
    if not data:
        return html.Div("データを読み込み中...", className="text-center")
    
    if active_tab == "forecast-tab":
        return create_forecast_tab()
    elif active_tab == "demand-forecast-tab":
        return create_demand_forecast_tab()
    elif active_tab == "logic-analysis-tab":
        return create_logic_analysis_tab()
    elif active_tab == "seasonal-tab":
        return create_seasonal_tab()
    elif active_tab == "fatigue-tab":
        return create_fatigue_tab()
    elif active_tab == "turnover-tab":
        return create_turnover_tab()
    
    return html.Div("タブが選択されていません。")

def create_forecast_tab():
    """高度予測タブのコンテンツ"""
    return html.Div([
        html.H3("🔮 高度予測分析", className="mb-4"),
        
        html.Div([
            html.H5("予測モデルの選択"),
            dcc.Checklist(
                id='forecast-models',
                options=[
                    {'label': ' SARIMA（季節性自己回帰統合移動平均）', 'value': 'sarima'},
                    {'label': ' Prophet（Facebook時系列予測）', 'value': 'prophet'},
                    {'label': ' LSTM（長短期記憶ネットワーク）', 'value': 'lstm'},
                ],
                value=['sarima', 'prophet'],
                className="mb-3"
            ),
            
            html.Div([
                html.Label("予測期間（日数）："),
                dcc.Slider(
                    id='forecast-periods',
                    min=7, max=90, step=7, value=30,
                    marks={i: f'{i}日' for i in [7, 14, 30, 60, 90]},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], className="mb-3"),
            
            html.Button('予測実行', id='run-forecast-btn', 
                       className='btn btn-primary', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='forecast-results')
    ])

def create_seasonal_tab():
    """季節性分析タブのコンテンツ"""
    return html.Div([
        html.H3("📊 季節性パターン分析", className="mb-4"),
        
        html.Div([
            html.H5("分析手法の選択"),
            dcc.Checklist(
                id='seasonal-methods',
                options=[
                    {'label': ' 時系列分解（STL・古典的）', 'value': 'decomposition'},
                    {'label': ' スペクトル解析（FFT）', 'value': 'spectral'},
                    {'label': ' 祝日効果分析', 'value': 'holiday'},
                    {'label': ' パターンクラスタリング', 'value': 'clustering'},
                ],
                value=['decomposition', 'spectral'],
                className="mb-3"
            ),
            
            html.Button('分析実行', id='run-seasonal-btn', 
                       className='btn btn-success', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='seasonal-results')
    ])

def create_fatigue_tab():
    """疲労度予測タブのコンテンツ"""
    return html.Div([
        html.H3("😴 疲労度予測", className="mb-4"),
        
        html.Div([
            html.H5("予測設定"),
            html.Div([
                html.Label("予測日数："),
                dcc.Slider(
                    id='fatigue-days',
                    min=3, max=14, step=1, value=7,
                    marks={i: f'{i}日' for i in [3, 7, 14]},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], className="mb-3"),
            
            html.Div([
                html.Label("モデルタイプ："),
                dcc.RadioItems(
                    id='fatigue-model',
                    options=[
                        {'label': 'LSTM', 'value': 'lstm'},
                        {'label': 'GRU', 'value': 'gru'},
                        {'label': 'ハイブリッド', 'value': 'hybrid'},
                    ],
                    value='lstm',
                    className="mb-3"
                )
            ]),
            
            html.Button('予測実行', id='run-fatigue-btn', 
                       className='btn btn-warning', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='fatigue-results')
    ])

def create_turnover_tab():
    """離職リスク予測タブのコンテンツ"""
    return html.Div([
        html.H3("⚠️ 離職リスク予測", className="mb-4"),
        
        html.Div([
            html.H5("予測設定"),
            html.Div([
                html.Label("分析期間（月数）："),
                dcc.Slider(
                    id='turnover-months',
                    min=3, max=12, step=1, value=6,
                    marks={i: f'{i}ヶ月' for i in [3, 6, 9, 12]},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], className="mb-3"),
            
            html.Div([
                html.Label("機械学習モデル："),
                dcc.RadioItems(
                    id='turnover-model',
                    options=[
                        {'label': 'アンサンブル（推奨）', 'value': 'ensemble'},
                        {'label': 'ランダムフォレスト', 'value': 'random_forest'},
                        {'label': 'XGBoost', 'value': 'xgboost'},
                        {'label': 'ロジスティック回帰', 'value': 'logistic'},
                    ],
                    value='ensemble',
                    className="mb-3"
                )
            ]),
            
            html.Button('予測実行', id='run-turnover-btn', 
                       className='btn btn-danger', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='turnover-results')
    ])

# 高度予測実行
@app.callback(
    Output('forecast-results', 'children'),
    [Input('run-forecast-btn', 'n_clicks')],
    [State('forecast-models', 'value'),
     State('forecast-periods', 'value'),
     State('sample-data-store', 'data')]
)
def run_forecast_analysis(n_clicks, models, periods, data):
    """高度予測を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        # サンプルデータから実際のライブラリを使用した予測を実行
        from shift_suite.tasks.advanced_forecast import AdvancedForecastEngine
        
        # データフレーム復元
        demand_df = pd.DataFrame(data['demand'])
        demand_df['ds'] = pd.to_datetime(demand_df['ds'])
        
        # 予測エンジン初期化
        engine = AdvancedForecastEngine(
            enable_sarima='sarima' in models,
            enable_prophet='prophet' in models,
            enable_lstm='lstm' in models,
            enable_ensemble=len(models) > 1
        )
        
        # モデル訓練
        fit_results = engine.fit_all_models(demand_df)
        
        # 予測実行
        predictions = engine.predict(periods=periods)
        
        # 結果の可視化
        fig = go.Figure()
        
        # 実績データ
        fig.add_trace(go.Scatter(
            x=demand_df['ds'], y=demand_df['y'],
            mode='lines', name='実績', line=dict(color='blue')
        ))
        
        # 予測データ
        colors = {'sarima': 'red', 'prophet': 'green', 'lstm': 'purple', 'ensemble': 'orange'}
        for model in models:
            if model in predictions.columns:
                fig.add_trace(go.Scatter(
                    x=predictions['ds'], y=predictions[model],
                    mode='lines', name=f'{model.upper()}予測',
                    line=dict(color=colors.get(model, 'gray'), dash='dash')
                ))
        
        if 'ensemble' in predictions.columns:
            fig.add_trace(go.Scatter(
                x=predictions['ds'], y=predictions['ensemble'],
                mode='lines', name='アンサンブル予測',
                line=dict(color='orange', width=3)
            ))
        
        fig.update_layout(
            title=f"高度予測結果（{periods}日間）",
            xaxis_title="日付", yaxis_title="需要",
            height=500, template="plotly_white"
        )
        
        # 精度情報
        summary = engine.get_model_summary()
        
        results = [
            dcc.Graph(figure=fig),
            html.H5("モデル精度", className="mt-4"),
            html.Div([
                html.P(f"最良モデル: {summary['best_model'].upper()}", className="fw-bold"),
                html.Div([
                    html.P(f"{model}: MAPE {metrics['mape']:.2f}%")
                    for model, metrics in summary['metrics'].items()
                ])
            ], className="card p-3")
        ]
        
        return results
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}"),
            html.P("必要なライブラリがインストールされているか確認してください。")
        ], className="alert alert-danger")

# 季節性分析実行
@app.callback(
    Output('seasonal-results', 'children'),
    [Input('run-seasonal-btn', 'n_clicks')],
    [State('seasonal-methods', 'value'),
     State('sample-data-store', 'data')]
)
def run_seasonal_analysis(n_clicks, methods, data):
    """季節性分析を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        from shift_suite.tasks.seasonal_analysis import SeasonalAnalysisEngine
        
        # データフレーム復元
        shift_df = pd.DataFrame(data['shift'])
        shift_df['ds'] = pd.to_datetime(shift_df['ds'])
        
        # 分析エンジン初期化
        engine = SeasonalAnalysisEngine(
            enable_decomposition='decomposition' in methods,
            enable_spectral='spectral' in methods,
            enable_holiday_effects='holiday' in methods,
            enable_clustering='clustering' in methods
        )
        
        # 時系列データ準備
        time_series_data = engine.prepare_time_series_data(shift_df)
        
        # 分析実行
        results = engine.analyze_all_seasonality(time_series_data)
        
        # 結果表示
        content = [html.H5("季節性分析結果", className="mt-4")]
        
        if results['decomposition']:
            content.append(html.H6("時系列分解"))
            for series_name, decomp in results['decomposition'].items():
                content.append(html.P(
                    f"{series_name}: 季節性強度 {decomp['seasonal_strength']:.3f}, "
                    f"トレンド強度 {decomp['trend_strength']:.3f}"
                ))
        
        if results['spectral']:
            content.append(html.H6("スペクトル解析"))
            for series_name, spectral in results['spectral'].items():
                periods = spectral.get('dominant_periods', [])[:3]
                content.append(html.P(
                    f"{series_name}: 主要周期 {[f'{p:.1f}日' for p in periods if p > 0]}"
                ))
        
        return html.Div(content, className="card p-3")
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}"),
        ], className="alert alert-danger")

# 疲労度予測実行
@app.callback(
    Output('fatigue-results', 'children'),
    [Input('run-fatigue-btn', 'n_clicks')],
    [State('fatigue-days', 'value'),
     State('fatigue-model', 'value'),
     State('sample-data-store', 'data')]
)
def run_fatigue_prediction(n_clicks, days, model_type, data):
    """疲労度予測を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        from shift_suite.tasks.fatigue_prediction import FatiguePredictionEngine
        
        # データフレーム復元
        shift_df = pd.DataFrame(data['shift'])
        shift_df['ds'] = pd.to_datetime(shift_df['ds'])
        
        # 予測エンジン初期化
        engine = FatiguePredictionEngine(
            lookback_days=14,
            forecast_days=days,
            model_type=model_type,
            enable_personal_patterns=True
        )
        
        # 特徴量抽出
        features_df = engine.extract_fatigue_features(shift_df)
        
        if features_df.empty:
            return html.Div("特徴量の抽出に失敗しました。", className="alert alert-warning")
        
        # 疲労スコア計算
        fatigue_df = engine.calculate_fatigue_score(features_df)
        
        # モデル訓練
        global_result = engine.train_global_model(fatigue_df)
        
        # 結果表示
        content = [
            html.H5("疲労度予測結果", className="mt-4"),
            html.P(f"分析対象スタッフ数: {len(fatigue_df['staff'].unique())}"),
            html.P(f"予測期間: {days}日"),
            html.P(f"使用モデル: {model_type.upper()}")
        ]
        
        if global_result['success']:
            content.extend([
                html.P(f"モデル精度 - MAE: {global_result['mae']:.4f}, RMSE: {global_result['rmse']:.4f}"),
            ])
        
        return html.Div(content, className="card p-3")
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}"),
        ], className="alert alert-danger")

# 離職リスク予測実行
@app.callback(
    Output('turnover-results', 'children'),
    [Input('run-turnover-btn', 'n_clicks')],
    [State('turnover-months', 'value'),
     State('turnover-model', 'value'),
     State('sample-data-store', 'data')]
)
def run_turnover_prediction(n_clicks, months, model_type, data):
    """離職リスク予測を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        from shift_suite.tasks.turnover_prediction import TurnoverPredictionEngine
        
        # データフレーム復元
        shift_df = pd.DataFrame(data['shift'])
        shift_df['ds'] = pd.to_datetime(shift_df['ds'])
        
        # 予測エンジン初期化
        engine = TurnoverPredictionEngine(
            model_type=model_type,
            lookback_months=months,
            enable_early_warning=True
        )
        
        # 特徴量抽出
        features_df = engine.extract_turnover_features(shift_df)
        
        if features_df.empty:
            return html.Div("特徴量の抽出に失敗しました。", className="alert alert-warning")
        
        # 合成ラベル生成
        features_with_labels = engine.generate_synthetic_labels(features_df)
        
        # モデル用データ準備
        X, y, feature_names = engine.prepare_model_data(features_with_labels)
        
        # モデル訓練
        training_results = engine.train_models(X, y, feature_names)
        
        # 予測実行
        predictions_df = engine.predict_turnover_risk(features_with_labels)
        
        # アラート生成
        alerts = engine.generate_risk_alerts(predictions_df)
        
        # 結果表示
        content = [
            html.H5("離職リスク予測結果", className="mt-4"),
            html.P(f"分析対象スタッフ数: {len(predictions_df)}"),
            html.P(f"分析期間: {months}ヶ月"),
            html.P(f"使用モデル: {model_type.upper()}")
        ]
        
        if not predictions_df.empty:
            risk_counts = predictions_df['risk_level'].value_counts()
            content.extend([
                html.H6("リスクレベル分布"),
                html.Ul([
                    html.Li(f"{level}: {count}名")
                    for level, count in risk_counts.items()
                ])
            ])
        
        if alerts:
            content.extend([
                html.H6("アラート"),
                html.Ul([
                    html.Li(f"{alert['type']}: {alert['message']}")
                    for alert in alerts[:5]  # 最初の5件
                ])
            ])
        
        return html.Div(content, className="card p-3")
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}"),
        ], className="alert alert-danger")

def create_demand_forecast_tab():
    """需要予測タブのコンテンツ"""
    return html.Div([
        html.H3("📈 需要予測分析", className="mb-4"),
        
        html.Div([
            html.H5("基本需要予測"),
            html.P("Prophet モデルを使用した需要予測機能です。"),
            
            html.Div([
                html.Label("予測期間（日数）："),
                dcc.Slider(
                    id='demand-forecast-periods',
                    min=7, max=60, step=7, value=14,
                    marks={i: f'{i}日' for i in [7, 14, 21, 30, 60]},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], className="mb-3"),
            
            html.Button('需要予測実行', id='run-demand-forecast-btn', 
                       className='btn btn-primary', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='demand-forecast-results')
    ])

def create_logic_analysis_tab():
    """ロジック解明タブのコンテンツ"""
    return html.Div([
        html.H3("🔍 ロジック解明", className="mb-4"),
        
        html.Div([
            html.H5("シフト作成ロジック分析"),
            html.P("シフト作成の意思決定プロセスとパターンを分析します。"),
            
            html.Div([
                html.Label("分析対象："),
                dcc.RadioItems(
                    id='logic-analysis-target',
                    options=[
                        {'label': '全体パターン', 'value': 'overall'},
                        {'label': '職種別ロジック', 'value': 'by_role'},
                        {'label': '時間帯別ロジック', 'value': 'by_time'},
                        {'label': '個人別パターン', 'value': 'by_staff'},
                    ],
                    value='overall',
                    className="mb-3"
                )
            ]),
            
            html.Button('ロジック分析実行', id='run-logic-analysis-btn', 
                       className='btn btn-info', n_clicks=0),
        ], className="card p-3 mb-4"),
        
        # 結果表示エリア
        html.Div(id='logic-analysis-results')
    ])

# 需要予測実行
@app.callback(
    Output('demand-forecast-results', 'children'),
    [Input('run-demand-forecast-btn', 'n_clicks')],
    [State('demand-forecast-periods', 'value'),
     State('sample-data-store', 'data')]
)
def run_demand_forecast_analysis(n_clicks, periods, data):
    """需要予測を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        # サンプルデータから需要予測を実行
        from prophet import Prophet
        
        # データフレーム復元
        demand_df = pd.DataFrame(data['demand'])
        demand_df['ds'] = pd.to_datetime(demand_df['ds'])
        
        # Prophet モデル訓練
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        model.fit(demand_df)
        
        # 未来の予測
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # 結果の可視化
        fig = go.Figure()
        
        # 実績データ
        fig.add_trace(go.Scatter(
            x=demand_df['ds'], y=demand_df['y'],
            mode='lines', name='実績', line=dict(color='blue')
        ))
        
        # 予測データ
        forecast_future = forecast[forecast['ds'] > demand_df['ds'].max()]
        fig.add_trace(go.Scatter(
            x=forecast_future['ds'], y=forecast_future['yhat'],
            mode='lines+markers', name='予測',
            line=dict(color='red', dash='dash')
        ))
        
        # 信頼区間
        fig.add_trace(go.Scatter(
            x=forecast_future['ds'], y=forecast_future['yhat_upper'],
            mode='lines', name='上限', line=dict(color='lightcoral', width=1),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=forecast_future['ds'], y=forecast_future['yhat_lower'],
            mode='lines', name='下限', line=dict(color='lightcoral', width=1),
            fill='tonexty', fillcolor='rgba(255,182,193,0.3)',
            showlegend=False
        ))
        
        fig.update_layout(
            title=f"需要予測結果（{periods}日間）",
            xaxis_title="日付", yaxis_title="需要",
            height=500, template="plotly_white"
        )
        
        # 予測統計
        future_avg = forecast_future['yhat'].mean()
        future_max = forecast_future['yhat'].max()
        future_min = forecast_future['yhat'].min()
        
        results = [
            dcc.Graph(figure=fig),
            html.H5("予測統計", className="mt-4"),
            html.Div([
                html.P(f"予測期間平均: {future_avg:.1f}"),
                html.P(f"予測最大値: {future_max:.1f}"),
                html.P(f"予測最小値: {future_min:.1f}")
            ], className="card p-3")
        ]
        
        return results
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}")
        ], className="alert alert-danger")

# ロジック分析実行
@app.callback(
    Output('logic-analysis-results', 'children'),
    [Input('run-logic-analysis-btn', 'n_clicks')],
    [State('logic-analysis-target', 'value'),
     State('sample-data-store', 'data')]
)
def run_logic_analysis(n_clicks, target, data):
    """ロジック分析を実行"""
    if n_clicks == 0 or not data:
        return html.Div()
    
    try:
        # データフレーム復元
        shift_df = pd.DataFrame(data['shift'])
        shift_df['ds'] = pd.to_datetime(shift_df['ds'])
        
        # 基本統計
        total_shifts = len(shift_df)
        unique_staff = shift_df['staff'].nunique()
        
        if target == 'overall':
            # 全体パターン分析
            hourly_pattern = shift_df.groupby(shift_df['ds'].dt.hour).size()
            daily_pattern = shift_df.groupby(shift_df['ds'].dt.dayofweek).size()
            
            content = [
                html.H5("全体パターン分析"),
                html.P(f"総シフト数: {total_shifts}"),
                html.P(f"スタッフ数: {unique_staff}"),
                html.H6("時間帯別分布"),
                dcc.Graph(figure=px.bar(
                    x=hourly_pattern.index, y=hourly_pattern.values,
                    title="時間帯別シフト数", labels={'x': '時間', 'y': 'シフト数'}
                )),
                html.H6("曜日別分布"),
                dcc.Graph(figure=px.bar(
                    x=daily_pattern.index, y=daily_pattern.values,
                    title="曜日別シフト数", labels={'x': '曜日', 'y': 'シフト数'}
                ))
            ]
            
        elif target == 'by_role':
            # 職種別分析
            role_stats = shift_df.groupby('role').agg({
                'staff': 'nunique',
                'ds': 'count'
            }).rename(columns={'staff': 'スタッフ数', 'ds': 'シフト数'}).reset_index()
            
            content = [
                html.H5("職種別ロジック分析"),
                dcc.Graph(figure=px.bar(
                    role_stats, x='role', y='シフト数',
                    title="職種別シフト数", color='role'
                )),
                dash_table.DataTable(
                    data=role_stats.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in role_stats.columns]
                )
            ]
            
        else:
            content = [
                html.H5(f"{target} 分析"),
                html.P("この分析タイプは準備中です。")
            ]
        
        return html.Div(content, className="card p-3")
        
    except Exception as e:
        return html.Div([
            html.H5("エラーが発生しました", className="text-danger"),
            html.P(f"詳細: {str(e)}")
        ], className="alert alert-danger")

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                    🚀 Shift-Suite Advanced Features                          ║
    ║                          高度機能専用アプリケーション                            ║
    ╠══════════════════════════════════════════════════════════════════════════════╣
    ║ 📊 提供機能:                                                                  ║
    ║   • 高度予測 (SARIMA, Prophet, LSTM)                                        ║
    ║   • 需要予測 (Prophet基本モデル)                                               ║
    ║   • ロジック解明 (シフト作成パターン分析)                                       ║
    ║   • 季節性分析 (時系列分解, スペクトル解析)                                     ║
    ║   • 疲労度予測 (ディープラーニング)                                            ║
    ║   • 離職リスク予測 (機械学習)                                                  ║
    ║                                                                              ║
    ║ 🌐 URL: http://127.0.0.1:8051                                               ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app.run_server(debug=True, port=8051, host='127.0.0.1')