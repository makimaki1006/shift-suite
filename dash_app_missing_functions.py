"""
dash_app.pyで必要な欠落関数を提供するモジュール
========================================
作成日: 2025-08-29
目的: 統合テストを実行可能にするため、必要な関数を実装
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from shift_suite.tasks.constants import DEFAULT_SLOT_MINUTES


class TimeAxisShortageCalculator:
    """時間軸での不足計算を行うクラス"""
    
    def __init__(self, slot_minutes: int = DEFAULT_SLOT_MINUTES):
        """
        初期化
        
        Args:
            slot_minutes: スロット時間（分）
        """
        self.slot_minutes = slot_minutes
        self.slot_hours = slot_minutes / 60.0
    
    def calculate_shortage(self, need_df: pd.DataFrame, staff_df: pd.DataFrame) -> pd.DataFrame:
        """
        不足を計算
        
        Args:
            need_df: 必要人数データ
            staff_df: スタッフ配置データ
            
        Returns:
            不足データ
        """
        # 次元を合わせる
        common_index = need_df.index.intersection(staff_df.index)
        common_columns = need_df.columns.intersection(staff_df.columns)
        
        if len(common_index) == 0 or len(common_columns) == 0:
            return pd.DataFrame()
        
        need_aligned = need_df.loc[common_index, common_columns]
        staff_aligned = staff_df.loc[common_index, common_columns]
        
        # 不足計算（need - staff、0以下は0）
        shortage = (need_aligned - staff_aligned).clip(lower=0)
        
        return shortage
    
    def calculate_excess(self, staff_df: pd.DataFrame, upper_df: pd.DataFrame) -> pd.DataFrame:
        """
        過剰を計算
        
        Args:
            staff_df: スタッフ配置データ
            upper_df: 上限データ
            
        Returns:
            過剰データ
        """
        # 次元を合わせる
        common_index = staff_df.index.intersection(upper_df.index)
        common_columns = staff_df.columns.intersection(upper_df.columns)
        
        if len(common_index) == 0 or len(common_columns) == 0:
            return pd.DataFrame()
        
        staff_aligned = staff_df.loc[common_index, common_columns]
        upper_aligned = upper_df.loc[common_index, common_columns]
        
        # 過剰計算（staff - upper、0以下は0）
        excess = (staff_aligned - upper_aligned).clip(lower=0)
        
        return excess
    
    def calculate_ratio(self, shortage_df: pd.DataFrame, need_df: pd.DataFrame) -> pd.DataFrame:
        """
        不足率を計算
        
        Args:
            shortage_df: 不足データ
            need_df: 必要人数データ
            
        Returns:
            不足率データ（0-1の範囲）
        """
        # 次元を合わせる
        common_index = shortage_df.index.intersection(need_df.index)
        common_columns = shortage_df.columns.intersection(need_df.columns)
        
        if len(common_index) == 0 or len(common_columns) == 0:
            return pd.DataFrame()
        
        shortage_aligned = shortage_df.loc[common_index, common_columns]
        need_aligned = need_df.loc[common_index, common_columns]
        
        # ゼロ除算を避けながら比率計算
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.divide(
                shortage_aligned.values,
                need_aligned.values,
                out=np.zeros_like(shortage_aligned.values, dtype=np.float64),
                where=(need_aligned.values != 0)
            )
        
        ratio_df = pd.DataFrame(
            ratio,
            index=common_index,
            columns=common_columns
        )
        
        return ratio_df
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        サマリー統計を取得
        
        Args:
            df: データフレーム
            
        Returns:
            統計情報の辞書
        """
        if df.empty:
            return {
                'mean': 0.0,
                'median': 0.0,
                'max': 0.0,
                'min': 0.0,
                'std': 0.0,
                'total': 0.0
            }
        
        return {
            'mean': float(df.mean().mean()),
            'median': float(df.median().median()),
            'max': float(df.max().max()),
            'min': float(df.min().min()),
            'std': float(df.std().std()),
            'total': float(df.sum().sum())
        }


def get_dynamic_slot_hours(slot_minutes: Optional[int] = None) -> float:
    """
    動的にslot_hoursを計算する関数
    
    Args:
        slot_minutes: スロット時間（分）。Noneの場合はデフォルト値を使用
        
    Returns:
        スロット時間（時間）
    """
    if slot_minutes is None:
        slot_minutes = DEFAULT_SLOT_MINUTES
    
    return slot_minutes / 60.0


def calculate_time_based_metrics(
    data: pd.DataFrame,
    slot_minutes: int = DEFAULT_SLOT_MINUTES
) -> Dict[str, Any]:
    """
    時間ベースのメトリクスを計算
    
    Args:
        data: 分析対象データ
        slot_minutes: スロット時間（分）
        
    Returns:
        メトリクスの辞書
    """
    slot_hours = get_dynamic_slot_hours(slot_minutes)
    
    metrics = {
        'slot_minutes': slot_minutes,
        'slot_hours': slot_hours,
        'total_slots': len(data) if not data.empty else 0,
        'total_hours': len(data) * slot_hours if not data.empty else 0.0,
    }
    
    # 日別の集計
    if 'date' in data.columns:
        daily_counts = data.groupby('date').size()
        metrics['daily_average_slots'] = float(daily_counts.mean())
        metrics['daily_average_hours'] = float(daily_counts.mean() * slot_hours)
        metrics['max_daily_slots'] = int(daily_counts.max()) if len(daily_counts) > 0 else 0
        metrics['min_daily_slots'] = int(daily_counts.min()) if len(daily_counts) > 0 else 0
    
    return metrics


def validate_data_consistency(
    need_df: pd.DataFrame,
    staff_df: pd.DataFrame,
    upper_df: Optional[pd.DataFrame] = None
) -> Dict[str, bool]:
    """
    データの整合性を検証
    
    Args:
        need_df: 必要人数データ
        staff_df: スタッフ配置データ
        upper_df: 上限データ（オプション）
        
    Returns:
        検証結果の辞書
    """
    validation_results = {
        'has_data': not need_df.empty and not staff_df.empty,
        'same_shape': need_df.shape == staff_df.shape,
        'same_index': list(need_df.index) == list(staff_df.index),
        'same_columns': list(need_df.columns) == list(staff_df.columns),
        'no_negative_values': (need_df >= 0).all().all() and (staff_df >= 0).all().all(),
    }
    
    if upper_df is not None and not upper_df.empty:
        validation_results['upper_shape_match'] = upper_df.shape == staff_df.shape
        validation_results['upper_no_negative'] = (upper_df >= 0).all().all()
        validation_results['upper_greater_than_need'] = (upper_df >= need_df).all().all() if upper_df.shape == need_df.shape else False
    
    validation_results['is_valid'] = all([
        validation_results['has_data'],
        validation_results['same_shape'],
        validation_results['no_negative_values']
    ])
    
    return validation_results


# エクスポート用のヘルパー関数
def prepare_export_data(
    data: pd.DataFrame,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    エクスポート用にデータを準備
    
    Args:
        data: エクスポート対象データ
        metadata: メタデータ（オプション）
        
    Returns:
        エクスポート用の辞書
    """
    export_dict = {
        'data': data.to_dict('records'),
        'shape': data.shape,
        'columns': list(data.columns),
        'index': list(data.index),
    }
    
    if metadata:
        export_dict['metadata'] = metadata
    
    # NumPy型をPython型に変換
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        return obj
    
    return convert_numpy_types(export_dict)