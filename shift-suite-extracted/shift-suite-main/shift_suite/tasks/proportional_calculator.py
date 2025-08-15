#!/usr/bin/env python3
"""
按分計算モジュール
全データフローで一貫した按分計算ロジックを提供
"""

from typing import Dict, Tuple, List, Optional
import pandas as pd
import numpy as np
import logging
from shift_suite.tasks.constants import SLOT_HOURS

log = logging.getLogger(__name__)

class ProportionalCalculator:
    """
    按分計算クラス
    全体不足時間を職種別・雇用形態別に按分配分
    """
    
    def __init__(self):
        self.tolerance = 0.01  # 1分未満の誤差は許容
    
    def calculate_proportional_shortage(
        self, 
        working_data: pd.DataFrame, 
        total_shortage_hours: float
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        按分方式による職種別・雇用形態別不足時間計算
        
        Args:
            working_data: 勤務データ（holiday_type='通常勤務'のもの）
            total_shortage_hours: 全体不足時間
        
        Returns:
            (職種別不足時間辞書, 雇用形態別不足時間辞書)
        """
        if working_data.empty or total_shortage_hours <= 0:
            return {}, {}
        
        total_records = len(working_data)
        
        # 職種別按分計算
        role_shortages = {}
        role_counts = working_data['role'].value_counts()
        
        for role, count in role_counts.items():
            proportion = count / total_records
            role_shortage = total_shortage_hours * proportion
            role_shortages[role] = role_shortage
        
        # 雇用形態別按分計算
        employment_shortages = {}
        employment_counts = working_data['employment'].value_counts()
        
        for employment, count in employment_counts.items():
            proportion = count / total_records
            employment_shortage = total_shortage_hours * proportion
            employment_shortages[employment] = employment_shortage
        
        # ログ出力
        log.debug(f"按分計算完了: 職種{len(role_shortages)}個, 雇用形態{len(employment_shortages)}個")
        
        return role_shortages, employment_shortages
    
    def validate_consistency(
        self, 
        total: float, 
        role_dict: Dict[str, float], 
        employment_dict: Dict[str, float]
    ) -> Dict[str, any]:
        """
        三つのレベル計算の一貫性検証
        
        Returns:
            検証結果辞書
        """
        role_sum = sum(role_dict.values()) if role_dict else 0
        employment_sum = sum(employment_dict.values()) if employment_dict else 0
        
        total_vs_role = abs(total - role_sum) < self.tolerance
        total_vs_employment = abs(total - employment_sum) < self.tolerance
        
        result = {
            "total_vs_role": total_vs_role,
            "total_vs_employment": total_vs_employment,
            "all_consistent": total_vs_role and total_vs_employment,
            "role_sum": role_sum,
            "employment_sum": employment_sum,
            "role_diff": total - role_sum,
            "employment_diff": total - employment_sum
        }
        
        if not result["all_consistent"]:
            log.warning(f"一貫性検証失敗: role_diff={result['role_diff']:.6f}, emp_diff={result['employment_diff']:.6f}")
        
        return result
    
    def create_proportional_summary_df(
        self, 
        working_data: pd.DataFrame, 
        total_shortage_hours: float,
        scenario: str = "median"
    ) -> pd.DataFrame:
        """
        按分計算結果のサマリーDataFrame作成
        
        Args:
            working_data: 勤務データ
            total_shortage_hours: 全体不足時間
            scenario: シナリオ名
        
        Returns:
            職種別不足時間サマリーDF
        """
        if working_data.empty:
            return pd.DataFrame()
        
        role_shortages, _ = self.calculate_proportional_shortage(working_data, total_shortage_hours)
        
        summary_data = []
        total_records = len(working_data)
        
        for role, shortage_hours in role_shortages.items():
            record_count = len(working_data[working_data['role'] == role])
            proportion = record_count / total_records
            
            summary_data.append({
                'role': role,
                'shortage_hours': shortage_hours,
                'proportion': proportion,
                'record_count': record_count,
                'scenario': scenario
            })
        
        return pd.DataFrame(summary_data)
    
    def create_employment_summary_df(
        self, 
        working_data: pd.DataFrame, 
        total_shortage_hours: float,
        scenario: str = "median"
    ) -> pd.DataFrame:
        """
        按分計算結果の雇用形態別サマリーDF作成
        """
        if working_data.empty:
            return pd.DataFrame()
        
        _, employment_shortages = self.calculate_proportional_shortage(working_data, total_shortage_hours)
        
        summary_data = []
        total_records = len(working_data)
        
        for employment, shortage_hours in employment_shortages.items():
            record_count = len(working_data[working_data['employment'] == employment])
            proportion = record_count / total_records
            
            summary_data.append({
                'employment': employment,
                'shortage_hours': shortage_hours,
                'proportion': proportion,
                'record_count': record_count,
                'scenario': scenario
            })
        
        return pd.DataFrame(summary_data)
    
    def calculate_total_shortage_from_data(
        self, 
        working_data: pd.DataFrame, 
        scenario: str = "median"
    ) -> float:
        """
        勤務データから全体不足時間を計算（統合需要モデル）
        
        Args:
            working_data: 勤務データ
            scenario: 'median', 'mean', '25th_percentile', '75th_percentile'
        
        Returns:
            全体不足時間（時間単位）
        """
        if working_data.empty:
            return 0.0
        
        # 日付と時間スロットを準備
        working_data = working_data.copy()
        working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
        working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
        
        # 日別時間スロット別カウント
        daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        
        # シナリオに応じた需要計算
        if scenario == "median":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
        elif scenario == "mean":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].mean()
        elif scenario == "25th_percentile":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].quantile(0.25)
        elif scenario == "75th_percentile":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].quantile(0.75)
        else:
            log.warning(f"Unknown scenario: {scenario}, using median")
            demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
        
        # 実績平均
        unique_dates = working_data['date'].nunique()
        actual_by_slot = working_data.groupby('time_slot').size() / unique_dates
        
        # 不足計算
        shortage_by_slot = np.maximum(0, demand_by_slot - actual_by_slot)
        total_shortage_hours = shortage_by_slot.sum() * SLOT_HOURS  # スロット時間をDEFAULT_SLOT_MINUTESから動的計算
        
        log.debug(f"全体不足時間計算: {scenario}シナリオで{total_shortage_hours:.3f}時間")
        
        return total_shortage_hours


# グローバルインスタンス
_calculator = ProportionalCalculator()

# 便利関数
def calculate_proportional_shortage(working_data: pd.DataFrame, total_shortage_hours: float) -> Tuple[Dict[str, float], Dict[str, float]]:
    """按分計算の便利関数"""
    return _calculator.calculate_proportional_shortage(working_data, total_shortage_hours)

def validate_calculation_consistency(total: float, role_dict: Dict[str, float], employment_dict: Dict[str, float]) -> Dict[str, any]:
    """一貫性検証の便利関数"""
    return _calculator.validate_consistency(total, role_dict, employment_dict)

def calculate_total_shortage_from_data(working_data: pd.DataFrame, scenario: str = "median") -> float:
    """全体不足時間計算の便利関数"""
    return _calculator.calculate_total_shortage_from_data(working_data, scenario)

def create_proportional_summary_df(working_data: pd.DataFrame, total_shortage_hours: float, scenario: str = "median") -> pd.DataFrame:
    """職種別サマリーDF作成の便利関数"""
    return _calculator.create_proportional_summary_df(working_data, total_shortage_hours, scenario)

def create_employment_summary_df(working_data: pd.DataFrame, total_shortage_hours: float, scenario: str = "median") -> pd.DataFrame:
    """雇用形態別サマリーDF作成の便利関数"""
    return _calculator.create_employment_summary_df(working_data, total_shortage_hours, scenario)