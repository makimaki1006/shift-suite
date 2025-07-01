"""Dash callbacks for enhanced blueprint analysis tab."""
from __future__ import annotations


import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
import pandas as pd


def create_enhanced_blueprint_tab() -> html.Div:
    """Return the layout for the enhanced blueprint tab."""
    return html.Div(
        [
            html.H3("\U0001F9E0 Enhanced Blueprint Analysis"),
            html.Button("Run", id="enhanced-blueprint-analyze-button", n_clicks=0),
            html.Div(id="enhanced-blueprint-results"),
        ]
    )


def register_enhanced_callbacks(app):
    """Register callbacks for enhanced blueprint analysis."""

    @app.callback(
        Output("enhanced-blueprint-results", "children"),
        Input("enhanced-blueprint-analyze-button", "n_clicks"),
        State("data-loaded", "data"),
        prevent_initial_call=True,
    )
    def _run_analysis(n_clicks, _status):
        long_df = app.server.config.get("long_df", pd.DataFrame())
        if long_df.empty:
            return html.Div("No data loaded")
        from .shift_creation_process_reconstructor import ShiftCreationProcessReconstructor
        recon = ShiftCreationProcessReconstructor()
        result = recon.reconstruct_creation_process(long_df)
        return dcc.Markdown(f"**decisions**: {result.get('decision_count', 0)}")


def create_progress_bar(progress: float, message: str) -> go.Figure:
    """Utility to show progress."""
    fig = go.Figure(
        go.Bar(x=[progress], y=["progress"], orientation="h", text=[f"{progress}%"])
    )
    fig.update_layout(xaxis={"range": [0, 100]}, height=40, title=message)
    return fig
