"""
Missing functions for dash_app.py
"""

from dash import html, dcc
import plotly.graph_objects as go

def create_overview_section(data=None):
    """概要セクションを作成"""
    return html.Div([
        html.H3("概要"),
        html.P("データの概要を表示します"),
        html.Hr()
    ])

def create_kpi_cards(metrics=None):
    """KPIカードを作成"""
    if metrics is None:
        metrics = {
            "total": 0,
            "average": 0,
            "max": 0,
            "min": 0
        }

    return html.Div([
        html.Div([
            html.H4("合計"),
            html.P(str(metrics.get("total", 0)))
        ], style={'display': 'inline-block', 'margin': '10px'}),
        html.Div([
            html.H4("平均"),
            html.P(str(metrics.get("average", 0)))
        ], style={'display': 'inline-block', 'margin': '10px'}),
        html.Div([
            html.H4("最大"),
            html.P(str(metrics.get("max", 0)))
        ], style={'display': 'inline-block', 'margin': '10px'}),
        html.Div([
            html.H4("最小"),
            html.P(str(metrics.get("min", 0)))
        ], style={'display': 'inline-block', 'margin': '10px'})
    ])

def create_chart_section(chart_data=None):
    """チャートセクションを作成"""
    if chart_data is None:
        # デフォルトの空グラフ
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[], mode='lines'))
        fig.update_layout(title="データチャート")
    else:
        fig = chart_data

    return html.Div([
        html.H3("チャート"),
        dcc.Graph(figure=fig)
    ])

def create_analysis_section(analysis_results=None):
    """分析セクションを作成"""
    if analysis_results is None:
        analysis_results = "分析結果がありません"

    return html.Div([
        html.H3("分析結果"),
        html.P(analysis_results),
        html.Hr()
    ])

def create_info_card(title="情報", content="内容"):
    """情報カードを作成"""
    return html.Div([
        html.Div([
            html.H4(title),
            html.P(content)
        ], style={
            'border': '1px solid #ddd',
            'border-radius': '5px',
            'padding': '15px',
            'margin': '10px'
        })
    ])