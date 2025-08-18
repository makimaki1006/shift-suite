import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

# 最小限のテストデータ
df = pd.DataFrame({
    'x': [1, 2, 3, 4],
    'y': [10, 11, 12, 13]
})

app.layout = html.Div([
    html.H1("シフト分析システム - 緊急テスト版", 
            style={'textAlign': 'center', 'color': 'blue'}),
    
    html.Div([
        html.H3("システム状態"),
        html.P("✅ Dashアプリケーション起動成功"),
        html.P("✅ 基本UI表示成功"),
        html.P("✅ ユーザーアクセス可能")
    ], style={'margin': '20px', 'padding': '20px', 'border': '1px solid #ccc'}),
    
    html.Div([
        html.H3("テストグラフ"),
        dcc.Graph(
            figure=px.line(df, x='x', y='y', title='接続テスト')
        )
    ], style={'margin': '20px'})
])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8051, debug=True)