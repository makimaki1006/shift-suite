"""Dash callbacks for the enhanced blueprint analysis tab."""
from __future__ import annotations

import base64
import io
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
# sklearn import removed - plot_tree functionality disabled
# from sklearn.tree import plot_tree

def plot_tree(*args, **kwargs):
    """Dummy plot_tree function to replace sklearn dependency"""
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.text(0.5, 0.5, 'Decision Tree Visualization\nDisabled due to sklearn dependency', 
             horizontalalignment='center', verticalalignment='center', 
             transform=plt.gca().transAxes, fontsize=14)
    plt.axis('off')
    return plt.gca()


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
        advanced_results = engine.discover_all_implicit_knowledge(
            long_df,
            progress_callback=set_progress,
        )
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


def create_thinking_summary(model) -> dcc.Markdown:
    """Return a short natural language summary of the first tree split."""
    if not model or not hasattr(model, "tree_"):
        return dcc.Markdown("思考サマリーを生成できませんでした。")
    feature_names = getattr(model, "feature_names_in_", None)
    feature_idx = int(model.tree_.feature[0])
    threshold = float(model.tree_.threshold[0])
    if feature_idx == -2:
        return dcc.Markdown("決定木に有効な分岐がありません。")
    label = feature_names[feature_idx] if feature_names is not None else str(feature_idx)
    text = f"最初の判断基準は **{label}** が {threshold:.2f} を超えるかどうかです。"
    return dcc.Markdown(text)


def create_full_decision_tree_graph(model) -> html.Img:
    """Render the entire decision tree as a static image."""
    if not model or not hasattr(model, "tree_"):
        return html.Img()
    buf = io.BytesIO()
    fig, ax = plt.subplots(figsize=(16, 10))
    plot_tree(
        model,
        filled=True,
        feature_names=getattr(model, "feature_names_in_", None),
        fontsize=8,
        ax=ax,
        impurity=False,
        proportion=True,
    )
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    encoded = base64.b64encode(buf.getvalue()).decode()
    return html.Img(src=f"data:image/png;base64,{encoded}", style={"width": "100%", "maxWidth": "1200px"})


def create_full_importance_table(importance_df: pd.DataFrame) -> dash_table.DataTable:
    """Show all feature importances sorted by score."""
    if importance_df is None or importance_df.empty:
        return dash_table.DataTable(data=[], columns=[])
    df = importance_df.sort_values("importance", ascending=False)
    tooltip = {
        "feature": {"value": "判断基準項目", "type": "markdown"},
        "importance": {"value": "モデルが重視する度合い", "type": "markdown"},
    }
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        tooltip_header=tooltip,
        sort_action="native",
        page_size=20,
    )


def create_knowledge_card(rule: dict) -> html.Div:
    """Generate a clickable card summarising one implicit rule."""
    rule_id = rule.get("id", 0)
    strength = float(rule.get("strength", 0))
    progress_style = {
        "width": f"{strength * 100:.0f}%",
        "height": "100%",
        "backgroundColor": "#428bca",
        "borderRadius": "4px",
    }
    return html.Div(
        id={"type": "knowledge-card", "index": rule_id},
        children=[
            html.H5(rule.get("category", ""), style={"marginBottom": "5px"}),
            html.P(rule.get("description", ""), style={"fontSize": "14px"}),
            html.Div(
                [html.Div(style=progress_style)],
                style={
                    "height": "8px",
                    "backgroundColor": "#e0e0e0",
                    "borderRadius": "4px",
                    "marginTop": "5px",
                },
            ),
        ],
        style={
            "border": "1px solid #ccc",
            "borderRadius": "8px",
            "padding": "10px",
            "margin": "5px",
            "cursor": "pointer",
            "width": "200px",
        },
    )
