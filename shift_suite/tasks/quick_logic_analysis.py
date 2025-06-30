"""Utilities for fast shift logic analysis."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
from dash import dcc, html
from sklearn.tree import DecisionTreeClassifier

log = logging.getLogger(__name__)


def get_basic_shift_stats(df: pd.DataFrame) -> dict:
    """Return simple summary statistics for a shift DataFrame."""
    return {
        "total_records": len(df),
        "unique_staff": df["staff"].nunique(),
        "date_range": f"{df['ds'].min().date()} 〜 {df['ds'].max().date()}",
        "unique_shifts": df["code"].nunique() if "code" in df.columns else "N/A",
        "avg_daily_staff": df.groupby(df["ds"].dt.date)["staff"].nunique().mean(),
    }


def get_quick_patterns(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Detect quick patterns using a small sample."""
    patterns: list[dict[str, Any]] = []
    if "code" in df.columns and not df.empty:
        top_code = df["code"].value_counts().head(1)
        if not top_code.empty:
            patterns.append(
                {
                    "type": "頻出勤務",
                    "description": f"最も多い勤務パターンは「{top_code.index[0]}」"
                    f"({top_code.values[0]}回)",
                }
            )
    if not df.empty:
        hour_counts = df["ds"].dt.hour.value_counts().head(1)
        if not hour_counts.empty:
            patterns.append(
                {
                    "type": "繁忙時間",
                    "description": f"最も忙しい時間帯は{hour_counts.index[0]}時台",
                }
            )
        df["is_weekend"] = df["ds"].dt.dayofweek.isin([5, 6])
        weekend_ratio = df["is_weekend"].mean()
        patterns.append(
            {
                "type": "週末稼働",
                "description": f"週末の稼働率は{weekend_ratio:.1%}",
            }
        )
    return patterns


def create_minimal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate lightweight features for training."""
    features = pd.DataFrame()
    hour_counts = df.groupby(df["ds"].dt.hour).size()
    for hour in range(24):
        features[f"hour_{hour}_count"] = [hour_counts.get(hour, 0)]
    dow_counts = df.groupby(df["ds"].dt.dayofweek).size()
    for dow in range(7):
        features[f"dow_{dow}_count"] = [dow_counts.get(dow, 0)]
    features["unique_staff"] = [df["staff"].nunique()]
    features["total_slots"] = [len(df)]
    if "code" in df.columns:
        mode_val = df["code"].mode()
        features["most_common_code"] = [mode_val.iloc[0] if not mode_val.empty else "unknown"]
    return features


def create_dummy_target(df: pd.DataFrame) -> np.ndarray:
    """Create a dummy target variable for analysis."""
    daily_ratio = df.groupby(df["ds"].dt.date).apply(
        lambda x: x["code"].astype(str).str.contains("\u591c", na=False).sum() / len(x)
    )
    median_ratio = daily_ratio.median()
    targets = (daily_ratio <= median_ratio).astype(int)
    df["date"] = df["ds"].dt.date
    df_with_target = df.merge(targets.to_frame("target"), left_on="date", right_index=True, how="left")
    return df_with_target["target"].fillna(0).values[: len(df)]


def run_ultra_light_analysis(df: pd.DataFrame) -> dict:
    """Run a fast analysis on at most 500 samples."""
    sample_size = min(500, len(df))
    sample_df = df.sample(n=sample_size) if len(df) > sample_size else df
    results: dict[str, Any] = {}
    try:
        features = create_minimal_features(sample_df)
        y = create_dummy_target(sample_df)
        model = DecisionTreeClassifier(max_depth=2, min_samples_split=50, min_samples_leaf=20)
        model.fit(features, y)
        importance = (
            pd.DataFrame({"feature": features.columns, "importance": model.feature_importances_})
            .nlargest(5, "importance")
        )
        results["feature_importance"] = importance.to_dict("records")
        results["simple_tree"] = model
    except Exception as exc:  # pragma: no cover - safety log
        log.error("light analysis failed: %s", exc)
        results["error"] = str(exc)
    return results


def run_optimized_analysis(df: pd.DataFrame) -> dict:
    """Placeholder for a slower but thorough analysis."""
    return run_ultra_light_analysis(df)


def create_stats_cards(stats: dict) -> html.Div:
    """Return cards displaying statistics."""
    cards = []
    label_map = {
        "total_records": "総レコード数",
        "unique_staff": "スタッフ数",
        "date_range": "分析期間",
        "unique_shifts": "シフト種類",
        "avg_daily_staff": "日平均スタッフ数",
    }
    for key, value in stats.items():
        card = html.Div(
            [
                html.Div(label_map.get(key, key), style={"fontSize": "12px", "color": "#666"}),
                html.Div(
                    f"{value:.1f}" if isinstance(value, (int, float)) else str(value),
                    style={"fontSize": "20px", "fontWeight": "bold"},
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "15px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "width": "150px",
                "display": "inline-block",
                "margin": "5px",
            },
        )
        cards.append(card)
    return html.Div(cards)


def create_pattern_list(patterns: List[Dict[str, Any]]) -> html.Div:
    """Display detected patterns in a list."""
    items = []
    for pattern in patterns:
        items.append(
            html.Div(
                [
                    html.Span(
                        f"【{pattern['type']}】",
                        style={"fontWeight": "bold", "color": "#1f77b4"},
                    ),
                    html.Span(f" {pattern['description']}")
                ],
                style={"marginBottom": "10px"},
            )
        )
    return html.Div(items, style={"backgroundColor": "#f5f5f5", "padding": "15px", "borderRadius": "5px"})


def generate_simple_tree_explanation(tree_model: DecisionTreeClassifier) -> str:
    """Generate a simple text explanation for the decision tree."""
    if not hasattr(tree_model, "tree_"):
        return "分析結果の説明を生成できません"
    n_nodes = tree_model.tree_.node_count
    depth = tree_model.get_depth()
    return (
        "\nシフト作成の判断プロセス:\n"
        f"- 主に{depth}段階の判断で構成\n"
        f"- {n_nodes}個の判断ポイントを特定\n"
        "- 最も重要な要素から順に評価\n"
    )


def create_deep_analysis_display(results: Dict[str, Any]) -> html.Div:
    """Visualise the output from a deep analysis."""
    if "error" in results:
        return html.Div(
            [
                html.P("詳細分析は完了できませんでしたが、基本分析結果をご確認ください。"),
                html.P(f"エラー: {results['error']}", style={"fontSize": "12px", "color": "#999"}),
            ]
        )
    sections = []
    imp = results.get("feature_importance")
    if imp:
        fig = px.bar(pd.DataFrame(imp), x="importance", y="feature", orientation="h", title="シフト作成の重要な要素")
        fig.update_layout(height=250)
        sections.append(html.Div([dcc.Graph(figure=fig, config={"displayModeBar": False})]))
    tree = results.get("simple_tree")
    if tree:
        tree_text = generate_simple_tree_explanation(tree)
        sections.append(
            html.Div(
                [
                    html.H6("判断の流れ"),
                    html.Pre(
                        tree_text,
                        style={
                            "backgroundColor": "#f9f9f9",
                            "padding": "10px",
                            "borderRadius": "5px",
                            "fontSize": "12px",
                        },
                    ),
                ]
            )
        )
    return html.Div(sections) if sections else html.P("詳細分析結果なし")

