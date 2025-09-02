#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
エラー境界実装 - Phase 1 即座対応
部分的エラーでの全体クラッシュを防ぐ
"""

import logging
import traceback
from functools import wraps
from dash import html, dcc
from typing import Any, Callable, Optional
import json

log = logging.getLogger(__name__)

class ErrorBoundary:
    """エラー境界コンポーネント - アプリケーションの安定性を保証"""
    
    def __init__(self, fallback_ui=None):
        """
        エラー境界の初期化
        
        Args:
            fallback_ui: エラー時に表示するUIコンポーネント
        """
        self.error_count = 0
        self.error_log = []
        self.fallback_ui = fallback_ui or self._default_fallback_ui
        
    def _default_fallback_ui(self, error_info: dict) -> html.Div:
        """デフォルトのエラー表示UI"""
        return html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle",
                      style={'fontSize': '48px', 'color': '#e74c3c', 'marginBottom': '20px'}),
                html.H3("申し訳ございません", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                html.P("一時的な問題が発生しました。", style={'fontSize': '16px', 'marginBottom': '20px'}),
                html.Details([
                    html.Summary("詳細情報", style={'cursor': 'pointer', 'color': '#3498db'}),
                    html.Pre(
                        json.dumps(error_info, ensure_ascii=False, indent=2),
                        style={'fontSize': '12px', 'backgroundColor': '#f8f9fa', 'padding': '10px'}
                    )
                ], style={'marginTop': '20px'}),
                html.Div([
                    html.Button(
                        "ページを再読み込み",
                        id="reload-page-btn",
                        style={
                            'marginTop': '20px',
                            'padding': '10px 20px',
                            'backgroundColor': '#3498db',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer'
                        }
                    )
                ])
            ], style={
                'textAlign': 'center',
                'padding': '40px',
                'backgroundColor': 'white',
                'borderRadius': '8px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
            })
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'minHeight': '400px',
            'backgroundColor': '#f8f9fa'
        })
    
    def safe_callback(self, func: Callable) -> Callable:
        """
        コールバックをエラー境界で保護
        
        Args:
            func: 保護するコールバック関数
            
        Returns:
            エラー保護されたコールバック関数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.error_count += 1
                error_info = self._capture_error_info(e, func.__name__)
                self.error_log.append(error_info)
                
                log.error(f"Callback error in {func.__name__}: {str(e)}")
                log.debug(traceback.format_exc())
                
                # エラー回数が多い場合は警告
                if self.error_count > 10:
                    log.warning(f"High error rate detected: {self.error_count} errors")
                
                return self.fallback_ui(error_info)
        
        return wrapper
    
    def safe_component(self, component_func: Callable) -> Callable:
        """
        コンポーネント生成をエラー境界で保護
        
        Args:
            component_func: 保護するコンポーネント生成関数
            
        Returns:
            エラー保護されたコンポーネント生成関数
        """
        @wraps(component_func)
        def wrapper(*args, **kwargs):
            try:
                return component_func(*args, **kwargs)
            except Exception as e:
                error_info = self._capture_error_info(e, component_func.__name__)
                log.error(f"Component error in {component_func.__name__}: {str(e)}")
                
                return html.Div([
                    html.P(f"コンポーネントの読み込みに失敗しました: {component_func.__name__}",
                          style={'color': '#e74c3c', 'padding': '20px'})
                ])
        
        return wrapper
    
    def _capture_error_info(self, error: Exception, context: str) -> dict:
        """
        エラー情報を収集
        
        Args:
            error: 発生したエラー
            context: エラーが発生したコンテキスト
            
        Returns:
            エラー情報の辞書
        """
        import datetime
        
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_count': self.error_count
        }
    
    def wrap_layout(self, layout_func: Callable) -> Callable:
        """
        レイアウト全体をエラー境界で保護
        
        Args:
            layout_func: レイアウト生成関数
            
        Returns:
            エラー保護されたレイアウト
        """
        @wraps(layout_func)
        def wrapper(*args, **kwargs):
            try:
                return layout_func(*args, **kwargs)
            except Exception as e:
                log.critical(f"Layout error: {str(e)}")
                log.critical(traceback.format_exc())
                
                return html.Div([
                    html.H1("システムエラー", style={'color': '#e74c3c', 'textAlign': 'center'}),
                    html.P("アプリケーションの起動に失敗しました。", 
                          style={'textAlign': 'center', 'fontSize': '18px'}),
                    html.P("管理者にお問い合わせください。",
                          style={'textAlign': 'center', 'color': '#666'})
                ])
        
        return wrapper
    
    def get_error_summary(self) -> dict:
        """
        エラーサマリーを取得
        
        Returns:
            エラー統計情報
        """
        if not self.error_log:
            return {'total_errors': 0, 'unique_errors': 0, 'last_error': None}
        
        unique_errors = len(set(e['error_type'] for e in self.error_log))
        last_error = self.error_log[-1] if self.error_log else None
        
        return {
            'total_errors': self.error_count,
            'unique_errors': unique_errors,
            'last_error': last_error,
            'error_types': self._count_error_types()
        }
    
    def _count_error_types(self) -> dict:
        """エラータイプ別の集計"""
        from collections import Counter
        
        if not self.error_log:
            return {}
        
        error_types = [e['error_type'] for e in self.error_log]
        return dict(Counter(error_types))
    
    def reset_errors(self):
        """エラー情報をリセット"""
        self.error_count = 0
        self.error_log = []
        log.info("Error boundary reset")

# グローバルインスタンス
error_boundary = ErrorBoundary()

# デコレータとして使いやすくする
safe_callback = error_boundary.safe_callback
safe_component = error_boundary.safe_component

# Dashアプリケーション用のヘルパー関数
def apply_error_boundaries(app):
    """
    Dashアプリケーション全体にエラー境界を適用
    
    Args:
        app: Dashアプリケーションインスタンス
    """
    import dash
    
    # レイアウトのエラー境界
    if hasattr(app, 'layout') and callable(app.layout):
        original_layout = app.layout
        app.layout = error_boundary.wrap_layout(original_layout)
    
    log.info("Error boundaries applied to Dash application")
    
    return app

# エラー回復用のクライアントサイドコールバック
error_recovery_script = """
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    error_recovery: {
        reload_page: function(n_clicks) {
            if (n_clicks > 0) {
                window.location.reload();
            }
            return '';
        }
    }
});
"""