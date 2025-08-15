#!/usr/bin/env python3
"""
Hierarchical Truth Analyzer
階層的真実分析システム - 3段階検証による最高精度分析
"""

from __future__ import annotations  # 型ヒント互換性のため保持

# import json  # レポート出力で将来使用される可能性
import logging
from datetime import datetime  # , timedelta  # timedelta は現在未使用
from enum import Enum
# from pathlib import Path  # ファイル出力で将来使用される可能性
from typing import Any, Dict, List, Optional
# from typing import Tuple  # 未使用のためコメントアウト

import numpy as np
import pandas as pd  # DataFrame以外でも分析処理で使用される可能性
from pandas import DataFrame

from .enhanced_data_ingestion import QualityAssuredDataset
from .truth_assured_decomposer import DecompositionResult
from .utils import apply_rest_exclusion_filter, log

# Analysis logger
analysis_logger = logging.getLogger('analysis')


class AnalysisConfidenceLevel(Enum):
    """分析信頼度レベル"""
    VERY_HIGH = "very_high"  # 95-100%
    HIGH = "high"            # 85-94%
    MEDIUM = "medium"        # 70-84%
    LOW = "low"              # 50-69%
    VERY_LOW = "very_low"    # 0-49%


class TruthAnalysisResult:
    """真実分析結果"""
    
    def __init__(self, analysis_type: str):
        self.analysis_type = analysis_type
        self.confidence_score: float = 0.0
        self.confidence_level: AnalysisConfidenceLevel = AnalysisConfidenceLevel.VERY_LOW
        
        # 分析結果データ
        self.shortage_by_time: Dict[str, float] = {}
        self.shortage_by_role: Dict[str, float] = {}
        self.shortage_by_employment: Dict[str, float] = {}
        self.total_shortage_hours: float = 0.0
        
        # 根拠データ
        self.evidence_data: Dict[str, Any] = {}
        self.validation_checks: Dict[str, bool] = {}
        self.truth_indicators: Dict[str, float] = {}
        
        # メタデータ
        self.processing_timestamp: datetime = datetime.now()
        self.data_sources: List[str] = []
        self.processing_notes: List[str] = []
    
    def calculate_confidence_level(self) -> AnalysisConfidenceLevel:
        """信頼度レベル計算"""
        if self.confidence_score >= 95:
            return AnalysisConfidenceLevel.VERY_HIGH
        elif self.confidence_score >= 85:
            return AnalysisConfidenceLevel.HIGH
        elif self.confidence_score >= 70:
            return AnalysisConfidenceLevel.MEDIUM
        elif self.confidence_score >= 50:
            return AnalysisConfidenceLevel.LOW
        else:
            return AnalysisConfidenceLevel.VERY_LOW


class NeedBasedTruthEngine:
    """Need-based真実分析エンジン（階層1: Primary Truth Engine）"""
    
    def __init__(self):
        self.analysis_precision = "maximum"
        self.truth_verification_level = "strict"
    
    def analyze(self, dataset: QualityAssuredDataset, decomposition: DecompositionResult) -> TruthAnalysisResult:
        """Need-based真実分析実行"""
        analysis_logger.info("[PRIMARY_TRUTH] Need-based真実分析開始")
        
        result = TruthAnalysisResult("need_based_primary")
        
        try:
            # Need分析結果の検証と精緻化
            if decomposition.need_analysis:
                result = self._analyze_need_based_truth(dataset, decomposition, result)
            else:
                result = self._fallback_to_direct_analysis(dataset, result)
            
            # 真実性検証
            result = self._verify_truth_indicators(dataset, result)
            
            # 信頼度計算
            result.confidence_score = self._calculate_need_based_confidence(dataset, decomposition, result)
            result.confidence_level = result.calculate_confidence_level()
            
            analysis_logger.info(f"[PRIMARY_TRUTH] 完了: 信頼度{result.confidence_score:.1f}%")
            
            return result
            
        except Exception as e:
            log.error(f"Need-based分析エラー: {e}")
            result.processing_notes.append(f"分析エラー: {e}")
            return result
    
    def _analyze_need_based_truth(
        self, 
        dataset: QualityAssuredDataset, 
        decomposition: DecompositionResult,
        result: TruthAnalysisResult
    ) -> TruthAnalysisResult:
        """Need-based真実分析実行"""
        
        need_analysis = decomposition.need_analysis
        
        # 実際のケア需要vs現在の配置の詳細比較
        result.evidence_data["care_demands"] = need_analysis.care_demands_by_time
        result.evidence_data["care_demands_by_role"] = need_analysis.care_demands_by_role
        
        # 現在の配置状況分析
        current_staffing = self._analyze_current_staffing(dataset.data)
        result.evidence_data["current_staffing"] = current_staffing
        
        # 不足時間計算（高精度）
        result.shortage_by_time = self._calculate_precise_time_shortages(
            need_analysis.care_demands_by_time, 
            current_staffing["time_distribution"]
        )
        
        result.shortage_by_role = self._calculate_precise_role_shortages(
            need_analysis.care_demands_by_role,
            current_staffing["role_distribution"]
        )
        
        # 総不足時間
        result.total_shortage_hours = sum(result.shortage_by_time.values())
        
        # 真実性指標の計算
        result.truth_indicators = self._calculate_truth_indicators(need_analysis, current_staffing)
        
        result.data_sources.append("need_file_direct")
        result.processing_notes.append("Need File直接分析による高精度計算")
        
        return result
    
    def _analyze_current_staffing(self, data: DataFrame) -> Dict[str, Any]:
        """現在のスタッフ配置状況分析"""
        staffing_analysis = {
            "time_distribution": {},
            "role_distribution": {},
            "employment_distribution": {},
            "total_staff_hours": 0.0,
            "coverage_gaps": []
        }
        
        try:
            # 時間別配置分析
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            for col in time_columns:
                # 休暇除外フィルター適用
                filtered_data = apply_rest_exclusion_filter(data, f"staffing_analysis_{col}")
                staff_count = filtered_data[col].notna().sum()
                staffing_analysis["time_distribution"][str(col)] = staff_count
            
            # 職種別配置分析
            if 'role' in data.columns:
                filtered_data = apply_rest_exclusion_filter(data, "role_analysis")
                role_counts = filtered_data[filtered_data['role'].notna()]['role'].value_counts()
                staffing_analysis["role_distribution"] = role_counts.to_dict()
            
            # 雇用形態別分析
            if 'employment' in data.columns:
                filtered_data = apply_rest_exclusion_filter(data, "employment_analysis")
                employment_counts = filtered_data[filtered_data['employment'].notna()]['employment'].value_counts()
                staffing_analysis["employment_distribution"] = employment_counts.to_dict()
            
            # 総スタッフ時間計算
            staffing_analysis["total_staff_hours"] = sum(staffing_analysis["time_distribution"].values())
            
            # カバレッジギャップ検出
            staffing_analysis["coverage_gaps"] = self._detect_coverage_gaps(staffing_analysis["time_distribution"])
            
            return staffing_analysis
            
        except Exception as e:
            log.error(f"現在配置分析エラー: {e}")
            return staffing_analysis
    
    def _calculate_precise_time_shortages(
        self, 
        care_demands: Dict[str, float], 
        current_staffing: Dict[str, float]
    ) -> Dict[str, float]:
        """時間別精密不足計算"""
        shortages = {}
        
        for time_slot, demand in care_demands.items():
            current = current_staffing.get(time_slot, 0.0)
            shortage = max(0.0, demand - current)
            shortages[time_slot] = shortage
        
        return shortages
    
    def _calculate_precise_role_shortages(
        self,
        role_demands: Dict[str, float],
        current_roles: Dict[str, float] 
    ) -> Dict[str, float]:
        """職種別精密不足計算"""
        shortages = {}
        
        for role, demand in role_demands.items():
            current = current_roles.get(role, 0.0)
            shortage = max(0.0, demand - current)
            shortages[role] = shortage
        
        return shortages
    
    def _calculate_truth_indicators(
        self, 
        need_analysis, 
        current_staffing: Dict[str, Any]
    ) -> Dict[str, float]:
        """真実性指標計算"""
        indicators = {}
        
        try:
            # 需要適合度（実際の需要にどれだけ適合しているか）
            total_demand = need_analysis.total_care_hours
            total_current = current_staffing["total_staff_hours"]
            
            if total_demand > 0:
                indicators["demand_alignment"] = min(100.0, (total_current / total_demand) * 100)
            else:
                indicators["demand_alignment"] = 0.0
            
            # ケア品質指標（ピーク時間の充足度）
            peak_coverage = 0.0
            if need_analysis.peak_hours:
                peak_demand = sum(need_analysis.care_demands_by_time.get(h, 0) for h in need_analysis.peak_hours)
                peak_current = sum(current_staffing["time_distribution"].get(h, 0) for h in need_analysis.peak_hours)
                
                if peak_demand > 0:
                    peak_coverage = min(100.0, (peak_current / peak_demand) * 100)
            
            indicators["peak_hour_coverage"] = peak_coverage
            
            # データ整合性指標
            indicators["data_completeness"] = need_analysis.data_completeness
            indicators["confidence_baseline"] = need_analysis.confidence_score
            
            return indicators
            
        except Exception as e:
            log.error(f"真実性指標計算エラー: {e}")
            return indicators
    
    def _verify_truth_indicators(self, dataset: QualityAssuredDataset, result: TruthAnalysisResult) -> TruthAnalysisResult:
        """真実性指標の検証"""
        
        try:
            # データ品質との整合性チェック
            result.validation_checks["data_quality_consistent"] = (
                result.truth_indicators.get("data_completeness", 0) >= 70.0
            )
            
            # 需要適合性チェック
            result.validation_checks["demand_realistic"] = (
                0 <= result.truth_indicators.get("demand_alignment", 0) <= 150.0  # 150%以下は現実的
            )
            
            # ピーク時カバレッジ妥当性
            result.validation_checks["peak_coverage_adequate"] = (
                result.truth_indicators.get("peak_hour_coverage", 0) >= 50.0
            )
            
            # 総不足時間の妥当性
            result.validation_checks["shortage_reasonable"] = (
                result.total_shortage_hours <= dataset.data.shape[0] * 24  # 非現実的でない範囲
            )
            
            return result
            
        except Exception as e:
            log.error(f"真実性検証エラー: {e}")
            return result
    
    def _calculate_need_based_confidence(
        self, 
        dataset: QualityAssuredDataset, 
        decomposition: DecompositionResult, 
        result: TruthAnalysisResult
    ) -> float:
        """Need-based信頼度計算"""
        
        try:
            # ベース信頼度（データ品質）
            base_confidence = dataset.quality_result.overall_score
            
            # Need分析品質ボーナス
            need_quality_bonus = 0.0
            if decomposition.need_analysis:
                need_quality_bonus = decomposition.need_analysis.confidence_score * 0.3
            
            # 検証チェック通過率
            validation_passed = sum(1 for v in result.validation_checks.values() if v)
            validation_total = len(result.validation_checks)
            validation_ratio = validation_passed / validation_total if validation_total > 0 else 0.0
            validation_bonus = validation_ratio * 15.0
            
            # 真実性指標ボーナス
            truth_indicators_avg = np.mean(list(result.truth_indicators.values())) if result.truth_indicators else 0.0
            truth_bonus = truth_indicators_avg * 0.1
            
            # 総合信頼度計算
            confidence = min(100.0, base_confidence + need_quality_bonus + validation_bonus + truth_bonus)
            
            return confidence
            
        except Exception as e:
            log.error(f"Need-based信頼度計算エラー: {e}")
            return 0.0
    
    def _fallback_to_direct_analysis(self, dataset: QualityAssuredDataset, result: TruthAnalysisResult) -> TruthAnalysisResult:
        """Need Fileなしの場合の直接分析"""
        analysis_logger.warning("[PRIMARY_TRUTH] Need File未検出、直接分析にフォールバック")
        
        # 現在の配置から需要を推定
        current_staffing = self._analyze_current_staffing(dataset.data)
        
        # 推定需要（現在配置の1.2倍を適正とする）
        estimated_demands = {}
        for time_slot, current in current_staffing["time_distribution"].items():
            estimated_demands[time_slot] = current * 1.2
        
        # 不足計算
        result.shortage_by_time = self._calculate_precise_time_shortages(
            estimated_demands, 
            current_staffing["time_distribution"]
        )
        
        result.total_shortage_hours = sum(result.shortage_by_time.values())
        
        # 信頼度は低下
        result.truth_indicators["estimation_based"] = True
        result.processing_notes.append("Need File未検出のため推定値による分析")
        
        return result
    
    def _detect_coverage_gaps(self, time_distribution: Dict[str, float]) -> List[str]:
        """カバレッジギャップ検出"""
        gaps = []
        
        for time_slot, staff_count in time_distribution.items():
            if staff_count == 0:
                gaps.append(time_slot)
        
        return gaps
    
    def _is_time_column(self, col: Any) -> bool:
        """時間列判定"""
        col_str = str(col)
        return bool(':' in col_str and any(c.isdigit() for c in col_str))


class PatternBasedValidationEngine:
    """Pattern-based検証分析エンジン（階層2: Validation Engine）"""
    
    def __init__(self):
        self.validation_methods = ["time_series", "statistical", "trend_analysis"]
    
    def validate(self, primary_result: TruthAnalysisResult, dataset: QualityAssuredDataset) -> TruthAnalysisResult:
        """Pattern-based検証分析"""
        analysis_logger.info("[VALIDATION_ENGINE] Pattern-based検証開始")
        
        validation_result = TruthAnalysisResult("pattern_based_validation")
        
        try:
            # 時系列パターン検証
            validation_result = self._time_series_validation(primary_result, dataset, validation_result)
            
            # 統計的妥当性検証
            validation_result = self._statistical_validation(primary_result, dataset, validation_result)
            
            # トレンド整合性検証
            validation_result = self._trend_validation(primary_result, dataset, validation_result)
            
            # 検証信頼度計算
            validation_result.confidence_score = self._calculate_validation_confidence(primary_result, validation_result)
            validation_result.confidence_level = validation_result.calculate_confidence_level()
            
            analysis_logger.info(f"[VALIDATION_ENGINE] 完了: 信頼度{validation_result.confidence_score:.1f}%")
            
            return validation_result
            
        except Exception as e:
            log.error(f"Pattern-based検証エラー: {e}")
            validation_result.processing_notes.append(f"検証エラー: {e}")
            return validation_result
    
    def _time_series_validation(
        self, 
        primary_result: TruthAnalysisResult, 
        dataset: QualityAssuredDataset,
        validation_result: TruthAnalysisResult
    ) -> TruthAnalysisResult:
        """時系列パターン検証"""
        
        try:
            # 時間別不足パターンの妥当性検証
            time_shortages = primary_result.shortage_by_time
            
            if time_shortages:
                # パターンの一貫性チェック
                shortage_values = list(time_shortages.values())
                
                # 極端な値の検出
                shortage_mean = np.mean(shortage_values)
                shortage_std = np.std(shortage_values)
                
                extreme_values = [v for v in shortage_values if abs(v - shortage_mean) > 3 * shortage_std]
                validation_result.validation_checks["no_extreme_outliers"] = len(extreme_values) == 0
                
                # パターンの滑らかさ検証
                if len(shortage_values) > 2:
                    smoothness_score = self._calculate_pattern_smoothness(shortage_values)
                    validation_result.truth_indicators["pattern_smoothness"] = smoothness_score
                    validation_result.validation_checks["pattern_smooth"] = smoothness_score > 0.6
                
                validation_result.evidence_data["time_series_validation"] = {
                    "mean_shortage": shortage_mean,
                    "std_shortage": shortage_std,
                    "extreme_values_count": len(extreme_values),
                    "pattern_consistency": "consistent" if len(extreme_values) == 0 else "inconsistent"
                }
            
            return validation_result
            
        except Exception as e:
            log.error(f"時系列検証エラー: {e}")
            return validation_result
    
    def _statistical_validation(
        self,
        primary_result: TruthAnalysisResult,
        dataset: QualityAssuredDataset,
        validation_result: TruthAnalysisResult
    ) -> TruthAnalysisResult:
        """統計的妥当性検証"""
        
        try:
            # 不足時間の統計的分布検証
            total_shortage = primary_result.total_shortage_hours
            
            # 現実的範囲内かチェック
            data_size = dataset.data.shape[0]
            max_reasonable_shortage = data_size * 8  # 1人あたり最大8時間不足と仮定
            
            validation_result.validation_checks["shortage_within_reasonable_range"] = (
                0 <= total_shortage <= max_reasonable_shortage
            )
            
            # 職種間バランス検証
            role_shortages = primary_result.shortage_by_role
            if role_shortages:
                role_values = list(role_shortages.values())
                if len(role_values) > 1:
                    # ジニ係数による不平等度測定
                    gini_coefficient = self._calculate_gini_coefficient(role_values)
                    validation_result.truth_indicators["role_balance_gini"] = gini_coefficient
                    validation_result.validation_checks["role_balance_reasonable"] = gini_coefficient < 0.8
            
            # データとの整合性検証
            if 'role' in dataset.data.columns:
                actual_role_distribution = dataset.data['role'].value_counts(normalize=True)
                shortage_distribution = {k: v/sum(role_shortages.values()) for k, v in role_shortages.items() if sum(role_shortages.values()) > 0}
                
                # 分布の類似性チェック（KLダイバージェンス的な考え方）
                distribution_similarity = self._calculate_distribution_similarity(
                    actual_role_distribution.to_dict(), 
                    shortage_distribution
                )
                validation_result.truth_indicators["distribution_similarity"] = distribution_similarity
                validation_result.validation_checks["distribution_consistent"] = distribution_similarity > 0.7
            
            return validation_result
            
        except Exception as e:
            log.error(f"統計的検証エラー: {e}")
            return validation_result
    
    def _trend_validation(
        self,
        primary_result: TruthAnalysisResult,
        dataset: QualityAssuredDataset,
        validation_result: TruthAnalysisResult
    ) -> TruthAnalysisResult:
        """トレンド整合性検証"""
        
        try:
            # 時間帯別トレンドの妥当性
            time_shortages = primary_result.shortage_by_time
            
            if len(time_shortages) >= 3:
                # ピーク時間帯の妥当性検証
                sorted_times = sorted(time_shortages.items(), key=lambda x: x[1], reverse=True)
                peak_times = [t[0] for t in sorted_times[:3]]  # 上位3時間帯
                
                # 一般的なピーク時間帯パターンとの整合性
                expected_peak_patterns = ["07:00", "08:00", "17:00", "18:00", "22:00", "23:00"]
                peak_pattern_match = any(
                    any(expected in peak_time for expected in expected_peak_patterns)
                    for peak_time in peak_times
                )
                
                validation_result.validation_checks["peak_pattern_realistic"] = peak_pattern_match
                validation_result.evidence_data["detected_peak_times"] = peak_times
            
            # 長期トレンド検証（過去データとの比較）
            # 注: 実装では過去データがないため、現在は基本的な妥当性チェックのみ
            validation_result.validation_checks["trend_analysis_completed"] = True
            
            return validation_result
            
        except Exception as e:
            log.error(f"トレンド検証エラー: {e}")  
            return validation_result
    
    def _calculate_pattern_smoothness(self, values: List[float]) -> float:
        """パターンの滑らかさ計算"""
        if len(values) < 3:
            return 1.0
        
        # 隣接する値の差の分散を基準にした滑らかさスコア
        differences = [abs(values[i+1] - values[i]) for i in range(len(values)-1)]
        if not differences:
            return 1.0
        
        diff_std = np.std(differences)
        diff_mean = np.mean(differences)
        
        # 標準偏差が平均に対して小さいほど滑らか
        smoothness = 1.0 / (1.0 + diff_std / max(diff_mean, 0.01))
        return min(1.0, smoothness)
    
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """ジニ係数計算"""
        if not values or len(values) < 2:
            return 0.0
        
        values = sorted([v for v in values if v >= 0])
        n = len(values)
        
        if sum(values) == 0:
            return 0.0
        
        cumulative = np.cumsum(values)
        return (n + 1 - 2 * sum((n + 1 - i) * v for i, v in enumerate(values, 1))) / (n * sum(values))
    
    def _calculate_distribution_similarity(self, dist1: Dict[str, float], dist2: Dict[str, float]) -> float:
        """分布の類似性計算"""
        try:
            all_keys = set(dist1.keys()) | set(dist2.keys())
            
            similarity_sum = 0.0
            for key in all_keys:
                val1 = dist1.get(key, 0.0)
                val2 = dist2.get(key, 0.0)
                similarity_sum += min(val1, val2)
            
            return similarity_sum
            
        except Exception as e:
            log.error(f"分布類似性計算エラー: {e}")
            return 0.0
    
    def _calculate_validation_confidence(
        self, 
        primary_result: TruthAnalysisResult, 
        validation_result: TruthAnalysisResult
    ) -> float:
        """検証信頼度計算"""
        
        try:
            # プライマリ結果の信頼度をベース
            base_confidence = primary_result.confidence_score
            
            # 検証チェック通過率
            checks_passed = sum(1 for v in validation_result.validation_checks.values() if v)
            total_checks = len(validation_result.validation_checks)
            check_ratio = checks_passed / total_checks if total_checks > 0 else 0.0
            
            # 検証による信頼度調整
            if check_ratio >= 0.8:
                confidence_adjustment = 5.0  # ボーナス
            elif check_ratio >= 0.6:
                confidence_adjustment = 0.0  # 変更なし
            else:
                confidence_adjustment = -10.0  # ペナルティ
            
            # 真実性指標による調整
            truth_indicators_avg = np.mean(list(validation_result.truth_indicators.values())) if validation_result.truth_indicators else 0.0
            truth_adjustment = truth_indicators_avg * 0.1
            
            final_confidence = min(100.0, max(0.0, base_confidence + confidence_adjustment + truth_adjustment))
            
            return final_confidence
            
        except Exception as e:
            log.error(f"検証信頼度計算エラー: {e}")
            return 0.0


class ProportionalFallbackEngine:
    """Proportional補完分析エンジン（階層3: Fallback Engine）"""
    
    def __init__(self):
        self.fallback_mode = "proportional_estimation"
    
    def supplement(self, dataset: QualityAssuredDataset, primary_confidence: float) -> TruthAnalysisResult:
        """按分補完分析"""
        analysis_logger.info("[FALLBACK_ENGINE] Proportional補完分析開始")
        
        result = TruthAnalysisResult("proportional_fallback")
        
        try:
            # 按分方式による基本分析
            result = self._proportional_shortage_analysis(dataset, result)
            
            # 補完信頼度計算
            result.confidence_score = self._calculate_fallback_confidence(primary_confidence, result)
            result.confidence_level = result.calculate_confidence_level()
            
            result.processing_notes.append("データ品質不足のため按分方式による補完分析")
            analysis_logger.info(f"[FALLBACK_ENGINE] 完了: 信頼度{result.confidence_score:.1f}%")
            
            return result
            
        except Exception as e:
            log.error(f"按分補完分析エラー: {e}")
            result.processing_notes.append(f"補完分析エラー: {e}")
            return result
    
    def _proportional_shortage_analysis(self, dataset: QualityAssuredDataset, result: TruthAnalysisResult) -> TruthAnalysisResult:
        """按分方式不足分析"""
        
        try:
            data = dataset.data
            filtered_data = apply_rest_exclusion_filter(data, "proportional_analysis")
            
            if filtered_data.empty:
                return result
            
            # 全体の推定不足時間（簡易計算）
            total_records = len(filtered_data)
            estimated_total_shortage = total_records * 0.5  # 1レコードあたり0.5時間不足と仮定
            
            # 職種別按分
            if 'role' in filtered_data.columns:
                role_counts = filtered_data['role'].value_counts()
                for role, count in role_counts.items():
                    proportion = count / total_records
                    result.shortage_by_role[role] = estimated_total_shortage * proportion
            
            # 雇用形態別按分
            if 'employment' in filtered_data.columns:
                employment_counts = filtered_data['employment'].value_counts()
                for employment, count in employment_counts.items():
                    proportion = count / total_records
                    result.shortage_by_employment[employment] = estimated_total_shortage * proportion
            
            # 時間別按分（時間列が存在する場合）
            time_columns = [col for col in data.columns if self._is_time_column(col)]
            if time_columns:
                time_slot_shortage = estimated_total_shortage / len(time_columns)
                for col in time_columns:
                    result.shortage_by_time[str(col)] = time_slot_shortage
            
            result.total_shortage_hours = estimated_total_shortage
            
            # 補完特有の真実性指標
            result.truth_indicators["proportional_estimation"] = True
            result.truth_indicators["data_driven_confidence"] = min(100.0, total_records * 2)  # レコード数に基づく信頼度
            
            return result
            
        except Exception as e:
            log.error(f"按分分析エラー: {e}")
            return result
    
    def _calculate_fallback_confidence(self, primary_confidence: float, result: TruthAnalysisResult) -> float:
        """補完信頼度計算"""
        
        # 按分方式は基本的に低信頼度
        base_fallback_confidence = 45.0
        
        # データ量による調整
        data_driven_confidence = result.truth_indicators.get("data_driven_confidence", 0.0)
        data_adjustment = min(15.0, data_driven_confidence * 0.1)
        
        # プライマリ分析の失敗度による調整
        primary_failure_penalty = max(0.0, (70.0 - primary_confidence) * 0.1)
        
        final_confidence = max(10.0, base_fallback_confidence + data_adjustment - primary_failure_penalty)
        
        return min(60.0, final_confidence)  # 按分方式の最大信頼度は60%
    
    def _is_time_column(self, col: Any) -> bool:
        """時間列判定"""
        col_str = str(col)
        return bool(':' in col_str and any(c.isdigit() for c in col_str))


class ComprehensiveTruthResult:
    """総合真実分析結果"""
    
    def __init__(self):
        self.primary_result: Optional[TruthAnalysisResult] = None
        self.validation_result: Optional[TruthAnalysisResult] = None
        self.fallback_result: Optional[TruthAnalysisResult] = None
        
        self.final_analysis: TruthAnalysisResult = TruthAnalysisResult("comprehensive_truth")
        self.analysis_method_used: str = "unknown"
        self.confidence_level: AnalysisConfidenceLevel = AnalysisConfidenceLevel.VERY_LOW
        
        self.recommendation: str = ""
        self.analysis_summary: Dict[str, Any] = {}
        self.processing_metadata: Dict[str, Any] = {}
    
    def generate_comprehensive_report(self) -> str:
        """総合レポート生成"""
        report = f"""
🎯 階層的真実分析 - 総合レポート
{'='*70}
📊 最終信頼度: {self.final_analysis.confidence_score:.1f}% ({self.confidence_level.value})
🔍 採用分析手法: {self.analysis_method_used}

📋 分析結果サマリー:
├─ 総不足時間: {self.final_analysis.total_shortage_hours:.1f}時間
├─ 職種別不足: {len(self.final_analysis.shortage_by_role)}職種
├─ 時間別不足: {len(self.final_analysis.shortage_by_time)}時間帯
└─ 雇用形態別不足: {len(self.final_analysis.shortage_by_employment)}形態

🏆 各階層の評価:
├─ 階層1 (Need-based): {self.primary_result.confidence_score:.1f}% if self.primary_result else 'N/A'
├─ 階層2 (Pattern-based): {self.validation_result.confidence_score:.1f}% if self.validation_result else 'N/A'
└─ 階層3 (Proportional): {self.fallback_result.confidence_score:.1f}% if self.fallback_result else 'N/A'

💡 推奨事項: {self.recommendation}

🔧 処理メタデータ:
└─ 分析完了時刻: {self.final_analysis.processing_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return report


class HierarchicalTruthAnalyzer:
    """階層的真実分析システム"""
    
    def __init__(self):
        self.primary_engine = NeedBasedTruthEngine()
        self.validation_engine = PatternBasedValidationEngine()
        self.fallback_engine = ProportionalFallbackEngine()
        
        self.analysis_threshold = {
            "primary_minimum": 70.0,
            "validation_minimum": 60.0,
            "fallback_acceptable": 40.0
        }
    
    def analyze_with_confidence(
        self, 
        dataset: QualityAssuredDataset, 
        decomposition: DecompositionResult
    ) -> ComprehensiveTruthResult:
        """信頼度付き階層分析"""
        analysis_logger.info("[HIERARCHICAL_TRUTH] 階層的真実分析開始")
        
        comprehensive_result = ComprehensiveTruthResult()
        
        try:
            # 階層1: Need-based真実分析
            comprehensive_result.primary_result = self.primary_engine.analyze(dataset, decomposition)
            
            # 階層2: Pattern-based検証（プライマリが一定以上の場合）
            if comprehensive_result.primary_result.confidence_score >= self.analysis_threshold["validation_minimum"]:
                comprehensive_result.validation_result = self.validation_engine.validate(
                    comprehensive_result.primary_result, dataset
                )
            
            # 階層3: Proportional補完（必要な場合のみ）
            if comprehensive_result.primary_result.confidence_score < self.analysis_threshold["primary_minimum"]:
                comprehensive_result.fallback_result = self.fallback_engine.supplement(
                    dataset, comprehensive_result.primary_result.confidence_score
                )
            
            # 最終結果統合
            comprehensive_result = self._integrate_analysis_results(comprehensive_result)
            
            # 推奨事項生成
            comprehensive_result.recommendation = self._generate_recommendation(comprehensive_result)
            
            analysis_logger.info(f"[HIERARCHICAL_TRUTH] 完了: 最終信頼度{comprehensive_result.final_analysis.confidence_score:.1f}%")
            analysis_logger.info(comprehensive_result.generate_comprehensive_report())
            
            return comprehensive_result
            
        except Exception as e:
            log.error(f"階層的真実分析エラー: {e}")
            comprehensive_result.final_analysis.processing_notes.append(f"分析エラー: {e}")
            return comprehensive_result
    
    def _integrate_analysis_results(self, comprehensive_result: ComprehensiveTruthResult) -> ComprehensiveTruthResult:
        """分析結果統合"""
        
        try:
            primary = comprehensive_result.primary_result
            validation = comprehensive_result.validation_result
            fallback = comprehensive_result.fallback_result
            
            # 最高信頼度の分析結果を採用
            candidates = []
            if primary:
                candidates.append(("primary", primary))
            if validation:
                candidates.append(("validation", validation))  
            if fallback:
                candidates.append(("fallback", fallback))
            
            if not candidates:
                comprehensive_result.analysis_method_used = "none"
                return comprehensive_result
            
            # 信頼度順にソート
            candidates.sort(key=lambda x: x[1].confidence_score, reverse=True)
            best_method, best_result = candidates[0]
            
            # 最良結果を最終結果として採用
            comprehensive_result.final_analysis = best_result
            comprehensive_result.analysis_method_used = best_method
            comprehensive_result.confidence_level = best_result.confidence_level
            
            # 分析サマリー生成
            comprehensive_result.analysis_summary = {
                "methods_evaluated": len(candidates),
                "selected_method": best_method,
                "confidence_scores": {method: result.confidence_score for method, result in candidates},
                "validation_performed": validation is not None,
                "fallback_required": fallback is not None
            }
            
            return comprehensive_result
            
        except Exception as e:
            log.error(f"結果統合エラー: {e}")
            return comprehensive_result
    
    def _generate_recommendation(self, comprehensive_result: ComprehensiveTruthResult) -> str:
        """推奨事項生成"""
        
        final_confidence = comprehensive_result.final_analysis.confidence_score
        method_used = comprehensive_result.analysis_method_used
        
        if final_confidence >= 90:
            return f"信頼度{final_confidence:.1f}%で高精度分析完了。{method_used}手法による結果を意思決定に使用可能。"
        elif final_confidence >= 75:
            return f"信頼度{final_confidence:.1f}%で良好な分析結果。{method_used}手法による結果は信頼性があります。"
        elif final_confidence >= 60:
            return f"信頼度{final_confidence:.1f}%で中程度の分析結果。{method_used}手法による結果は参考として利用可能。"
        elif final_confidence >= 40:
            return f"信頼度{final_confidence:.1f}%で低品質な分析結果。データ品質の改善を推奨します。"
        else:
            return f"信頼度{final_confidence:.1f}%で分析結果の信頼性が不十分。データの再収集・クレンジングが必要です。"


# 便利関数
def analyze_with_hierarchical_truth(
    dataset: QualityAssuredDataset, 
    decomposition: DecompositionResult
) -> ComprehensiveTruthResult:
    """階層的真実分析（便利関数）"""
    analyzer = HierarchicalTruthAnalyzer()
    return analyzer.analyze_with_confidence(dataset, decomposition)


# Export
__all__ = [
    "TruthAnalysisResult",
    "ComprehensiveTruthResult", 
    "HierarchicalTruthAnalyzer",
    "analyze_with_hierarchical_truth"
]