# visualization_engine.py - 高度な可視化エンジン
"""
レスポンシブ・インタラクティブ・リアルタイム進捗対応の統合可視化システム
ユーザー体験を大幅に向上
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
from dataclasses import dataclass
import numpy as np

# ログ設定
log = logging.getLogger(__name__)

@dataclass
class VisualizationConfig:
    """可視化設定"""
    responsive_breakpoints: Dict[str, int] = None
    animation_duration: int = 500
    color_scheme: str = "modern_blue"
    enable_interactivity: bool = True
    show_progress: bool = True
    
    def __post_init__(self):
        if self.responsive_breakpoints is None:
            self.responsive_breakpoints = {
                'mobile': 768,
                'tablet': 1024, 
                'desktop': 1440
            }

class ResponsiveVisualizationEngine:
    """レスポンシブ対応可視化エンジン"""
    
    def __init__(self, config: VisualizationConfig = None):
        self.config = config or VisualizationConfig()
        self.color_schemes = self._initialize_color_schemes()
        self.device_layouts = self._initialize_device_layouts()
        self._figure_cache = {}
        
    def _initialize_color_schemes(self) -> Dict[str, Dict[str, List[str]]]:
        """カラースキーム初期化"""
        return {
            'modern_blue': {
                'primary': ['#3498db', '#2980b9', '#1abc9c', '#16a085'],
                'secondary': ['#ecf0f1', '#bdc3c7', '#95a5a6', '#7f8c8d'],
                'accent': ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60']
            },
            'professional': {
                'primary': ['#2c3e50', '#34495e', '#95a5a6', '#bdc3c7'],
                'secondary': ['#ecf0f1', '#d5dbdb', '#aeb6bf', '#85929e'],
                'accent': ['#e67e22', '#d35400', '#c0392b', '#8e44ad']
            },
            'vibrant': {
                'primary': ['#9b59b6', '#8e44ad', '#3498db', '#2980b9'],
                'secondary': ['#e8daef', '#d7dbdd', '#aed6f1', '#85c1e9'],
                'accent': ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60']
            }
        }
    
    def _initialize_device_layouts(self) -> Dict[str, Dict[str, Any]]:
        """デバイス別レイアウト初期化"""
        return {
            'mobile': {
                'figure_height': 300,
                'margin': {'l': 30, 'r': 30, 't': 40, 'b': 30},
                'font_size': 10,
                'legend_orientation': 'h',
                'grid_columns': 1
            },
            'tablet': {
                'figure_height': 400,
                'margin': {'l': 50, 'r': 50, 't': 60, 'b': 40},
                'font_size': 12,
                'legend_orientation': 'v',
                'grid_columns': 2
            },
            'desktop': {
                'figure_height': 500,
                'margin': {'l': 70, 'r': 70, 't': 80, 'b': 50},
                'font_size': 14,
                'legend_orientation': 'v',
                'grid_columns': 3
            }
        }
    
    def detect_device_type(self, screen_width: Optional[int] = None) -> str:
        """デバイスタイプ自動判定"""
        if screen_width is None:
            return 'desktop'  # デフォルト
        
        if screen_width <= self.config.responsive_breakpoints['mobile']:
            return 'mobile'
        elif screen_width <= self.config.responsive_breakpoints['tablet']:
            return 'tablet'
        else:
            return 'desktop'
    
    def create_responsive_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "ヒートマップ",
        device_type: str = "desktop",
        progress_callback: Optional[callable] = None
    ) -> go.Figure:
        """レスポンシブ対応ヒートマップ"""
        
        if progress_callback:
            progress_callback("ヒートマップ生成", 10)
        
        layout_config = self.device_layouts[device_type]
        colors = self.color_schemes[self.config.color_scheme]['primary']
        
        # データ準備の進捗
        if progress_callback:
            progress_callback("データ準備中", 30)
        
        # デバイス別データ調整
        if device_type == 'mobile' and len(data.columns) > 7:
            # モバイルでは列数を制限
            data = data.iloc[:, :7]
        elif device_type == 'tablet' and len(data.columns) > 15:
            # タブレットでは列数を制限
            data = data.iloc[:, :15]
        
        if progress_callback:
            progress_callback("レンダリング中", 60)
        
        # プロフェッショナル単色グラデーション（直感的で理解しやすい）
        data_max = data.max().max()
        data_min = data.min().min()
        
        # 単色ブルーグラデーション - 濃さで人数を直感的に表現
        professional_blue_scale = [
            [0, '#f8f9ff'],      # 最薄 - 0人用の非常に薄いブルー
            [0.1, '#e3f2fd'],    # 薄いブルー - 少数
            [0.2, '#bbdefb'],    # やや薄いブルー
            [0.3, '#90caf9'],    # 中薄ブルー
            [0.4, '#64b5f6'],    # 中間ブルー
            [0.5, '#42a5f5'],    # やや濃いブルー
            [0.6, '#2196f3'],    # 中濃ブルー
            [0.7, '#1e88e5'],    # 濃いブルー
            [0.8, '#1976d2'],    # より濃いブルー
            [0.9, '#1565c0'],    # かなり濃いブルー
            [1.0, '#0d47a1']     # 最濃ネイビー - 最大人数
        ]
        
        # データ範囲に応じてテキスト表示を制御（職種別対応）
        max_value = data.max().max()
        # 職種別やデータが大きい場合はテキスト表示を無効化
        is_role_specific = any(keyword in title.lower() for keyword in ['職種', 'role', '看護師', 'ドクター', '薬剤師'])
        show_text = max_value <= 3 and not is_role_specific  # さらに厳しい条件
        
        # ヒートマップ生成
        heatmap_data = go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=professional_blue_scale,
            zmin=0,  # 最小値を0に固定
            zmax=data_max if data_max > 0 else 1,  # 最大値を設定
            showscale=True,
            hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
            colorbar=dict(
                thickness=15 if device_type != 'mobile' else 10,
                len=0.7,
                x=1.02,
                title=dict(
                    text="値",
                    font=dict(size=layout_config['font_size'])
                )
            )
        )
        
        # テキスト表示の制御（コントラスト改善）
        if show_text:
            heatmap_data.update(
                text=data.values,
                texttemplate='%{text}',
                textfont=dict(
                    size=layout_config['font_size'] - 1,
                    color='black'  # 基本は黒文字（薄い色に対応）
                )
            )
        
        fig = go.Figure(data=heatmap_data)
        
        # レスポンシブレイアウト適用
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=layout_config['font_size'] + 2),
                x=0.5,
                xanchor='center'
            ),
            height=layout_config['figure_height'],
            margin=layout_config['margin'],
            font=dict(size=layout_config['font_size']),
            xaxis=dict(
                title="",
                tickangle=-45 if device_type == 'mobile' else 0,
                tickfont=dict(size=layout_config['font_size'] - 2)
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=layout_config['font_size'] - 2)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        if progress_callback:
            progress_callback("完了", 100)
        
        return fig
    
    def create_responsive_shortage_chart(
        self,
        data: pd.DataFrame,
        device_type: str = "desktop",
        progress_callback: Optional[callable] = None
    ) -> go.Figure:
        """レスポンシブ対応不足分析チャート"""
        
        if progress_callback:
            progress_callback("不足分析チャート生成", 10)
        
        layout_config = self.device_layouts[device_type]
        colors = self.color_schemes[self.config.color_scheme]
        
        # デバイス別サブプロット構成
        if device_type == 'mobile':
            rows, cols = len(data.columns), 1
            subplot_titles = list(data.columns)
        elif device_type == 'tablet':
            cols = 2
            rows = (len(data.columns) + 1) // 2
            subplot_titles = list(data.columns)
        else:  # desktop
            cols = min(3, len(data.columns))
            rows = (len(data.columns) + 2) // 3
            subplot_titles = list(data.columns)
        
        if progress_callback:
            progress_callback("サブプロット構成", 30)
        
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 各列のグラフを生成
        for i, col in enumerate(data.columns):
            row = (i // cols) + 1
            col_pos = (i % cols) + 1
            
            if progress_callback:
                progress_callback(f"グラフ生成: {col}", 40 + (i * 40 // len(data.columns)))
            
            # 正の値（不足）と負の値（余剰）を分離
            positive_data = data[col].where(data[col] > 0, 0)
            negative_data = data[col].where(data[col] < 0, 0)
            
            # 不足分（赤系）
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=positive_data,
                    name=f"{col}_不足",
                    marker_color=colors['accent'][0],
                    showlegend=(i == 0),
                    hovertemplate=f"<b>{col}</b><br>%{{x}}: %{{y}}<extra></extra>"
                ),
                row=row, col=col_pos
            )
            
            # 余剰分（緑系）
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=negative_data,
                    name=f"{col}_余剰",
                    marker_color=colors['accent'][3],
                    showlegend=(i == 0),
                    hovertemplate=f"<b>{col}</b><br>%{{x}}: %{{y}}<extra></extra>"
                ),
                row=row, col=col_pos
            )
        
        # レスポンシブレイアウト
        fig.update_layout(
            height=layout_config['figure_height'] * rows,
            margin=layout_config['margin'],
            font=dict(size=layout_config['font_size']),
            showlegend=True,
            legend=dict(
                orientation=layout_config['legend_orientation'],
                x=0.5 if layout_config['legend_orientation'] == 'h' else 1.02,
                y=-0.1 if layout_config['legend_orientation'] == 'h' else 0.5,
                xanchor='center' if layout_config['legend_orientation'] == 'h' else 'left'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        if progress_callback:
            progress_callback("完了", 100)
        
        return fig
    
    def create_progress_visualization(
        self,
        current_step: str,
        progress_percentage: int,
        estimated_remaining: int,
        device_type: str = "desktop"
    ) -> html.Div:
        """進捗可視化コンポーネント"""
        
        layout_config = self.device_layouts[device_type]
        colors = self.color_schemes[self.config.color_scheme]
        
        # 進捗バー
        progress_fig = go.Figure(go.Bar(
            x=[progress_percentage],
            y=['進捗'],
            orientation='h',
            marker=dict(
                color=colors['primary'][0],
                opacity=0.8
            ),
            text=[f"{progress_percentage}%"],
            textposition='inside',
            textfont=dict(
                color='white', 
                size=layout_config['font_size']
            )
        ))
        
        progress_fig.update_layout(
            xaxis=dict(range=[0, 100], showticklabels=False),
            yaxis=dict(showticklabels=False),
            height=layout_config['figure_height'] // 6,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # 時間情報
        remaining_min = estimated_remaining // 60
        remaining_sec = estimated_remaining % 60
        
        return html.Div([
            # 現在のステップ表示
            html.Div([
                html.H4(f"🔄 {current_step}", 
                       style={
                           'color': colors['primary'][0],
                           'margin': '0 0 10px 0',
                           'fontSize': f"{layout_config['font_size'] + 2}px"
                       }),
            ]),
            
            # 進捗バー
            dcc.Graph(
                figure=progress_fig,
                config={'displayModeBar': False},
                style={'height': f"{layout_config['figure_height'] // 6}px"}
            ),
            
            # 残り時間表示
            html.Div([
                html.Span(f"⏱️ 推定残り時間: {remaining_min:02d}:{remaining_sec:02d}",
                         style={
                             'color': colors['secondary'][2],
                             'fontSize': f"{layout_config['font_size']}px"
                         })
            ], style={'marginTop': '10px', 'textAlign': 'center'})
            
        ], style={
            'padding': '15px',
            'backgroundColor': 'white',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'margin': '10px 0'
        })
    
    def create_interactive_dashboard_grid(
        self,
        figures: Dict[str, go.Figure],
        device_type: str = "desktop"
    ) -> html.Div:
        """インタラクティブダッシュボードグリッド"""
        
        layout_config = self.device_layouts[device_type]
        grid_cols = layout_config['grid_columns']
        
        # グリッド構成
        grid_items = []
        figure_items = list(figures.items())
        
        for i in range(0, len(figure_items), grid_cols):
            row_figures = figure_items[i:i + grid_cols]
            
            row_components = []
            for title, fig in row_figures:
                # 各図表をカードとして配置
                card = html.Div([
                    html.H5(title, style={
                        'textAlign': 'center',
                        'margin': '0 0 10px 0',
                        'color': '#2c3e50',
                        'fontSize': f"{layout_config['font_size'] + 1}px"
                    }),
                    dcc.Graph(
                        figure=fig,
                        config={
                            'displayModeBar': True,
                            'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d'],
                            'displaylogo': False
                        }
                    )
                ], style={
                    'backgroundColor': 'white',
                    'borderRadius': '8px',
                    'padding': '15px',
                    'margin': '10px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'flex': '1',
                    'minWidth': f"{100 // grid_cols - 5}%"
                })
                
                row_components.append(card)
            
            # 行として追加
            grid_items.append(
                html.Div(row_components, style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'space-around'
                })
            )
        
        return html.Div(grid_items, style={
            'width': '100%',
            'maxWidth': '100vw',
            'overflowX': 'hidden'
        })

# グローバルインスタンス
visualization_engine = ResponsiveVisualizationEngine()

# 便利な関数
def create_responsive_figure(data, chart_type, device_type="desktop", **kwargs):
    """レスポンシブ図表生成"""
    if chart_type == "heatmap":
        return visualization_engine.create_responsive_heatmap(data, device_type=device_type, **kwargs)
    elif chart_type == "shortage":
        return visualization_engine.create_responsive_shortage_chart(data, device_type=device_type, **kwargs)
    else:
        log.warning(f"未対応のチャートタイプ: {chart_type}")
        return go.Figure()

def create_progress_display(step, progress, remaining, device_type="desktop"):
    """進捗表示生成"""
    return visualization_engine.create_progress_visualization(
        step, progress, remaining, device_type
    )

def create_dashboard_grid(figures, device_type="desktop"):
    """ダッシュボードグリッド生成"""
    return visualization_engine.create_interactive_dashboard_grid(figures, device_type)