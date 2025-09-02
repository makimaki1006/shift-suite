#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
メモリガード実装 - Phase 1 即座対応
メモリリークを防ぎ、アプリケーションの安定性を保証
"""

import gc
import logging
import os
import sys
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import weakref

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Memory monitoring limited.")

log = logging.getLogger(__name__)

class MemoryGuard:
    """メモリ使用量を監視・制御するガードシステム"""
    
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
        
        # 監視スレッド
        self.monitoring = False
        self.monitor_thread = None
        
        log.info(f"MemoryGuard initialized: max={max_memory_mb}MB, warning={warning_threshold*100}%")
    
    def start_monitoring(self):
        """メモリ監視を開始"""
        if self.monitoring:
            log.warning("Memory monitoring already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        log.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """メモリ監視を停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        log.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                self.check_memory()
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
            return {
                'rss_mb': usage.ru_maxrss / 1024,  # Linux/macOSでは異なる単位
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0
            }
    
    def check_memory(self) -> bool:
        """
        メモリ使用量をチェック
        
        Returns:
            True if memory is within limits, False if cleanup was triggered
        """
        memory_info = self.get_memory_info()
        current_mb = memory_info['rss_mb']
        
        # 履歴に追加
        self.memory_history.append({
            'timestamp': datetime.now(),
            'memory_mb': current_mb,
            'percent': memory_info['percent']
        })
        
        # 履歴を最新100件に制限
        if len(self.memory_history) > 100:
            self.memory_history = self.memory_history[-100:]
        
        # 閾値チェック
        usage_ratio = current_mb / self.max_memory_mb
        
        if usage_ratio > 1.0:
            log.critical(f"Memory limit exceeded: {current_mb:.1f}MB / {self.max_memory_mb}MB")
            self.emergency_cleanup()
            return False
        elif usage_ratio > self.warning_threshold:
            log.warning(f"Memory usage high: {current_mb:.1f}MB / {self.max_memory_mb}MB ({usage_ratio*100:.1f}%)")
            self.gentle_cleanup()
            return False
        
        return True
    
    def register_cache(self, cache_object):
        """キャッシュオブジェクトを登録"""
        self.cache_refs.add(cache_object)
        log.debug(f"Cache registered: {type(cache_object).__name__}")
    
    def gentle_cleanup(self):
        """穏やかなメモリクリーンアップ"""
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
                            cache_ref.popitem()
        
        # 2. ガベージコレクション（第1世代まで）
        gc.collect(0)
        
        self.cleanup_count += 1
        self.last_cleanup = datetime.now()
        
        memory_after = self.get_memory_info()['rss_mb']
        log.info(f"Gentle cleanup completed. Memory: {memory_after:.1f}MB")
    
    def emergency_cleanup(self):
        """緊急メモリクリーンアップ"""
        log.warning("Starting emergency memory cleanup")
        
        # 1. 全キャッシュクリア
        for cache_ref in self.cache_refs:
            if hasattr(cache_ref, 'clear'):
                cache_ref.clear()
                log.debug(f"Cleared cache: {type(cache_ref).__name__}")
        
        # 2. グローバル変数のクリーンアップ
        self._clear_large_globals()
        
        # 3. 完全ガベージコレクション
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
        current = self.get_memory_info()
        
        # トレンド計算
        trend = "stable"
        if len(self.memory_history) >= 2:
            recent = self.memory_history[-5:]
            if len(recent) >= 2:
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
            'history_points': len(self.memory_history)
        }
    
    def create_memory_report(self) -> str:
        """メモリレポートを生成"""
        stats = self.get_memory_stats()
        
        report = f"""
=== Memory Guard Report ===
Current Usage: {stats['current_mb']:.1f}MB / {stats['max_mb']}MB ({stats['usage_percent']:.1f}%)
Available: {stats['available_mb']:.1f}MB
Trend: {stats['trend']}
Cleanups: {stats['cleanup_count']}
Last Cleanup: {stats['last_cleanup'] or 'Never'}
===========================
        """
        
        return report.strip()

# グローバルインスタンス
memory_guard = MemoryGuard()

# キャッシュデコレータ with メモリ管理
class ManagedCache:
    """メモリ管理機能付きキャッシュ"""
    
    def __init__(self, maxsize=128, ttl=3600):
        self.cache = {}
        self.timestamps = {}
        self.maxsize = maxsize
        self.ttl = ttl
        
        # メモリガードに登録
        memory_guard.register_cache(self)
    
    def get(self, key):
        """キャッシュから取得"""
        if key in self.cache:
            # TTLチェック
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                return self.cache[key]
            else:
                # 期限切れ
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key, value):
        """キャッシュに設定"""
        # サイズ制限チェック
        if len(self.cache) >= self.maxsize:
            # 最も古いアイテムを削除
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
    
    def clear(self):
        """キャッシュをクリア"""
        self.cache.clear()
        self.timestamps.clear()
    
    def clear_expired(self):
        """期限切れアイテムをクリア"""
        now = datetime.now()
        expired_keys = [
            k for k, t in self.timestamps.items()
            if now - t > timedelta(seconds=self.ttl)
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]
        
        return len(expired_keys)
    
    def __len__(self):
        return len(self.cache)
    
    def popitem(self):
        """最も古いアイテムを削除"""
        if self.timestamps:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            value = self.cache.pop(oldest_key)
            del self.timestamps[oldest_key]
            return oldest_key, value
        return None

# 便利な関数
def check_memory_usage():
    """現在のメモリ使用量を確認"""
    return memory_guard.get_memory_stats()

def force_cleanup():
    """手動でクリーンアップを実行"""
    memory_guard.emergency_cleanup()