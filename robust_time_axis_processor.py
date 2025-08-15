#!/usr/bin/env python
"""
堅牢な時間軸処理システム

タイムゾーン対応と動的日付スライダーの実装
夏時間などによる日付ズレを防止
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pytz
import logging
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path

log = logging.getLogger(__name__)

# 日本標準時の定義
JST = pytz.timezone('Asia/Tokyo')

class RobustTimeProcessor:
    """堅牢な時間軸処理クラス"""
    
    def __init__(self, default_timezone: str = 'Asia/Tokyo'):
        """
        初期化
        
        Args:
            default_timezone: デフォルトタイムゾーン（日本標準時）
        """
        self.default_tz = pytz.timezone(default_timezone)
        self.processed_data = None
        self.date_range_info = {}
        
    def normalize_datetime_with_timezone(self, df: pd.DataFrame, datetime_column: str = 'ds') -> pd.DataFrame:
        """
        タイムゾーンを考慮した日時正規化
        
        Args:
            df: 処理対象DataFrame
            datetime_column: 日時列名
            
        Returns:
            正規化されたDataFrame
        """
        log.info(f"[TIME_NORMALIZE] タイムゾーン正規化開始: {datetime_column}")
        
        df_normalized = df.copy()
        
        try:
            # 元の日時データの分析
            original_dt_info = self._analyze_original_datetime(df[datetime_column])
            log.info(f"[TIME_NORMALIZE] 元データ分析: {original_dt_info}")
            
            # pandas to_datetime で基本変換
            dt_series = pd.to_datetime(df_normalized[datetime_column], errors='coerce')
            
            # タイムゾーン情報の処理
            if dt_series.dt.tz is None:
                # タイムゾーン未指定の場合、日本標準時として解釈
                log.info("[TIME_NORMALIZE] タイムゾーン未指定 -> JST適用")
                dt_series = dt_series.dt.tz_localize(self.default_tz, ambiguous='infer')
            else:
                # 既存タイムゾーンをJSTに変換
                log.info(f"[TIME_NORMALIZE] タイムゾーン変換: {dt_series.dt.tz} -> JST")
                dt_series = dt_series.dt.tz_convert(self.default_tz)
            
            # 正規化された日時を設定
            df_normalized[datetime_column] = dt_series
            
            # 追加の時間関連列を生成
            df_normalized = self._add_time_features(df_normalized, datetime_column)
            
            # 日付範囲情報を保存
            self.date_range_info = self._extract_date_range_info(dt_series)
            
            log.info(f"[TIME_NORMALIZE] 正規化完了: {len(df_normalized)}レコード")
            return df_normalized
            
        except Exception as e:
            log.error(f"[TIME_NORMALIZE] エラー: {e}")
            raise ValueError(f"日時正規化に失敗しました: {e}")
    
    def _analyze_original_datetime(self, dt_series: pd.Series) -> Dict[str, any]:
        """元の日時データの分析"""
        
        # サンプルデータの確認
        sample_values = dt_series.dropna().head(10).tolist()
        
        # データ型の確認
        data_types = set(type(val).__name__ for val in sample_values)
        
        # 日付パターンの推定
        date_patterns = []
        for val in sample_values:
            if isinstance(val, str):
                if '/' in val:
                    date_patterns.append('slash_separated')
                elif '-' in val:
                    date_patterns.append('hyphen_separated')
                elif len(val) == 8 and val.isdigit():
                    date_patterns.append('yyyymmdd')
                else:
                    date_patterns.append('other_string')
        
        return {
            'total_records': len(dt_series),
            'null_count': dt_series.isnull().sum(),
            'sample_values': sample_values,
            'data_types': list(data_types),
            'date_patterns': list(set(date_patterns)),
            'min_value': dt_series.min() if not dt_series.empty else None,
            'max_value': dt_series.max() if not dt_series.empty else None
        }
    
    def _add_time_features(self, df: pd.DataFrame, datetime_column: str) -> pd.DataFrame:
        """時間関連特徴量の追加"""
        
        dt_col = df[datetime_column]
        
        # 基本的な時間要素
        df['date'] = dt_col.dt.date
        df['time'] = dt_col.dt.time
        df['hour'] = dt_col.dt.hour
        df['minute'] = dt_col.dt.minute
        df['weekday'] = dt_col.dt.weekday  # 0=月曜日
        df['weekday_name'] = dt_col.dt.day_name()
        df['month'] = dt_col.dt.month
        df['quarter'] = dt_col.dt.quarter
        df['year'] = dt_col.dt.year
        
        # 日本の営業日判定
        df['is_weekend'] = df['weekday'] >= 5
        df['is_business_hour'] = (df['hour'] >= 9) & (df['hour'] < 17)
        
        # 時間帯カテゴリ
        df['time_category'] = df['hour'].apply(self._categorize_time_period)
        
        # 月内の週
        df['week_of_month'] = (df[datetime_column].dt.day - 1) // 7 + 1
        
        return df
    
    def _categorize_time_period(self, hour: int) -> str:
        """時間帯のカテゴリ分類"""
        if 6 <= hour < 9:
            return 'early_morning'
        elif 9 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 14:
            return 'lunch'
        elif 14 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 20:
            return 'evening'
        elif 20 <= hour < 23:
            return 'night'
        else:
            return 'late_night'
    
    def _extract_date_range_info(self, dt_series: pd.Series) -> Dict[str, any]:
        """日付範囲情報の抽出"""
        
        if dt_series.empty:
            return {}
        
        min_date = dt_series.min()
        max_date = dt_series.max()
        date_span = (max_date - min_date).days
        
        # 日付のユニーク値
        unique_dates = dt_series.dt.date.unique()
        unique_dates_sorted = sorted(unique_dates)
        
        return {
            'min_datetime': min_date,
            'max_datetime': max_date,
            'date_span_days': date_span,
            'unique_dates': unique_dates_sorted,
            'total_unique_dates': len(unique_dates_sorted),
            'timezone': str(min_date.tz) if min_date.tz else 'None'
        }
    
    def generate_dynamic_date_slider_config(self) -> Dict[str, any]:
        """動的日付スライダー設定の生成"""
        
        if not self.date_range_info:
            return self._default_slider_config()
        
        unique_dates = self.date_range_info.get('unique_dates', [])
        
        if not unique_dates:
            return self._default_slider_config()
        
        # スライダー設定の生成
        slider_config = {
            'min_value': 0,
            'max_value': len(unique_dates) - 1,
            'default_range': [0, len(unique_dates) - 1],
            'step': 1,
            'marks': {},
            'date_mapping': {},
            'metadata': {
                'total_days': len(unique_dates),
                'date_span': self.date_range_info.get('date_span_days', 0),
                'start_date': str(unique_dates[0]) if unique_dates else None,
                'end_date': str(unique_dates[-1]) if unique_dates else None
            }
        }
        
        # マークとマッピングの生成
        for i, date in enumerate(unique_dates):
            date_str = date.strftime('%m/%d')
            
            # 週の始まり（月曜日）または月の始まりにマークを付ける
            weekday = pd.Timestamp(date).weekday()
            is_month_start = date.day <= 7
            
            if weekday == 0 or is_month_start or i == 0 or i == len(unique_dates) - 1:
                slider_config['marks'][i] = date_str
            
            slider_config['date_mapping'][i] = str(date)
        
        log.info(f"[SLIDER] 動的スライダー設定生成: {len(unique_dates)}日間")
        return slider_config
    
    def _default_slider_config(self) -> Dict[str, any]:
        """デフォルトスライダー設定"""
        return {
            'min_value': 0,
            'max_value': 6,
            'default_range': [0, 6],
            'step': 1,
            'marks': {i: f'Day {i+1}' for i in range(7)},
            'date_mapping': {i: f'day_{i+1}' for i in range(7)},
            'metadata': {
                'total_days': 7,
                'date_span': 6,
                'start_date': 'unknown',
                'end_date': 'unknown'
            }
        }
    
    def validate_date_consistency(self, df: pd.DataFrame, datetime_column: str = 'ds') -> Dict[str, any]:
        """日付データの整合性検証"""
        
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
        
        try:
            dt_series = df[datetime_column]
            
            # 欠損値チェック
            null_count = dt_series.isnull().sum()
            if null_count > 0:
                validation['warnings'].append(f"欠損値が{null_count}件あります")
            
            # 重複チェック
            duplicate_count = dt_series.duplicated().sum()
            if duplicate_count > 0:
                validation['warnings'].append(f"重複日時が{duplicate_count}件あります")
            
            # 時系列順序チェック
            if not dt_series.is_monotonic_increasing:
                validation['warnings'].append("時系列が昇順ではありません")
            
            # 異常な時間間隔チェック
            time_diffs = dt_series.diff().dropna()
            if not time_diffs.empty:
                mode_diff = time_diffs.mode()
                if len(mode_diff) > 0:
                    expected_interval = mode_diff.iloc[0]
                    unusual_intervals = time_diffs[
                        (time_diffs < expected_interval * 0.5) | 
                        (time_diffs > expected_interval * 2)
                    ]
                    
                    if len(unusual_intervals) > 0:
                        validation['warnings'].append(
                            f"異常な時間間隔が{len(unusual_intervals)}箇所あります"
                        )
            
            # 統計情報
            validation['statistics'] = {
                'total_records': len(dt_series),
                'null_count': null_count,
                'duplicate_count': duplicate_count,
                'unique_count': dt_series.nunique(),
                'date_range': {
                    'start': str(dt_series.min()) if not dt_series.empty else None,
                    'end': str(dt_series.max()) if not dt_series.empty else None,
                    'span_days': (dt_series.max() - dt_series.min()).days if not dt_series.empty else 0
                }
            }
            
            # エラーの場合
            if len(validation['errors']) > 0:
                validation['is_valid'] = False
            
        except Exception as e:
            validation['is_valid'] = False
            validation['errors'].append(f"日付検証エラー: {e}")
        
        return validation

def create_dash_date_slider_component(slider_config: Dict[str, any]) -> Dict[str, any]:
    """
    Dash用日付スライダーコンポーネントの設定生成
    
    Args:
        slider_config: generate_dynamic_date_slider_config()の出力
        
    Returns:
        Dashのdcc.RangeSliderに渡すprops
    """
    
    return {
        'id': 'dynamic-date-range-slider',
        'min': slider_config['min_value'],
        'max': slider_config['max_value'],
        'value': slider_config['default_range'],
        'step': slider_config['step'],
        'marks': slider_config['marks'],
        'tooltip': {
            'placement': 'bottom',
            'always_visible': True
        },
        'className': 'dynamic-date-slider'
    }

def process_time_data_for_analysis(
    df: pd.DataFrame, 
    datetime_column: str = 'ds'
) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    分析用の完全な時間データ処理
    
    Args:
        df: 元のDataFrame
        datetime_column: 日時列名
        
    Returns:
        tuple: (処理済みDataFrame, スライダー設定)
    """
    
    processor = RobustTimeProcessor()
    
    # 1. タイムゾーン正規化
    df_normalized = processor.normalize_datetime_with_timezone(df, datetime_column)
    
    # 2. 整合性検証
    validation = processor.validate_date_consistency(df_normalized, datetime_column)
    if not validation['is_valid']:
        log.warning(f"日付整合性の問題: {validation['errors']}")
    
    # 3. 動的スライダー設定生成
    slider_config = processor.generate_dynamic_date_slider_config()
    
    # 4. 追加情報の付与
    slider_config['validation'] = validation
    slider_config['timezone_info'] = {
        'processed_timezone': str(processor.default_tz),
        'sample_datetime': str(df_normalized[datetime_column].iloc[0]) if not df_normalized.empty else None
    }
    
    log.info("時間軸処理完了: タイムゾーン正規化とスライダー設定生成")
    
    return df_normalized, slider_config

# 使用例とテスト
def test_robust_time_processing():
    """堅牢な時間処理のテスト"""
    
    # テストデータの作成
    test_dates = pd.date_range('2025-01-01', periods=14, freq='30min')
    test_df = pd.DataFrame({
        'ds': test_dates,
        'staff': np.random.randint(1, 5, len(test_dates)),
        'role': np.random.choice(['介護', '看護', '事務'], len(test_dates))
    })
    
    print("=== 堅牢な時間軸処理テスト ===")
    
    # 処理実行
    processed_df, slider_config = process_time_data_for_analysis(test_df)
    
    print(f"処理済みレコード数: {len(processed_df)}")
    print(f"生成された列数: {len(processed_df.columns)}")
    print(f"スライダー日数: {slider_config['metadata']['total_days']}")
    print(f"タイムゾーン: {slider_config['timezone_info']['processed_timezone']}")
    
    # スライダーコンポーネント設定
    dash_config = create_dash_date_slider_component(slider_config)
    print(f"Dashスライダー設定: min={dash_config['min']}, max={dash_config['max']}")
    
    return processed_df, slider_config

if __name__ == "__main__":
    # テスト実行
    test_df, test_config = test_robust_time_processing()
    print("\n堅牢な時間軸処理のテストが完了しました！")