"""ShiftMindReaderとMECE事実抽出を統合した、Blueprint-V2の中核エンジン"""
import logging
from typing import Dict, Any, List

import pandas as pd

log = logging.getLogger(__name__)

from .advanced_blueprint_engine import AdvancedBlueprintEngine

# ShiftMindReader import with fallback (force lightweight version to avoid sklearn issues)
# Use the lightweight version by default to avoid any sklearn dependencies
try:
    from .shift_mind_reader_lite import ShiftMindReaderLite as ShiftMindReader
    _HAS_SHIFT_MIND_READER = True
except ImportError:
    _HAS_SHIFT_MIND_READER = False
    # Create a dummy class as ultimate fallback
    class ShiftMindReader:
        def __init__(self, *args, **kwargs):
            pass
        def analyze_shift_decisions(self, *args, **kwargs):
            return {"error": "ShiftMindReader not available"}
        def extract_decision_rules(self, *args, **kwargs):
            return ["ShiftMindReader not available"]

if _HAS_SHIFT_MIND_READER:
    log.info("[AdvancedBlueprintEngineV2] Using lightweight ShiftMindReader (sklearn-free)")
else:
    log.error("[AdvancedBlueprintEngineV2] ShiftMindReaderLite not available")
from .mece_fact_extractor import MECEFactExtractor
from .axis2_staff_mece_extractor import StaffMECEFactExtractor
from .axis3_time_calendar_mece_extractor import TimeCalendarMECEFactExtractor

log = logging.getLogger(__name__)


class AdvancedBlueprintEngineV2(AdvancedBlueprintEngine):
    """思考プロセス解読機能と既存分析を統合したエンジン"""

    def __init__(self, slot_minutes: int = 30):
        super().__init__()
        self.slot_minutes = slot_minutes
        self.mind_reader = ShiftMindReader()
        self.mece_extractor = MECEFactExtractor(slot_minutes=slot_minutes)
        try:
            self.staff_mece_extractor = StaffMECEFactExtractor()
            self.time_calendar_extractor = TimeCalendarMECEFactExtractor()
        except Exception as e:
            log.warning(f"軸2・軸3抽出器の初期化に失敗: {e}")
            self.staff_mece_extractor = None
            self.time_calendar_extractor = None

    def run_full_blueprint_analysis(self, long_df: pd.DataFrame, wt_df: pd.DataFrame = None) -> Dict[str, Any]:
        """V2の全分析を実行する統合メソッド（軸1+軸2+軸3 MECE事実抽出含む）"""
        log.info("Blueprint-V2 フル分析を開始します...")

        # MECE事実抽出（軸1: 施設ルール）
        log.info("軸1: 施設ルールのMECE事実抽出を実行中...")
        facility_mece_results = self.mece_extractor.extract_axis1_facility_rules(long_df, wt_df)

        # MECE事実抽出（軸2: 職員ルール）
        log.info("軸2: 職員ルールのMECE事実抽出を実行中...")
        staff_mece_results = self.staff_mece_extractor.extract_axis2_staff_rules(long_df, wt_df)

        # MECE事実抽出（軸3: 時間・カレンダールール）
        log.info("軸3: 時間・カレンダールールのMECE事実抽出を実行中...")
        time_calendar_results = self.time_calendar_extractor.extract_axis3_time_calendar_rules(long_df, wt_df)

        # 軸1+軸2+軸3制約統合処理
        log.info("軸1+軸2+軸3制約統合処理を実行中...")
        integrated_constraints = self._integrate_multi_axis_constraints(facility_mece_results, staff_mece_results, time_calendar_results)

        # 既存の分析
        causal_results = self.analyze_causal_relationships(long_df)
        ml_pattern_results = self.analyze_hidden_patterns_with_ml(long_df)
        network_results = self.analyze_network_effects(long_df)
        temporal_results = self.temporal_pattern_mining(long_df)

        mind_reader_results = self.mind_reader.read_creator_mind(long_df)

        all_results = {
            "mece_facility_facts": facility_mece_results,
            "mece_staff_facts": staff_mece_results,
            "mece_time_calendar_facts": time_calendar_results,
            "integrated_constraints": integrated_constraints,
            "causal_analysis": causal_results,
            "ml_patterns": ml_pattern_results,
            "network_analysis": network_results,
            "temporal_analysis": temporal_results,
            "mind_reading": mind_reader_results,
        }

        all_results["actionable_insights"] = self.generate_actionable_insights_v2(all_results)

        return all_results

    def generate_actionable_insights_v2(self, all_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """思考プロセス解読結果も加味した、より高度なインサイトを生成"""

        insights = super().generate_actionable_insights(all_results.get("causal_analysis", {}))

        mind_reader_results = all_results.get("mind_reading", {})
        feature_importance = pd.DataFrame(mind_reader_results.get("feature_importance", []))

        if not feature_importance.empty:
            top_factor = feature_importance.iloc[0]
            insights.append({
                "type": "mental_model",
                "priority": "high",
                "action": f"最優先事項の共有: このシフトは「{top_factor['feature']}」を最も重視して作成されています。",
                "expected_impact": "チーム全体の判断基準を統一し、意思決定のブレをなくす。",
                "confidence": 0.9,
                "source": "ShiftMindReader",
            })

        return insights

    def analyze_implicit_patterns(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """暗黙知パターンの分析（dash_app.py用）"""
        log.info("[AdvancedBlueprintEngineV2] 暗黙知パターン分析を開始...")
        
        try:
            # MECEFactExtractorを使用した軸1事実抽出
            facility_facts = self.mece_extractor.extract_axis1_facility_rules(long_df)
            
            # ShiftMindReaderによる暗黙知抽出
            mind_results = self.mind_reader.read_creator_mind(long_df) if hasattr(self.mind_reader, 'read_creator_mind') else {}
            
            # 暗黙知パターンの統合処理
            implicit_patterns = []
            
            # MECE事実から暗黙知パターンを抽出
            human_readable = facility_facts.get('human_readable', {})
            high_confidence_facts = human_readable.get('確信度別分類', {}).get('高確信度', [])
            
            for fact in high_confidence_facts[:10]:  # 上位10件
                implicit_patterns.append({
                    'pattern_id': f"P{len(implicit_patterns)+1:03d}",
                    'description': f"{fact.get('カテゴリー', 'N/A')}: {fact.get('詳細', {}).get('制約種別', 'N/A')}",
                    'confidence': fact.get('確信度', 0.0),
                    'affected_staff': fact.get('詳細', {}).get('スタッフ', 'N/A'),
                    'category': fact.get('サブカテゴリー', 'N/A'),
                    'source': 'MECE事実抽出'
                })
            
            # マインドリーダー結果の統合
            if mind_results:
                feature_importance = mind_results.get('feature_importance', [])
                for i, feature in enumerate(feature_importance[:5]):
                    implicit_patterns.append({
                        'pattern_id': f"M{i+1:03d}",
                        'description': f"思考パターン: {feature.get('feature', 'N/A')}を重視",
                        'confidence': feature.get('importance', 0.0),
                        'affected_staff': 'シフト作成者',
                        'category': '意思決定パターン',
                        'source': 'ShiftMindReader'
                    })
            
            log.info(f"[AdvancedBlueprintEngineV2] 暗黙知パターン {len(implicit_patterns)}件を抽出")
            
            return {
                'implicit_patterns': implicit_patterns,
                'analysis_metadata': {
                    'total_patterns': len(implicit_patterns),
                    'high_confidence_count': len([p for p in implicit_patterns if p['confidence'] >= 0.8]),
                    'data_period': {
                        'start': long_df['ds'].min().isoformat() if not long_df.empty else None,
                        'end': long_df['ds'].max().isoformat() if not long_df.empty else None
                    }
                }
            }
            
        except Exception as e:
            log.error(f"[AdvancedBlueprintEngineV2] 暗黙知分析エラー: {e}", exc_info=True)
            return {
                'implicit_patterns': [],
                'error': str(e),
                'analysis_metadata': {'total_patterns': 0}
            }

    def analyze_objective_facts(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """客観的事実の分析（dash_app.py用）"""
        log.info("[AdvancedBlueprintEngineV2] 客観的事実分析を開始...")
        
        try:
            # MECEFactExtractorによる事実抽出
            facility_facts = self.mece_extractor.extract_axis1_facility_rules(long_df)
            
            # 客観的事実の構造化
            objective_facts = []
            
            # MECE分解事実から客観的事実を抽出
            mece_facts = facility_facts.get('human_readable', {}).get('MECE分解事実', {})
            
            for category, facts_list in mece_facts.items():
                for fact in facts_list:
                    objective_facts.append({
                        'スタッフ': fact.get('スタッフ', 'N/A'),
                        'カテゴリー': category,
                        '事実タイプ': fact.get('制約種別', 'N/A'),
                        '詳細': str(fact.get('勤務コード', fact.get('職種', fact.get('時間帯', 'N/A')))),
                        '確信度': fact.get('確信度', 0.0),
                        '事実性': fact.get('事実性', '実績ベース'),
                        'メタデータ': fact
                    })
            
            # カテゴリー別集計
            category_summary = {}
            for fact in objective_facts:
                category = fact['カテゴリー']
                if category not in category_summary:
                    category_summary[category] = {
                        'count': 0,
                        'avg_confidence': 0.0,
                        'high_confidence_count': 0
                    }
                category_summary[category]['count'] += 1
                category_summary[category]['avg_confidence'] += fact['確信度']
                if fact['確信度'] >= 0.8:
                    category_summary[category]['high_confidence_count'] += 1
            
            # 平均確信度の計算
            for category in category_summary:
                count = category_summary[category]['count']
                if count > 0:
                    category_summary[category]['avg_confidence'] /= count
            
            log.info(f"[AdvancedBlueprintEngineV2] 客観的事実 {len(objective_facts)}件を抽出")
            
            return {
                'objective_facts': objective_facts,
                'category_summary': category_summary,
                'analysis_metadata': {
                    'total_facts': len(objective_facts),
                    'categories_count': len(category_summary),
                    'high_confidence_facts': len([f for f in objective_facts if f['確信度'] >= 0.8])
                }
            }
            
        except Exception as e:
            log.error(f"[AdvancedBlueprintEngineV2] 客観的事実分析エラー: {e}", exc_info=True)
            return {
                'objective_facts': [],
                'error': str(e),
                'analysis_metadata': {'total_facts': 0}
            }

    def analyze_comprehensive(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """統合分析（暗黙知＋客観的事実）"""
        log.info("[AdvancedBlueprintEngineV2] 統合分析を開始...")
        
        try:
            # 暗黙知と客観的事実の両方を取得
            implicit_results = self.analyze_implicit_patterns(long_df)
            facts_results = self.analyze_objective_facts(long_df)
            
            implicit_patterns = implicit_results.get('implicit_patterns', [])
            objective_facts = facts_results.get('objective_facts', [])
            
            # 暗黙知と事実の関連性分析
            relationships = []
            
            # 同じカテゴリーまたはスタッフに関連する暗黙知と事実を関連付け
            for pattern in implicit_patterns:
                related_facts = []
                for fact in objective_facts:
                    # カテゴリーまたはスタッフの一致で関連性を判定
                    if (pattern.get('category') == fact.get('カテゴリー') or
                        pattern.get('affected_staff') == fact.get('スタッフ')):
                        related_facts.append(fact)
                
                if related_facts:
                    relationships.append({
                        'pattern_id': pattern.get('pattern_id'),
                        'pattern_description': pattern.get('description'),
                        'related_facts_count': len(related_facts),
                        'related_facts': related_facts[:3],  # 上位3件のみ
                        'relationship_strength': min(1.0, len(related_facts) / 5.0),
                        'insight': f"「{pattern.get('description')}」は{len(related_facts)}件の客観的事実に裏付けられています"
                    })
            
            # 統合インサイトの生成
            integrated_insights = []
            
            # 高確信度の暗黙知と事実の組み合わせ
            high_conf_patterns = [p for p in implicit_patterns if p.get('confidence', 0) >= 0.8]
            high_conf_facts = [f for f in objective_facts if f.get('確信度', 0) >= 0.8]
            
            if high_conf_patterns and high_conf_facts:
                integrated_insights.append({
                    'type': 'high_confidence_integration',
                    'insight': f"{len(high_conf_patterns)}件の高確信度暗黙知と{len(high_conf_facts)}件の高確信度事実が発見されました",
                    'recommendation': "これらの組み合わせから、シフト作成の核となるルールを確立できます",
                    'priority': 'high'
                })
            
            log.info(f"[AdvancedBlueprintEngineV2] 統合分析完了: 関連性{len(relationships)}件, インサイト{len(integrated_insights)}件")
            
            return {
                'implicit_patterns': implicit_patterns,
                'objective_facts': objective_facts,
                'relationships': relationships,
                'integrated_insights': integrated_insights,
                'analysis_metadata': {
                    'total_patterns': len(implicit_patterns),
                    'total_facts': len(objective_facts),
                    'relationships_found': len(relationships),
                    'insights_generated': len(integrated_insights)
                }
            }
            
        except Exception as e:
            log.error(f"[AdvancedBlueprintEngineV2] 統合分析エラー: {e}", exc_info=True)
            return {
                'implicit_patterns': [],
                'objective_facts': [],
                'relationships': [],
                'error': str(e),
                'analysis_metadata': {'total_patterns': 0, 'total_facts': 0}
            }

    def _integrate_multi_axis_constraints(self, facility_results: Dict[str, Any], staff_results: Dict[str, Any], time_calendar_results: Dict[str, Any]) -> Dict[str, Any]:
        """軸1+軸2+軸3の統合制約処理
        
        Args:
            facility_results: 軸1施設ルールの抽出結果
            staff_results: 軸2職員ルールの抽出結果
            time_calendar_results: 軸3時間・カレンダールールの抽出結果
            
        Returns:
            統合制約データ（3軸統合版）
        """
        from datetime import datetime
        
        log.info("3軸制約統合処理を開始...")
        
        # 各軸のmachine_readableデータを取得
        facility_constraints = facility_results.get('machine_readable', {})
        staff_constraints = staff_results.get('machine_readable', {})
        time_calendar_constraints = time_calendar_results.get('machine_readable', {})
        
        # 統合制約データの初期化
        integrated = {
            "hard_constraints": [],
            "soft_constraints": [],
            "preferences": [],
            "constraint_relationships": [],
            "conflict_resolution": {},
            "integration_metadata": {}
        }
        
        # 軸1制約の統合（施設レベル制約）
        facility_hard = facility_constraints.get('hard_constraints', [])
        facility_soft = facility_constraints.get('soft_constraints', [])
        facility_prefs = facility_constraints.get('preferences', [])
        
        # 軸2制約の統合（個人レベル制約）
        staff_hard = staff_constraints.get('staff_hard_constraints', [])
        staff_soft = staff_constraints.get('staff_soft_constraints', [])
        staff_prefs = staff_constraints.get('staff_preferences', [])
        
        # 軸3制約の統合（時間・カレンダー制約）
        time_hard = time_calendar_constraints.get('time_hard_constraints', [])
        time_soft = time_calendar_constraints.get('time_soft_constraints', [])
        time_prefs = time_calendar_constraints.get('time_preferences', [])
        time_calendar = time_calendar_constraints.get('calendar_constraints', [])
        
        # ハード制約統合（最高優先度）
        for constraint in facility_hard:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        for constraint in staff_hard:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        for constraint in time_hard:
            constraint['axis'] = 3
            constraint['scope'] = 'temporal'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        # カレンダー制約は特別扱い（高優先度ハード制約）
        for constraint in time_calendar:
            constraint['axis'] = 3
            constraint['scope'] = 'calendar'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        # ソフト制約統合（中優先度）
        for constraint in facility_soft:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'high'
            integrated["soft_constraints"].append(constraint)
        
        for constraint in staff_soft:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'high'
            integrated["soft_constraints"].append(constraint)
        
        for constraint in time_soft:
            constraint['axis'] = 3
            constraint['scope'] = 'temporal'
            constraint['integration_priority'] = 'high'
            integrated["soft_constraints"].append(constraint)
        
        # 推奨設定統合（低優先度）
        for constraint in facility_prefs:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'medium'
            integrated["preferences"].append(constraint)
        
        for constraint in staff_prefs:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'medium'
            integrated["preferences"].append(constraint)
        
        for constraint in time_prefs:
            constraint['axis'] = 3
            constraint['scope'] = 'temporal'
            constraint['integration_priority'] = 'medium'
            integrated["preferences"].append(constraint)
        
        # 3軸間関係性分析
        relationships = self._analyze_multi_axis_relationships(integrated)
        integrated["constraint_relationships"] = relationships
        
        # 3軸競合解決策
        conflicts = self._detect_and_resolve_multi_axis_conflicts(integrated)
        integrated["conflict_resolution"] = conflicts
        
        # 統合メタデータ
        integrated["integration_metadata"] = {
            "integration_timestamp": datetime.now().isoformat(),
            "axis_coverage": {
                "axis_1_facility": len(facility_hard) + len(facility_soft) + len(facility_prefs),
                "axis_2_staff": len(staff_hard) + len(staff_soft) + len(staff_prefs),
                "axis_3_time_calendar": len(time_hard) + len(time_soft) + len(time_prefs) + len(time_calendar)
            },
            "constraint_distribution": {
                "hard_constraints": len(integrated["hard_constraints"]),
                "soft_constraints": len(integrated["soft_constraints"]),
                "preferences": len(integrated["preferences"])
            },
            "integration_quality": {
                "relationship_coverage": len(relationships),
                "conflict_detection": len(conflicts),
                "completeness_score": self._calculate_multi_axis_completeness(facility_results, staff_results, time_calendar_results)
            }
        }
        
        # 統合レポート作成
        integrated_report = self._create_multi_axis_human_readable_report(
            facility_results, staff_results, time_calendar_results, integrated
        )
        
        return {
            "machine_readable": integrated,
            "human_readable": integrated_report,
            "training_data": self._format_multi_axis_training_data(facility_results, staff_results, time_calendar_results),
            "integration_metadata": integrated["integration_metadata"]
        }

    def _integrate_axis1_axis2_constraints(self, facility_results: Dict[str, Any], staff_results: Dict[str, Any]) -> Dict[str, Any]:
        """軸1(施設ルール)+軸2(職員ルール)の制約統合処理
        
        Args:
            facility_results: 軸1施設ルールの抽出結果
            staff_results: 軸2職員ルールの抽出結果
            
        Returns:
            統合制約データ（人間確認用+AI実行用+関係性分析）
        """
        from datetime import datetime
        
        log.info("制約統合処理を開始...")
        
        # 各軸のmachine_readableデータを取得
        facility_constraints = facility_results.get('machine_readable', {})
        staff_constraints = staff_results.get('machine_readable', {})
        
        # 統合制約データの初期化
        integrated = {
            "hard_constraints": [],
            "soft_constraints": [],
            "preferences": [],
            "constraint_relationships": [],
            "conflict_resolution": {},
            "integration_metadata": {}
        }
        
        # 軸1制約の統合（施設レベル制約）
        facility_hard = facility_constraints.get('hard_constraints', [])
        facility_soft = facility_constraints.get('soft_constraints', [])
        facility_prefs = facility_constraints.get('preferences', [])
        
        # 軸2制約の統合（個人レベル制約）
        staff_hard = staff_constraints.get('staff_hard_constraints', [])
        staff_soft = staff_constraints.get('staff_soft_constraints', [])
        staff_prefs = staff_constraints.get('staff_preferences', [])
        
        # ハード制約統合（最高優先度）
        for constraint in facility_hard:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        for constraint in staff_hard:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'critical'
            integrated["hard_constraints"].append(constraint)
        
        # ソフト制約統合（中優先度）
        for constraint in facility_soft:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'high'
            integrated["soft_constraints"].append(constraint)
        
        for constraint in staff_soft:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'high'
            integrated["soft_constraints"].append(constraint)
        
        # 推奨設定統合（低優先度）
        for constraint in facility_prefs:
            constraint['axis'] = 1
            constraint['scope'] = 'facility'
            constraint['integration_priority'] = 'medium'
            integrated["preferences"].append(constraint)
        
        for constraint in staff_prefs:
            constraint['axis'] = 2
            constraint['scope'] = 'individual'
            constraint['integration_priority'] = 'medium'
            integrated["preferences"].append(constraint)
        
        # 制約間関係性分析
        relationships = self._analyze_constraint_relationships(integrated)
        integrated["constraint_relationships"] = relationships
        
        # 競合解決策
        conflicts = self._detect_and_resolve_conflicts(integrated)
        integrated["conflict_resolution"] = conflicts
        
        # 統合メタデータ
        integrated["integration_metadata"] = {
            "integration_timestamp": datetime.now().isoformat(),
            "axis_coverage": {
                "axis_1_facility": len(facility_hard) + len(facility_soft) + len(facility_prefs),
                "axis_2_staff": len(staff_hard) + len(staff_soft) + len(staff_prefs)
            },
            "constraint_distribution": {
                "hard_constraints": len(integrated["hard_constraints"]),
                "soft_constraints": len(integrated["soft_constraints"]),
                "preferences": len(integrated["preferences"])
            },
            "integration_quality": {
                "relationship_coverage": len(relationships),
                "conflict_detection": len(conflicts),
                "completeness_score": self._calculate_integration_completeness(facility_results, staff_results)
            }
        }
        
        # 統合レポート作成
        integrated_report = self._create_integrated_human_readable_report(
            facility_results, staff_results, integrated
        )
        
        return {
            "machine_readable": integrated,
            "human_readable": integrated_report,
            "training_data": self._format_integrated_training_data(facility_results, staff_results),
            "integration_metadata": integrated["integration_metadata"]
        }
    
    def _analyze_constraint_relationships(self, integrated_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制約間の関係性分析"""
        relationships = []
        
        all_constraints = (
            integrated_constraints.get("hard_constraints", []) +
            integrated_constraints.get("soft_constraints", []) +
            integrated_constraints.get("preferences", [])
        )
        
        # 軸1-軸2間の関係性検出
        facility_constraints = [c for c in all_constraints if c.get('axis') == 1]
        staff_constraints = [c for c in all_constraints if c.get('axis') == 2]
        
        for facility_constraint in facility_constraints:
            for staff_constraint in staff_constraints:
                relationship_type = self._detect_relationship_type(facility_constraint, staff_constraint)
                if relationship_type:
                    relationships.append({
                        "constraint_1_id": facility_constraint.get('id'),
                        "constraint_2_id": staff_constraint.get('id'),
                        "relationship_type": relationship_type,
                        "interaction_strength": self._calculate_interaction_strength(facility_constraint, staff_constraint),
                        "resolution_strategy": self._suggest_resolution_strategy(relationship_type)
                    })
        
        return relationships
    
    def _detect_relationship_type(self, constraint1: Dict, constraint2: Dict) -> str:
        """制約間の関係タイプを検出"""
        # 簡略化された関係検出ロジック
        type1 = constraint1.get('type', '')
        type2 = constraint2.get('type', '')
        
        # 時間関連の関係
        time_related = ['勤務体制制約', '時間制約', '時間選好制約', '勤務時間制約']
        if any(keyword in type1 for keyword in time_related) and any(keyword in type2 for keyword in time_related):
            return 'temporal_correlation'
        
        # 人員関連の関係
        staff_related = ['人員配置制約', '職種', 'スキル', '役職制約']
        if any(keyword in type1 for keyword in staff_related) and any(keyword in type2 for keyword in staff_related):
            return 'staffing_correlation'
        
        # 休暇・休息関連の関係
        rest_related = ['継続性制約', '休暇', '休息', '疲労']
        if any(keyword in type1 for keyword in rest_related) and any(keyword in type2 for keyword in rest_related):
            return 'rest_correlation'
        
        return 'general_correlation'
    
    def _calculate_interaction_strength(self, constraint1: Dict, constraint2: Dict) -> float:
        """制約間の相互作用強度を計算"""
        # 簡略化された強度計算
        confidence1 = constraint1.get('confidence', 0.5)
        confidence2 = constraint2.get('confidence', 0.5)
        
        # 両方の確信度を考慮した相互作用強度
        return (confidence1 + confidence2) / 2
    
    def _suggest_resolution_strategy(self, relationship_type: str) -> str:
        """関係タイプに基づく解決策提案"""
        strategies = {
            'temporal_correlation': '時間制約の優先度調整と時間枠最適化',
            'staffing_correlation': '人員配置制約の階層化と例外処理',
            'rest_correlation': '休息制約の統一基準設定と個人差配慮',
            'general_correlation': '制約優先度のバランシングと段階的適用'
        }
        return strategies.get(relationship_type, '個別分析による最適化')
    
    def _detect_and_resolve_conflicts(self, integrated_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """制約間競合の検出と解決策提案"""
        conflicts = {
            "detected_conflicts": [],
            "resolution_strategies": [],
            "priority_hierarchy": []
        }
        
        # 基本的な競合検出（簡略版）
        hard_constraints = integrated_constraints.get("hard_constraints", [])
        
        facility_hard = [c for c in hard_constraints if c.get('axis') == 1]
        staff_hard = [c for c in hard_constraints if c.get('axis') == 2]
        
        if len(facility_hard) > 0 and len(staff_hard) > 0:
            conflicts["detected_conflicts"].append({
                "conflict_type": "axis_level_tension",
                "description": "施設レベル制約と個人レベル制約間の調整が必要",
                "affected_constraints": len(facility_hard) + len(staff_hard),
                "severity": "medium"
            })
            
            conflicts["resolution_strategies"].append({
                "strategy": "hierarchical_priority",
                "description": "施設レベル制約を基準とし、個人制約を可能な範囲で適用",
                "implementation": "施設制約 → 個人制約の順で適用し、競合時は施設制約を優先"
            })
        
        # 優先度階層の定義
        conflicts["priority_hierarchy"] = [
            {"level": 1, "type": "facility_hard_constraints", "description": "施設レベル必須制約"},
            {"level": 2, "type": "staff_hard_constraints", "description": "個人レベル必須制約"},
            {"level": 3, "type": "facility_soft_constraints", "description": "施設レベル推奨制約"},
            {"level": 4, "type": "staff_soft_constraints", "description": "個人レベル推奨制約"},
            {"level": 5, "type": "preferences", "description": "最適化ヒント"}
        ]
        
        return conflicts
    
    def _calculate_integration_completeness(self, facility_results: Dict, staff_results: Dict) -> float:
        """統合完全性スコアの計算"""
        facility_metadata = facility_results.get('extraction_metadata', {})
        staff_metadata = staff_results.get('extraction_metadata', {})
        
        facility_coverage = facility_metadata.get('extraction_coverage', {})
        staff_coverage = staff_metadata.get('extraction_coverage', {})
        
        facility_total = sum(facility_coverage.values()) if facility_coverage else 0
        staff_total = sum(staff_coverage.values()) if staff_coverage else 0
        
        # 両軸のバランスを考慮した完全性スコア
        if facility_total + staff_total == 0:
            return 0.0
        
        balance_score = 1 - abs(facility_total - staff_total) / (facility_total + staff_total)
        coverage_score = min(1.0, (facility_total + staff_total) / 50)  # 基準値50で正規化
        
        return (balance_score * 0.4 + coverage_score * 0.6)
    
    def _create_integrated_human_readable_report(self, facility_results: Dict, staff_results: Dict, integrated: Dict) -> Dict[str, Any]:
        """統合された人間確認用レポート作成"""
        facility_hr = facility_results.get('human_readable', {})
        staff_hr = staff_results.get('human_readable', {})
        
        return {
            "統合サマリー": {
                "軸1_施設ルール": facility_hr.get('抽出事実サマリー', {}),
                "軸2_職員ルール": staff_hr.get('抽出事実サマリー', {}),
                "統合制約数": {
                    "ハード制約": len(integrated['machine_readable'].get('hard_constraints', [])),
                    "ソフト制約": len(integrated['machine_readable'].get('soft_constraints', [])),
                    "推奨設定": len(integrated['machine_readable'].get('preferences', []))
                }
            },
            "制約統合分析": {
                "関係性": integrated['machine_readable'].get('constraint_relationships', []),
                "競合解決": integrated['machine_readable'].get('conflict_resolution', {}),
                "完全性スコア": integrated['machine_readable']['integration_metadata'].get('integration_quality', {}).get('completeness_score', 0)
            },
            "実行優先度": integrated['machine_readable'].get('conflict_resolution', {}).get('priority_hierarchy', []),
            "要確認事項": self._generate_integration_review_items(facility_hr, staff_hr, integrated)
        }
    
    def _format_integrated_training_data(self, facility_results: Dict, staff_results: Dict) -> Dict[str, Any]:
        """統合学習データの形式化"""
        facility_training = facility_results.get('training_data', {})
        staff_training = staff_results.get('training_data', {})
        
        return {
            "integrated_features": {
                "facility_level": facility_training,
                "individual_level": staff_training,
                "cross_axis_correlations": []  # 軸間相関特徴量（将来拡張）
            },
            "constraint_embeddings": [],  # 制約のベクトル表現（将来拡張）
            "relationship_graph": []  # 制約関係グラフ（将来拡張）
        }
    
    def _generate_integration_review_items(self, facility_hr: Dict, staff_hr: Dict, integrated: Dict) -> List[str]:
        """統合結果の要確認事項を生成"""
        review_items = []
        
        # 制約数の妥当性確認
        total_constraints = len(integrated['machine_readable'].get('hard_constraints', []))
        if total_constraints > 100:
            review_items.append(f"制約数が{total_constraints}件と多数です。優先度の見直しをご検討ください。")
        
        # 軸間バランス確認
        facility_count = len([c for c in integrated['machine_readable'].get('hard_constraints', []) if c.get('axis') == 1])
        staff_count = len([c for c in integrated['machine_readable'].get('hard_constraints', []) if c.get('axis') == 2])
        
        if facility_count == 0:
            review_items.append("施設レベル制約が検出されませんでした。データの確認が必要です。")
        if staff_count == 0:
            review_items.append("個人レベル制約が検出されませんでした。スタッフデータの確認が必要です。")
        
        # 競合の確認
        conflicts = integrated['machine_readable'].get('conflict_resolution', {}).get('detected_conflicts', [])
        if len(conflicts) > 0:
            review_items.append(f"{len(conflicts)}件の制約競合が検出されました。解決策の確認が必要です。")
        
        return review_items

    def _analyze_multi_axis_relationships(self, integrated_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """3軸間の制約関係性分析"""
        relationships = []
        
        all_constraints = (
            integrated_constraints.get("hard_constraints", []) +
            integrated_constraints.get("soft_constraints", []) +
            integrated_constraints.get("preferences", [])
        )
        
        # 軸間の関係性検出
        axis_groups = {
            1: [c for c in all_constraints if c.get('axis') == 1],
            2: [c for c in all_constraints if c.get('axis') == 2],
            3: [c for c in all_constraints if c.get('axis') == 3]
        }
        
        # 軸1-軸3関係性（施設×時間）
        for facility_constraint in axis_groups[1]:
            for time_constraint in axis_groups[3]:
                relationship_type = self._detect_facility_time_relationship(facility_constraint, time_constraint)
                if relationship_type:
                    relationships.append({
                        "constraint_1_id": facility_constraint.get('id'),
                        "constraint_2_id": time_constraint.get('id'),
                        "relationship_type": relationship_type,
                        "axis_pair": "facility_time",
                        "interaction_strength": self._calculate_interaction_strength(facility_constraint, time_constraint),
                        "resolution_strategy": self._suggest_facility_time_resolution(relationship_type)
                    })
        
        # 軸2-軸3関係性（職員×時間）
        for staff_constraint in axis_groups[2]:
            for time_constraint in axis_groups[3]:
                relationship_type = self._detect_staff_time_relationship(staff_constraint, time_constraint)
                if relationship_type:
                    relationships.append({
                        "constraint_1_id": staff_constraint.get('id'),
                        "constraint_2_id": time_constraint.get('id'),
                        "relationship_type": relationship_type,
                        "axis_pair": "staff_time",
                        "interaction_strength": self._calculate_interaction_strength(staff_constraint, time_constraint),
                        "resolution_strategy": self._suggest_staff_time_resolution(relationship_type)
                    })
        
        # 3軸同時関係性（施設×職員×時間）
        for facility_constraint in axis_groups[1][:5]:  # 計算量制御のため制限
            for staff_constraint in axis_groups[2][:5]:
                for time_constraint in axis_groups[3][:5]:
                    relationship_type = self._detect_three_way_relationship(facility_constraint, staff_constraint, time_constraint)
                    if relationship_type:
                        relationships.append({
                            "constraint_1_id": facility_constraint.get('id'),
                            "constraint_2_id": staff_constraint.get('id'),
                            "constraint_3_id": time_constraint.get('id'),
                            "relationship_type": relationship_type,
                            "axis_pair": "facility_staff_time",
                            "interaction_strength": (
                                self._calculate_interaction_strength(facility_constraint, staff_constraint) +
                                self._calculate_interaction_strength(staff_constraint, time_constraint) +
                                self._calculate_interaction_strength(facility_constraint, time_constraint)
                            ) / 3,
                            "resolution_strategy": self._suggest_three_way_resolution(relationship_type)
                        })
        
        return relationships
    
    def _detect_facility_time_relationship(self, facility_constraint: Dict, time_constraint: Dict) -> str:
        """施設×時間制約の関係タイプ検出"""
        facility_type = facility_constraint.get('type', '')
        time_type = time_constraint.get('type', '')
        
        # 営業時間×勤務体制
        if '営業時間' in time_type and '勤務体制' in facility_type:
            return 'operating_hours_workshift'
        
        # 繁忙期×人員配置
        if '繁忙期' in time_type and '人員配置' in facility_type:
            return 'busy_period_staffing'
        
        # 祝日×例外制約
        if '祝日' in time_type and '例外' in facility_type:
            return 'holiday_exception'
        
        return 'general_facility_time'
    
    def _detect_staff_time_relationship(self, staff_constraint: Dict, time_constraint: Dict) -> str:
        """職員×時間制約の関係タイプ検出"""
        staff_type = staff_constraint.get('type', '')
        time_type = time_constraint.get('type', '')
        
        # 個人勤務パターン×曜日制約
        if '個人勤務' in staff_type and '曜日' in time_type:
            return 'personal_weekday'
        
        # 時間選好×営業時間
        if '時間選好' in staff_type and '営業時間' in time_type:
            return 'time_preference_hours'
        
        # 休暇制約×繁忙期
        if '休暇' in staff_type and '繁忙期' in time_type:
            return 'leave_busy_period'
        
        return 'general_staff_time'
    
    def _detect_three_way_relationship(self, facility_constraint: Dict, staff_constraint: Dict, time_constraint: Dict) -> str:
        """3軸同時関係の検出"""
        facility_type = facility_constraint.get('type', '')
        staff_type = staff_constraint.get('type', '')
        time_type = time_constraint.get('type', '')
        
        # 施設人員配置×個人スキル×営業時間
        if '人員配置' in facility_type and 'スキル' in staff_type and '営業時間' in time_type:
            return 'staffing_skill_hours'
        
        # 勤務体制×個人パターン×曜日制約
        if '勤務体制' in facility_type and '個人勤務' in staff_type and '曜日' in time_type:
            return 'workshift_personal_weekday'
        
        return 'complex_three_way'
    
    def _suggest_facility_time_resolution(self, relationship_type: str) -> str:
        """施設×時間関係の解決策"""
        strategies = {
            'operating_hours_workshift': '営業時間内での効率的な勤務体制構築',
            'busy_period_staffing': '繁忙期に向けた段階的人員増強計画',
            'holiday_exception': '祝日営業の特別運用ルール策定',
            'general_facility_time': '時間制約を考慮した施設運用最適化'
        }
        return strategies.get(relationship_type, '個別最適化による調整')
    
    def _suggest_staff_time_resolution(self, relationship_type: str) -> str:
        """職員×時間関係の解決策"""
        strategies = {
            'personal_weekday': '個人の曜日選好を考慮したシフト調整',
            'time_preference_hours': '勤務時間帯の個人選好マッチング',
            'leave_busy_period': '繁忙期休暇制限と代替休暇提供',
            'general_staff_time': '個人制約と時間制約のバランス調整'
        }
        return strategies.get(relationship_type, '個人時間制約の柔軟な調整')
    
    def _suggest_three_way_resolution(self, relationship_type: str) -> str:
        """3軸関係の解決策"""
        strategies = {
            'staffing_skill_hours': 'スキルベース時間帯別人員配置最適化',
            'workshift_personal_weekday': '個人パターンを活かした曜日別勤務体制',
            'complex_three_way': '3軸バランス型段階的最適化'
        }
        return strategies.get(relationship_type, '多軸統合最適化アプローチ')
    
    def _detect_and_resolve_multi_axis_conflicts(self, integrated_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """3軸間競合の検出と解決策提案"""
        conflicts = {
            "detected_conflicts": [],
            "resolution_strategies": [],
            "priority_hierarchy": []
        }
        
        # 基本的な3軸競合検出
        hard_constraints = integrated_constraints.get("hard_constraints", [])
        
        facility_hard = [c for c in hard_constraints if c.get('axis') == 1]
        staff_hard = [c for c in hard_constraints if c.get('axis') == 2]
        time_hard = [c for c in hard_constraints if c.get('axis') == 3]
        
        # 3軸間の競合分析
        if len(facility_hard) > 0 and len(staff_hard) > 0 and len(time_hard) > 0:
            conflicts["detected_conflicts"].append({
                "conflict_type": "three_axis_tension",
                "description": "施設×職員×時間の3軸間で制約調整が必要",
                "affected_constraints": len(facility_hard) + len(staff_hard) + len(time_hard),
                "severity": "high",
                "axis_involvement": [1, 2, 3]
            })
            
            conflicts["resolution_strategies"].append({
                "strategy": "hierarchical_three_axis_priority",
                "description": "3軸優先度に基づく段階的制約適用",
                "implementation": "施設制約 → 時間制約 → 個人制約の順で適用し、上位制約を優先"
            })
        
        # 時間制約の特別扱い
        if len(time_hard) > 0:
            conflicts["resolution_strategies"].append({
                "strategy": "temporal_constraint_foundation",
                "description": "時間・カレンダー制約を基盤とした制約構築",
                "implementation": "営業時間・祝日等の時間制約を基盤とし、その範囲内で他制約を最適化"
            })
        
        # 3軸優先度階層の定義
        conflicts["priority_hierarchy"] = [
            {"level": 1, "type": "calendar_constraints", "description": "カレンダー・祝日制約", "axis": 3},
            {"level": 2, "type": "facility_hard_constraints", "description": "施設レベル必須制約", "axis": 1},
            {"level": 3, "type": "time_hard_constraints", "description": "時間帯必須制約", "axis": 3},
            {"level": 4, "type": "staff_hard_constraints", "description": "個人レベル必須制約", "axis": 2},
            {"level": 5, "type": "facility_soft_constraints", "description": "施設レベル推奨制約", "axis": 1},
            {"level": 6, "type": "time_soft_constraints", "description": "時間帯推奨制約", "axis": 3},
            {"level": 7, "type": "staff_soft_constraints", "description": "個人レベル推奨制約", "axis": 2},
            {"level": 8, "type": "preferences", "description": "最適化ヒント", "axis": "all"}
        ]
        
        return conflicts
    
    def _calculate_multi_axis_completeness(self, facility_results: Dict, staff_results: Dict, time_calendar_results: Dict) -> float:
        """3軸統合完全性スコアの計算"""
        facility_metadata = facility_results.get('extraction_metadata', {})
        staff_metadata = staff_results.get('extraction_metadata', {})
        time_metadata = time_calendar_results.get('extraction_metadata', {})
        
        facility_coverage = facility_metadata.get('extraction_coverage', {})
        staff_coverage = staff_metadata.get('extraction_coverage', {})
        time_coverage = time_metadata.get('extraction_coverage', {})
        
        facility_total = sum(facility_coverage.values()) if facility_coverage else 0
        staff_total = sum(staff_coverage.values()) if staff_coverage else 0
        time_total = sum(time_coverage.values()) if time_coverage else 0
        
        # 3軸のバランスを考慮した完全性スコア
        total_constraints = facility_total + staff_total + time_total
        if total_constraints == 0:
            return 0.0
        
        # 各軸の均等性評価
        axis_totals = [facility_total, staff_total, time_total]
        mean_total = np.mean(axis_totals)
        balance_score = 1 - (np.std(axis_totals) / mean_total if mean_total > 0 else 1)
        
        # カバレッジスコア
        coverage_score = min(1.0, total_constraints / 75)  # 基準値75で正規化（3軸分）
        
        return (balance_score * 0.4 + coverage_score * 0.6)
    
    def _create_multi_axis_human_readable_report(self, facility_results: Dict, staff_results: Dict, time_calendar_results: Dict, integrated: Dict) -> Dict[str, Any]:
        """3軸統合された人間確認用レポート作成"""
        facility_hr = facility_results.get('human_readable', {})
        staff_hr = staff_results.get('human_readable', {})
        time_hr = time_calendar_results.get('human_readable', {})
        
        return {
            "統合サマリー": {
                "軸1_施設ルール": facility_hr.get('抽出事実サマリー', {}),
                "軸2_職員ルール": staff_hr.get('抽出事実サマリー', {}),
                "軸3_時間カレンダー": time_hr.get('抽出事実サマリー', {}),
                "統合制約数": {
                    "ハード制約": len(integrated['machine_readable'].get('hard_constraints', [])),
                    "ソフト制約": len(integrated['machine_readable'].get('soft_constraints', [])),
                    "推奨設定": len(integrated['machine_readable'].get('preferences', []))
                }
            },
            "3軸制約統合分析": {
                "関係性": integrated['machine_readable'].get('constraint_relationships', []),
                "競合解決": integrated['machine_readable'].get('conflict_resolution', {}),
                "完全性スコア": integrated['machine_readable']['integration_metadata'].get('integration_quality', {}).get('completeness_score', 0)
            },
            "実行優先度": integrated['machine_readable'].get('conflict_resolution', {}).get('priority_hierarchy', []),
            "要確認事項": self._generate_multi_axis_review_items(facility_hr, staff_hr, time_hr, integrated)
        }
    
    def _format_multi_axis_training_data(self, facility_results: Dict, staff_results: Dict, time_calendar_results: Dict) -> Dict[str, Any]:
        """3軸統合学習データの形式化"""
        facility_training = facility_results.get('training_data', {})
        staff_training = staff_results.get('training_data', {})
        time_training = time_calendar_results.get('training_data', {})
        
        return {
            "integrated_features": {
                "facility_level": facility_training,
                "individual_level": staff_training,
                "temporal_level": time_training,
                "cross_axis_correlations": []  # 軸間相関特徴量（将来拡張）
            },
            "constraint_embeddings": [],  # 制約のベクトル表現（将来拡張）
            "relationship_graph": [],  # 制約関係グラフ（将来拡張）
            "temporal_patterns": []  # 時間パターン特徴量（将来拡張）
        }
    
    def _generate_multi_axis_review_items(self, facility_hr: Dict, staff_hr: Dict, time_hr: Dict, integrated: Dict) -> List[str]:
        """3軸統合結果の要確認事項を生成"""
        review_items = []
        
        # 制約数の妥当性確認
        total_constraints = len(integrated['machine_readable'].get('hard_constraints', []))
        if total_constraints > 150:  # 3軸分なので基準値を上げる
            review_items.append(f"3軸統合制約数が{total_constraints}件と多数です。優先度の見直しをご検討ください。")
        
        # 軸間バランス確認
        facility_count = len([c for c in integrated['machine_readable'].get('hard_constraints', []) if c.get('axis') == 1])
        staff_count = len([c for c in integrated['machine_readable'].get('hard_constraints', []) if c.get('axis') == 2])
        time_count = len([c for c in integrated['machine_readable'].get('hard_constraints', []) if c.get('axis') == 3])
        
        if facility_count == 0:
            review_items.append("軸1(施設レベル)制約が検出されませんでした。データの確認が必要です。")
        if staff_count == 0:
            review_items.append("軸2(個人レベル)制約が検出されませんでした。スタッフデータの確認が必要です。")
        if time_count == 0:
            review_items.append("軸3(時間・カレンダー)制約が検出されませんでした。時間データの確認が必要です。")
        
        # 3軸競合の確認
        conflicts = integrated['machine_readable'].get('conflict_resolution', {}).get('detected_conflicts', [])
        three_axis_conflicts = [c for c in conflicts if c.get('conflict_type') == 'three_axis_tension']
        if len(three_axis_conflicts) > 0:
            review_items.append(f"3軸間競合が{len(three_axis_conflicts)}件検出されました。優先度調整が必要です。")
        
        # 時間制約の特別確認
        time_facts = time_hr.get('抽出事実サマリー', {}).get('総事実数', 0)
        if time_facts > 0:
            review_items.append(f"時間・カレンダー制約{time_facts}件が抽出されました。営業時間・祝日対応の確認をお勧めします。")
        
        return review_items
