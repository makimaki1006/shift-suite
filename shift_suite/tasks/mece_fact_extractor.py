"""
軸1(施設ルール)専用 MECE事実抽出システム
過去シフト実績から施設固有の運用ルールを網羅的に事実ベースで抽出

主な抽出範囲：
- 勤務体制・時間帯制約
- 人員配置・組み合わせルール  
- 空白時間・連続性制約
- 役職・レベル別運用ルール
- 曜日・時期別運用パターン
- 特殊業務・イベント対応
- リスク・安全性配慮
- 業務継続性・引き継ぎルール
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np

from .constants import STATISTICAL_THRESHOLDS, DEFAULT_SLOT_MINUTES
from .utils import validate_and_convert_slot_minutes, safe_slot_calculation

log = logging.getLogger(__name__)


class MECEFactExtractor:
    """軸1(施設ルール)のMECE完全事実抽出システム"""
    
    def __init__(self, slot_minutes: int = 30):
        self.confidence_threshold = 0.7
        self.sample_size_minimum = 5
        self.slot_hours = validate_and_convert_slot_minutes(slot_minutes, "MECEFactExtractor.__init__")
        self.slot_minutes = slot_minutes
        log.info(f"[MECEFactExtractor] 初期化: スロット{slot_minutes}分={self.slot_hours}時間")
        
    def extract_axis1_facility_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """軸1: 施設ルールの完全MECE事実抽出
        
        Returns:
            Dict containing:
            - human_readable: 人間確認用MECE構造化事実
            - machine_readable: AI実行用制約データ  
            - training_data: 学習データ用特徴量
        """
        log.info("軸1(施設ルール) MECE事実抽出を開始...")
        
        if long_df.empty:
            return self._empty_result()
            
        # MECE分解による事実抽出（不足カテゴリー補完済み）
        facility_facts = {
            "勤務体制制約": self._extract_work_system_constraints(long_df, wt_df),
            "人員配置制約": self._extract_staffing_constraints(long_df),
            "時間制約": self._extract_time_constraints(long_df, wt_df),
            "組み合わせ制約": self._extract_combination_constraints(long_df),
            "継続性制約": self._extract_continuity_constraints(long_df),
            "役職制約": self._extract_role_constraints(long_df),
            "周期性制約": self._extract_periodic_constraints(long_df),
            "例外制約": self._extract_exception_constraints(long_df),
            # === 不足していたカテゴリーの補完 ===
            "設備制約": self._extract_facility_equipment_constraints(long_df),
            "業務範囲制約": self._extract_business_scope_constraints(long_df),
            "施設特性制約": self._extract_facility_characteristics_constraints(long_df),
            "エリア制約": self._extract_area_constraints(long_df),
            "運用時間制約": self._extract_operation_time_constraints(long_df, wt_df),
            "配置基準制約": self._extract_placement_standard_constraints(long_df),
            "役割定義制約": self._extract_role_definition_constraints(long_df),
            "協力体制制約": self._extract_cooperation_system_constraints(long_df),
        }
        
        return {
            "human_readable": self._format_for_human_confirmation(facility_facts),
            "machine_readable": self._format_for_ai_execution(facility_facts),
            "training_data": self._format_for_training(facility_facts, long_df),
            "extraction_metadata": self._generate_metadata(long_df, facility_facts)
        }
        
    def _extract_work_system_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, List[Dict]]:
        """勤務体制・時間帯制約の抽出"""
        facts = {
            "基本勤務時間": [],
            "シフト種別制約": [],
            "時間帯配置制約": [],
            "最低人員制約": []
        }
        
        # 基本勤務時間の事実抽出
        if wt_df is not None and not wt_df.empty:
            for _, row in wt_df.iterrows():
                if row.get('start_parsed') and row.get('end_parsed'):
                    facts["基本勤務時間"].append({
                        "コード": row['code'],
                        "開始時刻": row['start_parsed'],
                        "終了時刻": row['end_parsed'],
                        "勤務時間": safe_slot_calculation(
                            pd.Series([row.get('parsed_slots_count', 0)]), 
                            self.slot_minutes, 
                            "sum", 
                            "extract_work_system_constraints"
                        ),
                        "勤務種別": row.get('holiday_type', '通常勤務'),
                        "事実性": "定義済み",
                        "確信度": 1.0
                    })
        
        # 実績ベースの時間帯配置制約
        hourly_staffing = long_df[long_df['parsed_slots_count'] > 0].groupby(
            long_df['ds'].dt.hour
        )['staff'].nunique().to_dict()
        
        for hour, staff_count in hourly_staffing.items():
            if staff_count >= self.sample_size_minimum:
                facts["時間帯配置制約"].append({
                    "時間帯": f"{hour}:00-{hour+1}:00",
                    "平均人員数": staff_count,
                    "制約種別": "実績ベース最低人員",
                    "事実性": "実績確認済み",
                    "確信度": min(1.0, len(long_df[long_df['ds'].dt.hour == hour]) / 30)
                })
        
        return facts
    
    def _extract_staffing_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """人員配置・組み合わせ制約の抽出"""
        facts = {
            "同時配置制約": [],
            "排他配置制約": [],
            "最小配置制約": [],
            "役割分担制約": []
        }
        
        # 同時勤務の分析
        daily_groups = long_df[long_df['parsed_slots_count'] > 0].groupby([
            long_df['ds'].dt.date, long_df['ds'].dt.hour
        ])['staff'].apply(list)
        
        staff_pair_counts = defaultdict(int)
        staff_total_hours = long_df.groupby('staff')['ds'].count()
        
        for staff_list in daily_groups:
            if len(staff_list) >= 2:
                from itertools import combinations
                for staff1, staff2 in combinations(sorted(set(staff_list)), 2):
                    staff_pair_counts[(staff1, staff2)] += 1
        
        # 強制同時配置の検出
        for (staff1, staff2), co_occurrence in staff_pair_counts.items():
            if staff1 in staff_total_hours.index and staff2 in staff_total_hours.index:
                staff1_hours = staff_total_hours[staff1]
                staff2_hours = staff_total_hours[staff2]
                
                expected_co_occurrence = min(staff1_hours, staff2_hours) * 0.1  # 期待値
                
                if co_occurrence > expected_co_occurrence * 3:  # 3倍以上
                    facts["同時配置制約"].append({
                        "スタッフ1": staff1,
                        "スタッフ2": staff2,
                        "実績同時勤務回数": co_occurrence,
                        "期待値": round(expected_co_occurrence, 1),
                        "制約種別": "強制同時配置",
                        "事実性": "実績ベース推定",
                        "確信度": min(1.0, co_occurrence / 10)
                    })
        
        return facts
    
    def _extract_time_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, List[Dict]]:
        """時間制約（連続性、間隔、境界）の抽出"""
        facts = {
            "連続勤務制約": [],
            "休憩間隔制約": [],
            "勤務境界制約": [],
            "跨ぎ制約": []
        }
        
        # スタッフ別の連続勤務パターン分析
        for staff in long_df['staff'].unique():
            if not staff:
                continue
                
            staff_df = long_df[
                (long_df['staff'] == staff) & 
                (long_df['parsed_slots_count'] > 0)
            ].sort_values('ds')
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 連続勤務日数の分析
            staff_df['date'] = staff_df['ds'].dt.date
            consecutive_days = self._calculate_consecutive_days(staff_df['date'].unique())
            
            if consecutive_days:
                max_consecutive = max(consecutive_days)
                avg_consecutive = np.mean(consecutive_days)
                
                facts["連続勤務制約"].append({
                    "スタッフ": staff,
                    "最大連続勤務日数": max_consecutive,
                    "平均連続勤務日数": round(avg_consecutive, 1),
                    "制約種別": "実績ベース上限",
                    "事実性": "実績確認済み",
                    "確信度": min(1.0, len(consecutive_days) / 10)
                })
        
        return facts
    
    def _extract_combination_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """組み合わせ制約（職種、雇用形態、経験レベル）の抽出"""
        facts = {
            "職種組み合わせ制約": [],
            "雇用形態制約": [],
            "経験レベル制約": [],
            "バランス制約": []
        }
        
        # 職種組み合わせの分析
        if 'role' in long_df.columns:
            hourly_role_combinations = long_df[long_df['parsed_slots_count'] > 0].groupby([
                long_df['ds'].dt.date, long_df['ds'].dt.hour
            ])['role'].apply(lambda x: sorted(x.unique().tolist()))
            
            role_pattern_counts = defaultdict(int)
            for role_combination in hourly_role_combinations:
                if len(role_combination) > 1:
                    role_pattern_counts[tuple(role_combination)] += 1
            
            # 頻出する職種組み合わせを制約として抽出
            total_multi_role_hours = sum(role_pattern_counts.values())
            for role_pattern, count in role_pattern_counts.items():
                if count >= self.sample_size_minimum and count / total_multi_role_hours > 0.1:
                    facts["職種組み合わせ制約"].append({
                        "職種組み合わせ": list(role_pattern),
                        "実績回数": count,
                        "全体に占める割合": round(count / total_multi_role_hours, 3),
                        "制約種別": "推奨組み合わせ",
                        "事実性": "実績ベース推定",
                        "確信度": min(1.0, count / 20)
                    })
        
        return facts
    
    def _extract_continuity_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """継続性制約（引き継ぎ、空白時間、業務連続性）の抽出"""
        facts = {
            "引き継ぎ制約": [],
            "空白時間制約": [],
            "業務連続性制約": []
        }
        
        # 時間帯別の人員空白分析
        hourly_coverage = long_df[long_df['parsed_slots_count'] > 0].groupby([
            long_df['ds'].dt.date, long_df['ds'].dt.hour
        ])['staff'].nunique()
        
        zero_coverage_hours = hourly_coverage[hourly_coverage == 0]
        if len(zero_coverage_hours) > 0:
            facts["空白時間制約"].append({
                "空白時間帯数": len(zero_coverage_hours),
                "空白発生パターン": "実績確認済み",
                "制約種別": "人員配置必須時間帯",
                "事実性": "実績逆算",
                "確信度": 1.0
            })
        
        return facts
    
    def _extract_role_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """役職・レベル別運用制約の抽出"""
        facts = {
            "管理職配置制約": [],
            "新人配置制約": [],
            "専門職制約": [],
            "責任者制約": []
        }
        
        if 'role' in long_df.columns:
            role_distribution = long_df[long_df['parsed_slots_count'] > 0]['role'].value_counts()
            
            for role, count in role_distribution.items():
                if count >= self.sample_size_minimum:
                    facts["専門職制約"].append({
                        "職種": role,
                        "総勤務時間": safe_slot_calculation(
                            pd.Series([count]), 
                            self.slot_minutes, 
                            "sum", 
                            "extract_role_constraints"
                        ),
                        "制約種別": "職種別最低配置時間",
                        "事実性": "実績確認済み",
                        "確信度": 1.0
                    })
        
        return facts
    
    def _extract_periodic_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """周期性制約（曜日、月次、季節性）の抽出 - 勤務区分と勤務時間データ統合版"""
        facts = {
            "曜日制約": [],
            "月次制約": [],
            "季節制約": [],
            "週次制約": [],
            "勤務時間周期制約": []  # 新規追加：勤務時間含む分析
        }
        
        # 勤務区分別の周期性パターン分析
        if 'code' in long_df.columns and 'parsed_slots_count' in long_df.columns:
            # 勤務区分別 + 曜日別の複合分析
            worktype_weekday_patterns = long_df[long_df['parsed_slots_count'] > 0].groupby([
                'code', long_df['ds'].dt.dayofweek
            ]).agg({
                'parsed_slots_count': ['count', 'sum'],  # 回数と総勤務時間
                'staff': 'nunique'
            }).round(2)
            
            weekday_names = ['月', '火', '水', '木', '金', '土', '日']
            
            for (code, day_num), data in worktype_weekday_patterns.iterrows():
                shift_count = data[('parsed_slots_count', 'count')]
                total_hours = data[('parsed_slots_count', 'sum')] * (DEFAULT_SLOT_MINUTES / 60.0)
                staff_count = data[('staff', 'nunique')]
                
                if shift_count >= self.sample_size_minimum:
                    total_hours = safe_slot_calculation(
                        data[('parsed_slots_count', 'sum')], 
                        self.slot_minutes, 
                        "sum", 
                        "extract_periodic_constraints"
                    )
                    facts["勤務時間周期制約"].append({
                        "勤務コード": code,
                        "曜日": weekday_names[day_num],
                        "勤務回数": shift_count,
                        "総勤務時間": round(total_hours, 1),
                        "担当スタッフ数": staff_count,
                        "平均勤務時間": round(total_hours / shift_count if shift_count > 0 else 0, 1),
                        "制約種別": "勤務区分別周期パターン",
                        "事実性": "実績確認済み",
                        "確信度": min(1.0, shift_count / 10)
                    })
        
        # 週次パターン（回数+時間の複合分析）
        if 'ds' in long_df.columns:
            long_df_working = long_df[long_df['parsed_slots_count'] > 0].copy()
            long_df_working['week'] = long_df_working['ds'].dt.isocalendar().week
            long_df_working['year'] = long_df_working['ds'].dt.year
            
            weekly_patterns = long_df_working.groupby(['staff', 'year', 'week']).agg({
                'parsed_slots_count': ['count', 'sum'],  # 勤務回数と総時間
                'ds': 'nunique'  # 勤務日数
            })
            
            # 週40時間ルールのチェック
            for staff in weekly_patterns.index.get_level_values('staff').unique():
                staff_weekly = weekly_patterns.loc[staff]
                
                if len(staff_weekly) >= 4:  # 最低4週のデータがある場合
                    weekly_hours = safe_slot_calculation(
                        staff_weekly[('parsed_slots_count', 'sum')], 
                        self.slot_minutes, 
                        "element_wise", 
                        "extract_periodic_constraints_weekly"
                    )
                    over_40h_weeks = (weekly_hours > 40).sum()
                    
                    facts["週次制約"].append({
                        "スタッフ": staff,
                        "分析週数": len(staff_weekly),
                        "平均週間勤務時間": round(weekly_hours.mean(), 1),
                        "40時間超過週数": over_40h_weeks,
                        "超過率": round(over_40h_weeks / len(staff_weekly), 3),
                        "制約種別": "週間労働時間制約",
                        "事実性": "実績ベース推定",
                        "確信度": min(1.0, len(staff_weekly) / 10)
                    })
        
        # 月次パターン（回数+時間の複合分析）
        if 'ds' in long_df.columns:
            long_df_working['month'] = long_df_working['ds'].dt.month
            
            monthly_patterns = long_df_working.groupby(['staff', 'year', 'month']).agg({
                'parsed_slots_count': ['count', 'sum'],  # 勤務回数と総時間
                'ds': 'nunique'  # 勤務日数
            })
            
            # 月160時間ルールのチェック（FTE基準）
            for staff in monthly_patterns.index.get_level_values('staff').unique():
                staff_monthly = monthly_patterns.loc[staff]
                
                if len(staff_monthly) >= 3:  # 最低3ヶ月のデータがある場合
                    monthly_hours = safe_slot_calculation(
                        staff_monthly[('parsed_slots_count', 'sum')], 
                        self.slot_minutes, 
                        "element_wise", 
                        "extract_periodic_constraints_monthly"
                    )
                    over_160h_months = (monthly_hours > 160).sum()
                    
                    facts["月次制約"].append({
                        "スタッフ": staff,
                        "分析月数": len(staff_monthly),
                        "平均月間勤務時間": round(monthly_hours.mean(), 1),
                        "160時間超過月数": over_160h_months,
                        "超過率": round(over_160h_months / len(staff_monthly), 3),
                        "制約種別": "月間労働時間制約",
                        "事実性": "実績ベース推定",
                        "確信度": min(1.0, len(staff_monthly) / 6)
                    })
        
        # 従来の曜日別人員配置パターン（強化版）
        if 'ds' in long_df.columns:
            weekday_detailed = long_df[long_df['parsed_slots_count'] > 0].groupby(
                long_df['ds'].dt.dayofweek
            ).agg({
                'staff': 'nunique',
                'parsed_slots_count': ['count', 'sum']
            })
            
            weekday_names = ['月', '火', '水', '木', '金', '土', '日']
            for day_num, data in weekday_detailed.iterrows():
                staff_count = data[('staff', 'nunique')]
                shift_count = data[('parsed_slots_count', 'count')]
                total_hours = data[('parsed_slots_count', 'sum')] * (DEFAULT_SLOT_MINUTES / 60.0)
                
                if staff_count >= self.sample_size_minimum:
                    total_hours = safe_slot_calculation(
                        data[('parsed_slots_count', 'sum')], 
                        self.slot_minutes, 
                        "sum", 
                        "extract_periodic_constraints_weekday"
                    )
                    facts["曜日制約"].append({
                        "曜日": weekday_names[day_num],
                        "平均人員数": staff_count,
                        "総勤務回数": shift_count,
                        "総勤務時間": round(total_hours, 1),
                        "平均勤務時間": round(total_hours / shift_count if shift_count > 0 else 0, 1),
                        "制約種別": "曜日別人員・時間パターン",
                        "事実性": "実績確認済み",
                        "確信度": 1.0
                    })
        
        return facts
    
    def _extract_exception_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """例外制約（特殊業務、緊急対応、イベント）の抽出"""
        facts = {
            "特殊勤務制約": [],
            "緊急対応制約": [],
            "イベント制約": [],
            "例外処理制約": []
        }
        
        # 特殊コードの使用パターン分析
        if 'code' in long_df.columns:
            code_usage = long_df[long_df['code'] != '']['code'].value_counts()
            rare_codes = code_usage[code_usage < code_usage.quantile(0.1)]
            
            for code, count in rare_codes.items():
                if count >= 1:  # 特殊コードは1回でも記録
                    facts["特殊勤務制約"].append({
                        "勤務コード": code,
                        "使用回数": count,
                        "制約種別": "特殊業務コード",
                        "事実性": "実績確認済み",
                        "確信度": 1.0
                    })
        
        return facts
    
    def _calculate_consecutive_days(self, dates: np.ndarray) -> List[int]:
        """連続勤務日数の計算"""
        if len(dates) == 0:
            return []
        
        dates = sorted(dates)
        consecutive_runs = []
        current_run = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_run += 1
            else:
                consecutive_runs.append(current_run)
                current_run = 1
        
        consecutive_runs.append(current_run)
        return consecutive_runs
    
    def _format_for_human_confirmation(self, facility_facts: Dict) -> Dict[str, Any]:
        """人間確認用のMECE構造化フォーマット"""
        formatted = {
            "抽出事実サマリー": {},
            "MECE分解事実": {},
            "確信度別分類": {"高確信度": [], "中確信度": [], "低確信度": []},
            "要確認事項": []
        }
        
        total_facts = 0
        for category, subcategories in facility_facts.items():
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
        return formatted
    
    def _format_for_ai_execution(self, facility_facts: Dict) -> Dict[str, Any]:
        """AI実行用制約データフォーマット"""
        constraints = {
            "hard_constraints": [],
            "soft_constraints": [],
            "preferences": [],
            "constraint_weights": {}
        }
        
        for category, subcategories in facility_facts.items():
            for subcategory, facts in subcategories.items():
                for fact in facts:
                    confidence = fact.get('確信度', 0.5)
                    
                    constraint = {
                        "id": f"{category}_{subcategory}_{len(constraints['hard_constraints']) + len(constraints['soft_constraints'])}",
                        "type": subcategory,
                        "category": category,
                        "rule": fact,
                        "confidence": confidence,
                        "priority": "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low"
                    }
                    
                    if confidence >= 0.8:
                        constraints["hard_constraints"].append(constraint)
                    elif confidence >= 0.5:
                        constraints["soft_constraints"].append(constraint)
                    else:
                        constraints["preferences"].append(constraint)
        
        return constraints
    
    def _format_for_training(self, facility_facts: Dict, long_df: pd.DataFrame) -> Dict[str, Any]:
        """学習データ用特徴量フォーマット"""
        features = {
            "constraint_features": [],
            "pattern_features": [],
            "statistical_features": {},
            "temporal_features": {}
        }
        
        # 統計的特徴量
        features["statistical_features"] = {
            "total_staff": long_df['staff'].nunique(),
            "total_roles": long_df['role'].nunique() if 'role' in long_df.columns else 0,
            "total_working_hours": len(long_df[long_df['parsed_slots_count'] > 0]),
            "date_range_days": (long_df['ds'].max() - long_df['ds'].min()).days,
            "avg_daily_staff": long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.date)['staff'].nunique().mean()
        }
        
        # 時系列特徴量
        features["temporal_features"] = {
            "weekday_patterns": long_df.groupby(long_df['ds'].dt.dayofweek)['staff'].nunique().to_dict(),
            "hourly_patterns": long_df.groupby(long_df['ds'].dt.hour)['staff'].nunique().to_dict()
        }
        
        return features
    
    def _generate_metadata(self, long_df: pd.DataFrame, facility_facts: Dict) -> Dict[str, Any]:
        """抽出メタデータ生成"""
        return {
            "extraction_timestamp": datetime.now().isoformat(),
            "data_period": {
                "start": long_df['ds'].min().isoformat(),
                "end": long_df['ds'].max().isoformat(),
                "total_days": (long_df['ds'].max() - long_df['ds'].min()).days
            },
            "data_quality": {
                "total_records": len(long_df),
                "working_records": len(long_df[long_df['parsed_slots_count'] > 0]),
                "staff_count": long_df['staff'].nunique(),
                "completeness_ratio": len(long_df[long_df['parsed_slots_count'] > 0]) / len(long_df)
            },
            "extraction_coverage": {
                category: sum(len(facts) for facts in subcategories.values())
                for category, subcategories in facility_facts.items()
            }
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """空のデータ用の結果"""
        return {
            "human_readable": {"抽出事実サマリー": {"総事実数": 0}},
            "machine_readable": {"hard_constraints": [], "soft_constraints": [], "preferences": []},
            "training_data": {"constraint_features": [], "statistical_features": {}},
            "extraction_metadata": {"extraction_timestamp": datetime.now().isoformat(), "data_quality": {"total_records": 0}}
        }
    
    # === 不足していたカテゴリーメソッドの追加実装 ===
    
    def _extract_facility_equipment_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """設備制約の抽出"""
        facts = {
            "設備利用制約": [],
            "設備配置制約": [],
            "設備安全制約": [],
            "設備保守制約": []
        }
        
        # 勤務場所や設備使用パターンから推定
        if 'worktype' in long_df.columns:
            equipment_usage = long_df[long_df['parsed_slots_count'] > 0].groupby('worktype')['ds'].count()
            
            for worktype, usage_count in equipment_usage.items():
                if usage_count >= self.sample_size_minimum:
                    facts["設備利用制約"].append({
                        "勤務種別": worktype,
                        "利用頻度": usage_count,
                        "設備必要性": "推定",
                        "制約種別": "設備必須",
                        "確信度": min(1.0, usage_count / 50)
                    })
        
        return facts
    
    def _extract_business_scope_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """業務範囲制約の抽出"""
        facts = {
            "業務分担制約": [],
            "業務責任制約": [],
            "業務権限制約": [],
            "業務範囲制約": []
        }
        
        # 職種別の業務範囲分析
        if 'role' in long_df.columns:
            role_time_patterns = long_df[long_df['parsed_slots_count'] > 0].groupby(['role', long_df['ds'].dt.hour]).size()
            
            for (role, hour), count in role_time_patterns.items():
                if count >= self.sample_size_minimum:
                    facts["業務分担制約"].append({
                        "職種": role,
                        "時間帯": f"{hour}:00-{hour+1}:00",
                        "業務頻度": count,
                        "業務範囲": f"{role}専門業務",
                        "制約種別": "職種専門性",
                        "確信度": min(1.0, count / 20)
                    })
        
        return facts
    
    def _extract_facility_characteristics_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """施設特性制約の抽出"""
        facts = {
            "施設規模制約": [],
            "施設構造制約": [],
            "施設機能制約": [],
            "施設環境制約": []
        }
        
        # 施設規模の推定（スタッフ数と稼働時間から）
        total_staff = long_df['staff'].nunique()
        active_hours = long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.hour).size()
        peak_hour_staff = long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.hour)['staff'].nunique().max()
        
        facts["施設規模制約"].append({
            "総スタッフ数": total_staff,
            "ピーク時最大人員": peak_hour_staff,
            "稼働時間数": len(active_hours[active_hours > 0]),
            "施設規模推定": "中規模" if total_staff < 20 else "大規模",
            "制約種別": "規模ベース制約",
            "確信度": 0.8
        })
        
        return facts
    
    def _extract_area_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """エリア制約の抽出"""
        facts = {
            "エリア配置制約": [],
            "エリア移動制約": [],
            "エリア専任制約": [],
            "エリア重複制約": []
        }
        
        # 同時勤務パターンからエリア配置を推定
        hourly_staff_counts = long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.hour)['staff'].nunique()
        
        for hour, staff_count in hourly_staff_counts.items():
            if staff_count >= 2:
                facts["エリア配置制約"].append({
                    "時間帯": f"{hour}:00-{hour+1}:00",
                    "同時配置人数": staff_count,
                    "エリア推定": f"複数エリア対応",
                    "制約種別": "エリア分散配置",
                    "確信度": min(1.0, staff_count / 5)
                })
        
        return facts
    
    def _extract_operation_time_constraints(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, List[Dict]]:
        """運用時間制約の抽出"""
        facts = {
            "営業時間制約": [],
            "深夜運用制約": [],
            "早朝運用制約": [],
            "運用継続制約": []
        }
        
        # 時間帯別の運用状況分析
        hourly_operations = long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.hour).size()
        
        for hour, operation_count in hourly_operations.items():
            if operation_count >= self.sample_size_minimum:
                time_category = ""
                if 6 <= hour <= 22:
                    time_category = "通常営業時間"
                elif 23 <= hour or hour <= 5:
                    time_category = "深夜運用"
                else:
                    time_category = "早朝運用"
                
                constraint_type = "営業時間制約" if time_category == "通常営業時間" else \
                                "深夜運用制約" if time_category == "深夜運用" else "早朝運用制約"
                
                facts[constraint_type].append({
                    "時間帯": f"{hour}:00-{hour+1}:00",
                    "運用回数": operation_count,
                    "運用カテゴリー": time_category,
                    "制約種別": "運用時間必須",
                    "確信度": min(1.0, operation_count / 30)
                })
        
        return facts
    
    def _extract_placement_standard_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """配置基準制約の抽出"""
        facts = {
            "最低配置基準": [],
            "最適配置基準": [],
            "バランス配置基準": [],
            "緊急配置基準": []
        }
        
        # 時間帯別の最低・最適配置人数分析
        hourly_staff_stats = long_df[long_df['parsed_slots_count'] > 0].groupby(long_df['ds'].dt.hour)['staff'].agg(['nunique', 'count'])
        
        for hour, stats in hourly_staff_stats.iterrows():
            unique_staff = stats['nunique']
            total_slots = stats['count']
            
            if unique_staff >= 1:
                facts["最低配置基準"].append({
                    "時間帯": f"{hour}:00-{hour+1}:00",
                    "最低人員": max(1, unique_staff - 1),
                    "推奨人員": unique_staff,
                    "最大人員": unique_staff + 1,
                    "配置密度": round(total_slots / unique_staff, 1) if unique_staff > 0 else 0,
                    "制約種別": "配置基準",
                    "確信度": min(1.0, total_slots / 50)
                })
        
        return facts
    
    def _extract_role_definition_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """役割定義制約の抽出"""
        facts = {
            "役割責任制約": [],
            "役割権限制約": [],
            "役割代替制約": [],
            "役割専門制約": []
        }
        
        # 職種別の役割パターン分析
        if 'role' in long_df.columns:
            role_patterns = long_df[long_df['parsed_slots_count'] > 0].groupby('role').agg({
                'ds': ['count', 'nunique'],
                'staff': 'nunique'
            }).round(2)
            
            for role in role_patterns.index:
                work_frequency = role_patterns.loc[role, ('ds', 'count')]
                unique_days = role_patterns.loc[role, ('ds', 'nunique')]
                staff_count = role_patterns.loc[role, ('staff', 'nunique')]
                
                if work_frequency >= self.sample_size_minimum:
                    facts["役割責任制約"].append({
                        "職種": role,
                        "勤務頻度": work_frequency,
                        "勤務日数": unique_days,
                        "担当スタッフ数": staff_count,
                        "専門性レベル": "高" if staff_count <= 2 else "中" if staff_count <= 5 else "低",
                        "制約種別": "役割専門性",
                        "確信度": min(1.0, work_frequency / 100)
                    })
        
        return facts
    
    def _extract_cooperation_system_constraints(self, long_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """協力体制制約の抽出"""
        facts = {
            "チーム協力制約": [],
            "連携必須制約": [],
            "相互支援制約": [],
            "協力体制制約": []
        }
        
        # スタッフ間の協力パターン分析
        daily_teams = long_df[long_df['parsed_slots_count'] > 0].groupby([
            long_df['ds'].dt.date, long_df['ds'].dt.hour
        ])['staff'].apply(list)
        
        collaboration_patterns = defaultdict(int)
        for team_members in daily_teams:
            if len(team_members) >= 2:
                from itertools import combinations
                for pair in combinations(sorted(team_members), 2):
                    collaboration_patterns[pair] += 1
        
        # 頻繁な協力ペアの抽出
        total_collaborations = sum(collaboration_patterns.values())
        for (staff1, staff2), count in collaboration_patterns.items():
            if count >= self.sample_size_minimum and count / total_collaborations > 0.05:
                facts["チーム協力制約"].append({
                    "協力ペア": f"{staff1} - {staff2}",
                    "協力回数": count,
                    "協力頻度": round(count / total_collaborations, 3),
                    "制約種別": "チーム連携推奨",
                    "確信度": min(1.0, count / 20)
                })
        
        return facts