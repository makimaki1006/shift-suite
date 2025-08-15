# memory_manager.py - インテリジェントメモリ管理システム
"""
メモリリーク防止・効率的キャッシュ管理・ガベージコレクション最適化
大量データ処理時の安定性を確保
"""

import gc
import logging
import time
import threading
import weakref
from typing import Dict, Any, Optional, Callable, Set
from dataclasses import dataclass
from collections import OrderedDict
import pandas as pd
import numpy as np

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ログ設定
log = logging.getLogger(__name__)

@dataclass
class MemoryMetrics:
    """メモリ使用量メトリクス"""
    rss_mb: float          # 物理メモリ使用量
    vms_mb: float          # 仮想メモリ使用量
    percent: float         # システム全体に対する割合
    available_mb: float    # 利用可能メモリ
    cached_objects: int    # キャッシュされたオブジェクト数
    timestamp: float       # 計測時刻

class IntelligentMemoryManager:
    """インテリジェントメモリ管理システム"""
    
    def __init__(self, 
                 max_memory_percent: float = 70.0,
                 cleanup_threshold_percent: float = 80.0,
                 emergency_threshold_percent: float = 90.0,
                 monitoring_interval: int = 30):
        """
        Args:
            max_memory_percent: 通常時の最大メモリ使用率
            cleanup_threshold_percent: クリーンアップ開始しきい値
            emergency_threshold_percent: 緊急クリーンアップしきい値
            monitoring_interval: 監視間隔（秒）
        """
        self.max_memory_percent = max_memory_percent
        self.cleanup_threshold_percent = cleanup_threshold_percent
        self.emergency_threshold_percent = emergency_threshold_percent
        self.monitoring_interval = monitoring_interval
        
        # 内部状態
        self._cache_registry: Dict[str, weakref.ref] = {}
        self._cleanup_callbacks: Set[Callable] = set()
        self._metrics_history: list = []
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # キャッシュ統計
        self.cache_hits = 0
        self.cache_misses = 0
        self.cleanup_count = 0
        
    def get_memory_metrics(self) -> MemoryMetrics:
        """現在のメモリ使用量を取得"""
        if not PSUTIL_AVAILABLE:
            return MemoryMetrics(0, 0, 0, 0, len(self._cache_registry), time.time())
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            virtual_memory = psutil.virtual_memory()
            
            return MemoryMetrics(
                rss_mb=memory_info.rss / (1024 * 1024),
                vms_mb=memory_info.vms / (1024 * 1024),
                percent=process.memory_percent(),
                available_mb=virtual_memory.available / (1024 * 1024),
                cached_objects=len(self._cache_registry),
                timestamp=time.time()
            )
        except Exception as e:
            log.error(f"[メモリ管理] メトリクス取得エラー: {e}")
            return MemoryMetrics(0, 0, 0, 0, len(self._cache_registry), time.time())
    
    def register_cache_object(self, key: str, obj: Any) -> None:
        """キャッシュオブジェクトを登録"""
        with self._lock:
            # 弱参照で登録（オブジェクトが削除されると自動的にレジストリからも削除）
            try:
                self._cache_registry[key] = weakref.ref(obj, lambda ref: self._cleanup_key(key))
            except TypeError:
                # 弱参照できないオブジェクトの場合（intなど）
                pass
    
    def _cleanup_key(self, key: str) -> None:
        """キーのクリーンアップ"""
        with self._lock:
            self._cache_registry.pop(key, None)
    
    def add_cleanup_callback(self, callback: Callable) -> None:
        """クリーンアップコールバックを追加"""
        self._cleanup_callbacks.add(callback)
    
    def remove_cleanup_callback(self, callback: Callable) -> None:
        """クリーンアップコールバックを削除"""
        self._cleanup_callbacks.discard(callback)
    
    def check_memory_pressure(self) -> bool:
        """メモリ圧迫状況をチェック"""
        metrics = self.get_memory_metrics()
        return metrics.percent > self.cleanup_threshold_percent
    
    def perform_cleanup(self, force: bool = False) -> MemoryMetrics:
        """メモリクリーンアップを実行"""
        start_metrics = self.get_memory_metrics()
        
        if not force and start_metrics.percent < self.cleanup_threshold_percent:
            return start_metrics
        
        log.info(f"[メモリ管理] クリーンアップ開始: {start_metrics.percent:.1f}% 使用中")
        
        with self._lock:
            # Phase 1: 弱参照のクリーンアップ
            dead_keys = []
            for key, weak_ref in self._cache_registry.items():
                if weak_ref() is None:
                    dead_keys.append(key)
            
            for key in dead_keys:
                del self._cache_registry[key]
            
            # Phase 2: 登録されたクリーンアップコールバックを実行
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    log.error(f"[メモリ管理] クリーンアップコールバックエラー: {e}")
            
            # Phase 3: 強制ガベージコレクション
            collected = gc.collect()
            log.info(f"[メモリ管理] ガベージコレクション: {collected}個のオブジェクトを回収")
            
            self.cleanup_count += 1
        
        end_metrics = self.get_memory_metrics()
        saved_mb = start_metrics.rss_mb - end_metrics.rss_mb
        log.info(f"[メモリ管理] クリーンアップ完了: {saved_mb:.1f}MB節約、{end_metrics.percent:.1f}%使用中")
        
        return end_metrics
    
    def emergency_cleanup(self) -> MemoryMetrics:
        """緊急メモリクリーンアップ"""
        log.warning("[メモリ管理] 緊急クリーンアップを実行")
        
        # 段階的クリーンアップ
        metrics = self.perform_cleanup(force=True)
        
        if metrics.percent > self.emergency_threshold_percent:
            # さらなるクリーンアップが必要
            log.warning("[メモリ管理] 追加の緊急措置を実行")
            
            # DataFrameの最適化
            self._optimize_dataframes()
            
            # 強制的なガベージコレクション（複数回）
            for i in range(3):
                collected = gc.collect()
                log.info(f"[メモリ管理] 追加GC #{i+1}: {collected}個回収")
                time.sleep(0.1)  # 少し待機
            
            metrics = self.get_memory_metrics()
            log.info(f"[メモリ管理] 緊急クリーンアップ後: {metrics.percent:.1f}%使用中")
        
        return metrics
    
    def _optimize_dataframes(self) -> None:
        """DataFrameのメモリ最適化"""
        optimized_count = 0
        
        for key, weak_ref in list(self._cache_registry.items()):
            obj = weak_ref()
            if obj is not None and isinstance(obj, pd.DataFrame):
                try:
                    # データ型の最適化
                    for col in obj.select_dtypes(include=['int64']).columns:
                        if obj[col].min() >= 0 and obj[col].max() < 65536:
                            obj[col] = obj[col].astype('uint16')
                        elif obj[col].min() >= -32768 and obj[col].max() < 32768:
                            obj[col] = obj[col].astype('int16')
                    
                    for col in obj.select_dtypes(include=['float64']).columns:
                        obj[col] = obj[col].astype('float32')
                    
                    optimized_count += 1
                except Exception as e:
                    log.debug(f"[メモリ管理] DataFrame最適化失敗 {key}: {e}")
        
        if optimized_count > 0:
            log.info(f"[メモリ管理] {optimized_count}個のDataFrameを最適化")
    
    def start_monitoring(self) -> None:
        """バックグラウンドメモリ監視を開始"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        log.info("[メモリ管理] バックグラウンド監視開始")
    
    def stop_monitoring(self) -> None:
        """バックグラウンドメモリ監視を停止"""
        self._monitoring_active = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        log.info("[メモリ管理] バックグラウンド監視停止")
    
    def _monitor_loop(self) -> None:
        """監視ループ"""
        while self._monitoring_active:
            try:
                metrics = self.get_memory_metrics()
                self._metrics_history.append(metrics)
                
                # 履歴の制限（直近100回分のみ保持）
                if len(self._metrics_history) > 100:
                    self._metrics_history.pop(0)
                
                # メモリ圧迫チェック
                if metrics.percent > self.emergency_threshold_percent:
                    self.emergency_cleanup()
                elif metrics.percent > self.cleanup_threshold_percent:
                    self.perform_cleanup()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                log.error(f"[メモリ管理] 監視ループエラー: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        current_metrics = self.get_memory_metrics()
        
        # 履歴からトレンドを計算
        trend = "安定"
        if len(self._metrics_history) >= 2:
            recent_avg = sum(m.percent for m in self._metrics_history[-5:]) / min(5, len(self._metrics_history))
            older_avg = sum(m.percent for m in self._metrics_history[-10:-5]) / min(5, len(self._metrics_history) - 5)
            
            if recent_avg > older_avg + 5:
                trend = "増加"
            elif recent_avg < older_avg - 5:
                trend = "減少"
        
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) * 100 if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            'current_memory_percent': current_metrics.percent,
            'memory_rss_mb': current_metrics.rss_mb,
            'available_memory_mb': current_metrics.available_mb,
            'cached_objects': current_metrics.cached_objects,
            'memory_trend': trend,
            'cache_hit_rate': cache_hit_rate,
            'cleanup_count': self.cleanup_count,
            'monitoring_active': self._monitoring_active
        }

class SmartCacheManager:
    """スマートキャッシュ管理システム"""
    
    def __init__(self, max_size: int = 100, memory_manager: IntelligentMemoryManager = None):
        self.max_size = max_size
        self.memory_manager = memory_manager or IntelligentMemoryManager()
        self._cache: OrderedDict = OrderedDict()
        self._access_counts: Dict[str, int] = {}
        self._lock = threading.RLock()
        
        # メモリマネージャーにクリーンアップコールバックを登録
        self.memory_manager.add_cleanup_callback(self._emergency_cache_cleanup)
    
    def get(self, key: str, default: Any = None) -> Any:
        """キャッシュから値を取得"""
        with self._lock:
            if key in self._cache:
                # LRU: アクセスされたアイテムを末尾に移動
                value = self._cache.pop(key)
                self._cache[key] = value
                self._access_counts[key] = self._access_counts.get(key, 0) + 1
                self.memory_manager.cache_hits += 1
                return value
            else:
                self.memory_manager.cache_misses += 1
                return default
    
    def set(self, key: str, value: Any) -> None:
        """キャッシュに値を設定"""
        with self._lock:
            # 既存キーの更新
            if key in self._cache:
                self._cache.pop(key)
            
            # 新しい値を追加
            self._cache[key] = value
            self._access_counts[key] = 1
            
            # メモリマネージャーに登録
            self.memory_manager.register_cache_object(key, value)
            
            # サイズ制限チェック
            while len(self._cache) > self.max_size:
                self._evict_least_used()
    
    def _evict_least_used(self) -> None:
        """最も使用頻度の低いアイテムを削除"""
        if not self._cache:
            return
        
        # アクセス数が最も少ないキーを見つける
        min_access_key = min(self._access_counts.keys(), 
                           key=lambda k: self._access_counts.get(k, 0))
        
        # 削除
        self._cache.pop(min_access_key, None)
        self._access_counts.pop(min_access_key, None)
        
        log.debug(f"[スマートキャッシュ] LRU削除: {min_access_key}")
    
    def _emergency_cache_cleanup(self) -> None:
        """緊急時のキャッシュクリーンアップ"""
        with self._lock:
            # キャッシュサイズを半分に削減
            target_size = self.max_size // 2
            while len(self._cache) > target_size:
                self._evict_least_used()
            
            log.info(f"[スマートキャッシュ] 緊急クリーンアップ完了: {len(self._cache)}個保持")
    
    def clear(self) -> None:
        """キャッシュを全クリア"""
        with self._lock:
            self._cache.clear()
            self._access_counts.clear()
    
    def keys(self) -> list:
        """キャッシュキー一覧を取得"""
        with self._lock:
            return list(self._cache.keys())
    
    def get_cache_info(self) -> Dict[str, Any]:
        """キャッシュ情報を取得"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': self.memory_manager.cache_hits / (self.memory_manager.cache_hits + self.memory_manager.cache_misses) * 100 if (self.memory_manager.cache_hits + self.memory_manager.cache_misses) > 0 else 0,
                'most_accessed': max(self._access_counts.items(), key=lambda x: x[1]) if self._access_counts else None
            }

# グローバルインスタンス
memory_manager = IntelligentMemoryManager()
smart_cache = SmartCacheManager(memory_manager=memory_manager)

# 便利な関数
def start_memory_monitoring():
    """メモリ監視開始"""
    memory_manager.start_monitoring()

def stop_memory_monitoring():
    """メモリ監視停止"""
    memory_manager.stop_monitoring()

def get_memory_status():
    """メモリ状況取得"""
    return memory_manager.get_statistics()

def force_cleanup():
    """強制クリーンアップ"""
    return memory_manager.perform_cleanup(force=True)