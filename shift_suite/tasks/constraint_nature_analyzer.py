"""
勤務制約の性質判別分析エンジン

このモジュールは、スタッフの勤務パターンから「制約の性質」を高精度で判別します。
例：週3日勤務 → 上限制約なのか、下限希望なのか、固定希望なのかを統計的に判定

Author: Claude Code Assistant  
Created: 2025-01-14
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Literal
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks

from .constants import CONSTRAINT_ANALYSIS_PARAMETERS

log = logging.getLogger(__name__)

class ConstraintType(Enum):
    """制約の性質を表す列挙型"""
    UPPER_LIMIT = "上限制約"      # 「週3日まで」- 超えることができない制約
    LOWER_LIMIT = "下限希望"      # 「週3日以上」- 最低限確保したい希望
    FIXED_PREFERENCE = "固定希望"  # 「週3日がベスト」- この日数が最適
    FLEXIBLE_PATTERN = "柔軟パターン"  # 特に制約なし、状況に応じて変動
    SEASONAL_CONSTRAINT = "季節制約"   # 特定時期のみの制約
    UNCERTAIN = "判定不能"        # データが不十分で判定できない

@dataclass
class ConstraintAnalysis:
    """制約分析結果を格納するクラス"""
    staff_name: str
    constraint_type: ConstraintType
    confidence_score: float  # 判定の信頼度 (0.0-1.0)
    threshold_value: float   # 制約の閾値（週○日、月○日等）
    evidence: Dict[str, any]  # 判定根拠となった統計的証拠
    recommendations: List[str]  # シフト作成者への推奨事項

class ConstraintNatureAnalyzer:
    """勤務制約の性質を判別する高度分析エンジン"""
    
    def __init__(self):
        self.min_observation_weeks = CONSTRAINT_ANALYSIS_PARAMETERS["min_observation_weeks"]  # 最小観測期間（週）
        self.confidence_threshold = CONSTRAINT_ANALYSIS_PARAMETERS["confidence_threshold"]  # 判定に必要な最低信頼度
        
    def analyze_weekly_constraints(self, long_df: pd.DataFrame) -> List[ConstraintAnalysis]:
        """
        週勤務日数制約の性質を判別
        
        Args:
            long_df: 勤務データ
            
        Returns:
            制約分析結果のリスト
        """
        if long_df.empty:
            return []
            
        log.info("🔍 週勤務日数制約の性質判別分析を開始...")
        
        # 週ごとのデータ準備
        working_df = long_df[long_df['parsed_slots_count'] > 0].copy()
        working_df['week'] = working_df['ds'].dt.isocalendar().week
        working_df['year'] = working_df['ds'].dt.year
        working_df['year_week'] = working_df['year'].astype(str) + '_' + working_df['week'].astype(str)
        
        results = []
        
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            analysis = self._analyze_individual_weekly_pattern(staff, staff_df)
            if analysis:
                results.append(analysis)
                
        return results
    
    def _analyze_individual_weekly_pattern(self, staff: str, staff_df: pd.DataFrame) -> Optional[ConstraintAnalysis]:
        """個人の週勤務パターンを詳細分析"""
        
        # 週ごとの勤務日数を計算
        weekly_counts = staff_df.groupby('year_week')['ds'].nunique()
        
        if len(weekly_counts) < self.min_observation_weeks:
            return ConstraintAnalysis(
                staff_name=staff,
                constraint_type=ConstraintType.UNCERTAIN,
                confidence_score=0.0,
                threshold_value=0.0,
                evidence={"reason": "観測期間が不十分", "weeks": len(weekly_counts)},
                recommendations=["より長期間のデータが必要"]
            )
        
        # 基本統計量
        mean_days = weekly_counts.mean()
        std_days = weekly_counts.std()
        min_days = weekly_counts.min()
        max_days = weekly_counts.max()
        mode_days = weekly_counts.mode().iloc[0] if not weekly_counts.mode().empty else mean_days
        
        # 1. 上限制約の判定
        upper_limit_analysis = self._detect_upper_limit_constraint(weekly_counts, mean_days, std_days, max_days)
        
        # 2. 下限希望の判定  
        lower_limit_analysis = self._detect_lower_limit_preference(weekly_counts, mean_days, std_days, min_days)
        
        # 3. 固定希望の判定
        fixed_preference_analysis = self._detect_fixed_preference(weekly_counts, mode_days, std_days)
        
        # 4. 季節制約の判定
        seasonal_analysis = self._detect_seasonal_constraints(staff_df, weekly_counts)
        
        # 5. 柔軟パターンの判定
        flexible_analysis = self._detect_flexible_pattern(weekly_counts, std_days, mean_days)
        
        # 6. 最も確信度の高い判定を選択
        analyses = [
            upper_limit_analysis,
            lower_limit_analysis, 
            fixed_preference_analysis,
            seasonal_analysis,
            flexible_analysis
        ]
        
        best_analysis = max(analyses, key=lambda x: x.confidence_score)
        
        # 信頼度が閾値を下回る場合は不確定とする
        if best_analysis.confidence_score < self.confidence_threshold:
            best_analysis.constraint_type = ConstraintType.UNCERTAIN
            best_analysis.recommendations.append("判定信頼度が低いため追加データが必要")
            
        return best_analysis
    
    def _detect_upper_limit_constraint(self, weekly_counts: pd.Series, mean_days: float, 
                                     std_days: float, max_days: int) -> ConstraintAnalysis:
        """上限制約の検出"""
        
        evidence = {}
        confidence = 0.0
        threshold = max_days
        recommendations = []
        
        # 判定基準1: 最大値が一定で変動が小さい
        if std_days < CONSTRAINT_ANALYSIS_PARAMETERS["low_variation_threshold"]:  # 変動が非常に小さい
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["low_variation_evidence_weight"]
            evidence["low_variation"] = f"標準偏差{std_days:.2f} < {CONSTRAINT_ANALYSIS_PARAMETERS['low_variation_threshold']}"
            
        # 判定基準2: 最大値を超える週が皆無
        exceed_weeks = (weekly_counts > max_days).sum()
        if exceed_weeks == 0:
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["no_exceed_evidence_weight"]
            evidence["no_exceed"] = "最大値を超える週が0週"
        
        # 判定基準3: 最大値近辺での頻度が高い
        near_max_ratio = (weekly_counts >= max_days - 0.5).mean()
        if near_max_ratio >= CONSTRAINT_ANALYSIS_PARAMETERS["near_max_ratio_threshold"]:  # 指定%以上が最大値近辺
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
            evidence["concentrated_at_max"] = f"最大値近辺の週が{near_max_ratio:.1%}"
            
        # 判定基準4: 段階的減少パターン（上限に向けた調整）
        gradual_increase = self._detect_gradual_trend_to_limit(weekly_counts, max_days)
        if gradual_increase:
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["consistency_bonus_weight"]
            evidence["gradual_approach"] = "上限に向けた段階的調整パターンを検出"
            
        if confidence >= self.confidence_threshold:
            recommendations.extend([
                f"週{threshold}日が上限制約の可能性が高い",
                "緊急時以外は超過させない",
                "本人の制約事情を確認することを推奨"
            ])
        
        return ConstraintAnalysis(
            staff_name="",
            constraint_type=ConstraintType.UPPER_LIMIT,
            confidence_score=confidence,
            threshold_value=threshold,
            evidence=evidence,
            recommendations=recommendations
        )
    
    def _detect_lower_limit_preference(self, weekly_counts: pd.Series, mean_days: float,
                                     std_days: float, min_days: int) -> ConstraintAnalysis:
        """下限希望の検出"""
        
        evidence = {}
        confidence = 0.0
        threshold = min_days
        recommendations = []
        
        # 判定基準1: 最小値を下回る週が皆無または極少
        below_min_weeks = (weekly_counts < min_days).sum()
        below_min_ratio = below_min_weeks / len(weekly_counts)
        
        if below_min_ratio <= CONSTRAINT_ANALYSIS_PARAMETERS["below_min_ratio_threshold"]:  # 指定%以下
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["low_variation_evidence_weight"]
            evidence["rare_below_min"] = f"最小値未満の週が{below_min_ratio:.1%}"
            
        # 判定基準2: 最小値以上での分布が右寄り
        above_min_counts = weekly_counts[weekly_counts >= min_days]
        if len(above_min_counts) > 0:
            skewness = stats.skew(above_min_counts)
            if skewness > CONSTRAINT_ANALYSIS_PARAMETERS["skewness_threshold"]:  # 右寄り分布
                confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
                evidence["right_skewed"] = f"最小値以上の分布が右寄り(歪度{skewness:.2f})"
                
        # 判定基準3: 緊急時・繁忙期での増加パターン
        peak_weeks = self._detect_peak_weeks(weekly_counts)
        if len(peak_weeks) > 0:
            avg_peak = weekly_counts.iloc[peak_weeks].mean()
            if avg_peak > mean_days + std_days:
                confidence += 0.2
                evidence["emergency_increase"] = f"繁忙期に平均+1σ超えで対応({avg_peak:.1f}日)"
                
        # 判定基準4: 時系列での上昇トレンド
        trend_slope = self._calculate_trend_slope(weekly_counts)
        if trend_slope > CONSTRAINT_ANALYSIS_PARAMETERS["trend_slope_threshold"]:  # 上昇傾向
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
            evidence["upward_trend"] = f"週勤務日数の上昇トレンド(傾き{trend_slope:.3f})"
            
        if confidence >= self.confidence_threshold:
            recommendations.extend([
                f"週{threshold}日が下限希望の可能性が高い",
                "収入確保等の理由で最低限の勤務日数を維持したい",
                "可能な範囲で追加勤務の打診を検討"
            ])
            
        return ConstraintAnalysis(
            staff_name="",
            constraint_type=ConstraintType.LOWER_LIMIT,
            confidence_score=confidence,
            threshold_value=threshold,
            evidence=evidence,
            recommendations=recommendations
        )
    
    def _detect_fixed_preference(self, weekly_counts: pd.Series, mode_days: float, 
                               std_days: float) -> ConstraintAnalysis:
        """固定希望の検出"""
        
        evidence = {}
        confidence = 0.0
        threshold = mode_days
        recommendations = []
        
        # 判定基準1: 最頻値の集中度が高い
        mode_ratio = (weekly_counts == mode_days).mean()
        if mode_ratio >= CONSTRAINT_ANALYSIS_PARAMETERS["mode_concentration_threshold"]:  # 指定%以上が最頻値
            confidence += 0.5
            evidence["high_mode_concentration"] = f"最頻値{mode_days}日の週が{mode_ratio:.1%}"
            
        # 判定基準2: 標準偏差が小さい（安定性）
        if std_days < CONSTRAINT_ANALYSIS_PARAMETERS["mode_concentration_threshold"]:
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["no_exceed_evidence_weight"]
            evidence["low_standard_deviation"] = f"標準偏差{std_days:.2f} < 0.7"
            
        # 判定基準3: 最頻値からの乖離が両側に分散
        deviations = weekly_counts - mode_days
        positive_dev = (deviations > 0).sum()
        negative_dev = (deviations < 0).sum()
        
        if positive_dev > 0 and negative_dev > 0:
            balance_ratio = min(positive_dev, negative_dev) / max(positive_dev, negative_dev)
            if balance_ratio >= CONSTRAINT_ANALYSIS_PARAMETERS["deviation_balance_threshold"]:  # 両側に指定%以上の比率で分散
                confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
                evidence["balanced_deviation"] = f"最頻値からの乖離が両側に分散(バランス比{balance_ratio:.2f})"
                
        if confidence >= self.confidence_threshold:
            recommendations.extend([
                f"週{threshold:.0f}日が固定希望の可能性が高い",
                "ワークライフバランス重視",
                "この日数での安定的なシフト組みを継続"
            ])
            
        return ConstraintAnalysis(
            staff_name="",
            constraint_type=ConstraintType.FIXED_PREFERENCE,
            confidence_score=confidence,
            threshold_value=threshold,
            evidence=evidence,
            recommendations=recommendations
        )
    
    def _detect_seasonal_constraints(self, staff_df: pd.DataFrame, 
                                   weekly_counts: pd.Series) -> ConstraintAnalysis:
        """季節制約の検出"""
        
        evidence = {}
        confidence = 0.0
        threshold = weekly_counts.mean()
        recommendations = []
        
        # 月別の勤務日数パターン分析
        staff_df['month'] = staff_df['ds'].dt.month
        monthly_pattern = staff_df.groupby(['year_week', 'month'])['ds'].nunique().reset_index()
        
        if len(monthly_pattern) < 12:  # 1年未満のデータ
            return ConstraintAnalysis(
                staff_name="",
                constraint_type=ConstraintType.SEASONAL_CONSTRAINT,
                confidence_score=0.0,
                threshold_value=threshold,
                evidence={"insufficient_data": "季節性判定に必要な1年分のデータが不足"},
                recommendations=["季節制約判定には1年以上のデータが必要"]
            )
            
        # 季節変動の検出
        monthly_avg = monthly_pattern.groupby('month')['ds'].mean()
        seasonal_variance = monthly_avg.var()
        overall_variance = weekly_counts.var()
        
        if seasonal_variance > overall_variance * CONSTRAINT_ANALYSIS_PARAMETERS["low_variation_threshold"]:  # 季節変動が全体変動の指定%以上
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["low_variation_evidence_weight"]
            evidence["seasonal_variance"] = f"季節変動が全体変動の{seasonal_variance/overall_variance:.1%}"
            
            # 特定月での極端な変化を検出
            max_month = monthly_avg.idxmax()
            min_month = monthly_avg.idxmin()
            range_ratio = (monthly_avg.max() - monthly_avg.min()) / monthly_avg.mean()
            
            if range_ratio > CONSTRAINT_ANALYSIS_PARAMETERS["range_variation_threshold"]:  # 指定%以上の変動
                confidence += CONSTRAINT_ANALYSIS_PARAMETERS["no_exceed_evidence_weight"]
                evidence["extreme_seasonal_change"] = f"{max_month}月最多({monthly_avg.max():.1f}日), {min_month}月最少({monthly_avg.min():.1f}日)"
                recommendations.extend([
                    f"{max_month}月は勤務増加傾向",
                    f"{min_month}月は勤務制限傾向",
                    "季節的な個人事情（学校行事、家族の休暇等）の可能性"
                ])
                
        return ConstraintAnalysis(
            staff_name="",
            constraint_type=ConstraintType.SEASONAL_CONSTRAINT,
            confidence_score=confidence,
            threshold_value=threshold,
            evidence=evidence,
            recommendations=recommendations
        )
    
    def _detect_flexible_pattern(self, weekly_counts: pd.Series, std_days: float, 
                               mean_days: float) -> ConstraintAnalysis:
        """柔軟パターンの検出"""
        
        evidence = {}
        confidence = 0.0
        threshold = mean_days
        recommendations = []
        
        # 判定基準1: 変動が大きい
        if std_days > CONSTRAINT_ANALYSIS_PARAMETERS["flexibility_std_threshold"]:
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["no_exceed_evidence_weight"]
            evidence["high_variation"] = f"標準偏差{std_days:.2f} > {CONSTRAINT_ANALYSIS_PARAMETERS['flexibility_std_threshold']}"
            
        # 判定基準2: 広い範囲に分散
        range_days = weekly_counts.max() - weekly_counts.min()
        if range_days >= 3:  # 3日以上の幅
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["no_exceed_evidence_weight"]
            evidence["wide_range"] = f"勤務日数の幅{range_days}日 >= 3日"
            
        # 判定基準3: 特定の値への集中がない
        value_counts = weekly_counts.value_counts()
        max_concentration = value_counts.max() / len(weekly_counts)
        if max_concentration < CONSTRAINT_ANALYSIS_PARAMETERS["max_concentration_threshold"]:  # 最頻値でも指定%未満
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
            evidence["no_strong_preference"] = f"最大集中度{max_concentration:.1%} < {CONSTRAINT_ANALYSIS_PARAMETERS['max_concentration_threshold']:.0%}"
            
        # 判定基準4: ランダム性の検証（ラン検定）
        median_days = weekly_counts.median()
        runs = self._count_runs(weekly_counts, median_days)
        expected_runs = len(weekly_counts) / 2
        if abs(runs - expected_runs) / expected_runs < CONSTRAINT_ANALYSIS_PARAMETERS["random_pattern_tolerance"]:  # 期待値の±指定%以内
            confidence += CONSTRAINT_ANALYSIS_PARAMETERS["high_concentration_weight"]
            evidence["random_pattern"] = f"ラン数{runs}が期待値{expected_runs:.1f}に近い"
            
        if confidence >= self.confidence_threshold:
            recommendations.extend([
                "柔軟な勤務パターン（特定の制約なし）",
                "状況に応じて勤務日数を調整可能",
                "繁忙期の戦力として活用可能"
            ])
            
        return ConstraintAnalysis(
            staff_name="",
            constraint_type=ConstraintType.FLEXIBLE_PATTERN,
            confidence_score=confidence,
            threshold_value=threshold,
            evidence=evidence,
            recommendations=recommendations
        )
    
    def _detect_gradual_trend_to_limit(self, weekly_counts: pd.Series, limit: int) -> bool:
        """上限に向けた段階的調整パターンの検出"""
        if len(weekly_counts) < 4:
            return False
            
        # 最近4週の傾向を分析
        recent_weeks = weekly_counts.tail(4)
        trend_to_limit = all(recent_weeks >= recent_weeks.iloc[0])  # 単調増加
        near_limit = recent_weeks.mean() >= limit - 0.5  # 上限近辺
        
        return trend_to_limit and near_limit
    
    def _detect_peak_weeks(self, weekly_counts: pd.Series) -> List[int]:
        """勤務日数のピーク週を検出"""
        if len(weekly_counts) < 5:
            return []
            
        # scipy.signal.find_peaksを使用してピークを検出
        peaks, _ = find_peaks(weekly_counts.values, height=weekly_counts.mean() + weekly_counts.std())
        return peaks.tolist()
    
    def _calculate_trend_slope(self, weekly_counts: pd.Series) -> float:
        """時系列トレンドの傾きを計算"""
        if len(weekly_counts) < 3:
            return 0.0
            
        x = np.arange(len(weekly_counts))
        slope, _, _, _, _ = stats.linregress(x, weekly_counts.values)
        return slope
    
    def _count_runs(self, series: pd.Series, threshold: float) -> int:
        """ラン検定用のラン数を計算"""
        binary = (series > threshold).astype(int)
        runs = 1
        for i in range(1, len(binary)):
            if binary.iloc[i] != binary.iloc[i-1]:
                runs += 1
        return runs


def analyze_constraint_nature(long_df: pd.DataFrame) -> Dict[str, List[ConstraintAnalysis]]:
    """
    勤務制約の性質を包括的に分析
    
    Args:
        long_df: 勤務データ
        
    Returns:
        制約分析結果の辞書
    """
    analyzer = ConstraintNatureAnalyzer()
    
    results = {
        "weekly_constraints": analyzer.analyze_weekly_constraints(long_df),
        # 将来的に月次制約、時間帯制約等も追加可能
    }
    
    return results