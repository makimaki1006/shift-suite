#!/usr/bin/env python
"""
統一過不足計算ロジック

全体分析と職種別分析で使用される過不足計算を統一
真の過不足・不足のみ・過剰のみを明確に分離して計算
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional

log = logging.getLogger(__name__)

def calculate_true_shortage(need_df: pd.DataFrame, staff_df: pd.DataFrame, slot_hours: float) -> Dict[str, any]:
    """
    真の過不足、不足のみ、過剰のみを計算する統一関数
    
    Args:
        need_df: 需要データフレーム（時間帯×日付）
        staff_df: スタッフ配置データフレーム（時間帯×日付）
        slot_hours: スロット時間（UIから受け取った値）
        
    Returns:
        dict: 分析結果を含む辞書
            - true_balance: 真の過不足（正:不足, 負:過剰）
            - shortage_only: 不足のみ  
            - excess_only: 過剰のみ
            - net_hours: 実質時間（正:不足, 負:過剰）
            - shortage_hours: 不足時間のみ
            - excess_hours: 過剰時間のみ
            - statistics: 詳細統計情報
    """
    log.info(f"統一過不足計算開始: slot_hours={slot_hours}")
    
    # データ形状の検証
    if need_df.shape != staff_df.shape:
        log.warning(f"データ形状不一致: need={need_df.shape}, staff={staff_df.shape}")
        # 共通の列・行に合わせる
        common_columns = need_df.columns.intersection(staff_df.columns)
        common_index = need_df.index.intersection(staff_df.index)
        
        need_df = need_df.loc[common_index, common_columns]
        staff_df = staff_df.loc[common_index, common_columns]
        log.info(f"共通部分に調整: {need_df.shape}")
    
    # 真の過不足計算（clipしない）
    true_balance_df = need_df - staff_df
    
    # 分析用データフレームを分離
    shortage_only_df = true_balance_df.clip(lower=0)  # 不足のみ（正の値のみ）
    excess_only_df = (-true_balance_df).clip(lower=0)  # 過剰のみ（負の値を正に変換）
    
    # 時間換算の計算
    net_hours = true_balance_df.sum().sum() * slot_hours
    shortage_hours = shortage_only_df.sum().sum() * slot_hours  
    excess_hours = excess_only_df.sum().sum() * slot_hours
    
    # 詳細統計の計算
    statistics = _calculate_detailed_statistics(
        true_balance_df, shortage_only_df, excess_only_df, slot_hours
    )
    
    # 妥当性検証
    validation_results = _validate_shortage_calculation(
        need_df, staff_df, true_balance_df, slot_hours
    )
    
    results = {
        'true_balance': true_balance_df,      # 真の過不足（正:不足, 負:過剰）
        'shortage_only': shortage_only_df,    # 不足のみ
        'excess_only': excess_only_df,        # 過剰のみ
        'net_hours': net_hours,               # 実質時間（正:不足, 負:過剰）
        'shortage_hours': shortage_hours,     # 不足時間のみ
        'excess_hours': excess_hours,         # 過剰時間のみ
        'statistics': statistics,             # 詳細統計
        'validation': validation_results,     # 妥当性検証結果
        'calculation_params': {
            'slot_hours': slot_hours,
            'data_shape': need_df.shape,
            'analysis_method': 'unified_true_shortage'
        }
    }
    
    log.info(f"統一過不足計算完了: 実質{net_hours:.1f}h (不足:{shortage_hours:.1f}h, 過剰:{excess_hours:.1f}h)")
    
    return results

def _calculate_detailed_statistics(
    true_balance_df: pd.DataFrame, 
    shortage_only_df: pd.DataFrame, 
    excess_only_df: pd.DataFrame, 
    slot_hours: float
) -> Dict[str, any]:
    """詳細統計情報の計算"""
    
    # 日別統計
    daily_balance = true_balance_df.sum(axis=0) * slot_hours  # 日別実質過不足
    daily_shortage = shortage_only_df.sum(axis=0) * slot_hours  # 日別不足
    daily_excess = excess_only_df.sum(axis=0) * slot_hours  # 日別過剰
    
    # 時間帯別統計
    hourly_balance = true_balance_df.sum(axis=1) * slot_hours  # 時間帯別実質過不足
    hourly_shortage = shortage_only_df.sum(axis=1) * slot_hours  # 時間帯別不足
    hourly_excess = excess_only_df.sum(axis=1) * slot_hours  # 時間帯別過剰
    
    # 分散・偏差統計
    balance_std = true_balance_df.std().std()  # 過不足のばらつき
    shortage_concentration = _calculate_concentration_index(shortage_only_df)
    
    statistics = {
        'daily_statistics': {
            'avg_daily_balance': daily_balance.mean(),
            'max_daily_shortage': daily_shortage.max(),
            'max_daily_excess': daily_excess.max(),
            'days_with_shortage': (daily_shortage > 0).sum(),
            'days_with_excess': (daily_excess > 0).sum(),
            'balance_stability': daily_balance.std()
        },
        'hourly_statistics': {
            'peak_shortage_hour': hourly_shortage.idxmax() if hourly_shortage.max() > 0 else None,
            'peak_shortage_value': hourly_shortage.max(),
            'peak_excess_hour': hourly_excess.idxmax() if hourly_excess.max() > 0 else None,
            'peak_excess_value': hourly_excess.max(),
            'shortage_hours_count': (hourly_shortage > 0).sum(),
            'excess_hours_count': (hourly_excess > 0).sum()
        },
        'distribution_analysis': {
            'balance_variance': balance_std,
            'shortage_concentration': shortage_concentration,
            'coverage_efficiency': _calculate_coverage_efficiency(true_balance_df),
            'utilization_rate': _calculate_utilization_rate(true_balance_df)
        }
    }
    
    return statistics

def _calculate_concentration_index(shortage_df: pd.DataFrame) -> float:
    """不足の集中度指数を計算"""
    total_shortage = shortage_df.sum().sum()
    if total_shortage == 0:
        return 0.0
    
    # ジニ係数的な集中度計算
    flattened = shortage_df.values.flatten()
    sorted_values = np.sort(flattened)
    n = len(sorted_values)
    
    if n == 0 or total_shortage == 0:
        return 0.0
    
    cumsum = np.cumsum(sorted_values)
    concentration = (2 * np.sum((np.arange(n) + 1) * sorted_values) / (n * total_shortage)) - (n + 1) / n
    
    return max(0.0, min(1.0, concentration))

def _calculate_coverage_efficiency(balance_df: pd.DataFrame) -> float:
    """配置効率を計算（過剰と不足のバランス）"""
    positive_count = (balance_df > 0).sum().sum()  # 不足スロット数
    negative_count = (balance_df < 0).sum().sum()  # 過剰スロット数
    total_count = positive_count + negative_count
    
    if total_count == 0:
        return 1.0  # 完璧な配置
    
    # バランススコア（50:50が理想的）
    balance_score = 1 - abs(positive_count - negative_count) / total_count
    return balance_score

def _calculate_utilization_rate(balance_df: pd.DataFrame) -> float:
    """人員利用率を計算"""
    zero_count = (balance_df == 0).sum().sum()  # 過不足ゼロのスロット数
    total_slots = balance_df.size
    
    if total_slots == 0:
        return 0.0
    
    utilization = zero_count / total_slots
    return utilization

def _validate_shortage_calculation(
    need_df: pd.DataFrame, 
    staff_df: pd.DataFrame, 
    balance_df: pd.DataFrame, 
    slot_hours: float
) -> Dict[str, any]:
    """計算妥当性の検証"""
    
    validation = {
        'data_integrity': True,
        'calculation_accuracy': True,
        'warnings': [],
        'errors': []
    }
    
    # データ整合性チェック
    if need_df.isnull().any().any():
        validation['warnings'].append("需要データに欠損値が含まれています")
        validation['data_integrity'] = False
    
    if staff_df.isnull().any().any():
        validation['warnings'].append("スタッフデータに欠損値が含まれています")
        validation['data_integrity'] = False
    
    # 計算精度チェック
    calculated_balance = need_df - staff_df
    if not balance_df.equals(calculated_balance):
        validation['errors'].append("過不足計算に不整合があります")
        validation['calculation_accuracy'] = False
    
    # 現実性チェック
    max_shortage_hours = balance_df.clip(lower=0).sum().sum() * slot_hours
    total_days = len(balance_df.columns)
    daily_avg_shortage = max_shortage_hours / max(1, total_days)
    
    if daily_avg_shortage > 12:  # 1日12時間超過は非現実的
        validation['warnings'].append(f"日平均不足{daily_avg_shortage:.1f}時間は過大である可能性があります")
    
    # 範囲チェック
    if slot_hours <= 0 or slot_hours > 24:
        validation['errors'].append(f"スロット時間{slot_hours}は無効です")
        validation['calculation_accuracy'] = False
    
    return validation

def apply_unified_shortage_to_existing_code(shortage_df: pd.DataFrame, slot_hours: float) -> pd.DataFrame:
    """
    既存コードとの互換性を保つためのラッパー関数
    従来の shortage_only_df を返す
    """
    # ダミーのneed_dfとstaff_dfを再構成（既存コードとの互換性のため）
    # shortage_df が既に clip(lower=0) されていることを前提
    
    log.info("既存コードとの互換性モードで実行")
    
    # shortage_dfがclipされたものと仮定して、統計情報のみ計算
    shortage_hours = shortage_df.sum().sum() * slot_hours
    
    # 簡易統計
    daily_shortage = shortage_df.sum(axis=0) * slot_hours
    hourly_shortage = shortage_df.sum(axis=1) * slot_hours
    
    statistics = {
        'shortage_hours': shortage_hours,
        'daily_avg_shortage': daily_shortage.mean(),
        'max_daily_shortage': daily_shortage.max(),
        'peak_hour': hourly_shortage.idxmax() if hourly_shortage.max() > 0 else None,
        'calculation_method': 'compatibility_mode'
    }
    
    log.info(f"互換モード完了: 不足{shortage_hours:.1f}時間")
    
    return shortage_df  # 元のDataFrameをそのまま返す

# 使用例とテスト関数
def test_unified_shortage_calculation():
    """統一過不足計算のテスト"""
    
    # テストデータの作成
    dates = pd.date_range('2025-01-01', periods=7, freq='D')
    time_slots = pd.date_range('09:00', '17:00', freq='30min').strftime('%H:%M')
    
    need_data = np.random.randint(1, 5, size=(len(time_slots), len(dates)))
    staff_data = np.random.randint(0, 4, size=(len(time_slots), len(dates)))
    
    need_df = pd.DataFrame(need_data, index=time_slots, columns=dates)
    staff_df = pd.DataFrame(staff_data, index=time_slots, columns=dates)
    
    # 統一計算の実行
    results = calculate_true_shortage(need_df, staff_df, slot_hours=0.5)
    
    print("=== 統一過不足計算テスト結果 ===")
    print(f"実質時間: {results['net_hours']:.1f}時間")
    print(f"不足時間: {results['shortage_hours']:.1f}時間") 
    print(f"過剰時間: {results['excess_hours']:.1f}時間")
    print(f"データ整合性: {results['validation']['data_integrity']}")
    print(f"計算精度: {results['validation']['calculation_accuracy']}")
    
    daily_stats = results['statistics']['daily_statistics']
    print(f"日平均過不足: {daily_stats['avg_daily_balance']:.1f}時間")
    print(f"最大日不足: {daily_stats['max_daily_shortage']:.1f}時間")
    
    return results

if __name__ == "__main__":
    # テスト実行
    test_results = test_unified_shortage_calculation()
    print("\n統一過不足計算ロジックのテストが完了しました！")