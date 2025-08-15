"""
ブループリント分析統合システム - 統合制約抽出システムへの追加

主な機能：
1. ブループリント分析の実行
2. 深度スコアにブループリント要素を統合
3. 既存制約抽出システムとのマージ
"""

from __future__ import annotations

import logging
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

from .enhanced_blueprint_analyzer import EnhancedBlueprintAnalyzer
from .advanced_blueprint_engine_v2 import AdvancedBlueprintEngineV2
from .shift_mind_reader import ShiftMindReader

log = logging.getLogger(__name__)


class BlueprintIntegratedConstraintSystem:
    """ブループリント分析を統合した制約抽出システム"""
    
    def __init__(self):
        # ブループリント分析コンポーネント
        self.blueprint_analyzer = EnhancedBlueprintAnalyzer()
        self.blueprint_engine_v2 = AdvancedBlueprintEngineV2()
        self.mind_reader = ShiftMindReader()
    
    def execute_blueprint_analysis(self, long_df: pd.DataFrame, worktype_definitions: Dict = None) -> Dict[str, Any]:
        """ブループリント暗黙知分析の実行"""
        try:
            if long_df is None or long_df.empty:
                log.warning("long_dfが空またはNoneです（ブループリント分析）")
                return self._empty_blueprint_result()
            
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
            
            # 拡張ブループリント分析の実行
            blueprint_analysis_results = self.blueprint_analyzer.analyze_shift_creation_blueprint(long_df)
            
            # Blueprint Engine V2の実行
            try:
                blueprint_v2_results = self.blueprint_engine_v2.run_full_blueprint_analysis(long_df, wt_df)
                
                # 結果の統合
                results = {
                    "blueprint_analysis": blueprint_analysis_results,
                    "blueprint_v2_full": blueprint_v2_results,
                    "processing_metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "approach": "blueprint",
                        "components": ["enhanced_analyzer", "engine_v2"]
                    }
                }
                
            except Exception as e:
                log.warning(f"Blueprint Engine V2実行エラー: {e}")
                # V2が失敗した場合は拡張分析のみ
                results = {
                    "blueprint_analysis": blueprint_analysis_results,
                    "processing_metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "approach": "blueprint",
                        "components": ["enhanced_analyzer_only"]
                    }
                }
            
            # Mind Readerの実行
            try:
                mind_reader_results = self.mind_reader.read_creator_mind(long_df)
                results["mind_reader"] = mind_reader_results
                results["processing_metadata"]["components"].append("mind_reader")
            except Exception as e:
                log.warning(f"Mind Reader実行エラー: {e}")
            
            log.info(f"ブループリント分析完了: {self._count_blueprint_constraints(results)}個の暗黙知制約を発見")
            return results
            
        except Exception as e:
            log.error(f"ブループリント分析実行エラー: {e}")
            return self._empty_blueprint_result()
    
    def integrate_blueprint_constraints_into_validation(self, blueprint_results: Dict, 
                                                      approach1: Dict, 
                                                      approach2: Dict, 
                                                      mece: Dict) -> Dict[str, List[Dict]]:
        """ブループリント制約を統合制約検証に組み込み"""
        integrated = {
            "high_confidence_constraints": [],
            "medium_confidence_constraints": [],
            "supplementary_constraints": [],
            "conflicting_constraints": []
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
        
        # MECEからの制約
        if "machine_readable" in mece:
            for constraint_type in ["hard_constraints", "soft_constraints", "preferences"]:
                for constraint in mece["machine_readable"].get(constraint_type, []):
                    constraint["source"] = "mece"
                    constraint["source_category"] = constraint_type
                    all_constraints.append(constraint)
        
        # ブループリント制約の追加
        blueprint_constraints = self._extract_blueprint_constraints(blueprint_results)
        all_constraints.extend(blueprint_constraints)
        
        # 制約の交差検証と分類（ブループリント要素込み）
        constraint_groups = self._group_constraints_with_blueprint(all_constraints)
        
        for group_id, constraints in constraint_groups.items():
            if len(constraints) >= 2:
                # 複数手法で確認された制約 → 高信頼度
                consensus_constraint = self._create_blueprint_enhanced_consensus(constraints)
                integrated["high_confidence_constraints"].append(consensus_constraint)
            
            elif len(constraints) == 1:
                constraint = constraints[0]
                confidence = self._extract_blueprint_confidence_score(constraint)
                
                if confidence >= 0.8:
                    integrated["high_confidence_constraints"].append(constraint)
                elif confidence >= 0.5:
                    integrated["medium_confidence_constraints"].append(constraint)
                else:
                    integrated["supplementary_constraints"].append(constraint)
        
        log.info(f"ブループリント統合完了: 高信頼度={len(integrated['high_confidence_constraints'])}, "
                f"中信頼度={len(integrated['medium_confidence_constraints'])}, "
                f"補完={len(integrated['supplementary_constraints'])}")
        
        return integrated
    
    def calculate_blueprint_enhanced_depth_score(self, filtered_constraints: List[Dict],
                                               approach1: Dict,
                                               approach2: Dict,
                                               mece: Dict,
                                               blueprint: Dict) -> Dict[str, float]:
        """ブループリント要素を統合した深度スコア計算"""
        metrics = {
            "overall_quality_score": 0.0,
            "depth_score": 0.0,
            "practicality_score": 0.0,
            "coverage_score": 0.0,
            "confidence_score": 0.0,
            "blueprint_insight_score": 0.0  # 新規追加
        }
        
        if not filtered_constraints:
            return metrics
        
        # 従来の深度スコア（制約数とソース多様性）
        total_constraints = len(filtered_constraints)
        source_diversity = len(set(c.get("source", "unknown") for c in filtered_constraints))
        
        # ブループリント要素を考慮した深度スコア強化
        blueprint_rules_count = len(blueprint.get("blueprint_analysis", {}).get("rules", []))
        blueprint_high_confidence_count = len(blueprint.get("blueprint_analysis", {}).get("high_confidence_rules", []))
        
        # 深度スコア = 基本制約数 + ソース多様性 + ブループリント暗黙知
        base_depth = (total_constraints / 50) * 0.5
        source_depth = (source_diversity / 4) * 0.2  # ブループリントを含めて4ソース
        blueprint_depth = (blueprint_rules_count / 30) * 0.3  # ブループリント独自の深度貢献
        
        metrics["depth_score"] = min(1.0, base_depth + source_depth + blueprint_depth)
        
        # ブループリント洞察スコア
        if blueprint_rules_count > 0:
            high_confidence_ratio = blueprint_high_confidence_count / blueprint_rules_count
            blueprint_coverage = len(blueprint.get("blueprint_analysis", {}).get("segments", {}))
            
            metrics["blueprint_insight_score"] = (high_confidence_ratio * 0.6 + 
                                                 min(1.0, blueprint_coverage / 5) * 0.4)
        
        # 実用性スコア（ブループリント要素の実用性考慮）
        practical_count = sum(1 for c in filtered_constraints if self._is_blueprint_practically_useful(c))
        metrics["practicality_score"] = practical_count / total_constraints if total_constraints > 0 else 0
        
        # カバレッジスコア（MECE + ブループリント網羅性）
        mece_categories = len(mece.get("human_readable", {}).get("MECE分解事実", {}))
        blueprint_categories = len(set(rule.get("rule_type", "") for rule in blueprint.get("blueprint_analysis", {}).get("rules", [])))
        
        total_coverage = mece_categories + blueprint_categories
        metrics["coverage_score"] = min(1.0, total_coverage / 15)  # 15カテゴリで満点
        
        # 信頼度スコア（ブループリント信頼度も含む）
        confidences = [self._extract_blueprint_confidence_score(c) for c in filtered_constraints]
        metrics["confidence_score"] = sum(confidences) / len(confidences) if confidences else 0
        
        # 総合品質スコア（ブループリント要素統合版）
        metrics["overall_quality_score"] = (
            metrics["depth_score"] * 0.25 +
            metrics["practicality_score"] * 0.25 +
            metrics["coverage_score"] * 0.2 +
            metrics["confidence_score"] * 0.15 +
            metrics["blueprint_insight_score"] * 0.15
        )
        
        return metrics
    
    def _extract_blueprint_constraints(self, blueprint_results: Dict) -> List[Dict]:
        """ブループリント結果から制約を抽出"""
        constraints = []
        
        # 拡張ブループリント分析からの制約
        if "blueprint_analysis" in blueprint_results:
            rules = blueprint_results["blueprint_analysis"].get("rules", [])
            for rule in rules:
                constraint = {
                    "source": "blueprint",
                    "source_category": "implicit_knowledge",
                    "type": rule.rule_type,
                    "rule": rule.rule_description,
                    "confidence": rule.confidence_score,
                    "staff": rule.staff_name,
                    "segment": rule.segment,
                    "statistical_evidence": rule.statistical_evidence
                }
                constraints.append(constraint)
        
        # Blueprint V2からの制約
        if "blueprint_v2_full" in blueprint_results:
            v2_results = blueprint_results["blueprint_v2_full"]
            
            # MECE事実抽出結果
            for mece_key in ["mece_facility_facts", "mece_staff_facts", "mece_time_calendar_facts"]:
                if mece_key in v2_results and "machine_readable" in v2_results[mece_key]:
                    for constraint_type in ["hard_constraints", "soft_constraints", "preferences"]:
                        for constraint in v2_results[mece_key]["machine_readable"].get(constraint_type, []):
                            constraint["source"] = "blueprint_v2"
                            constraint["source_category"] = f"{mece_key}_{constraint_type}"
                            constraints.append(constraint)
        
        # Mind Readerからの制約
        if "mind_reader" in blueprint_results:
            mind_results = blueprint_results["mind_reader"]
            if "feature_importance" in mind_results:
                for feature in mind_results["feature_importance"]:
                    constraint = {
                        "source": "mind_reader",
                        "source_category": "feature_importance",
                        "type": "mind_reading_insight",
                        "rule": f"重要特徴量: {feature.get('feature', '')} (重要度: {feature.get('importance', 0):.3f})",
                        "confidence": feature.get("importance", 0),
                        "feature_name": feature.get("feature", "")
                    }
                    constraints.append(constraint)
        
        return constraints
    
    def _group_constraints_with_blueprint(self, constraints: List[Dict]) -> Dict[str, List[Dict]]:
        """ブループリント要素を考慮した制約グルーピング"""
        from collections import defaultdict
        
        groups = defaultdict(list)
        
        for constraint in constraints:
            # ブループリント特有のグループキー生成
            group_key = self._generate_blueprint_group_key(constraint)
            groups[group_key].append(constraint)
        
        return dict(groups)
    
    def _generate_blueprint_group_key(self, constraint: Dict) -> str:
        """ブループリント要素を含むグループキー生成"""
        key_components = []
        
        # 従来のキー要素
        if "type" in constraint:
            key_components.append(constraint["type"])
        elif "制約種別" in constraint:
            key_components.append(constraint["制約種別"])
        
        # ブループリント特有の要素
        if constraint.get("source") == "blueprint":
            if "staff" in constraint:
                key_components.append(f"blueprint_staff_{constraint['staff']}")
            if "segment" in constraint:
                key_components.append(f"segment_{constraint['segment']}")
        
        # Mind Reader特有の要素
        if constraint.get("source") == "mind_reader":
            if "feature_name" in constraint:
                key_components.append(f"feature_{constraint['feature_name']}")
        
        # 従来の要素
        if "column" in constraint:
            key_components.append(constraint["column"])
        elif "曜日" in constraint:
            key_components.append(f"weekday_{constraint['曜日']}")
        
        return "_".join(str(comp) for comp in key_components if comp)
    
    def _create_blueprint_enhanced_consensus(self, constraints: List[Dict]) -> Dict:
        """ブループリント要素を含む合意制約作成"""
        consensus = {
            "type": "blueprint_enhanced_consensus",
            "source_count": len(constraints),
            "source_methods": list(set(c.get("source", "unknown") for c in constraints)),
            "confidence_scores": [self._extract_blueprint_confidence_score(c) for c in constraints],
            "consensus_confidence": 0.0,
            "constraint_text": "",
            "supporting_evidence": constraints,
            "blueprint_enriched": any(c.get("source") == "blueprint" for c in constraints)
        }
        
        # ブループリント強化信頼度の計算
        confidence_scores = consensus["confidence_scores"]
        if confidence_scores:
            base_confidence = sum(confidence_scores) / len(confidence_scores)
            
            # ブループリント制約が含まれている場合はボーナス
            if consensus["blueprint_enriched"]:
                blueprint_bonus = 0.1
                consensus["consensus_confidence"] = min(1.0, base_confidence + blueprint_bonus)
            else:
                consensus["consensus_confidence"] = base_confidence
        
        # 制約テキストの統合（ブループリント要素優先）
        constraint_texts = []
        blueprint_texts = []
        
        for c in constraints:
            text = ""
            if "rule" in c:
                text = c["rule"]
            elif "constraint_implication" in c:
                text = c["constraint_implication"]
            elif "制約種別" in c:
                text = str(c["制約種別"])
            
            if text:
                if c.get("source") == "blueprint":
                    blueprint_texts.append(text)
                else:
                    constraint_texts.append(text)
        
        # ブループリントテキストを優先して統合
        all_texts = blueprint_texts + constraint_texts
        if all_texts:
            consensus["constraint_text"] = " | ".join(set(all_texts))
        
        return consensus
    
    def _extract_blueprint_confidence_score(self, constraint: Dict) -> float:
        """ブループリント要素を考慮した信頼度スコア抽出"""
        # 従来の信頼度抽出
        confidence_keys = ["confidence", "確信度", "confidence_score", "priority_score", "importance"]
        
        for key in confidence_keys:
            if key in constraint:
                confidence = float(constraint[key])
                
                # ブループリント制約の場合は信頼度を微調整
                if constraint.get("source") == "blueprint":
                    # 統計的根拠がある場合はボーナス
                    if "statistical_evidence" in constraint:
                        confidence = min(1.0, confidence + 0.05)
                
                return confidence
        
        # P値がある場合
        if "p_value" in constraint:
            return 1 - float(constraint["p_value"])
        
        # ブループリント特有の信頼度計算
        if constraint.get("source") == "blueprint" and "statistical_evidence" in constraint:
            evidence = constraint["statistical_evidence"]
            if isinstance(evidence, dict) and "confidence_score" in evidence:
                return float(evidence["confidence_score"])
        
        # デフォルト
        return 0.5
    
    def _is_blueprint_practically_useful(self, constraint: Dict) -> bool:
        """ブループリント要素を考慮した実用性判定"""
        # 従来の実用性指標
        basic_useful_indicators = [
            "constraint_text" in constraint and len(constraint["constraint_text"]) > 10,
            "rule" in constraint and len(str(constraint["rule"])) > 5,
            "constraint_implication" in constraint and len(constraint["constraint_implication"]) > 10,
            self._extract_blueprint_confidence_score(constraint) > 0.3,
            any(key in constraint for key in ["staff", "スタッフ", "曜日", "時間帯", "勤務コード"])
        ]
        
        # ブループリント特有の実用性指標
        blueprint_useful_indicators = [
            constraint.get("source") == "blueprint",
            "statistical_evidence" in constraint,
            constraint.get("segment") != "全体",  # セグメント特化は実用的
            "staff" in constraint,  # スタッフ固有制約は実用的
        ]
        
        # 基本実用性 + ブループリント実用性
        basic_score = sum(basic_useful_indicators)
        blueprint_score = sum(blueprint_useful_indicators)
        
        # いずれかが半数以上満たしていれば実用的
        basic_threshold = len(basic_useful_indicators) // 2
        blueprint_threshold = len(blueprint_useful_indicators) // 2
        
        return (basic_score >= basic_threshold) or (blueprint_score >= blueprint_threshold)
    
    def _count_blueprint_constraints(self, results: Dict) -> int:
        """ブループリント結果内の制約数をカウント"""
        count = 0
        
        if "blueprint_analysis" in results:
            count += len(results["blueprint_analysis"].get("rules", []))
        
        if "blueprint_v2_full" in results:
            v2_results = results["blueprint_v2_full"]
            for key in ["mece_facility_facts", "mece_staff_facts", "mece_time_calendar_facts"]:
                if key in v2_results and "machine_readable" in v2_results[key]:
                    for constraint_type in ["hard_constraints", "soft_constraints", "preferences"]:
                        count += len(v2_results[key]["machine_readable"].get(constraint_type, []))
        
        if "mind_reader" in results:
            count += len(results["mind_reader"].get("feature_importance", []))
        
        return count
    
    def _empty_blueprint_result(self) -> Dict[str, Any]:
        """空のブループリント結果を生成"""
        return {
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "approach": "blueprint",
                "status": "empty_result"
            }
        }