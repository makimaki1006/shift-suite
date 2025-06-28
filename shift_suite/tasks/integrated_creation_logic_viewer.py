"""
シフト作成ロジックの完全解明結果を統合表示するビューア
"""
from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
from dash import dcc, html

from .shift_creation_logic_analyzer import ShiftCreationLogicAnalyzer
from .shift_creation_forensics import ShiftCreationForensics
from .shift_mind_reader import ShiftMindReader


def create_creation_logic_analysis_tab() -> html.Div:
    """Return layout for the creation logic analysis tab."""
    return html.Div([
        html.H3("シフト作成ロジック完全解明", style={"marginBottom": "20px"}),
        dcc.RadioItems(
            id="logic-analysis-depth",
            options=[
                {"label": "概要", "value": "basic"},
                {"label": "詳細", "value": "detailed"},
                {"label": "完全", "value": "complete"},
                {"label": "究極", "value": "ultimate"},
            ],
            value="basic",
            inline=True,
            style={"marginBottom": "10px"},
        ),
        html.Button(
            "シフト作成ロジックを解明",
            id="analyze-creation-logic-button",
            n_clicks=0,
            style={"marginLeft": "10px"},
        ),
        html.Div(id="logic-analysis-progress", style={"marginTop": "10px"}),
        dcc.Loading(
            id="logic-analysis-loading",
            type="default",
            children=html.Div(id="creation-logic-results"),
        ),
    ])


def run_integrated_logic_analysis(long_df: pd.DataFrame, depth: str) -> html.Div:
    """Execute all analyzers and return a summary view."""
    logic_analyzer = ShiftCreationLogicAnalyzer()
    forensics = ShiftCreationForensics()
    mind_reader = ShiftMindReader()

    results: Dict[str, Any] = {}

    if depth in ["basic", "detailed", "complete", "ultimate"]:
        results["logic_results"] = logic_analyzer.reverse_engineer_creation_process(long_df)
    if depth in ["detailed", "complete", "ultimate"]:
        results["forensics_results"] = forensics.full_forensic_analysis(long_df)
    if depth in ["complete", "ultimate"]:
        results["mind_results"] = mind_reader.read_creator_mind(long_df)

    return html.Pre(json.dumps(results, indent=2, ensure_ascii=False))
