#!/usr/bin/env python3
"""
最小限動作バージョン - 段階的復旧用
"""

import dash
from dash import html, dcc, Input, Output
import sys
import os

# 最小限の設定
app = dash.Dash(__name__, assets_folder='assets')

# 最もシンプルなレイアウト
app.layout = html.Div([
    html.H1("🧪 最小限テスト", style={'color': '#000000'}),
    
    dcc.Dropdown(
        id='simple-dropdown',
        options=[
            {'label': '概要ダッシュボード', 'value': 'overview'},
            {'label': 'ヒートマップ', 'value': 'heatmap'},
            {'label': '不足分析', 'value': 'shortage'},
            {'label': '🧠 作成ブループリント', 'value': 'blueprint_analysis'},
            {'label': '📚 統合ファクトブック', 'value': 'fact_book_analysis'},
            {'label': '🔧 MECE制約抽出', 'value': 'mece_constraint_system'},
            {'label': '🔍 ロジック解明', 'value': 'logic_analysis'}
        ],
        value='overview',
        style={'margin': '20px 0'}
    ),
    
    html.Div(id='simple-output', style={'padding': '20px'})
])

@app.callback(
    Output('simple-output', 'children'),
    Input('simple-dropdown', 'value')
)
def update_output(value):
    """最小限のコールバック"""
    return html.Div([
        html.H3(f"✅ 選択: {value}"),
        html.P("基本機能が正常に動作しています。"),
        html.Hr(),
        html.P("🎯 次のステップ: 複雑な機能を段階的に追加")
    ])

if __name__ == '__main__':
    print("最小限Dashアプリ開始...")
    print("URL: http://127.0.0.1:8052/")
    app.run(debug=True, port=8052, host='127.0.0.1')