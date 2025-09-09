"""
科学的根拠に基づく疲労予測システム（改善版）
労働科学・産業医学の知見を反映したモデル
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class ScientificFatiguePredictionEngine:
    """科学的根拠に基づいた疲労予測エンジン"""
    
    def __init__(self):
        # 労働科学研究に基づく重み設定
        # 参考: ILO労働安全衛生基準, 日本産業衛生学会ガイドライン
        self.fatigue_weights = {
            'consecutive_days': 0.40,      # 最重要：連続勤務による疲労蓄積
            'night_shift_load': 0.30,      # 概日リズム破綻による疲労
            'weekly_hours': 0.20,          # 週間労働時間（非線形）
            'shift_irregularity': 0.10     # シフト不規則性
        }
        
        # 疲労回復モデル（指数減衰）
        self.recovery_rates = {
            'normal_day': 0.7,      # 通常の休日での回復率（70%）
            'weekend': 0.8,         # 週末での回復率（80%）
            'consecutive_off': 0.9,  # 連続休日での回復率（90%）
        }
        
        # 疲労閾値（産業医学基準）
        self.fatigue_thresholds = {
            'normal': 0.3,      # 正常範囲（30%未満）
            'caution': 0.5,     # 注意レベル（30-50%）
            'warning': 0.7,     # 警告レベル（50-70%）
            'danger': 0.8,      # 危険レベル（70%以上）
        }
        
    def calculate_scientific_fatigue(self, shift_data: pd.DataFrame) -> pd.DataFrame:
        """科学的根拠に基づく疲労度計算"""
        result_df = shift_data.copy()
        result_df['fatigue_score'] = 0.0
        result_df['risk_level'] = 'normal'
        
        for staff in result_df['staff'].unique():
            staff_data = result_df[result_df['staff'] == staff].sort_values('date')
            staff_fatigue = self._calculate_staff_fatigue(staff_data)
            result_df.loc[result_df['staff'] == staff, 'fatigue_score'] = staff_fatigue['fatigue_score']
            result_df.loc[result_df['staff'] == staff, 'risk_level'] = staff_fatigue['risk_level']
            
        return result_df
    
    def _calculate_staff_fatigue(self, staff_data: pd.DataFrame) -> pd.DataFrame:
        """個人別疲労度計算"""
        staff_data = staff_data.copy()
        fatigue_scores = []
        
        for i, row in staff_data.iterrows():
            # 1. 連続勤務日数の疲労（指数的増加）
            consecutive_days = self._get_consecutive_days(staff_data, i)
            consecutive_fatigue = self._consecutive_days_fatigue(consecutive_days)
            
            # 2. 夜勤による疲労
            night_fatigue = self._night_shift_fatigue(row, staff_data, i)
            
            # 3. 週間労働時間による疲労
            weekly_fatigue = self._weekly_hours_fatigue(staff_data, i)
            
            # 4. シフト不規則性による疲労
            irregularity_fatigue = self._shift_irregularity_fatigue(staff_data, i)
            
            # 5. 前日からの疲労回復
            previous_fatigue = fatigue_scores[-1] if fatigue_scores else 0
            recovered_fatigue = self._apply_recovery(previous_fatigue, row)
            
            # 総合疲労度（重み付き合計）
            daily_fatigue = (
                consecutive_fatigue * self.fatigue_weights['consecutive_days'] +
                night_fatigue * self.fatigue_weights['night_shift_load'] +
                weekly_fatigue * self.fatigue_weights['weekly_hours'] +
                irregularity_fatigue * self.fatigue_weights['shift_irregularity']
            )
            
            # 累積疲労（回復考慮）
            total_fatigue = min(1.0, recovered_fatigue + daily_fatigue)
            fatigue_scores.append(total_fatigue)
        
        staff_data['fatigue_score'] = fatigue_scores
        staff_data['risk_level'] = staff_data['fatigue_score'].apply(self._classify_risk_level)
        
        return staff_data
    
    def _consecutive_days_fatigue(self, consecutive_days: int) -> float:
        """連続勤務日数による疲労（指数的増加）"""
        # 労働科学：3日目から急激な疲労蓄積
        if consecutive_days <= 2:
            return consecutive_days * 0.1
        else:
            return min(1.0, 0.2 + (consecutive_days - 2) ** 1.5 * 0.15)
    
    def _night_shift_fatigue(self, current_row: pd.Series, staff_data: pd.DataFrame, current_idx: int) -> float:
        """夜勤による疲労（概日リズム考慮）"""
        fatigue = 0.0
        
        # 当日夜勤
        if current_row.get('is_night_shift', 0):
            fatigue += 0.4
        
        # 過去3日間の夜勤回数（概日リズム回復期間）
        past_3_days = staff_data.iloc[max(0, current_idx-3):current_idx]
        night_count = past_3_days.get('is_night_shift', pd.Series([])).sum()
        fatigue += night_count * 0.15
        
        return min(1.0, fatigue)
    
    def _weekly_hours_fatigue(self, staff_data: pd.DataFrame, current_idx: int) -> float:
        """週間労働時間による疲労（非線形）"""
        # 過去7日間の労働時間
        past_week = staff_data.iloc[max(0, current_idx-6):current_idx+1]
        weekly_hours = past_week.get('work_hours', pd.Series([])).sum()
        
        # 労働基準法：40時間/週を基準とした非線形疲労
        if weekly_hours <= 40:
            return weekly_hours / 40 * 0.3
        else:
            # 40時間超過分は指数的疲労増加
            excess_hours = weekly_hours - 40
            return min(1.0, 0.3 + (excess_hours / 10) ** 1.3 * 0.4)
    
    def _shift_irregularity_fatigue(self, staff_data: pd.DataFrame, current_idx: int) -> float:
        """シフト不規則性による疲労"""
        if current_idx < 3:
            return 0.0
        
        # 過去4日間の出勤時間の分散
        past_4_days = staff_data.iloc[current_idx-3:current_idx+1]
        start_times = past_4_days.get('start_time_variance', pd.Series([]))
        
        if len(start_times) < 4:
            return 0.0
        
        # 時間のバラツキが大きいほど疲労
        variance = start_times.var()
        return min(1.0, variance / 4.0)  # 4時間分散を最大値と仮定
    
    def _apply_recovery(self, previous_fatigue: float, current_row: pd.Series) -> float:
        """疲労回復の適用"""
        if previous_fatigue == 0:
            return 0
        
        is_working = current_row.get('work_hours', 0) > 0
        is_weekend = current_row.get('is_weekend', 0)
        
        if not is_working:  # 休日
            if is_weekend:
                recovery_rate = self.recovery_rates['weekend']
            else:
                recovery_rate = self.recovery_rates['normal_day']
        else:
            recovery_rate = 0.1  # 労働日の軽微な回復
        
        return previous_fatigue * (1 - recovery_rate)
    
    def _get_consecutive_days(self, staff_data: pd.DataFrame, current_idx: int) -> int:
        """連続勤務日数の計算"""
        consecutive = 0
        for i in range(current_idx, -1, -1):
            if staff_data.iloc[i].get('work_hours', 0) > 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    def _classify_risk_level(self, fatigue_score: float) -> str:
        """疲労度によるリスク分類"""
        if fatigue_score < self.fatigue_thresholds['normal']:
            return 'normal'
        elif fatigue_score < self.fatigue_thresholds['caution']:
            return 'caution'
        elif fatigue_score < self.fatigue_thresholds['warning']:
            return 'warning'
        else:
            return 'danger'
    
    def predict_future_fatigue(self, current_data: pd.DataFrame, future_shifts: pd.DataFrame) -> Dict:
        """将来の疲労度予測"""
        predictions = {}
        
        for staff in current_data['staff'].unique():
            staff_current = current_data[current_data['staff'] == staff]
            staff_future = future_shifts[future_shifts['staff'] == staff]
            
            # 現在の疲労度を取得
            current_fatigue = staff_current['fatigue_score'].iloc[-1] if len(staff_current) > 0 else 0
            
            # 将来のシフトに基づく疲労予測
            future_fatigue = self._predict_staff_fatigue(staff_current, staff_future, current_fatigue)
            
            predictions[staff] = {
                'current_fatigue': current_fatigue,
                'predicted_fatigue': future_fatigue,
                'risk_trend': self._analyze_risk_trend(staff_current['fatigue_score'].tolist() + future_fatigue),
                'recommendations': self._generate_recommendations(future_fatigue)
            }
        
        return predictions
    
    def _predict_staff_fatigue(self, current_data: pd.DataFrame, future_shifts: pd.DataFrame, current_fatigue: float) -> list:
        """個人の将来疲労度予測"""
        # 簡略化された予測（実際にはより複雑な時系列予測を使用）
        fatigue_progression = [current_fatigue]
        
        for _, shift in future_shifts.iterrows():
            prev_fatigue = fatigue_progression[-1]
            
            # 簡易的な疲労増減計算
            if shift.get('work_hours', 0) > 0:
                daily_increase = 0.1 + (shift.get('is_night_shift', 0) * 0.2)
                next_fatigue = min(1.0, prev_fatigue + daily_increase)
            else:
                # 休日の回復
                next_fatigue = prev_fatigue * 0.7
            
            fatigue_progression.append(next_fatigue)
        
        return fatigue_progression[1:]  # 現在値を除く
    
    def _analyze_risk_trend(self, fatigue_series: list) -> str:
        """リスク傾向の分析"""
        if len(fatigue_series) < 2:
            return 'stable'
        
        recent_trend = np.mean(fatigue_series[-3:]) - np.mean(fatigue_series[-6:-3])
        
        if recent_trend > 0.1:
            return 'increasing'
        elif recent_trend < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_recommendations(self, future_fatigue: list) -> list:
        """疲労度に基づく推奨事項"""
        recommendations = []
        max_fatigue = max(future_fatigue) if future_fatigue else 0
        
        if max_fatigue > self.fatigue_thresholds['danger']:
            recommendations.append('緊急：連続勤務の制限が必要')
            recommendations.append('産業医面談の実施')
        elif max_fatigue > self.fatigue_thresholds['warning']:
            recommendations.append('注意：夜勤回数の調整を検討')
            recommendations.append('十分な休息時間の確保')
        elif max_fatigue > self.fatigue_thresholds['caution']:
            recommendations.append('観察：疲労度の継続監視')
        
        return recommendations


def create_improved_fatigue_engine():
    """改善された疲労予測エンジンの作成"""
    return ScientificFatiguePredictionEngine()


if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample_data = pd.DataFrame({
        'staff': ['A', 'A', 'A', 'A', 'A'],
        'date': pd.date_range('2025-01-01', periods=5),
        'work_hours': [8, 8, 10, 8, 0],  # 最後は休日
        'is_night_shift': [0, 1, 1, 0, 0],
        'start_time_variance': [1, 3, 2, 1, 0],
        'is_weekend': [0, 0, 0, 0, 1]
    })
    
    engine = ScientificFatiguePredictionEngine()
    result = engine.calculate_scientific_fatigue(sample_data)
    
    print("改善された疲労予測結果:")
    print(result[['date', 'fatigue_score', 'risk_level']])