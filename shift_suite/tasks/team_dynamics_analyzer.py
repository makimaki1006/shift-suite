"""
チームダイナミクス・相性分析エンジン

スタッフ間のチームワーク相性、学習効果、緊急対応能力を分析し、
最適なチーム編成とシフト配置を支援します。

Author: Claude Code Assistant
Created: 2025-01-14
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import cosine
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .constants import TEAM_DYNAMICS_PARAMETERS

log = logging.getLogger(__name__)

@dataclass
class TeamCompatibility:
    """チーム相性分析結果"""
    staff_pair: Tuple[str, str]
    compatibility_score: float  # 0.0-1.0
    collaboration_frequency: float
    performance_impact: float
    risk_factors: List[str]
    synergy_factors: List[str]
    recommendation: str

@dataclass
class LearningPattern:
    """学習・成長パターン分析結果"""
    staff_name: str
    experience_level: str  # 新人、中堅、ベテラン
    learning_speed: float
    skill_growth_areas: List[str]
    mentoring_capacity: float
    optimal_mentors: List[str]
    recommended_tasks: List[str]

@dataclass
class EmergencyCapacity:
    """緊急対応能力分析結果"""
    staff_name: str
    flexibility_score: float  # 0.0-1.0
    cross_training_level: float
    stress_resilience: float
    emergency_availability: float
    backup_roles: List[str]
    response_time_category: str

class TeamDynamicsAnalyzer:
    """チームダイナミクス・相性分析エンジン"""
    
    def __init__(self):
        self.compatibility_threshold = TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_good"]  # 相性良好の閾値
        self.emergency_score_threshold = TEAM_DYNAMICS_PARAMETERS["emergency_score_threshold"]  # 緊急対応可能の閾値
        
    def analyze_team_dynamics(self, long_df: pd.DataFrame) -> Dict[str, any]:
        """チームダイナミクスの包括分析"""
        
        if long_df.empty:
            return {}
            
        log.info("🤝 チームダイナミクス分析を開始...")
        
        # 1. スタッフ間相性分析
        compatibility_results = self._analyze_staff_compatibility(long_df)
        
        # 2. 学習・成長パターン分析
        learning_patterns = self._analyze_learning_patterns(long_df)
        
        # 3. 緊急対応能力分析
        emergency_capacity = self._analyze_emergency_capacity(long_df)
        
        # 4. 最適チーム編成提案
        optimal_teams = self._generate_optimal_teams(
            compatibility_results, learning_patterns, emergency_capacity
        )
        
        # 5. ストレス耐性分析
        stress_analysis = self._analyze_stress_resilience(long_df)
        
        return {
            'staff_compatibility': compatibility_results,
            'learning_patterns': learning_patterns,
            'emergency_capacity': emergency_capacity,
            'optimal_teams': optimal_teams,
            'stress_resilience': stress_analysis,
            'team_recommendations': self._generate_team_recommendations(
                compatibility_results, learning_patterns, emergency_capacity
            )
        }
    
    def _analyze_staff_compatibility(self, long_df: pd.DataFrame) -> List[TeamCompatibility]:
        """スタッフ間相性分析"""
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        compatibility_results = []
        
        # 同日勤務の分析
        daily_teams = working_df.groupby(['ds', 'code'])['staff'].apply(list).reset_index()
        
        # ペア共起統計
        pair_stats = defaultdict(lambda: {
            'co_occurrences': 0,
            'total_opportunities': 0,
            'performance_indicators': []
        })
        
        staff_list = list(working_df['staff'].unique())
        
        for staff1, staff2 in combinations(staff_list, 2):
            # 共起回数の計算
            staff1_days = set(working_df[working_df['staff'] == staff1]['ds'].dt.date)
            staff2_days = set(working_df[working_df['staff'] == staff2]['ds'].dt.date)
            
            co_occurrence_days = staff1_days.intersection(staff2_days)
            total_opportunity_days = staff1_days.union(staff2_days)
            
            if len(total_opportunity_days) > 0:
                collaboration_freq = len(co_occurrence_days) / len(total_opportunity_days)
                
                # 相性スコアの計算
                compatibility_score = self._calculate_compatibility_score(
                    staff1, staff2, working_df, collaboration_freq
                )
                
                # パフォーマンス影響の分析
                performance_impact = self._analyze_performance_impact(
                    staff1, staff2, working_df, co_occurrence_days
                )
                
                # リスク・シナジー要因の特定
                risk_factors, synergy_factors = self._identify_compatibility_factors(
                    staff1, staff2, working_df
                )
                
                # 推奨事項の生成
                recommendation = self._generate_compatibility_recommendation(
                    compatibility_score, collaboration_freq, performance_impact
                )
                
                compatibility_results.append(TeamCompatibility(
                    staff_pair=(staff1, staff2),
                    compatibility_score=compatibility_score,
                    collaboration_frequency=collaboration_freq,
                    performance_impact=performance_impact,
                    risk_factors=risk_factors,
                    synergy_factors=synergy_factors,
                    recommendation=recommendation
                ))
        
        # 相性スコア順でソート
        compatibility_results.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        return compatibility_results
    
    def _analyze_learning_patterns(self, long_df: pd.DataFrame) -> List[LearningPattern]:
        """学習・成長パターン分析"""
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        learning_patterns = []
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            # 経験レベルの判定
            experience_level = self._assess_experience_level(staff_df)
            
            # 学習速度の分析
            learning_speed = self._calculate_learning_speed(staff_df)
            
            # スキル成長領域の特定
            skill_growth_areas = self._identify_skill_growth_areas(staff_df)
            
            # メンタリング能力の評価
            mentoring_capacity = self._assess_mentoring_capacity(staff_df, experience_level)
            
            # 最適メンターの提案
            optimal_mentors = self._identify_optimal_mentors(
                staff, working_df, experience_level
            )
            
            # 推奨タスクの生成
            recommended_tasks = self._generate_task_recommendations(
                experience_level, skill_growth_areas
            )
            
            learning_patterns.append(LearningPattern(
                staff_name=staff,
                experience_level=experience_level,
                learning_speed=learning_speed,
                skill_growth_areas=skill_growth_areas,
                mentoring_capacity=mentoring_capacity,
                optimal_mentors=optimal_mentors,
                recommended_tasks=recommended_tasks
            ))
        
        return learning_patterns
    
    def _analyze_emergency_capacity(self, long_df: pd.DataFrame) -> List[EmergencyCapacity]:
        """緊急対応能力分析"""
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        emergency_capacity = []
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            # 柔軟性スコアの計算
            flexibility_score = self._calculate_flexibility_score(staff_df)
            
            # クロストレーニングレベルの評価
            cross_training_level = self._assess_cross_training_level(staff_df)
            
            # ストレス耐性の評価
            stress_resilience = self._assess_stress_resilience(staff_df)
            
            # 緊急時対応可能性の計算
            emergency_availability = self._calculate_emergency_availability(staff_df)
            
            # バックアップ可能役割の特定
            backup_roles = self._identify_backup_roles(staff_df)
            
            # 対応時間カテゴリの分類
            response_time_category = self._categorize_response_time(
                flexibility_score, emergency_availability
            )
            
            emergency_capacity.append(EmergencyCapacity(
                staff_name=staff,
                flexibility_score=flexibility_score,
                cross_training_level=cross_training_level,
                stress_resilience=stress_resilience,
                emergency_availability=emergency_availability,
                backup_roles=backup_roles,
                response_time_category=response_time_category
            ))
        
        # 緊急対応能力順でソート
        emergency_capacity.sort(key=lambda x: x.flexibility_score, reverse=True)
        
        return emergency_capacity
    
    def _analyze_stress_resilience(self, long_df: pd.DataFrame) -> Dict[str, any]:
        """ストレス耐性の詳細分析"""
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        stress_analysis = {}
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            
            # 1. 負荷変動への適応性
            workload_variance = staff_df['parsed_slots_count'].var()
            adaptation_score = min(1.0, 1.0 / (1.0 + workload_variance))
            
            # 2. 連続勤務耐性
            consecutive_tolerance = self._assess_consecutive_tolerance(staff_df)
            
            # 3. 繁忙期対応力
            peak_period_performance = self._assess_peak_period_performance(staff_df)
            
            # 4. 総合ストレス耐性スコア
            overall_resilience = (
                adaptation_score * TEAM_DYNAMICS_PARAMETERS["adaptation_weight"] +
                consecutive_tolerance * TEAM_DYNAMICS_PARAMETERS["consecutive_tolerance_weight"] +
                peak_period_performance * TEAM_DYNAMICS_PARAMETERS["peak_performance_weight"]
            )
            
            stress_analysis[staff] = {
                'adaptation_score': adaptation_score,
                'consecutive_tolerance': consecutive_tolerance,
                'peak_period_performance': peak_period_performance,
                'overall_resilience': overall_resilience,
                'stress_category': self._categorize_stress_level(overall_resilience)
            }
        
        return stress_analysis
    
    def _generate_optimal_teams(self, compatibility_results: List[TeamCompatibility],
                              learning_patterns: List[LearningPattern],
                              emergency_capacity: List[EmergencyCapacity]) -> List[Dict[str, any]]:
        """最適チーム編成の提案"""
        
        optimal_teams = []
        
        # 高相性ペアの抽出
        high_compatibility_pairs = [
            comp for comp in compatibility_results 
            if comp.compatibility_score >= self.compatibility_threshold
        ]
        
        # 経験レベル別スタッフ分類
        experience_groups = defaultdict(list)
        for pattern in learning_patterns:
            experience_groups[pattern.experience_level].append(pattern.staff_name)
        
        # 緊急対応可能スタッフの特定
        emergency_responders = [
            cap.staff_name for cap in emergency_capacity 
            if cap.flexibility_score >= self.emergency_score_threshold
        ]
        
        # チーム編成アルゴリズム
        team_id = 1
        used_staff = set()
        
        for pair in high_compatibility_pairs:
            staff1, staff2 = pair.staff_pair
            
            if staff1 not in used_staff and staff2 not in used_staff:
                # 経験バランスの確認
                exp1 = next((p.experience_level for p in learning_patterns if p.staff_name == staff1), "不明")
                exp2 = next((p.experience_level for p in learning_patterns if p.staff_name == staff2), "不明")
                
                # チーム特性の分析
                team_characteristics = {
                    'compatibility_score': pair.compatibility_score,
                    'experience_balance': self._assess_experience_balance(exp1, exp2),
                    'emergency_coverage': any(staff in emergency_responders for staff in [staff1, staff2]),
                    'learning_potential': self._assess_learning_potential(staff1, staff2, learning_patterns),
                    'synergy_factors': pair.synergy_factors
                }
                
                optimal_teams.append({
                    'team_id': f"Team_{team_id:02d}",
                    'members': [staff1, staff2],
                    'characteristics': team_characteristics,
                    'recommendation_reason': f"高相性ペア（相性度{pair.compatibility_score:.2f}）",
                    'optimal_scenarios': self._identify_optimal_scenarios(pair, team_characteristics)
                })
                
                used_staff.add(staff1)
                used_staff.add(staff2)
                team_id += 1
        
        return optimal_teams
    
    def _generate_team_recommendations(self, compatibility_results: List[TeamCompatibility],
                                     learning_patterns: List[LearningPattern],
                                     emergency_capacity: List[EmergencyCapacity]) -> List[str]:
        """チーム編成に関する推奨事項"""
        
        recommendations = []
        
        # 1. 高相性ペアの活用推奨
        excellent_pairs = [c for c in compatibility_results if c.compatibility_score >= TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_excellent"]]
        if excellent_pairs:
            recommendations.append(
                f"優秀な相性ペア{len(excellent_pairs)}組の積極活用を推奨"
            )
        
        # 2. 経験バランス改善
        newcomers = [p.staff_name for p in learning_patterns if p.experience_level == "新人"]
        veterans = [p.staff_name for p in learning_patterns if p.experience_level == "ベテラン"]
        
        if len(newcomers) > len(veterans):
            recommendations.append(
                f"新人{len(newcomers)}名に対しベテラン{len(veterans)}名でメンタリング体制強化が必要"
            )
        
        # 3. 緊急対応体制の提案
        emergency_ready = [e.staff_name for e in emergency_capacity if e.flexibility_score >= TEAM_DYNAMICS_PARAMETERS["emergency_ready_threshold"]]
        if len(emergency_ready) < 3:
            recommendations.append(
                "緊急対応可能スタッフが不足。クロストレーニング実施を推奨"
            )
        
        # 4. リスクペアの警告
        risky_pairs = [c for c in compatibility_results if c.compatibility_score < TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_risky"]]
        if risky_pairs:
            recommendations.append(
                f"相性に課題のあるペア{len(risky_pairs)}組について配置注意が必要"
            )
        
        return recommendations
    
    # ヘルパーメソッド群
    def _calculate_compatibility_score(self, staff1: str, staff2: str, 
                                     working_df: pd.DataFrame, collaboration_freq: float) -> float:
        """相性スコアの計算"""
        
        # 基本要因
        freq_score = min(collaboration_freq * 2, 1.0)  # 協働頻度
        
        # 勤務パターンの類似性
        pattern_similarity = self._calculate_pattern_similarity(staff1, staff2, working_df)
        
        # パフォーマンス指標（簡易版）
        performance_score = TEAM_DYNAMICS_PARAMETERS["performance_default_score"]  # 実際の実装では具体的なKPIを使用
        
        # 重み付き合成
        compatibility_score = (
            freq_score * TEAM_DYNAMICS_PARAMETERS["frequency_weight"] +
            pattern_similarity * TEAM_DYNAMICS_PARAMETERS["pattern_weight"] +
            performance_score * TEAM_DYNAMICS_PARAMETERS["performance_weight"]
        )
        
        return min(compatibility_score, 1.0)
    
    def _calculate_pattern_similarity(self, staff1: str, staff2: str, working_df: pd.DataFrame) -> float:
        """勤務パターンの類似性計算"""
        
        staff1_df = working_df[working_df['staff'] == staff1]
        staff2_df = working_df[working_df['staff'] == staff2]
        
        # 曜日パターンの類似性
        weekday1 = staff1_df.groupby(staff1_df['ds'].dt.dayofweek).size()
        weekday2 = staff2_df.groupby(staff2_df['ds'].dt.dayofweek).size()
        
        # コサイン類似度で計算
        weekday1_norm = weekday1.reindex(range(7), fill_value=0).values
        weekday2_norm = weekday2.reindex(range(7), fill_value=0).values
        
        if np.sum(weekday1_norm) > 0 and np.sum(weekday2_norm) > 0:
            similarity = 1 - cosine(weekday1_norm, weekday2_norm)
        else:
            similarity = 0.0
            
        return max(0.0, similarity)
    
    def _analyze_performance_impact(self, staff1: str, staff2: str, 
                                  working_df: pd.DataFrame, co_occurrence_days: Set) -> float:
        """パフォーマンス影響の分析"""
        
        # 簡易実装：共起日数に基づく影響度
        impact_score = min(len(co_occurrence_days) / TEAM_DYNAMICS_PARAMETERS["impact_normalization_days"], 1.0)  # 指定日数を上限として正規化
        
        return impact_score
    
    def _identify_compatibility_factors(self, staff1: str, staff2: str, 
                                      working_df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """相性要因の特定"""
        
        risk_factors = []
        synergy_factors = []
        
        staff1_df = working_df[working_df['staff'] == staff1]
        staff2_df = working_df[working_df['staff'] == staff2]
        
        # 勤務時間の重複度
        overlap_ratio = len(set(staff1_df['ds'].dt.date).intersection(set(staff2_df['ds'].dt.date))) / \
                       len(set(staff1_df['ds'].dt.date).union(set(staff2_df['ds'].dt.date)))
        
        if overlap_ratio > TEAM_DYNAMICS_PARAMETERS["overlap_ratio_high"]:
            synergy_factors.append("高い勤務時間重複")
        elif overlap_ratio < TEAM_DYNAMICS_PARAMETERS["overlap_ratio_low"]:
            risk_factors.append("勤務時間重複が少ない")
        
        # 職種の組み合わせ
        roles1 = set(staff1_df['role'].unique())
        roles2 = set(staff2_df['role'].unique())
        
        if len(roles1.intersection(roles2)) > 0:
            synergy_factors.append("同職種での連携可能")
        else:
            synergy_factors.append("異職種での補完関係")
        
        return risk_factors, synergy_factors
    
    def _generate_compatibility_recommendation(self, compatibility_score: float,
                                             collaboration_freq: float,
                                             performance_impact: float) -> str:
        """相性に基づく推奨事項"""
        
        if compatibility_score >= TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_high"]:
            return "積極的なペア配置を推奨"
        elif compatibility_score >= TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_decent"]:
            return "条件が合えばペア配置可能"
        elif compatibility_score >= TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_acceptable"]:
            return "短時間での組み合わせは可能"
        else:
            return "ペア配置は避けることを推奨"
    
    def _assess_experience_level(self, staff_df: pd.DataFrame) -> str:
        """経験レベルの判定"""
        
        total_days = len(staff_df['ds'].dt.date.unique())
        data_span = (staff_df['ds'].max() - staff_df['ds'].min()).days
        
        if total_days < TEAM_DYNAMICS_PARAMETERS["experience_newcomer_days"] or data_span < TEAM_DYNAMICS_PARAMETERS["experience_newcomer_span"]:
            return "新人"
        elif total_days < TEAM_DYNAMICS_PARAMETERS["experience_midlevel_days"] or data_span < TEAM_DYNAMICS_PARAMETERS["experience_midlevel_span"]:
            return "中堅"
        else:
            return "ベテラン"
    
    def _calculate_learning_speed(self, staff_df: pd.DataFrame) -> float:
        """学習速度の計算"""
        
        # 勤務区分の多様性増加率で学習速度を推定
        codes_over_time = []
        for week in staff_df['ds'].dt.isocalendar().week.unique():
            week_df = staff_df[staff_df['ds'].dt.isocalendar().week == week]
            codes_over_time.append(len(week_df['code'].unique()))
        
        if len(codes_over_time) > 1:
            # 線形回帰で増加率を計算
            x = np.arange(len(codes_over_time))
            slope, _, _, _, _ = stats.linregress(x, codes_over_time)
            learning_speed = max(0.0, min(slope / TEAM_DYNAMICS_PARAMETERS["slope_normalization_factor"], 1.0))  # 正規化
        else:
            learning_speed = TEAM_DYNAMICS_PARAMETERS["learning_default_speed"]  # デフォルト値
            
        return learning_speed
    
    def _identify_skill_growth_areas(self, staff_df: pd.DataFrame) -> List[str]:
        """スキル成長領域の特定"""
        
        # 使用頻度の低い勤務区分を成長領域として特定
        code_counts = staff_df['code'].value_counts()
        growth_areas = code_counts[code_counts <= TEAM_DYNAMICS_PARAMETERS["skill_growth_min_frequency"]].index.tolist()
        
        return growth_areas[:TEAM_DYNAMICS_PARAMETERS["max_growth_areas"]]  # 上位指定数まで
    
    def _assess_mentoring_capacity(self, staff_df: pd.DataFrame, experience_level: str) -> float:
        """メンタリング能力の評価"""
        
        if experience_level == "ベテラン":
            # 勤務区分の多様性をメンタリング能力の指標とする
            code_diversity = len(staff_df['code'].unique())
            mentoring_capacity = min(code_diversity / TEAM_DYNAMICS_PARAMETERS["mentoring_diversity_factor"], 1.0)
        elif experience_level == "中堅":
            mentoring_capacity = TEAM_DYNAMICS_PARAMETERS["mentoring_capacity_default"]
        else:
            mentoring_capacity = TEAM_DYNAMICS_PARAMETERS["mentoring_capacity_low"]
            
        return mentoring_capacity
    
    def _identify_optimal_mentors(self, staff: str, working_df: pd.DataFrame, 
                                experience_level: str) -> List[str]:
        """最適メンターの特定"""
        
        if experience_level == "ベテラン":
            return []  # ベテランにはメンターは不要
        
        # 同じ職種のベテランを探す
        staff_role = working_df[working_df['staff'] == staff]['role'].iloc[0] if not working_df[working_df['staff'] == staff].empty else None
        
        potential_mentors = []
        for mentor_candidate in working_df['staff'].unique():
            if mentor_candidate != staff:
                mentor_df = working_df[working_df['staff'] == mentor_candidate]
                mentor_exp_level = self._assess_experience_level(mentor_df)
                mentor_role = mentor_df['role'].iloc[0] if not mentor_df.empty else None
                
                if (mentor_exp_level == "ベテラン" and 
                    mentor_role == staff_role):
                    potential_mentors.append(mentor_candidate)
        
        return potential_mentors[:TEAM_DYNAMICS_PARAMETERS["max_mentors_per_person"]]  # 最大指定人数
    
    def _generate_task_recommendations(self, experience_level: str, 
                                     skill_growth_areas: List[str]) -> List[str]:
        """推奨タスクの生成"""
        
        if experience_level == "新人":
            return ["基本業務の習得", "メンター同行", "安全手順の確認"]
        elif experience_level == "中堅":
            return ["新人指導", "専門スキル向上", "リーダーシップ発揮"]
        else:
            return ["メンタリング", "品質管理", "業務改善提案"]
    
    def _calculate_flexibility_score(self, staff_df: pd.DataFrame) -> float:
        """柔軟性スコアの計算"""
        
        # 勤務パターンの変動性を柔軟性の指標とする
        weekday_variance = staff_df.groupby(staff_df['ds'].dt.dayofweek).size().var()
        code_diversity = len(staff_df['code'].unique())
        
        flexibility = min((code_diversity / TEAM_DYNAMICS_PARAMETERS["flexibility_code_factor"] + 1 / (1 + weekday_variance)) / TEAM_DYNAMICS_PARAMETERS["flexibility_variance_weight"], 1.0)
        
        return flexibility
    
    def _assess_cross_training_level(self, staff_df: pd.DataFrame) -> float:
        """クロストレーニングレベルの評価"""
        
        # 複数職種・複数勤務区分への対応度
        role_count = len(staff_df['role'].unique())
        code_count = len(staff_df['code'].unique())
        
        cross_training_level = min((role_count + code_count) / TEAM_DYNAMICS_PARAMETERS["cross_training_normalization_factor"], 1.0)
        
        return cross_training_level
    
    def _assess_stress_resilience(self, staff_df: pd.DataFrame) -> float:
        """ストレス耐性の評価"""
        
        # 連続勤務日数と勤務時間の変動への適応性
        consecutive_days = self._calculate_max_consecutive(staff_df)
        hours_variance = staff_df['parsed_slots_count'].var()
        
        resilience = min(consecutive_days / TEAM_DYNAMICS_PARAMETERS["stress_consecutive_days_factor"] + 1 / (1 + hours_variance), 1.0)
        
        return resilience
    
    def _calculate_emergency_availability(self, staff_df: pd.DataFrame) -> float:
        """緊急時対応可能性の計算"""
        
        # 勤務頻度と柔軟性から緊急対応可能性を推定
        total_days = len(staff_df['ds'].dt.date.unique())
        data_span = (staff_df['ds'].max() - staff_df['ds'].min()).days
        
        availability = min(total_days / max(data_span, 1) * TEAM_DYNAMICS_PARAMETERS["emergency_availability_factor"], 1.0)
        
        return availability
    
    def _identify_backup_roles(self, staff_df: pd.DataFrame) -> List[str]:
        """バックアップ可能役割の特定"""
        
        return staff_df['role'].unique().tolist()
    
    def _categorize_response_time(self, flexibility_score: float, 
                                emergency_availability: float) -> str:
        """対応時間カテゴリの分類"""
        
        combined_score = (flexibility_score + emergency_availability) / 2
        
        if combined_score >= TEAM_DYNAMICS_PARAMETERS["response_time_instant_threshold"]:
            return "即座対応可能"
        elif combined_score >= TEAM_DYNAMICS_PARAMETERS["response_time_quick_threshold"]:
            return "短時間で対応可能"
        elif combined_score >= TEAM_DYNAMICS_PARAMETERS["response_time_adjusted_threshold"]:
            return "調整後対応可能"
        else:
            return "対応困難"
    
    def _calculate_max_consecutive(self, staff_df: pd.DataFrame) -> int:
        """最大連続勤務日数の計算"""
        
        dates = sorted(staff_df['ds'].dt.date.unique())
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
                
        return max_consecutive
    
    def _assess_consecutive_tolerance(self, staff_df: pd.DataFrame) -> float:
        """連続勤務耐性の評価"""
        
        max_consecutive = self._calculate_max_consecutive(staff_df)
        tolerance = min(max_consecutive / TEAM_DYNAMICS_PARAMETERS["consecutive_tolerance_factor"], 1.0)  # 指定日数を上限として正規化
        
        return tolerance
    
    def _assess_peak_period_performance(self, staff_df: pd.DataFrame) -> float:
        """繁忙期対応力の評価"""
        
        # 月末（指定日以降）の勤務頻度で繁忙期対応力を評価
        month_end_days = staff_df[staff_df['ds'].dt.day >= TEAM_DYNAMICS_PARAMETERS["month_end_threshold"]]
        total_month_end_possible = len(staff_df[staff_df['ds'].dt.day >= TEAM_DYNAMICS_PARAMETERS["month_end_threshold"]]['ds'].dt.date.unique())
        
        if total_month_end_possible > 0:
            peak_performance = len(month_end_days) / total_month_end_possible
        else:
            peak_performance = 0.5
            
        return min(peak_performance, 1.0)
    
    def _categorize_stress_level(self, overall_resilience: float) -> str:
        """ストレスレベルのカテゴリ分類"""
        
        if overall_resilience >= TEAM_DYNAMICS_PARAMETERS["stress_high_threshold"]:
            return "高ストレス耐性"
        elif overall_resilience >= TEAM_DYNAMICS_PARAMETERS["stress_medium_threshold"]:
            return "中ストレス耐性"
        elif overall_resilience >= TEAM_DYNAMICS_PARAMETERS["stress_low_threshold"]:
            return "低ストレス耐性"
        else:
            return "ストレス注意"
    
    def _assess_experience_balance(self, exp1: str, exp2: str) -> str:
        """経験バランスの評価"""
        
        if exp1 == exp2:
            return f"同レベル（{exp1}）"
        elif (exp1 == "ベテラン" and exp2 == "新人") or (exp1 == "新人" and exp2 == "ベテラン"):
            return "メンタリング関係"
        else:
            return "バランス良好"
    
    def _assess_learning_potential(self, staff1: str, staff2: str, 
                                 learning_patterns: List[LearningPattern]) -> float:
        """学習ポテンシャルの評価"""
        
        pattern1 = next((p for p in learning_patterns if p.staff_name == staff1), None)
        pattern2 = next((p for p in learning_patterns if p.staff_name == staff2), None)
        
        if pattern1 and pattern2:
            learning_potential = (pattern1.learning_speed + pattern2.learning_speed) / 2
        else:
            learning_potential = 0.5
            
        return learning_potential
    
    def _identify_optimal_scenarios(self, pair: TeamCompatibility, 
                                  team_characteristics: Dict[str, any]) -> List[str]:
        """最適シナリオの特定"""
        
        scenarios = []
        
        if team_characteristics['emergency_coverage']:
            scenarios.append("緊急時対応")
        
        if team_characteristics['experience_balance'] == "メンタリング関係":
            scenarios.append("新人指導")
        
        if pair.compatibility_score >= TEAM_DYNAMICS_PARAMETERS["compatibility_threshold_excellent"]:
            scenarios.append("重要業務担当")
        
        if not scenarios:
            scenarios.append("通常業務")
        
        return scenarios


def analyze_team_dynamics(long_df: pd.DataFrame) -> Dict[str, any]:
    """
    チームダイナミクス分析のメイン関数
    
    Args:
        long_df: 勤務データ
        
    Returns:
        チームダイナミクス分析結果
    """
    analyzer = TeamDynamicsAnalyzer()
    return analyzer.analyze_team_dynamics(long_df)