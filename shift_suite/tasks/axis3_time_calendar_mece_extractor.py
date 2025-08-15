"""
軸3(時間・カレンダールール)専用 MECE事実抽出システム
過去シフト実績から時間・カレンダーに関する運用ルール・制約を網羅的に事実ベースで抽出

主な抽出範囲：
- 祝日・特別日の勤務パターン
- 季節性・月次変動パターン
- 時間帯別運用ルール
- 週末・平日の違い
- 年間カレンダー制約
- 時間枠制約
- 繁忙期・閑散期パターン
- カレンダー依存制約
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime, time, timedelta, date
import pandas as pd
import numpy as np
import calendar
import json

from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS

log = logging.getLogger(__name__)


class TimeCalendarMECEFactExtractor:
    """軸3(時間・カレンダールール)のMECE完全事実抽出システム"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.sample_size_minimum = 5
        self.seasonal_analysis_threshold = 30  # 季節性分析に必要な最低日数
        
        # 日本の一般的な祝日（基本セット）
        self.common_holidays = {
            'new_year': ['1-1', '1-2', '1-3'],
            'golden_week': ['4-29', '5-3', '5-4', '5-5'],
            'summer_holidays': ['8-11', '8-12', '8-13', '8-14', '8-15', '8-16'],
            'autumn_holidays': ['9-23', '11-23'],
            'year_end': ['12-29', '12-30', '12-31']
        }
        
    def _convert_to_json_serializable(self, obj):
        """numpy型をJSONシリアライズ可能な型に変換"""
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        return obj
        
    def extract_axis3_time_calendar_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """軸3: 時間・カレンダールールの完全MECE事実抽出
        
        Args:
            long_df: 長形式シフトデータ
            wt_df: 勤務区分データ（オプション）
            
        Returns:
            Dict containing:
            - human_readable: 人間確認用MECE構造化事実
            - machine_readable: AI実行用制約データ  
            - training_data: 学習データ用特徴量
        """
        log.info("軸3(時間・カレンダールール) MECE事実抽出を開始...")
        
        if long_df.empty:
            return self._empty_result()
            
        # 日付・時間データの前処理
        processed_df = self._preprocess_datetime_data(long_df)
        
        # MECE分解による時間・カレンダー制約抽出
        time_calendar_facts = {
            "祝日・特別日制約": self._extract_holiday_special_day_constraints(processed_df),
            "季節性・月次制約": self._extract_seasonal_monthly_constraints(processed_df),
            "曜日・週次制約": self._extract_weekday_weekly_constraints(processed_df),
            "時間帯制約": self._extract_time_slot_constraints(processed_df),
            "繁忙期・閑散期制約": self._extract_busy_quiet_period_constraints(processed_df),
            "年間カレンダー制約": self._extract_annual_calendar_constraints(processed_df),
            "時間枠・間隔制約": self._extract_time_frame_interval_constraints(processed_df),
            "カレンダー依存制約": self._extract_calendar_dependent_constraints(processed_df),
        }
        
        result = {
            "human_readable": self._format_for_human_confirmation(time_calendar_facts, processed_df),
            "machine_readable": self._format_for_ai_execution(time_calendar_facts),
            "training_data": self._format_for_training(time_calendar_facts, processed_df),
            "extraction_metadata": self._generate_metadata(processed_df, time_calendar_facts)
        }
        
        # JSON シリアライズ可能な形式に変換
        return self._convert_to_json_serializable(result)
    
    def _preprocess_datetime_data(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """日付・時間データの前処理"""
        df = long_df.copy()
        
        # 日付・時間関連カラムの追加
        df['year'] = df['ds'].dt.year
        df['month'] = df['ds'].dt.month
        df['day'] = df['ds'].dt.day
        df['weekday'] = df['ds'].dt.dayofweek  # 0=月曜日
        df['week_of_year'] = df['ds'].dt.isocalendar().week
        df['day_of_year'] = df['ds'].dt.dayofyear
        df['hour'] = df['ds'].dt.hour
        df['quarter'] = df['ds'].dt.quarter
        
        # 曜日名追加
        df['weekday_name'] = df['ds'].dt.day_name()
        df['weekday_name_jp'] = df['weekday'].map({
            0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'
        })
        
        # 週末・平日フラグ
        df['is_weekend'] = df['weekday'].isin([5, 6])  # 土日
        df['is_weekday'] = ~df['is_weekend']
        
        # 月日文字列（祝日判定用）
        df['month_day'] = df['month'].astype(str) + '-' + df['day'].astype(str)
        
        # 祝日・特別日フラグ（基本的な判定）
        df['is_holiday'] = df['month_day'].isin([
            item for sublist in self.common_holidays.values() 
            for item in sublist
        ])
        
        # 四半期開始・終了フラグ
        df['is_quarter_start'] = df['month'].isin([1, 4, 7, 10]) & (df['day'] == 1)
        df['is_quarter_end'] = df['month'].isin([3, 6, 9, 12]) & (
            df['day'] == df['ds'].dt.days_in_month
        )
        
        # 月初・月末フラグ
        df['is_month_start'] = df['day'] <= 3
        df['is_month_end'] = df['day'] >= (df['ds'].dt.days_in_month - 2)
        
        return df
    
    def _extract_holiday_special_day_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """祝日・特別日制約の抽出"""
        facts = {
            "祝日勤務パターン": [],
            "特別日制約": [],
            "連休対応": [],
            "年末年始制約": []
        }
        
        if df.empty:
            return facts
        
        # 祝日の勤務パターン分析
        holiday_data = df[df['is_holiday'] == True]
        regular_data = df[df['is_holiday'] == False]
        
        if len(holiday_data) > 0 and len(regular_data) > 0:
            # 祝日の勤務密度
            holiday_work_ratio = (holiday_data['parsed_slots_count'] > 0).mean()
            regular_work_ratio = (regular_data['parsed_slots_count'] > 0).mean()
            
            ratio_diff = holiday_work_ratio - regular_work_ratio
            
            if abs(ratio_diff) > 0.2:  # 20%以上の差がある場合
                pattern_type = "祝日勤務増加" if ratio_diff > 0 else "祝日勤務減少"
                facts["祝日勤務パターン"].append({
                    "制約タイプ": pattern_type,
                    "詳細": f"祝日の勤務密度が通常より{abs(ratio_diff):.1%}{'高い' if ratio_diff > 0 else '低い'}",
                    "祝日勤務率": round(holiday_work_ratio, 3),
                    "通常勤務率": round(regular_work_ratio, 3),
                    "差分": round(ratio_diff, 3),
                    "分析対象祝日数": len(holiday_data['ds'].dt.date.unique()),
                    "確信度": min(1.0, len(holiday_data) / 20),
                    "事実性": "実績ベース確定"
                })
        
        # 年末年始パターン分析
        year_end_data = df[df['month_day'].isin(['12-29', '12-30', '12-31', '1-1', '1-2', '1-3'])]
        if len(year_end_data) > 0:
            year_end_work_ratio = (year_end_data['parsed_slots_count'] > 0).mean()
            
            if year_end_work_ratio < 0.3:
                facts["年末年始制約"].append({
                    "制約タイプ": "年末年始休業",
                    "詳細": f"年末年始期間の勤務率{year_end_work_ratio:.1%}（大幅減少）",
                    "年末年始勤務率": round(year_end_work_ratio, 3),
                    "確信度": min(1.0, len(year_end_data) / 10),
                    "事実性": "実績ベース確定"
                })
            elif year_end_work_ratio > 0.8:
                facts["年末年始制約"].append({
                    "制約タイプ": "年末年始通常営業",
                    "詳細": f"年末年始期間も通常レベルの勤務率{year_end_work_ratio:.1%}",
                    "年末年始勤務率": round(year_end_work_ratio, 3),
                    "確信度": min(1.0, len(year_end_data) / 10),
                    "事実性": "実績ベース確定"
                })
        
        return facts
    
    def _extract_seasonal_monthly_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """季節性・月次制約の抽出"""
        facts = {
            "季節変動制約": [],
            "月次変動制約": [],
            "四半期制約": [],
            "年間周期制約": []
        }
        
        if df.empty:
            return facts
        
        # 月別勤務パターン分析
        monthly_work = df[df['parsed_slots_count'] > 0].groupby('month').agg({
            'parsed_slots_count': 'sum',
            'ds': 'count'
        })
        
        if len(monthly_work) >= 6:  # 6ヶ月以上のデータがある場合
            monthly_density = monthly_work['parsed_slots_count'] / monthly_work['ds']
            
            # 変動係数計算
            cv = monthly_density.std() / monthly_density.mean()
            
            if cv > 0.3:  # 変動係数が30%以上
                max_month = monthly_density.idxmax()
                min_month = monthly_density.idxmin()
                
                facts["月次変動制約"].append({
                    "制約タイプ": "月次変動大",
                    "詳細": f"月次勤務密度の変動係数{cv:.2f}（大きな季節変動）",
                    "最大月": f"{max_month}月",
                    "最小月": f"{min_month}月",
                    "変動係数": round(cv, 3),
                    "最大密度": round(monthly_density.max(), 2),
                    "最小密度": round(monthly_density.min(), 2),
                    "確信度": min(1.0, len(monthly_work) / 12),
                    "事実性": "実績ベース確定"
                })
        
        # 四半期パターン分析
        quarterly_work = df[df['parsed_slots_count'] > 0].groupby('quarter').agg({
            'parsed_slots_count': 'sum',
            'ds': 'count'
        })
        
        if len(quarterly_work) >= 2:
            quarterly_density = quarterly_work['parsed_slots_count'] / quarterly_work['ds']
            
            if quarterly_density.std() / quarterly_density.mean() > 0.2:
                max_quarter = quarterly_density.idxmax()
                min_quarter = quarterly_density.idxmin()
                
                facts["四半期制約"].append({
                    "制約タイプ": "四半期変動",
                    "詳細": f"Q{max_quarter}が最繁忙、Q{min_quarter}が最閑散",
                    "最大四半期": f"Q{max_quarter}",
                    "最小四半期": f"Q{min_quarter}",
                    "最大密度": round(quarterly_density.max(), 2),
                    "最小密度": round(quarterly_density.min(), 2),
                    "確信度": min(1.0, len(quarterly_work) / 4),
                    "事実性": "実績ベース確定"
                })
        
        return facts
    
    def _extract_weekday_weekly_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """曜日・週次制約の抽出"""
        facts = {
            "曜日固定制約": [],
            "週末制約": [],
            "週次パターン": [],
            "曜日変動制約": []
        }
        
        if df.empty:
            return facts
        
        # 曜日別勤務パターン分析
        weekday_work = df[df['parsed_slots_count'] > 0].groupby('weekday_name_jp').agg({
            'parsed_slots_count': 'sum',
            'ds': 'count'
        })
        
        if len(weekday_work) > 0:
            weekday_density = weekday_work['parsed_slots_count'] / weekday_work['ds']
            
            # 週末vs平日の比較
            weekend_days = ['土', '日']
            weekday_days = ['月', '火', '水', '木', '金']
            
            weekend_density = weekday_density[weekday_density.index.isin(weekend_days)].mean()
            weekdays_density = weekday_density[weekday_density.index.isin(weekday_days)].mean()
            
            if not pd.isna(weekend_density) and not pd.isna(weekdays_density):
                ratio = weekend_density / weekdays_density
                
                if ratio < 0.5:
                    facts["週末制約"].append({
                        "制約タイプ": "週末勤務大幅減少",
                        "詳細": f"週末の勤務密度が平日の{ratio:.1%}（大幅減少）",
                        "週末密度": round(weekend_density, 2),
                        "平日密度": round(weekdays_density, 2),
                        "比率": round(ratio, 3),
                        "確信度": 0.9,
                        "事実性": "実績ベース確定"
                    })
                elif ratio > 1.5:
                    facts["週末制約"].append({
                        "制約タイプ": "週末勤務増加",
                        "詳細": f"週末の勤務密度が平日の{ratio:.1%}（増加傾向）",
                        "週末密度": round(weekend_density, 2),
                        "平日密度": round(weekdays_density, 2),
                        "比率": round(ratio, 3),
                        "確信度": 0.9,
                        "事実性": "実績ベース確定"
                    })
            
            # 特定曜日の固定パターン検出
            for day_name, density in weekday_density.items():
                if density / weekday_density.mean() > 1.5:  # 平均の1.5倍以上
                    facts["曜日固定制約"].append({
                        "制約タイプ": "特定曜日集中",
                        "詳細": f"{day_name}曜日の勤務密度が平均の{density/weekday_density.mean():.1f}倍",
                        "対象曜日": day_name,
                        "密度": round(density, 2),
                        "平均密度": round(weekday_density.mean(), 2),
                        "倍率": round(density/weekday_density.mean(), 2),
                        "確信度": 0.8,
                        "事実性": "実績ベース確定"
                    })
        
        return facts
    
    def _extract_time_slot_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """時間帯制約の抽出"""
        facts = {
            "営業時間制約": [],
            "時間帯固定制約": [],
            "夜間・早朝制約": [],
            "時間集中制約": []
        }
        
        if df.empty:
            return facts
        
        # 時間帯別勤務パターン分析
        hourly_work = df[df['parsed_slots_count'] > 0].groupby('hour').size()
        
        if len(hourly_work) > 0:
            # 営業時間の推定
            total_work = hourly_work.sum()
            cumulative_ratio = hourly_work.cumsum() / total_work
            
            # 開始時間：累積5%に達する時間
            start_hour = cumulative_ratio[cumulative_ratio >= 0.05].index[0] if len(cumulative_ratio[cumulative_ratio >= 0.05]) > 0 else hourly_work.index.min()
            
            # 終了時間：累積95%に達する時間
            end_hour = cumulative_ratio[cumulative_ratio >= 0.95].index[0] if len(cumulative_ratio[cumulative_ratio >= 0.95]) > 0 else hourly_work.index.max()
            
            facts["営業時間制約"].append({
                "制約タイプ": "実質営業時間",
                "詳細": f"{start_hour}:00-{end_hour}:00の時間帯で全勤務の90%を占める",
                "開始時間": start_hour,
                "終了時間": end_hour,
                "営業時間": end_hour - start_hour + 1,
                "確信度": 0.9,
                "事実性": "実績ベース推定"
            })
            
            # 夜間勤務の検出（22:00-6:00）
            night_hours = list(range(22, 24)) + list(range(0, 6))
            night_work = hourly_work[hourly_work.index.isin(night_hours)].sum()
            night_ratio = night_work / total_work
            
            if night_ratio > 0.1:  # 夜間勤務が10%以上
                facts["夜間・早朝制約"].append({
                    "制約タイプ": "夜間勤務あり",
                    "詳細": f"夜間時間帯(22:00-6:00)で全勤務の{night_ratio:.1%}",
                    "夜間勤務比率": round(night_ratio, 3),
                    "夜間勤務時間数": len([h for h in night_hours if h in hourly_work.index and hourly_work[h] > 0]),
                    "確信度": 0.8,
                    "事実性": "実績ベース確定"
                })
            
            # 時間集中の検出
            max_hour = hourly_work.idxmax()
            max_ratio = hourly_work.max() / total_work
            
            if max_ratio > 0.2:  # 特定時間に20%以上集中
                facts["時間集中制約"].append({
                    "制約タイプ": "時間集中",
                    "詳細": f"{max_hour}:00の時間帯に全勤務の{max_ratio:.1%}が集中",
                    "集中時間": max_hour,
                    "集中率": round(max_ratio, 3),
                    "確信度": 0.8,
                    "事実性": "実績ベース確定"
                })
        
        return facts
    
    def _extract_busy_quiet_period_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """繁忙期・閑散期制約の抽出"""
        facts = {
            "繁忙期制約": [],
            "閑散期制約": [],
            "需要変動制約": [],
            "負荷調整制約": []
        }
        
        if df.empty:
            return facts
        
        # 日別勤務量の計算
        daily_work = df[df['parsed_slots_count'] > 0].groupby(df['ds'].dt.date).agg({
            'parsed_slots_count': 'sum',
            'staff': 'nunique'
        })
        
        if len(daily_work) >= 30:  # 30日以上のデータがある場合
            work_intensity = daily_work['parsed_slots_count']
            
            # 繁忙期・閑散期の検出（上位/下位20%）
            q80 = work_intensity.quantile(0.8)
            q20 = work_intensity.quantile(0.2)
            
            busy_days = work_intensity[work_intensity >= q80]
            quiet_days = work_intensity[work_intensity <= q20]
            
            if len(busy_days) > 0:
                # 繁忙期の月分布分析
                busy_dates = pd.to_datetime(busy_days.index)
                busy_months = busy_dates.month.value_counts()
                
                if len(busy_months) > 0:
                    dominant_busy_month = busy_months.idxmax()
                    busy_concentration = busy_months.max() / len(busy_days)
                    
                    if busy_concentration > 0.3:  # 30%以上が特定月に集中
                        facts["繁忙期制約"].append({
                            "制約タイプ": "月次繁忙期",
                            "詳細": f"{dominant_busy_month}月に繁忙日の{busy_concentration:.1%}が集中",
                            "繁忙月": dominant_busy_month,
                            "繁忙日数": len(busy_days),
                            "集中率": round(busy_concentration, 3),
                            "平均勤務量": round(busy_days.mean(), 1),
                            "確信度": min(1.0, len(busy_days) / 10),
                            "事実性": "実績ベース推定"
                        })
            
            if len(quiet_days) > 0:
                # 閑散期の月分布分析
                quiet_dates = pd.to_datetime(quiet_days.index)
                quiet_months = quiet_dates.month.value_counts()
                
                if len(quiet_months) > 0:
                    dominant_quiet_month = quiet_months.idxmax()
                    quiet_concentration = quiet_months.max() / len(quiet_days)
                    
                    if quiet_concentration > 0.3:
                        facts["閑散期制約"].append({
                            "制約タイプ": "月次閑散期",
                            "詳細": f"{dominant_quiet_month}月に閑散日の{quiet_concentration:.1%}が集中",
                            "閑散月": dominant_quiet_month,
                            "閑散日数": len(quiet_days),
                            "集中率": round(quiet_concentration, 3),
                            "平均勤務量": round(quiet_days.mean(), 1),
                            "確信度": min(1.0, len(quiet_days) / 10),
                            "事実性": "実績ベース推定"
                        })
        
        return facts
    
    def _extract_annual_calendar_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """年間カレンダー制約の抽出"""
        facts = {
            "年度制約": [],
            "学校カレンダー連動": [],
            "行事・イベント制約": [],
            "年間スケジュール制約": []
        }
        
        if df.empty:
            return facts
        
        # 年度区切りの検出（3月末・4月初の変化）
        if df['month'].isin([3, 4]).any():
            march_data = df[(df['month'] == 3) & (df['parsed_slots_count'] > 0)]
            april_data = df[(df['month'] == 4) & (df['parsed_slots_count'] > 0)]
            
            if len(march_data) > 0 and len(april_data) > 0:
                march_intensity = len(march_data) / df[df['month'] == 3]['ds'].dt.date.nunique()
                april_intensity = len(april_data) / df[df['month'] == 4]['ds'].dt.date.nunique()
                
                change_ratio = abs(april_intensity - march_intensity) / march_intensity
                
                if change_ratio > 0.3:  # 30%以上の変化
                    change_type = "年度開始増加" if april_intensity > march_intensity else "年度末減少"
                    facts["年度制約"].append({
                        "制約タイプ": change_type,
                        "詳細": f"3月→4月で勤務密度が{change_ratio:.1%}変化",
                        "3月密度": round(march_intensity, 2),
                        "4月密度": round(april_intensity, 2),
                        "変化率": round(change_ratio, 3),
                        "確信度": 0.7,
                        "事実性": "実績ベース推定"
                    })
        
        return facts
    
    def _extract_time_frame_interval_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """時間枠・間隔制約の抽出"""
        facts = {
            "勤務間隔制約": [],
            "連続勤務制約": [],
            "時間枠制約": [],
            "勤務長制約": []
        }
        
        if df.empty:
            return facts
        
        # スタッフ別の勤務間隔分析
        if 'staff' in df.columns:
            staff_work_times = df[df['parsed_slots_count'] > 0].groupby('staff')['ds'].apply(list)
            
            for staff, work_times in staff_work_times.items():
                if len(work_times) >= 3:
                    work_times = sorted(work_times)
                    intervals = [(work_times[i+1] - work_times[i]).total_seconds() / 3600 
                               for i in range(len(work_times) - 1)]
                    
                    # 最小間隔の検出
                    min_interval = min(intervals)
                    if min_interval >= 8:  # 8時間以上の間隔
                        facts["勤務間隔制約"].append({
                            "制約タイプ": "最小勤務間隔",
                            "詳細": f"スタッフ{staff}の最小勤務間隔{min_interval:.1f}時間",
                            "スタッフ": staff,
                            "最小間隔": round(min_interval, 1),
                            "平均間隔": round(np.mean(intervals), 1),
                            "確信度": min(1.0, len(intervals) / 10),
                            "事実性": "実績ベース推定"
                        })
        
        return facts
    
    def _extract_calendar_dependent_constraints(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """カレンダー依存制約の抽出"""
        facts = {
            "月末月初制約": [],
            "連休制約": [],
            "特定日制約": [],
            "カレンダー周期制約": []
        }
        
        if df.empty:
            return facts
        
        # 月末・月初パターンの分析
        month_start_data = df[df['is_month_start'] == True]
        month_end_data = df[df['is_month_end'] == True]
        regular_data = df[(df['is_month_start'] == False) & (df['is_month_end'] == False)]
        
        if len(month_start_data) > 0 and len(regular_data) > 0:
            start_work_ratio = (month_start_data['parsed_slots_count'] > 0).mean()
            regular_work_ratio = (regular_data['parsed_slots_count'] > 0).mean()
            
            ratio_diff = start_work_ratio - regular_work_ratio
            
            if abs(ratio_diff) > 0.2:
                pattern_type = "月初勤務増加" if ratio_diff > 0 else "月初勤務減少"
                facts["月末月初制約"].append({
                    "制約タイプ": pattern_type,
                    "詳細": f"月初の勤務密度が通常より{abs(ratio_diff):.1%}{'高い' if ratio_diff > 0 else '低い'}",
                    "月初勤務率": round(start_work_ratio, 3),
                    "通常勤務率": round(regular_work_ratio, 3),
                    "差分": round(ratio_diff, 3),
                    "確信度": 0.7,
                    "事実性": "実績ベース推定"
                })
        
        return facts
    
    def _format_for_human_confirmation(self, time_calendar_facts: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """人間確認用のMECE構造化フォーマット"""
        formatted = {
            "抽出事実サマリー": {},
            "MECE分解事実": {},
            "時間カレンダー分析": {},
            "確信度別分類": {"高確信度": [], "中確信度": [], "低確信度": []},
            "要確認事項": []
        }
        
        total_facts = 0
        for category, subcategories in time_calendar_facts.items():
            category_facts = []
            for subcategory, facts in subcategories.items():
                total_facts += len(facts)
                for fact in facts:
                    confidence = fact.get('確信度', 0.5)
                    fact_summary = {
                        "カテゴリー": category,
                        "サブカテゴリー": subcategory,
                        "詳細": fact,
                        "確信度": confidence
                    }
                    
                    if confidence >= 0.8:
                        formatted["確信度別分類"]["高確信度"].append(fact_summary)
                    elif confidence >= 0.5:
                        formatted["確信度別分類"]["中確信度"].append(fact_summary)
                    else:
                        formatted["確信度別分類"]["低確信度"].append(fact_summary)
                
                category_facts.extend(facts)
            
            formatted["MECE分解事実"][category] = category_facts
            formatted["抽出事実サマリー"][category] = len(category_facts)
        
        formatted["抽出事実サマリー"]["総事実数"] = total_facts
        formatted["抽出事実サマリー"]["分析期間"] = f"{df['ds'].min().date()} - {df['ds'].max().date()}"
        formatted["抽出事実サマリー"]["分析日数"] = df['ds'].dt.date.nunique()
        
        # 時間カレンダー特有の分析
        formatted["時間カレンダー分析"]["営業日数"] = len(df[df['parsed_slots_count'] > 0]['ds'].dt.date.unique())
        formatted["時間カレンダー分析"]["平均日次勤務量"] = round(df[df['parsed_slots_count'] > 0].groupby(df['ds'].dt.date)['parsed_slots_count'].sum().mean(), 1)
        formatted["時間カレンダー分析"]["時間帯カバレッジ"] = len(df[df['parsed_slots_count'] > 0]['hour'].unique())
        
        return formatted
    
    def _format_for_ai_execution(self, time_calendar_facts: Dict) -> Dict[str, Any]:
        """AI実行用制約データフォーマット"""
        constraints = {
            "time_hard_constraints": [],
            "time_soft_constraints": [],
            "time_preferences": [],
            "calendar_constraints": [],
            "temporal_patterns": []
        }
        
        for category, subcategories in time_calendar_facts.items():
            for subcategory, facts in subcategories.items():
                for fact in facts:
                    confidence = fact.get('確信度', 0.5)
                    
                    constraint = {
                        "id": f"time_{category}_{subcategory}_{len(constraints['time_hard_constraints']) + len(constraints['time_soft_constraints'])}",
                        "type": subcategory,
                        "category": category,
                        "rule": fact,
                        "confidence": confidence,
                        "priority": "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low",
                        "scope": "temporal",
                        "axis": 3
                    }
                    
                    # 時間・カレンダー関連の制約分類
                    if category in ["祝日・特別日制約", "年間カレンダー制約"]:
                        constraints["calendar_constraints"].append(constraint)
                    elif confidence >= 0.8:
                        constraints["time_hard_constraints"].append(constraint)
                    elif confidence >= 0.5:
                        constraints["time_soft_constraints"].append(constraint)
                    else:
                        constraints["time_preferences"].append(constraint)
        
        return constraints
    
    def _format_for_training(self, time_calendar_facts: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """学習データ用特徴量フォーマット"""
        features = {
            "temporal_features": [],
            "calendar_features": [],
            "seasonal_features": [],
            "statistical_features": {}
        }
        
        # 時間・カレンダー統計特徴量
        temporal_stats = {
            "work_hours_range": [df[df['parsed_slots_count'] > 0]['hour'].min(), 
                               df[df['parsed_slots_count'] > 0]['hour'].max()],
            "monthly_variation": df[df['parsed_slots_count'] > 0].groupby('month').size().std(),
            "weekday_variation": df[df['parsed_slots_count'] > 0].groupby('weekday').size().std(),
            "holiday_work_ratio": (df[df['is_holiday']]['parsed_slots_count'] > 0).mean(),
            "weekend_work_ratio": (df[df['is_weekend']]['parsed_slots_count'] > 0).mean()
        }
        
        features["statistical_features"]["temporal_stats"] = temporal_stats
        
        return features
    
    def _generate_metadata(self, df: pd.DataFrame, time_calendar_facts: Dict) -> Dict[str, Any]:
        """抽出メタデータ生成"""
        return {
            "extraction_timestamp": datetime.now().isoformat(),
            "axis": 3,
            "axis_name": "時間・カレンダールール",
            "data_period": {
                "start": df['ds'].min().isoformat(),
                "end": df['ds'].max().isoformat(),
                "total_days": (df['ds'].max() - df['ds'].min()).days,
                "working_days": df[df['parsed_slots_count'] > 0]['ds'].dt.date.nunique()
            },
            "data_quality": {
                "total_records": len(df),
                "working_records": len(df[df['parsed_slots_count'] > 0]),
                "time_coverage_hours": len(df[df['parsed_slots_count'] > 0]['hour'].unique()),
                "calendar_coverage_months": len(df['month'].unique()),
                "weekend_coverage": df['is_weekend'].sum() > 0,
                "holiday_coverage": df['is_holiday'].sum() > 0
            },
            "extraction_coverage": {
                category: sum(len(facts) for facts in subcategories.values())
                for category, subcategories in time_calendar_facts.items()
            }
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """空のデータ用の結果"""
        return {
            "human_readable": {"抽出事実サマリー": {"総事実数": 0, "分析日数": 0}},
            "machine_readable": {"time_hard_constraints": [], "time_soft_constraints": [], "time_preferences": []},
            "training_data": {"temporal_features": [], "statistical_features": {}},
            "extraction_metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "axis": 3,
                "data_quality": {"total_records": 0, "working_days": 0}
            }
        }