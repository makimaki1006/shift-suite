"""
シフト作成者の思考プロセスを解読するシステム（軽量版）
機械学習依存関係なしでの動作
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

import pandas as pd

from .constants import SLOT_HOURS

log = logging.getLogger(__name__)


@dataclass
class DecisionPoint:
    """シフト作成における意思決定ポイント"""

    context: Dict[str, Any]
    options: List[Dict[str, Any]]
    chosen_idx: int
    query_id: int


class ShiftMindReaderLite:
    """シフト作成者の思考を読み解く（軽量版）"""

    def __init__(self):
        self.preference_model = None

    def read_creator_mind(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """作成者の思考プロセスを解読するメインフロー（軽量版）"""
        log.info("思考プロセス解読を開始（軽量版）...")
        
        # 基本的な統計分析のみ実行
        basic_analysis = self._analyze_basic_patterns(long_df)
        decision_patterns = self._extract_simple_decision_patterns(long_df)
        
        return {
            "basic_analysis": basic_analysis,
            "decision_patterns": decision_patterns,
            "analysis_type": "lightweight",
            "note": "機械学習依存関係なしの基本分析"
        }
    
    def _analyze_basic_patterns(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """基本的なパターン分析"""
        if long_df.empty:
            return {"error": "データが空です"}
        
        # スタッフ別の基本統計
        staff_stats = {}
        for staff in long_df['staff'].unique():
            staff_data = long_df[long_df['staff'] == staff]
            
            staff_stats[staff] = {
                "total_shifts": len(staff_data),
                "avg_hours_per_shift": len(staff_data) * SLOT_HOURS / max(1, staff_data['ds'].dt.date.nunique()),
                "unique_dates": staff_data['ds'].dt.date.nunique(),
                "most_common_role": staff_data.get('role', pd.Series()).mode().iloc[0] if 'role' in staff_data.columns and not staff_data['role'].empty else 'unknown'
            }
        
        # 全体パターン
        overall_patterns = {
            "total_staff": long_df['staff'].nunique(),
            "total_shifts": len(long_df),
            "date_range": {
                "start": str(long_df['ds'].min().date()) if not long_df['ds'].empty else None,
                "end": str(long_df['ds'].max().date()) if not long_df['ds'].empty else None
            },
            "avg_shifts_per_staff": len(long_df) / max(1, long_df['staff'].nunique())
        }
        
        return {
            "staff_statistics": staff_stats,
            "overall_patterns": overall_patterns
        }
    
    def _extract_simple_decision_patterns(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """簡単な意思決定パターンの抽出"""
        patterns = {
            "workload_distribution": {},
            "temporal_patterns": {},
            "staff_preferences": {}
        }
        
        if long_df.empty:
            return patterns
        
        # 負荷分散パターン
        staff_workload = long_df.groupby('staff').size()
        patterns["workload_distribution"] = {
            "most_utilized": staff_workload.idxmax() if not staff_workload.empty else None,
            "least_utilized": staff_workload.idxmin() if not staff_workload.empty else None,
            "workload_variance": float(staff_workload.var()) if not staff_workload.empty else 0,
            "balance_score": 1.0 / (1.0 + float(staff_workload.var())) if not staff_workload.empty and staff_workload.var() > 0 else 1.0
        }
        
        # 時間パターン
        if 'ds' in long_df.columns:
            hourly_distribution = long_df['ds'].dt.hour.value_counts()
            patterns["temporal_patterns"] = {
                "peak_hours": hourly_distribution.head(3).index.tolist(),
                "off_peak_hours": hourly_distribution.tail(3).index.tolist(),
                "hourly_distribution": hourly_distribution.to_dict()
            }
        
        # スタッフの傾向
        for staff in long_df['staff'].unique():
            staff_data = long_df[long_df['staff'] == staff]
            if 'role' in staff_data.columns and not staff_data['role'].empty:
                role_dist = staff_data['role'].value_counts()
                patterns["staff_preferences"][staff] = {
                    "primary_role": role_dist.index[0] if not role_dist.empty else 'unknown',
                    "role_diversity": len(role_dist),
                    "specialization_score": float(role_dist.iloc[0] / len(staff_data)) if not role_dist.empty else 0
                }
        
        return patterns

    def get_simplified_insights(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """簡略化された洞察を提供"""
        analysis = self.read_creator_mind(long_df)
        
        insights = {
            "key_findings": [],
            "recommendations": [],
            "confidence": "basic_analysis"
        }
        
        if "basic_analysis" in analysis:
            basic = analysis["basic_analysis"]
            
            # 主要な発見
            if "overall_patterns" in basic:
                overall = basic["overall_patterns"]
                insights["key_findings"].append(f"総スタッフ数: {overall.get('total_staff', 0)}名")
                insights["key_findings"].append(f"総シフト数: {overall.get('total_shifts', 0)}件")
                insights["key_findings"].append(f"スタッフ当たり平均シフト数: {overall.get('avg_shifts_per_staff', 0):.1f}件")
            
            # 推奨事項
            if "decision_patterns" in analysis:
                patterns = analysis["decision_patterns"]
                if "workload_distribution" in patterns:
                    workload = patterns["workload_distribution"]
                    balance_score = workload.get("balance_score", 0)
                    
                    if balance_score < 0.7:
                        insights["recommendations"].append("スタッフ間の負荷バランスの改善を検討してください")
                    else:
                        insights["recommendations"].append("スタッフ間の負荷バランスは良好です")
        
        return insights


# 互換性のためのエイリアス
ShiftMindReader = ShiftMindReaderLite