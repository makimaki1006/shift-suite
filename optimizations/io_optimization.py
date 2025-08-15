
# I/O最適化モジュール - Excel読み込み高速化
import pandas as pd
from functools import lru_cache
import pickle
from pathlib import Path

class ExcelOptimizer:
    """Excel読み込み最適化クラス"""
    
    def __init__(self, cache_dir="cache/excel"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @lru_cache(maxsize=32)
    def load_excel_optimized(self, file_path: str, sheet_name: str = None):
        """キャッシュ機能付きExcel読み込み"""
        
        file_path = Path(file_path)
        cache_key = f"{file_path.stem}_{sheet_name or 'default'}.pkl"
        cache_file = self.cache_dir / cache_key
        
        # ファイル変更チェック
        if cache_file.exists():
            cache_mtime = cache_file.stat().st_mtime
            file_mtime = file_path.stat().st_mtime
            
            if cache_mtime > file_mtime:
                # キャッシュの方が新しい
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        # 新規読み込み（最適化パラメータ付き）
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine='openpyxl',  # 高速エンジン
            na_filter=False,    # NA変換無効化で高速化
            keep_default_na=False
        )
        
        # キャッシュ保存
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
        
        return df
    
    def clear_cache(self):
        """キャッシュクリア"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

# 使用例
excel_optimizer = ExcelOptimizer()

def load_excel_fast(file_path, sheet_name=None):
    """高速Excel読み込み関数"""
    return excel_optimizer.load_excel_optimized(str(file_path), sheet_name)
