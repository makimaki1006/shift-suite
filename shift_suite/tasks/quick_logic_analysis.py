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


def create_minimal_features(df: pd.DataFrame, all_possible_codes: list[str]) -> pd.DataFrame:
    """Generate lightweight features for training with stable dummy columns."""
    features = pd.DataFrame()

    # 1. hour based counts
    hour_counts = df.groupby(df["ds"].dt.hour).size()
    for hour in range(24):
        features[f"hour_{hour}_count"] = [hour_counts.get(hour, 0)]

    # 2. day-of-week counts
    dow_counts = df.groupby(df["ds"].dt.dayofweek).size()
    for dow in range(7):
        features[f"dow_{dow}_count"] = [dow_counts.get(dow, 0)]

    # 3. staff and slot statistics
    features["unique_staff"] = [df["staff"].nunique()]
    features["total_slots"] = [len(df)]

    # 4. most common code dummy variables across all_possible_codes
    if "code" in df.columns and all_possible_codes:
        mode_val = df["code"].mode()
        most_common_code = mode_val.iloc[0] if not mode_val.empty else "unknown"

        code_series = pd.Series([most_common_code])
        code_categorical = pd.Categorical(code_series, categories=all_possible_codes)
        dummies = pd.get_dummies(code_categorical, prefix="most_common_code")

        for col in dummies.columns:
            features[col] = [dummies[col].iloc[0]]

    return features


def create_standard_features(daily_group: pd.DataFrame, all_possible_codes: list[str]) -> pd.DataFrame:
    """標準モード用の中程度の粒度の特徴量を生成する"""
    # 高速版の特徴量をベースにする
    features = create_minimal_features(daily_group, all_possible_codes)

    # 1. 勤務間隔の統計
    if not daily_group.empty:
        daily_group = daily_group.sort_values("ds")
        rest_hours = (daily_group["ds"].diff().dt.total_seconds() / 3600).fillna(0)
        features["avg_rest_hours"] = [rest_hours.mean()]
        features["min_rest_hours"] = [rest_hours.min()]

    # 2. 勤務コードの多様性
    if "code" in daily_group.columns:
        features["unique_code_ratio"] = [
            daily_group["code"].nunique() / len(all_possible_codes) if all_possible_codes else 0
        ]

    return features


def run_ultra_light_analysis(df: pd.DataFrame) -> dict:
    """10秒以内で完了する超軽量分析（日単位集計版）"""

    sample_size = min(500, len(df))
    sample_df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
    results: dict[str, Any] = {}

    try:
        # --- ▼▼▼ 新しいロジック ▼▼▼ ---

        # 1. 日単位でデータをグループ化
        daily_groups = sample_df.groupby(sample_df["ds"].dt.date)

        X_daily: list[pd.DataFrame] = []
        y_daily: list[int] = []

        all_codes = df["code"].unique().tolist() if "code" in df.columns else []

        # 全データから夜勤率の中央値を計算（比較基準を統一するため）
        global_median_night_ratio = df.groupby(df["ds"].dt.date).apply(
            lambda x: x["code"].astype(str).str.contains("夜", na=False).sum() / len(x) if len(x) > 0 else 0
        ).median()

        for date, group in daily_groups:
            if group.empty:
                continue

            # 2. 1日分の特徴量ベクトルを生成
            daily_features = create_minimal_features(group, all_possible_codes=all_codes)
            X_daily.append(daily_features)

            # 3. 1日分の正解ラベルを生成
            night_ratio = group["code"].astype(str).str.contains("夜", na=False).sum() / len(group) if len(group) > 0 else 0
            y_daily.append(1 if night_ratio <= global_median_night_ratio else 0)

        if not X_daily:
            raise ValueError("日単位での分析データが生成できませんでした。")

        # 日ごとの特徴量を一つのデータフレームに結合
        features = pd.concat(X_daily, ignore_index=True)
        y = np.array(y_daily)

        # --- ▲▲▲ 新しいロジックここまで ▲▲▲ ---

        # これ以降のモデル学習部分は変更なし
        model = DecisionTreeClassifier(max_depth=2, min_samples_split=10, min_samples_leaf=5, random_state=42)
        model.fit(features, y)

        importance = (
            pd.DataFrame({"feature": features.columns, "importance": model.feature_importances_})
            .nlargest(5, "importance")
        )
        print("---------- DEBUG: Feature Importances ----------")
        print(importance)
        print("------------------------------------------")
        results["feature_importance"] = importance.to_dict("records")
        results["simple_tree"] = model

    except Exception as exc:
        log.error("light analysis failed: %s", exc, exc_info=True)
        results["error"] = str(exc)

    return results


def run_standard_analysis(df: pd.DataFrame) -> dict:
    """標準モード：中規模サンプリングとやや詳細な特徴量で分析"""
    sample_size = min(5000, len(df))
    sample_df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
    results: dict[str, Any] = {}
    try:
        daily_groups = sample_df.groupby(sample_df["ds"].dt.date)
        X_daily, y_daily = [], []
        all_codes = df["code"].unique().tolist() if "code" in df.columns else []
        global_median_night_ratio = df.groupby(df["ds"].dt.date).apply(
            lambda x: x["code"].astype(str).str.contains("夜", na=False).sum() / len(x) if len(x) > 0 else 0
        ).median()

        for _, group in daily_groups:
            if group.empty:
                continue
            X_daily.append(create_standard_features(group, all_possible_codes=all_codes))
            night_ratio = group["code"].astype(str).str.contains("夜", na=False).sum() / len(group) if len(group) > 0 else 0
            y_daily.append(1 if night_ratio <= global_median_night_ratio else 0)

        if not X_daily:
            raise ValueError("日単位の分析データが生成できませんでした。")
        features = pd.concat(X_daily, ignore_index=True).fillna(0)
        y = np.array(y_daily)

        model = DecisionTreeClassifier(max_depth=3, min_samples_split=20, min_samples_leaf=10, random_state=42)
        model.fit(features, y)

        importance = (
            pd.DataFrame({"feature": features.columns, "importance": model.feature_importances_})
            .nlargest(10, "importance")
        )
        results["feature_importance"] = importance.to_dict("records")
        results["simple_tree"] = model
    except Exception as exc:
        log.error("standard analysis failed: %s", exc, exc_info=True)
        results["error"] = str(exc)
    return results


def run_full_analysis(df: pd.DataFrame) -> dict:
    """詳細モード：全データとオリジナルの重い分析ロジックを実行"""
    log.info("詳細分析（full analysis）を開始します。時間がかかる可能性があります。")
    try:
        from shift_suite.tasks.advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2

        engine = AdvancedBlueprintEngineV2()
        full_results = engine.run_full_blueprint_analysis(df)
        return full_results.get("mind_reading", {})
    except Exception as exc:
        log.error("full analysis failed: %s", exc, exc_info=True)
        return {"error": str(exc)}


def run_optimized_analysis(df: pd.DataFrame, detail_level: str) -> dict:
    """分析レベルに応じて適切な分析関数を呼び出すルーター"""
    if detail_level == "fast":
        return run_ultra_light_analysis(df)
    if detail_level == "standard":
        return run_standard_analysis(df)
    if detail_level == "detailed":
        return run_full_analysis(df)
    log.warning(f"不明な分析レベル: {detail_level}。高速モードを実行します。")
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

