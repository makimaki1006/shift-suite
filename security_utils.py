"""
セキュリティユーティリティモジュール
ULTRATHINKING Phase 1: Session ID検証とセキュリティ機能の実装
"""

import re
import html
import logging
import hashlib
import secrets
from typing import Optional, Any, Dict, List
from functools import wraps
import pandas as pd

# ロガー設定
log = logging.getLogger(__name__)

# セッションID検証用正規表現パターン
SESSION_ID_PATTERN = re.compile(r'^[a-f0-9]{8,64}$')
SAFE_CHARACTERS_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

# セキュリティ設定
MAX_SESSION_ID_LENGTH = 64
MIN_SESSION_ID_LENGTH = 8
MAX_DATA_KEY_LENGTH = 128
SENSITIVE_DATA_KEYS = ['password', 'token', 'secret', 'key', 'auth', 'credential']


def validate_session_id(session_id: Optional[str]) -> bool:
    """
    セッションIDの安全性を検証する

    Args:
        session_id: 検証するセッションID

    Returns:
        bool: 安全な場合True、危険な場合False
    """
    if not session_id:
        log.warning("Session ID validation failed: empty session_id")
        return False

    # 長さチェック
    if not (MIN_SESSION_ID_LENGTH <= len(session_id) <= MAX_SESSION_ID_LENGTH):
        log.warning(f"Session ID validation failed: invalid length {len(session_id)}")
        return False

    # パストラバーサル攻撃チェック
    if '..' in session_id or '/' in session_id or '\\' in session_id:
        log.error(f"Session ID validation failed: path traversal attempt detected")
        return False

    # 正規表現パターンチェック
    if not SESSION_ID_PATTERN.match(session_id):
        log.warning(f"Session ID validation failed: invalid format")
        return False

    # SQLインジェクション文字列チェック
    dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', ';', '--', '/*', '*/', 'OR ', 'AND ']
    session_upper = session_id.upper()
    for pattern in dangerous_patterns:
        if pattern in session_upper:
            log.error(f"Session ID validation failed: SQL injection pattern detected")
            return False

    return True


def sanitize_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    セッションIDをサニタイズして安全にする

    Args:
        session_id: サニタイズするセッションID

    Returns:
        str: サニタイズ済みのセッションID、または無効な場合None
    """
    if not session_id:
        return None

    # 基本的なサニタイゼーション
    sanitized = str(session_id).strip()

    # 危険な文字を除去
    sanitized = re.sub(r'[^a-f0-9]', '', sanitized.lower())

    # 長さ制限
    if len(sanitized) > MAX_SESSION_ID_LENGTH:
        sanitized = sanitized[:MAX_SESSION_ID_LENGTH]

    # 最終検証
    if validate_session_id(sanitized):
        return sanitized

    return None


def escape_html_content(content: Any) -> str:
    """
    HTMLコンテンツをエスケープしてXSS攻撃を防ぐ

    Args:
        content: エスケープするコンテンツ

    Returns:
        str: エスケープ済みの安全な文字列
    """
    if content is None:
        return ""

    # 文字列に変換
    str_content = str(content)

    # HTMLエスケープ
    escaped = html.escape(str_content, quote=True)

    # JavaScriptインジェクション対策
    dangerous_js_patterns = [
        'javascript:', 'onclick=', 'onerror=', 'onload=',
        '<script', '</script', 'eval(', 'alert('
    ]

    for pattern in dangerous_js_patterns:
        escaped = escaped.replace(pattern, '')

    return escaped


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameの内容をサニタイズしてXSS攻撃を防ぐ

    Args:
        df: サニタイズするDataFrame

    Returns:
        pd.DataFrame: サニタイズ済みのDataFrame
    """
    if df is None or df.empty:
        return df

    # カラム名のサニタイズ
    sanitized_df = df.copy()
    sanitized_df.columns = [escape_html_content(col) for col in df.columns]

    # データのサニタイズ（文字列型のみ）
    for col in sanitized_df.columns:
        if sanitized_df[col].dtype == 'object':
            sanitized_df[col] = sanitized_df[col].apply(
                lambda x: escape_html_content(x) if isinstance(x, str) else x
            )

    return sanitized_df


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    機密データをマスキングする

    Args:
        data: マスキングするデータ辞書

    Returns:
        dict: マスキング済みのデータ
    """
    if not data:
        return data

    masked_data = {}

    for key, value in data.items():
        # キー名から機密データを判定
        is_sensitive = any(
            sensitive_key in key.lower()
            for sensitive_key in SENSITIVE_DATA_KEYS
        )

        if is_sensitive:
            # 機密データはマスキング
            if isinstance(value, str):
                masked_data[key] = '*' * min(len(value), 8)
            else:
                masked_data[key] = '***MASKED***'
        else:
            masked_data[key] = value

    return masked_data


def generate_secure_session_id() -> str:
    """
    セキュアなセッションIDを生成する

    Returns:
        str: 32文字の16進数セッションID
    """
    # 暗号学的に安全なランダムバイトを生成
    random_bytes = secrets.token_bytes(16)

    # SHA-256でハッシュ化（追加のエントロピーと一貫性のため）
    session_hash = hashlib.sha256(random_bytes).hexdigest()[:32]

    return session_hash


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """
    セキュリティイベントをログに記録する

    Args:
        event_type: イベントタイプ（例：'session_validation_failed'）
        details: イベントの詳細情報
        severity: 重要度（INFO, WARNING, ERROR, CRITICAL）
    """
    # 機密データをマスキング
    safe_details = mask_sensitive_data(details) if details else {}

    # ログメッセージ作成
    log_message = f"SECURITY_EVENT[{event_type}]: {safe_details}"

    # 重要度に応じてログ出力
    if severity == "CRITICAL":
        log.critical(log_message)
    elif severity == "ERROR":
        log.error(log_message)
    elif severity == "WARNING":
        log.warning(log_message)
    else:
        log.info(log_message)


def secure_session_wrapper(func):
    """
    セッション検証を行うデコレーター

    Usage:
        @secure_session_wrapper
        def create_tab(session_id: str = None):
            # 安全なセッションIDが保証される
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # session_id引数の取得
        session_id = kwargs.get('session_id')

        if session_id is not None:
            # セッションIDの検証
            if not validate_session_id(session_id):
                log_security_event(
                    'invalid_session_id',
                    {'function': func.__name__, 'session_id': session_id[:8] + '...'},
                    'WARNING'
                )
                # サニタイズを試みる
                sanitized_id = sanitize_session_id(session_id)
                if sanitized_id:
                    kwargs['session_id'] = sanitized_id
                else:
                    # 無効なセッションIDの場合はNoneに置き換え
                    kwargs['session_id'] = None
                    log_security_event(
                        'session_id_rejected',
                        {'function': func.__name__},
                        'ERROR'
                    )

        try:
            # 元の関数を実行
            return func(*args, **kwargs)
        except Exception as e:
            # エラーハンドリング（詳細情報を露出しない）
            log_security_event(
                'function_error',
                {
                    'function': func.__name__,
                    'error_type': type(e).__name__
                },
                'ERROR'
            )
            # エラーメッセージは一般的なものに置き換え
            raise Exception(f"処理中にエラーが発生しました。管理者にお問い合わせください。")

    return wrapper


# テスト用サンプル関数
if __name__ == "__main__":
    # セッションID検証テスト
    print("=== Session ID Validation Tests ===")

    test_ids = [
        "a1b2c3d4e5f6789012345678",  # 有効
        "../../../etc/passwd",        # パストラバーサル
        "'; DROP TABLE users; --",    # SQLインジェクション
        "<script>alert('xss')</script>",  # XSS
        "abc123",                      # 短すぎる
        "A" * 100,                     # 長すぎる
        None,                          # Null
        ""                            # 空文字
    ]

    for test_id in test_ids:
        is_valid = validate_session_id(test_id)
        print(f"ID: {str(test_id)[:30]}... -> Valid: {is_valid}")

    # セキュアなセッションID生成テスト
    print("\n=== Secure Session ID Generation ===")
    for i in range(3):
        secure_id = generate_secure_session_id()
        print(f"Generated ID {i+1}: {secure_id}")

    # HTMLエスケープテスト
    print("\n=== HTML Escape Tests ===")
    test_contents = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "Normal text with 'quotes' and \"double quotes\"",
        None
    ]

    for content in test_contents:
        escaped = escape_html_content(content)
        print(f"Original: {content}")
        print(f"Escaped: {escaped}\n")