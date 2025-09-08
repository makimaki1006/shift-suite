#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改善版メモリガード実装
メモリリークを防ぎ、アプリケーションの安定性を保証
"""

import gc
import logging
import os
import sys
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import weakref
from functools import wraps

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Memory monitoring limited.")

log = logging.getLogger(__name__)

class ImprovedMemoryGuard:
    """改善版メモリ使用量監視・制御システム"""
    
    def __init__(self, 
                 max_memory_mb: int = 1000,
                 warning_threshold: float = 0.8,
                 check_interval: int = 30):
        """
        メモリガードの初期化
        
        Args:
            max_memory_mb: 最大メモリ使用量（MB）
            warning_threshold: 警告閾値（0-1）
            check_interval: チェック間隔（秒）
        """
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = warning_threshold
        self.check_interval = check_interval
        
        # 監視情報
        self.memory_history = []
        self.cleanup_count = 0
        self.last_cleanup = None
        
        # キャッシュへの弱参照を保持
        self.cache_refs = weakref.WeakSet()
        
        # クリーンアップコールバック
        self._cleanup_callbacks = []
        
        # 監視スレッド
        self.monitoring = False
        self.monitor_thread = None
        
        # スレッドセーフティ用ロック
        self._lock = threading.RLock()
        
        log.info(f"ImprovedMemoryGuard initialized: max={max_memory_mb}MB, warning={warning_threshold*100}%")
    
    def register_cleanup(self, callback: Callable):
        """クリーンアップコールバック登録"""
        with self._lock:
            self._cleanup_callbacks.append(callback)
            log.debug(f"Cleanup callback registered: {callback.__name__}")
    
    def start_monitoring(self):
        """メモリ監視を開始"""
        with self._lock:
            if self.monitoring:
                log.warning("Memory monitoring already running")
                return
            
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            log.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """メモリ監視を停止"""
        with self._lock:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            log.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                self.check_and_cleanup()
                time.sleep(self.check_interval)
            except Exception as e:
                log.error(f"Error in memory monitor: {e}")
                time.sleep(self.check_interval)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """現在のメモリ情報を取得"""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        else:
            # フォールバック: 基本的な情報のみ
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            
            # プラットフォーム別の処理
            if sys.platform == 'darwin':  # macOS
                rss_mb = usage.ru_maxrss / 1024 / 1024
            else:  # Linux
                rss_mb = usage.ru_maxrss / 1024
                
            return {
                'rss_mb': rss_mb,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0
            }
    
    def get_memory_usage(self) -> float:
        """メモリ使用率を取得（0-1）"""
        memory_info = self.get_memory_info()
        current_mb = memory_info['rss_mb']
        return current_mb / self.max_memory_mb
    
    def check_and_cleanup(self) -> float:
        """メモリチェックと自動クリーンアップ
        
        Returns:
            現在のメモリ使用率（0-1）
        """
        with self._lock:
            usage = self.get_memory_usage()
            memory_info = self.get_memory_info()
            current_mb = memory_info['rss_mb']
            
            # 履歴に追加
            self.memory_history.append({
                'timestamp': datetime.now(),
                'memory_mb': current_mb,
                'percent': memory_info['percent'],
                'usage_ratio': usage
            })
            
            # 履歴を最新100件に制限
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-100:]
            
            if usage > self.warning_threshold:
                # 警告レベル: ガベージコレクション
                log.warning(f"Memory usage high: {current_mb:.1f}MB / {self.max_memory_mb}MB ({usage*100:.1f}%)")
                gc.collect()
                
            if usage > 0.9:
                # 危険レベル: 強制クリーンアップ
                log.critical(f"Memory critical: {current_mb:.1f}MB / {self.max_memory_mb}MB ({usage*100:.1f}%)")
                for callback in self._cleanup_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        log.error(f"Cleanup callback failed: {e}")
                gc.collect(2)  # 完全ガベージコレクション
                
                self.cleanup_count += 1
                self.last_cleanup = datetime.now()
                
            return usage
    
    def enforce_limit(self, func: Callable) -> Callable:
        """メモリ制限付き関数実行デコレータ"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.check_and_cleanup()
            
            # メモリ使用量が限界なら実行拒否
            if self.get_memory_usage() > 0.95:
                raise MemoryError(f"Memory limit exceeded: Cannot execute {func.__name__}")
                
            return func(*args, **kwargs)
        return wrapper
    
    def register_cache(self, cache_object):
        """キャッシュオブジェクトを登録"""
        with self._lock:
            self.cache_refs.add(cache_object)
            log.debug(f"Cache registered: {type(cache_object).__name__}")
    
    def gentle_cleanup(self):
        """穏やかなメモリクリーンアップ"""
        with self._lock:
            log.info("Starting gentle memory cleanup")
            
            # 1. 期限切れキャッシュのクリア
            for cache_ref in self.cache_refs:
                if hasattr(cache_ref, 'clear_expired'):
                    cache_ref.clear_expired()
                elif hasattr(cache_ref, 'clear') and hasattr(cache_ref, '__len__'):
                    # 半分だけクリア
                    if len(cache_ref) > 10:
                        items_to_remove = len(cache_ref) // 2
                        for _ in range(items_to_remove):
                            if hasattr(cache_ref, 'popitem'):
                                try:
                                    cache_ref.popitem()
                                except:
                                    break
            
            # 2. ガベージコレクション（第1世代まで）
            gc.collect(0)
            
            self.cleanup_count += 1
            self.last_cleanup = datetime.now()
            
            memory_after = self.get_memory_info()['rss_mb']
            log.info(f"Gentle cleanup completed. Memory: {memory_after:.1f}MB")
    
    def emergency_cleanup(self):
        """緊急メモリクリーンアップ"""
        with self._lock:
            log.warning("Starting emergency memory cleanup")
            
            # 1. 全キャッシュクリア
            for cache_ref in self.cache_refs:
                if hasattr(cache_ref, 'clear'):
                    try:
                        cache_ref.clear()
                        log.debug(f"Cleared cache: {type(cache_ref).__name__}")
                    except:
                        pass
            
            # 2. コールバック実行
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    log.error(f"Cleanup callback failed: {e}")
            
            # 3. グローバル変数のクリーンアップ
            self._clear_large_globals()
            
            # 4. 完全ガベージコレクション
            gc.collect()
            gc.collect()  # 2回実行で循環参照も解放
            
            self.cleanup_count += 1
            self.last_cleanup = datetime.now()
            
            memory_after = self.get_memory_info()['rss_mb']
            log.warning(f"Emergency cleanup completed. Memory: {memory_after:.1f}MB")
    
    def _clear_large_globals(self):
        """大きなグローバル変数をクリア"""
        import sys
        
        # 大きなオブジェクトを検出してクリア
        for name, obj in list(globals().items()):
            if name.startswith('_'):
                continue
            
            try:
                size = sys.getsizeof(obj)
                if size > 10 * 1024 * 1024:  # 10MB以上
                    if hasattr(obj, 'clear'):
                        obj.clear()
                        log.debug(f"Cleared large global: {name} ({size/1024/1024:.1f}MB)")
            except:
                pass
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """メモリ統計情報を取得"""
        with self._lock:
            current = self.get_memory_info()
            
            # トレンド計算
            trend = "stable"
            if len(self.memory_history) >= 5:
                recent = self.memory_history[-5:]
                diff = recent[-1]['memory_mb'] - recent[0]['memory_mb']
                if diff > 10:
                    trend = "increasing"
                elif diff < -10:
                    trend = "decreasing"
            
            return {
                'current_mb': current['rss_mb'],
                'max_mb': self.max_memory_mb,
                'usage_percent': (current['rss_mb'] / self.max_memory_mb) * 100,
                'available_mb': current['available_mb'],
                'cleanup_count': self.cleanup_count,
                'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
                'trend': trend,
                'history_points': len(self.memory_history),
                'warning_level': self.warning_threshold * 100,
                'critical_level': 90
            }
    
    def create_memory_report(self) -> str:
        """メモリレポートを生成"""
        stats = self.get_memory_stats()
        
        # ステータス判定
        if stats['usage_percent'] > stats['critical_level']:
            status = "🚨 CRITICAL"
        elif stats['usage_percent'] > stats['warning_level']:
            status = "⚠️ WARNING"
        else:
            status = "✅ OK"
        
        report = f"""
=== Memory Guard Report ===
Status: {status}
Current Usage: {stats['current_mb']:.1f}MB / {stats['max_mb']}MB ({stats['usage_percent']:.1f}%)
Available: {stats['available_mb']:.1f}MB
Trend: {stats['trend']}
Cleanups: {stats['cleanup_count']}
Last Cleanup: {stats['last_cleanup'] or 'Never'}

Thresholds:
- Warning: {stats['warning_level']:.0f}%
- Critical: {stats['critical_level']:.0f}%
===========================
        """
        
        return report.strip()


class ManagedCache:
    """メモリ管理機能付きキャッシュ"""
    
    def __init__(self, maxsize=128, ttl=3600, memory_guard=None):
        self.cache = {}
        self.timestamps = {}
        self.access_count = {}
        self.maxsize = maxsize
        self.ttl = ttl
        self._lock = threading.RLock()
        
        # メモリガードに登録
        if memory_guard:
            memory_guard.register_cache(self)
    
    def get(self, key):
        """キャッシュから取得"""
        with self._lock:
            if key in self.cache:
                # TTLチェック
                if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                    self.access_count[key] = self.access_count.get(key, 0) + 1
                    return self.cache[key]
                else:
                    # 期限切れ
                    del self.cache[key]
                    del self.timestamps[key]
                    if key in self.access_count:
                        del self.access_count[key]
            return None
    
    def set(self, key, value):
        """キャッシュに設定"""
        with self._lock:
            # サイズ制限チェック
            if len(self.cache) >= self.maxsize:
                # LRU: 最も使用頻度の低いアイテムを削除
                lru_key = min(self.access_count.items(), key=lambda x: x[1])[0] if self.access_count else min(self.timestamps, key=self.timestamps.get)
                del self.cache[lru_key]
                del self.timestamps[lru_key]
                if lru_key in self.access_count:
                    del self.access_count[lru_key]
            
            self.cache[key] = value
            self.timestamps[key] = datetime.now()
            self.access_count[key] = 0
    
    def clear(self):
        """キャッシュをクリア"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
            self.access_count.clear()
    
    def clear_expired(self):
        """期限切れアイテムをクリア"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                k for k, t in self.timestamps.items()
                if now - t > timedelta(seconds=self.ttl)
            ]
            
            for key in expired_keys:
                del self.cache[key]
                del self.timestamps[key]
                if key in self.access_count:
                    del self.access_count[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        with self._lock:
            total_size = sys.getsizeof(self.cache) if self.cache else 0
            
            return {
                'entries': len(self.cache),
                'max_entries': self.maxsize,
                'total_size_bytes': total_size,
                'ttl_seconds': self.ttl,
                'hit_rate': sum(self.access_count.values()) if self.access_count else 0
            }
    
    def __len__(self):
        return len(self.cache)
    
    def popitem(self):
        """最も古いアイテムを削除"""
        with self._lock:
            if self.timestamps:
                oldest_key = min(self.timestamps, key=self.timestamps.get)
                value = self.cache.pop(oldest_key)
                del self.timestamps[oldest_key]
                if oldest_key in self.access_count:
                    del self.access_count[oldest_key]
                return oldest_key, value
        return None


# グローバルインスタンス
memory_guard = ImprovedMemoryGuard(max_memory_mb=1000, warning_threshold=0.8)

# 便利な関数
def check_memory_usage():
    """現在のメモリ使用量を確認"""
    return memory_guard.get_memory_stats()

def force_cleanup():
    """手動でクリーンアップを実行"""
    memory_guard.emergency_cleanup()

def get_memory_report():
    """メモリレポートを取得"""
    return memory_guard.create_memory_report()

def with_memory_limit(max_mb: int = 1000):
    """メモリ制限付きデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            guard = ImprovedMemoryGuard(max_memory_mb=max_mb)
            return guard.enforce_limit(func)(*args, **kwargs)
        return wrapper
    return decorator