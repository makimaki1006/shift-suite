"""ShiftMindReaderを統合した、Blueprint-V2の中核エンジン"""
import logging
from typing import Dict, Any, List

import pandas as pd

from .advanced_blueprint_engine import AdvancedBlueprintEngine
from .shift_mind_reader import ShiftMindReader

log = logging.getLogger(__name__)


class AdvancedBlueprintEngineV2(AdvancedBlueprintEngine):
    """思考プロセス解読機能と既存分析を統合したエンジン"""

    def __init__(self):
        super().__init__()
        self.mind_reader = ShiftMindReader()

    def run_full_blueprint_analysis(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """V2の全分析を実行する統合メソッド"""
        log.info("Blueprint-V2 フル分析を開始します...")

        causal_results = self.analyze_causal_relationships(long_df)
        ml_pattern_results = self.analyze_hidden_patterns_with_ml(long_df)
        network_results = self.analyze_network_effects(long_df)
        temporal_results = self.temporal_pattern_mining(long_df)

        mind_reader_results = self.mind_reader.read_creator_mind(long_df)

        all_results = {
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
