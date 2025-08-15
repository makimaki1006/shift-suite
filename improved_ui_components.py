#!/usr/bin/env python3
"""
UI改善コンポーネント
- 統一されたエラー表示
- ユーザーフレンドリーなメッセージ
- レスポンシブデザイン対応
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dash import html, dcc, dash_table
import plotly.graph_objects as go
from improved_data_validation import ValidationResult

log = logging.getLogger(__name__)

# ===== カラーパレット・スタイル定数 =====

class UIColors:
    """統一カラーパレット"""
    # プライマリカラー
    PRIMARY = "#3498db"
    PRIMARY_DARK = "#2980b9"
    PRIMARY_LIGHT = "#85c1e9"
    
    # ステータスカラー
    SUCCESS = "#27ae60"
    SUCCESS_LIGHT = "#d4edda"
    SUCCESS_BORDER = "#c3e6cb"
    
    WARNING = "#f39c12"
    WARNING_LIGHT = "#fff3cd"
    WARNING_BORDER = "#ffeaa7"
    
    ERROR = "#e74c3c"
    ERROR_LIGHT = "#f8d7da"
    ERROR_BORDER = "#f5c6cb"
    
    INFO = "#17a2b8"
    INFO_LIGHT = "#d1ecf1"
    INFO_BORDER = "#bee5eb"
    
    # ニュートラルカラー
    DARK = "#2c3e50"
    GRAY = "#95a5a6"
    LIGHT_GRAY = "#ecf0f1"
    WHITE = "#ffffff"

class UIStyles:
    """統一スタイル定義"""
    
    # ベーススタイル
    BASE_CARD = {
        'backgroundColor': UIColors.WHITE,
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'padding': '20px',
        'marginBottom': '20px'
    }
    
    BASE_BUTTON = {
        'border': 'none',
        'borderRadius': '5px',
        'padding': '10px 20px',
        'fontSize': '14px',
        'fontWeight': '500',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease'
    }
    
    # エラー表示スタイル
    ERROR_CARD = {
        **BASE_CARD,
        'backgroundColor': UIColors.ERROR_LIGHT,
        'border': f'1px solid {UIColors.ERROR_BORDER}',
        'borderLeftWidth': '4px',
        'borderLeftColor': UIColors.ERROR
    }
    
    WARNING_CARD = {
        **BASE_CARD,
        'backgroundColor': UIColors.WARNING_LIGHT,
        'border': f'1px solid {UIColors.WARNING_BORDER}',
        'borderLeftWidth': '4px',
        'borderLeftColor': UIColors.WARNING
    }
    
    SUCCESS_CARD = {
        **BASE_CARD,
        'backgroundColor': UIColors.SUCCESS_LIGHT,
        'border': f'1px solid {UIColors.SUCCESS_BORDER}',
        'borderLeftWidth': '4px',
        'borderLeftColor': UIColors.SUCCESS
    }
    
    INFO_CARD = {
        **BASE_CARD,
        'backgroundColor': UIColors.INFO_LIGHT,
        'border': f'1px solid {UIColors.INFO_BORDER}',
        'borderLeftWidth': '4px',
        'borderLeftColor': UIColors.INFO
    }

# ===== 改善されたエラー表示コンポーネント =====

class ErrorDisplayComponents:
    """統一エラー表示コンポーネント"""
    
    @staticmethod
    def create_error_alert(
        title: str,
        message: Union[str, List[str]],
        error_type: str = "error",
        dismissible: bool = False,
        show_details: bool = False,
        details: Optional[Dict[str, Any]] = None
    ) -> html.Div:
        """統一エラーアラート"""
        
        # アイコンとカラー設定
        icons = {
            'error': '❌',
            'warning': '⚠️', 
            'success': '✅',
            'info': 'ℹ️'
        }
        
        styles = {
            'error': UIStyles.ERROR_CARD,
            'warning': UIStyles.WARNING_CARD,
            'success': UIStyles.SUCCESS_CARD,
            'info': UIStyles.INFO_CARD
        }
        
        icon = icons.get(error_type, '❌')
        style = styles.get(error_type, UIStyles.ERROR_CARD)
        
        # メッセージの処理
        if isinstance(message, list):
            message_elements = [html.Li(msg) for msg in message]
            message_content = html.Ul(message_elements, style={'marginBottom': '0'})
        else:
            message_content = html.P(message, style={'marginBottom': '0'})
        
        # 基本コンテンツ
        content = [
            html.Div([
                html.Span(icon, style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Strong(title, style={'fontSize': '16px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
            message_content
        ]
        
        # 詳細情報の追加
        if show_details and details:
            details_content = []
            for key, value in details.items():
                if isinstance(value, dict):
                    value_str = ', '.join(f"{k}: {v}" for k, v in value.items())
                elif isinstance(value, list):
                    value_str = ', '.join(str(v) for v in value)
                else:
                    value_str = str(value)
                
                details_content.append(
                    html.P([
                        html.Strong(f"{key}: "),
                        html.Span(value_str)
                    ], style={'margin': '5px 0', 'fontSize': '12px'})
                )
            
            content.append(
                html.Details([
                    html.Summary("詳細情報を表示", style={'cursor': 'pointer', 'marginTop': '10px'}),
                    html.Div(details_content, style={'marginTop': '10px', 'paddingLeft': '20px'})
                ])
            )
        
        # 閉じるボタン
        if dismissible:
            content.append(
                html.Button(
                    "×",
                    id={'type': 'close-alert', 'index': f"alert-{error_type}"},
                    style={
                        'position': 'absolute',
                        'top': '10px',
                        'right': '15px',
                        'background': 'none',
                        'border': 'none',
                        'fontSize': '20px',
                        'cursor': 'pointer',
                        'color': UIColors.GRAY
                    }
                )
            )
            style['position'] = 'relative'
        
        return html.Div(content, style=style)
    
    @staticmethod
    def create_validation_summary(validation_result: ValidationResult) -> html.Div:
        """検証結果サマリー"""
        if validation_result.is_valid and not validation_result.warnings:
            return ErrorDisplayComponents.create_error_alert(
                "検証完了", 
                "データは正常に検証されました",
                "success"
            )
        
        components = []
        
        # エラー表示
        if validation_result.errors:
            components.append(
                ErrorDisplayComponents.create_error_alert(
                    "検証エラー",
                    validation_result.errors,
                    "error",
                    show_details=True,
                    details={
                        'ファイル情報': validation_result.file_info,
                        'データ情報': validation_result.data_info
                    }
                )
            )
        
        # 警告表示
        if validation_result.warnings:
            components.append(
                ErrorDisplayComponents.create_error_alert(
                    "注意事項",
                    validation_result.warnings,
                    "warning",
                    show_details=True,
                    details={
                        'データ情報': validation_result.data_info
                    }
                )
            )
        
        return html.Div(components)
    
    @staticmethod
    def create_loading_indicator(message: str = "処理中...", show_progress: bool = True) -> html.Div:
        """ローディングインジケーター"""
        content = [
            dcc.Loading(
                id="loading-spinner",
                type="default",
                children=html.Div([
                    html.I(className="fas fa-spinner fa-spin", style={'fontSize': '24px', 'color': UIColors.PRIMARY}),
                    html.P(message, style={'marginTop': '10px', 'fontSize': '14px'})
                ], style={'textAlign': 'center', 'padding': '20px'})
            )
        ]
        
        if show_progress:
            content.append(
                dcc.Interval(
                    id='loading-interval',
                    interval=100,
                    n_intervals=0
                )
            )
        
        return html.Div(content, style=UIStyles.INFO_CARD)

# ===== データ表示コンポーネント =====

class DataDisplayComponents:
    """データ表示用コンポーネント"""
    
    @staticmethod
    def create_data_preview_table(
        df, 
        title: str = "データプレビュー",
        max_rows: int = 10,
        max_cols: int = 10
    ) -> html.Div:
        """データプレビューテーブル"""
        
        if df.empty:
            return ErrorDisplayComponents.create_error_alert(
                "データなし",
                "表示するデータがありません",
                "info"
            )
        
        # データの一部を取得
        preview_df = df.head(max_rows).iloc[:, :max_cols]
        
        # 統計情報
        stats = {
            '総行数': f"{df.shape[0]:,}",
            '総列数': f"{df.shape[1]:,}",
            'メモリ使用量': f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB"
        }
        
        return html.Div([
            html.H4(title, style={'marginBottom': '15px'}),
            
            # 統計情報
            html.Div([
                html.Div([
                    html.Strong(key + ": "),
                    html.Span(value)
                ], style={'display': 'inline-block', 'marginRight': '20px'})
                for key, value in stats.items()
            ], style={'marginBottom': '15px', 'fontSize': '14px'}),
            
            # テーブル
            dash_table.DataTable(
                data=preview_df.to_dict('records'),
                columns=[{"name": col, "id": col} for col in preview_df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontSize': '12px'
                },
                style_header={
                    'backgroundColor': UIColors.PRIMARY_LIGHT,
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': UIColors.LIGHT_GRAY
                    }
                ]
            ),
            
            # 省略メッセージ
            html.P(
                f"※ 先頭{min(max_rows, df.shape[0])}行、"
                f"左から{min(max_cols, df.shape[1])}列を表示",
                style={'fontSize': '12px', 'color': UIColors.GRAY, 'marginTop': '10px'}
            ) if df.shape[0] > max_rows or df.shape[1] > max_cols else None
            
        ], style=UIStyles.BASE_CARD)
    
    @staticmethod
    def create_file_info_card(file_info: Dict[str, Any]) -> html.Div:
        """ファイル情報カード"""
        
        info_items = []
        for key, value in file_info.items():
            if key == 'size_bytes' and isinstance(value, (int, float)):
                # バイト数を人間が読みやすい形式に変換
                if value > 1024 * 1024:
                    display_value = f"{value / 1024 / 1024:.1f} MB"
                elif value > 1024:
                    display_value = f"{value / 1024:.1f} KB"
                else:
                    display_value = f"{value} bytes"
            else:
                display_value = str(value)
            
            info_items.append(
                html.Div([
                    html.Strong(f"{key}: "),
                    html.Span(display_value)
                ], style={'marginBottom': '5px'})
            )
        
        return html.Div([
            html.H5("ファイル情報", style={'marginBottom': '15px'}),
            html.Div(info_items)
        ], style=UIStyles.BASE_CARD)

# ===== アップロード改善コンポーネント =====

class ImprovedUploadComponents:
    """改善されたアップロードコンポーネント"""
    
    @staticmethod
    def create_enhanced_upload_area() -> html.Div:
        """拡張アップロードエリア"""
        return html.Div([
            # ヘッダー
            html.Div([
                html.H2("🚀 Shift-Suite 高速分析ビューア", 
                       style={'textAlign': 'center', 'color': UIColors.DARK, 'marginBottom': '10px'}),
                html.P("シフトデータをアップロードして高速分析を開始しましょう",
                      style={'textAlign': 'center', 'color': UIColors.GRAY, 'marginBottom': '30px'})
            ]),
            
            # サポート形式表示
            html.Div([
                html.H4("📁 サポートファイル形式", style={'color': UIColors.DARK, 'textAlign': 'center'}),
                html.Div([
                    html.Div([
                        html.Code(".zip", style={'backgroundColor': '#e3f2fd', 'padding': '4px 8px', 'borderRadius': '4px'}),
                        html.P("複数シナリオ分析用", style={'fontSize': '12px', 'margin': '5px 0'})
                    ], style={'textAlign': 'center', 'margin': '0 15px'}),
                    html.Div([
                        html.Code(".xlsx", style={'backgroundColor': '#e8f5e8', 'padding': '4px 8px', 'borderRadius': '4px'}),
                        html.P("Excel形式データ", style={'fontSize': '12px', 'margin': '5px 0'})
                    ], style={'textAlign': 'center', 'margin': '0 15px'}),
                    html.Div([
                        html.Code(".csv", style={'backgroundColor': '#fff3e0', 'padding': '4px 8px', 'borderRadius': '4px'}),
                        html.P("CSV形式データ", style={'fontSize': '12px', 'margin': '5px 0'})
                    ], style={'textAlign': 'center', 'margin': '0 15px'})
                ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'})
            ]),
            
            # メインアップロードエリア
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt", 
                          style={'fontSize': '64px', 'color': UIColors.PRIMARY, 'marginBottom': '15px'}),
                    html.H3("📤 ここにファイルをドラッグ&ドロップ", 
                           style={'fontWeight': 'bold', 'color': UIColors.DARK, 'marginBottom': '10px'}),
                    html.P("またはクリックしてファイルを選択してください", 
                          style={'color': UIColors.GRAY, 'fontSize': '16px'}),
                    
                    # 視覚的な境界線
                    html.Div(style={
                        'position': 'absolute',
                        'top': '10px', 'left': '10px', 'right': '10px', 'bottom': '10px',
                        'border': f'3px dashed {UIColors.PRIMARY}',
                        'borderRadius': '12px',
                        'pointerEvents': 'none'
                    })
                ], style={'position': 'relative', 'textAlign': 'center', 'padding': '40px'}),
                style={
                    'minHeight': '250px',
                    'backgroundColor': '#f8f9ff',
                    'border': f'2px solid {UIColors.PRIMARY}',
                    'borderRadius': '12px',
                    'cursor': 'pointer',
                    'transition': 'all 0.3s ease',
                    'marginBottom': '20px'
                },
                multiple=False
            ),
            
            # 使用方法ガイド
            html.Div([
                html.H4("📚 使用方法", style={'color': UIColors.DARK}),
                html.Ol([
                    html.Li("上の青いエリアにシフトデータファイルをドラッグ&ドロップ"),
                    html.Li("ファイルのアップロードと解析が自動で実行されます"),
                    html.Li("分析結果がタブ形式で表示されます")
                ], style={'color': UIColors.GRAY, 'lineHeight': '1.6'})
            ], style={
                'backgroundColor': UIColors.LIGHT_GRAY, 
                'padding': '20px', 
                'borderRadius': '8px',
                'border': f'1px solid {UIColors.GRAY}'
            })
            
        ], style={'maxWidth': '800px', 'margin': '0 auto', 'padding': '20px'})
    
    @staticmethod
    def create_upload_progress_display(current_step: str, progress: int, message: str) -> html.Div:
        """アップロード進捗表示"""
        
        steps = [
            {'key': 'validation', 'label': '検証', 'icon': '🔍'},
            {'key': 'extraction', 'label': '展開', 'icon': '📦'},
            {'key': 'analysis', 'label': '分析', 'icon': '⚡'},
            {'key': 'complete', 'label': '完了', 'icon': '✅'}
        ]
        
        step_elements = []
        for i, step in enumerate(steps):
            is_current = step['key'] == current_step
            is_completed = i < [s['key'] for s in steps].index(current_step) if current_step in [s['key'] for s in steps] else False
            
            style = {
                'display': 'inline-block',
                'padding': '10px 15px',
                'margin': '0 5px',
                'borderRadius': '20px',
                'fontSize': '14px',
                'fontWeight': 'bold'
            }
            
            if is_completed:
                style.update({
                    'backgroundColor': UIColors.SUCCESS,
                    'color': UIColors.WHITE
                })
            elif is_current:
                style.update({
                    'backgroundColor': UIColors.PRIMARY,
                    'color': UIColors.WHITE
                })
            else:
                style.update({
                    'backgroundColor': UIColors.LIGHT_GRAY,
                    'color': UIColors.GRAY
                })
            
            step_elements.append(
                html.Span([
                    html.Span(step['icon'], style={'marginRight': '5px'}),
                    step['label']
                ], style=style)
            )
        
        return html.Div([
            html.H4("アップロード進捗", style={'marginBottom': '15px'}),
            html.Div(step_elements, style={'textAlign': 'center', 'marginBottom': '20px'}),
            dcc.Interval(id='progress-bar', value=progress, max=100),
            html.P(message, style={'textAlign': 'center', 'fontSize': '14px', 'color': UIColors.GRAY})
        ], style=UIStyles.INFO_CARD)

# ===== ユーティリティ関数 =====

def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式でフォーマット"""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024 / 1024:.1f} GB"
    elif size_bytes >= 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes} bytes"

def create_responsive_container(children, container_class: str = "container") -> html.Div:
    """レスポンシブコンテナー"""
    return html.Div(
        children,
        className=container_class,
        style={
            'maxWidth': '1200px',
            'margin': '0 auto',
            'padding': '20px'
        }
    )

# ===== グローバルインスタンス =====
error_display = ErrorDisplayComponents()
data_display = DataDisplayComponents()
upload_components = ImprovedUploadComponents()