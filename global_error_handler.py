#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
グローバルエラーハンドリングシステム
統一されたエラー処理とユーザーフレンドリーなメッセージ
"""

import json
import logging
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
import pandas as pd
import dash
from dash import html
from dash.exceptions import PreventUpdate

log = logging.getLogger(__name__)

class GlobalErrorHandler:
    """統一エラーハンドリングシステム"""
    
    def __init__(self, error_log_path='error_log.json'):
        self.error_log_path = Path(error_log_path)
        self.error_count = 0
        self.session_errors = []
        
        # エラーログディレクトリを作成
        self.error_log_path.parent.mkdir(exist_ok=True)
        
    def log_error(self, func_name: str, error: Exception, context: dict = None):
        """エラー情報をログに記録"""
        self.error_count += 1
        
        error_details = {
            'id': self.error_count,
            'timestamp': datetime.now().isoformat(),
            'function': func_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # セッション内エラーリストに追加
        self.session_errors.append(error_details)
        
        # ファイルに記録
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                json.dump(error_details, f, ensure_ascii=False, indent=2)
                f.write('\n')
        except Exception as e:
            log.error(f"Failed to write error log: {e}")
        
        log.error(f"Error ID {self.error_count}: {func_name} - {str(error)}")
        
    def get_user_friendly_message(self, error: Exception) -> str:
        """ユーザーフレンドリーなエラーメッセージを生成"""
        error_type = type(error).__name__
        
        message_map = {
            'FileNotFoundError': 'ファイルが見つかりません',
            'PermissionError': 'アクセス権限がありません', 
            'ValueError': 'データ形式が正しくありません',
            'KeyError': 'データ項目が見つかりません',
            'MemoryError': 'メモリ不足が発生しました',
            'TimeoutError': 'タイムアウトが発生しました',
            'ImportError': '必要なライブラリが見つかりません',
            'AttributeError': 'データの属性にアクセスできません',
            'TypeError': 'データの型が正しくありません',
            'ZeroDivisionError': '計算でゼロ除算が発生しました',
            'IndexError': 'データの範囲外にアクセスしました',
            'ConnectionError': 'ネットワーク接続に問題があります'
        }
        
        base_message = message_map.get(error_type, '予期しないエラーが発生しました')
        
        # 特定のエラーメッセージパターンに基づく詳細化
        error_str = str(error).lower()
        if 'encoding' in error_str or 'utf-8' in error_str:
            return 'ファイルの文字エンコーディングに問題があります（UTF-8を推奨）'
        elif 'permission' in error_str:
            return 'ファイルへのアクセス権限がありません'
        elif 'disk space' in error_str or 'no space' in error_str:
            return 'ディスク容量が不足しています'
        elif 'out of memory' in error_str:
            return 'メモリが不足しています。データサイズを削減してください'
            
        return base_message
    
    def create_error_ui(self, error: Exception, error_id: int, show_details: bool = True) -> html.Div:
        """エラー用UIコンポーネントを生成"""
        user_message = self.get_user_friendly_message(error)
        
        components = [
            html.H4("⚠️ エラーが発生しました", style={'color': '#dc3545', 'marginBottom': '10px'}),
            html.P(user_message, style={'fontSize': '16px', 'marginBottom': '15px'}),
            html.P("💡 対処法:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            html.Ul([
                html.Li("データファイルの形式を確認してください"),
                html.Li("ファイルサイズが大きすぎないか確認してください"),
                html.Li("ページを再読み込みして再試行してください"),
                html.Li("問題が続く場合は管理者に連絡してください")
            ], style={'marginBottom': '15px'})
        ]
        
        if show_details:
            components.append(
                html.Details([
                    html.Summary("🔍 詳細情報", style={'cursor': 'pointer', 'color': '#007bff'}),
                    html.Pre(f"Error ID: {error_id}\nType: {type(error).__name__}\nMessage: {str(error)}", 
                           style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'border': '1px solid #dee2e6'})
                ])
            )
        
        return html.Div(components, style={
            'padding': '20px',
            'backgroundColor': '#f8d7da',
            'border': '1px solid #f5c6cb',
            'borderRadius': '8px',
            'margin': '10px'
        })
    
    def get_error_summary(self) -> dict:
        """セッション内のエラー統計を取得"""
        if not self.session_errors:
            return {'total': 0, 'types': {}, 'recent': []}
        
        # エラー種別の統計
        error_types = {}
        for err in self.session_errors:
            err_type = err['error_type']
            error_types[err_type] = error_types.get(err_type, 0) + 1
        
        # 最新5件のエラー
        recent_errors = self.session_errors[-5:]
        
        return {
            'total': len(self.session_errors),
            'types': error_types,
            'recent': recent_errors
        }

# グローバルエラーハンドラーインスタンス
error_handler = GlobalErrorHandler()

def global_error_handler(func):
    """統一エラーハンドリングデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PreventUpdate:
            # PreventUpdateはそのまま通す
            raise
        except Exception as e:
            # エラーをログに記録
            context = {
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys()),
                'function_module': func.__module__
            }
            
            error_handler.log_error(func.__name__, e, context)
            
            # ユーザーフレンドリーなエラーUIを返却
            error_ui = error_handler.create_error_ui(e, error_handler.error_count)
            
            # 関数の戻り値パターンに応じて適切に返す
            try:
                # 戻り値の個数を推定（Dashコールバックのパターン分析）
                import inspect
                sig = inspect.signature(func)
                annotations = [param.annotation for param in sig.parameters.values()]
                
                # 複数の戻り値が期待される場合
                if len(annotations) > 1 or func.__name__.startswith(('update_', 'create_')):
                    # 一般的なDashコールバックパターン
                    return error_ui, {'display': 'none'}, None
                else:
                    return error_ui
            except:
                # フォールバック: エラーUIのみ返す
                return error_ui
    
    return wrapper

def safe_data_operation(func):
    """データ操作専用の安全なデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # データフレームの安全性チェック
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    log.warning(f"{func.__name__}: 空のDataFrameが返されました")
                elif result.shape[0] > 100000:
                    log.warning(f"{func.__name__}: 大きなデータセット ({result.shape}) - メモリ注意")
            
            return result
            
        except Exception as e:
            log.error(f"{func.__name__} failed: {e}")
            
            # データ操作の場合は適切なデフォルト値を返す
            if 'dataframe' in func.__name__.lower() or 'df' in func.__name__.lower():
                return pd.DataFrame()
            elif 'list' in func.__name__.lower():
                return []
            elif 'dict' in func.__name__.lower():
                return {}
            else:
                return None
    
    return wrapper

# 便利な関数
def log_system_health():
    """システムの健全性をログに出力"""
    error_summary = error_handler.get_error_summary()
    log.info(f"Session Error Summary: {error_summary['total']} errors, Types: {error_summary['types']}")
    
def create_error_dashboard() -> html.Div:
    """エラー状況ダッシュボードを作成（デバッグ用）"""
    error_summary = error_handler.get_error_summary()
    
    if error_summary['total'] == 0:
        return html.Div([
            html.H4("✅ システム状態: 正常"),
            html.P("エラーは発生していません")
        ])
    
    return html.Div([
        html.H4("⚠️ エラー統計"),
        html.P(f"総エラー数: {error_summary['total']}"),
        html.H5("エラー種別:"),
        html.Ul([
            html.Li(f"{error_type}: {count}件")
            for error_type, count in error_summary['types'].items()
        ]),
        html.H5("最近のエラー:"),
        html.Ul([
            html.Li(f"{err['timestamp']}: {err['function']} - {err['error_type']}")
            for err in error_summary['recent']
        ])
    ])