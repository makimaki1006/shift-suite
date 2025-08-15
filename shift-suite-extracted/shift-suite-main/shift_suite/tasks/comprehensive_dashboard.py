#!/usr/bin/env python3
"""
comprehensive_dashboard.py - 統合シフト分析ダッシュボード
時系列分析・疲労度・公平性・勤務区分対応能力の包括的分析システム
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

log = logging.getLogger(__name__)

@dataclass
class FatigueMetrics:
    """疲労度指標"""
    consecutive_work_days: int = 0
    night_shift_frequency: float = 0.0
    rest_insufficiency: float = 0.0
    overtime_hours: float = 0.0
    fatigue_score: float = 0.0
    risk_level: str = "低"  # 低/中/高

@dataclass
class FairnessMetrics:
    """公平性指標"""
    work_hours_variance: float = 0.0
    night_shift_variance: float = 0.0
    holiday_work_variance: float = 0.0
    fairness_score: float = 1.0
    fairness_level: str = "良好"  # 良好/普通/要改善

@dataclass
class WorktypeCapability:
    """勤務区分対応能力"""
    total_worktypes: int = 0
    capable_worktypes: int = 0
    capability_ratio: float = 0.0
    multiskill_weight: float = 1.0
    capability_score: float = 0.0

@dataclass
class StaffAnalytics:
    """職員分析データ"""
    staff_id: str
    name: str
    role: str
    employment_type: str
    fatigue_metrics: FatigueMetrics
    fairness_metrics: FairnessMetrics
    worktype_capability: WorktypeCapability
    monthly_trends: Dict[str, float]
    performance_score: float = 0.0

class TimeSeriesDataModel:
    """時系列データモデル"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.monthly_trends = {}
        self.daily_patterns = {}
        self.staff_timeseries = {}
        self.worktype_evolution = {}
        self.data_range = None
        
    def load_historical_data(self, months_back: int = 6) -> bool:
        """過去数か月分のデータを読み込み"""
        try:
            log.info(f"時系列データ読み込み開始: 過去{months_back}か月")
            
            # 基本データファイル検索
            data_files = {
                'shortage_time': list(self.output_dir.glob('**/shortage_time*.parquet')),
                'heat_data': list(self.output_dir.glob('**/heat_*.parquet')),
                'staff_data': list(self.output_dir.glob('**/intermediate_data*.parquet')),
                'need_data': list(self.output_dir.glob('**/need_per_date_slot*.parquet'))
            }
            
            found_files = sum(len(files) for files in data_files.values())
            log.info(f"発見されたデータファイル数: {found_files}")
            
            if found_files == 0:
                log.warning("時系列分析用のデータファイルが見つかりません")
                return False
            
            # 各データタイプの処理
            self._process_shortage_trends(data_files['shortage_time'])
            self._process_staff_patterns(data_files['staff_data'])
            self._process_worktype_evolution(data_files['heat_data'])
            
            log.info("時系列データ読み込み完了")
            return True
            
        except Exception as e:
            log.error(f"時系列データ読み込みエラー: {e}")
            return False
    
    def _process_shortage_trends(self, files: List[Path]) -> None:
        """不足時間トレンドの処理"""
        if not files:
            return
            
        for file_path in files:
            try:
                df = pd.read_parquet(file_path)
                
                # 日付列の抽出
                date_columns = []
                for col in df.columns:
                    try:
                        pd.to_datetime(str(col))
                        date_columns.append(col)
                    except:
                        continue
                
                if date_columns:
                    # 月次集計
                    monthly_data = {}
                    for col in date_columns:
                        try:
                            date_obj = pd.to_datetime(str(col))
                            month_key = date_obj.strftime("%Y-%m")
                            
                            if month_key not in monthly_data:
                                monthly_data[month_key] = 0
                            
                            monthly_data[month_key] += df[col].sum() * 0.5  # 30分→時間換算
                        except:
                            continue
                    
                    self.monthly_trends['shortage'] = monthly_data
                    log.info(f"不足時間トレンド処理完了: {len(monthly_data)}か月分")
                    
            except Exception as e:
                log.warning(f"不足トレンド処理エラー {file_path}: {e}")
    
    def _process_staff_patterns(self, files: List[Path]) -> None:
        """職員パターンの処理"""
        if not files:
            return
            
        for file_path in files:
            try:
                df = pd.read_parquet(file_path)
                
                if 'staff' in df.columns and 'ds' in df.columns:
                    # 職員別パターン集計
                    staff_patterns = df.groupby('staff').agg({
                        'ds': 'count',  # 勤務日数
                        'role': 'first',  # 職種
                        'employment': 'first' if 'employment' in df.columns else lambda x: 'unknown'
                    }).to_dict('index')
                    
                    self.staff_timeseries.update(staff_patterns)
                    log.info(f"職員パターン処理完了: {len(staff_patterns)}名")
                    
            except Exception as e:
                log.warning(f"職員パターン処理エラー {file_path}: {e}")
    
    def _process_worktype_evolution(self, files: List[Path]) -> None:
        """勤務区分進化の処理"""
        if not files:
            return
            
        worktype_data = {}
        for file_path in files:
            try:
                if 'heat_' in file_path.name:
                    role = file_path.stem.replace('heat_', '')
                    df = pd.read_parquet(file_path)
                    
                    # 勤務区分別集計（簡易版）
                    worktype_data[role] = {
                        'total_slots': df.size,
                        'active_slots': (df > 0).sum().sum() if len(df.columns) > 0 else 0
                    }
                    
            except Exception as e:
                log.warning(f"勤務区分進化処理エラー {file_path}: {e}")
        
        self.worktype_evolution = worktype_data
        log.info(f"勤務区分進化処理完了: {len(worktype_data)}職種")

class AdvancedAnalyticsEngine:
    """高度分析エンジン"""
    
    def __init__(self, timeseries_model: TimeSeriesDataModel):
        self.timeseries_model = timeseries_model
        self.fatigue_weights = {
            'consecutive_days': 1.5,
            'night_frequency': 2.0,
            'rest_insufficiency': 2.5,
            'overtime': 1.2
        }
        self.fairness_weights = {
            'work_hours': 0.3,
            'night_shifts': 0.4,
            'holiday_work': 0.3
        }
    
    def calculate_fatigue_metrics(self, staff_data: Dict[str, Any]) -> FatigueMetrics:
        """疲労度指標の計算"""
        try:
            # 基本値の取得（サンプルデータ使用）
            consecutive_days = staff_data.get('consecutive_work_days', 0)
            night_frequency = staff_data.get('night_shift_ratio', 0.0)
            rest_insufficiency = staff_data.get('insufficient_rest_ratio', 0.0)
            overtime_hours = staff_data.get('monthly_overtime', 0.0)
            
            # 疲労スコア計算
            fatigue_score = (
                consecutive_days * self.fatigue_weights['consecutive_days'] +
                night_frequency * self.fatigue_weights['night_frequency'] +
                rest_insufficiency * self.fatigue_weights['rest_insufficiency'] +
                overtime_hours * self.fatigue_weights['overtime']
            ) / 10.0  # 正規化
            
            # リスクレベル判定
            if fatigue_score >= 7.0:
                risk_level = "高"
            elif fatigue_score >= 4.0:
                risk_level = "中"
            else:
                risk_level = "低"
            
            return FatigueMetrics(
                consecutive_work_days=consecutive_days,
                night_shift_frequency=night_frequency,
                rest_insufficiency=rest_insufficiency,
                overtime_hours=overtime_hours,
                fatigue_score=fatigue_score,
                risk_level=risk_level
            )
            
        except Exception as e:
            log.error(f"疲労度計算エラー: {e}")
            return FatigueMetrics()
    
    def calculate_fairness_metrics(self, team_data: List[Dict[str, Any]]) -> Dict[str, FairnessMetrics]:
        """公平性指標の計算"""
        fairness_results = {}
        
        try:
            if not team_data:
                return fairness_results
            
            # チーム全体の統計計算
            work_hours = [member.get('monthly_hours', 0) for member in team_data]
            night_shifts = [member.get('monthly_night_shifts', 0) for member in team_data]
            holiday_work = [member.get('monthly_holiday_work', 0) for member in team_data]
            
            # 分散計算
            work_hours_var = np.var(work_hours) if len(work_hours) > 1 else 0
            night_shifts_var = np.var(night_shifts) if len(night_shifts) > 1 else 0
            holiday_work_var = np.var(holiday_work) if len(holiday_work) > 1 else 0
            
            # 各職員の公平性指標
            for member in team_data:
                staff_id = member.get('staff_id', 'unknown')
                
                # 公平性スコア計算
                fairness_score = 1.0 - (
                    work_hours_var * self.fairness_weights['work_hours'] +
                    night_shifts_var * self.fairness_weights['night_shifts'] +
                    holiday_work_var * self.fairness_weights['holiday_work']
                ) / 100.0  # 正規化
                
                fairness_score = max(0.0, min(1.0, fairness_score))
                
                # レベル判定
                if fairness_score >= 0.8:
                    fairness_level = "良好"
                elif fairness_score >= 0.6:
                    fairness_level = "普通"
                else:
                    fairness_level = "要改善"
                
                fairness_results[staff_id] = FairnessMetrics(
                    work_hours_variance=work_hours_var,
                    night_shift_variance=night_shifts_var,
                    holiday_work_variance=holiday_work_var,
                    fairness_score=fairness_score,
                    fairness_level=fairness_level
                )
                
        except Exception as e:
            log.error(f"公平性計算エラー: {e}")
        
        return fairness_results
    
    def calculate_worktype_capability(self, staff_data: Dict[str, Any], available_worktypes: List[str]) -> WorktypeCapability:
        """勤務区分対応能力の計算"""
        try:
            capable_worktypes = staff_data.get('capable_worktypes', [])
            total_worktypes = len(available_worktypes)
            capable_count = len(capable_worktypes)
            
            capability_ratio = capable_count / total_worktypes if total_worktypes > 0 else 0
            
            # マルチスキル重み（対応可能勤務区分数に応じて）
            if capable_count >= total_worktypes * 0.8:
                multiskill_weight = 1.5
            elif capable_count >= total_worktypes * 0.6:
                multiskill_weight = 1.2
            else:
                multiskill_weight = 1.0
            
            capability_score = capability_ratio * multiskill_weight
            
            return WorktypeCapability(
                total_worktypes=total_worktypes,
                capable_worktypes=capable_count,
                capability_ratio=capability_ratio,
                multiskill_weight=multiskill_weight,
                capability_score=capability_score
            )
            
        except Exception as e:
            log.error(f"勤務区分対応能力計算エラー: {e}")
            return WorktypeCapability()

class IntegratedVisualizationSystem:
    """統合可視化システム"""
    
    def __init__(self, analytics_engine: AdvancedAnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.color_schemes = {
            'fatigue': ['#2ecc71', '#f39c12', '#e74c3c'],  # 緑・オレンジ・赤
            'fairness': ['#3498db', '#9b59b6', '#e67e22'],  # 青・紫・オレンジ
            'capability': ['#1abc9c', '#34495e', '#e74c3c']  # ティール・グレー・赤
        }
    
    def _get_optimal_text_position(self, x_values: List[float], y_values: List[float]) -> str:
        """データ点の密度に基づく最適なテキスト位置を決定"""
        try:
            # データ点の分散を計算
            x_range = max(x_values) - min(x_values) if len(x_values) > 1 else 1
            y_range = max(y_values) - min(y_values) if len(y_values) > 1 else 1
            
            # 密度が高い場合は上下に分散
            if len(x_values) > 10:
                return "middle right"
            elif x_range < y_range:
                return "top center"
            else:
                return "middle right"
        except Exception:
            return "top center"
    
    def _create_smart_hover_text(self, name: str, metrics: Dict[str, float]) -> str:
        """スマートなホバーテキストの生成"""
        lines = [f"<b>{name}</b>"]
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"{key}: {value:.2f}")
            else:
                lines.append(f"{key}: {value}")
        return "<br>".join(lines)
    
    def create_comprehensive_dashboard(self, staff_analytics: List[StaffAnalytics]) -> go.Figure:
        """統合ダッシュボードの作成（サイズ最適化版）"""
        try:
            staff_count = len(staff_analytics)
            
            # グラフ数とレイアウトの動的決定（サイズ優先）
            if staff_count <= 20:
                # 少数の場合: 2x2レイアウトで大きく表示
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[
                        "疲労度vs性能分析", "公平性スコア",
                        "勤務区分対応能力", "職員パフォーマンス"
                    ],
                    specs=[
                        [{"type": "scatter"}, {"type": "bar"}],
                        [{"type": "scatter"}, {"type": "bar"}]
                    ],
                    vertical_spacing=0.18,
                    horizontal_spacing=0.12
                )
                show_subplots = ['fatigue_vs_performance', 'fairness', 'capability', 'performance']
            else:
                # 多数の場合: 1x2レイアウトで最大表示
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=[
                        "疲労度vs性能分析", "公平性スコア"
                    ],
                    specs=[
                        [{"type": "scatter"}, {"type": "bar"}]
                    ],
                    horizontal_spacing=0.15
                )
                show_subplots = ['fatigue_vs_performance', 'fairness']
            
            # データ量に応じた表示制御
            show_text_labels = staff_count <= 10  # 10人以下の場合のみテキスト表示
            use_abbreviated_names = staff_count > 10  # 10人超過で名前略称化
            
            if not staff_analytics:
                # データがない場合のプレースホルダー
                fig.add_annotation(
                    text="データを読み込んでください",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=16, color="#666")
                )
                return fig
            
            # 基本データの取得
            fatigue_scores = [staff.fatigue_metrics.fatigue_score for staff in staff_analytics]
            performance_scores = [staff.performance_score for staff in staff_analytics]
            fairness_scores = [staff.fairness_metrics.fairness_score for staff in staff_analytics]
            capability_scores = [staff.worktype_capability.capability_score for staff in staff_analytics]
            capable_counts = [staff.worktype_capability.capable_worktypes for staff in staff_analytics]
            names = [staff.name for staff in staff_analytics]
            roles = [staff.role for staff in staff_analytics]
            
            # 表示名の動的処理（職員IDでもホバーで実名表示）
            if use_abbreviated_names:
                display_names = [f"S{i+1}" for i in range(staff_count)]
            else:
                display_names = names
            
            # 1. 疲労度vs性能分析（必須）
            if 'fatigue_vs_performance' in show_subplots:
                scatter_mode = 'markers+text' if show_text_labels else 'markers'
                text_position = self._get_optimal_text_position(fatigue_scores, performance_scores) if show_text_labels else None
                
                fig.add_trace(
                    go.Scatter(
                        x=fatigue_scores,
                        y=performance_scores,
                        mode=scatter_mode,
                        text=display_names if show_text_labels else None,
                        textposition=text_position,
                        textfont=dict(size=10),
                        hovertext=[f"<b>{name}</b><br>職種: {role}<br>疲労度: {f:.1f}<br>性能: {p:.1f}" 
                                  for name, role, f, p in zip(names, roles, fatigue_scores, performance_scores)],
                        hoverinfo='text',
                        marker=dict(
                            size=16 if not show_text_labels else 12,
                            color=fatigue_scores,
                            colorscale='RdYlGn',
                            reversescale=True,
                            showscale=False
                        ),
                        name="疲労度vs性能"
                    ),
                    row=1, col=1
                )
            
            # 2. 公平性分析（必須）
            if 'fairness' in show_subplots:
                hover_text = [f"<b>{name}</b><br>職種: {role}<br>公平性: {score:.2f}" 
                             for name, role, score in zip(names, roles, fairness_scores)]
                
                col_pos = 2 if staff_count <= 20 else 2
                row_pos = 1
                
                fig.add_trace(
                    go.Bar(
                        x=display_names,
                        y=fairness_scores,
                        name="公平性スコア",
                        marker_color=self.color_schemes['fairness'][0],
                        hovertext=hover_text,
                        hoverinfo='text'
                    ),
                    row=row_pos, col=col_pos
                )
            
            # 3. 勤務区分対応能力（条件付き）
            if 'capability' in show_subplots:
                fig.add_trace(
                    go.Scatter(
                        x=capable_counts,
                        y=capability_scores,
                        mode='markers',
                        marker=dict(
                            size=18,
                            color=capability_scores,
                            colorscale='Viridis',
                            showscale=False
                        ),
                        hovertext=[f"<b>{name}</b><br>職種: {role}<br>対応可能: {count}種<br>スコア: {score:.2f}" 
                                  for name, role, count, score in zip(names, roles, capable_counts, capability_scores)],
                        hoverinfo='text',
                        name="対応能力"
                    ),
                    row=2, col=1
                )
            
            # 4. 職員パフォーマンス（条件付き）
            if 'performance' in show_subplots:
                performance_hover = [f"<b>{name}</b><br>職種: {role}<br>パフォーマンス: {score:.2f}" 
                                   for name, role, score in zip(names, roles, performance_scores)]
                
                fig.add_trace(
                    go.Bar(
                        x=display_names,
                        y=performance_scores,
                        name="総合パフォーマンス",
                        marker_color=self.color_schemes['capability'][0],
                        hovertext=performance_hover,
                        hoverinfo='text'
                    ),
                    row=2, col=2
                )
            
            
            # レイアウト更新（サイズ最適化版）
            layout_height = 1000 if staff_count <= 20 else 600  # グラフ数に応じた高さ
            
            fig.update_layout(
                title=dict(
                    text="🏥 統合シフト分析ダッシュボード",
                    font=dict(size=20),
                    x=0.5
                ),
                height=layout_height,
                showlegend=False,
                plot_bgcolor='rgba(248,249,250,0.8)',
                paper_bgcolor='white',
                font=dict(size=12),
                # 充実したホバー情報
                hoverlabel=dict(
                    bgcolor="rgba(255,255,255,0.95)",
                    font_size=13,
                    font_family="Arial",
                    bordercolor="#333"
                ),
                # レスポンシブ対応
                autosize=True,
                margin=dict(l=80, r=80, t=100, b=80)
            )
            
            # X軸ラベルの回転設定（棒グラフ用）
            if staff_count > 8:
                if 'fairness' in show_subplots:
                    col_pos = 2 if staff_count <= 20 else 2
                    fig.update_xaxes(tickangle=45, row=1, col=col_pos)
                if 'performance' in show_subplots:
                    fig.update_xaxes(tickangle=45, row=2, col=2)
            
            # 軸ラベル設定（動的レイアウトに対応）
            fig.update_xaxes(title_text="疲労スコア", title_font_size=14, row=1, col=1)
            fig.update_yaxes(title_text="パフォーマンス", title_font_size=14, row=1, col=1)
            
            if 'fairness' in show_subplots:
                col_pos = 2 if staff_count <= 20 else 2
                fig.update_xaxes(title_text="職員" if not use_abbreviated_names else "職員ID", title_font_size=14, row=1, col=col_pos)
                fig.update_yaxes(title_text="公平性スコア", title_font_size=14, row=1, col=col_pos)
            
            if 'capability' in show_subplots:
                fig.update_xaxes(title_text="対応可能勤務区分数", title_font_size=14, row=2, col=1)
                fig.update_yaxes(title_text="対応能力スコア", title_font_size=14, row=2, col=1)
            
            if 'performance' in show_subplots:
                fig.update_xaxes(title_text="職員" if not use_abbreviated_names else "職員ID", title_font_size=14, row=2, col=2)
                fig.update_yaxes(title_text="パフォーマンス", title_font_size=14, row=2, col=2)
            
            log.info(f"統合ダッシュボード作成完了: {staff_count}名, レイアウト={len(show_subplots)}グラフ")
            return fig
            
        except Exception as e:
            log.error(f"統合ダッシュボード作成エラー: {e}")
            # エラー時のフォールバック
            return go.Figure().add_annotation(
                text=f"ダッシュボード作成エラー: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
    
    def create_fatigue_heatmap(self, staff_analytics: List[StaffAnalytics]) -> go.Figure:
        """疲労度ヒートマップの作成（テキスト重なり対策付き）"""
        if not staff_analytics:
            return go.Figure()
        
        try:
            # データ準備
            staff_names = [staff.name for staff in staff_analytics]
            staff_count = len(staff_names)
            metrics = ['連続勤務日数', '夜勤頻度', '休息不足', '残業時間']
            
            # 職員名の動的調整
            if staff_count > 15:
                display_names = [f"S{i+1}" for i in range(staff_count)]
            elif staff_count > 8:
                display_names = [name[:4] + '...' if len(name) > 5 else name for name in staff_names]
            else:
                display_names = staff_names
            
            heatmap_data = []
            for staff in staff_analytics:
                row = [
                    staff.fatigue_metrics.consecutive_work_days,
                    staff.fatigue_metrics.night_shift_frequency * 10,  # 視覚化のためスケール調整
                    staff.fatigue_metrics.rest_insufficiency * 10,
                    staff.fatigue_metrics.overtime_hours / 10
                ]
                heatmap_data.append(row)
            
            # 充実したホバーテキストの準備
            hover_text = []
            for i, staff in enumerate(staff_analytics):
                row_hover = []
                hover_data = {
                    '連続勤務日数': f"{staff.fatigue_metrics.consecutive_work_days}日",
                    '夜勤頻度': f"{staff.fatigue_metrics.night_shift_frequency:.2f}",
                    '休息不足': f"{staff.fatigue_metrics.rest_insufficiency:.2f}",
                    '残業時間': f"{staff.fatigue_metrics.overtime_hours:.1f}h"
                }
                for j, metric in enumerate(metrics):
                    hover_text_cell = (f"<b>{staff_names[i]}</b><br>"
                                     f"職種: {staff.role}<br>"
                                     f"{metric}: {hover_data[metric]}<br>"
                                     f"疲労スコア: {staff.fatigue_metrics.fatigue_score:.1f}<br>"
                                     f"リスクレベル: {staff.fatigue_metrics.risk_level}")
                    row_hover.append(hover_text_cell)
                hover_text.append(row_hover)
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=metrics,
                y=display_names,
                colorscale='RdYlGn',
                reversescale=True,
                showscale=True,
                colorbar=dict(
                    title="疲労度レベル",
                    titlefont=dict(size=12)
                ),
                hovertext=hover_text,
                hoverinfo='text'
            ))
            
            # ヒートマップのサイズ最適化
            heatmap_height = max(600, min(1200, staff_count * 30 + 150))
            
            fig.update_layout(
                title=dict(
                    text="👥 職員別疲労度分析ヒートマップ",
                    font=dict(size=18),
                    x=0.5
                ),
                xaxis_title="疲労度指標",
                yaxis_title="職員" if staff_count <= 15 else "職員ID",
                height=heatmap_height,
                font=dict(size=12),
                # Y軸ラベルの調整（職員名/ID表示の最適化）
                yaxis=dict(
                    tickfont=dict(size=10 if staff_count > 20 else 11),
                    automargin=True
                ),
                xaxis=dict(
                    tickfont=dict(size=12)
                ),
                # マージンの調整
                margin=dict(l=120, r=60, t=100, b=60),
                # ホバー情報の改善
                hoverlabel=dict(
                    bgcolor="rgba(255,255,255,0.95)",
                    font_size=13,
                    font_family="Arial",
                    bordercolor="#333"
                )
            )
            
            return fig
            
        except Exception as e:
            log.error(f"疲労度ヒートマップ作成エラー: {e}")
            return go.Figure()

class ComprehensiveDashboard:
    """統合ダッシュボードメインクラス"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.timeseries_model = TimeSeriesDataModel(output_dir)
        self.analytics_engine = AdvancedAnalyticsEngine(self.timeseries_model)
        self.visualization_system = IntegratedVisualizationSystem(self.analytics_engine)
        self.staff_analytics: List[StaffAnalytics] = []
        
    def initialize(self, months_back: int = 6) -> bool:
        """ダッシュボード初期化"""
        try:
            log.info("統合ダッシュボード初期化開始")
            
            # 時系列データ読み込み
            if not self.timeseries_model.load_historical_data(months_back):
                log.warning("時系列データの読み込みに失敗しましたが、処理を続行します")
            
            # 実データを使用した分析生成
            if not self._generate_real_analytics():
                # 実データが不足している場合のみサンプルデータを使用
                log.warning("実データが不十分のため、サンプルデータを使用します")
                self._generate_sample_analytics()
            
            log.info("統合ダッシュボード初期化完了")
            return True
            
        except Exception as e:
            log.error(f"ダッシュボード初期化エラー: {e}")
            return False
    
    def _generate_real_analytics(self) -> bool:
        """実データを使用した分析データの生成"""
        try:
            log.info("実データからの分析生成開始")
            
            # 実データファイルの検索
            real_data_files = {
                'shortage_role': list(self.output_dir.glob('**/shortage_role*.parquet')),
                'shortage_employment': list(self.output_dir.glob('**/shortage_employment*.parquet')),
                'staff_data': list(self.output_dir.glob('**/intermediate_data*.parquet')),
                'fairness_data': list(self.output_dir.glob('**/fairness*.parquet')),
                'shortage_time': list(self.output_dir.glob('**/shortage_time*.parquet'))
            }
            
            # 必要なファイルの存在確認
            required_files = ['shortage_role', 'staff_data']
            missing_files = [key for key in required_files 
                           if not real_data_files.get(key)]
            
            if missing_files:
                log.warning(f"必要なファイルが不足: {missing_files}")
                return False
            
            self.staff_analytics = []
            
            # 職種別データから職員情報を構築
            try:
                shortage_role_file = real_data_files['shortage_role'][0]
                shortage_role_df = pd.read_parquet(shortage_role_file)
                log.info(f"職種別不足データ読み込み: {len(shortage_role_df)}行")
                
                # 職員データの読み込み
                staff_file = real_data_files['staff_data'][0]
                staff_df = pd.read_parquet(staff_file)
                log.info(f"職員データ読み込み: {len(staff_df)}行")
                
                # 雇用形態別データ
                employment_df = pd.DataFrame()
                if real_data_files.get('shortage_employment'):
                    employment_df = pd.read_parquet(real_data_files['shortage_employment'][0])
                    log.info(f"雇用形態別データ読み込み: {len(employment_df)}行")
                
                # 公平性データ
                fairness_df = pd.DataFrame()
                if real_data_files.get('fairness_data'):
                    fairness_df = pd.read_parquet(real_data_files['fairness_data'][0])
                    log.info(f"公平性データ読み込み: {len(fairness_df)}行")
                
                # 職種ごとの分析データ生成
                for _, role_row in shortage_role_df.iterrows():
                    if pd.isna(role_row.get('role')) or role_row.get('role') in ['全体', '合計', '総計']:
                        continue
                    
                    role_name = role_row.get('role', 'unknown')
                    
                    # 該当職種の職員数を推定
                    role_staff = staff_df[staff_df.get('role', '') == role_name] if 'role' in staff_df.columns else pd.DataFrame()
                    staff_count = len(role_staff) if not role_staff.empty else 1
                    
                    # 職種レベルの指標から個人レベルを推定生成
                    for i in range(min(staff_count, 5)):  # 最大5名まで
                        staff_id = f"{role_name}_{i+1:03d}"
                        staff_name = f"{role_name}{i+1}"
                        
                        # 疲労度データ（不足時間から推定）
                        role_lack_h = role_row.get('lack_h', 0)
                        role_need_h = role_row.get('need_h', 1)
                        
                        # 不足率から疲労度を推定
                        shortage_ratio = role_lack_h / role_need_h if role_need_h > 0 else 0
                        estimated_fatigue = min(shortage_ratio * 10, 10)  # 0-10スケール
                        
                        fatigue_data = {
                            'consecutive_work_days': int(min(estimated_fatigue * 0.8, 7)),
                            'night_shift_ratio': min(shortage_ratio * 0.5, 0.4),
                            'insufficient_rest_ratio': min(shortage_ratio * 0.3, 0.3),
                            'monthly_overtime': min(role_lack_h * 2, 50)
                        }
                        
                        # 公平性データ（チーム平均を使用）
                        fairness_score = 0.8  # デフォルト
                        if not fairness_df.empty and 'fairness_score' in fairness_df.columns:
                            fairness_score = fairness_df['fairness_score'].mean()
                        
                        fairness_metrics = FairnessMetrics(
                            fairness_score=fairness_score,
                            fairness_level="良好" if fairness_score >= 0.8 else "普通" if fairness_score >= 0.6 else "要改善"
                        )
                        
                        # 勤務区分対応能力（職種に基づく推定）
                        if '看護師' in role_name:
                            capable_worktypes = ['日勤', '夜勤', '準夜勤']
                        elif '医師' in role_name:
                            capable_worktypes = ['日勤', '夜勤']
                        elif '薬剤師' in role_name:
                            capable_worktypes = ['日勤']
                        else:
                            capable_worktypes = ['日勤', '夜勤']
                        
                        capability_data = {
                            'capable_worktypes': capable_worktypes
                        }
                        available_worktypes = ['日勤', '夜勤', '準夜勤', '深夜勤']
                        
                        # 雇用形態の推定
                        employment_type = "正規"
                        if not employment_df.empty:
                            # 雇用形態データがある場合はランダムに選択
                            employment_types = employment_df.get('employment', ['正規']).tolist()
                            employment_type = np.random.choice(employment_types) if employment_types else "正規"
                        
                        # 月次トレンドデータ（時系列データから取得）
                        monthly_trends = {}
                        if hasattr(self.timeseries_model, 'monthly_trends') and self.timeseries_model.monthly_trends:
                            shortage_trends = self.timeseries_model.monthly_trends.get('shortage', {})
                            # 職種比率で配分
                            total_shortage = sum(shortage_trends.values()) if shortage_trends else 0
                            role_ratio = role_lack_h / total_shortage if total_shortage > 0 else 0
                            
                            for month, value in shortage_trends.items():
                                monthly_trends[month] = value * role_ratio
                        else:
                            # フォールバック
                            monthly_trends = {'2024-07': role_lack_h}
                        
                        # パフォーマンススコア（疲労度の逆数的関係）
                        performance_score = max(0.1, 1.0 - (estimated_fatigue / 10) * 0.5)
                        
                        # StaffAnalyticsオブジェクト作成
                        staff_analytics = StaffAnalytics(
                            staff_id=staff_id,
                            name=staff_name,
                            role=role_name,
                            employment_type=employment_type,
                            fatigue_metrics=self.analytics_engine.calculate_fatigue_metrics(fatigue_data),
                            fairness_metrics=fairness_metrics,
                            worktype_capability=self.analytics_engine.calculate_worktype_capability(
                                capability_data, available_worktypes
                            ),
                            monthly_trends=monthly_trends,
                            performance_score=performance_score
                        )
                        
                        self.staff_analytics.append(staff_analytics)
                
                log.info(f"実データから{len(self.staff_analytics)}名の分析データを生成")
                return len(self.staff_analytics) > 0
                
            except Exception as e:
                log.error(f"実データ処理エラー: {e}")
                return False
                
        except Exception as e:
            log.error(f"実データ分析生成エラー: {e}")
            return False

    def _generate_sample_analytics(self) -> None:
        """サンプル分析データの生成（開発用）"""
        sample_staff = [
            {"staff_id": "001", "name": "田中看護師", "role": "看護師", "employment_type": "正規"},
            {"staff_id": "002", "name": "佐藤医師", "role": "医師", "employment_type": "正規"},
            {"staff_id": "003", "name": "山田薬剤師", "role": "薬剤師", "employment_type": "パート"},
            {"staff_id": "004", "name": "鈴木看護師", "role": "看護師", "employment_type": "正規"},
            {"staff_id": "005", "name": "高橋技師", "role": "技師", "employment_type": "契約"},
        ]
        
        self.staff_analytics = []
        
        for staff_info in sample_staff:
            # サンプル疲労度データ
            fatigue_data = {
                'consecutive_work_days': np.random.randint(0, 8),
                'night_shift_ratio': np.random.uniform(0, 0.4),
                'insufficient_rest_ratio': np.random.uniform(0, 0.3),
                'monthly_overtime': np.random.uniform(0, 40)
            }
            
            # サンプル公平性データ（チーム全体で計算するため簡易版）
            fairness_metrics = FairnessMetrics(
                fairness_score=np.random.uniform(0.6, 1.0),
                fairness_level="良好" if np.random.random() > 0.3 else "普通"
            )
            
            # サンプル勤務区分対応能力データ
            capability_data = {
                'capable_worktypes': ['日勤', '夜勤', '準夜勤'][:np.random.randint(1, 4)]
            }
            available_worktypes = ['日勤', '夜勤', '準夜勤', '深夜勤']
            
            staff_analytics = StaffAnalytics(
                staff_id=staff_info['staff_id'],
                name=staff_info['name'],
                role=staff_info['role'],
                employment_type=staff_info['employment_type'],
                fatigue_metrics=self.analytics_engine.calculate_fatigue_metrics(fatigue_data),
                fairness_metrics=fairness_metrics,
                worktype_capability=self.analytics_engine.calculate_worktype_capability(
                    capability_data, available_worktypes
                ),
                monthly_trends={
                    '2024-01': np.random.uniform(100, 200),
                    '2024-02': np.random.uniform(100, 200),
                    '2024-03': np.random.uniform(100, 200)
                },
                performance_score=np.random.uniform(0.7, 1.0)
            )
            
            self.staff_analytics.append(staff_analytics)
    
    def get_dashboard_figures(self) -> Dict[str, go.Figure]:
        """ダッシュボード図表の取得"""
        try:
            figures = {
                'comprehensive': self.visualization_system.create_comprehensive_dashboard(self.staff_analytics),
                'fatigue_heatmap': self.visualization_system.create_fatigue_heatmap(self.staff_analytics)
            }
            
            log.info("ダッシュボード図表生成完了")
            return figures
            
        except Exception as e:
            log.error(f"ダッシュボード図表生成エラー: {e}")
            return {}
    
    def export_analytics_data(self, filename: str = "comprehensive_analytics.json") -> Path:
        """分析データのエクスポート"""
        try:
            export_data = {
                'generation_time': datetime.now().isoformat(),
                'staff_count': len(self.staff_analytics),
                'staff_analytics': [asdict(staff) for staff in self.staff_analytics],
                'summary_metrics': self._calculate_summary_metrics()
            }
            
            export_path = self.output_dir / filename
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            log.info(f"分析データエクスポート完了: {export_path}")
            return export_path
            
        except Exception as e:
            log.error(f"分析データエクスポートエラー: {e}")
            return None
    
    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """サマリーメトリクスの計算"""
        if not self.staff_analytics:
            return {}
        
        fatigue_scores = [staff.fatigue_metrics.fatigue_score for staff in self.staff_analytics]
        fairness_scores = [staff.fairness_metrics.fairness_score for staff in self.staff_analytics]
        capability_scores = [staff.worktype_capability.capability_score for staff in self.staff_analytics]
        
        return {
            'average_fatigue_score': np.mean(fatigue_scores),
            'average_fairness_score': np.mean(fairness_scores),
            'average_capability_score': np.mean(capability_scores),
            'high_fatigue_count': sum(1 for score in fatigue_scores if score >= 7.0),
            'low_fairness_count': sum(1 for score in fairness_scores if score < 0.6),
            'multiskill_staff_count': sum(1 for staff in self.staff_analytics 
                                        if staff.worktype_capability.capable_worktypes >= 3)
        }

# 便利な関数
def create_comprehensive_dashboard(output_dir: Path, months_back: int = 6) -> ComprehensiveDashboard:
    """統合ダッシュボードの作成"""
    dashboard = ComprehensiveDashboard(output_dir)
    dashboard.initialize(months_back)
    return dashboard

def generate_dashboard_report(output_dir: Path, report_file: str = "dashboard_report.json") -> Path:
    """ダッシュボードレポートの生成"""
    dashboard = create_comprehensive_dashboard(output_dir)
    return dashboard.export_analytics_data(report_file)