"""
軸2(職員ルール)専用 MECE事実抽出システム
過去シフト実績から個人レベルの運用ルール・制約を網羅的に事実ベースで抽出

主な抽出範囲：
- 個人勤務パターン・傾向
- スキル・資格による配置制限
- 個人の働き方特性
- 休暇・勤務時間の個人差
- 新人・ベテラン配置パターン
- 個人パフォーマンス特性
- 個人間の協働・回避パターン
- 個人のライフスタイル制約
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import json

from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS

log = logging.getLogger(__name__)


class StaffMECEFactExtractor:
    """軸2(職員ルール)のMECE完全事実抽出システム"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.sample_size_minimum = 5
        self.individual_analysis_threshold = 10  # 個人分析に必要な最低勤務回数
        
    def _convert_to_json_serializable(self, obj):
        """numpy型をJSONシリアライズ可能な型に変換"""
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        return obj
        
    def extract_axis2_staff_rules(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """軸2: 職員ルールの完全MECE事実抽出
        
        Args:
            long_df: 長形式シフトデータ
            wt_df: 勤務区分データ（オプション）
            
        Returns:
            Dict containing:
            - human_readable: 人間確認用MECE構造化事実
            - machine_readable: AI実行用制約データ  
            - training_data: 学習データ用特徴量
        """
        log.info("軸2(職員ルール) MECE事実抽出を開始...")
        
        if long_df.empty:
            return self._empty_result()
            
        # 個人分析対象者の事前フィルタリング
        eligible_staff = self._identify_eligible_staff(long_df)
        
        # MECE分解による個人レベル事実抽出
        staff_facts = {
            "個人勤務パターン": self._extract_individual_work_patterns(long_df, eligible_staff),
            "スキル・配置制約": self._extract_skill_placement_constraints(long_df, eligible_staff),
            "時間選好制約": self._extract_time_preference_constraints(long_df, eligible_staff),
            "休暇・休息制約": self._extract_leave_rest_constraints(long_df, eligible_staff),
            "経験・レベル制約": self._extract_experience_level_constraints(long_df, eligible_staff),
            "協働・相性制約": self._extract_collaboration_constraints(long_df, eligible_staff),
            "パフォーマンス制約": self._extract_performance_constraints(long_df, eligible_staff),
            "ライフスタイル制約": self._extract_lifestyle_constraints(long_df, eligible_staff),
        }
        
        result = {
            "human_readable": self._format_for_human_confirmation(staff_facts, eligible_staff),
            "machine_readable": self._format_for_ai_execution(staff_facts),
            "training_data": self._format_for_training(staff_facts, long_df),
            "extraction_metadata": self._generate_metadata(long_df, staff_facts, eligible_staff)
        }
        
        # JSON シリアライズ可能な形式に変換
        return self._convert_to_json_serializable(result)
    
    def _identify_eligible_staff(self, long_df: pd.DataFrame) -> List[str]:
        """分析対象となる十分なデータを持つスタッフを特定"""
        staff_work_counts = long_df[long_df['parsed_slots_count'] > 0].groupby('staff').size()
        eligible = staff_work_counts[staff_work_counts >= self.individual_analysis_threshold].index.tolist()
        
        log.info(f"分析対象スタッフ: {len(eligible)}名（全{long_df['staff'].nunique()}名中）")
        return eligible
    
    def _extract_individual_work_patterns(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """個人勤務パターン・傾向の抽出"""
        facts = {
            "固定パターン": [],
            "避回パターン": [],
            "変動パターン": [],
            "集中パターン": []
        }
        
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 曜日パターン分析
            weekday_pattern = staff_df.groupby(staff_df['ds'].dt.dayofweek).size()
            total_work_days = len(staff_df['ds'].dt.date.unique())
            
            # 固定曜日勤務の検出
            consistent_days = weekday_pattern[weekday_pattern > total_work_days * 0.7]
            if len(consistent_days) > 0:
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                consistent_day_names = [weekday_names[day] for day in consistent_days.index]
                
                facts["固定パターン"].append({
                    "スタッフ": staff,
                    "パターン種別": "固定曜日勤務",
                    "詳細": f"{', '.join(consistent_day_names)}に集中勤務",
                    "比率": round(consistent_days.sum() / len(staff_df), 3),
                    "確信度": min(1.0, len(staff_df) / 30),
                    "事実性": "実績ベース確定"
                })
            
            # 避回曜日の検出
            zero_days = set(range(7)) - set(weekday_pattern.index)
            if len(zero_days) > 0 and total_work_days >= 4:  # 十分な期間での避回
                avoided_day_names = [weekday_names[day] for day in zero_days]
                facts["避回パターン"].append({
                    "スタッフ": staff,
                    "パターン種別": "曜日避回",
                    "詳細": f"{', '.join(avoided_day_names)}完全避回",
                    "避回曜日数": len(zero_days),
                    "分析期間": total_work_days,
                    "確信度": min(1.0, total_work_days / 20),
                    "事実性": "実績ベース確定"
                })
            
            # 時間帯パターン分析
            if 'code' in staff_df.columns:
                code_pattern = staff_df['code'].value_counts(normalize=True)
                dominant_code = code_pattern.index[0] if len(code_pattern) > 0 else None
                
                if dominant_code and code_pattern.iloc[0] > 0.8:
                    facts["固定パターン"].append({
                        "スタッフ": staff,
                        "パターン種別": "固定勤務コード",
                        "詳細": f"勤務コード「{dominant_code}」に{code_pattern.iloc[0]:.1%}集中",
                        "主要コード": dominant_code,
                        "集中度": round(code_pattern.iloc[0], 3),
                        "確信度": min(1.0, len(staff_df) / 25),
                        "事実性": "実績ベース確定"
                    })
        
        return facts
    
    def _extract_skill_placement_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """スキル・配置制約の抽出"""
        facts = {
            "職種固定制約": [],
            "職種変動制約": [],
            "専門配置制約": [],
            "多能工制約": []
        }
        
        if 'role' not in long_df.columns:
            return facts
            
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 職種パターン分析
            role_pattern = staff_df['role'].value_counts()
            unique_roles = len(role_pattern)
            
            if unique_roles == 1:
                # 職種固定
                role = role_pattern.index[0]
                facts["職種固定制約"].append({
                    "スタッフ": staff,
                    "制約種別": "職種固定",
                    "詳細": f"職種「{role}」に完全固定",
                    "固定職種": role,
                    "勤務回数": len(staff_df),
                    "確信度": 1.0,
                    "事実性": "実績ベース確定"
                })
            elif unique_roles >= 3:
                # 多能工
                role_list = role_pattern.index.tolist()
                facts["多能工制約"].append({
                    "スタッフ": staff,
                    "制約種別": "多能工",
                    "詳細": f"{unique_roles}職種対応: {', '.join(role_list[:3])}{'...' if len(role_list) > 3 else ''}",
                    "対応職種数": unique_roles,
                    "対応職種": role_list,
                    "確信度": min(1.0, len(staff_df) / 20),
                    "事実性": "実績ベース確定"
                })
        
        return facts
    
    def _extract_time_preference_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """時間選好制約の抽出"""
        facts = {
            "早朝選好制約": [],
            "夜間選好制約": [],
            "時間回避制約": [],
            "勤務時間制約": []
        }
        
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 時間帯分析
            hours = staff_df['ds'].dt.hour
            
            # 早朝勤務パターン（5:00-8:00）
            early_morning_ratio = ((hours >= 5) & (hours < 8)).sum() / len(hours)
            if early_morning_ratio > 0.5:
                facts["早朝選好制約"].append({
                    "スタッフ": staff,
                    "制約種別": "早朝選好",
                    "詳細": f"全勤務の{early_morning_ratio:.1%}が早朝時間帯",
                    "早朝比率": round(early_morning_ratio, 3),
                    "確信度": min(1.0, len(staff_df) / 30),
                    "事実性": "実績ベース推定"
                })
            
            # 夜間勤務パターン（20:00-5:00）
            night_ratio = ((hours >= 20) | (hours < 5)).sum() / len(hours)
            if night_ratio > 0.5:
                facts["夜間選好制約"].append({
                    "スタッフ": staff,
                    "制約種別": "夜間選好",
                    "詳細": f"全勤務の{night_ratio:.1%}が夜間時間帯",
                    "夜間比率": round(night_ratio, 3),
                    "確信度": min(1.0, len(staff_df) / 30),
                    "事実性": "実績ベース推定"
                })
            
            # 連続勤務時間の分析
            daily_hours = staff_df.groupby(staff_df['ds'].dt.date).size() * SLOT_HOURS
            if len(daily_hours) > 0:
                avg_daily_hours = daily_hours.mean()
                max_daily_hours = daily_hours.max()
                
                if max_daily_hours <= 8 and avg_daily_hours <= 6:
                    facts["勤務時間制約"].append({
                        "スタッフ": staff,
                        "制約種別": "短時間勤務",
                        "詳細": f"平均{avg_daily_hours:.1f}時間/日、最大{max_daily_hours}時間/日",
                        "平均時間": round(avg_daily_hours, 2),
                        "最大時間": max_daily_hours,
                        "確信度": min(1.0, len(daily_hours) / 10),
                        "事実性": "実績ベース推定"
                    })
        
        return facts
    
    def _extract_leave_rest_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """休暇・休息制約の抽出"""
        facts = {
            "連続勤務制約": [],
            "休暇パターン": [],
            "休息間隔制約": [],
            "疲労回避制約": []
        }
        
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 連続勤務日数の分析
            work_dates = sorted(staff_df['ds'].dt.date.unique())
            consecutive_periods = self._calculate_consecutive_periods(work_dates)
            
            if consecutive_periods:
                max_consecutive = max(consecutive_periods)
                avg_consecutive = np.mean(consecutive_periods)
                
                facts["連続勤務制約"].append({
                    "スタッフ": staff,
                    "制約種別": "連続勤務上限",
                    "詳細": f"最大連続{max_consecutive}日、平均{avg_consecutive:.1f}日",
                    "最大連続日数": max_consecutive,
                    "平均連続日数": round(avg_consecutive, 1),
                    "確信度": min(1.0, len(consecutive_periods) / 5),
                    "事実性": "実績ベース推定"
                })
        
        return facts
    
    def _extract_experience_level_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """経験・レベル制約の抽出"""
        facts = {
            "経験レベル推定": [],
            "新人・ベテラン": [],
            "責任レベル": [],
            "指導・被指導": []
        }
        
        # 全スタッフの勤務頻度から経験レベルを推定
        staff_work_frequency = long_df[long_df['parsed_slots_count'] > 0].groupby('staff').size()
        
        # 四分位で経験レベル分類
        q25 = staff_work_frequency.quantile(0.25)
        q75 = staff_work_frequency.quantile(0.75)
        
        for staff in eligible_staff:
            work_count = staff_work_frequency.get(staff, 0)
            
            if work_count <= q25:
                level = "新人・初級"
                level_detail = "勤務頻度が下位25%"
            elif work_count >= q75:
                level = "ベテラン・上級"
                level_detail = "勤務頻度が上位25%"
            else:
                level = "中級"
                level_detail = "勤務頻度が中間層"
            
            facts["経験レベル推定"].append({
                "スタッフ": staff,
                "推定レベル": level,
                "詳細": level_detail,
                "勤務回数": work_count,
                "相対位置": f"{(staff_work_frequency <= work_count).mean():.1%}tile",
                "確信度": 0.6,  # 推定のため中程度の確信度
                "事実性": "実績ベース推定"
            })
        
        return facts
    
    def _extract_collaboration_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """協働・相性制約の抽出"""
        facts = {
            "協働パターン": [],
            "回避パターン": [],
            "相性制約": [],
            "チーム制約": []
        }
        
        # 同日・同時間勤務の分析
        daily_groups = long_df[long_df['parsed_slots_count'] > 0].groupby([
            long_df['ds'].dt.date, long_df['ds'].dt.hour
        ])['staff'].apply(list)
        
        # スタッフ間の共同勤務回数をカウント
        collaboration_counts = defaultdict(int)
        staff_total_work = long_df[long_df['parsed_slots_count'] > 0].groupby('staff').size()
        
        for staff_list in daily_groups:
            if len(staff_list) >= 2:
                from itertools import combinations
                for staff1, staff2 in combinations(sorted(set(staff_list)), 2):
                    if staff1 in eligible_staff and staff2 in eligible_staff:
                        collaboration_counts[(staff1, staff2)] += 1
        
        # 協働頻度分析
        for (staff1, staff2), collab_count in collaboration_counts.items():
            if collab_count >= self.sample_size_minimum:
                # 期待値計算
                total_days = long_df['ds'].dt.date.nunique()
                expected_collab = (staff_total_work.get(staff1, 0) * staff_total_work.get(staff2, 0)) / (total_days * total_days)
                
                if expected_collab > 0:
                    collaboration_ratio = collab_count / expected_collab
                    
                    if collaboration_ratio > 2.0:  # 期待値の2倍以上
                        facts["協働パターン"].append({
                            "スタッフ1": staff1,
                            "スタッフ2": staff2,
                            "制約種別": "協働促進",
                            "詳細": f"共同勤務{collab_count}回（期待値の{collaboration_ratio:.1f}倍）",
                            "実績回数": collab_count,
                            "期待値": round(expected_collab, 1),
                            "協働比率": round(collaboration_ratio, 2),
                            "確信度": min(1.0, collab_count / 10),
                            "事実性": "実績ベース推定"
                        })
        
        return facts
    
    def _extract_performance_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """パフォーマンス制約の抽出"""
        facts = {
            "安定性制約": [],
            "変動性制約": [],
            "効率性制約": [],
            "負荷制約": []
        }
        
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 勤務の一貫性・安定性分析
            monthly_work = staff_df.groupby(staff_df['ds'].dt.to_period('M')).size()
            
            if len(monthly_work) >= 2:
                work_stability = 1 - (monthly_work.std() / monthly_work.mean())
                
                if work_stability > 0.8:
                    facts["安定性制約"].append({
                        "スタッフ": staff,
                        "制約種別": "高安定性",
                        "詳細": f"月次勤務回数の変動係数{1-work_stability:.2f}（低変動）",
                        "安定性指数": round(work_stability, 3),
                        "確信度": min(1.0, len(monthly_work) / 3),
                        "事実性": "実績ベース推定"
                    })
                elif work_stability < 0.5:
                    facts["変動性制約"].append({
                        "スタッフ": staff,
                        "制約種別": "高変動性",
                        "詳細": f"月次勤務回数の変動係数{1-work_stability:.2f}（高変動）",
                        "変動性指数": round(1-work_stability, 3),
                        "確信度": min(1.0, len(monthly_work) / 3),
                        "事実性": "実績ベース推定"
                    })
        
        return facts
    
    def _extract_lifestyle_constraints(self, long_df: pd.DataFrame, eligible_staff: List[str]) -> Dict[str, List[Dict]]:
        """ライフスタイル制約の抽出"""
        facts = {
            "時間帯ライフスタイル": [],
            "曜日ライフスタイル": [],
            "期間ライフスタイル": [],
            "頻度ライフスタイル": []
        }
        
        for staff in eligible_staff:
            staff_df = long_df[(long_df['staff'] == staff) & (long_df['parsed_slots_count'] > 0)]
            
            if len(staff_df) < self.sample_size_minimum:
                continue
            
            # 全体的な勤務頻度からライフスタイル推定
            total_possible_days = (long_df['ds'].max() - long_df['ds'].min()).days + 1
            actual_work_days = staff_df['ds'].dt.date.nunique()
            work_frequency_ratio = actual_work_days / total_possible_days
            
            if work_frequency_ratio <= 0.3:
                facts["頻度ライフスタイル"].append({
                    "スタッフ": staff,
                    "ライフスタイル": "低頻度勤務",
                    "詳細": f"全期間の{work_frequency_ratio:.1%}のみ勤務",
                    "勤務頻度": round(work_frequency_ratio, 3),
                    "確信度": min(1.0, actual_work_days / 10),
                    "事実性": "実績ベース推定"
                })
            elif work_frequency_ratio >= 0.7:
                facts["頻度ライフスタイル"].append({
                    "スタッフ": staff,
                    "ライフスタイル": "高頻度勤務",
                    "詳細": f"全期間の{work_frequency_ratio:.1%}で勤務",
                    "勤務頻度": round(work_frequency_ratio, 3),
                    "確信度": min(1.0, actual_work_days / 10),
                    "事実性": "実績ベース推定"
                })
        
        return facts
    
    def _calculate_consecutive_periods(self, dates: List) -> List[int]:
        """連続勤務期間の計算"""
        if not dates:
            return []
        
        dates = sorted(dates)
        consecutive_periods = []
        current_period = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_period += 1
            else:
                consecutive_periods.append(current_period)
                current_period = 1
        
        consecutive_periods.append(current_period)
        return consecutive_periods
    
    def _format_for_human_confirmation(self, staff_facts: Dict, eligible_staff: List[str]) -> Dict[str, Any]:
        """人間確認用のMECE構造化フォーマット"""
        formatted = {
            "抽出事実サマリー": {},
            "MECE分解事実": {},
            "スタッフ別分析": {},
            "確信度別分類": {"高確信度": [], "中確信度": [], "低確信度": []},
            "要確認事項": []
        }
        
        total_facts = 0
        for category, subcategories in staff_facts.items():
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
        formatted["抽出事実サマリー"]["分析対象スタッフ数"] = len(eligible_staff)
        
        # スタッフ別サマリー
        staff_summary = {}
        for staff in eligible_staff:
            staff_fact_count = sum(
                1 for category in staff_facts.values()
                for subcategory in category.values()
                for fact in subcategory
                if fact.get('スタッフ') == staff or fact.get('スタッフ1') == staff or fact.get('スタッフ2') == staff
            )
            staff_summary[staff] = staff_fact_count
        
        formatted["スタッフ別分析"] = staff_summary
        return formatted
    
    def _format_for_ai_execution(self, staff_facts: Dict) -> Dict[str, Any]:
        """AI実行用制約データフォーマット"""
        constraints = {
            "staff_hard_constraints": [],
            "staff_soft_constraints": [],
            "staff_preferences": [],
            "staff_constraint_weights": {}
        }
        
        for category, subcategories in staff_facts.items():
            for subcategory, facts in subcategories.items():
                for fact in facts:
                    confidence = fact.get('確信度', 0.5)
                    
                    constraint = {
                        "id": f"staff_{category}_{subcategory}_{len(constraints['staff_hard_constraints']) + len(constraints['staff_soft_constraints'])}",
                        "type": subcategory,
                        "category": category,
                        "rule": fact,
                        "confidence": confidence,
                        "priority": "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low",
                        "scope": "individual"  # 個人レベル制約
                    }
                    
                    if confidence >= 0.8:
                        constraints["staff_hard_constraints"].append(constraint)
                    elif confidence >= 0.5:
                        constraints["staff_soft_constraints"].append(constraint)
                    else:
                        constraints["staff_preferences"].append(constraint)
        
        return constraints
    
    def _format_for_training(self, staff_facts: Dict, long_df: pd.DataFrame) -> Dict[str, Any]:
        """学習データ用特徴量フォーマット"""
        features = {
            "individual_features": [],
            "collaboration_features": [],
            "pattern_features": [],
            "statistical_features": {}
        }
        
        # 個人レベル統計特徴量
        staff_stats = long_df[long_df['parsed_slots_count'] > 0].groupby('staff').agg({
            'ds': ['count', 'nunique'],
            'parsed_slots_count': 'sum'
        }).round(2)
        
        features["statistical_features"]["individual_stats"] = staff_stats.to_dict()
        
        return features
    
    def _generate_metadata(self, long_df: pd.DataFrame, staff_facts: Dict, eligible_staff: List[str]) -> Dict[str, Any]:
        """抽出メタデータ生成"""
        return {
            "extraction_timestamp": datetime.now().isoformat(),
            "axis": 2,
            "axis_name": "職員ルール",
            "data_period": {
                "start": long_df['ds'].min().isoformat(),
                "end": long_df['ds'].max().isoformat(),
                "total_days": (long_df['ds'].max() - long_df['ds'].min()).days
            },
            "data_quality": {
                "total_records": len(long_df),
                "working_records": len(long_df[long_df['parsed_slots_count'] > 0]),
                "total_staff_count": long_df['staff'].nunique(),
                "eligible_staff_count": len(eligible_staff),
                "analysis_coverage_ratio": len(eligible_staff) / long_df['staff'].nunique()
            },
            "extraction_coverage": {
                category: sum(len(facts) for facts in subcategories.values())
                for category, subcategories in staff_facts.items()
            }
        }
    
    def _empty_result(self) -> Dict[str, Any]:
        """空のデータ用の結果"""
        return {
            "human_readable": {"抽出事実サマリー": {"総事実数": 0, "分析対象スタッフ数": 0}},
            "machine_readable": {"staff_hard_constraints": [], "staff_soft_constraints": [], "staff_preferences": []},
            "training_data": {"individual_features": [], "statistical_features": {}},
            "extraction_metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "axis": 2,
                "data_quality": {"total_records": 0, "eligible_staff_count": 0}
            }
        }