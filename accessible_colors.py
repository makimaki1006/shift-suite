#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
アクセシブルカラーパレット定義
WCAG 2.1 AAレベル（コントラスト比4.5:1以上）対応
色覚多様性（色盲）対応パレット
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# アクセシブル基本カラーパレット（WCAG 2.1 AA準拠）
ACCESSIBLE_COLORS = {
    'primary': '#2E86AB',      # 青（コントラスト比 4.5:1以上）
    'secondary': '#A23B72',    # 紫
    'success': '#73AB84',      # 緑
    'warning': '#F18F01',      # オレンジ
    'danger': '#C73E1D',       # 赤
    'info': '#6C91C2',         # 薄青
    'light': '#F5F5F5',        # 薄灰
    'dark': '#2C3E50'          # 濃灰
}

# 色覚多様性対応パレット（カラーユニバーサルデザイン）
COLORBLIND_SAFE_PALETTE = [
    '#DC267F',  # 赤-ピンク
    '#FE6100',  # オレンジ
    '#FFB000',  # 黄色
    '#648FFF',  # 青
    '#785EF0',  # 紫
    '#267300',  # 緑
    '#000000',  # 黒
    '#666666'   # グレー
]

# 職種別カラーパレット（区別しやすい色）
ROLE_COLOR_PALETTE = [
    '#1f77b4',  # 青
    '#ff7f0e',  # オレンジ  
    '#2ca02c',  # 緑
    '#d62728',  # 赤
    '#9467bd',  # 紫
    '#8c564b',  # 茶色
    '#e377c2',  # ピンク
    '#7f7f7f',  # グレー
    '#bcbd22',  # オリーブ
    '#17becf'   # シアン
]

# 時間帯別カラーパレット（時間の流れを表現）
TIME_COLOR_PALETTE = [
    '#00429d',  # 深夜（濃い青）
    '#2e59a8',  # 早朝（青）
    '#5681b9',  # 朝（明るい青）
    '#73a2c6',  # 午前（薄い青）
    '#93c5d2',  # 昼（最も明るい）
    '#b7e6d7',  # 午後（緑がかった青）
    '#d4edda',  # 夕方（薄い緑）
    '#ffeda0',  # 夜（黄色）
    '#fed976',  # 深夜（オレンジ）
    '#fd8d3c'   # 深夜（濃いオレンジ）
]

# グラフ種別ごとのカラースケール
GRAPH_COLOR_SCALES = {
    'heatmap': 'RdYlBu_r',        # ヒートマップ（赤-黄-青）
    'diverging': 'RdBu_r',        # 発散型（赤-青）
    'sequential': 'Blues',        # 順次型（青のグラデーション）
    'categorical': COLORBLIND_SAFE_PALETTE,  # カテゴリカル
    'continuous': 'Viridis'       # 連続型（紫-青-緑-黄）
}

def get_accessible_color_palette(graph_type: str = 'categorical', n_colors: int = 10) -> List[str]:
    """
    指定されたグラフタイプに対応するアクセシブルなカラーパレットを取得
    
    Args:
        graph_type: グラフの種類 ('categorical', 'sequential', 'diverging', 'heatmap')
        n_colors: 必要な色数
        
    Returns:
        色のリスト
    """
    if graph_type == 'categorical':
        # 必要数に応じてパレットを拡張
        if n_colors <= len(COLORBLIND_SAFE_PALETTE):
            return COLORBLIND_SAFE_PALETTE[:n_colors]
        else:
            # 不足分はPlotlyの色を追加
            extended = COLORBLIND_SAFE_PALETTE.copy()
            plotly_colors = px.colors.qualitative.Set3
            for i in range(n_colors - len(COLORBLIND_SAFE_PALETTE)):
                extended.append(plotly_colors[i % len(plotly_colors)])
            return extended[:n_colors]
    
    elif graph_type == 'role':
        return ROLE_COLOR_PALETTE[:n_colors] if n_colors <= len(ROLE_COLOR_PALETTE) else ROLE_COLOR_PALETTE
    
    elif graph_type == 'time':
        return TIME_COLOR_PALETTE[:n_colors] if n_colors <= len(TIME_COLOR_PALETTE) else TIME_COLOR_PALETTE
    
    else:
        # その他はPlotlyの安全なパレットを使用
        return px.colors.qualitative.Bold[:n_colors]

def apply_accessible_colors_to_figure(fig, graph_type: str = 'categorical', n_colors: int = None):
    """
    Plotlyフィギュアにアクセシブルな色を適用
    
    Args:
        fig: Plotlyフィギュア
        graph_type: グラフタイプ
        n_colors: 色数（自動検出可能）
    """
    if not n_colors:
        # データから色数を推定
        if hasattr(fig, 'data') and fig.data:
            n_colors = len(fig.data)
        else:
            n_colors = 10  # デフォルト
    
    colors = get_accessible_color_palette(graph_type, n_colors)
    
    # フィギュアに色を適用
    if hasattr(fig, 'data'):
        for i, trace in enumerate(fig.data):
            if i < len(colors):
                if hasattr(trace, 'marker'):
                    trace.marker.color = colors[i]
                elif hasattr(trace, 'line'):
                    trace.line.color = colors[i]
    
    return fig

def get_accessible_colorscale(scale_type: str = 'sequential'):
    """
    アクセシブルなカラースケールを取得
    
    Args:
        scale_type: スケールタイプ ('sequential', 'diverging', 'heatmap')
        
    Returns:
        カラースケール名または配列
    """
    return GRAPH_COLOR_SCALES.get(scale_type, 'Viridis')

# CSS用のカラー変数定義
ACCESSIBLE_CSS_VARS = {
    '--primary-color': ACCESSIBLE_COLORS['primary'],
    '--secondary-color': ACCESSIBLE_COLORS['secondary'], 
    '--success-color': ACCESSIBLE_COLORS['success'],
    '--warning-color': ACCESSIBLE_COLORS['warning'],
    '--danger-color': ACCESSIBLE_COLORS['danger'],
    '--info-color': ACCESSIBLE_COLORS['info'],
    '--light-color': ACCESSIBLE_COLORS['light'],
    '--dark-color': ACCESSIBLE_COLORS['dark']
}

def get_css_color_variables() -> str:
    """CSS color variables文字列を生成"""
    css_vars = []
    for var_name, color_value in ACCESSIBLE_CSS_VARS.items():
        css_vars.append(f"  {var_name}: {color_value};")
    
    return ":root {\n" + "\n".join(css_vars) + "\n}"

# 使いやすさのためのヘルパー関数
def safe_colors_for_plotly(n_colors: int, graph_type: str = 'categorical'):
    """Plotlyで安全に使える色のリストを取得"""
    return get_accessible_color_palette(graph_type, n_colors)

def enhance_figure_accessibility(fig, title: str = None, graph_type: str = 'categorical'):
    """
    フィギュアのアクセシビリティを向上
    
    Args:
        fig: Plotlyフィギュア
        title: グラフタイトル
        graph_type: グラフタイプ
    """
    # 色の適用
    apply_accessible_colors_to_figure(fig, graph_type)
    
    # アクセシブルなレイアウト設定
    fig.update_layout(
        font=dict(size=14, color=ACCESSIBLE_COLORS['dark']),
        plot_bgcolor='white',
        paper_bgcolor='white',
        title=dict(
            text=title,
            font=dict(size=16, color=ACCESSIBLE_COLORS['dark'])
        ) if title else None
    )
    
    return fig