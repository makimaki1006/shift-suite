"""Dash callbacks for the enhanced blueprint analysis tab."""
from __future__ import annotations

from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px


def register_enhanced_callbacks(app) -> None:
    """Register callbacks enabling progressive blueprint analysis."""

    @app.long_callback(
        output=Output("enhanced-blueprint-results", "children"),
        inputs=Input("enhanced-blueprint-analyze-button", "n_clicks"),
        state=[State("blueprint-analysis-mode", "value"), State("data-loaded", "data")],
        running=[
            (Output("enhanced-blueprint-analyze-button", "disabled"), True, False),
            (Output("analysis-progress-bar", "style"), {"display": "block"}, {"display": "none"}),
        ],
        progress=[
            Output("analysis-progress-bar", "figure"),
            Output("analysis-progress-text", "children"),
        ],
        prevent_initial_call=True,
    )
    def run_analysis_and_render(set_progress, n_clicks, mode, data_status):  # pragma: no cover - dash callback
        """Run both basic and advanced analysis while updating progress."""
        if not n_clicks:
            return html.Div()

        set_progress((0, "分析準備中..."))
        from shift_suite.tasks.blueprint_analyzer import create_blueprint_list
        from shift_suite.tasks.advanced_implicit_knowledge_engine import AdvancedImplicitKnowledgeEngine

        long_df = pd.read_json(data_status["long_df_json"], orient="split")

        # basic analysis first
        set_progress((20, "基本分析を実行中..."))
        basic_results = create_blueprint_list(long_df)
        basic_display = create_basic_analysis_display(basic_results)

        # heavy advanced analysis
        set_progress((50, "高度な暗黙知を発見中..."))
        engine = AdvancedImplicitKnowledgeEngine()
        advanced_results = engine.discover_all_implicit_knowledge(long_df)
        advanced_display = create_advanced_analysis_display(advanced_results)

        set_progress((100, "分析完了！"))
        return html.Div([
            html.H3("分析結果", style={"textAlign": "center"}),
            html.Div(basic_display),
            html.Hr(),
            html.Div(advanced_display),
        ])

    @app.callback(
        Output("modal-team-details", "is_open"),
        Output("modal-team-content", "children"),
        Input("knowledge-network-graph", "clickData"),
        prevent_initial_call=True,
    )
    def display_team_details(clickData):  # pragma: no cover - dash callback
        if not clickData or not clickData.get("nodes"):
            return False, None
        node_id = clickData["nodes"][0]
        team_info = f"チーム {node_id} の詳細情報..."
        return True, html.Div([html.H4("コアチーム詳細"), html.P(team_info)])


def create_basic_analysis_display(results: dict) -> dash_table.DataTable | html.Div:
    df = pd.DataFrame(results.get("rules_df", []))
    if df.empty:
        return html.P("基本分析結果なし")
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
    )


def create_advanced_analysis_display(results: dict) -> dcc.Markdown:
    summary = results.get("summary", "高度な分析結果なし")
    return dcc.Markdown(summary)


def create_feature_importance_graph(importance_df: pd.DataFrame) -> dcc.Graph:
    """Generate an interactive bar chart showing feature importance."""
    if importance_df is None or importance_df.empty:
        fig = px.bar(title="シフト作成における判断基準 TOP10")
    else:
        fig = px.bar(
            importance_df.head(10).sort_values("importance", ascending=True),
            x="importance",
            y="feature",
            orientation="h",
            title="シフト作成における判断基準 TOP10",
            labels={"importance": "重要度スコア", "feature": "判断基準"},
            template="plotly_white",
        )
        fig.update_layout(margin=dict(l=150), title_x=0.5)
    return dcc.Graph(figure=fig)
