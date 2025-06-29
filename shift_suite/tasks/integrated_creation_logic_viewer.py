"""シフト作成ロジックの完全解明結果を統合表示するビューア"""
from dash import dcc, html


def create_creation_logic_analysis_tab() -> html.Div:
    """Improved layout for the logic analysis tab."""
    return html.Div([
        html.H3("🧠 シフト作成ロジック完全解明"),
        html.P(
            "AIがシフト作成者の思考プロセスを解読し、判断基準を明らかにします。",
        ),
        html.Div([
            html.Label("分析の詳細度："),
            dcc.RadioItems(
                id="analysis-detail-level",
                options=[
                    {"label": "高速（簡易分析）", "value": "fast"},
                    {"label": "標準", "value": "standard"},
                    {"label": "詳細（時間がかかります）", "value": "detailed"},
                ],
                value="fast",
                inline=True,
            ),
        ], style={"marginBottom": "20px"}),
        html.Button(
            "🚀 シフト作成ロジックを解明",
            id="analyze-creation-logic-button",
            n_clicks=0,
            style={
                "marginTop": "10px",
                "marginBottom": "20px",
                "padding": "10px 20px",
                "fontSize": "16px",
            },
        ),
        html.Div(
            id="estimated-time",
            children="予想処理時間: 約10秒",
            style={"color": "#666", "fontSize": "14px", "marginBottom": "20px"},
        ),
        dcc.Loading(
            id="loading-creation-logic",
            type="default",
            children=html.Div(id="creation-logic-results"),
        ),
    ])
