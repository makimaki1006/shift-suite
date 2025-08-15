# dash_app.py の安定性向上パッチ
import time
import weakref
import psutil
import os
from functools import lru_cache, wraps
from typing import Dict, List, Tuple, Optional, Any
from collections import OrderedDict
import threading
import gc
import logging

log = logging.getLogger(__name__)

# === リソース監視機能 ===
def get_memory_usage() -> Dict[str, float]:
    """現在のメモリ使用量を取得"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 実際のメモリ使用量
            "vms_mb": memory_info.vms / 1024 / 1024,  # 仮想メモリ使用量
            "percent": process.memory_percent(),       # システム全体に対する割合
        }
    except Exception as e:
        log.warning(f"Memory usage monitoring failed: {e}")
        return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

def check_memory_pressure() -> bool:
    """メモリプレッシャーをチェック"""
    memory_info = get_memory_usage()
    # メモリ使用率80%以上で警告
    return memory_info["percent"] > 80

def emergency_cleanup():
    """緊急メモリクリーンアップ"""
    log.warning("緊急メモリクリーンアップを実行します")
    
    # キャッシュをクリア
    # DATA_CACHE.clear()  # これは元のコードで実装
    # safe_read_parquet.cache_clear()
    # safe_read_csv.cache_clear()
    
    # 強制ガベージコレクション
    gc.collect()
    
    memory_after = get_memory_usage()
    log.info(f"クリーンアップ後メモリ使用量: {memory_after['rss_mb']:.1f}MB ({memory_after['percent']:.1f}%)")

# === スレッドセーフなLRUキャッシュの実装 ===
class ThreadSafeLRUCache:
    """スレッドセーフなLRUキャッシュ実装"""
    def __init__(self, maxsize: int = 50):
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0
        
    def get(self, key: str, default=None):
        with self._lock:
            if key in self._cache:
                # LRU: 最近使用したものを末尾に移動
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return default
            
    def set(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._cache[key] = value
            # サイズ制限を超えたら最も古いものを削除
            if len(self._cache) > self._maxsize:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                log.debug(f"Cache evicted: {oldest_key}")
                
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            
    def get_stats(self):
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate
            }
            
    def __contains__(self, key):
        with self._lock:
            return key in self._cache
            
    def keys(self):
        with self._lock:
            return list(self._cache.keys())

# === 改善されたsafe_callback関数 ===
def safe_callback_enhanced(func):
    """Wrap Dash callbacks with enhanced error handling and resource monitoring."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        memory_start = get_memory_usage()
        
        try:
            # メモリプレッシャーチェック
            if check_memory_pressure():
                log.warning(f"High memory usage detected before {func.__name__}: {memory_start['percent']:.1f}%")
                emergency_cleanup()
            
            # ガベージコレクションのプロアクティブな実行
            if gc.get_count()[0] > 700:
                gc.collect()
                
            # 実際のコールバック実行
            result = func(*args, **kwargs)
            
            # パフォーマンスログ
            execution_time = time.time() - start_time
            memory_end = get_memory_usage()
            memory_delta = memory_end['rss_mb'] - memory_start['rss_mb']
            
            if execution_time > 5:  # 5秒以上の処理を警告
                log.warning(f"Slow callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
            elif execution_time > 1:  # 1秒以上を情報ログ
                log.info(f"Callback {func.__name__}: {execution_time:.2f}s, memory delta: {memory_delta:+.1f}MB")
                
            return result
            
        except Exception as e:
            # PreventUpdateは正常なフローなので再発生
            if e.__class__.__name__ == 'PreventUpdate':
                raise
                
            log.exception(f"予期しないエラー in {func.__name__}")
            
            # エラー時のメモリクリーンアップ
            if check_memory_pressure():
                emergency_cleanup()
                
            # エラー詳細を含むHTML要素を返す
            from dash import html
            return html.Div([
                html.H4(f"エラーが発生しました ({func.__name__})", style={'color': 'red'}),
                html.Details([
                    html.Summary("エラー詳細を表示"),
                    html.Pre(str(e), style={'background': '#f0f0f0', 'padding': '10px', 'overflow': 'auto'})
                ]),
                html.P("問題が続く場合はブラウザを更新してください。")
            ])
    return wrapper

# === メモリ効率的なファイル読み込み関数 ===
@lru_cache(maxsize=16)  # キャッシュサイズを増加
def safe_read_parquet_enhanced(filepath: str, columns: Optional[str] = None, optimize_memory: bool = True):
    """Parquetファイルを安全に読み込み結果をキャッシュ（メモリ最適化版）"""
    import pandas as pd
    from pathlib import Path
    
    try:
        filepath_obj = Path(filepath)
        if not filepath_obj.exists():
            log.debug(f"File does not exist: {filepath}")
            return pd.DataFrame()
        
        # メモリ効率のための読み込みオプション
        read_kwargs = {}
        if columns:
            read_kwargs['columns'] = columns.split(',') if isinstance(columns, str) else columns
            
        df = pd.read_parquet(filepath_obj, **read_kwargs)
        
        # メモリ最適化
        if optimize_memory and not df.empty:
            original_size = df.memory_usage(deep=True).sum() / 1024 / 1024
            
            # 数値カラムのダウンキャスト
            for col in df.select_dtypes(include=['float64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='float')
            for col in df.select_dtypes(include=['int64']).columns:
                df[col] = pd.to_numeric(df[col], downcast='integer')
                
            new_size = df.memory_usage(deep=True).sum() / 1024 / 1024
            if new_size < original_size * 0.9:  # 10%以上のメモリ節約
                log.debug(f"Memory optimized {filepath_obj.name}: {original_size:.1f}MB → {new_size:.1f}MB")
        
        log.debug(f"Loaded parquet {filepath_obj.name}: {df.shape}")
        return df
    except Exception as e:
        log.error(f"Error reading parquet {filepath}: {e}")
        return pd.DataFrame()