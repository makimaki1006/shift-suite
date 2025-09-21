"""
セッション統合レイヤー
dash_app.pyとSessionManagerを繋ぐ統合層
"""

import os
from pathlib import Path
from typing import Optional, Any, Dict, Callable
from functools import wraps
import logging
import pandas as pd

# Dashインポート（インストールされている場合）
try:
    from dash import callback_context, dcc, html
    import dash
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    callback_context = None

from session_manager import session_manager, get_workspace

# ロガー設定
log = logging.getLogger(__name__)

# グローバル変数（後方互換性のため）
CURRENT_SCENARIO_DIR: Optional[Path] = None


class SessionIntegration:
    """
    既存のdash_app.pyとSessionManagerを統合するクラス
    """

    def __init__(self):
        self.fallback_session_id = None
        self.migration_mode = False
        self.compatibility_mode = True  # 後方互換モード

    def get_session_id(self) -> Optional[str]:
        """
        現在のセッションIDを取得
        優先順位:
        1. Dashコールバックコンテキストから
        2. 環境変数から
        3. フォールバックセッションID
        4. 新規生成
        """
        # Dashコンテキストから取得
        if DASH_AVAILABLE and callback_context:
            try:
                # Statesから取得
                if hasattr(callback_context, 'states'):
                    session_id = callback_context.states.get('session-id-store.data')
                    if session_id:
                        return session_id

                # Inputsから取得
                if hasattr(callback_context, 'inputs'):
                    session_id = callback_context.inputs.get('session-id-store.data')
                    if session_id:
                        return session_id

                # Triggered propsから取得
                if hasattr(callback_context, 'triggered'):
                    for item in callback_context.triggered:
                        if isinstance(item, dict) and item.get('prop_id', '').startswith('session-id-store'):
                            session_id = item.get('value')
                            if session_id:
                                return session_id

            except Exception as e:
                log.debug(f"Failed to get session from context: {e}")

        # 環境変数から取得
        env_session = os.environ.get('DASH_SESSION_ID')
        if env_session:
            return env_session

        # フォールバックセッションID
        if self.fallback_session_id:
            return self.fallback_session_id

        # 新規生成
        import uuid
        new_session_id = str(uuid.uuid4())
        self.fallback_session_id = new_session_id
        log.info(f"Generated fallback session ID: {new_session_id[:8]}...")
        return new_session_id

    def get_workspace_path(self, session_id: Optional[str] = None) -> Path:
        """
        セッション用のワークスペースパスを取得

        Args:
            session_id: セッションID（省略時は自動取得）

        Returns:
            ワークスペースパス
        """
        if session_id is None:
            session_id = self.get_session_id()

        # SessionManagerから取得
        workspace = session_manager.get_workspace(session_id)

        if workspace is None:
            # ワークスペースが存在しない場合は作成
            _, workspace = session_manager.create_session(session_id)

        return workspace

    def migrate_from_global_dir(self, global_dir: Path) -> str:
        """
        既存のCURRENT_SCENARIO_DIRからセッションベースに移行

        Args:
            global_dir: 既存のグローバルディレクトリ

        Returns:
            作成されたセッションID
        """
        if not global_dir or not global_dir.exists():
            log.warning(f"Global directory does not exist: {global_dir}")
            return None

        # 新規セッション作成
        session_id, workspace = session_manager.create_session(
            user_info={'migrated_from': str(global_dir)}
        )

        # データコピー
        import shutil
        for item in global_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, workspace)
            elif item.is_dir() and item.name in ['intermediate', 'output', 'cache']:
                target_dir = workspace / item.name
                if item.exists():
                    shutil.copytree(item, target_dir, dirs_exist_ok=True)

        log.info(f"Migrated from {global_dir} to session {session_id[:8]}...")

        # グローバル変数を更新（後方互換性）
        global CURRENT_SCENARIO_DIR
        CURRENT_SCENARIO_DIR = workspace

        return session_id

    def inject_session_store(self, layout: Any) -> Any:
        """
        既存のレイアウトにセッションストアを注入

        Args:
            layout: Dashレイアウト

        Returns:
            セッションストアが追加されたレイアウト
        """
        if not DASH_AVAILABLE:
            return layout

        # セッションストアコンポーネント
        session_stores = [
            dcc.Store(id='session-id-store', storage_type='session'),
            dcc.Store(id='session-workspace-store', storage_type='session'),
            dcc.Store(id='session-metadata-store', storage_type='session'),
        ]

        # レイアウトがhtml.Divの場合
        if hasattr(layout, '__class__') and layout.__class__.__name__ == 'Div':
            if hasattr(layout, 'children'):
                if isinstance(layout.children, list):
                    # リストの最初に追加
                    layout.children = session_stores + layout.children
                else:
                    # 単一要素の場合はリスト化
                    layout.children = session_stores + [layout.children]

        return layout


# グローバルインスタンス
session_integration = SessionIntegration()


# 既存のdata_get関数を置き換える新しい実装
def session_aware_data_get(key: str, default=None, for_display: bool = False,
                          session_id: Optional[str] = None,
                          use_global_fallback: bool = True):
    """
    セッション対応版のdata_get関数

    Args:
        key: データキー
        default: デフォルト値
        for_display: 表示用フラグ
        session_id: セッションID（省略時は自動取得）
        use_global_fallback: グローバル変数へのフォールバック

    Returns:
        要求されたデータ
    """
    # セッションIDを取得
    if session_id is None:
        session_id = session_integration.get_session_id()

    # ワークスペースを取得
    workspace = session_integration.get_workspace_path(session_id)

    # 検索ディレクトリ
    search_dirs = [workspace / 'intermediate', workspace]

    # グローバルフォールバック（後方互換性）
    if use_global_fallback and CURRENT_SCENARIO_DIR:
        search_dirs.append(CURRENT_SCENARIO_DIR)
        search_dirs.append(CURRENT_SCENARIO_DIR / 'intermediate')

    # ファイル名パターン
    file_patterns = {
        "intermediate_data": ["intermediate_data.parquet", "intermediate_data.csv"],
        "shortage_data": ["shortage_analysis.parquet", "shortage_analysis.csv"],
        "cost_data": ["cost_analysis.parquet", "cost_analysis.csv"],
        "fatigue_data": ["fatigue_analysis.parquet", "fatigue_analysis.csv"],
        # 他のパターンを追加
    }

    # デフォルトパターン
    patterns = file_patterns.get(key, [f"{key}.parquet", f"{key}.csv", f"{key}.xlsx"])

    # ファイル検索
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for pattern in patterns:
            file_path = search_dir / pattern

            if file_path.exists():
                try:
                    # ファイル読み込み
                    if file_path.suffix == '.parquet':
                        return pd.read_parquet(file_path)
                    elif file_path.suffix == '.csv':
                        return pd.read_csv(file_path)
                    elif file_path.suffix == '.xlsx':
                        return pd.read_excel(file_path)

                except Exception as e:
                    log.error(f"Failed to load {file_path}: {e}")
                    continue

    # デフォルト値を返す
    if default is not None:
        return default

    # 空のDataFrameを返す
    return pd.DataFrame()


def session_aware_save_data(data: Any, key: str,
                           session_id: Optional[str] = None,
                           format: str = 'parquet'):
    """
    セッション対応版のデータ保存関数

    Args:
        data: 保存するデータ
        key: データキー
        session_id: セッションID（省略時は自動取得）
        format: 保存形式（parquet/csv/xlsx）
    """
    # セッションIDを取得
    if session_id is None:
        session_id = session_integration.get_session_id()

    # ワークスペースを取得
    workspace = session_integration.get_workspace_path(session_id)

    # 保存先ディレクトリ
    save_dir = workspace / 'intermediate'
    save_dir.mkdir(exist_ok=True)

    # ファイルパス
    if format == 'parquet':
        file_path = save_dir / f"{key}.parquet"
        if isinstance(data, pd.DataFrame):
            data.to_parquet(file_path)
    elif format == 'csv':
        file_path = save_dir / f"{key}.csv"
        if isinstance(data, pd.DataFrame):
            data.to_csv(file_path, index=False)
    elif format == 'xlsx':
        file_path = save_dir / f"{key}.xlsx"
        if isinstance(data, pd.DataFrame):
            data.to_excel(file_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

    log.info(f"Saved {key} to {file_path}")


def add_session_to_callback(callback_func: Callable) -> Callable:
    """
    既存のコールバック関数にセッションサポートを追加するデコレータ

    Args:
        callback_func: 元のコールバック関数

    Returns:
        セッション対応版のコールバック関数
    """
    @wraps(callback_func)
    def wrapper(*args, **kwargs):
        # セッションIDを取得
        session_id = session_integration.get_session_id()

        # kwargsにセッション情報を追加
        kwargs['session_id'] = session_id
        kwargs['workspace'] = session_integration.get_workspace_path(session_id)

        # 元の関数を実行
        return callback_func(*args, **kwargs)

    return wrapper


def make_callback_session_aware(app: Any, callback_id: str,
                               outputs: list, inputs: list, states: list = None):
    """
    既存のコールバックをセッション対応にする

    Args:
        app: Dashアプリケーションインスタンス
        callback_id: コールバックID
        outputs: Output定義
        inputs: Input定義
        states: State定義（オプション）

    Returns:
        セッション対応コールバックデコレータ
    """
    if not DASH_AVAILABLE:
        return lambda f: f

    # Stateリストにセッションストアを追加
    if states is None:
        states = []

    # セッションストアをStateに追加
    from dash import State
    states.append(State('session-id-store', 'data'))

    def decorator(func):
        # セッション対応ラッパー
        @wraps(func)
        def wrapper(*args):
            # 最後の引数がセッションID
            session_id = args[-1] if args else None

            # セッションIDが無効な場合は新規作成
            if not session_id:
                session_id = session_integration.get_session_id()

            # ワークスペースを取得
            workspace = session_integration.get_workspace_path(session_id)

            # 元の関数にセッション情報を渡す
            # 新しい引数リストを作成（セッションIDを除く）
            new_args = args[:-1] if args else []

            # 関数を実行
            return func(*new_args, session_id=session_id, workspace=workspace)

        # コールバックを登録
        app.callback(outputs, inputs, states)(wrapper)

        return wrapper

    return decorator


# 移行用ヘルパー関数
def initialize_session_support(app: Any, auto_migrate: bool = True) -> bool:
    """
    既存のDashアプリにセッションサポートを初期化

    Args:
        app: Dashアプリケーションインスタンス
        auto_migrate: 既存データの自動移行

    Returns:
        初期化成功の場合True
    """
    if not DASH_AVAILABLE:
        log.error("Dash is not available")
        return False

    # レイアウトにセッションストアを注入
    if hasattr(app, 'layout'):
        app.layout = session_integration.inject_session_store(app.layout)

    # 自動移行
    if auto_migrate and CURRENT_SCENARIO_DIR and CURRENT_SCENARIO_DIR.exists():
        session_id = session_integration.migrate_from_global_dir(CURRENT_SCENARIO_DIR)
        log.info(f"Auto-migrated to session {session_id[:8]}...")

    # セッション初期化コールバックを追加
    from dash import Input, Output

    @app.callback(
        Output('session-id-store', 'data'),
        Input('session-id-store', 'data')
    )
    def initialize_session(existing_session_id):
        """セッション初期化コールバック"""
        if existing_session_id:
            return existing_session_id

        # 新規セッション作成
        new_session_id = session_integration.get_session_id()
        log.info(f"Initialized new session: {new_session_id[:8]}...")
        return new_session_id

    log.info("Session support initialized successfully")
    return True


# 後方互換性のためのエイリアス
def get_current_scenario_dir(session_id: Optional[str] = None) -> Optional[Path]:
    """
    CURRENT_SCENARIO_DIR互換の関数

    Args:
        session_id: セッションID（省略時は自動取得）

    Returns:
        シナリオディレクトリパス
    """
    if session_id is None and CURRENT_SCENARIO_DIR:
        # 後方互換モード
        return CURRENT_SCENARIO_DIR

    return session_integration.get_workspace_path(session_id)


if __name__ == "__main__":
    # テスト
    print("Testing Session Integration...")

    # セッションID取得テスト
    sid = session_integration.get_session_id()
    print(f"Session ID: {sid[:8]}...")

    # ワークスペース取得テスト
    workspace = session_integration.get_workspace_path()
    print(f"Workspace: {workspace}")

    # データ保存テスト
    test_df = pd.DataFrame({'test': [1, 2, 3]})
    session_aware_save_data(test_df, 'test_data')
    print("Data saved")

    # データ読み込みテスト
    loaded_df = session_aware_data_get('test_data')
    print(f"Data loaded: {loaded_df.shape}")

    print("Test completed!")