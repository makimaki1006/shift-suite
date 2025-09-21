#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SessionAwareDataManager - セッション対応データ管理システム
Phase 1: データ抽象化基盤の実装

目的: DATA_CACHEをセッション対応にし、会社間のデータ分離を実現
"""

import logging
import time
import threading
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json

# 既存のキャッシュマネージャーをインポート（存在する場合）
try:
    from improved_memory_guard import ImprovedUnifiedCacheManager
    EXISTING_CACHE_AVAILABLE = True
except ImportError:
    EXISTING_CACHE_AVAILABLE = False

log = logging.getLogger(__name__)


class SessionContext:
    """セッションコンテキスト管理"""

    def __init__(self, session_id: str = None, company_id: str = None, user_id: str = None):
        self.session_id = session_id
        self.company_id = company_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

    def update_access(self):
        """最終アクセス時刻を更新"""
        self.last_accessed = datetime.now()

    def to_key(self) -> str:
        """セッションコンテキストをキー文字列に変換"""
        if not self.session_id:
            return "global"
        return f"{self.company_id or 'no_company'}:{self.user_id or 'no_user'}:{self.session_id}"


class SessionAwareDataManager:
    """
    セッション対応データマネージャー
    会社とユーザーごとにデータを完全分離
    """

    def __init__(self, max_sessions: int = 100, ttl_seconds: int = 3600):
        """
        初期化

        Args:
            max_sessions: 最大セッション数
            ttl_seconds: セッションの有効期限（秒）
        """
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds

        # セッション別データストア
        self._session_stores: Dict[str, Dict[str, Any]] = {}

        # セッションコンテキスト管理
        self._contexts: Dict[str, SessionContext] = OrderedDict()

        # 既存のキャッシュマネージャー（後方互換性）
        if EXISTING_CACHE_AVAILABLE:
            self.existing_manager = ImprovedUnifiedCacheManager()
            log.info("既存のImprovedUnifiedCacheManagerを使用")
        else:
            self.existing_manager = None
            log.info("新規SessionAwareDataManagerとして動作")

        # スレッドセーフティ
        self._lock = threading.RLock()

        # 統計情報
        self._stats = {
            'get_calls': 0,
            'set_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'session_creates': 0,
            'session_expires': 0
        }

        log.info(f"SessionAwareDataManager initialized: max_sessions={max_sessions}, ttl={ttl_seconds}s")

    def _get_or_create_session_store(self, context_key: str) -> Dict[str, Any]:
        """セッションストアを取得または作成"""
        with self._lock:
            if context_key not in self._session_stores:
                # 最大セッション数チェック
                if len(self._session_stores) >= self.max_sessions:
                    self._expire_oldest_session()

                self._session_stores[context_key] = {}
                self._stats['session_creates'] += 1
                log.debug(f"New session store created: {context_key}")

            return self._session_stores[context_key]

    def _expire_oldest_session(self):
        """最も古いセッションを削除"""
        with self._lock:
            if not self._contexts:
                return

            # 最も古いセッションを特定
            oldest_key = next(iter(self._contexts))

            # セッションデータを削除
            if oldest_key in self._session_stores:
                del self._session_stores[oldest_key]
            if oldest_key in self._contexts:
                del self._contexts[oldest_key]

            self._stats['session_expires'] += 1
            log.info(f"Expired session: {oldest_key}")

    def get_data(self, key: str, session_id: str = None,
                 company_id: str = None, user_id: str = None) -> Optional[Any]:
        """
        セッション対応のデータ取得

        Args:
            key: データキー
            session_id: セッションID
            company_id: 会社ID
            user_id: ユーザーID

        Returns:
            取得したデータ（存在しない場合はNone）
        """
        self._stats['get_calls'] += 1

        # セッションコンテキストなしの場合（後方互換性）
        if not session_id:
            if self.existing_manager:
                return self.existing_manager.data_cache.get(key)
            return None

        # セッションコンテキストを作成
        context = SessionContext(session_id, company_id, user_id)
        context_key = context.to_key()

        with self._lock:
            # セッションストアから取得
            session_store = self._session_stores.get(context_key, {})

            if key in session_store:
                self._stats['cache_hits'] += 1
                # コンテキストの最終アクセス時刻を更新
                if context_key in self._contexts:
                    self._contexts[context_key].update_access()

                log.debug(f"Cache hit: {context_key}:{key}")
                return session_store[key]

            self._stats['cache_misses'] += 1
            log.debug(f"Cache miss: {context_key}:{key}")
            return None

    def set_data(self, key: str, value: Any, session_id: str = None,
                 company_id: str = None, user_id: str = None) -> None:
        """
        セッション対応のデータ設定

        Args:
            key: データキー
            value: 設定する値
            session_id: セッションID
            company_id: 会社ID
            user_id: ユーザーID
        """
        self._stats['set_calls'] += 1

        # セッションコンテキストなしの場合（後方互換性）
        if not session_id:
            if self.existing_manager:
                self.existing_manager.data_cache[key] = value
            return

        # セッションコンテキストを作成
        context = SessionContext(session_id, company_id, user_id)
        context_key = context.to_key()

        with self._lock:
            # セッションストアを取得または作成
            session_store = self._get_or_create_session_store(context_key)

            # データを設定
            session_store[key] = value

            # コンテキストを更新
            self._contexts[context_key] = context

            log.debug(f"Data set: {context_key}:{key}")

    def clear_session(self, session_id: str, company_id: str = None, user_id: str = None):
        """特定セッションのデータをクリア"""
        context = SessionContext(session_id, company_id, user_id)
        context_key = context.to_key()

        with self._lock:
            if context_key in self._session_stores:
                del self._session_stores[context_key]
            if context_key in self._contexts:
                del self._contexts[context_key]

            log.info(f"Session cleared: {context_key}")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            return {
                **self._stats,
                'active_sessions': len(self._session_stores),
                'total_keys': sum(len(store) for store in self._session_stores.values())
            }

    def cleanup_expired_sessions(self):
        """期限切れセッションのクリーンアップ"""
        with self._lock:
            now = datetime.now()
            expired_keys = []

            for context_key, context in self._contexts.items():
                if (now - context.last_accessed).total_seconds() > self.ttl_seconds:
                    expired_keys.append(context_key)

            for key in expired_keys:
                if key in self._session_stores:
                    del self._session_stores[key]
                if key in self._contexts:
                    del self._contexts[key]
                self._stats['session_expires'] += 1

            if expired_keys:
                log.info(f"Cleaned up {len(expired_keys)} expired sessions")


class DataCacheWrapper:
    """
    既存のDATA_CACHE呼び出しをラップ
    段階的移行のための互換性レイヤー
    """

    def __init__(self, manager: SessionAwareDataManager):
        self.manager = manager
        self._session_context: Optional[SessionContext] = None

    def set_session_context(self, session_id: str = None,
                           company_id: str = None, user_id: str = None):
        """セッションコンテキストを設定"""
        self._session_context = SessionContext(session_id, company_id, user_id) if session_id else None

    def get(self, key: str, default=None) -> Any:
        """辞書のget()メソッド互換"""
        if self._session_context:
            value = self.manager.get_data(
                key,
                session_id=self._session_context.session_id,
                company_id=self._session_context.company_id,
                user_id=self._session_context.user_id
            )
        else:
            value = self.manager.get_data(key)

        return value if value is not None else default

    def __getitem__(self, key: str) -> Any:
        """辞書のインデックスアクセス互換"""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any):
        """辞書の代入操作互換"""
        if self._session_context:
            self.manager.set_data(
                key, value,
                session_id=self._session_context.session_id,
                company_id=self._session_context.company_id,
                user_id=self._session_context.user_id
            )
        else:
            self.manager.set_data(key, value)

    def __contains__(self, key: str) -> bool:
        """in演算子のサポート"""
        return self.get(key) is not None

    def clear(self):
        """clear()メソッド互換"""
        if self._session_context:
            self.manager.clear_session(
                session_id=self._session_context.session_id,
                company_id=self._session_context.company_id,
                user_id=self._session_context.user_id
            )

    def keys(self):
        """keys()メソッド互換（部分実装）"""
        if self._session_context:
            context_key = self._session_context.to_key()
            with self.manager._lock:
                store = self.manager._session_stores.get(context_key, {})
                return store.keys()
        return []

    def values(self):
        """values()メソッド互換（部分実装）"""
        if self._session_context:
            context_key = self._session_context.to_key()
            with self.manager._lock:
                store = self.manager._session_stores.get(context_key, {})
                return store.values()
        return []

    def items(self):
        """items()メソッド互換（部分実装）"""
        if self._session_context:
            context_key = self._session_context.to_key()
            with self.manager._lock:
                store = self.manager._session_stores.get(context_key, {})
                return store.items()
        return []


# テスト用のコード
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(level=logging.DEBUG,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # マネージャーの作成
    manager = SessionAwareDataManager()

    # テスト1: セッション分離の確認
    print("\n=== セッション分離テスト ===")

    # Company A, User 1のデータ
    manager.set_data('test_key', 'value_company_a_user1',
                    session_id='sess1', company_id='compA', user_id='user1')

    # Company B, User 2のデータ
    manager.set_data('test_key', 'value_company_b_user2',
                    session_id='sess2', company_id='compB', user_id='user2')

    # データが混在しないことを確認
    val1 = manager.get_data('test_key', 'sess1', 'compA', 'user1')
    val2 = manager.get_data('test_key', 'sess2', 'compB', 'user2')

    print(f"Company A, User 1: {val1}")
    print(f"Company B, User 2: {val2}")
    assert val1 == 'value_company_a_user1', "Company Aのデータが正しくない"
    assert val2 == 'value_company_b_user2', "Company Bのデータが正しくない"

    # テスト2: ラッパーの動作確認
    print("\n=== ラッパー動作テスト ===")

    wrapper = DataCacheWrapper(manager)

    # セッションなし（グローバル）
    wrapper['global_key'] = 'global_value'
    print(f"Global: {wrapper.get('global_key')}")

    # セッションあり
    wrapper.set_session_context('sess3', 'compC', 'user3')
    wrapper['session_key'] = 'session_value'
    print(f"Session: {wrapper.get('session_key')}")

    # 統計情報
    print("\n=== 統計情報 ===")
    print(json.dumps(manager.get_stats(), indent=2))

    print("\n✅ 全テスト合格！SessionAwareDataManagerが正常に動作しています。")