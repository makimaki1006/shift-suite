#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブループリント分析 Phase 3.2: ファクトブック可視化機能
Phase 2のFactExtractor + Phase 3.1のLightweightAnomalyDetectorの統合可視化
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import json
from dataclasses import asdict

# Dash関連のインポート
try:
    import dash
    from dash import dcc, html, dash_table
    import plotly.graph_objects as go
    import plotly.express as px
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

# Phase 2 & 3.1 の統合
try:
    from .fact_extractor_prototype import FactExtractorPrototype
    from .lightweight_anomaly_detector import LightweightAnomalyDetector, AnomalyResult
    PHASE_COMPONENTS_AVAILABLE = True
except ImportError:
    PHASE_COMPONENTS_AVAILABLE = False

log = logging.getLogger(__name__)

class FactBookVisualizer:
    """
    ファクトブック可視化システム
    Phase 2 + Phase 3.1 の統合可視化を提供
    """
    
    def __init__(self, sensitivity: str = "medium"):
        """
        初期化
        
        Args:
            sensitivity: 異常検知の感度設定
        """
        self.sensitivity = sensitivity
        
        if PHASE_COMPONENTS_AVAILABLE:
            self.fact_extractor = FactExtractorPrototype()
            self.anomaly_detector = LightweightAnomalyDetector(sensitivity=sensitivity)
            log.info("[FactBookVisualizer] Phase 2 & 3.1 コンポーネント統合完了")
        else:
            log.warning("[FactBookVisualizer] Phase 2/3.1 コンポーネントが利用できません")
        
        # 可視化用の色設定
        self.colors = {
            "primary": "#3498db",
            "success": "#2ecc71", 
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "info": "#17a2b8",
            "light": "#f8f9fa",
            "dark": "#343a40"
        }
        
        # 重要度別の色設定
        self.severity_colors = {
            "緊急": "#dc3545",
            "高": "#fd7e14", 
            "中": "#ffc107",
            "低": "#6c757d"
        }
    
    def generate_comprehensive_fact_book(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """
        包括的ファクトブックの生成
        
        Args:
            long_df: 長形式シフトデータ
            
        Returns:
            統合されたファクトブック結果
        """
        log.info("[FactBookVisualizer] 包括的ファクトブック生成開始")
        
        if not PHASE_COMPONENTS_AVAILABLE:
            return {"error": "必要なコンポーネントが利用できません"}
        
        if long_df.empty:
            log.warning("[FactBookVisualizer] 入力データが空です")
            return {"error": "入力データが空です"}
        
        fact_book = {
            "generation_timestamp": datetime.now().isoformat(),
            "data_overview": self._generate_data_overview(long_df),
            "basic_facts": {},
            "anomalies": [],
            "summary": {},
            "visualizations": {}
        }
        
        try:
            # Phase 2: 基本事実の抽出
            log.info("[FactBookVisualizer] 基本事実抽出開始")
            basic_facts = self.fact_extractor.extract_basic_facts(long_df)
            fact_book["basic_facts"] = basic_facts
            
            # Phase 3.1: 異常検知
            log.info("[FactBookVisualizer] 異常検知開始")
            anomalies = self.anomaly_detector.detect_anomalies(long_df)
            fact_book["anomalies"] = [asdict(anomaly) for anomaly in anomalies]
            
            # 統合サマリーの生成
            fact_book["summary"] = self._generate_integrated_summary(basic_facts, anomalies)
            
            # 可視化データの準備
            if DASH_AVAILABLE:
                fact_book["visualizations"] = self._prepare_visualization_data(basic_facts, anomalies)
            
            log.info(f"[FactBookVisualizer] ファクトブック生成完了: {len(basic_facts)}カテゴリの事実, {len(anomalies)}件の異常")
            
        except Exception as e:
            log.error(f"[FactBookVisualizer] ファクトブック生成中にエラー: {e}")
            fact_book["error"] = str(e)
        
        return fact_book
    
    def _generate_data_overview(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """データ概要の生成"""
        overview = {
            "total_records": len(long_df),
            "staff_count": long_df['staff'].nunique() if 'staff' in long_df.columns else 0,
            "date_range": {
                "start": long_df['ds'].min().isoformat() if 'ds' in long_df.columns else None,
                "end": long_df['ds'].max().isoformat() if 'ds' in long_df.columns else None
            },
            "work_records": len(long_df[long_df['parsed_slots_count'] > 0]) if 'parsed_slots_count' in long_df.columns else 0
        }
        
        if 'code' in long_df.columns:
            overview["unique_work_codes"] = long_df['code'].nunique()
        
        if 'role' in long_df.columns:
            overview["unique_roles"] = long_df['role'].nunique()
        
        return overview
    
    def _generate_integrated_summary(self, basic_facts: Dict[str, pd.DataFrame], anomalies: List[AnomalyResult]) -> Dict[str, Any]:
        """統合サマリーの生成"""
        summary = {
            "fact_categories": len(basic_facts),
            "total_facts": sum(len(df) for df in basic_facts.values()),
            "anomaly_count": len(anomalies),
            "critical_issues": len([a for a in anomalies if a.severity in ["緊急", "高"]]),
            "top_anomaly_types": {}
        }
        
        # 異常タイプ別の集計
        anomaly_types = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.anomaly_type
            if anomaly_type not in anomaly_types:
                anomaly_types[anomaly_type] = 0
            anomaly_types[anomaly_type] += 1
        
        summary["top_anomaly_types"] = dict(sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # 事実カテゴリ別の集計
        fact_breakdown = {}
        for category, df in basic_facts.items():
            fact_breakdown[category] = len(df)
        summary["fact_breakdown"] = fact_breakdown
        
        return summary
    
    def _prepare_visualization_data(self, basic_facts: Dict[str, pd.DataFrame], anomalies: List[AnomalyResult]) -> Dict[str, Any]:
        """可視化用データの準備"""
        viz_data = {
            "anomaly_charts": self._prepare_anomaly_charts(anomalies),
            "fact_charts": self._prepare_fact_charts(basic_facts),
            "dashboard_cards": self._prepare_dashboard_cards(basic_facts, anomalies)
        }
        return viz_data
    
    def _prepare_anomaly_charts(self, anomalies: List[AnomalyResult]) -> Dict[str, Any]:
        """異常検知結果のチャート準備"""
        if not anomalies:
            return {"message": "異常は検知されませんでした"}
        
        # 重要度別の分布
        severity_counts = {}
        for anomaly in anomalies:
            if anomaly.severity not in severity_counts:
                severity_counts[anomaly.severity] = 0
            severity_counts[anomaly.severity] += 1
        
        # 異常タイプ別の分布
        type_counts = {}
        for anomaly in anomalies:
            if anomaly.anomaly_type not in type_counts:
                type_counts[anomaly.anomaly_type] = 0
            type_counts[anomaly.anomaly_type] += 1
        
        return {
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "top_issues": [
                {
                    "staff": anomaly.staff,
                    "type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "description": anomaly.description
                }
                for anomaly in sorted(anomalies, key=lambda x: {"緊急": 0, "高": 1, "中": 2, "低": 3}.get(x.severity, 4))[:10]
            ]
        }
    
    def _prepare_fact_charts(self, basic_facts: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """基本事実のチャート準備"""
        if not basic_facts:
            return {"message": "抽出された事実がありません"}
        
        charts = {}
        
        # 基本勤務統計の可視化準備
        if "基本勤務統計" in basic_facts:
            df = basic_facts["基本勤務統計"]
            if not df.empty and "総労働時間" in df.columns:
                charts["work_hours_distribution"] = {
                    "data": df[["スタッフ", "総労働時間"]].to_dict('records'),
                    "chart_type": "bar"
                }
        
        # 職種・雇用形態統計の可視化準備
        if "職種・雇用形態統計" in basic_facts:
            df = basic_facts["職種・雇用形態統計"]
            if not df.empty and "カテゴリ" in df.columns:
                charts["role_distribution"] = {
                    "data": df[["カテゴリ", "職員数"]].to_dict('records') if "職員数" in df.columns else [],
                    "chart_type": "pie"
                }
        
        return charts
    
    def _prepare_dashboard_cards(self, basic_facts: Dict[str, pd.DataFrame], anomalies: List[AnomalyResult]) -> List[Dict[str, Any]]:
        """ダッシュボードカードの準備"""
        cards = []
        
        # 異常検知サマリーカード
        critical_count = len([a for a in anomalies if a.severity in ["緊急", "高"]])
        cards.append({
            "title": "異常検知サマリー",
            "value": len(anomalies),
            "subtitle": f"うち重要: {critical_count}件",
            "color": "danger" if critical_count > 0 else "success",
            "icon": "exclamation-triangle" if critical_count > 0 else "check-circle"
        })
        
        # 基本統計カード
        if "基本勤務統計" in basic_facts:
            df = basic_facts["基本勤務統計"]
            if not df.empty:
                total_hours = df["総労働時間"].sum() if "総労働時間" in df.columns else 0
                cards.append({
                    "title": "総労働時間",
                    "value": f"{total_hours:.1f}時間",
                    "subtitle": f"{len(df)}名の職員",
                    "color": "info",
                    "icon": "clock"
                })
        
        # 職種統計カード
        if "職種・雇用形態統計" in basic_facts:
            df = basic_facts["職種・雇用形態統計"]
            if not df.empty:
                unique_roles = df["カテゴリ"].nunique() if "カテゴリ" in df.columns else 0
                cards.append({
                    "title": "職種・雇用形態",
                    "value": unique_roles,
                    "subtitle": "種類",
                    "color": "primary",
                    "icon": "users"
                })
        
        return cards
    
    def create_dash_layout(self, fact_book: Dict[str, Any]) -> html.Div:
        """Dashレイアウトの生成"""
        if not DASH_AVAILABLE:
            return html.Div("Dashが利用できません")
        
        if "error" in fact_book:
            return html.Div([
                html.H3("エラー", style={"color": self.colors["danger"]}),
                html.P(fact_book["error"])
            ])
        
        return html.Div([
            # ヘッダー
            html.H1("📊 ファクトブック分析ダッシュボード", 
                   style={"textAlign": "center", "color": self.colors["dark"], "marginBottom": "30px"}),
            
            # サマリーカード行
            self._create_summary_cards(fact_book.get("visualizations", {}).get("dashboard_cards", [])),
            
            # メインコンテンツ
            html.Div([
                # 左カラム: 基本事実
                html.Div([
                    html.H3("📋 基本事実", style={"color": self.colors["primary"]}),
                    self._create_facts_display(fact_book.get("basic_facts", {}))
                ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "marginRight": "2%"}),
                
                # 右カラム: 異常検知
                html.Div([
                    html.H3("⚠️ 異常検知結果", style={"color": self.colors["danger"]}),
                    self._create_anomalies_display(fact_book.get("anomalies", []))
                ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "marginLeft": "2%"})
            ]),
            
            # フッター
            html.Hr(),
            html.P(f"生成日時: {fact_book.get('generation_timestamp', 'N/A')}", 
                  style={"textAlign": "center", "color": self.colors["dark"], "fontSize": "12px"})
        ], style={"padding": "20px", "backgroundColor": self.colors["light"], "minHeight": "100vh"})
    
    def _create_summary_cards(self, cards_data: List[Dict[str, Any]]) -> html.Div:
        """サマリーカード行の作成"""
        if not cards_data:
            return html.Div()
        
        cards = []
        for card in cards_data[:4]:  # 最大4つまで表示
            card_style = {
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "8px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "textAlign": "center",
                "margin": "10px",
                "borderLeft": f"4px solid {self.colors.get(card.get('color', 'primary'), self.colors['primary'])}"
            }
            
            cards.append(
                html.Div([
                    html.H4(card.get("title", ""), style={"margin": "0", "color": self.colors["dark"]}),
                    html.H2(str(card.get("value", "")), style={"margin": "10px 0", "color": self.colors.get(card.get('color', 'primary'), self.colors['primary'])}),
                    html.P(card.get("subtitle", ""), style={"margin": "0", "color": self.colors["dark"], "fontSize": "14px"})
                ], style=card_style)
            )
        
        return html.Div(cards, style={"display": "flex", "justifyContent": "space-around", "marginBottom": "30px"})
    
    def _create_facts_display(self, basic_facts: Dict[str, pd.DataFrame]) -> html.Div:
        """基本事実の表示作成"""
        if not basic_facts:
            return html.P("基本事実が抽出されていません")
        
        facts_components = []
        
        for category, df in basic_facts.items():
            if df.empty:
                continue
            
            # データテーブルの作成
            table = dash_table.DataTable(
                data=df.head(10).to_dict('records'),  # 最大10行まで表示
                columns=[{"name": col, "id": col} for col in df.columns],
                style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                style_header={'backgroundColor': self.colors["primary"], 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                page_size=5
            )
            
            facts_components.append(html.Div([
                html.H5(f"📊 {category}", style={"marginTop": "20px", "color": self.colors["dark"]}),
                table,
                html.P(f"総件数: {len(df)}件", style={"fontSize": "12px", "color": self.colors["dark"], "marginTop": "5px"})
            ]))
        
        return html.Div(facts_components)
    
    def _create_anomalies_display(self, anomalies: List[Dict[str, Any]]) -> html.Div:
        """異常検知結果の表示作成"""
        if not anomalies:
            return html.Div([
                html.P("✅ 異常は検知されませんでした", 
                      style={"color": self.colors["success"], "fontSize": "16px", "textAlign": "center"})
            ])
        
        anomaly_components = []
        
        # 重要度別にソート
        sorted_anomalies = sorted(anomalies, key=lambda x: {"緊急": 0, "高": 1, "中": 2, "低": 3}.get(x.get("severity", "低"), 4))
        
        for anomaly in sorted_anomalies[:10]:  # 最大10件まで表示
            severity = anomaly.get("severity", "低")
            color = self.severity_colors.get(severity, self.colors["dark"])
            
            anomaly_card = html.Div([
                html.Div([
                    html.Span(severity, style={
                        "backgroundColor": color, 
                        "color": "white", 
                        "padding": "2px 8px", 
                        "borderRadius": "4px", 
                        "fontSize": "12px",
                        "fontWeight": "bold"
                    }),
                    html.Span(anomaly.get("anomaly_type", ""), style={
                        "marginLeft": "10px", 
                        "fontWeight": "bold",
                        "color": self.colors["dark"]
                    })
                ], style={"marginBottom": "8px"}),
                
                html.P([
                    html.Strong(f"職員: {anomaly.get('staff', 'N/A')} "),
                    anomaly.get("description", "")
                ], style={"margin": "0", "fontSize": "14px", "color": self.colors["dark"]}),
                
                html.P(f"値: {anomaly.get('value', 'N/A')}", 
                      style={"margin": "5px 0 0 0", "fontSize": "12px", "color": self.colors["dark"]})
                
            ], style={
                "backgroundColor": "white",
                "padding": "15px",
                "borderRadius": "6px",
                "borderLeft": f"4px solid {color}",
                "marginBottom": "10px",
                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
            })
            
            anomaly_components.append(anomaly_card)
        
        return html.Div(anomaly_components)

def test_fact_book_visualizer():
    """ファクトブック可視化システムのテスト"""
    print("🧪 ファクトブック可視化システムテスト開始")
    
    if not PHASE_COMPONENTS_AVAILABLE:
        print("❌ Phase 2/3.1 コンポーネントが利用できません")
        return
    
    # テスト用のサンプルデータ作成
    import pandas as pd
    sample_data = {
        'ds': pd.date_range('2025-01-01 08:00', periods=30, freq='8H'),
        'staff': ['田中'] * 15 + ['佐藤'] * 15,
        'role': ['介護士'] * 20 + ['看護師'] * 10,
        'code': ['日勤'] * 18 + ['夜勤'] * 12,
        'holiday_type': [''] * 28 + ['祝日'] * 2,
        'parsed_slots_count': [1] * 30,
        'employment': ['正社員'] * 25 + ['パート'] * 5
    }
    
    sample_df = pd.DataFrame(sample_data)
    
    # ファクトブック生成テスト
    visualizer = FactBookVisualizer(sensitivity="medium")
    fact_book = visualizer.generate_comprehensive_fact_book(sample_df)
    
    print(f"生成されたファクトブック:")
    print(f"  - 基本事実カテゴリ数: {fact_book['summary']['fact_categories']}")
    print(f"  - 総事実数: {fact_book['summary']['total_facts']}")
    print(f"  - 異常検知数: {fact_book['summary']['anomaly_count']}")
    print(f"  - 重要異常数: {fact_book['summary']['critical_issues']}")
    
    # Dashレイアウト生成テスト
    if DASH_AVAILABLE:
        layout = visualizer.create_dash_layout(fact_book)
        print("✅ Dashレイアウト生成成功")
    else:
        print("⚠️ Dash未インストールのためレイアウト生成スキップ")
    
    print("✅ ファクトブック可視化システムテスト完了")
    return fact_book

if __name__ == "__main__":
    test_fact_book_visualizer()