#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
確実に動作するシンプルなシフト分析アプリ
"""

import dash
from dash import html, dcc, Input, Output
import pandas as pd
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(level=logging.ERROR)

# アプリ作成
app = dash.Dash(__name__)

# 基本データの確認
def check_data():
    """利用可能なデータを確認"""
    data_dir = Path("extracted_results")
    if data_dir.exists():
        scenario_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
        return scenario_dirs
    return []

# レイアウト
app.layout = html.Div([
    html.H1("シフト分析システム", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("機能選択:"),
        dcc.Dropdown(
            id='function-dropdown',
            options=[
                {'label': '概要', 'value': 'overview'},
                {'label': 'ヒートマップ', 'value': 'heatmap'},
                {'label': '不足分析', 'value': 'shortage'},
                {'label': 'データ確認', 'value': 'data'}
            ],
            value='overview'
        )
    ], style={'margin': '20px', 'padding': '10px'}),
    
    html.Div(id='content-area', style={'margin': '20px'})
])

@app.callback(
    Output('content-area', 'children'),
    Input('function-dropdown', 'value')
)
def update_content(selected):
    if selected == 'overview':
        return html.Div([
            html.H3("概要ダッシュボード"),
            html.P("システムが正常に動作しています。"),
            html.P("利用可能な機能を上のプルダウンから選択してください。")
        ])
    
    elif selected == 'data':
        scenarios = check_data()
        if scenarios:
            return html.Div([
                html.H3("データ確認"),
                html.P("利用可能なシナリオ:"),
                html.Ul([html.Li(str(s.name)) for s in scenarios])
            ])
        else:
            return html.Div([
                html.H3("データ確認"),
                html.P("データディレクトリが見つかりません。")
            ])
    
    elif selected == 'heatmap':
        return html.Div([
            html.H3("ヒートマップ分析"),
            html.P("時間帯別の配置状況を表示します。"),
            html.P("データ読み込み機能を準備中...")
        ])
    
    elif selected == 'shortage':
        return html.Div([
            html.H3("不足分析"),
            html.P("職種別・時間帯別の人員不足を分析します。"),
            html.P("分析機能を準備中...")
        ])
    
    return html.P("機能を選択してください。")

if __name__ == '__main__':
    print("シンプルなシフト分析アプリを起動中...")
    app.run_server(debug=False, host='127.0.0.1', port=8082)