# analysis_engine.py - 高速分析計算エンジン
"""
分析処理のボトルネックを解消する高速計算エンジン
ベクトル化・並列化・メモリ最適化を駆使
"""

import logging
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any
import multiprocessing as mp
from dataclasses import dataclass
import time

from shift_suite.tasks.statistical_need_calculator import (
    calculate_all_statistical_needs,
)
from shift_suite.tasks.time_axis_shortage_calculator import (
    calculate_time_axis_shortage,
)
from shift_suite.tasks.shortage import assign_shortage_to_individuals

# ログ設定
log = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    """分析処理設定"""
    enable_parallel: bool = True
    max_workers: int = min(4, mp.cpu_count())
    chunk_size: int = 1000
    use_vectorization: bool = True
    memory_limit_mb: int = 500

class OptimizedAnalysisEngine:
    """最適化された分析計算エンジン"""
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.executor = None
        self._cache = {}
        
    def __enter__(self):
        if self.config.enable_parallel:
            self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def calculate_role_dynamic_need_optimized(
        self, 
        df_heat: pd.DataFrame, 
        date_cols: List[str], 
        heat_key: str,
        data_cache: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        最適化された職種別動的need計算
        O(n²) → O(n) に改善
        """
        start_time = time.time()
        log.info(f"[最適化エンジン] 高速計算開始: {heat_key}")
        
        # キャッシュキー生成
        cache_key = f"role_need_{heat_key}_{len(date_cols)}_{hash(tuple(date_cols))}"
        if cache_key in self._cache:
            log.info(f"[最適化エンジン] キャッシュヒット: {heat_key}")
            return self._cache[cache_key]
        
        try:
            # Step 1: 詳細need値ファイルの直接使用（最優先）
            result = self._try_detailed_need_file(df_heat, date_cols, heat_key, data_cache)
            if result is not None:
                self._cache[cache_key] = result
                elapsed = time.time() - start_time
                log.info(f"[最適化エンジン] 詳細ファイル使用完了: {heat_key} ({elapsed:.2f}秒)")
                return result
            
            # Step 2: ベクトル化された高速計算
            result = self._vectorized_calculation(df_heat, date_cols, heat_key, data_cache)
            self._cache[cache_key] = result
            
            elapsed = time.time() - start_time
            log.info(f"[最適化エンジン] ベクトル化計算完了: {heat_key} ({elapsed:.2f}秒)")
            return result
            
        except Exception as e:
            log.error(f"[最適化エンジン] 計算エラー {heat_key}: {e}")
            # フォールバック: 基本計算
            return self._fallback_calculation(df_heat, date_cols)
    
    def _try_detailed_need_file(
        self, 
        df_heat: pd.DataFrame, 
        date_cols: List[str], 
        heat_key: str,
        data_cache: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """詳細need値ファイルの直接使用を試行"""
        detailed_need_key = None
        
        if heat_key.startswith('heat_emp_'):
            emp_name = heat_key.replace('heat_emp_', '').replace('heat_', '')
            detailed_need_key = f"need_per_date_slot_emp_{emp_name}"
        elif heat_key.startswith('heat_') and heat_key not in ['heat_all', 'heat_ALL']:
            role_name = heat_key.replace('heat_', '')
            detailed_need_key = f"need_per_date_slot_role_{role_name}"
        
        if detailed_need_key and detailed_need_key in data_cache:
            detailed_need_df = data_cache[detailed_need_key]
            if isinstance(detailed_need_df, pd.DataFrame) and not detailed_need_df.empty:
                # 効率的な列フィルタリング
                available_cols = [col for col in date_cols if col in detailed_need_df.columns]
                if available_cols:
                    result = detailed_need_df[available_cols].reindex(
                        index=df_heat.index, 
                        fill_value=0
                    )
                    return result
        
        return None
    
    def _vectorized_calculation(
        self, 
        df_heat: pd.DataFrame, 
        date_cols: List[str], 
        heat_key: str,
        data_cache: Dict[str, Any]
    ) -> pd.DataFrame:
        """ベクトル化された高速計算"""
        
        # 全体need値を取得
        need_per_date_df = data_cache.get('need_per_date_slot', pd.DataFrame())
        if need_per_date_df.empty:
            return self._fallback_calculation(df_heat, date_cols)
        
        # ベクトル化: 全職種のbaseline need値を一括計算
        role_keys = [k for k in data_cache.keys() 
                    if k.startswith('heat_') 
                    and k not in ['heat_all', 'heat_ALL']
                    and not k.startswith('heat_emp_')]
        
        # NumPy配列で一括処理
        baseline_needs = []
        for role_key in role_keys:
            role_heat = data_cache.get(role_key, pd.DataFrame())
            if not role_heat.empty and 'need' in role_heat.columns:
                baseline_needs.append(role_heat['need'].sum())
        
        if not baseline_needs:
            return self._fallback_calculation(df_heat, date_cols)
        
        # ベクトル化計算
        total_baseline_need = np.sum(baseline_needs)
        current_baseline = df_heat['need'].sum() if 'need' in df_heat.columns else len(df_heat)
        role_ratio = current_baseline / total_baseline_need if total_baseline_need > 0 else 0
        
        # 行列演算による高速化
        result_df = pd.DataFrame(index=df_heat.index, columns=date_cols)
        need_columns = [str(col) for col in date_cols if str(col) in need_per_date_df.columns]
        
        if need_columns:
            # NumPy行列演算を使用
            need_matrix = need_per_date_df[need_columns].values
            role_need_matrix = need_matrix * role_ratio
            
            # 結果DataFrameに一括代入
            for i, col in enumerate(need_columns):
                original_col = date_cols[date_cols.index(col) if col in [str(c) for c in date_cols] else 0]
                if len(role_need_matrix) == len(df_heat):
                    result_df[original_col] = role_need_matrix[:, i]
        
        return result_df.fillna(0)
    
    def _fallback_calculation(self, df_heat: pd.DataFrame, date_cols: List[str]) -> pd.DataFrame:
        """フォールバック計算"""
        baseline_values = df_heat['need'].values if 'need' in df_heat.columns else np.ones(len(df_heat))
        return pd.DataFrame(
            np.repeat(baseline_values[:, np.newaxis], len(date_cols), axis=1),
            index=df_heat.index, 
            columns=date_cols
        )
    
    def batch_process_heatmaps(
        self, 
        heatmap_tasks: List[Tuple[pd.DataFrame, List[str], str]], 
        data_cache: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """並列バッチ処理でヒートマップを高速計算"""
        if not self.config.enable_parallel or not self.executor:
            # シーケンシャル処理
            results = {}
            for df_heat, date_cols, heat_key in heatmap_tasks:
                results[heat_key] = self.calculate_role_dynamic_need_optimized(
                    df_heat, date_cols, heat_key, data_cache
                )
            return results
        
        # 並列処理
        futures = {}
        for df_heat, date_cols, heat_key in heatmap_tasks:
            future = self.executor.submit(
                self.calculate_role_dynamic_need_optimized,
                df_heat, date_cols, heat_key, data_cache
            )
            futures[heat_key] = future
        
        # 結果収集
        results = {}
        for heat_key, future in futures.items():
            try:
                results[heat_key] = future.result(timeout=30)  # 30秒タイムアウト
            except Exception as e:
                log.error(f"[最適化エンジン] 並列処理エラー {heat_key}: {e}")
                # フォールバックを用意
                results[heat_key] = pd.DataFrame()
        
        return results
    
    def optimize_memory_usage(self, data_cache: Dict[str, Any]) -> Dict[str, Any]:
        """メモリ使用量最適化"""
        optimized_cache = {}
        total_memory = 0
        
        # データサイズを計算してソート
        cache_sizes = []
        for key, value in data_cache.items():
            if isinstance(value, pd.DataFrame):
                size_mb = value.memory_usage(deep=True).sum() / (1024 * 1024)
                cache_sizes.append((key, value, size_mb))
            else:
                cache_sizes.append((key, value, 0.001))  # 非DataFrameは小さいとみなす
        
        # メモリ使用量順にソート（大きいものから）
        cache_sizes.sort(key=lambda x: x[2], reverse=True)
        
        # メモリ制限内で必要なデータを保持
        for key, value, size_mb in cache_sizes:
            if total_memory + size_mb <= self.config.memory_limit_mb:
                optimized_cache[key] = value
                total_memory += size_mb
            else:
                log.info(f"[最適化エンジン] メモリ制限により除外: {key} ({size_mb:.1f}MB)")
        
        log.info(f"[最適化エンジン] メモリ最適化完了: {total_memory:.1f}MB / {self.config.memory_limit_mb}MB")
        return optimized_cache

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timing(self, operation: str):
        """計測開始"""
        self.start_times[operation] = time.time()
    
    def end_timing(self, operation: str) -> float:
        """計測終了"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = duration
            del self.start_times[operation]
            return duration
        return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        total_time = sum(self.metrics.values())
        report = {
            'total_time': total_time,
            'operations': len(self.metrics),
            'average_time': total_time / len(self.metrics) if self.metrics else 0,
            'details': self.metrics.copy()
        }
        return report

# グローバルインスタンス
analysis_engine = OptimizedAnalysisEngine()
performance_monitor = PerformanceMonitor()


def run(actual_df: pd.DataFrame, time_unit_minutes: int) -> pd.DataFrame:
    """統計的Need値算出から不足割当までを一括で実行する。"""
    needs_df = calculate_all_statistical_needs(actual_df, time_unit_minutes)
    shortage_df = calculate_time_axis_shortage(actual_df, needs_df, time_unit_minutes)
    return assign_shortage_to_individuals(actual_df, shortage_df, time_unit_minutes)
