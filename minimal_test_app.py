#!/usr/bin/env python3
"""
最小限のテストアプリ - Bootstrap依存なし
"""
import dash
from dash import html, dcc
from dash.dependencies import Input, Output

# Dashアプリの初期化（外部CSSを使用）
app = dash.Dash(__name__, assets_folder='assets')

# インラインCSSでより強力に指定
app.layout = html.Div([
    html.H1("テストアプリ", style={
        'color': '#000000 !important', 
        'fontSize': '32px',
        'fontWeight': 'bold'
    }),
    html.P("このテキストが見えますか？", style={
        'color': '#000000 !important', 
        'fontSize': '18px',
        'fontWeight': '600'
    }),
    
    html.Div([
        html.Label("プルダウンテスト:", style={
            'color': '#000000 !important', 
            'fontSize': '16px',
            'fontWeight': '600'
        }),
        dcc.Dropdown(
            id='test-dropdown',
            options=[
                {'label': 'オプション1', 'value': '1'},
                {'label': 'オプション2', 'value': '2'},
                {'label': 'オプション3', 'value': '3'}
            ],
            value='1',
            style={
                'width': '200px', 
                'color': '#000000 !important',
                'fontWeight': '600'
            }
        )
    ], style={'margin': '20px 0'}),
    
    html.Div(id='output', style={
        'color': '#000000 !important', 
        'fontSize': '16px', 
        'margin': '20px 0',
        'fontWeight': '600'
    })
], style={
    'padding': '20px',
    'backgroundColor': '#ffffff',
    'color': '#000000 !important',
    'fontFamily': 'Arial, sans-serif'
})

@app.callback(
    Output('output', 'children'),
    Input('test-dropdown', 'value')
)
def update_output(value):
    return f"選択された値: {value}"

if __name__ == '__main__':
    print("最小限テストアプリを起動...")
    print("ブラウザで http://127.0.0.1:8052 にアクセス")
    app.run(debug=True, port=8052)