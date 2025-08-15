
# キャッシュ最適化モジュール
import pickle
import hashlib
from pathlib import Path
from functools import wraps
import time

class SmartCache:
    """スマートキャッシュシステム"""
    
    def __init__(self, cache_dir="cache/smart", ttl=3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl  # Time to live (秒)
    
    def cache_key(self, *args, **kwargs):
        """キャッシュキー生成"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def cached_function(self, ttl=None):
        """関数キャッシュデコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # キャッシュキー生成
                cache_key = self.cache_key(func.__name__, *args, **kwargs)
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                
                # キャッシュ有効性チェック
                if cache_file.exists():
                    cache_age = time.time() - cache_file.stat().st_mtime
                    if cache_age < (ttl or self.ttl):
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                
                # 関数実行
                result = func(*args, **kwargs)
                
                # 結果をキャッシュ
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                
                return result
            return wrapper
        return decorator
    
    def invalidate_cache(self, pattern="*"):
        """キャッシュ無効化"""
        for cache_file in self.cache_dir.glob(f"{pattern}.pkl"):
            cache_file.unlink()

# 計算結果キャッシュシステム
calculation_cache = SmartCache(cache_dir="cache/calculations")

@calculation_cache.cached_function(ttl=1800)  # 30分間キャッシュ
def cached_slot_hours_calculation(data_hash, slot_counts):
    """SLOT_HOURS計算結果のキャッシュ"""
    return slot_counts * 0.5

@calculation_cache.cached_function(ttl=3600)  # 1時間キャッシュ
def cached_aggregation(data_hash, group_columns, values):
    """集計結果のキャッシュ"""
    # 実際の集計処理
    return {"total": sum(values), "count": len(values)}

def clear_calculation_cache():
    """計算キャッシュクリア"""
    calculation_cache.invalidate_cache()
