"""
複合的制約発見システム - シフト作成者の真の意図をあぶり出す

このシステムは以下の2段階で動作します：
1. 各手法による単一分析をMECE的に実行
2. 単一分析結果の複合的組み合わせによる真の制約発見

複合的組み合わせの例：
- 時間パターン × スタッフ属性 × 業務特性
- 暗黙知 × 統計的裏付け × 業務要件
- 異常検知 × パターン認識 × ドメイン知識

Author: Claude Code Assistant  
Created: 2025-01-28
"""

from __future__ import annotations

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from itertools import combinations, product
import json

from .integrated_constraint_extraction_system import IntegratedConstraintExtractionSystem
from .blueprint_integrated_system import BlueprintIntegratedConstraintSystem
from .constants import SLOT_HOURS, STATISTICAL_THRESHOLDS

log = logging.getLogger(__name__)


class CompoundConstraintDiscoverySystem:
    """複合的制約発見システム - 単一分析の組み合わせから真の制約を発見"""
    
    def __init__(self):
        self.integrated_system = IntegratedConstraintExtractionSystem()
        self.blueprint_system = BlueprintIntegratedConstraintSystem()
        
        # 複合分析パラメータ
        self.min_compound_evidence_count = 2  # 複合制約として認定する最小根拠数
        self.compound_confidence_threshold = 0.6  # 複合制約の最小信頼度
        self.creator_intent_confidence_threshold = 0.8  # 作成者意図として認定する信頼度
        
    def discover_compound_constraints(self, 
                                    raw_excel_path: str,
                                    processed_data_dir: str,
                                    worktype_definitions: Dict = None,
                                    long_df: pd.DataFrame = None) -> Dict[str, Any]:
        """複合的制約発見の実行
        
        Args:
            raw_excel_path: 生データExcelファイルパス
            processed_data_dir: 加工済みデータディレクトリ
            worktype_definitions: 勤務区分定義
            long_df: 既存のlong形式データフレーム
            
        Returns:
            複合制約発見結果
        """
        log.info("=== 複合的制約発見システム開始 ===")
        
        # Phase 1: MECE的単一分析の実行
        log.info("Phase 1: MECE的単一分析実行中...")
        single_analysis_results = self._execute_mece_single_analyses(
            raw_excel_path, processed_data_dir, worktype_definitions, long_df
        )
        
        # Phase 2: 複合的組み合わせによる制約発見
        log.info("Phase 2: 複合的組み合わせによる制約発見中...")
        compound_constraints = self._discover_compound_patterns(single_analysis_results)
        
        # Phase 3: シフト作成者の意図推定
        log.info("Phase 3: シフト作成者の意図推定中...")
        creator_intentions = self._infer_creator_intentions(compound_constraints, single_analysis_results)
        
        # Phase 4: 人間確認用の優先度付けと構造化
        log.info("Phase 4: 人間確認用構造化中...")
        human_reviewable_results = self._structure_for_human_review(
            compound_constraints, creator_intentions, single_analysis_results
        )
        
        final_results = {
            "execution_metadata": {
                "timestamp": datetime.now().isoformat(),
                "system_version": "compound_discovery_v1.0",
                "single_analyses_count": len(single_analysis_results),
                "compound_constraints_count": len(compound_constraints),
                "creator_intentions_count": len(creator_intentions),
                "human_review_items_count": len(human_reviewable_results.get("priority_review_items", []))
            },
            "single_analysis_results": single_analysis_results,
            "compound_constraints": compound_constraints,
            "creator_intentions": creator_intentions,
            "human_reviewable_output": human_reviewable_results,
            "quality_assessment": self._assess_compound_quality(compound_constraints, creator_intentions)
        }
        
        log.info(f"=== 複合的制約発見完了 ===\n"
                f"発見した複合制約: {len(compound_constraints)}個\n"
                f"推定した作成者意図: {len(creator_intentions)}個\n"
                f"人間確認推奨項目: {len(human_reviewable_results.get('priority_review_items', []))}個")
        
        return final_results
    
    def _execute_mece_single_analyses(self, raw_excel_path: str, processed_data_dir: str,
                                     worktype_definitions: Dict, long_df: pd.DataFrame) -> Dict[str, Any]:
        """MECE的な単一分析の実行"""
        single_results = {}
        
        # 1. 統合制約抽出システム（既存）
        try:
            integrated_results = self.integrated_system.execute_integrated_constraint_extraction(
                raw_excel_path, processed_data_dir, worktype_definitions, long_df
            )
            single_results["integrated_extraction"] = integrated_results
            log.info(f"統合制約抽出完了: {integrated_results['execution_metadata']['final_filtered_constraints']}個の制約")
        except Exception as e:
            log.error(f"統合制約抽出エラー: {e}")
            single_results["integrated_extraction"] = {"error": str(e)}
        
        # 2. ブループリント統合システム（既存）
        try:
            if long_df is not None and not long_df.empty:
                blueprint_results = self.blueprint_system.execute_blueprint_analysis(long_df, worktype_definitions)
                single_results["blueprint_analysis"] = blueprint_results
                log.info(f"ブループリント分析完了: {self.blueprint_system._count_blueprint_constraints(blueprint_results)}個の暗黙知")
        except Exception as e:
            log.error(f"ブループリント分析エラー: {e}")
            single_results["blueprint_analysis"] = {"error": str(e)}
        
        # 3. 時系列パターン分析（新規）
        try:
            if long_df is not None and not long_df.empty:
                temporal_results = self._analyze_temporal_patterns(long_df)
                single_results["temporal_analysis"] = temporal_results
                log.info(f"時系列パターン分析完了: {len(temporal_results.get('patterns', []))}個のパターン")
        except Exception as e:
            log.error(f"時系列パターン分析エラー: {e}")
            single_results["temporal_analysis"] = {"error": str(e)}
        
        # 4. スタッフ関係性分析（新規）
        try:
            if long_df is not None and not long_df.empty:
                relationship_results = self._analyze_staff_relationships(long_df)
                single_results["relationship_analysis"] = relationship_results
                log.info(f"スタッフ関係性分析完了: {len(relationship_results.get('relationships', []))}個の関係性")
        except Exception as e:
            log.error(f"スタッフ関係性分析エラー: {e}")
            single_results["relationship_analysis"] = {"error": str(e)}
        
        # 5. 業務特性分析（新規）
        try:
            if long_df is not None and not long_df.empty:
                business_results = self._analyze_business_characteristics(long_df, worktype_definitions)
                single_results["business_analysis"] = business_results
                log.info(f"業務特性分析完了: {len(business_results.get('characteristics', []))}個の特性")
        except Exception as e:
            log.error(f"業務特性分析エラー: {e}")
            single_results["business_analysis"] = {"error": str(e)}
        
        return single_results
    
    def _analyze_temporal_patterns(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """時系列パターンの単一分析"""
        patterns = {
            "cyclic_patterns": [],      # 周期的パターン
            "trend_patterns": [],       # トレンドパターン
            "seasonal_patterns": [],    # 季節パターン
            "anomaly_patterns": []      # 異常パターン
        }
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        # 週次周期パターン
        weekly_patterns = self._find_weekly_cyclic_patterns(working_df)
        patterns["cyclic_patterns"].extend(weekly_patterns)
        
        # 長期トレンド
        trend_patterns = self._find_long_term_trends(working_df)
        patterns["trend_patterns"].extend(trend_patterns)
        
        # 月内季節性
        seasonal_patterns = self._find_monthly_seasonal_patterns(working_df)
        patterns["seasonal_patterns"].extend(seasonal_patterns)
        
        return {
            "patterns": patterns,
            "analysis_metadata": {
                "total_patterns": sum(len(p) for p in patterns.values()),
                "data_period": {
                    "start": working_df['ds'].min().isoformat() if not working_df.empty else None,
                    "end": working_df['ds'].max().isoformat() if not working_df.empty else None
                }
            }
        }
    
    def _find_weekly_cyclic_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """週次周期パターンの発見"""
        patterns = []
        
        # スタッフ別の曜日パターン
        for staff in working_df['staff'].unique():
            staff_df = working_df[working_df['staff'] == staff]
            weekday_counts = staff_df.groupby(staff_df['ds'].dt.dayofweek).size()
            
            # 明確な曜日偏重があるか
            if len(weekday_counts) > 0:
                max_weekday = weekday_counts.idxmax()
                max_ratio = weekday_counts.max() / weekday_counts.sum()
                
                if max_ratio > 0.4:  # 40%以上が特定曜日に集中
                    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                    
                    patterns.append({
                        "type": "週次曜日集中パターン",
                        "staff": staff,
                        "dominant_weekday": weekday_names[max_weekday],
                        "concentration_ratio": max_ratio,
                        "pattern_strength": max_ratio,
                        "evidence": weekday_counts.to_dict()
                    })
        
        return patterns
    
    def _find_long_term_trends(self, working_df: pd.DataFrame) -> List[Dict]:
        """長期トレンドの発見"""
        patterns = []
        
        # 月別勤務頻度の変化
        monthly_counts = working_df.groupby([working_df['ds'].dt.to_period('M'), 'staff']).size().unstack(fill_value=0)
        
        if len(monthly_counts) >= 3:  # 3ヶ月以上のデータがある場合
            for staff in monthly_counts.columns:
                staff_trend = monthly_counts[staff]
                
                # 単純な線形トレンド計算
                x = np.arange(len(staff_trend))
                if len(x) > 0 and staff_trend.std() > 0:
                    correlation = np.corrcoef(x, staff_trend)[0, 1]
                    
                    if abs(correlation) > 0.7:  # 強い相関
                        trend_direction = "増加" if correlation > 0 else "減少"
                        
                        patterns.append({
                            "type": "長期勤務頻度トレンド",
                            "staff": staff,
                            "trend_direction": trend_direction,
                            "correlation_strength": abs(correlation),
                            "pattern_strength": abs(correlation),
                            "evidence": staff_trend.to_dict()
                        })
        
        return patterns
    
    def _find_monthly_seasonal_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """月内季節パターンの発見"""
        patterns = []
        
        # 月内期間別（月初・月中・月末）の分析
        working_df = working_df.copy()
        working_df['month_period'] = working_df['ds'].dt.day.apply(
            lambda d: '月初' if d <= 10 else '月中' if d <= 20 else '月末'
        )
        
        period_patterns = working_df.groupby(['staff', 'month_period']).size().unstack(fill_value=0)
        
        for staff in period_patterns.index:
            staff_periods = period_patterns.loc[staff]
            total = staff_periods.sum()
            
            if total >= 5:  # 最小サンプルサイズ
                max_period = staff_periods.idxmax()
                max_ratio = staff_periods.max() / total
                
                if max_ratio > 0.5:  # 50%以上が特定期間に集中
                    patterns.append({
                        "type": "月内期間集中パターン",
                        "staff": staff,
                        "preferred_period": max_period,
                        "concentration_ratio": max_ratio,
                        "pattern_strength": max_ratio,
                        "evidence": staff_periods.to_dict()
                    })
        
        return patterns
    
    def _analyze_staff_relationships(self, long_df: pd.DataFrame) -> Dict[str, Any]:
        """スタッフ関係性の単一分析"""
        relationships = {
            "collaboration_patterns": [],   # 協働パターン
            "avoidance_patterns": [],      # 回避パターン
            "mentor_mentee_patterns": [],  # 指導関係パターン
            "role_complement_patterns": [] # 役割補完パターン
        }
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        # 同日同勤務での協働分析
        collaboration_patterns = self._find_collaboration_patterns(working_df)
        relationships["collaboration_patterns"].extend(collaboration_patterns)
        
        # 意図的回避パターン
        avoidance_patterns = self._find_avoidance_patterns(working_df)
        relationships["avoidance_patterns"].extend(avoidance_patterns)
        
        # 指導関係推定
        if 'role' in working_df.columns:
            mentor_patterns = self._find_mentor_mentee_patterns(working_df)
            relationships["mentor_mentee_patterns"].extend(mentor_patterns)
        
        return {
            "relationships": relationships,
            "analysis_metadata": {
                "total_relationships": sum(len(r) for r in relationships.values()),
                "staff_count": working_df['staff'].nunique()
            }
        }
    
    def _find_collaboration_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """協働パターンの発見"""
        patterns = []
        
        # 同日同勤務区分でのペア分析
        daily_staff_groups = working_df.groupby(['ds', 'code'])['staff'].apply(list).reset_index()
        
        pair_counts = defaultdict(int)
        staff_total_days = working_df.groupby('staff')['ds'].nunique()
        
        for _, row in daily_staff_groups.iterrows():
            staff_list = row['staff']
            if len(staff_list) >= 2:
                for pair in combinations(sorted(set(staff_list)), 2):
                    pair_counts[pair] += 1
        
        # 統計的有意性の検定
        for (staff1, staff2), observed_count in pair_counts.items():
            if staff1 in staff_total_days.index and staff2 in staff_total_days.index:
                days1 = staff_total_days[staff1]
                days2 = staff_total_days[staff2]
                total_days = working_df['ds'].nunique()
                
                # 期待値計算
                expected_count = (days1 * days2) / total_days if total_days > 0 else 0
                
                if expected_count > 0:
                    collaboration_ratio = observed_count / expected_count
                    
                    if collaboration_ratio >= 2.0 and observed_count >= 3:  # 期待値の2倍以上で3回以上
                        patterns.append({
                            "type": "高頻度協働パターン",
                            "staff_pair": [staff1, staff2],
                            "observed_collaborations": observed_count,
                            "expected_collaborations": expected_count,
                            "collaboration_ratio": collaboration_ratio,
                            "pattern_strength": min(1.0, collaboration_ratio / 3.0),
                            "evidence": {
                                "staff1_total_days": days1,
                                "staff2_total_days": days2,
                                "total_period_days": total_days
                            }
                        })
        
        return patterns
    
    def _find_avoidance_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """回避パターンの発見"""
        patterns = []
        
        # 同様の分析だが、期待値より大幅に少ない場合を検出
        daily_staff_groups = working_df.groupby(['ds', 'code'])['staff'].apply(list).reset_index()
        
        all_staff = set(working_df['staff'].unique())
        pair_counts = defaultdict(int)
        staff_total_days = working_df.groupby('staff')['ds'].nunique()
        
        # 実際の共起回数をカウント
        for _, row in daily_staff_groups.iterrows():
            staff_list = row['staff']
            if len(staff_list) >= 1:
                present_staff = set(staff_list)
                for pair in combinations(sorted(all_staff), 2):
                    if all(s in present_staff for s in pair):
                        pair_counts[pair] += 1
        
        # 回避パターンの検出
        for pair in combinations(sorted(all_staff), 2):
            staff1, staff2 = pair
            observed_count = pair_counts.get(pair, 0)
            
            if staff1 in staff_total_days.index and staff2 in staff_total_days.index:
                days1 = staff_total_days[staff1]
                days2 = staff_total_days[staff2]
                total_days = working_df['ds'].nunique()
                
                expected_count = (days1 * days2) / total_days if total_days > 0 else 0
                
                if expected_count >= 2.0 and observed_count == 0:  # 期待値2回以上なのに共起なし
                    patterns.append({
                        "type": "意図的回避パターン",
                        "staff_pair": [staff1, staff2],
                        "expected_collaborations": expected_count,
                        "actual_collaborations": 0,
                        "avoidance_strength": min(1.0, expected_count / 5.0),
                        "pattern_strength": min(1.0, expected_count / 5.0),
                        "evidence": {
                            "staff1_total_days": days1,
                            "staff2_total_days": days2,
                            "total_period_days": total_days
                        }
                    })
        
        return patterns
    
    def _find_mentor_mentee_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """指導関係パターンの発見"""
        patterns = []
        
        # 役職や経験に基づく推定（簡易版）
        role_hierarchy = {
            'manager': 3, 'supervisor': 2, 'senior': 2, 
            'regular': 1, 'junior': 1, 'trainee': 0, 'intern': 0
        }
        
        staff_roles = working_df.groupby('staff')['role'].first()
        
        # 役職差がある組み合わせを分析
        for (staff1, role1), (staff2, role2) in combinations(staff_roles.items(), 2):
            level1 = role_hierarchy.get(role1.lower(), 1)
            level2 = role_hierarchy.get(role2.lower(), 1)
            
            if abs(level1 - level2) >= 2:  # 2段階以上の差
                senior_staff = staff1 if level1 > level2 else staff2
                junior_staff = staff2 if level1 > level2 else staff1
                
                # 同勤務での指導機会分析
                senior_days = set(working_df[working_df['staff'] == senior_staff]['ds'])
                junior_days = set(working_df[working_df['staff'] == junior_staff]['ds'])
                overlap_days = senior_days & junior_days
                
                if len(overlap_days) >= 3:  # 3日以上の重複
                    overlap_ratio = len(overlap_days) / len(junior_days) if junior_days else 0
                    
                    if overlap_ratio > 0.3:  # 30%以上で重複
                        patterns.append({
                            "type": "指導関係パターン",
                            "mentor": senior_staff,
                            "mentee": junior_staff,
                            "overlap_days": len(overlap_days),
                            "mentee_coverage_ratio": overlap_ratio,
                            "pattern_strength": min(1.0, overlap_ratio),
                            "evidence": {
                                "mentor_role": staff_roles[senior_staff],
                                "mentee_role": staff_roles[junior_staff],
                                "mentor_total_days": len(senior_days),
                                "mentee_total_days": len(junior_days)
                            }
                        })
        
        return patterns
    
    def _analyze_business_characteristics(self, long_df: pd.DataFrame, 
                                        worktype_definitions: Dict = None) -> Dict[str, Any]:
        """業務特性の単一分析"""
        characteristics = {
            "workload_patterns": [],        # 業務負荷パターン
            "skill_requirement_patterns": [], # スキル要求パターン
            "coverage_patterns": [],        # カバレッジパターン
            "efficiency_patterns": []       # 効率性パターン
        }
        
        working_df = long_df[long_df['parsed_slots_count'] > 0]
        
        # 業務負荷パターン
        workload_patterns = self._find_workload_patterns(working_df)
        characteristics["workload_patterns"].extend(workload_patterns)
        
        # スキル要求パターン（勤務区分ベース）
        if worktype_definitions:
            skill_patterns = self._find_skill_requirement_patterns(working_df, worktype_definitions)
            characteristics["skill_requirement_patterns"].extend(skill_patterns)
        
        return {
            "characteristics": characteristics,
            "analysis_metadata": {
                "total_characteristics": sum(len(c) for c in characteristics.values())
            }
        }
    
    def _find_workload_patterns(self, working_df: pd.DataFrame) -> List[Dict]:
        """業務負荷パターンの発見"""
        patterns = []
        
        # 日別業務負荷の計算
        daily_workload = working_df.groupby('ds')['parsed_slots_count'].sum()
        
        if len(daily_workload) >= 7:  # 1週間以上のデータ
            mean_load = daily_workload.mean()
            std_load = daily_workload.std()
            
            # 高負荷日の特定
            high_load_threshold = mean_load + std_load
            high_load_days = daily_workload[daily_workload > high_load_threshold]
            
            if len(high_load_days) > 0:
                # 高負荷日の曜日パターン
                high_load_weekdays = [day.dayofweek for day in high_load_days.index]
                weekday_counter = Counter(high_load_weekdays)
                
                if weekday_counter:
                    most_common_weekday = weekday_counter.most_common(1)[0][0]
                    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                    
                    patterns.append({
                        "type": "高負荷日パターン",
                        "dominant_weekday": weekday_names[most_common_weekday],
                        "high_load_frequency": len(high_load_days),
                        "pattern_strength": min(1.0, len(high_load_days) / len(daily_workload)),
                        "evidence": {
                            "mean_load": mean_load,
                            "threshold": high_load_threshold,
                            "high_load_days_count": len(high_load_days),
                            "weekday_distribution": dict(weekday_counter)
                        }
                    })
        
        return patterns
    
    def _find_skill_requirement_patterns(self, working_df: pd.DataFrame, 
                                       worktype_definitions: Dict) -> List[Dict]:
        """スキル要求パターンの発見"""
        patterns = []
        
        # 勤務区分別のスタッフ配置分析
        code_staff_matrix = working_df.groupby(['code', 'staff']).size().unstack(fill_value=0)
        
        for code in code_staff_matrix.index:
            if code in worktype_definitions:
                staff_counts = code_staff_matrix.loc[code]
                active_staff = staff_counts[staff_counts > 0]
                
                if len(active_staff) > 0:
                    # 特定少数スタッフに限定される勤務区分かどうか
                    if len(active_staff) <= 3 and active_staff.sum() >= 5:  # 3名以下で5回以上
                        patterns.append({
                            "type": "専門スキル要求パターン",
                            "work_code": code,
                            "qualified_staff": active_staff.index.tolist(),
                            "specialization_level": 1.0 - (len(active_staff) / working_df['staff'].nunique()),
                            "pattern_strength": min(1.0, active_staff.sum() / 10),
                            "evidence": {
                                "total_assignments": active_staff.sum(),
                                "staff_distribution": active_staff.to_dict(),
                                "work_definition": worktype_definitions.get(code, {})
                            }
                        })
        
        return patterns
    
    def _discover_compound_patterns(self, single_results: Dict[str, Any]) -> List[Dict]:
        """単一分析結果の複合的組み合わせによる制約発見"""
        compound_constraints = []
        
        # 複合パターン1: 時間パターン × スタッフ関係性
        temporal_staff_compounds = self._find_temporal_staff_compounds(single_results)
        compound_constraints.extend(temporal_staff_compounds)
        
        # 複合パターン2: 暗黙知 × 統計的裏付け
        implicit_statistical_compounds = self._find_implicit_statistical_compounds(single_results)
        compound_constraints.extend(implicit_statistical_compounds)
        
        # 複合パターン3: 業務特性 × スタッフ能力
        business_staff_compounds = self._find_business_staff_compounds(single_results)
        compound_constraints.extend(business_staff_compounds)
        
        # 複合パターン4: 多層制約の相互作用
        interaction_compounds = self._find_constraint_interactions(single_results)
        compound_constraints.extend(interaction_compounds)
        
        log.info(f"複合パターン発見完了: {len(compound_constraints)}個の複合制約")
        return compound_constraints
    
    def _find_temporal_staff_compounds(self, single_results: Dict) -> List[Dict]:
        """時間パターン × スタッフ関係性の複合制約"""
        compounds = []
        
        temporal_patterns = single_results.get("temporal_analysis", {}).get("patterns", {})
        relationship_patterns = single_results.get("relationship_analysis", {}).get("relationships", {})
        
        # 週次パターンと協働パターンの組み合わせ
        weekly_patterns = temporal_patterns.get("cyclic_patterns", [])
        collaboration_patterns = relationship_patterns.get("collaboration_patterns", [])
        
        for weekly in weekly_patterns:
            if weekly.get("type") == "週次曜日集中パターン":
                weekly_staff = weekly.get("staff")
                target_weekday = weekly.get("dominant_weekday")
                
                # この曜日で高頻度協働するペアを探す
                for collab in collaboration_patterns:
                    if collab.get("type") == "高頻度協働パターン":
                        staff_pair = collab.get("staff_pair", [])
                        
                        if weekly_staff in staff_pair:
                            partner_staff = [s for s in staff_pair if s != weekly_staff][0]
                            
                            compounds.append({
                                "type": "曜日指定ペア勤務制約",
                                "constraint_description": f"{weekly_staff}が{target_weekday}に勤務する際は、{partner_staff}との協働が高確率で発生",
                                "primary_staff": weekly_staff,
                                "partner_staff": partner_staff,
                                "target_weekday": target_weekday,
                                "compound_confidence": min(
                                    weekly.get("pattern_strength", 0),
                                    collab.get("pattern_strength", 0)
                                ) * 0.8,  # 複合制約は信頼度を若干下げる
                                "evidence_sources": ["temporal_analysis", "relationship_analysis"],
                                "supporting_evidence": {
                                    "weekly_pattern": weekly,
                                    "collaboration_pattern": collab
                                }
                            })
        
        return compounds
    
    def _find_implicit_statistical_compounds(self, single_results: Dict) -> List[Dict]:
        """暗黙知 × 統計的裏付けの複合制約"""
        compounds = []
        
        # ブループリント分析結果の取得
        blueprint_results = single_results.get("blueprint_analysis", {})
        blueprint_rules = blueprint_results.get("rules", [])
        
        # 統合制約抽出結果の取得
        integrated_results = single_results.get("integrated_extraction", {})
        filtered_constraints = integrated_results.get("filtered_practical_constraints", [])
        
        # ブループリントルールを統計的制約で裏付け
        for blueprint_rule in blueprint_rules:
            if hasattr(blueprint_rule, 'staff_name') and hasattr(blueprint_rule, 'rule_type'):
                blueprint_staff = blueprint_rule.staff_name
                blueprint_type = blueprint_rule.rule_type
                
                # 関連する統計的制約を探す
                for stat_constraint in filtered_constraints:
                    if stat_constraint.get("source") in ["approach1", "approach2"]:
                        # スタッフが一致し、制約タイプが関連する場合
                        if (blueprint_staff in str(stat_constraint) and 
                            ("週勤務" in blueprint_type and "週" in str(stat_constraint)) or
                            ("曜日" in blueprint_type and "曜日" in str(stat_constraint))):
                            
                            # 信頼度の相互補強
                            blueprint_confidence = getattr(blueprint_rule, 'confidence_score', 0.5)
                            stat_confidence = stat_constraint.get("confidence", 0.5)
                            
                            # 相互に補強される複合制約
                            compound_confidence = (blueprint_confidence + stat_confidence) / 2 * 1.2  # 相互補強ボーナス
                            compound_confidence = min(1.0, compound_confidence)
                            
                            if compound_confidence > self.compound_confidence_threshold:
                                compounds.append({
                                    "type": "暗黙知統計裏付け制約",
                                    "constraint_description": f"{blueprint_staff}の{blueprint_type}は統計的分析でも確認された",
                                    "staff": blueprint_staff,
                                    "constraint_category": blueprint_type,
                                    "compound_confidence": compound_confidence,
                                    "evidence_sources": ["blueprint_analysis", "statistical_analysis"],
                                    "supporting_evidence": {
                                        "blueprint_rule": {
                                            "type": blueprint_rule.rule_type,
                                            "description": blueprint_rule.rule_description,
                                            "confidence": blueprint_confidence
                                        },
                                        "statistical_constraint": stat_constraint
                                    }
                                })
        
        return compounds
    
    def _find_business_staff_compounds(self, single_results: Dict) -> List[Dict]:
        """業務特性 × スタッフ能力の複合制約"""
        compounds = []
        
        business_characteristics = single_results.get("business_analysis", {}).get("characteristics", {})
        relationship_analysis = single_results.get("relationship_analysis", {}).get("relationships", {})
        
        # 専門スキル要求 × 指導関係パターン
        skill_patterns = business_characteristics.get("skill_requirement_patterns", [])
        mentor_patterns = relationship_analysis.get("mentor_mentee_patterns", [])
        
        for skill_pattern in skill_patterns:
            if skill_pattern.get("type") == "専門スキル要求パターン":
                qualified_staff = skill_pattern.get("qualified_staff", [])
                work_code = skill_pattern.get("work_code")
                
                # 指導関係があるペアを探す
                for mentor_pattern in mentor_patterns:
                    mentor = mentor_pattern.get("mentor")
                    mentee = mentor_pattern.get("mentee")
                    
                    # 専門職務に指導関係のペアが関与している場合
                    if mentor in qualified_staff or mentee in qualified_staff:
                        compounds.append({
                            "type": "専門業務指導体制制約",
                            "constraint_description": f"{work_code}勤務では{mentor}による{mentee}への指導体制が組まれている",
                            "work_code": work_code,
                            "mentor": mentor,
                            "mentee": mentee,
                            "compound_confidence": min(
                                skill_pattern.get("pattern_strength", 0),
                                mentor_pattern.get("pattern_strength", 0)
                            ) * 0.9,
                            "evidence_sources": ["business_analysis", "relationship_analysis"],
                            "supporting_evidence": {
                                "skill_requirement": skill_pattern,
                                "mentoring_relationship": mentor_pattern
                            }
                        })
        
        return compounds
    
    def _find_constraint_interactions(self, single_results: Dict) -> List[Dict]:
        """多層制約の相互作用発見"""
        compounds = []
        
        # 各分析結果から制約を統合的に分析
        all_constraints = []
        
        # 統合制約抽出結果
        integrated_results = single_results.get("integrated_extraction", {})
        filtered_constraints = integrated_results.get("filtered_practical_constraints", [])
        for constraint in filtered_constraints:
            constraint["analysis_source"] = "integrated_extraction"
            all_constraints.append(constraint)
        
        # 制約間の相互作用を分析
        constraint_interactions = self._analyze_constraint_interactions(all_constraints)
        compounds.extend(constraint_interactions)
        
        return compounds
    
    def _analyze_constraint_interactions(self, constraints: List[Dict]) -> List[Dict]:
        """制約間の相互作用分析"""
        interactions = []
        
        # 同一スタッフに関する制約の相互作用
        staff_constraints = defaultdict(list)
        for constraint in constraints:
            # スタッフ情報を抽出（様々なキーを試行）
            staff_keys = ["staff", "スタッフ", "staff_name", "primary_staff"]
            for key in staff_keys:
                if key in constraint:
                    staff = constraint[key]
                    staff_constraints[staff].append(constraint)
                    break
                elif key in str(constraint):
                    # 文字列内からスタッフ名を推定（簡易版）
                    # より高度な実装では自然言語処理を使用
                    pass
        
        # 複数制約があるスタッフの相互作用を分析
        for staff, staff_constraint_list in staff_constraints.items():
            if len(staff_constraint_list) >= 2:
                # 制約間の潜在的矛盾や相乗効果を分析
                interaction_analysis = self._analyze_staff_constraint_interactions(staff, staff_constraint_list)
                if interaction_analysis:
                    interactions.append(interaction_analysis)
        
        return interactions
    
    def _analyze_staff_constraint_interactions(self, staff: str, constraints: List[Dict]) -> Optional[Dict]:
        """特定スタッフの制約間相互作用分析"""
        if len(constraints) < 2:
            return None
        
        # 制約の種類を分析
        constraint_types = [c.get("type", "不明") for c in constraints]
        
        # 週勤務日数制限 + 曜日制限 の組み合わせなど、特定の組み合わせを検出
        has_weekly_limit = any("週勤務" in ct or "週" in ct for ct in constraint_types)
        has_weekday_limit = any("曜日" in ct for ct in constraint_types)
        
        if has_weekly_limit and has_weekday_limit:
            weekly_constraints = [c for c in constraints if "週" in c.get("type", "")]
            weekday_constraints = [c for c in constraints if "曜日" in c.get("type", "")]
            
            if weekly_constraints and weekday_constraints:
                return {
                    "type": "週日数-曜日制限相互作用",
                    "constraint_description": f"{staff}は週勤務日数制限と曜日制限の両方が設定されており、相互に影響する",
                    "staff": staff,
                    "interaction_type": "制約相乗効果",
                    "compound_confidence": min([c.get("confidence", 0.5) for c in constraints]) * 1.1,  # 相乗効果ボーナス
                    "evidence_sources": ["constraint_interaction_analysis"],
                    "supporting_evidence": {
                        "weekly_constraints": weekly_constraints,
                        "weekday_constraints": weekday_constraints,
                        "interaction_note": "曜日制限により実質的な週勤務日数がさらに制限される"
                    }
                }
        
        return None
    
    def _infer_creator_intentions(self, compound_constraints: List[Dict], 
                                single_results: Dict[str, Any]) -> List[Dict]:
        """シフト作成者の意図推定"""
        intentions = []
        
        # 高信頼度の複合制約から作成者意図を推定
        high_confidence_compounds = [
            c for c in compound_constraints 
            if c.get("compound_confidence", 0) >= self.creator_intent_confidence_threshold
        ]
        
        for compound in high_confidence_compounds:
            intention = self._infer_specific_creator_intention(compound, single_results)
            if intention:
                intentions.append(intention)
        
        # 制約パターンの組み合わせから意図を推定
        pattern_based_intentions = self._infer_pattern_based_intentions(compound_constraints)
        intentions.extend(pattern_based_intentions)
        
        log.info(f"作成者意図推定完了: {len(intentions)}個の意図を推定")
        return intentions
    
    def _infer_specific_creator_intention(self, compound_constraint: Dict, 
                                        single_results: Dict) -> Optional[Dict]:
        """特定の複合制約から作成者意図を推定"""
        constraint_type = compound_constraint.get("type")
        
        if constraint_type == "曜日指定ペア勤務制約":
            return {
                "intention_type": "チームワーク重視",
                "intention_description": f"特定の曜日において、経験豊富なスタッフとのペア体制を意図的に構築",
                "confidence": compound_constraint.get("compound_confidence", 0),
                "affected_staff": [
                    compound_constraint.get("primary_staff"),
                    compound_constraint.get("partner_staff")
                ],
                "business_rationale": "新人教育・業務品質確保・チーム連携強化",
                "evidence": compound_constraint
            }
        
        elif constraint_type == "専門業務指導体制制約":
            return {
                "intention_type": "スキル継承体制",
                "intention_description": "専門業務における知識・スキルの継承を意図した指導体制の構築",
                "confidence": compound_constraint.get("compound_confidence", 0),
                "affected_staff": [
                    compound_constraint.get("mentor"),
                    compound_constraint.get("mentee")
                ],
                "business_rationale": "専門スキル継承・人材育成・業務継続性確保",
                "evidence": compound_constraint
            }
        
        elif constraint_type == "暗黙知統計裏付け制約":
            return {
                "intention_type": "個人最適化配慮",
                "intention_description": "スタッフ個人の特性・制約を考慮した個別最適化されたシフト配置",
                "confidence": compound_constraint.get("compound_confidence", 0),
                "affected_staff": [compound_constraint.get("staff")],
                "business_rationale": "スタッフ満足度向上・離職防止・業務効率最大化",
                "evidence": compound_constraint
            }
        
        return None
    
    def _infer_pattern_based_intentions(self, compound_constraints: List[Dict]) -> List[Dict]:
        """制約パターンの組み合わせから意図を推定"""
        intentions = []
        
        # 制約の種類別グルーピング
        constraint_by_type = defaultdict(list)
        for constraint in compound_constraints:
            constraint_type = constraint.get("type", "不明")
            constraint_by_type[constraint_type].append(constraint)
        
        # 複数の専門業務指導体制がある場合
        mentoring_constraints = constraint_by_type.get("専門業務指導体制制約", [])
        if len(mentoring_constraints) >= 2:
            intentions.append({
                "intention_type": "組織的人材育成戦略",
                "intention_description": "複数の専門領域において系統的な人材育成・スキル継承体制を構築",
                "confidence": np.mean([c.get("compound_confidence", 0) for c in mentoring_constraints]),
                "affected_constraints_count": len(mentoring_constraints),
                "business_rationale": "長期的な組織力強化・専門性の維持・世代交代の準備",
                "evidence": mentoring_constraints
            })
        
        # 複数のペア勤務制約がある場合
        pair_constraints = constraint_by_type.get("曜日指定ペア勤務制約", [])
        if len(pair_constraints) >= 2:
            intentions.append({
                "intention_type": "チーム連携強化戦略",
                "intention_description": "複数の曜日・ペアにおいて連携体制を強化し、業務品質を安定化",
                "confidence": np.mean([c.get("compound_confidence", 0) for c in pair_constraints]),
                "affected_constraints_count": len(pair_constraints),
                "business_rationale": "業務品質の安定化・リスク分散・チームワーク向上",
                "evidence": pair_constraints
            })
        
        return intentions
    
    def _structure_for_human_review(self, compound_constraints: List[Dict], 
                                   creator_intentions: List[Dict],
                                   single_results: Dict[str, Any]) -> Dict[str, Any]:
        """人間確認用の構造化"""
        
        # 優先度別の分類
        priority_review_items = []
        
        # 高信頼度の作成者意図（最優先確認）
        high_confidence_intentions = [
            intent for intent in creator_intentions 
            if intent.get("confidence", 0) >= self.creator_intent_confidence_threshold
        ]
        
        for intention in high_confidence_intentions:
            priority_review_items.append({
                "priority": "最優先",
                "category": "作成者意図推定",
                "title": intention.get("intention_description", ""),
                "confidence": intention.get("confidence", 0),
                "business_impact": intention.get("business_rationale", ""),
                "review_question": f"この意図推定は正確ですか？: {intention.get('intention_description')}",
                "affected_staff": intention.get("affected_staff", []),
                "evidence_summary": self._summarize_evidence_for_human(intention.get("evidence", {}))
            })
        
        # 高信頼度の複合制約（高優先確認）
        high_confidence_compounds = [
            comp for comp in compound_constraints 
            if comp.get("compound_confidence", 0) >= self.compound_confidence_threshold
        ]
        
        for compound in high_confidence_compounds:
            priority_review_items.append({
                "priority": "高",
                "category": "複合制約",
                "title": compound.get("constraint_description", ""),
                "confidence": compound.get("compound_confidence", 0),
                "constraint_type": compound.get("type", ""),
                "review_question": f"この制約は実際に適用されていますか？: {compound.get('constraint_description')}",
                "evidence_summary": self._summarize_evidence_for_human(compound.get("supporting_evidence", {}))
            })
        
        # 信頼度順でソート
        priority_review_items.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return {
            "priority_review_items": priority_review_items,
            "review_statistics": {
                "total_items": len(priority_review_items),
                "high_confidence_intentions": len(high_confidence_intentions),
                "high_confidence_compounds": len(high_confidence_compounds),
                "average_confidence": np.mean([item.get("confidence", 0) for item in priority_review_items]) if priority_review_items else 0
            },
            "review_instructions": {
                "recommended_review_order": "信頼度の高い順（作成者意図 → 複合制約 → 単一制約）",
                "key_questions": [
                    "推定された作成者意図は実際の意図と一致しますか？",
                    "発見された制約は実際に適用されていますか？",
                    "見落とされている重要な制約はありますか？",
                    "制約の優先度や重要度の評価は適切ですか？"
                ]
            }
        }
    
    def _summarize_evidence_for_human(self, evidence: Dict) -> str:
        """人間が理解しやすい形での根拠要約"""
        if not evidence:
            return "根拠データなし"
        
        summary_parts = []
        
        # 統計的根拠の要約
        if "statistical_constraint" in evidence:
            stat = evidence["statistical_constraint"]
            confidence = stat.get("confidence", 0)
            summary_parts.append(f"統計分析（信頼度{confidence:.1%}）")
        
        # ブループリント分析の要約
        if "blueprint_rule" in evidence:
            blueprint = evidence["blueprint_rule"]
            confidence = blueprint.get("confidence", 0)
            summary_parts.append(f"暗黙知分析（信頼度{confidence:.1%}）")
        
        # 時間パターンの要約
        if "weekly_pattern" in evidence:
            weekly = evidence["weekly_pattern"]
            weekday = weekly.get("dominant_weekday", "")
            ratio = weekly.get("concentration_ratio", 0)
            summary_parts.append(f"{weekday}曜日集中（{ratio:.1%}）")
        
        # 協働パターンの要約
        if "collaboration_pattern" in evidence:
            collab = evidence["collaboration_pattern"]
            ratio = collab.get("collaboration_ratio", 0)
            summary_parts.append(f"協働頻度（期待値の{ratio:.1f}倍）")
        
        return " + ".join(summary_parts) if summary_parts else "複合的な根拠あり"
    
    def _assess_compound_quality(self, compound_constraints: List[Dict], 
                                creator_intentions: List[Dict]) -> Dict[str, float]:
        """複合制約発見の品質評価"""
        quality_metrics = {
            "compound_discovery_rate": 0.0,     # 複合制約発見率
            "creator_intent_accuracy": 0.0,     # 作成者意図推定精度
            "actionability_score": 0.0,         # 実行可能性スコア
            "business_relevance_score": 0.0,    # 業務関連性スコア
            "overall_compound_quality": 0.0     # 総合品質スコア
        }
        
        if not compound_constraints and not creator_intentions:
            return quality_metrics
        
        # 複合制約発見率
        high_confidence_compounds = [
            c for c in compound_constraints 
            if c.get("compound_confidence", 0) >= self.compound_confidence_threshold
        ]
        quality_metrics["compound_discovery_rate"] = len(high_confidence_compounds) / max(1, len(compound_constraints))
        
        # 作成者意図推定精度
        high_confidence_intentions = [
            i for i in creator_intentions 
            if i.get("confidence", 0) >= self.creator_intent_confidence_threshold
        ]
        quality_metrics["creator_intent_accuracy"] = len(high_confidence_intentions) / max(1, len(creator_intentions))
        
        # 実行可能性スコア（人間が確認・実行できそうな制約の割合）
        actionable_items = [
            item for item in compound_constraints + creator_intentions
            if (item.get("compound_confidence", 0) >= 0.7 or item.get("confidence", 0) >= 0.7) and
               len(item.get("constraint_description", item.get("intention_description", ""))) > 20
        ]
        total_items = len(compound_constraints) + len(creator_intentions)
        quality_metrics["actionability_score"] = len(actionable_items) / max(1, total_items)
        
        # 業務関連性スコア（業務に直接関連する制約の割合）
        business_relevant_items = [
            item for item in compound_constraints + creator_intentions
            if any(keyword in str(item).lower() for keyword in 
                  ["指導", "教育", "チーム", "専門", "スキル", "品質", "効率", "安全"])
        ]
        quality_metrics["business_relevance_score"] = len(business_relevant_items) / max(1, total_items)
        
        # 総合品質スコア
        quality_metrics["overall_compound_quality"] = (
            quality_metrics["compound_discovery_rate"] * 0.3 +
            quality_metrics["creator_intent_accuracy"] * 0.3 +
            quality_metrics["actionability_score"] * 0.2 +
            quality_metrics["business_relevance_score"] * 0.2
        )
        
        return quality_metrics


def create_compound_constraint_discovery(raw_excel_path: str,
                                       processed_data_dir: str,
                                       worktype_definitions: Dict = None,
                                       long_df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    複合的制約発見システムのメイン実行関数
    
    Args:
        raw_excel_path: 生データExcelファイルパス
        processed_data_dir: 加工済みデータディレクトリ
        worktype_definitions: 勤務区分定義
        long_df: 既存のlong形式データフレーム
        
    Returns:
        複合制約発見結果
    """
    system = CompoundConstraintDiscoverySystem()
    return system.discover_compound_constraints(
        raw_excel_path, processed_data_dir, worktype_definitions, long_df
    )