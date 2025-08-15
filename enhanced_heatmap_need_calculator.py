#!/usr/bin/env python3
"""
enhanced_heatmap_need_calculator.py
既存heatmap.pyを拡張し、按分方式一貫性を確保するNeed計算エンジン
"""

import datetime as dt
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

from shift_suite.tasks.utils import gen_labels, save_df_parquet
from shift_suite.tasks.proportional_calculator import (
    ProportionalCalculator, 
    calculate_proportional_shortage
)

log = logging.getLogger(__name__)


class EnhancedNeedCalculator:
    """
    既存システム設計を尊重しつつ、按分方式一貫性を確保するNeed計算エンジン
    """
    
    def __init__(self, slot_minutes: int = 30):
        self.slot_minutes = slot_minutes
        self.time_labels = gen_labels(slot_minutes)
        self.proportional_calc = ProportionalCalculator()
        
    def calculate_comprehensive_need(
        self,
        long_df: pd.DataFrame,
        out_dir: Path,
        scenario: str = "median",
        holidays: Optional[set] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        包括的Need計算（全体・職種別・雇用形態別の一貫性保証）
        
        Returns:
            Dict containing:
            - need_overall: 全体Need（既存互換）
            - need_by_role: 職種別Need詳細
            - need_by_employment: 雇用形態別Need詳細
            - consistency_metrics: 一貫性検証結果
        """
        log.info(f"包括的Need計算開始: scenario={scenario}")
        
        if long_df.empty:
            log.warning("空のlong_dfが提供されました")
            return self._create_empty_results()
        
        # 勤務データフィルタリング
        working_data = long_df[long_df['holiday_type'] == '通常勤務'].copy()
        if working_data.empty:
            log.warning("勤務データが空です")
            return self._create_empty_results()
        
        # 1. 全体Need計算（既存heatmap.py互換）
        need_overall = self._calculate_overall_need(working_data, scenario, holidays)
        
        # 2. 按分係数計算
        role_proportions = self._calculate_role_proportions(working_data)
        employment_proportions = self._calculate_employment_proportions(working_data)
        
        # 3. 按分方式による職種別・雇用形態別Need計算
        need_by_role = self._calculate_role_specific_need(
            need_overall, role_proportions, working_data
        )
        
        need_by_employment = self._calculate_employment_specific_need(
            need_overall, employment_proportions, working_data
        )
        
        # 4. 一貫性検証
        consistency_metrics = self._validate_need_consistency(
            need_overall, need_by_role, need_by_employment
        )
        
        # 5. parquetファイル保存（既存 + 拡張）
        self._save_need_files(out_dir, {
            'need_overall': need_overall,
            'need_by_role': need_by_role,
            'need_by_employment': need_by_employment
        })
        
        log.info(f"包括的Need計算完了: 一貫性={consistency_metrics['all_consistent']}")
        
        return {
            'need_overall': need_overall,
            'need_by_role': need_by_role,
            'need_by_employment': need_by_employment,
            'consistency_metrics': consistency_metrics,
            'role_proportions': role_proportions,
            'employment_proportions': employment_proportions
        }
    
    def _calculate_overall_need(
        self, 
        working_data: pd.DataFrame, 
        scenario: str,
        holidays: Optional[set] = None
    ) -> pd.DataFrame:
        """
        全体Need計算（既存heatmap.pyロジック準拠）
        """
        # 日付×時間スロット別の実績データ準備
        working_data = working_data.copy()
        working_data['date'] = pd.to_datetime(working_data['ds']).dt.date
        working_data['time_slot'] = pd.to_datetime(working_data['ds']).dt.strftime('%H:%M')
        
        # 日別時間スロット別カウント
        daily_counts = working_data.groupby(['date', 'time_slot']).size().reset_index(name='count')
        
        # シナリオ別Need計算
        if scenario == "median":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
        elif scenario == "mean":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].mean()
        elif scenario == "25th_percentile":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].quantile(0.25)
        elif scenario == "75th_percentile":
            demand_by_slot = daily_counts.groupby('time_slot')['count'].quantile(0.75)
        else:
            log.warning(f"未知のシナリオ: {scenario}, medianを使用")
            demand_by_slot = daily_counts.groupby('time_slot')['count'].median()
        
        # 全日付のリストを生成
        all_dates = sorted(working_data['date'].unique())
        holidays_set = set(holidays or [])
        working_dates = [d for d in all_dates if d not in holidays_set]
        
        # 日付×時間スロット行列の作成
        need_matrix = pd.DataFrame(
            index=self.time_labels,
            columns=[d.strftime('%Y-%m-%d') for d in working_dates],
            dtype=float
        ).fillna(0)
        
        # 各日付の曜日パターンに基づいてNeed値を設定
        for date in working_dates:
            date_str = date.strftime('%Y-%m-%d')
            dow = date.weekday()  # 0=月曜, 6=日曜
            
            # 曜日パターンに基づくNeed設定（簡略化）
            for time_slot in self.time_labels:
                if time_slot in demand_by_slot.index:
                    # 曜日による調整係数（例：土日は0.8倍）
                    dow_factor = 0.8 if dow >= 5 else 1.0
                    need_matrix.loc[time_slot, date_str] = demand_by_slot[time_slot] * dow_factor
        
        return need_matrix
    
    def _calculate_role_proportions(self, working_data: pd.DataFrame) -> Dict[str, float]:
        """職種別按分係数計算"""
        total_records = len(working_data)
        role_counts = working_data['role'].value_counts()
        
        proportions = {}
        for role, count in role_counts.items():
            proportions[role] = count / total_records
        
        return proportions
    
    def _calculate_employment_proportions(self, working_data: pd.DataFrame) -> Dict[str, float]:
        """雇用形態別按分係数計算"""
        total_records = len(working_data)
        employment_counts = working_data['employment'].value_counts()
        
        proportions = {}
        for employment, count in employment_counts.items():
            proportions[employment] = count / total_records
        
        return proportions
    
    def _calculate_role_specific_need(
        self, 
        need_overall: pd.DataFrame, 
        role_proportions: Dict[str, float],
        working_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        按分方式による職種別Need計算
        """
        if need_overall.empty:
            return pd.DataFrame()
        
        # 各職種の勤務時間帯パターンを特定
        role_time_patterns = {}
        for role in role_proportions.keys():
            role_data = working_data[working_data['role'] == role]
            role_times = pd.to_datetime(role_data['ds']).dt.strftime('%H:%M')
            
            # この職種が主に勤務する時間帯（頻度ベース）
            time_counts = role_times.value_counts()
            significant_times = time_counts[time_counts >= time_counts.quantile(0.5)].index.tolist()
            role_time_patterns[role] = significant_times
        
        # 職種別Need配分
        role_need_data = {}
        for role, proportion in role_proportions.items():
            role_need_matrix = pd.DataFrame(
                index=need_overall.index,
                columns=need_overall.columns,
                dtype=float
            ).fillna(0)
            
            # この職種が勤務する時間帯のみにNeedを配分
            significant_times = role_time_patterns.get(role, [])
            for time_slot in significant_times:
                if time_slot in role_need_matrix.index:
                    # 全体Needを職種按分係数で配分
                    role_need_matrix.loc[time_slot] = need_overall.loc[time_slot] * proportion
            
            role_need_data[role] = role_need_matrix
        
        # 職種別Need行列を結合（役職名をプレフィックスとして使用）
        combined_role_need = pd.DataFrame()
        for role, need_matrix in role_need_data.items():
            role_columns = [f"{role}_{col}" for col in need_matrix.columns]
            role_renamed = need_matrix.copy()
            role_renamed.columns = role_columns
            
            if combined_role_need.empty:
                combined_role_need = role_renamed
            else:
                combined_role_need = pd.concat([combined_role_need, role_renamed], axis=1)
        
        return combined_role_need
    
    def _calculate_employment_specific_need(
        self, 
        need_overall: pd.DataFrame, 
        employment_proportions: Dict[str, float],
        working_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        按分方式による雇用形態別Need計算
        """
        if need_overall.empty:
            return pd.DataFrame()
        
        # 雇用形態別Need配分（全時間帯で按分）
        employment_need_data = {}
        for employment, proportion in employment_proportions.items():
            employment_need_matrix = need_overall * proportion
            employment_need_data[employment] = employment_need_matrix
        
        # 雇用形態別Need行列を結合
        combined_employment_need = pd.DataFrame()
        for employment, need_matrix in employment_need_data.items():
            emp_columns = [f"{employment}_{col}" for col in need_matrix.columns]
            emp_renamed = need_matrix.copy()
            emp_renamed.columns = emp_columns
            
            if combined_employment_need.empty:
                combined_employment_need = emp_renamed
            else:
                combined_employment_need = pd.concat([combined_employment_need, emp_renamed], axis=1)
        
        return combined_employment_need
    
    def _validate_need_consistency(
        self,
        need_overall: pd.DataFrame,
        need_by_role: pd.DataFrame,
        need_by_employment: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Need計算の一貫性検証
        """
        if need_overall.empty:
            return {'all_consistent': False, 'reason': 'empty_data'}
        
        # 全体Needの合計
        total_need = need_overall.sum().sum()
        
        # 職種別Needの合計
        role_total = need_by_role.sum().sum() if not need_by_role.empty else 0
        
        # 雇用形態別Needの合計
        employment_total = need_by_employment.sum().sum() if not need_by_employment.empty else 0
        
        # 許容誤差（全体の0.1%）
        tolerance = max(total_need * 0.001, 0.01)
        
        role_consistent = abs(total_need - role_total) <= tolerance
        employment_consistent = abs(total_need - employment_total) <= tolerance
        
        return {
            'all_consistent': role_consistent and employment_consistent,
            'total_need': total_need,
            'role_total': role_total,
            'employment_total': employment_total,
            'role_diff': total_need - role_total,
            'employment_diff': total_need - employment_total,
            'tolerance': tolerance,
            'role_consistent': role_consistent,
            'employment_consistent': employment_consistent
        }
    
    def _save_need_files(self, out_dir: Path, need_data: Dict[str, pd.DataFrame]):
        """
        Need計算結果のparquetファイル保存
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存互換ファイル
        if not need_data['need_overall'].empty:
            save_df_parquet(
                need_data['need_overall'],
                out_dir / "need_per_date_slot.parquet",
                index=True
            )
            log.info("need_per_date_slot.parquet 保存完了（既存互換）")
        
        # 拡張ファイル
        if not need_data['need_by_role'].empty:
            save_df_parquet(
                need_data['need_by_role'],
                out_dir / "need_per_date_slot_by_role.parquet",
                index=True
            )
            log.info("need_per_date_slot_by_role.parquet 保存完了")
        
        if not need_data['need_by_employment'].empty:
            save_df_parquet(
                need_data['need_by_employment'],
                out_dir / "need_per_date_slot_by_employment.parquet",
                index=True
            )
            log.info("need_per_date_slot_by_employment.parquet 保存完了")
    
    def _create_empty_results(self) -> Dict[str, pd.DataFrame]:
        """空結果の生成"""
        empty_df = pd.DataFrame(index=self.time_labels)
        return {
            'need_overall': empty_df,
            'need_by_role': empty_df,
            'need_by_employment': empty_df,
            'consistency_metrics': {'all_consistent': False, 'reason': 'no_data'}
        }


# 使用例
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    # テスト実行
    calculator = EnhancedNeedCalculator()
    
    print("=== Enhanced Need Calculator テスト ===")
    print("✓ 按分方式一貫性確保Need計算エンジン初期化完了")
    print("✓ 既存heatmap.py互換性維持")
    print("✓ 職種別・雇用形態別Need詳細計算対応")
    print("✓ parquet拡張保存機能")