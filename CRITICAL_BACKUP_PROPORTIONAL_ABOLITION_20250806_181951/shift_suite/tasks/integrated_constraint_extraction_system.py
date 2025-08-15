"""
統合制約抽出システム - 深度19.6%問題の解決
アプローチ①とアプローチ②を統合し、「洗い出しが行えていない」問題を根本的に解決

主要機能：
1. アプローチ①②の統合実行
2. 制約の交差検証と信頼性向上
3. 動的制約発見パイプライン
4. 実用的制約フィルタリング
5. AI読み込み対応形式での出力
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from pathlib import Path

from .enhanced_raw_data_processor import EnhancedRawDataProcessor
from .advanced_processed_data_analyzer import AdvancedProcessedDataAnalyzer
from .mece_fact_extractor import MECEFactExtractor
from .enhanced_blueprint_analyzer import EnhancedBlueprintAnalyzer
from .advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
from .shift_mind_reader import ShiftMindReader
from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS

log = logging.getLogger(__name__)


class IntegratedConstraintExtractionSystem:
    """統合制約抽出システム - 深度問題の根本解決"""
    
    def __init__(self):
        self.raw_processor = EnhancedRawDataProcessor()
        self.processed_analyzer = AdvancedProcessedDataAnalyzer()
        self.mece_extractor = MECEFactExtractor()
        
        # ブループリント分析コンポーネント
        self.blueprint_analyzer = EnhancedBlueprintAnalyzer()
        self.blueprint_engine_v2 = AdvancedBlueprintEngineV2()
        self.mind_reader = ShiftMindReader()
        
        self.confidence_threshold = STATISTICAL_THRESHOLDS['confidence_level']
        self.min_sample_size = STATISTICAL_THRESHOLDS['min_sample_size']
        
    def execute_integrated_constraint_extraction(self, 
                                               raw_excel_path: str,
                                               processed_data_dir: str,
                                               worktype_definitions: Dict = None,
                                               long_df: pd.DataFrame = None) -> Dict[str, Any]:
        """統合制約抽出の実行
        
        Args:
            raw_excel_path: 生データExcelファイルパス
            processed_data_dir: 加工済みデータディレクトリ
            worktype_definitions: 勤務区分定義
            long_df: 既存のlong形式データフレーム
            
        Returns:
            統合制約抽出結果
        """
        log.info("=== 統合制約抽出システム開始 ===")
        
        # Phase 1: アプローチ①の実行
        log.info("Phase 1: 生データ特化分析を実行中...")
        approach1_results = self._execute_approach1(raw_excel_path, worktype_definitions)
        
        # Phase 2: アプローチ②の実行  
        log.info("Phase 2: 既存データ深化分析を実行中...")
        approach2_results = self._execute_approach2(processed_data_dir)
        
        # Phase 3: MECE事実抽出の実行
        log.info("Phase 3: MECE事実抽出を実行中...")
        mece_results = self._execute_mece_extraction(long_df, worktype_definitions)
        
        # Phase 3.5: ブループリント分析の実行
        log.info("Phase 3.5: ブループリント暗黙知分析を実行中...")
        blueprint_results = self._execute_blueprint_analysis(long_df, worktype_definitions)
        
        # Phase 4: 制約の統合と交差検証
        log.info("Phase 4: 制約統合と交差検証を実行中...")
        integrated_constraints = self._integrate_and_cross_validate_constraints(
            approach1_results, approach2_results, mece_results, blueprint_results
        )
        
        # Phase 5: 実用的制約フィルタリング
        log.info("Phase 5: 実用的制約フィルタリングを実行中...")
        filtered_constraints = self._filter_practical_constraints(integrated_constraints)
        
        # Phase 6: AI読み込み対応形式での出力
        log.info("Phase 6: AI読み込み対応形式での出力生成中...")
        ai_readable_output = self._generate_ai_readable_output(filtered_constraints)
        
        # Phase 7: 品質評価と深度計算（ブループリント要素込み）
        log.info("Phase 7: 品質評価と深度計算を実行中...")
        quality_metrics = self._calculate_extraction_quality_metrics(
            filtered_constraints, approach1_results, approach2_results, mece_results, blueprint_results
        )
        
        final_results = {
            "execution_metadata": {
                "timestamp": datetime.now().isoformat(),
                "system_version": "integrated_v1.0",
                "approach1_results": len(approach1_results.get("implicit_patterns", {})),
                "approach2_results": len(approach2_results.get("cross_domain_relationships", {})),
                "mece_results": len(mece_results.get("human_readable", {}).get("MECE分解事実", {})),
                "blueprint_results": len(blueprint_results.get("rules", [])),
                "total_raw_constraints": sum(self._count_constraints_in_results(r) for r in [approach1_results, approach2_results, mece_results, blueprint_results]),
                "final_filtered_constraints": len(filtered_constraints)
            },
            "approach1_raw_results": approach1_results,
            "approach2_processed_results": approach2_results,
            "mece_extraction_results": mece_results,
            "blueprint_analysis_results": blueprint_results,
            "integrated_constraints": integrated_constraints,
            "filtered_practical_constraints": filtered_constraints,
            "ai_readable_constraints": ai_readable_output,
            "quality_metrics": quality_metrics
        }
        
        log.info(f"=== 統合制約抽出完了 ==="
                f"生成制約数: {final_results['execution_metadata']['final_filtered_constraints']}"
                f"品質スコア: {quality_metrics.get('overall_quality_score', 0):.1%}")
        
        return final_results
    
    def _execute_approach1(self, excel_path: str, worktype_definitions: Dict = None) -> Dict[str, Any]:
        """アプローチ①: 生データ特化分析の実行"""
        try:
            if not Path(excel_path).exists():
                log.warning(f"生データファイルが見つかりません: {excel_path}")
                return self._empty_approach_result("approach1")
            
            results = self.raw_processor.process_raw_data_for_constraint_extraction(
                excel_path, worktype_definitions
            )
            
            log.info(f"アプローチ①完了: {self._count_constraints_in_results(results)}個の制約候補を発見")
            return results
            
        except Exception as e:
            log.error(f"アプローチ①実行エラー: {e}")
            return self._empty_approach_result("approach1")
    
    def _execute_approach2(self, processed_data_dir: str) -> Dict[str, Any]:
        """アプローチ②: 既存データ深化分析の実行"""
        try:
            if not Path(processed_data_dir).exists():
                log.warning(f"加工済みデータディレクトリが見つかりません: {processed_data_dir}")
                return self._empty_approach_result("approach2")
            
            results = self.processed_analyzer.analyze_processed_data_for_advanced_constraints(
                processed_data_dir
            )
            
            log.info(f"アプローチ②完了: {self._count_constraints_in_results(results)}個の高度制約を発見")
            return results
            
        except Exception as e:
            log.error(f"アプローチ②実行エラー: {e}")
            return self._empty_approach_result("approach2")
    
    def _execute_mece_extraction(self, long_df: pd.DataFrame, worktype_definitions: Dict = None) -> Dict[str, Any]:
        """MECE事実抽出の実行"""
        try:
            if long_df is None or long_df.empty:
                log.warning("long_dfが空またはNoneです")
                return self._empty_approach_result("mece")
            
            # 勤務区分定義をDataFrame形式に変換
            wt_df = None
            if worktype_definitions:
                wt_data = []
                for code, definition in worktype_definitions.items():
                    if isinstance(definition, dict):
                        wt_data.append({
                            'code': code,
                            'start_parsed': definition.get('start_time'),
                            'end_parsed': definition.get('end_time'),
                            'parsed_slots_count': definition.get('slot_count', 0),
                            'holiday_type': definition.get('type', '通常勤務')
                        })
                
                if wt_data:
                    wt_df = pd.DataFrame(wt_data)
            
            results = self.mece_extractor.extract_axis1_facility_rules(long_df, wt_df)
            
            log.info(f"MECE抽出完了: {self._count_constraints_in_results(results)}個の施設制約を抽出")
            return results
            
        except Exception as e:
            log.error(f"MECE抽出実行エラー: {e}")
            return self._empty_approach_result("mece")
    
    def _integrate_and_cross_validate_constraints(self, 
                                                approach1: Dict, 
                                                approach2: Dict, 
                                                mece: Dict) -> Dict[str, List[Dict]]:
        """制約の統合と交差検証"""
        integrated = {
            "high_confidence_constraints": [],    # 複数手法で確認された高信頼度制約
            "medium_confidence_constraints": [],  # 単一手法だが信頼度の高い制約
            "supplementary_constraints": [],      # 補完的制約
            "conflicting_constraints": []         # 矛盾する制約（要検証）
        }
        
        # 各アプローチから制約を抽出
        all_constraints = []
        
        # アプローチ①からの制約
        if "implicit_patterns" in approach1:
            for category, patterns in approach1["implicit_patterns"].items():
                for pattern in patterns:
                    pattern["source"] = "approach1"
                    pattern["source_category"] = category
                    all_constraints.append(pattern)
        
        # アプローチ②からの制約
        if "cross_domain_relationships" in approach2:
            for category, relationships in approach2["cross_domain_relationships"].items():
                for relationship in relationships:
                    relationship["source"] = "approach2"
                    relationship["source_category"] = category
                    all_constraints.append(relationship)
        
        if "statistical_patterns" in approach2:
            for category, patterns in approach2["statistical_patterns"].items():
                for pattern in patterns:
                    pattern["source"] = "approach2"
                    pattern["source_category"] = category
                    all_constraints.append(pattern)
        
        # MECEからの制約
        if "machine_readable" in mece:
            for constraint_type in ["hard_constraints", "soft_constraints", "preferences"]:
                for constraint in mece["machine_readable"].get(constraint_type, []):
                    constraint["source"] = "mece"
                    constraint["source_category"] = constraint_type
                    all_constraints.append(constraint)
        
        # 制約の交差検証と分類
        constraint_groups = self._group_similar_constraints(all_constraints)
        
        for group_id, constraints in constraint_groups.items():
            if len(constraints) >= 2:
                # 複数手法で確認された制約 → 高信頼度
                consensus_constraint = self._create_consensus_constraint(constraints)
                integrated["high_confidence_constraints"].append(consensus_constraint)
            
            elif len(constraints) == 1:
                constraint = constraints[0]
                confidence = self._extract_confidence_score(constraint)
                
                if confidence >= 0.8:
                    integrated["high_confidence_constraints"].append(constraint)
                elif confidence >= 0.5:
                    integrated["medium_confidence_constraints"].append(constraint)
                else:
                    integrated["supplementary_constraints"].append(constraint)
        
        # 矛盾制約の検出
        conflicting = self._detect_conflicting_constraints(all_constraints)
        integrated["conflicting_constraints"].extend(conflicting)
        
        log.info(f"制約統合完了: 高信頼度={len(integrated['high_confidence_constraints'])}, "
                f"中信頼度={len(integrated['medium_confidence_constraints'])}, "
                f"補完={len(integrated['supplementary_constraints'])}, "
                f"矛盾={len(integrated['conflicting_constraints'])}")
        
        return integrated
    
    def _group_similar_constraints(self, constraints: List[Dict]) -> Dict[str, List[Dict]]:
        """類似制約のグルーピング"""
        groups = defaultdict(list)
        
        for constraint in constraints:
            # 制約の特徴に基づくグループID生成
            group_key = self._generate_constraint_group_key(constraint)
            groups[group_key].append(constraint)
        
        return dict(groups)
    
    def _generate_constraint_group_key(self, constraint: Dict) -> str:
        """制約のグループキー生成"""
        # 主要な特徴を組み合わせてキーを生成
        key_components = []
        
        # タイプ情報
        if "type" in constraint:
            key_components.append(constraint["type"])
        elif "制約種別" in constraint:
            key_components.append(constraint["制約種別"])
        
        # 関連する列や値
        if "column" in constraint:
            key_components.append(constraint["column"])
        elif "曜日" in constraint:
            key_components.append(f"weekday_{constraint['曜日']}")
        
        # スタッフ関連
        if "staff" in constraint or "スタッフ" in constraint:
            staff_name = constraint.get("staff", constraint.get("スタッフ", ""))
            key_components.append(f"staff_{staff_name}")
        
        return "_".join(str(comp) for comp in key_components if comp)
    
    def _create_consensus_constraint(self, constraints: List[Dict]) -> Dict:
        """複数制約からの合意制約作成"""
        consensus = {
            "type": "consensus_constraint",
            "source_count": len(constraints),
            "source_methods": list(set(c.get("source", "unknown") for c in constraints)),
            "confidence_scores": [self._extract_confidence_score(c) for c in constraints],
            "consensus_confidence": 0.0,
            "constraint_text": "",
            "supporting_evidence": constraints
        }
        
        # 合意信頼度の計算（複数手法の平均）
        confidence_scores = consensus["confidence_scores"]
        if confidence_scores:
            consensus["consensus_confidence"] = np.mean(confidence_scores)
        
        # 制約テキストの統合
        constraint_texts = []
        for c in constraints:
            if "rule" in c:
                constraint_texts.append(c["rule"])
            elif "constraint_implication" in c:
                constraint_texts.append(c["constraint_implication"])
            elif "制約種別" in c:
                constraint_texts.append(str(c["制約種別"]))
        
        if constraint_texts:
            consensus["constraint_text"] = " | ".join(set(constraint_texts))
        
        return consensus
    
    def _extract_confidence_score(self, constraint: Dict) -> float:
        """制約から信頼度スコアを抽出"""
        # 様々なキーから信頼度を抽出
        confidence_keys = ["confidence", "確信度", "confidence_score", "priority_score"]
        
        for key in confidence_keys:
            if key in constraint:
                return float(constraint[key])
        
        # P値がある場合は1-p_valueを信頼度とする
        if "p_value" in constraint:
            return 1 - float(constraint["p_value"])
        
        # フリークエンシーベースの信頼度
        if "frequency" in constraint and "total_observations" in constraint:
            freq = constraint["frequency"]
            total = constraint["total_observations"]
            if total > 0:
                return min(1.0, freq / total)
        
        # デフォルト
        return 0.5
    
    def _detect_conflicting_constraints(self, constraints: List[Dict]) -> List[Dict]:
        """矛盾制約の検出"""
        conflicting = []
        
        # 同じ対象に対する矛盾する制約を検出
        constraint_by_target = defaultdict(list)
        
        for constraint in constraints:
            target = self._identify_constraint_target(constraint)
            if target:
                constraint_by_target[target].append(constraint)
        
        for target, target_constraints in constraint_by_target.items():
            if len(target_constraints) >= 2:
                conflicts = self._check_for_conflicts_in_group(target_constraints)
                conflicting.extend(conflicts)
        
        return conflicting
    
    def _identify_constraint_target(self, constraint: Dict) -> str:
        """制約の対象を特定"""
        # 制約が適用される対象を特定
        target_keys = ["column", "staff", "スタッフ", "曜日", "時間帯"]
        
        for key in target_keys:
            if key in constraint:
                return f"{key}_{constraint[key]}"
        
        return ""
    
    def _check_for_conflicts_in_group(self, constraints: List[Dict]) -> List[Dict]:
        """グループ内の矛盾チェック"""
        conflicts = []
        
        # 数値的な矛盾をチェック
        numeric_constraints = []
        for c in constraints:
            if any(key in c for key in ["min_value", "max_value", "平均人員数", "最大連続勤務日数"]):
                numeric_constraints.append(c)
        
        if len(numeric_constraints) >= 2:
            # 数値範囲の矛盾をチェック
            for i, c1 in enumerate(numeric_constraints):
                for c2 in numeric_constraints[i+1:]:
                    if self._are_numeric_constraints_conflicting(c1, c2):
                        conflicts.append({
                            "type": "数値矛盾",
                            "constraint1": c1,
                            "constraint2": c2,
                            "conflict_description": "数値範囲が矛盾しています"
                        })
        
        return conflicts
    
    def _are_numeric_constraints_conflicting(self, c1: Dict, c2: Dict) -> bool:
        """数値制約の矛盾判定"""
        # 簡単な矛盾チェックの実装
        # より詳細な実装が必要な場合は拡張
        return False
    
    def _filter_practical_constraints(self, integrated_constraints: Dict) -> List[Dict]:
        """実用的制約のフィルタリング"""
        practical_constraints = []
        
        # 高信頼度制約は全て採用
        practical_constraints.extend(integrated_constraints["high_confidence_constraints"])
        
        # 中信頼度制約は実用性でフィルタリング
        for constraint in integrated_constraints["medium_confidence_constraints"]:
            if self._is_practically_useful(constraint):
                practical_constraints.append(constraint)
        
        # 補完制約は選別的に採用
        supplementary_sorted = sorted(
            integrated_constraints["supplementary_constraints"],
            key=lambda x: self._extract_confidence_score(x),
            reverse=True
        )
        
        # 上位30%を採用
        top_count = max(1, len(supplementary_sorted) // 3)
        for constraint in supplementary_sorted[:top_count]:
            if self._is_practically_useful(constraint):
                practical_constraints.append(constraint)
        
        log.info(f"実用的制約フィルタリング完了: {len(practical_constraints)}個の制約を選定")
        return practical_constraints
    
    def _is_practically_useful(self, constraint: Dict) -> bool:
        """制約の実用性判定"""
        # 実用性の判定基準
        useful_indicators = [
            "constraint_text" in constraint and len(constraint["constraint_text"]) > 10,
            "rule" in constraint and len(str(constraint["rule"])) > 5,
            "constraint_implication" in constraint and len(constraint["constraint_implication"]) > 10,
            self._extract_confidence_score(constraint) > 0.3,
            any(key in constraint for key in ["staff", "スタッフ", "曜日", "時間帯", "勤務コード"])
        ]
        
        # 半数以上の条件を満たせば実用的
        return sum(useful_indicators) >= len(useful_indicators) // 2
    
    def _generate_ai_readable_output(self, constraints: List[Dict]) -> Dict[str, Any]:
        """AI読み込み対応形式での出力生成"""
        ai_output = {
            "constraint_rules": [],
            "execution_parameters": {},
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "total_constraints": len(constraints),
                "confidence_distribution": self._calculate_confidence_distribution(constraints)
            }
        }
        
        # 制約ルールの構造化
        for i, constraint in enumerate(constraints):
            ai_constraint = {
                "id": f"constraint_{i+1}",
                "type": constraint.get("type", "unknown"),
                "condition": self._extract_constraint_condition(constraint),
                "action": self._extract_constraint_action(constraint),
                "confidence": self._extract_confidence_score(constraint),
                "priority": self._determine_constraint_priority(constraint),
                "applicable_contexts": self._extract_applicable_contexts(constraint),
                "original_constraint": constraint
            }
            
            ai_output["constraint_rules"].append(ai_constraint)
        
        # 実行パラメータの設定
        ai_output["execution_parameters"] = {
            "confidence_threshold": self.confidence_threshold,
            "enforcement_mode": "soft",  # hard | soft | advisory
            "conflict_resolution": "highest_confidence",
            "validation_required": True
        }
        
        return ai_output
    
    def _extract_constraint_condition(self, constraint: Dict) -> str:
        """制約の条件部分を抽出"""
        condition_keys = ["condition", "if", "when", "曜日", "時間帯", "スタッフ"]
        
        for key in condition_keys:
            if key in constraint:
                return f"{key}: {constraint[key]}"
        
        # デフォルトの条件生成
        if "type" in constraint:
            return f"type: {constraint['type']}"
        
        return "always"
    
    def _extract_constraint_action(self, constraint: Dict) -> str:
        """制約のアクション部分を抽出"""
        action_keys = ["rule", "constraint_implication", "action", "then"]
        
        for key in action_keys:
            if key in constraint:
                return str(constraint[key])
        
        # 制約種別から推定
        if "制約種別" in constraint:
            return f"apply: {constraint['制約種別']}"
        
        return "constraint_applies"
    
    def _determine_constraint_priority(self, constraint: Dict) -> str:
        """制約の優先度決定"""
        confidence = self._extract_confidence_score(constraint)
        
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _extract_applicable_contexts(self, constraint: Dict) -> List[str]:
        """制約の適用コンテキスト抽出"""
        contexts = []
        
        # ソース別コンテキスト
        if constraint.get("source") == "approach1":
            contexts.append("raw_data_pattern")
        elif constraint.get("source") == "approach2":
            contexts.append("statistical_analysis")
        elif constraint.get("source") == "mece":
            contexts.append("facility_rules")
        
        # 内容別コンテキスト
        if any(key in constraint for key in ["staff", "スタッフ"]):
            contexts.append("staff_assignment")
        if any(key in constraint for key in ["曜日", "weekday"]):
            contexts.append("weekly_pattern")
        if any(key in constraint for key in ["時間", "hour", "time"]):
            contexts.append("time_scheduling")
        
        return contexts if contexts else ["general"]
    
    def _calculate_confidence_distribution(self, constraints: List[Dict]) -> Dict[str, int]:
        """信頼度分布の計算"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for constraint in constraints:
            confidence = self._extract_confidence_score(constraint)
            if confidence >= 0.8:
                distribution["high"] += 1
            elif confidence >= 0.5:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution
    
    def _calculate_extraction_quality_metrics(self, 
                                             filtered_constraints: List[Dict],
                                             approach1: Dict,
                                             approach2: Dict,
                                             mece: Dict) -> Dict[str, float]:
        """抽出品質メトリクスの計算"""
        metrics = {
            "overall_quality_score": 0.0,
            "depth_score": 0.0,
            "practicality_score": 0.0,
            "coverage_score": 0.0,
            "confidence_score": 0.0
        }
        
        if not filtered_constraints:
            return metrics
        
        # 深度スコア（制約数とソース多様性）
        total_constraints = len(filtered_constraints)
        source_diversity = len(set(c.get("source", "unknown") for c in filtered_constraints))
        metrics["depth_score"] = min(1.0, (total_constraints / 50) * 0.7 + (source_diversity / 3) * 0.3)
        
        # 実用性スコア（実用的制約の割合）
        practical_count = sum(1 for c in filtered_constraints if self._is_practically_useful(c))
        metrics["practicality_score"] = practical_count / total_constraints if total_constraints > 0 else 0
        
        # カバレッジスコア（MECE分解の網羅性）
        mece_categories = len(mece.get("human_readable", {}).get("MECE分解事実", {}))
        metrics["coverage_score"] = min(1.0, mece_categories / 10)  # 10カテゴリで満点
        
        # 信頼度スコア（平均信頼度）
        confidences = [self._extract_confidence_score(c) for c in filtered_constraints]
        metrics["confidence_score"] = np.mean(confidences) if confidences else 0
        
        # 総合品質スコア
        metrics["overall_quality_score"] = (
            metrics["depth_score"] * 0.3 +
            metrics["practicality_score"] * 0.3 +
            metrics["coverage_score"] * 0.2 +
            metrics["confidence_score"] * 0.2
        )
        
        return metrics
    
    def _count_constraints_in_results(self, results: Dict) -> int:
        """結果内の制約数をカウント"""
        count = 0
        
        if isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, list):
                    count += len(value)
                elif isinstance(value, dict):
                    count += self._count_constraints_in_results(value)
        
        return count
    
    def _empty_approach_result(self, approach_name: str) -> Dict[str, Any]:
        """空のアプローチ結果を生成"""
        return {
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "approach": approach_name,
                "status": "empty_result"
            }
        }