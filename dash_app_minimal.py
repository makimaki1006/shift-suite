#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小構成のDashアプリで動作確認
"""

import dash
from dash import html, dcc
from dash.dependencies import Input, Output

# 最小Dashアプリ
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("動作確認アプリ"),
    html.P("このアプリが正常に表示されれば、基本的なDash機能は動作しています。"),
    
    dcc.Dropdown(
        id='test-dropdown',
        options=[
            {'label': 'オプション1', 'value': '1'},
            {'label': 'オプション2', 'value': '2'}
        ],
        value='1'
    ),
    
    html.Div(id='test-output')
])

@app.callback(
    Output('test-output', 'children'),
    Input('test-dropdown', 'value')
)
def update_output(value):
    return f"選択された値: {value}"

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8060)