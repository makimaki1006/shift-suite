"""シフト作成ロジックの完全解明結果を統合表示するビューア"""
from dash import dcc, html


def create_creation_logic_analysis_tab() -> html.Div:
    """シフト作成ロジック完全解明タブのレイアウト"""
    return html.Div([
        html.H3("🧠 シフト作成ロジック完全解明"),
        html.P(
            "AIがシフト作成者の思考プロセスを解読し、どのような優先順位と判断基準でシフトが作られているかを明らかにします。"
        ),
        html.Button(
            "🚀 シフト作成ロジックを解明",
            id="analyze-creation-logic-button",
            n_clicks=0,
            style={"marginTop": "20px", "marginBottom": "20px"},
        ),
        dcc.Loading(
            id="loading-creation-logic",
            type="circle",
            children=html.Div(id="creation-logic-results"),
        ),
    ])
