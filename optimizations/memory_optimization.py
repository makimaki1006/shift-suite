
# メモリ最適化モジュール
import pandas as pd
import gc
from contextlib import contextmanager

class MemoryOptimizer:
    """メモリ使用量最適化クラス"""
    
    @staticmethod
    def optimize_dataframe_memory(df):
        """DataFrameメモリ使用量最適化"""
        
        df_optimized = df.copy()
        
        for col in df_optimized.columns:
            col_type = df_optimized[col].dtype
            
            if col_type != 'object':
                # 数値型の最適化
                c_min = df_optimized[col].min()
                c_max = df_optimized[col].max()
                
                if str(col_type)[:3] == 'int':
                    # 整数型の最適化
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df_optimized[col] = df_optimized[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df_optimized[col] = df_optimized[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df_optimized[col] = df_optimized[col].astype(np.int32)
                
                elif str(col_type)[:5] == 'float':
                    # 浮動小数点型の最適化
                    if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df_optimized[col] = df_optimized[col].astype(np.float32)
            else:
                # 文字列型の最適化
                num_unique_values = len(df_optimized[col].unique())
                num_total_values = len(df_optimized[col])
                
                if num_unique_values / num_total_values < 0.5:
                    df_optimized[col] = df_optimized[col].astype('category')
        
        return df_optimized
    
    @staticmethod
    @contextmanager
    def memory_manager():
        """メモリ管理コンテキストマネージャー"""
        try:
            yield
        finally:
            gc.collect()
    
    @staticmethod
    def chunked_processing(df, chunk_size=1000, process_func=None):
        """チャンク単位での処理（メモリ効率向上）"""
        
        results = []
        
        for start_idx in range(0, len(df), chunk_size):
            end_idx = min(start_idx + chunk_size, len(df))
            chunk = df.iloc[start_idx:end_idx]
            
            if process_func:
                chunk_result = process_func(chunk)
                results.append(chunk_result)
            
            # メモリクリア
            del chunk
            gc.collect()
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# 使用例
memory_optimizer = MemoryOptimizer()

def process_large_dataset(df):
    """大規模データセットの効率的処理"""
    with memory_optimizer.memory_manager():
        df_optimized = memory_optimizer.optimize_dataframe_memory(df)
        return df_optimized
