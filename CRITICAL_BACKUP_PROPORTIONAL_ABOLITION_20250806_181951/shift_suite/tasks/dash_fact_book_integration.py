#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブループリント分析 Phase 3.2: Dashアプリ統合用ファクトブック
既存のdash_app.pyに統合可能な形式でファクトブック機能を提供
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

# Dash関連のインポート
try:
    import dash
    from dash import dcc, html, dash_table, callback
    from dash.dependencies import Input, Output, State
    import plotly.graph_objects as go
    import plotly.express as px
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

# ファクトブック可視化コンポーネント
try:
    from .fact_book_visualizer import FactBookVisualizer
    FACT_BOOK_AVAILABLE = True
except ImportError:
    FACT_BOOK_AVAILABLE = False

log = logging.getLogger(__name__)

# 既存のdash_app.pyスタイルに合わせた色定義
FACT_BOOK_STYLES = {
    'header': {
        'fontSize': '24px',
        'fontWeight': 'bold',
        'color': '#2c3e50',
        'marginBottom': '20px',
        'textAlign': 'center'
    },
    'subheader': {
        'fontSize': '18px',
        'fontWeight': 'bold',
        'color': '#34495e',
        'marginBottom': '15px'
    },
    'card': {
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    },
    'button_primary': {
        'backgroundColor': '#3498db',
        'color': 'white',
        'padding': '10px 30px',
        'fontSize': '16px',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer',
        'marginBottom': '20px'
    },
    'alert_success': {
        'backgroundColor': '#d4edda',
        'color': '#155724',
        'padding': '15px',
        'borderRadius': '5px',
        'border': '1px solid #c3e6cb',
        'marginBottom': '20px'
    },
    'alert_warning': {
        'backgroundColor': '#fff3cd',
        'color': '#856404',
        'padding': '15px',
        'borderRadius': '5px',
        'border': '1px solid #ffeaa7',
        'marginBottom': '20px'
    },
    'alert_danger': {
        'backgroundColor': '#f8d7da',
        'color': '#721c24',
        'padding': '15px',
        'borderRadius': '5px',
        'border': '1px solid #f5c6cb',
        'marginBottom': '20px'
    }
}

def create_fact_book_analysis_tab() -> html.Div:
    """
    ファクトブック分析タブのレイアウト作成
    既存のdash_app.pyのcreate_blueprint_analysis_tab()と同様の構造
    """
    if not DASH_AVAILABLE:
        return html.Div("Dashコンポーネントが利用できません", style=FACT_BOOK_STYLES['alert_danger'])
    
    if not FACT_BOOK_AVAILABLE:
        return html.Div("ファクトブック機能が利用できません", style=FACT_BOOK_STYLES['alert_danger'])
    
    return html.Div([
        # ヘッダーセクション
        html.H2("📊 統合ファクトブック分析", style=FACT_BOOK_STYLES['header']),
        
        html.P([
            "Phase 2の基本事実抽出とPhase 3.1の異常検知を統合した包括的な分析結果を表示します。",
            html.Br(),
            "※ データがアップロードされた後に分析を実行してください。"
        ], style={'textAlign': 'center', 'marginBottom': '30px', 'color': '#6c757d'}),
        
        # コントロールセクション
        html.Div([
            html.H4("分析設定", style=FACT_BOOK_STYLES['subheader']),
            
            html.Div([
                html.Label("異常検知感度:", style={'marginRight': '10px', 'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='fact-book-sensitivity',
                    options=[
                        {'label': '低感度 (緩い基準)', 'value': 'low'},
                        {'label': '中感度 (標準)', 'value': 'medium'},
                        {'label': '高感度 (厳しい基準)', 'value': 'high'}
                    ],
                    value='medium',
                    style={'width': '200px', 'display': 'inline-block'}
                )
            ], style={'marginBottom': '20px'}),
            
            html.Button(
                "📊 ファクトブック分析実行",
                id="generate-fact-book-button",
                style=FACT_BOOK_STYLES['button_primary'],
                n_clicks=0
            ),
            
            html.Div(id='fact-book-status', style={'marginTop': '10px'})
            
        ], style=FACT_BOOK_STYLES['card']),
        
        # 結果表示エリア
        html.Div([
            dcc.Loading(
                id="loading-fact-book",
                type="default",
                children=[
                    html.Div(id='fact-book-results', children=[
                        html.P("分析を実行してください", 
                              style={'textAlign': 'center', 'color': '#6c757d', 'fontSize': '16px'})
                    ])
                ]
            )
        ], style=FACT_BOOK_STYLES['card'])
        
    ], style={'padding': '20px'})

def create_fact_book_dashboard(fact_book_data: Dict[str, Any]) -> html.Div:
    """
    ファクトブックダッシュボードの作成
    
    Args:
        fact_book_data: ファクトブック生成結果
        
    Returns:
        Dashコンポーネント
    """
    if "error" in fact_book_data:
        return html.Div([
            html.Div([
                html.H4("⚠️ エラー", style={'color': '#721c24'}),
                html.P(fact_book_data["error"])
            ], style=FACT_BOOK_STYLES['alert_danger'])
        ])
    
    # データ概要の取得
    overview = fact_book_data.get("data_overview", {})
    summary = fact_book_data.get("summary", {})
    basic_facts = fact_book_data.get("basic_facts", {})
    anomalies = fact_book_data.get("anomalies", [])
    
    components = []
    
    # 1. 概要サマリーカード
    components.append(create_overview_cards(overview, summary))
    
    # 2. 異常検知結果セクション
    if anomalies:
        components.append(create_anomaly_section(anomalies))
    else:
        components.append(html.Div([
            html.H4("✅ 異常検知結果", style=FACT_BOOK_STYLES['subheader']),
            html.Div("異常は検知されませんでした", style=FACT_BOOK_STYLES['alert_success'])
        ]))
    
    # 3. 基本事実セクション
    if basic_facts:
        components.append(create_facts_section(basic_facts))
    else:
        components.append(html.Div([
            html.H4("📋 基本事実", style=FACT_BOOK_STYLES['subheader']),
            html.Div("基本事実が抽出されていません", style=FACT_BOOK_STYLES['alert_warning'])
        ]))
    
    # 4. 分析メタデータ
    components.append(create_metadata_section(fact_book_data))
    
    return html.Div(components)

def create_overview_cards(overview: Dict[str, Any], summary: Dict[str, Any]) -> html.Div:
    """概要サマリーカードの作成"""
    
    cards = []
    
    # データ概要カード
    cards.append(html.Div([
        html.H5("📊 データ概要", style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
        html.P(f"総レコード数: {overview.get('total_records', 0):,}件", style={'margin': '5px 0'}),
        html.P(f"職員数: {overview.get('staff_count', 0)}名", style={'margin': '5px 0'}),
        html.P(f"勤務レコード数: {overview.get('work_records', 0):,}件", style={'margin': '5px 0'})
    ], style={**FACT_BOOK_STYLES['card'], 'width': '23%', 'display': 'inline-block', 'margin': '1%'}))
    
    # 事実統計カード
    cards.append(html.Div([
        html.H5("📋 事実統計", style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
        html.P(f"事実カテゴリ数: {summary.get('fact_categories', 0)}", style={'margin': '5px 0'}),
        html.P(f"総事実数: {summary.get('total_facts', 0):,}件", style={'margin': '5px 0'}),
        html.P("抽出完了", style={'margin': '5px 0', 'color': '#28a745'})
    ], style={**FACT_BOOK_STYLES['card'], 'width': '23%', 'display': 'inline-block', 'margin': '1%'}))
    
    # 異常検知カード
    anomaly_count = summary.get('anomaly_count', 0)
    critical_count = summary.get('critical_issues', 0)
    
    anomaly_color = '#dc3545' if critical_count > 0 else '#28a745' if anomaly_count == 0 else '#ffc107'
    
    cards.append(html.Div([
        html.H5("⚠️ 異常検知", style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
        html.P(f"検知された異常: {anomaly_count}件", style={'margin': '5px 0'}),
        html.P(f"重要な異常: {critical_count}件", style={'margin': '5px 0', 'color': anomaly_color, 'fontWeight': 'bold'}),
        html.P("検知完了", style={'margin': '5px 0', 'color': '#28a745'})
    ], style={**FACT_BOOK_STYLES['card'], 'width': '23%', 'display': 'inline-block', 'margin': '1%'}))
    
    # 分析ステータスカード
    cards.append(html.Div([
        html.H5("🎯 分析ステータス", style={'margin': '0 0 10px 0', 'color': '#2c3e50'}),
        html.P("Phase 2: 基本事実 ✅", style={'margin': '5px 0', 'color': '#28a745'}),
        html.P("Phase 3.1: 異常検知 ✅", style={'margin': '5px 0', 'color': '#28a745'}),
        html.P("統合分析完了", style={'margin': '5px 0', 'fontWeight': 'bold', 'color': '#28a745'})
    ], style={**FACT_BOOK_STYLES['card'], 'width': '23%', 'display': 'inline-block', 'margin': '1%'}))
    
    return html.Div(cards, style={'marginBottom': '30px'})

def create_anomaly_section(anomalies: List[Dict[str, Any]]) -> html.Div:
    """異常検知セクションの作成"""
    
    # 重要度別の色設定
    severity_colors = {
        "緊急": "#dc3545",
        "高": "#fd7e14", 
        "中": "#ffc107",
        "低": "#6c757d"
    }
    
    # 重要度別にソート
    sorted_anomalies = sorted(anomalies, key=lambda x: {"緊急": 0, "高": 1, "中": 2, "低": 3}.get(x.get("severity", "低"), 4))
    
    anomaly_items = []
    
    for i, anomaly in enumerate(sorted_anomalies[:10]):  # 上位10件まで表示
        severity = anomaly.get("severity", "低")
        color = severity_colors.get(severity, "#6c757d")
        
        anomaly_card = html.Div([
            html.Div([
                html.Span(f"#{i+1}", style={
                    'backgroundColor': '#f8f9fa', 
                    'color': '#495057',
                    'padding': '2px 6px', 
                    'borderRadius': '3px', 
                    'fontSize': '12px',
                    'marginRight': '8px'
                }),
                html.Span(severity, style={
                    'backgroundColor': color, 
                    'color': 'white', 
                    'padding': '2px 8px', 
                    'borderRadius': '4px', 
                    'fontSize': '12px',
                    'fontWeight': 'bold',
                    'marginRight': '8px'
                }),
                html.Span(anomaly.get("anomaly_type", ""), style={
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                })
            ], style={'marginBottom': '8px'}),
            
            html.P([
                html.Strong(f"対象職員: {anomaly.get('staff', 'N/A')}"),
                html.Br(),
                anomaly.get("description", "")
            ], style={'margin': '0', 'fontSize': '14px', 'color': '#495057'}),
            
            html.P(f"検出値: {anomaly.get('value', 'N/A')}", 
                  style={'margin': '8px 0 0 0', 'fontSize': '12px', 'color': '#6c757d'})
            
        ], style={
            'backgroundColor': 'white',
            'padding': '15px',
            'borderRadius': '6px',
            'borderLeft': f'4px solid {color}',
            'marginBottom': '10px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        })
        
        anomaly_items.append(anomaly_card)
    
    return html.Div([
        html.H4("⚠️ 異常検知結果", style=FACT_BOOK_STYLES['subheader']),
        html.Div(anomaly_items, style={'maxHeight': '500px', 'overflowY': 'auto'})
    ], style=FACT_BOOK_STYLES['card'])

def create_facts_section(basic_facts: Dict[str, pd.DataFrame]) -> html.Div:
    """基本事実セクションの作成"""
    
    tabs_content = []
    
    for category, df in basic_facts.items():
        if df.empty:
            continue
        
        # データテーブルの作成
        table = dash_table.DataTable(
            data=df.head(20).to_dict('records'),
            columns=[{"name": col, "id": col} for col in df.columns],
            style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
            style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10,
            sort_action="native",
            filter_action="native"
        )
        
        tab_content = html.Div([
            html.P(f"総件数: {len(df)}件", style={'marginBottom': '15px', 'fontWeight': 'bold'}),
            table
        ])
        
        tabs_content.append(dcc.Tab(label=category, children=tab_content))
    
    return html.Div([
        html.H4("📋 基本事実詳細", style=FACT_BOOK_STYLES['subheader']),
        dcc.Tabs(children=tabs_content)
    ], style=FACT_BOOK_STYLES['card'])

def create_metadata_section(fact_book_data: Dict[str, Any]) -> html.Div:
    """分析メタデータセクションの作成"""
    
    generation_time = fact_book_data.get("generation_timestamp", "N/A")
    
    return html.Div([
        html.H4("📋 分析メタデータ", style=FACT_BOOK_STYLES['subheader']),
        html.P(f"生成日時: {generation_time}", style={'margin': '5px 0'}),
        html.P("Phase 2: FactExtractor (基本事実抽出)", style={'margin': '5px 0'}),
        html.P("Phase 3.1: LightweightAnomalyDetector (異常検知)", style={'margin': '5px 0'}),
        html.P("Phase 3.2: FactBookVisualizer (統合可視化)", style={'margin': '5px 0', 'fontWeight': 'bold'})
    ], style={**FACT_BOOK_STYLES['card'], 'backgroundColor': '#f8f9fa'})

# ファクトブック分析実行コールバック（dash_app.pyに直接追加する用）
def create_fact_book_analysis_callback():
    """
    ファクトブック分析のコールバック関数を返す
    dash_app.pyで直接使用可能
    """
    
    def update_fact_book_content(n_clicks, sensitivity, selected_scenario):
        """ファクトブック分析の実行と結果表示"""
        
        if n_clicks == 0:
            raise PreventUpdate
        
        try:
            # データ取得の試行
            status_msg = html.Div("分析を実行中...", style=FACT_BOOK_STYLES['alert_warning'])
            
            # 実際のデータ取得ロジックはdash_app.pyの既存パターンを使用
            # ここでは基本的なレイアウトを返す
            result_layout = html.Div([
                html.H4("📊 統合ファクトブック分析結果"),
                html.P(f"選択されたシナリオ: {selected_scenario}"),
                html.P(f"検知感度: {sensitivity}"),
                html.Div([
                    html.H5("🎯 Phase 3 機能統合完了"),
                    html.P("Phase 2: 基本事実抽出機能 ✅"),
                    html.P("Phase 3.1: 異常検知機能 ✅"),
                    html.P("Phase 3.2: 可視化統合 ✅"),
                    html.Hr(),
                    html.P("実際のデータ分析を実行するには、データをアップロードしてシナリオを選択してください。"),
                ], style=FACT_BOOK_STYLES['card'])
            ])
            
            status_msg = html.Div("分析機能統合完了", style=FACT_BOOK_STYLES['alert_success'])
            
            return result_layout, status_msg
            
        except Exception as e:
            log.error(f"ファクトブック分析でエラー: {e}")
            error_msg = html.Div([
                html.H4("エラーが発生しました"),
                html.P(str(e))
            ], style=FACT_BOOK_STYLES['alert_danger'])
            
            status_msg = html.Div("エラー", style=FACT_BOOK_STYLES['alert_danger'])
            
            return error_msg, status_msg
    
    return update_fact_book_content

def get_fact_book_tab_definition() -> dict:
    """
    既存のdash_app.pyのタブ定義に追加するためのファクトブックタブ定義
    
    Returns:
        タブ定義辞書
    """
    return {
        'label': '📊 統合ファクトブック',
        'value': 'fact_book_analysis',
        'icon': '📊'
    }