
# CPU最適化モジュール - SLOT_HOURS計算高速化
import numpy as np
import pandas as pd
from numba import jit, prange
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

class SlotHoursOptimizer:
    """SLOT_HOURS計算最適化クラス"""
    
    def __init__(self):
        self.SLOT_HOURS = 0.5
        self.cpu_count = mp.cpu_count()
    
    @jit(nopython=True)
    def vectorized_slot_calculation(self, slot_counts):
        """ベクトル化されたSLOT_HOURS計算"""
        return slot_counts * 0.5
    
    def parallel_slot_calculation(self, df, column_name='parsed_slots_count'):
        """並列化されたSLOT_HOURS計算"""
        
        # データを分割
        chunk_size = len(df) // self.cpu_count
        chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
        
        with ProcessPoolExecutor(max_workers=self.cpu_count) as executor:
            results = list(executor.map(self._calculate_chunk_hours, chunks))
        
        # 結果を結合
        return pd.concat(results, ignore_index=True)
    
    def _calculate_chunk_hours(self, chunk_df):
        """チャンク単位の計算"""
        chunk_df = chunk_df.copy()
        chunk_df['hours'] = chunk_df['parsed_slots_count'] * self.SLOT_HOURS
        return chunk_df
    
    def optimized_aggregation(self, df, group_columns, value_column='parsed_slots_count'):
        """最適化された集計処理"""
        
        # NumPyベースの高速集計
        if len(df) > 10000:  # 大きなデータセットの場合
            return self._numpy_based_aggregation(df, group_columns, value_column)
        else:
            return df.groupby(group_columns)[value_column].sum() * self.SLOT_HOURS
    
    def _numpy_based_aggregation(self, df, group_columns, value_column):
        """NumPyベースの集計"""
        # カテゴリ化で高速化
        for col in group_columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype('category')
        
        return df.groupby(group_columns, observed=True)[value_column].sum() * self.SLOT_HOURS

# 使用例
slot_optimizer = SlotHoursOptimizer()

def calculate_hours_fast(df, column='parsed_slots_count'):
    """高速時間計算"""
    if len(df) > 1000:
        return slot_optimizer.parallel_slot_calculation(df, column)
    else:
        return df[column] * 0.5
